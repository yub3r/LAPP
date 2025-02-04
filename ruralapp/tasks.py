import slack, time
from slack import WebClient
from slack.errors import SlackApiError
from celery import shared_task
from django.utils import timezone
from ruralapp.models import WeeklyMenu, AppState, Order
from datetime import timedelta
from django.contrib.auth import get_user_model
from ruralapp.views import get_menu_day_and_week  # Reemplaza advance_week por simulación local
import logging

logger = logging.getLogger(__name__)

TOKEN = 'xoxb-2569679174866-6651760390341-nXgxbFm3vJVs2eSq30Se0pZF'
client = slack.WebClient(TOKEN)


# Función auxiliar para calcular el rango de tiempo válido
def calculate_time_range():
    now = timezone.localtime(timezone.now())
    today_weekday = now.weekday()

    if now.hour > 13 or (now.hour == 13 and now.minute >= 10):
        start_date = now.replace(hour=13, minute=10, second=0, microsecond=0)
    else:
        if today_weekday == 0:
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=10)
        elif today_weekday in [5, 6]:
            last_friday = now - timedelta(days=(today_weekday - 4))
            start_date = last_friday.replace(hour=13, minute=10)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=10)

    end_date = start_date + timedelta(days=1)
    return start_date, end_date


def calculate_week_no_update():
    app_state, _ = AppState.objects.get_or_create(id=1)
    return (app_state.current_week % 4) + 1


@shared_task
def send_slack_menu():
    logger.info("Inicio de la tarea send_slack_menu.")
    menu_day_name, current_week = get_menu_day_and_week()

    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=menu_day_name)
        main_dish_1, main_dish_2 = daily_menu.main_dish_1, daily_menu.main_dish_2
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


# Nueva función para calcular el nombre del día siguiente y la semana correspondiente
def get_tomorrow_menu_day_and_week():
    today_weekday = timezone.localtime(timezone.now()).weekday()
    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    current_week = get_menu_day_and_week()[1]
    tomorrow_menu_day_name = "Lunes"
    tomorrow_week = current_week

    if today_weekday in range(5):
        if today_weekday == 4:
            tomorrow_menu_day_name, tomorrow_week = "Lunes", calculate_week_no_update()
        else:
            tomorrow_menu_day_name = menu_days[(today_weekday + 1) % 5]

    return tomorrow_menu_day_name, tomorrow_week

@shared_task
def send_slack_tomorrow_menu():
    logger.info("Inicio de la tarea send_slack_tomorrow_menu.")
    tomorrow_menu_day_name, tomorrow_week = get_tomorrow_menu_day_and_week()

    try:
        daily_menu = WeeklyMenu.objects.get(week=tomorrow_week, day=tomorrow_menu_day_name)
        main_dish_1, main_dish_2 = daily_menu.main_dish_1, daily_menu.main_dish_2
        message = (
            f"*Desde ya puedes ordenar!! 🍽 Menú del día {tomorrow_menu_day_name}*:\n"
            f"- {main_dish_1}\n"
            f"- {main_dish_2}\n\n"
            f"⏰ *Por favor ordenar antes de las 16:00*"
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
    start_date, end_date = calculate_time_range()

    active_users = User.objects.filter(userprofile__menu=True)
    users_with_orders = Order.objects.filter(order_date__range=(start_date, end_date)).values_list('user', flat=True)
    users_without_orders = active_users.exclude(id__in=users_with_orders)

    tomorrow_menu_day_name, _ = get_tomorrow_menu_day_and_week()
    if users_without_orders.exists():
        user_mentions = ', '.join(f"@{user.get_full_name()}" for user in users_without_orders)
        message = (
            f"👮‍♂️ *Recordatorio de órdenes del día {tomorrow_menu_day_name}:*\n"
            f"🔍 Los usuarios {user_mentions}\n\n"
            f"🤷‍♂️ *NO han realizado sus pedidos*"
        )
    else:
        message = "\U0001F4C5 Todos los usuarios han realizado sus pedidos hoy. \U0001F389"

    try:
        client.chat_postMessage(channel='C054TP80E5V', text=message)
        return f"Mensaje enviado a Slack: {message}"
    except slack.errors.SlackApiError as e:
        raise Exception(f"Error al enviar mensaje a Slack: {e.response['error']}")
    except Exception as e:
        raise Exception(f"Error desconocido al enviar mensaje a Slack: {str(e)}")

# def get_channel_members(channel_id):
#     try:
#         response = client.conversations_members(channel=channel_id)
#         return response.get('members', [])
#     except SlackApiError as e:
#         logger.error(f"Error fetching channel members: {e.response['error']}")
#         return []

# def get_user_slack_id(username, channel_members, all_users):
#     for member in all_users:
#         if member["id"] in channel_members:  # Filtrar solo los miembros del canal
#             profile = member.get("profile", {})
#             if profile.get("real_name") == username or profile.get("real_name_normalized") == username:
#                 return member.get("id")
#     return None

# @shared_task
# def send_slack_pending_orders():
#     logger.info("Inicio de la tarea send_slack_pending_orders.")
#     start_date, end_date = calculate_time_range()

#     active_users = User.objects.filter(userprofile__menu=True)
#     users_with_orders = Order.objects.filter(order_date__range=(start_date, end_date)).values_list('user', flat=True)
#     users_without_orders = active_users.exclude(id__in=users_with_orders)
#     channel_id = "C054TP80E5V"  # Tu ID de canal
#     channel_members = get_channel_members(channel_id)

#     try:
#         all_users = client.users_list()["members"]
#     except SlackApiError as e:
#         logger.error(f"Error fetching user list from Slack: {e.response['error']}")
#         return

#     slack_ids = []
#     for user in users_without_orders:
#         slack_id = get_user_slack_id(user.get_full_name(), channel_members, all_users)
#         if slack_id:
#             slack_ids.append(slack_id)
#         time.sleep(1)  # Esperar entre llamadas para evitar rate limit

#     valid_mentions = [f"<@{user_id}>" for user_id in slack_ids if user_id]
    
#     tomorrow_menu_day_name, _ = get_tomorrow_menu_day_and_week()
#     if valid_mentions:
#         message = (
#             f"👮‍♂️ *Recordatorio de órdenes del día {tomorrow_menu_day_name}:*\n"
#             f"🔍 Los usuarios {', '.join(valid_mentions)}\n"
#             f"🤷‍♂️ *NO han realizado sus pedidos*"
#         )
#     else:
#         message = "\U0001F4C5 Todos los usuarios han realizado sus pedidos hoy. \U0001F389"

#     try:
#         client.chat_postMessage(channel='C054TP80E5V', text=message)
#         return f"Mensaje enviado a Slack: {message}"
#     except SlackApiError as e:
#         logger.error(f"Error al enviar mensaje a Slack: {e.response['error']}")
#         return f"Error al enviar mensaje a Slack: {e.response['error']}"
