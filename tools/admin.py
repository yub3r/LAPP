from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
# from .models import HistorialEjecucionSWD, HistorialEjecucionSWA, SwitchDeAcceso, SwitchDeDistribucion, Rack
from .models import HistorialEjecucionSWD, HistorialEjecucionSWA, SwitchDeAcceso, SwitchDeDistribucion, Rack, SwitchCore, GrupoVLAN, HistorialEjecucionSWCore


class HistorialEjecucionSWCoreAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora_ejecucion', 'usuario', 'switch_core', 'grupo_vlan', 'accion', 'resultado')

class HistorialEjecucionSWDAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora_ejecucion',  'usuario', 'nro_swd', 'accion', 'resultado')

class HistorialEjecucionSWAAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora_ejecucion',  'usuario', 'nro_rack', 'portchannel', 'accion', 'resultado')

class SwitchCoreAdmin(admin.ModelAdmin):
    list_display = ('nro_swc', 'ip')

class GrupoVLANAdmin(admin.ModelAdmin):
    list_display = ('nombre_grupo', 'vlans', 'switch_core')

class SwitchDeDistribucionAdmin(admin.ModelAdmin):
    list_display = ('ip', 'nro_swd')

class SwitchDeAccesoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['nro_rack', 'portchannel', 'nro_swa']
    list_filter = ['nro_rack', 'portchannel', 'nro_swa']

class RackAdmin(admin.ModelAdmin):
    list_display = ('nro_swd', 'nro_rack') 

admin.site.register(HistorialEjecucionSWD, HistorialEjecucionSWDAdmin)
admin.site.register(HistorialEjecucionSWA, HistorialEjecucionSWAAdmin)
admin.site.register(HistorialEjecucionSWCore, HistorialEjecucionSWCoreAdmin)
admin.site.register(SwitchDeDistribucion, SwitchDeDistribucionAdmin)
admin.site.register(SwitchDeAcceso, SwitchDeAccesoAdmin)
admin.site.register(SwitchCore, SwitchCoreAdmin)
admin.site.register(GrupoVLAN, GrupoVLANAdmin)
admin.site.register(Rack, RackAdmin)