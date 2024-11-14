from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from datetime import datetime, timedelta

class Guardia(models.Model):
    usuario1 = models.ForeignKey(User, related_name='usuario1', on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Tecnico 1'})
    usuario2 = models.ForeignKey(User, related_name='usuario2', on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Tecnico 2'})
    usuario3 = models.ForeignKey(User, related_name='usuario3', on_delete=models.CASCADE, limit_choices_to={'groups__name': 'IT'})
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField(default="16:00")
    hora_fin = models.TimeField(default="07:00")
    total_horas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def calcular_total_horas(self):
        # Crear datetime con fecha y hora de inicio y fin
        datetime_inicio = datetime.combine(self.fecha_inicio, self.hora_inicio)
        datetime_fin = datetime.combine(self.fecha_fin, self.hora_fin)

        # Si la hora de fin es menor que la de inicio, significa que pasa al siguiente día
        if datetime_fin <= datetime_inicio:
            datetime_fin += timedelta(days=1)

        # Calcular diferencia y convertir a horas
        diferencia = datetime_fin - datetime_inicio
        horas_totales = diferencia.total_seconds() / 3600
        return horas_totales

    def save(self, *args, **kwargs):
        # Calcular el total de horas antes de guardar
        self.total_horas = self.calcular_total_horas()
        super(Guardia, self).save(*args, **kwargs)


class Sorteo(models.Model):
    titulo = models.CharField(max_length=50)
    cantidad_ganadores = models.IntegerField(default=1)
    participantes = models.ManyToManyField(User)
    fecha = models.DateTimeField(auto_now_add=True)
    

class Ganador(models.Model):
    sorteo = models.ForeignKey(Sorteo, on_delete=models.CASCADE)
    ganador = models.ForeignKey(User, on_delete=models.CASCADE)



UBICACION = [
    ('M0', 'Modulo 0'),
    ('M1', 'Modulo 1'),
    ('M2', 'Modulo 2'),
    ('M3', 'Modulo 3'),
    ('M4', 'Modulo 4'),
    ('M5', 'Modulo 5'),
    ('CF1', 'Corta Fuego 1'),
    ('CF2', 'Corta Fuego 2'),
    ('CF3', 'Corta Fuego 3'),
    ('CF4', 'Corta Fuego 4'),
    ('CF5', 'Corta Fuego 5')
]

ZONAS = [
    ('A', 'Lado A'),
    ('B', 'Lado B')
]


TASK = [
    ('Sop', 'Soplado'),
    ('Asp', 'Aspirado'),
    ('Lav', 'Lavado'),
]

AREA = [
    ('PTAL', 'Parte alta'),
    ('PTBA', 'Parte baja'),
    ('PSCA', 'Pasillo caliente'),
    ('PSFR', 'Pasillo frio'),
    ('PSFI', 'Pasillo filtro'),
]


class Task(models.Model):
    galpon = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(choices=UBICACION, max_length=3)
    zona = models.CharField(choices=ZONAS, max_length=1, blank=True)
    area = models.CharField(choices=AREA, max_length=4, blank=True)
    tarea = models.CharField(choices=TASK, max_length=3, default=None)
    created = models.DateTimeField(auto_now_add=True)
    datecompleted = models.DateTimeField(null=True, blank=True)
    

    def __str__(self):
        return self.tarea + ' - ' + self.user.username


class CryptoPrice(models.Model):
    symbol = models.CharField(max_length=10)
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']




class HoraExtra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    total_horas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    justificar = models.TextField(max_length=500)
    aprobado = models.BooleanField(null=True, blank=True)  # True para aprobado, False para rechazado, None para pendiente
    feedback_admin = models.TextField(max_length=500, blank=True, null=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    def calcular_total_horas(self):
        datetime_inicio = datetime.combine(self.fecha_inicio, self.hora_inicio)
        datetime_fin = datetime.combine(self.fecha_fin, self.hora_fin)
        if datetime_fin <= datetime_inicio:
            datetime_fin += timedelta(days=1)
        diferencia = datetime_fin - datetime_inicio
        horas_totales = diferencia.total_seconds() / 3600
        return horas_totales

    def save(self, *args, **kwargs):
        # Calcula el total de horas si no está calculado
        self.total_horas = self.calcular_total_horas()

        # Si el estado de aprobación cambia, se actualiza la fecha_aprobacion
        if self.aprobado is not None and not self.fecha_aprobacion:
            self.fecha_aprobacion = datetime.now()

        super(HoraExtra, self).save(*args, **kwargs)