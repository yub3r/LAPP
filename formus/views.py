from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Form, Question, Answer, CompletedForm, FormImage, Vehiculo
# from .forms import
from datetime import date, timedelta
from django.core.cache import cache
from django.views.generic.base import RedirectView
import random, re, slack
from django.http import JsonResponse


@login_required
def formularios(request):
    return render(request, 'formularios.html')


FORMULARIO_NAME = 'Formulario 1'


TOKEN = 'xoxb-2569679174866-6651760390341-nXgxbFm3vJVs2eSq30Se0pZF'
client = slack.WebClient(TOKEN)



@login_required
def tijera_form(request):
    form = Form.objects.get(name=FORMULARIO_NAME)
    questions = Question.objects.filter(form=form)
    vehiculos = Vehiculo.objects.filter(tipo='EMOVIL')  # Filtrar solo los vehículos de tipo 'EMOVIL'
    if request.method == 'POST':
        observations = request.POST.get('observations')
        vehiculo_id = request.POST.get('vehiculo')
        vehiculo = Vehiculo.objects.get(patente_id=vehiculo_id)
        tiempo_uso_anterior = vehiculo.tiempo_uso  # Guardar el valor anterior de tiempo_uso
        tiempo_uso = int(request.POST.get('tiempo_uso'))
        vehiculo.tiempo_uso = tiempo_uso
        vehiculo.save()
        tiempo_uso_actual = vehiculo.tiempo_uso  # Obtener el valor actual de tiempo_uso desde el modelo
        tiempo_adicionado = round(tiempo_uso_actual - tiempo_uso_anterior)  # Calcular el tiempo que se ha añadido
        completed_form = CompletedForm.objects.create(user=request.user, form=form, vehiculo=vehiculo, observations=observations, tiempo_uso_actual=tiempo_uso, tiempo_adicionado=tiempo_adicionado)
        negative_answers = []

        for question in questions:
            response = request.POST.get(f'response-{question.id}')
            if response:
                Answer.objects.create(
                    completed_form=completed_form, question=question, response=response)
                if response == 'NO':
                    negative_answers.append(question.text)

        if negative_answers:
            client.chat_postMessage(
                channel='_notifi_lapp', 
                text="############################\n*Resumen de Formulario Completado*\n"
                    + timezone.localtime().strftime('%H:%M hs - %d de %B')
                    + "\n*Usuario:* "
                    + str(request.user)
                    + "\n\n*Preguntas respondidas NO:*\n"
                    + "\n".join(negative_answers)
                    + "\n" + "\n" + str(observations)
            )

        for f in request.FILES.getlist('images'):
            FormImage.objects.create(completed_form=completed_form, image=f)
        return redirect('formularios')
    return render(request, 'tijera_form.html', {'questions': questions, 'vehiculos': vehiculos})


@login_required
def completed_forms(request):
    form = Form.objects.get(name=FORMULARIO_NAME)
    completed_forms = CompletedForm.objects.filter(form=form).order_by('-timestamp')
    return render(request, 'completed_forms.html', {
        'completed_forms': completed_forms,
        'formulario_name': FORMULARIO_NAME
    })


@login_required
def detail_form(request, completed_form_id):
    completed_form = get_object_or_404(CompletedForm, id=completed_form_id)
    responses = Answer.objects.filter(completed_form=completed_form).order_by('question__id')
    vehiculo = completed_form.vehiculo  # obtener el vehículo asociado al formulario completado

    # Obtener el formulario completado anterior para el mismo vehículo
    try:
        completed_form_anterior = completed_form.get_previous_by_timestamp(vehiculo=vehiculo)
        tiempo_uso_anterior = completed_form_anterior.tiempo_uso_actual
    except CompletedForm.DoesNotExist:
        tiempo_uso_anterior = timedelta(0)  # Si no hay formulario completado anterior, usar 0 como tiempo de uso anterior

    return render(request, 'detail_form.html', {'completed_form': completed_form, 'responses': responses, 'vehiculo': vehiculo, 'tiempo_uso_anterior': tiempo_uso_anterior})