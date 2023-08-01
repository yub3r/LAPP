from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class HistorialEjecucionSWD(models.Model):
    fecha_hora_ejecucion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    num_switch = models.IntegerField()
    accion = models.CharField(max_length=10)
    resultado = models.CharField(max_length=255)

    def __str__(self):
        return f"Switch: {self.num_switch}, Acción: {self.accion}, Usuario: {self.usuario.username}, Resultado: {self.resultado}"

    
    class Meta:
        ordering = ['-fecha_hora_ejecucion']