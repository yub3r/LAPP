from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangocrud.settings')

# Crear la aplicación Celery
app = Celery('djangocrud')

# Configuración adicional
app.conf.update(
    broker_connection_retry_on_startup=True  # Maneja la advertencia para futuras versiones de Celery
)

# Cargar configuración desde settings.py con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Detectar automáticamente tareas en las apps instaladas
app.autodiscover_tasks(['ruralapp'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
