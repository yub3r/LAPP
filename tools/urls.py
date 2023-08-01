from django.urls import path, re_path
from tools import views


urlpatterns = [
    path('ejecutar_swd_script/', views.ejecutar_swd_script, name='ejecutar_swd_script'),
]