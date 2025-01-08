from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError  # Importar ValidationError

class AppState(models.Model):
    id = models.AutoField(primary_key=True)
    current_week = models.IntegerField(default=1)  # Semana actual en el ciclo de 4 semanas
    last_week_advance = models.DateTimeField(null=True, blank=True)  # Última vez que se avanzó la semana
    
class Salad(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class OtherDish(models.Model):
    name = models.CharField(max_length=100)
    plus_side = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class SideDish(models.Model):
    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class WeeklyMenu(models.Model):
    DAYS_OF_WEEK = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    week = models.IntegerField()
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    main_dish_1 = models.CharField(max_length=100)
    main_dish_2 = models.CharField(max_length=100)
    dessert = models.CharField(max_length=100)

    def __str__(self):
        return f"Semana {self.week} - {self.day}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True, db_index=True)  # Índice agregado
    main_dish = models.CharField(max_length=100, blank=True, null=True)
    salad = models.ForeignKey(Salad, on_delete=models.SET_NULL, null=True, blank=True)
    other_dish = models.ForeignKey(OtherDish, on_delete=models.SET_NULL, null=True, blank=True)
    side_dish = models.ForeignKey(SideDish, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(blank=True)
    extra_requests = models.TextField(blank=True)

    def __str__(self):
        return f"Pedido de {self.user.username} el {self.order_date.strftime('%Y-%m-%d %H:%M:%S')}"

    def clean(self):
        if not self.main_dish and not self.salad and not self.other_dish:
            raise ValidationError('Debe seleccionar al menos un plato principal, una ensalada o un plato adicional.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class WhatsAppGroup(models.Model):
    name = models.CharField(max_length=100)
    group_id = models.CharField(max_length=100, unique=True)  # ID único del grupo
    phone_number = models.CharField(max_length=15)  # Número de teléfono asociado

    def __str__(self):
        return self.name

class GroupNotification(models.Model):
    group = models.ForeignKey(WhatsAppGroup, on_delete=models.CASCADE)
    message = models.TextField()
    send_date = models.DateTimeField(db_index=True)  # Índice agregado
    status = models.CharField(max_length=20, default='pending')  # 'pending', 'sent', 'failed'
    notification_type = models.CharField(max_length=20)  # 'reminder', 'order_summary', etc.

    def __str__(self):
        return f"Notification to {self.group.name} - {self.status}"
    
class EventLog(models.Model):
    event_type = models.CharField(max_length=50)  # 'notification', 'message_sent', etc.
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"