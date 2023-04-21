from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields


from .models import Task, Guardia


class TaskResource(resources.ModelResource):

    class Meta:
        model = Task
        fields = ('user__username', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted')
        export_order = ('user__username', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted')
        widgets = {
                'created': {'format': '%d-%m-%Y %H:%M'},
                'datecompleted': {'format': '%d-%m-%Y %H:%M'},
                }


    
# Register your models here.
class TaskAdmin(ImportExportModelAdmin, admin.ModelAdmin):
  resource_classes = [TaskResource]
  list_display = ['user', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted']
  list_filter = ['user', 'tarea', 'created', 'datecompleted']


class GuardiaResource(resources.ModelResource):
    usuario1 = fields.Field(column_name='Técnico 1', attribute='usuario1__username')
    usuario2 = fields.Field(column_name='Técnico 2', attribute='usuario2__username')
    usuario3 = fields.Field(column_name='IT', attribute='usuario3__username')

    class Meta:
        model = Guardia
        fields = ('usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin')
        export_order = ('fecha_inicio', 'fecha_fin','usuario1', 'usuario2', 'usuario3') 
        widgets = {
                'fecha_inicio': {'format': '%d-%m-%Y'},
                'fecha_fin': {'format': '%d-%m-%Y'},
                }


class GuardiaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
  resource_classes = [GuardiaResource]
  list_display = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin']
  list_filter = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin']

admin.site.register(Task, TaskAdmin)
admin.site.register(Guardia, GuardiaAdmin)