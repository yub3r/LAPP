from django.utils import timezone
from datetime import timedelta

def calculate_time_range():
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()

    if current_hour > 13 or (current_hour == 13 and current_minute >= 10):
        start_date = now.replace(hour=13, minute=10, second=0, microsecond=0)
    else:
        if today_weekday == 0:
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        elif today_weekday in [5, 6]:
            last_friday = now - timedelta(days=(today_weekday - 4))
            start_date = last_friday.replace(hour=13, minute=10, second=0, microsecond=0)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=10, second=0, microsecond=0)

    end_date = start_date + timedelta(days=1)
    return start_date, end_date