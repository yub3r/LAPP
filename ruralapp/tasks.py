import slack
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ruralapp.models import WeeklyMenu, AppState
import logging
logger = logging.getLogger(__name__)


TOKEN = 'xoxb-2569679174866-6651760390341-nXgxbFm3vJVs2eSq30Se0pZF'
client = slack.WebClient(TOKEN)

def get_current_week():
    """Obtiene y actualiza dinámicamente la semana actual desde AppState."""
    app_state, _ = AppState.objects.get_or_create(id=1)  # ID fijo para asegurar un único registro
    return app_state.current_week

def advance_week():
    """Avanza la semana actual en el ciclo de 4 semanas."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    app_state.current_week = (app_state.current_week % 4) + 1
    app_state.save()
    return app_state.current_week

@shared_task
def send_slack_menu():
    logger.info("Inicio de la tarea send_slack_menu.")
    now = timezone.localtime(timezone.now())
    current_hour = now.time().hour
    today_weekday = now.weekday()  # 0 = Lunes, ..., 6 = Domingo

    # Obtener la semana actual desde AppState
    current_week = get_current_week()
    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

    # Determinar el día del menú
    if today_weekday == 4 and current_hour >= 13:  # Viernes después de las 13:00
        current_week = advance_week()
        menu_day_name = 'Lunes'
    elif today_weekday in (5, 6):  # Sábado o domingo
        current_week = advance_week()
        menu_day_name = 'Lunes'
    else:
        menu_day_name = menu_days[today_weekday]
        if current_hour >= 13 and today_weekday < 4:  # Avanzar al siguiente día (Lunes-Jueves)
            menu_day_name = menu_days[(today_weekday + 1) % 5]

    # Obtener el menú
    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=menu_day_name)
        main_dish_1 = daily_menu.main_dish_1
        main_dish_2 = daily_menu.main_dish_2
        message = (
            f"🍽 *El menú de hoy {menu_day_name}*:\n"
            f"- {main_dish_1}\n"
            f"- {main_dish_2}\n\n"
            "⏰ *Recuerden ordenar antes de las 8:30*"
        )
    except WeeklyMenu.DoesNotExist:
        message = f"🍽 *Hoy {menu_day_name} no hay menú configurado.*"
        # logger.info(f"Menú enviado para {menu_day_name}, semana {current_week}.")

    # Enviar mensaje a Slack
    try:
        client.chat_postMessage(
            channel='C054TP80E5V',  # ID del canal
            text=message
        )
        return f"Mensaje enviado a Slack: {message}"
        
    except slack.errors.SlackApiError as e:
        error_message = f"Error al enviar mensaje a Slack: {e.response['error']}"
        raise Exception(error_message)
    except Exception as e:
        raise Exception(f"Error desconocido al enviar mensaje a Slack: {str(e)}")
    
pass