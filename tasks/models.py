from django.db import models
from django.contrib.auth.models import User


MODULOS = [
    ('M0', 'Modulo 0'),
    ('M1', 'Modulo 1'),
    ('M2', 'Modulo 2'),
    ('M3', 'Modulo 3'),
    ('M4', 'Modulo 4'),
    ('M5', 'Modulo 5')
]

ZONAS = [
    ('A', 'Lado A'),
    ('B', 'Lado B')
]

CF = [
    ('CF1', 'Corta Fuego 1'),
    ('CF2', 'Corta Fuego 2'),
    ('CF3', 'Corta Fuego 3'),
    ('CF4', 'Corta Fuego 4'),
    ('CF5', 'Corta Fuego 5')
]

TASK = [
    ('Sop', 'Soplado'),
    ('Asp', 'Aspirado'),
    ('Lav', 'Lavado'),
]


class Task(models.Model):
    #title = models.CharField(max_length=200)
    tarea = models.CharField(choices=TASK, max_length=3)
    galpon = models.IntegerField(default=1)
    modulo = models.CharField(choices=MODULOS, max_length=2, null=True, blank=True)
    zona = models.CharField(choices=ZONAS, max_length=1, null=True, blank=True)
    cortafuego = models.CharField(choices=CF, max_length=3, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    datecompleted = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.tarea + ' - ' + self.user.username