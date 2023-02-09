from django.db import models
from django.contrib.auth.models import User



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
    #title = models.CharField(max_length=200)
    galpon = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(choices=UBICACION, max_length=3)
    zona = models.CharField(choices=ZONAS, max_length=1, blank=True)
    area = models.CharField(choices=AREA, max_length=4, blank=True)
    tarea = models.CharField(choices=TASK, max_length=3)
    created = models.DateTimeField(auto_now_add=True)
    datecompleted = models.DateTimeField(null=True, blank=True)
    

    def __str__(self):
        return self.tarea + ' - ' + self.user.username