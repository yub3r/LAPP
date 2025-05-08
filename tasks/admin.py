from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from .models import Task, Guardia, Sorteo, HoraExtra
from datetime import datetime


class TaskResource(resources.ModelResource):
    class Meta:
        model = Task
        fields = ('user__username', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted')
        export_order = ('user__username', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted')
        widgets = {
            'created': {'format': '%d-%m-%Y %H:%M'},
            'datecompleted': {'format': '%d-%m-%Y %H:%M'},
        }

class TaskAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [TaskResource]
    list_display = ['user', 'location', 'zona', 'area', 'tarea', 'created', 'datecompleted']
    list_filter = ['user', 'tarea', 'created', 'datecompleted']


class GuardiaResource(resources.ModelResource):
    usuario1 = fields.Field(column_name='Técnico 1', attribute='usuario1__username')
    usuario2 = fields.Field(column_name='Técnico 2', attribute='usuario2__username')
    usuario3 = fields.Field(column_name='IT', attribute='usuario3__username')
    hora_inicio = fields.Field(column_name='Hora Inicio', attribute='hora_inicio')
    hora_fin = fields.Field(column_name='Hora Fin', attribute='hora_fin')
    total_horas = fields.Field(column_name='Total Horas', attribute='total_horas')

    class Meta:
        model = Guardia
        fields = ('usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'total_horas')
        export_order = ('fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'total_horas', 'usuario1', 'usuario2', 'usuario3')
        widgets = {
            'fecha_inicio': {'format': '%d-%m-%Y'},
            'fecha_fin': {'format': '%d-%m-%Y'},
        }

class GuardiaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [GuardiaResource]
    list_display = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin']
    list_filter = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin']

# Filtros personalizados para mes y año
class MonthFilter(admin.SimpleListFilter):
    title = 'Mes'
    parameter_name = 'mes'

    def lookups(self, request, model_admin):
        months = HoraExtra.objects.dates('fecha_inicio', 'month', order='DESC')
        return [(month.month, month.strftime('%B')) for month in months]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_inicio__month=self.value())
        return queryset


class YearFilter(admin.SimpleListFilter):
    title = 'Año'
    parameter_name = 'año'

    def lookups(self, request, model_admin):
        years = HoraExtra.objects.dates('fecha_inicio', 'year', order='DESC')
        return [(year.year, year.year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_inicio__year=self.value())
        return queryset


class HoraExtraResource(resources.ModelResource):
    usuario = fields.Field(column_name='Usuario', attribute='usuario__username')
    fecha_inicio = fields.Field(column_name='Fecha de Inicio', attribute='fecha_inicio')
    fecha_fin = fields.Field(column_name='Fecha de Fin', attribute='fecha_fin')
    hora_inicio = fields.Field(column_name='Hora de Inicio', attribute='hora_inicio')
    hora_fin = fields.Field(column_name='Hora de Fin', attribute='hora_fin')
    total_horas = fields.Field(column_name='Total Horas', attribute='total_horas')
    justificar = fields.Field(column_name='Justificación', attribute='justificar')

    class Meta:
        model = HoraExtra
        fields = ('usuario', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'total_horas', 'justificar')
        export_order = ('usuario', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'total_horas', 'justificar')
        widgets = {
            'fecha_inicio': {'format': '%d-%m-%Y'},
            'fecha_fin': {'format': '%d-%m-%Y'},
        }


class HoraExtraAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_classes = [HoraExtraResource]
    list_display = [
        'usuario', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 
        'total_horas', 'justificar', 'aprobado', 'feedback_admin'  # Campos adicionales
    ]
    list_filter = ['usuario', MonthFilter, YearFilter, 'aprobado']  # Filtro adicional para estado de aprobación
    search_fields = ['usuario__username', 'justificar', 'feedback_admin']
    fields = (
        'usuario', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 
        'total_horas', 'justificar', 'aprobado', 'feedback_admin'  # Campos adicionales en el formulario de detalle
    )




class SorteoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha')


admin.site.register(Task, TaskAdmin)
admin.site.register(Guardia, GuardiaAdmin)
admin.site.register(HoraExtra, HoraExtraAdmin)
admin.site.register(Sorteo, SorteoAdmin)
