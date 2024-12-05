from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from collections import defaultdict, OrderedDict, Counter
from .models import Salad, OtherDish, WeeklyMenu, Order, SideDish
from datetime import datetime, time, timedelta
import logging

@login_required
def ruralapp(request):
    # Obtener la fecha y hora actual
    # now = timezone.now()
    now = timezone.localtime(timezone.now()) # Convierte explícitamente timezone.now() a la zona horaria local
    current_hour = now.hour
    today_weekday = now.weekday()  # 0 = Lunes, ..., 6 = Domingo

    # Inicializar el rango de tiempo
    if current_hour >= 13:  # Después de las 13:00
        start_date = now.replace(hour=13, minute=0, second=0, microsecond=0)  # Hoy a las 13:00
    else:  # Antes de las 13:00
        if today_weekday == 0:  # Si es lunes
            last_friday = now - timedelta(days=3)  # Retroceder al viernes
            start_date = last_friday.replace(hour=13, minute=0, second=0, microsecond=0)  # Viernes a las 13:00
        else:  # Para cualquier otro día de la semana
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=13, minute=0, second=0, microsecond=0)  # Ayer a las 13:00

    # Filtrar las órdenes realizadas en el rango de tiempo determinado
    recent_orders = Order.objects.filter(order_date__gte=start_date).order_by('-order_date')
    
    # Calcular el total de órdenes
    total_orders = recent_orders.count()

    return render(request, 'ruralapp.html', {'orders': recent_orders, 'total_orders': total_orders})



@login_required
def mis_ordenes(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'misordenes.html', {'orders': orders})

logger = logging.getLogger(__name__)


@login_required
def order_view(request):
    now = timezone.localtime(timezone.now())  # Fecha y hora actuales con zona horaria
    current_hour = now.time().hour
    today = now.date()
    tomorrow = today + timedelta(days=1)
    today_weekday = now.weekday()  # 0 = Lunes, ..., 6 = Domingo
    
    # Semana inicial definida manualmente (entre 1 y 4)
    initial_week = 2  # Cambia este valor según el punto de inicio del ciclo
    total_weeks = 4  # Total de semanas en el ciclo

    # Estado actual del ciclo (determinar semana actual)
    current_week = initial_week

    # Avanzar de semana según condiciones
    if today_weekday == 4 and current_hour >= 13:  # Viernes después de las 13:00
        current_week = (current_week % total_weeks) + 1  # Avanzar a la siguiente semana
    elif today_weekday in (5, 6):  # Sábado o domingo
        current_week = (current_week % total_weeks) + 1  # Usar la siguiente semana

    # Nombres de los días del menú en el ciclo
    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

    # Determinar el día del menú
    if today_weekday in range(5):  # Si es entre lunes y viernes
        menu_day_name = menu_days[today_weekday]
        if current_hour >= 13 and today_weekday < 4:  # Después de las 13:00 y no es viernes
            menu_day_name = menu_days[(today_weekday + 1) % 5]
    else:  # Fines de semana siempre reinician en lunes
        menu_day_name = 'Lunes'


    # Obtener el menú diario
    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    # Obtener datos adicionales para el formulario
    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()

    if request.method == 'POST':
        # Procesar el formulario
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
    now = timezone.localtime(timezone.now())
    current_hour = now.time().hour
    today_weekday = now.weekday()  # 0 = Lunes, ..., 6 = Domingo

    # Semana inicial definida manualmente (entre 1 y 4)
    initial_week = 2  # Cambia este valor según el punto de inicio del ciclo
    total_weeks = 4  # Total de semanas en el ciclo

    # Estado actual del ciclo (determinar semana actual)
    current_week = initial_week

    # Avanzar de semana según condiciones
    if today_weekday == 4 and current_hour >= 13:  # Viernes después de las 13:00
        current_week = (current_week % total_weeks) + 1  # Avanzar a la siguiente semana
    elif today_weekday in (5, 6):  # Sábado o domingo
        current_week = (current_week % total_weeks) + 1  # Usar la siguiente semana

    # Nombres de los días del menú en el ciclo
    menu_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

    # Determinar el día del menú
    if today_weekday in range(5):  # Si es entre lunes y viernes
        menu_day_name = menu_days[today_weekday]
        if current_hour >= 13 and today_weekday < 4:  # Después de las 13:00 y no es viernes
            menu_day_name = menu_days[(today_weekday + 1) % 5]
    else:  # Fines de semana siempre reinician en lunes
        menu_day_name = 'Lunes'

    # Obtener el menú correspondiente al día y semana calculados
    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=menu_day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    # Obtener listas de ensaladas, platos adicionales y guarniciones
    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
    side_dishes = SideDish.objects.all()

    # Obtener el pedido (si existe)
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Obtener y validar los datos del formulario
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments')

        # Validación: al menos un plato seleccionado
        if not main_dish and not salad_id and not other_dish_id and not side_dish_id:
            return JsonResponse({'success': False, 'error': "Debe seleccionar al menos un plato principal, una ensalada, un plato adicional o una guarnición."})

        # Actualizar el pedido
        order.main_dish = main_dish
        order.salad = Salad.objects.get(id=salad_id) if salad_id else None
        order.other_dish = OtherDish.objects.get(id=other_dish_id) if other_dish_id else None
        order.side_dish = SideDish.objects.get(id=side_dish_id) if side_dish_id else None
        order.comments = comments
        order.save()
        return JsonResponse({'success': True})

    # Renderizar la plantilla con los datos del menú
    return render(request, 'edit_order.html', {
        'order': order,
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert
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

    # Ordenar las secciones
    section_1 = sorted(section_1.items(), key=lambda x: x[1]['count'], reverse=True)
    section_2 = sorted(section_2.items(), key=lambda x: x[1]['count'], reverse=True)
    section_3 = sorted(section_3.items(), key=lambda x: x[1]['count'], reverse=True)

    # Generar mensaje para WhatsApp
    whatsapp_message = "```\n"
    for section in [section_1, section_2, section_3]:
        for dish, data in section:
            whatsapp_message += f"{data['count']} {dish[:45]:<45}\n"
        whatsapp_message += "---------------\n"

    total_orders = len(unique_orders)
    
    whatsapp_message += f"```\n*{total_orders}* Pedidos en total.\n"

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






