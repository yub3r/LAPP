from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum, F, Func, IntegerField
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, CryptoPrice, Guardia, Sorteo, Ganador, HoraExtra
from .forms import TaskForm, GuardiaForm, SorteoForm, RepetirSorteoForm, HoraExtraForm
from datetime import date, timedelta
from django.utils.timezone import now 
from django.http import JsonResponse
import ccxt, calendar, random, re, locale, requests
import yfinance as yf
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.views.generic.base import RedirectView



favicon_view = RedirectView.as_view(url='/media/favicon.ico', permanent=True)


def admin_o_ususario(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    try:
        user = user.objects.get(user=user.id)
    except ObjectDoesNotExist:
        user = None
    return user is not None


def es_admin(user):
    return user.is_authenticated and user.is_superuser

def sobremi(request):
    return render(request, "about.html")


########################  GUARDIAS  ######################################################  GUARDIAS  ##############################
@login_required
def registrar_horas_extra(request):
    horas_extras = HoraExtra.objects.filter(usuario=request.user).order_by('-fecha_inicio')

    if request.method == 'POST':
        form = HoraExtraForm(request.POST, usuario=request.user)  # Pasamos el usuario
        if form.is_valid():
            hora_extra = form.save(commit=False)
            hora_extra.usuario = request.user
            hora_extra.save()
            # messages.success(request, "Horas extras registradas correctamente.")
            return redirect('registrar_horas_extra')
        else:
            # Si hay errores en el formulario, agrega mensajes de error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error) 
                    print(f"Error en el campo '{field}': {error}")
    else:
        form = HoraExtraForm(usuario=request.user)  # Pasamos el usuario

    return render(request, 'registrar_horas_extra.html', {
        'form': form,
        'horas_extras': horas_extras,
    })

@user_passes_test(es_admin)
def lista_horas_extra(request):
    # Obtenemos el año actual
    current_year = now().year

    # Obtenemos todos los registros de horas extra
    horas_extras = HoraExtra.objects.all().order_by('-fecha_inicio')

    # Filtro para identificar registros que provienen de guardias
    horas_guardia = horas_extras.filter(es_guardia=True)

    return render(request, 'lista_horas_extra.html', {
        'horas_extras': horas_extras,
        'horas_guardia': horas_guardia,
    })

@login_required
def eliminar_horas_extra(request, id):
    if request.method == 'POST':
        hora_extra = get_object_or_404(HoraExtra, id=id, usuario=request.user)
        hora_extra.delete()
        return JsonResponse({'success': True, 'message': 'Registro de horas extras eliminado exitosamente.'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

@login_required
@user_passes_test(es_admin)
def aprobar_rechazar_horas_extra(request, id):
    hora_extra = get_object_or_404(HoraExtra, id=id)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        feedback = request.POST.get('feedback')
        
        if accion == 'aprobar':
            hora_extra.aprobado = True
        elif accion == 'rechazar':
            hora_extra.aprobado = False
        hora_extra.feedback_admin = feedback
        hora_extra.save()
        return redirect('lista_horas_extra')

@login_required
@user_passes_test(es_admin)
def horas_extras_aprobadas(request):
    horas_extras_aprobadas_rechazadas = HoraExtra.objects.filter(aprobado__isnull=False).order_by('-fecha_inicio')
    return render(request, 'horas_aprobadas.html', {
        'horas_extras': horas_extras_aprobadas_rechazadas,
    })

@login_required
@user_passes_test(es_admin)
def cargar_guardias_a_horas_extra(request):
    if request.method == "POST":
        fecha_limite = now().date() - timedelta(days=40)
        guardias_vencidas = Guardia.objects.filter(
            fecha_fin__lt=now().date(),
            fecha_fin__gte=fecha_limite
        )

        registros_cargados = 0
        for guardia in guardias_vencidas:
            usuarios = [guardia.usuario1, guardia.usuario2]

            for usuario in usuarios:
                if usuario:  # Validar si el usuario no es None
                    existe_registro = HoraExtra.objects.filter(
                        usuario=usuario,
                        fecha_inicio=guardia.fecha_inicio,
                        fecha_fin=guardia.fecha_fin,
                        hora_inicio=guardia.hora_inicio,
                        hora_fin=guardia.hora_fin,
                        justificar__icontains="Guardia",
                        es_guardia=True
                    ).exists()

                    if not existe_registro:
                        # Crear nuevo registro si no existe
                        HoraExtra.objects.create(
                            usuario=usuario,
                            fecha_inicio=guardia.fecha_inicio,
                            fecha_fin=guardia.fecha_fin,
                            hora_inicio=guardia.hora_inicio,
                            hora_fin=guardia.hora_fin,
                            total_horas=guardia.total_horas,
                            justificar=f"Guardia - {guardia.fecha_inicio.strftime('%b')}",
                            aprobado=None,
                            es_guardia=True,
                            porcent='25%'  # Asignar el valor por defecto de '25%'
                        )
                        registros_cargados += 1

        mensaje = f"Se han cargado {registros_cargados} nuevas guardias." if registros_cargados > 0 else "No se encontraron guardias nuevas para cargar."
        return JsonResponse({
            'success': True,
            'registros': registros_cargados,
            'mensaje': mensaje,
            'fecha_inicio': fecha_limite.strftime("%d/%m/%Y"),
            'fecha_fin': now().strftime("%d/%m/%Y")
        })

    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(es_admin)
def stats_horas(request):
    # Total de horas por mes/usuario y porcentaje
    horas_por_mes_usuario = []
    horas_extras = HoraExtra.objects.filter(aprobado=True)  # Solo registros aprobados

    for hora in horas_extras:
        anio_mes = f"{hora.fecha_inicio.year}/{hora.fecha_inicio.month:02d}"
        encontrado = next(
            (item for item in horas_por_mes_usuario
             if item['anio_mes'] == anio_mes and item['usuario'] == hora.usuario.username),
            None
        )
        if encontrado:
            encontrado['25%'] += hora.total_horas if hora.porcent == '25%' else 0
            encontrado['50%'] += hora.total_horas if hora.porcent == '50%' else 0
            encontrado['100%'] += hora.total_horas if hora.porcent == '100%' else 0
            encontrado['total_horas'] += hora.total_horas
        else:
            horas_por_mes_usuario.append({
                'anio_mes': anio_mes,
                'usuario': hora.usuario.username,
                '25%': hora.total_horas if hora.porcent == '25%' else 0,
                '50%': hora.total_horas if hora.porcent == '50%' else 0,
                '100%': hora.total_horas if hora.porcent == '100%' else 0,
                'total_horas': hora.total_horas,
            })

    # Total de horas por mes (sin agrupar por usuario ni porcentaje)
    horas_por_mes = []
    for hora in horas_extras:
        anio_mes = f"{hora.fecha_inicio.year}/{hora.fecha_inicio.month:02d}"
        encontrado = next((item for item in horas_por_mes if item['anio_mes'] == anio_mes), None)
        if encontrado:
            encontrado['total_horas'] += hora.total_horas
        else:
            horas_por_mes.append({
                'anio_mes': anio_mes,
                'total_horas': hora.total_horas,
            })

    return render(request, 'stats_horas.html', {
        'horas_por_mes_usuario': horas_por_mes_usuario,
        'horas_por_mes': horas_por_mes,
    })

@login_required
def reservar_guardia(request):
    if request.method == "POST":
        form = GuardiaForm(request.POST)
        if form.is_valid():
            # Crear la guardia
            guardia = form.save(commit=False)
            guardia.creador = request.user
            guardia.save()
            return redirect('guardias') 
    else:
        form = GuardiaForm()

    return render(request, 'reservar_guardia.html', {'form': form})

@login_required
def guardias(request):
    fecha_actual = date.today()
    fecha_limite = fecha_actual - timedelta(days=90)
    guardias = Guardia.objects.filter(fecha_inicio__gte=fecha_limite).order_by('fecha_inicio')
    
    fecha_proxima = None
    for guardia in guardias:
        if guardia.fecha_inicio >= fecha_actual:
            fecha_proxima = guardia.fecha_inicio
            break
            
    return render(request, 'guardias.html', {"form": guardias, "fecha_actual": fecha_actual, "fecha_proxima": fecha_proxima})

@login_required
def eliminar_guardia(request, guardia_id):
    guardia = get_object_or_404(Guardia, id=guardia_id)
    guardia.delete()
    return redirect('guardias')

@login_required
def actualizar_guardia(request, pk):
    guardia = get_object_or_404(Guardia, pk=pk)
    if request.method == 'POST':
        form = GuardiaForm(request.POST, instance=guardia)
        if form.is_valid():
            form.save()
            return redirect('guardias')
    else:
        form = GuardiaForm(instance=guardia)
    return render(request, 'actualizar_guardia.html', {'form': form, 'guardia': guardia})


########################  SORTEOS  ######################################################  SORTEOS  ##############################

@login_required
def sorteo(request):
    if request.method == 'POST':
        form = SorteoForm(request.POST)
        if form.is_valid():
            sorteo = form.save()
            ganadores = random.sample(list(sorteo.participantes.all()), min(sorteo.cantidad_ganadores, sorteo.participantes.count()))
            for ganador in ganadores:
                Ganador.objects.create(sorteo=sorteo, ganador=ganador)
            request.session['sorteo_id'] = sorteo.id

            # Si es una solicitud AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                ganadores_data = [{
                    'username': ganador.username,
                    'full_name': ganador.get_full_name()  # Incluir el nombre completo
                } for ganador in ganadores]
                return JsonResponse({'ganadores': ganadores_data})
            else:
                # Si no es AJAX, renderizar la plantilla como antes
                return render(request, 'sorteo.html', {'ganadores': ganadores})
    else:
        form = SorteoForm()
    return render(request, 'nuevo_sorteo.html', {'form': form, 'username': request.user.username})


@login_required
def historial_sorteos(request):
    sorteos = Sorteo.objects.prefetch_related('ganador_set').order_by('-fecha')[:20]
    historial = [
        {
            'sorteo': sorteo,
            'ganadores': [ganador.ganador.username for ganador in sorteo.ganador_set.all()]
        }
        for sorteo in sorteos
    ]
    return render(request, 'historial_sorteos.html', {'historial': historial})


@login_required
def repetir_sorteo(request, sorteo_id):
    sorteo = get_object_or_404(Sorteo, id=sorteo_id)
    participantes = sorteo.participantes.all()

    # Generar un título único
    titulo_original = sorteo.titulo
    i = 1
    while True:
        titulo = f"{titulo_original} ({i})" if i > 1 else titulo_original
        if not Sorteo.objects.filter(titulo=titulo).exists():
            break
        i += 1

    # Crear el formulario con el título único
    initial_data = {'titulo': titulo, 'cantidad_ganadores': sorteo.cantidad_ganadores, 'participantes': participantes}
    form = RepetirSorteoForm(participantes, request.POST or None, initial=initial_data)

    if request.method == 'POST':
        if form.is_valid():
            nuevo_sorteo = Sorteo.objects.create(
                titulo=form.cleaned_data['titulo'],
                cantidad_ganadores=form.cleaned_data['cantidad_ganadores']
            )
            nuevo_sorteo.participantes.set(form.cleaned_data['participantes'])
            ganadores = random.sample(list(nuevo_sorteo.participantes.all()), nuevo_sorteo.cantidad_ganadores)
            for ganador in ganadores:
                Ganador.objects.create(sorteo=nuevo_sorteo, ganador=ganador)

            # Si es una solicitud AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                ganadores_data = [{
                    'username': ganador.username,
                    'full_name': ganador.get_full_name()  # Incluir el nombre completo
                } for ganador in ganadores]
                return JsonResponse({'ganadores': ganadores_data})
            else:
                # Si no es AJAX, renderizar la plantilla como antes
                return render(request, 'sorteo.html', {'ganadores': ganadores})

    context = {'form': form, 'sorteo': sorteo, 'username': request.user.username}
    return render(request, 'repetir_sorteo.html', context)


@user_passes_test(es_admin)
def eliminar_sorteo(request, sorteo_id):
    sorteo = get_object_or_404(Sorteo, id=sorteo_id)
    sorteo.delete()
    return redirect('historial_sorteos')

########################  LOGIN  ######################################################  LOGIN  ##############################

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {"form": UserCreationForm})
    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"])
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {"form": UserCreationForm, "error": "Username ya existe."})
        return render(request, 'signup.html', {"form": UserCreationForm, "error": "Contraseña no coincide"})


@login_required
def signout(request):
    logout(request)
    return render(request, 'logout.html')
    # return redirect('home')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {"form": AuthenticationForm})
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {"form": AuthenticationForm, "error": "Usuario o contraseña incorrecta."})

        login(request, user)
        messages.success(request, f"Bienvenido {user}")
        # return render(request, 'home.html')
        return redirect('home')

@login_required
def home(request):
    return render(request, "home.html")

########################  TAREAS  ######################################################  TAREAS  ##############################

@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True)
    return render(request, 'tasks.html', {"tasks": tasks})


@login_required
def tasks_completed(request):
    tasks = Task.objects.filter(
        user=request.user, datecompleted__isnull=False).order_by('-datecompleted')
    return render(request, 'completed_tasks.html', {"tasks": tasks})


@login_required
def all_tasks(request):
    tasks = Task.objects.all()
    return render(request, 'all_tasks.html', {"tasks": tasks})


@login_required
def create_task(request):
    if request.method == "GET":
        return render(request, 'create_task.html', {"form": TaskForm, 'last_task': False})
    else:
        try:
            form = TaskForm(request.POST)
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            messages.success(request, "Tarea Creada")
            return redirect('tasks')
        except ValueError:
            return render(request, 'create_task.html', {"form": TaskForm, "error": "Error creando la tarea.", 'last_task': False})


@login_required
def task_detail(request, task_id):
    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id, user=request.user)
        form = TaskForm(instance=task)
        return render(request, 'task_detail.html', {'task': task, 'form': form})
    else:
        try:
            task = get_object_or_404(Task, pk=task_id, user=request.user)
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'task_detail.html', {'task': task, 'form': form, 'error': 'Error actualizando la tarea.'})


@login_required
def last_task(request):
    if request.method == "GET":
        task = Task.objects.filter(user=request.user).latest('id')
        form = TaskForm(instance=task)
        return render(request, template_name='create_task.html', context={'task': task, 'form': form, 'last_task': True})
    else:
        return render(request, 'create_task.html', {"form": TaskForm, 'last_task': True})


@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.datecompleted = timezone.now()
        task.save()
        messages.success(request, "Tarea Completada")
        return redirect('tasks_completed')


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('tasks')


########################  Crypto_Prices  ######################################################  Crypto_Prices  ##############################

@login_required
def home_view(request):
    """Vista principal que lee los datos ya cacheados."""
    current_price = cache.get('bitf_price')
    dolar_data = cache.get('dolar_data')
    
    return render(request, 'home.html', {
        'bitf_price': current_price,
        'dolar_data': dolar_data
    })