from django import forms
from .models import Task, Guardia, Sorteo
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe
from django.conf import settings
from django.forms import DateTimeField
from django.core.exceptions import ValidationError
from django.utils import timezone


TASK = [
    ('Sop', 'Soplado'),
    ('Asp', 'Aspirado'),
    ('Lav', 'Lavado'),
]


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['location', 'zona', 'area', 'tarea']
        widgets = {
        'tarea': forms.RadioSelect(attrs={'class': 'form-check-inline'}),
        }


class GuardiaForm(forms.ModelForm):
    usuario1 = forms.ModelChoiceField(queryset=User.objects.filter(
        groups__name='Tecnico 1'), label='Técnico 1')
    usuario2 = forms.ModelChoiceField(queryset=User.objects.filter(
        groups__name='Tecnico 2'), label='Técnico 2')
    usuario3 = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='IT'), label='IT')

    class Meta:
        model = Guardia
        fields = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin']
        widgets = {
            # 'fecha_inicio': forms.TextInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'dd/mm/yyyy', 'autocomplete': 'on'}),
            # 'fecha_fin': forms.TextInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'dd/mm/yyyy', 'autocomplete': 'off'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        
        if fecha_inicio and fecha_fin:
            # Comparar fecha de inicio con fecha de fin
            if fecha_inicio > fecha_fin:
                raise ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin.")
            
            # Verificar si ya existe una guardia reservada en las mismas fechas
            guardias_exist = Guardia.objects.filter(
                fecha_inicio__lte=fecha_fin, fecha_fin__gte=fecha_inicio).exclude(pk=self.instance.pk)
            
            if guardias_exist.exists():
                raise ValidationError(
                    "Ya existe una guardia reservada en esa fecha.")
            

class SorteoForm(forms.ModelForm):
    class Meta:
        model = Sorteo
        fields = ('titulo', 'cantidad_ganadores', 'participantes')
    
    participantes = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().exclude(id=1).order_by('username'),
        widget=forms.CheckboxSelectMultiple,
    )
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad_ganadores = cleaned_data.get('cantidad_ganadores')
        participantes = cleaned_data.get('participantes')
        if cantidad_ganadores and participantes and cantidad_ganadores > participantes.count():
            raise forms.ValidationError('El número de ganadores no puede ser mayor al número de participantes.')
        return cleaned_data

class RepetirSorteoForm(forms.Form):
    titulo = forms.CharField(max_length=50, label='Título del nuevo sorteo')
    cantidad_ganadores = forms.IntegerField(label='Cantidad de ganadores')

    def __init__(self, participantes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participantes'] = forms.ModelMultipleChoiceField(
            queryset=participantes,
            widget=forms.CheckboxSelectMultiple,
            label='Participantes'
        )

    def clean(self):
        cleaned_data = super().clean()
        cantidad_ganadores = cleaned_data.get('cantidad_ganadores')
        participantes = cleaned_data.get('participantes')
        if cantidad_ganadores and participantes and cantidad_ganadores > participantes.count():
            raise forms.ValidationError('El número de ganadores no puede ser mayor al número de participantes.')
        return cleaned_data