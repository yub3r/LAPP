from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class SwitchDeDistribucion(models.Model):
    nro_swd = models.IntegerField(primary_key=True, db_index=True, unique=True)
    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return f"SWD {self.nro_swd}"


class Rack(models.Model):
    nro_swd = models.ForeignKey(SwitchDeDistribucion, on_delete=models.CASCADE)
    nro_rack = models.IntegerField(unique=True)

    def __str__(self):
        return f"Rack {self.nro_rack}"


class SwitchDeAcceso(models.Model):
    nro_rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    portchannel = models.IntegerField()
    nro_swa = models.IntegerField()

    def __str__(self):
        # return f"Switch {self.nro_swa} - Po{self.portchannel}"
        return f" SWA {self.nro_swa} |Po{self.portchannel} "


class HistorialEjecucionSWD(models.Model):
    fecha_hora_ejecucion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nro_swd = models.ForeignKey(SwitchDeDistribucion, on_delete=models.CASCADE)
    accion = models.CharField(max_length=10)
    resultado = models.CharField(max_length=255)

    def __str__(self):
        return f"Switch: {self.nro_swd}, Acción: {self.accion}, Usuario: {self.usuario.username}, Resultado: {self.resultado}"

    class Meta:
        ordering = ['-fecha_hora_ejecucion']


class HistorialEjecucionSWA(models.Model):
    fecha_hora_ejecucion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nro_rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name="historial_nro_rack")
    portchannel = models.ForeignKey(SwitchDeAcceso, on_delete=models.CASCADE, related_name="historial_portchannel")
    accion = models.CharField(max_length=10)
    resultado = models.CharField(max_length=255)

    def __str__(self):
        return f"Rack: {self.nro_rack}, Acción: {self.accion}, Switch {self.nro_swa} - Po{self.portchannel}, Usuario: {self.usuario.username}, Resultado: {self.resultado}"

    class Meta:
        ordering = ['-fecha_hora_ejecucion']
