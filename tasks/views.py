from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, CryptoPrice, Guardia
from .forms import TaskForm, GuardiaForm
import ccxt
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
    return user.is_authenticated and user.is_staff

def sobremi(request):
    return render(request, "about.html")


########################  GUARDIAS  ######################################################  GUARDIAS  ##############################

@login_required
def reservar_guardia(request):
    if request.method == 'POST':
        form = GuardiaForm(request.POST)
        if form.is_valid():
            guardia = form.save(commit=False)
            guardia.save()
            # redirigir a la lista de guardias reservadas
            return redirect('guardias')
    else:
        form = GuardiaForm()
    return render(request, 'reservar_guardia.html', {'form': form})


@login_required
def guardias(request):
    guardia = Guardia.objects.all()
    return render(request, 'guardias.html', {"form": guardia})

@user_passes_test(es_admin)
def eliminar_guardia(request, guardia_id):
    guardia = get_object_or_404(Guardia, id=guardia_id)
    guardia.delete()
    return redirect('guardias')

@user_passes_test(es_admin)
def actualizar_guardia(request, pk):
    guardia = get_object_or_404(Guardia, pk=pk)
    if request.method == 'POST':
        form = GuardiaForm(request.POST, instance=guardia)
        if form.is_valid():
            form.save()
            # redirigir a la lista de guardias reservadas
            return redirect('guardias')
    else:
        form = GuardiaForm(instance=guardia)
    return render(request, 'actualizar_guardia.html', {'form': form, 'guardia': guardia})


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
        return redirect('crypto_prices')


# def home(request):
#     crypto_prices_data = crypto_prices(request)
#     return render(request, "home.html")

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

# def bitcoin_price(request):
#     plot_html = cache.get('plot_html')
#     if plot_html is not None:
#         return render(request, 'home.html', {'plot_html': plot_html})

#     exchange = ccxt.binance()
#     symbol = 'BTC/USD'
#     timeframe = '1d'
#     candles = exchange.fetch_ohlcv(symbol, timeframe)
#     dates = [candle[0] for candle in candles]
#     prices = [candle[4] for candle in candles]


#     fig, ax = plt.subplots(figsize=(300/80, 200/80), dpi=130)
#     ax.plot(dates, prices)
#     # ax.set(xlabel='Date', ylabel='Price (USD)', title='Bitcoin Price in the Last 24 Hours')
#     plt.xticks([], [])

#     plt.tight_layout()

#     plot_html = mpld3.fig_to_html(fig)
#     cache.set('plot_html', plot_html, 14400)

#     return render(request, 'home.html', {'plot_html': plot_html})



########################  Crypto_Prices  ######################################################  Crypto_Prices  ##############################


@login_required
def crypto_prices(request):
    prices = cache.get('prices')
    if prices is not None:
        return render(request, 'home.html', {'prices': prices})

    #count_tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True).count()

    exchange = ccxt.binance()
    symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 'DOT/USD']
    prices = {}
    for symbol in symbols:
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        prices[symbol] = {'price': price}

        # Check if previous price exists in the database
        previous_price = CryptoPrice.objects.filter(symbol=symbol).first()
        if previous_price:
            prices[symbol]['previous_price'] = previous_price.price
        else:
            prices[symbol]['previous_price'] = 0

        # Save the current price to the database
        CryptoPrice.objects.create(symbol=symbol, price=price)

    cache.set('prices', prices, 3600)

    # return render(request, 'home.html', {'prices': prices, 'count_tasks': count_tasks})
    return render(request, 'home.html', {'prices': prices})
    # return redirect('home', {'prices': prices}, {"count_tasks": count_tasks})