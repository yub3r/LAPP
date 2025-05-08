from django.urls import include, path, re_path
from formus import views


urlpatterns = [
    path('formus/', views.formularios, name='formularios'),
    path('tijera_form/', views.tijera_form, name='tijera_form'),
    path('completed_forms/', views.completed_forms, name='completed_forms'),
    path('detail_form/<int:completed_form_id>/', views.detail_form, name='detail_form'),
    # path('get_vehiculo_tiempo_uso/', views.get_vehiculo_tiempo_uso, name='get_vehiculo_tiempo_uso'),
]