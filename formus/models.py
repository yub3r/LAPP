from django.db import models
from django.contrib.auth.models import User

class Form(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_priority = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Vehiculo(models.Model):
    RESPONSE_CHOICES = [
        ('EMOVIL', 'Equipo Movil'),
        ('TRANSPORTE', 'Transporte'),
    ]
    
    patente_id = models.CharField(unique=True, max_length=10)
    tipo = models.CharField(max_length=50, choices=RESPONSE_CHOICES)
    serial = models.CharField(max_length=50)
    marca_modelo = models.CharField(max_length=50)
    kilometraje = models.IntegerField(default=0)
    tiempo_uso = models.IntegerField(default=0)  # Duración en minutos
    operativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patente_id} - {self.marca_modelo} - {self.tipo} - {self.operativo}"
    
    
class CompletedForm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null=True, blank=True)
    tiempo_uso_actual = models.IntegerField(blank=True, null=True)
    tiempo_adicionado = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    observations = models.TextField(max_length=1020)

    def __str__(self):
        return f"{self.user.username} - {self.form.name} - {self.timestamp}"

    def has_negative_answer(self):
        return self.answer_set.filter(response='NO').exists()


class FormImage(models.Model):
    completed_form = models.ForeignKey(CompletedForm, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/formus/', blank=True, null=True)

class Answer(models.Model):
    RESPONSE_CHOICES = [
        ('SI', 'Sí'),
        ('NO', 'No'),
        ('NA', 'No Aplica'),
    ]

    completed_form = models.ForeignKey(CompletedForm, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.CharField(max_length=2, choices=RESPONSE_CHOICES)

    def __str__(self):
        return f"{self.completed_form.user.username} - {self.question.text} - {self.response}"