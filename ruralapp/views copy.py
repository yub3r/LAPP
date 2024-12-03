from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from collections import defaultdict
from .models import Salad, OtherDish, WeeklyMenu, Order
from datetime import datetime, time, timedelta
import json



@login_required
def ruralapp(request):
    return render(request, 'ruralapp.html')


@login_required
def mis_ordenes(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'misordenes.html', {'orders': orders})


@login_required
def order_view(request):
    # Obtener la fecha y hora actual
    now = timezone.now()

    # Definir los límites de tiempo (13:00 de hoy hasta 08:00 de mañana)
    start_time = timezone.make_aware(datetime.combine(now.date(), time(13, 0)))  # 13:00 hoy
    end_time = timezone.make_aware(datetime.combine(now.date() + timedelta(days=1), time(8, 0)))  # 08:00 mañana

    # Verificar si estamos dentro del tiempo permitido
    if not (start_time <= now <= end_time):
        # Fuera del horario permitido
        return JsonResponse({'success': False, 'error': "No puedes hacer o modificar pedidos en este horario. El horario es de 13:00 a 08:00."})

    # Obtener el día actual
    today = timezone.now().date()

    # Calcular el nombre del día actual (en español)
    days_of_week = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    day_name = days_of_week[today.weekday()]

    # Calcular el número de semana basado en el inicio de la aplicación
    start_week = 2  # Puedes cambiarlo según la semana de inicio
    current_week = ((today.isocalendar()[1] - 1) % 4) + start_week

    if current_week > 4:
        current_week = current_week % 4

    # Obtener el menú del día actual
    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
        dessert = daily_menu.dessert
    except WeeklyMenu.DoesNotExist:
        main_dishes = []
        dessert = "No disponible"

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.all()

    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        comments = request.POST.get('comments', '')

        if not main_dish and not salad_id and not other_dish_id:
            return JsonResponse({'success': False, 'error': "Debe seleccionar al menos un plato principal, una ensalada o un plato adicional."})

        # Crear y guardar la orden
        order = Order(
            user=request.user,
            main_dish=main_dish,
            salad=Salad.objects.get(id=salad_id) if salad_id else None,
            other_dish=OtherDish.objects.get(id=other_dish_id) if other_dish_id else None,
            comments=comments
        )
        order.save()

        return JsonResponse({'success': True})

    return render(request, 'order.html', {
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
        'dessert': dessert
    })


@login_required
def edit_order(request, order_id):
    # Obtener la fecha y hora actual
    now = timezone.now()

    # Definir los límites de tiempo (13:00 de hoy hasta 08:00 de mañana)
    start_time = timezone.make_aware(datetime.combine(now.date(), time(13, 0)))  # 13:00 hoy
    end_time = timezone.make_aware(datetime.combine(now.date() + timedelta(days=1), time(8, 0)))  # 08:00 mañana

    # Verificar si estamos dentro del tiempo permitido
    if not (start_time <= now <= end_time):
        # Fuera del horario permitido
        return JsonResponse({'success': False, 'error': "No puedes hacer o modificar pedidos en este horario. El horario es de 13:00 a 08:00."})

    order = get_object_or_404(Order, id=order_id, user=request.user)

    today = timezone.now().date()
    days_of_week = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    day_name = days_of_week[today.weekday()]
    start_week = 2
    current_week = ((today.isocalendar()[1] - 1) % 4) + start_week
    if current_week > 4:
        current_week = current_week % 4

    try:
        daily_menu = WeeklyMenu.objects.get(week=current_week, day=day_name)
        main_dishes = [daily_menu.main_dish_1, daily_menu.main_dish_2]
    except WeeklyMenu.DoesNotExist:
        main_dishes = []

    salads = Salad.objects.all()
    other_dishes = OtherDish.objects.all()

    if request.method == 'POST':
        main_dish = request.POST.get('main_dish')
        salad_id = request.POST.get('salad')
        other_dish_id = request.POST.get('other_dish')
        comments = request.POST.get('comments')
        order.main_dish = main_dish

        try:
            order.salad = Salad.objects.get(id=salad_id) if salad_id else None
        except Salad.DoesNotExist:
            order.salad = None

        try:
            order.other_dish = OtherDish.objects.get(id=other_dish_id) if other_dish_id else None
        except OtherDish.DoesNotExist:
            order.other_dish = None
        order.comments = comments
        order.save()
        return redirect('mis_ordenes')

    return render(request, 'edit_order.html', {
        'order': order,
        'main_dishes': main_dishes,
        'salads': salads,
        'other_dishes': other_dishes,
    })


@login_required
def ordenes_24hs(request):
    # Obtener la fecha y hora actual
    now = timezone.now()
    # Calcular la fecha y hora de hace 24 horas
    last_24_hours = now - datetime.timedelta(hours=24)
    # Filtrar las órdenes realizadas en las últimas 24 horas
    recent_orders = Order.objects.filter(order_date__gte=last_24_hours).order_by('-order_date')
    return render(request, '24hs_ordenes.html', {'orders': recent_orders})


@login_required
def resumen_pedidos(request):
    # Obtener la fecha y hora actual
    now = timezone.now()
    last_24_hours = now - datetime.timedelta(hours=24)
    
    # Obtener el nombre del día actual
    days_of_week = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    current_day = days_of_week[now.weekday()]

    # Filtrar las órdenes realizadas en las últimas 24 horas
    orders = Order.objects.filter(order_date__gte=last_24_hours)

    # Agrupar los pedidos por combinación de plato principal, ensalada y plato extra
    order_summary = defaultdict(lambda: {'count': 0, 'comments': []})
    
    for order in orders:
        key = (
            order.main_dish or 'N/A', 
            f"Ensalada {order.salad.id}" if order.salad else 'N/A', 
            order.other_dish.name if order.other_dish else 'N/A'
        )
        order_summary[key]['count'] += 1
        if order.comments:
            order_summary[key]['comments'].append(order.comments)

    # Convertir el resumen en una lista ordenada
    summary_list = []
    for key, value in order_summary.items():
        main_dish, salad, other_dish = key
        summary_list.append({
            'main_dish': main_dish,
            'salad': salad,
            'other_dish': other_dish,
            'count': value['count'],
            'comments': value['comments'],
        })

    # Renderizar el resumen en la plantilla
    return render(request, 'resumen_pedidos.html', {
        'summary_list': summary_list,
        'current_day': current_day,  # Pasar el día actual a la plantilla
    })



def generar_resumen_whatsapp():
    # Obtener la fecha y hora actual
    now = timezone.now()
    last_24_hours = now - datetime.timedelta(hours=24)

    # Filtrar las órdenes realizadas en las últimas 24 horas
    orders = Order.objects.filter(order_date__gte=last_24_hours)

    # Diccionario para agrupar y contar las órdenes
    resumen = defaultdict(lambda: {'count': 0, 'comments': []})

    for order in orders:
        key = (
            order.main_dish or 'N/A',
            f"Ensalada {order.salad.id}" if order.salad else 'N/A',
            order.other_dish.name if order.other_dish else 'N/A'
        )
        resumen[key]['count'] += 1
        if order.comments:
            resumen[key]['comments'].append(order.comments)

    # Crear la estructura del mensaje de WhatsApp
    whatsapp_message = "*Resumen de Pedidos*\n"
    total_orders = 0

    # Formatear cada entrada del resumen
    for key, value in resumen.items():
        main_dish, salad, other_dish = key
        count = value['count']
        comments = " / ".join(value['comments']) if value['comments'] else ''
        total_orders += count

        # Agregar la orden al mensaje
        whatsapp_message += f"{count:02d} - {main_dish} / {salad if salad != 'N/A' else ''} {other_dish if other_dish != 'N/A' else ''} / {comments}\n"

    # Agregar el total de órdenes al final
    whatsapp_message += f"*{total_orders}* - Ordenes para hoy {now.strftime('%A')}.\n"
    
    return whatsapp_message
