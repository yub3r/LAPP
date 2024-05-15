from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from .models import Form, Question, Answer, CompletedForm, FormImage, Vehiculo


class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['patente_id', 'tipo', 'marca_modelo', 'kilometraje_km', 'tiempo_uso_tiempo', 'operativo']
    list_filter = ['tipo']

    def kilometraje_km(self, obj):
        return obj.kilometraje
    kilometraje_km.short_description = 'KM'
    
    def tiempo_uso_tiempo(self, obj):
        return obj.tiempo_uso
    tiempo_uso_tiempo.short_description = 'T Uso' 

class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')   

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text','is_priority',)
    list_filter = ('is_priority',)

class AnswerAdmin(admin.ModelAdmin):
    list_display = ['completed_form', 'question', 'response']
    list_filter = ['completed_form', 'question', 'response']

class CompletedFormAdmin(admin.ModelAdmin):
    list_display = ['user', 'form', 'timestamp', 'observations']
    list_filter = ['user', 'form', 'timestamp']

class FormImageAdmin(admin.ModelAdmin):
    list_display = ['completed_form', 'image']

admin.site.register(Form, FormAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(CompletedForm, CompletedFormAdmin)
admin.site.register(FormImage, FormImageAdmin)
admin.site.register(Vehiculo, VehiculoAdmin)