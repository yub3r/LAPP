from django.contrib import admin
from .models import Task
from import_export import resources
from import_export.admin import ImportExportModelAdmin


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


admin.site.register(Task, TaskAdmin)