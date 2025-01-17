import slack
from celery import shared_task
from django.utils import timezone
from ruralapp.models import WeeklyMenu, AppState, Order
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from ruralapp.views import get_menu_day_and_week  # Reemplaza advance_week por simulación local
import logging

logger = logging.getLogger(__name__)

TOKEN = 'xoxb-2569679174866-6651760390341-nXgxbFm3vJVs2eSq30Se0pZF'
client = slack.WebClient(TOKEN)


# Función auxiliar para calcular el rango de tiempo válido
def calculate_time_range():
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()

    if current_hour > 13 or (current_hour == 13 and current_minute >= 10):
        start_date = now.replace(hour=13, minute=10, second=0, microsecond=0)
    else:
        if today_weekday == 0:  # Lunes antes de las 13:10
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        elif today_weekday in [5, 6]:  # Sábado o domingo
            last_friday = now - timedelta(days=(today_weekday - 4))
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=10, second=0, microsecond=0)

    end_date = start_date + timedelta(days=1)
    return start_date, end_date


def calculate_week_no_update():
    """Calcula la semana siguiente sin modificar el estado en la base de datos."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    return (app_state.current_week % 4) + 1

@shared_task
def send_slack_menu():
    logger.info("Inicio de la tarea send_slack_menu.")
    menu_day_name, current_week = get_menu_day_and_week()

    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=menu_day_name)
        main_dish_1 = daily_menu.main_dish_1
        main_dish_2 = daily_menu.main_dish_2
        message = (
            f"🍽 *El menú de hoy {menu_day_name}*:\n"
            f"- {main_dish_1}\n"
            f"- {main_dish_2}\n\n"
            "⏰ *Los que faltan, recuerden ordenar antes de las 8:30*\n"
            "👮‍♂️ _Quien no alcance a ordenar a tiempo y lo notifica, se le pedirá el menú A._"
        )
    except WeeklyMenu.DoesNotExist:
        message = f"🍽 *Hoy {menu_day_name} no hay menú configurado.*"

    try:
        client.chat_postMessage(channel='C054TP80E5V', text=message)
        return f"Mensaje enviado a Slack: {message}"
    except slack.errors.SlackApiError as e:
        raise Exception(f"Error al enviar mensaje a Slack: {e.response['error']}")
    except Exception as e:
        raise Exception(f"Error desconocido al enviar mensaje a Slack: {str(e)}")

@shared_task
def send_slack_tomorrow_menu():
    logger.info("Inicio de la tarea send_slack_tomorrow_menu.")
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()  # 0: Lunes, 4: Viernes

    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    current_week = get_menu_day_and_week()[1]  # Obtener la semana actual
    tomorrow_menu_day_name = "Lunes"  # Valor por defecto para el fin de semana
    tomorrow_week = current_week

    if today_weekday in range(5):  # Si hoy es de lunes a viernes
        if today_weekday == 4 and (current_hour > 13 or (current_hour == 13 and current_minute >= 10)):
            # Si es viernes después de las 13:10, mañana es lunes y se avanza la semana
            tomorrow_menu_day_name = "Lunes"
            tomorrow_week = calculate_week_no_update()
        else:
            tomorrow_index = (today_weekday + 1) % 5
            tomorrow_menu_day_name = menu_days[tomorrow_index]
            tomorrow_week = current_week if tomorrow_index != 0 else calculate_week_no_update()

    try:
        daily_menu = WeeklyMenu.objects.get(week=tomorrow_week, day=tomorrow_menu_day_name)
        main_dish_1 = daily_menu.main_dish_1
        main_dish_2 = daily_menu.main_dish_2
        message = (
            f"🍽 *El menú del día {tomorrow_menu_day_name}*:\n"
            f"- {main_dish_1}\n"
            f"- {main_dish_2}\n\n"
            "⏰ *Recuerden ordenar antes de las 16:00*"
        )
    except WeeklyMenu.DoesNotExist:
        message = f"🍽 *Mañana {tomorrow_menu_day_name} no hay menú configurado.*"

    try:
        client.chat_postMessage(channel='C054TP80E5V', text=message)
        return f"Mensaje enviado a Slack: {message}"
    except slack.errors.SlackApiError as e:
        raise Exception(f"Error al enviar mensaje a Slack: {e.response['error']}")
    except Exception as e:
        raise Exception(f"Error desconocido al enviar mensaje a Slack: {str(e)}")


User = get_user_model()

@shared_task
def send_slack_pending_orders():
    logger.info("Inicio de la tarea send_slack_pending_orders.")
    start_date, end_date = calculate_time_range()  # Rango de tiempo para las órdenes del día

    # Obtener todos los usuarios activos que no son superusuarios ni staff
    active_users = User.objects.filter(is_active=True, is_staff=False, is_superuser=False)

    # Obtener los usuarios que ya hicieron un pedido en el rango de tiempo actual
    users_with_orders = Order.objects.filter(order_date__range=(start_date, end_date)).values_list('user', flat=True)

    # Filtrar usuarios que no han realizado pedidos
    users_without_orders = active_users.exclude(id__in=users_with_orders)

    if users_without_orders.exists():
        user_mentions = ', '.join(f"@{user.get_full_name()}" for user in users_without_orders)
        message = f"\U0001F4C5 *Recordatorio de órdenes del día:* Los usuarios {user_mentions} *no han realizado sus pedidos*"
    else:
        message = "\U0001F4C5 Todos los usuarios han realizado sus pedidos hoy. \U0001F389"

    try:
        client.chat_postMessage(channel='C054TP80E5V', text=message)
        return f"Mensaje enviado a Slack: {message}"
    except slack.errors.SlackApiError as e:
        raise Exception(f"Error al enviar mensaje a Slack: {e.response['error']}")
    except Exception as e:
        raise Exception(f"Error desconocido al enviar mensaje a Slack: {str(e)}")
