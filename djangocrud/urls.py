"""djangocrud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from tasks import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve 
from django.contrib.auth.decorators import user_passes_test

urlpatterns = [
    # path('', views.home, name='home'),
    # path('crypto-prices/', views.crypto_prices, name='crypto_prices'),
    path('', views.crypto_prices, name='crypto_prices'),
    #path('', include('pwa.urls')),
    # path('completed_tasks', views.completed_tasks, name='completed_tasks'),
    path("about", views.sobremi, name="About"),
    path('admin/', admin.site.urls, name="Admin"),
    path('signup/', views.signup, name='signup'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks_completed/', views.tasks_completed, name='tasks_completed'),
    path('all_tasks/', views.all_tasks, name='all_tasks'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('create_task/', views.create_task, name='create_task'),
    path('reservar_guardia/', user_passes_test(views.es_admin)(views.reservar_guardia), name='reservar_guardia'),
    path('guardias/', views.guardias, name='guardias'),
    path('eliminar_guardia/<int:guardia_id>/',  user_passes_test(views.es_admin)(views.eliminar_guardia), name='eliminar_guardia'),
    path('actualizar_guardia/<int:pk>/', user_passes_test(views.es_admin)(views.actualizar_guardia), name='actualizar_guardia'),
    path('last_task/', views.last_task, name='last_task'),
    path('tasks/<int:task_id>/complete', views.complete_task, name='complete_task'),
    #path('tasks/<int:task_id>', views.task_detail, name='task_detail'),
    #path('tasks/<int:task_id>/delete', views.delete_task, name='delete_task'),
    re_path(r'^favicon\.ico$', views.favicon_view),
    path('favicon.ico',RedirectView.as_view(url='/media/favicon.ico')),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
