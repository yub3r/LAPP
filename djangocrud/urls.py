from django.contrib import admin
from django.urls import path, re_path, include
from tasks import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve 
from django.contrib.auth.decorators import user_passes_test

urlpatterns = [
    path('', views.home_view, name='home'),
    path('tools/', include("tools.urls")),
    path('formus/', include("formus.urls")),
    # path('crypto-prices/', views.crypto_prices, name='crypto_prices'),
    # path('', views.crypto_prices, name='crypto_prices'),
    path("about", views.sobremi, name="About"),
    path('admin/', admin.site.urls, name="Admin"),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),

    path('create_task/', views.create_task, name='create_task'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks_completed/', views.tasks_completed, name='tasks_completed'),
    path('all_tasks/', views.all_tasks, name='all_tasks'),
    path('last_task/', views.last_task, name='last_task'),
    path('tasks/<int:task_id>/complete', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/delete', views.delete_task, name='delete_task'),

    path('reservar_guardia/', user_passes_test(views.es_admin)(views.reservar_guardia), name='reservar_guardia'),
    path('guardias/', views.guardias, name='guardias'),
    path('eliminar_guardia/<int:guardia_id>/',  user_passes_test(views.es_admin)(views.eliminar_guardia), name='eliminar_guardia'),
    path('actualizar_guardia/<int:pk>/', user_passes_test(views.es_admin)(views.actualizar_guardia), name='actualizar_guardia'),
    path('registrar-horas-extra/', views.registrar_horas_extra, name='registrar_horas_extra'),
    path('lista-horas-extra/', views.lista_horas_extra, name='lista_horas_extra'),
    path('eliminar-horas-extra/<int:id>/', views.eliminar_horas_extra, name='eliminar-horas_extra'),
    path('aprobar_rechazar_horas_extra/<int:id>/', views.aprobar_rechazar_horas_extra, name='aprobar_rechazar_horas_extra'),



    path('sorteo/', views.sorteo, name='sorteo'),
    path('historial/', views.historial_sorteos, name='historial_sorteos'),
    path('repetir-sorteo/<int:sorteo_id>/', views.repetir_sorteo, name='repetir_sorteo'),
    path('eliminar_sorteo/<int:sorteo_id>/',  user_passes_test(views.es_admin)(views.eliminar_sorteo), name='eliminar_sorteo'),

    re_path(r'^favicon\.ico$', views.favicon_view),
    path('favicon.ico',RedirectView.as_view(url='/media/favicon.ico')),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]