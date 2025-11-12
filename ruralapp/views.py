from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
import json
from django.db.models import Max, Q
from collections import defaultdict, OrderedDict, Counter
from .models import Salad, OtherDish, WeeklyMenu, Order, SideDish, AppState
from datetime import datetime, time, timedelta
import logging
from django.utils.timezone import localtime, now as timezone_now
from django.views.decorators.cache import never_cache
            


@login_required
def mis_ordenes(request):
    start_date, end_date = calculate_time_range()
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'misordenes.html', {'orders': orders, 'start_date': start_date, 'end_date': end_date})


logger = logging.getLogger(__name__)


def get_current_week():
    """Obtiene la semana actual desde AppState sin modificarla."""
    app_state, _ = AppState.objects.get_or_create(id=1)
    return app_state.current_weeks


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
    today_weekday = now.weekday()  # 0=Lunes, ..., 6=Domingo

    def at_1310(dt):
        return dt.replace(hour=13, minute=10, second=0, microsecond=0)

    today_1310 = at_1310(now)

    # Casos por día de la semana
    if today_weekday == 5 or today_weekday == 6:  # Sábado o Domingo
        # Ventana de fin de semana: desde viernes 13:10 hasta lunes 13:10
        last_friday = now - timedelta(days=(today_weekday - 4))  # 5->1, 6->2
        next_monday = now + timedelta(days=(7 - today_weekday))  # 5->2, 6->1
        start_date = at_1310(last_friday)
        end_date = at_1310(next_monday)

    elif today_weekday == 4:  # Viernes
        if now >= today_1310:
            # Después de viernes 13:10: ventana se extiende hasta lunes 13:10
            start_date = today_1310
            end_date = at_1310(now + timedelta(days=3))  # Lunes
        else:
            # Antes de 13:10: desde jueves 13:10 hasta hoy 13:10
            start_date = at_1310(now - timedelta(days=1))
            end_date = today_1310

    elif today_weekday == 0:  # Lunes
        if now < today_1310:
            # Lunes antes de 13:10: incluir todo el fin de semana y mañana de lunes
            start_date = at_1310(now - timedelta(days=3))  # Viernes 13:10
            end_date = today_1310  # Lunes 13:10
        else:
            # Lunes después de 13:10: ventana normal 24h
            start_date = today_1310
            end_date = at_1310(now + timedelta(days=1))

    else:  # Martes, Miércoles, Jueves
        if now < today_1310:
            start_date = at_1310(now - timedelta(days=1))
            end_date = today_1310
        else:
            start_date = today_1310
            end_date = at_1310(now + timedelta(days=1))

    print(
        f"DEBUG: Rango de fechas - Desde: {start_date} Hasta: {end_date} (hoy={['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][today_weekday]})"
    )
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

    print(f"DEBUG: Menú del día: {menu_day_name}, Semana: {displayed_week}")
    return menu_day_name, displayed_week

@login_required
def ruralapp(request):
    # Obtener fechas y menú usando las funciones auxiliares
    start_date, end_date = calculate_time_range()
    menu_day_name, displayed_week = get_menu_day_and_week()
    
    # Filtrar órdenes en el rango de tiempo actual
    recent_orders = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lt=end_date
    ).order_by('-order_date')
    
    total_orders = recent_orders.count()
    
    print(f"DEBUG: Total de órdenes encontradas: {total_orders}")
    for order in recent_orders[:5]:  # Mostrar las primeras 5 para debug
        print(f"DEBUG: Orden {order.id} - Usuario: {order.user.username} - Fecha: {order.order_date}")

    # Validar si el usuario ya realizó un pedido en este rango
    has_existing_order = recent_orders.filter(user=request.user).exists()

    # Obtener el último pedido de cada usuario en el período
    latest_orders_by_user = {}
    for order in recent_orders:
        user_id = order.user_id
        if user_id not in latest_orders_by_user:
            latest_orders_by_user[user_id] = order

    # Marcar pedidos automáticos
    for order in recent_orders:
        user_id = order.user_id
        is_latest_for_user = latest_orders_by_user.get(user_id) == order
        order.show_auto = is_latest_for_user and order.repeat_for_week

    show_superuser_warning = request.user.is_superuser and has_existing_order

    return render(request, 'ruralapp.html', {
        'orders': recent_orders,
        'total_orders': total_orders,
        'show_superuser_warning': show_superuser_warning,
    })

@login_required
@never_cache
def ruralapp_orders_partial(request):
    start_date, end_date = calculate_time_range()

    recent_orders = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lt=end_date
    ).order_by('-order_date')

    # Determinar últimos por usuario y flag show_auto igual que en ruralapp
    latest_orders_by_user = {}
    for order in recent_orders:
        uid = order.user_id
        if uid not in latest_orders_by_user:
            latest_orders_by_user[uid] = order
    for order in recent_orders:
        uid = order.user_id
        order.show_auto = (latest_orders_by_user.get(uid) == order) and order.repeat_for_week

    html = render(request, 'ruralapp/_orders_table_body.html', {'orders': recent_orders}).content.decode('utf-8')
    return JsonResponse({
        'html': html,
        'total': recent_orders.count(),
    })

@login_required
def order_view(request):
    start_date, end_date = calculate_time_range()

    # Verificar si el usuario ya hizo un pedido hoy (excepto admins/superusuarios)
    if not request.user.is_superuser:
        user_orders = Order.objects.filter(
            user=request.user,
            order_date__range=(start_date, end_date)
        )
        if user_orders.exists():

            url = reverse('ruralapp') + '?pedido_existente=1'
            return HttpResponseRedirect(url)


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
        repeat_for_week = request.POST.get('repeat_for_week') == 'on'

        # Desactivar repetición en otros pedidos
        if repeat_for_week:
            Order.objects.filter(user=request.user, repeat_for_week=True).update(repeat_for_week=False)

        # Obtener objetos relacionados
        salad = Salad.objects.filter(id=salad_id).first() if salad_id else None
        other_dish = OtherDish.objects.filter(id=other_dish_id).first() if other_dish_id else None
        side_dish = SideDish.objects.filter(id=side_dish_id).first() if side_dish_id else None

        # Crear y validar pedido
        order = Order(
            user=request.user,
            main_dish=main_dish or None,
            salad=salad,
            other_dish=other_dish,
            side_dish=side_dish,
            comments=comments,
            repeat_for_week=repeat_for_week
        )

        try:
            order.full_clean()
            order.save()
            return JsonResponse({'success': True, 'message': 'Pedido registrado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Validar que solo se puedan editar pedidos del rango de tiempo actual
    start_date, end_date = calculate_time_range()
    if not (start_date <= order.order_date <= end_date):
        return JsonResponse({'success': False, 'error': 'No puedes editar pedidos fuera del rango de tiempo permitido.'})


    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        side_dish_id = request.POST.get('side_dish')
        comments = request.POST.get('comments', '')
        repeat_for_week = 'repeat_for_week' in request.POST

        # Desactivar repetición en otros pedidos
        if repeat_for_week:
            Order.objects.filter(user=request.user, repeat_for_week=True).exclude(pk=order.pk).update(repeat_for_week=False)

        # Actualizar campos
        order.main_dish = main_dish or None
        order.salad = Salad.objects.filter(id=salad_id).first() if salad_id else None
        order.other_dish = OtherDish.objects.filter(id=other_dish_id).first() if other_dish_id else None
        order.side_dish = SideDish.objects.filter(id=side_dish_id).first() if side_dish_id else None
        order.comments = comments
        order.repeat_for_week = repeat_for_week

        try:
            order.full_clean()
            order.save()
            return JsonResponse({'success': True, 'message': 'Pedido actualizado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Datos para el formulario
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

    return render(request, 'edit_order.html', {
        'order': order,
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'side_dishes': side_dishes,
        'dessert': dessert,
    })

# @login_required
# def edit_order(request, order_id):
#     menu_day_name, displayed_week = get_menu_day_and_week()
    
#     try:
#         daily_menu = WeeklyMenu.objects.get(week=displayed_week, day=menu_day_name)
#         main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
#         dessert = daily_menu.dessert
#     except WeeklyMenu.DoesNotExist:
#         main_dishes = []
#         dessert = "No disponible"

#     salads = Salad.objects.all()
#     other_dishes = OtherDish.objects.values('id', 'name', 'plus_side')
#     side_dishes = SideDish.objects.all()

#     order = get_object_or_404(Order, id=order_id, user=request.user)

#     # Buscar la orden original si la orden actual es una copia generada por Celery
#     original_order = Order.objects.filter(user=request.user, repeat_for_week=True).first()
#     if original_order and order.order_date != original_order.order_date:
#         order = original_order  # Editar la orden original en lugar de la copia del día

#     if request.method == 'POST':
#         main_dish = request.POST.get('main_dish')
#         salad_id = request.POST.get('salad')
#         other_dish_id = request.POST.get('other_dish')
#         side_dish_id = request.POST.get('side_dish')
#         comments = request.POST.get('comments', '')

#         # Manejo del checkbox repeat_for_week
#         repeat_for_week = 'repeat_for_week' in request.POST  

#         # Evitar múltiples órdenes repetitivas
#         if repeat_for_week:
#             # Si hay otra orden con repeat_for_week=True y no es la actual, desactivarla
#             Order.objects.filter(user=request.user, repeat_for_week=True).exclude(id=order.id).update(repeat_for_week=False)

#         order.repeat_for_week = repeat_for_week
#         order.main_dish = main_dish
#         order.salad = Salad.objects.get(id=salad_id) if salad_id else None
#         order.other_dish = OtherDish.objects.get(id=other_dish_id) if other_dish_id else None
#         order.side_dish = SideDish.objects.get(id=side_dish_id) if side_dish_id else None
#         order.comments = comments
#         order.save()

#         return JsonResponse({'success': True})

#     return render(request, 'edit_order.html', {
#         'order': order,
#         'main_dishes': main_dishes,
#         'salads': salads,
#         'other_dishes': other_dishes,
#         'side_dishes': side_dishes,
#         'dessert': dessert,
#         'menu_day_name': menu_day_name
#     })



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

