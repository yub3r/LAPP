from django.urls import include, path, re_path
from tools import views


urlpatterns = [
    path('ejecutar_swd_script/', views.ejecutar_swd_script, name='ejecutar_swd_script'),
    path('ejecutar_swa_script/', views.ejecutar_swa_script, name='ejecutar_swa_script'),
    path('ejecutar_swcore_script/', views.ejecutar_swcore_script, name='formulario_swcore_script'),
    path('cargar_racks/', views.cargar_racks, name='cargar_racks'),
    path('cargar_switches_acceso/', views.cargar_switches_acceso, name='cargar_switches_acceso'),
    path('cdp_nbr.html', views.cdp_neighbors_view, name='cdp_nbr'),
    # path("__debug__/", include("debug_toolbar.urls")),
]