from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from collections import defaultdict, OrderedDict, Counter
from .models import Salad, OtherDish, WeeklyMenu, Order, SideDish, AppState
from datetime import datetime, time, timedelta
import logging
from django.utils.timezone import localtime, now as timezone_now



@login_required
def mis_ordenes(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'misordenes.html', {'orders': orders})

logger = logging.getLogger(__name__)


def get_current_week():
    """Obtiene la semana actual desde AppState sin modificarla."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    return app_state.current_week


def advance_week():
    """Avanza la semana actual en el ciclo de 4 semanas si es lunes."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    current_time = timezone.localtime(timezone.now())

    # Verificar si hoy es lunes
    if current_time.weekday() == 0:  # Lunes = 0
        # Verificar si ya se avanzó esta semana
        if app_state.last_week_advance:
            last_advance = timezone.localtime(app_state.last_week_advance)
            if last_advance.date() == current_time.date():  # Ya se avanzó hoy
                return app_state.current_week

        # Avanzar a la siguiente semana
        app_state.current_week = (app_state.current_week % 4) + 1
        app_state.last_week_advance = current_time
        app_state.save()

    return app_state.current_week

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

# Función auxiliar para determinar el menú diario
def get_menu_day_and_week():
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    current_minute = now.minute
    today_weekday = now.weekday()

    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    current_week = advance_week()
    displayed_week = current_week

    if today_weekday in (0, 1, 2, 3, 4):  # Lunes a Viernes
        if current_hour > 13 or (current_hour == 13 and current_minute >= 10):
            if today_weekday == 4:  # Viernes después de las 13:10
                menu_day_name = "Lunes"
                displayed_week = (current_week % 4) + 1
            else:
                menu_day_name = menu_days[today_weekday + 1]
        else:
            menu_day_name = menu_days[today_weekday]
    else:  # Fin de semana
        menu_day_name = "Lunes"
        displayed_week = (current_week % 4) + 1

    return menu_day_name, displayed_week

@login_required
def ruralapp(request):
    start_date, _ = calculate_time_range()

    recent_orders = Order.objects.filter(order_date__gte=start_date).order_by('-order_date')
    total_orders = recent_orders.count()

    # Validar si el usuario ya realizó un pedido en este rango
    error_message = None
    if not (request.user.is_staff and request.user.is_superuser):  # Excluir admins/superusuarios de esta validación
        user_orders = recent_orders.filter(user=request.user)
        if user_orders.exists():
            error_message = "Ya has realizado un pedido en este periodo. No puedes realizar otro."


    return render(request, 'ruralapp.html', {
        'orders': recent_orders,
        'total_orders': total_orders,
        'error_message': error_message,
    })

@login_required
def order_view(request):
    start_date, end_date = calculate_time_range()

    # Verificar si el usuario ya hizo un pedido en este rango, excluyendo admins/superusuarios
    if not (request.user.is_staff and request.user.is_superuser):
        user_orders = Order.objects.filter(
            user=request.user,
            order_date__range=(start_date, end_date)
        )
        if user_orders.exists():
            return JsonResponse({'success': False, 'error': "Ya has realizado un pedido en este periodo. No puedes realizar otro."})

    menu_day_name, displayed_week = get_menu_day_and_week()

    try:
        daily_menu = WeeklyMenu.objects.get(week=displayed_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()

    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments', '')

        if not main_dish and not salad_id and not other_dish_id and not side_dish_id:
            return JsonResponse({'success': False, 'error': "Debe seleccionar al menos un plato principal, una ensalada, un plato adicional o una guarnición."})

        order = Order(
            user=request.user,
            main_dish=main_dish,
            salad=Salad.objects.get(id=salad_id) if salad_id else None,
            other_dish=OtherDish.objects.get(id=other_dish_id) if other_dish_id else None,
            side_dish=SideDish.objects.get(id=side_dish_id) if side_dish_id else None,
            comments=comments
        )
        order.save()
        return JsonResponse({'success': True})

    return render(request, 'order.html', {
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert,
        'menu_day_name': menu_day_name
    })

@login_required
def edit_order(request, order_id):
    menu_day_name, displayed_week = get_menu_day_and_week()

    try:
        daily_menu = WeeklyMenu.objects.get(week=displayed_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments', '')

        if not main_dish and not salad_id and not other_dish_id and not side_dish_id:
            return JsonResponse({'success': False, 'error': "Debe seleccionar al menos un plato principal, una ensalada, un plato adicional o una guarnición."})

        order.main_dish = main_dish
        order.salad = Salad.objects.get(id=salad_id) if salad_id else None
        order.other_dish = OtherDish.objects.get(id=other_dish_id) if other_dish_id else None
        order.side_dish = SideDish.objects.get(id=side_dish_id) if side_dish_id else None
        order.comments = comments
        order.save()
        return JsonResponse({'success': True})

    return render(request, 'edit_order.html', {
        'order': order,
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert,
        'menu_day_name': menu_day_name
    })



@login_required
def resumen_pedidos(request):
    now = timezone.localtime(timezone.now())
    current_hour = now.hour
    today_weekday = now.weekday()

    # Determinar el rango de tiempo
    if current_hour >= 13:
        start_date = now.replace(hour=13, minute=0, second=0, microsecond=0)
    else:
        if today_weekday == 0:
            last_friday = now - timedelta(days=3)
            start_date = last_friday.replace(hour=13, minute=0, second=0, microsecond=0)
        else:
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=0, second=0, microsecond=0)

    # Filtrar pedidos
    orders = Order.objects.filter(order_date__gte=start_date)

    # Inicializar secciones y contadores
    section_1 = defaultdict(lambda: {'count': 0, 'comments': []})
    section_2 = defaultdict(lambda: {'count': 0, 'comments': []})
    section_3 = defaultdict(lambda: {'count': 0, 'comments': []})
    unique_orders = set()

    for order in orders:
        # Sección 1: main_dish, salad y other_dish sin guarnición
        if order.main_dish or order.salad or (order.other_dish and not order.other_dish.plus_side):
            dish_name = " + ".join(
                filter(None, [
                    order.main_dish,
                    f"Ensalada {order.salad.id}" if order.salad else None,
                    order.other_dish.name if order.other_dish and not order.other_dish.plus_side else None,
                ])
            )
            section_1[dish_name]['count'] += 1
            if order.comments:
                section_1[dish_name]['comments'].append(order.comments)
            unique_orders.add(order.id)

        # Sección 2: other_dish con guarnición
        if order.other_dish and order.other_dish.plus_side:
            dish_name = order.other_dish.name
            section_2[dish_name]['count'] += 1
            if order.comments:
                section_2[dish_name]['comments'].append(order.comments)
            unique_orders.add(order.id)

        # Sección 3: guarniciones
        if order.side_dish:
            dish_name = order.side_dish.name
            section_3[dish_name]['count'] += 1
            if order.comments:
                section_3[dish_name]['comments'].append(order.comments)
            if not order.other_dish or not order.other_dish.plus_side:
                unique_orders.add(order.id)
        else:
            # Caso donde no hay guarnición
            print(f"El pedido {order.id} no tiene guarnición asignada.")

    # Ordenar las secciones
    section_1 = sorted(section_1.items(), key=lambda x: x[1]['count'], reverse=True)
    section_2 = sorted(section_2.items(), key=lambda x: x[1]['count'], reverse=True)
    section_3 = sorted(section_3.items(), key=lambda x: x[1]['count'], reverse=True)

    # Generar mensaje para WhatsApp
    menu_day, displayed_week = get_menu_day_and_week()  # Obtener el día del menú y la semana
    whatsapp_message = f"*BITFARMS*             Semana {displayed_week} / {menu_day}```\n\n"

    for section in [section_1, section_2, section_3]:
        for dish, data in section:
            whatsapp_message += f"{data['count']} {dish[:40]:<40}\n"
        whatsapp_message += "---------------\n"

    total_orders = len(unique_orders)
    
    whatsapp_message += f"```{total_orders} Pedidos en total.\n\nPor favor agregar __ menus adicionales.\nSerían ** pedidos para hoy.\n\nMuchas gracias."
    
    # Preparar datos para la plantilla
    summary_list = []
    for section in [section_1, section_2, section_3]:
        for dish, data in section:
            summary_list.append({
                'main_dish': dish,
                'count': data['count'],
                'comments': data['comments'],
            })

    # Renderizar vista
    if "generate_whatsapp" in request.GET:
        return render(request, 'whatsapp_preview.html', {
            'whatsapp_message': whatsapp_message,
        })

    return render(request, 'resumen_pedidos.html', {
        'summary_list': summary_list,
        'current_day': now.strftime('%A'),
        'total_orders': total_orders,
    })



