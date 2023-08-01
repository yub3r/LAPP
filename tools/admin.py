from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from .models import HistorialEjecucionSWD


class HistorialEjecucionSWDAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora_ejecucion',  'usuario', 'num_switch', 'accion', 'resultado')

admin.site.register(HistorialEjecucionSWD, HistorialEjecucionSWDAdmin)