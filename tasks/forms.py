from datetime import datetime
from django import forms
from django.db.models import Count
from .models import Task, Guardia, Sorteo, HoraExtra
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe
from django.conf import settings
from django.forms import DateTimeField, RadioSelect
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
    # Usuarios que pertenecen SOLO a Operaciones
    usuario1 = forms.ModelChoiceField(
        queryset=User.objects.annotate(group_count=Count('groups'))
                      .filter(groups__name='Operaciones', group_count=1),
        label='Operaciones'
    )
    
    # Usuarios que pertenecen SOLO a Mantenimiento
    usuario2 = forms.ModelChoiceField(
        queryset=User.objects.annotate(group_count=Count('groups'))
                      .filter(groups__name='Mantenimiento', group_count=1),
        label='Mantenimiento'
    )
    
    # Usuarios que pertenecen SOLO a IT
    usuario3 = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='IT'), label='IT')
        
    # Añadimos los campos de hora de inicio y hora de fin
    hora_inicio = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), initial="16:00", label='Hora de Inicio')
    hora_fin = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), initial="07:00", label='Hora de Fin')

    class Meta:
        model = Guardia
        fields = ['usuario1', 'usuario2', 'usuario3', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control'}),
        }

    # def __init__(self, *args, **kwargs):
    #     super(GuardiaForm, self).__init__(*args, **kwargs)
    #     self.fields['usuario3'].initial = User.objects.get(username='ymillan')

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")
        
        # Validar que la fecha de inicio no sea mayor a la fecha de fin
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")
            
            # Verificar si ya existe una guardia reservada en las mismas fechas
            guardias_exist = Guardia.objects.filter(
                fecha_inicio__lte=fecha_fin, fecha_fin__gte=fecha_inicio).exclude(pk=self.instance.pk)
            
            if guardias_exist.exists():
                raise ValidationError("Ya existe una guardia reservada en esa fecha.")

        # Validar que la hora de fin no sea menor que la hora de inicio si es el mismo día
        if fecha_inicio == fecha_fin and hora_inicio >= hora_fin:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio si es el mismo día.")
        
        return cleaned_data



class GroupCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        user = User.objects.get(id=value.value)  
        group = user.groups.first()
        if group:
            option['attrs']['data-group'] = group.name
        return option

class SorteoForm(forms.ModelForm):
    class Meta:
        model = Sorteo
        fields = ('titulo', 'cantidad_ganadores', 'participantes')

    participantes = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().exclude(username__in=['admin', 'Ingesa_01', 'Ingesa_02', 'Ingesa_03', 'aostanello']).order_by('first_name'),
        widget=GroupCheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['participantes'].label_from_instance = lambda obj: f'{obj.first_name} {obj.last_name}'

    
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
        field = forms.ModelMultipleChoiceField(
            queryset=participantes,
            widget=forms.CheckboxSelectMultiple,
            label='Participantes'
        )
        # Mostrar nombre completo
        field.label_from_instance = lambda obj: f'{obj.first_name} {obj.last_name}'.strip() or obj.username
        self.fields['participantes'] = field

    def clean(self):
        cleaned_data = super().clean()
        cantidad_ganadores = cleaned_data.get('cantidad_ganadores')
        participantes = cleaned_data.get('participantes')
        if cantidad_ganadores and participantes and cantidad_ganadores > participantes.count():
            raise forms.ValidationError('El número de ganadores no puede ser mayor al número de participantes.')
        return cleaned_data

    


class HoraExtraForm(forms.ModelForm):
    fecha_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    hora_inicio = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    hora_fin = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    justificar = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Justifique brevemente aquí...', 'rows': 3}),
        max_length=1020,
        required=True
    )
    porcent = forms.ChoiceField(
        choices=[('50%', '50%'), ('100%', '100%')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'})
    )

    class Meta:
        model = HoraExtra
        fields = ['fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'justificar', 'porcent']

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")

        if not all([fecha_inicio, fecha_fin, hora_inicio, hora_fin]):
            return cleaned_data

        datetime_inicio = datetime.combine(fecha_inicio, hora_inicio)
        datetime_fin = datetime.combine(fecha_fin, hora_fin)

        # Validación de fechas futuras
        if datetime_fin > datetime.now():
            raise ValidationError("No se pueden registrar horas extras en fechas futuras.")

        # Validación de superposición de horarios
        if self.usuario:
            horas_extras_existentes = HoraExtra.objects.filter(
                usuario=self.usuario,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            ).exclude(pk=self.instance.pk if self.instance.pk else None)  # Excluir la instancia actual en edición

            for registro in horas_extras_existentes:
                inicio_existente = datetime.combine(registro.fecha_inicio, registro.hora_inicio)
                fin_existente = datetime.combine(registro.fecha_fin, registro.hora_fin)

                if datetime_inicio < fin_existente and datetime_fin > inicio_existente:
                    raise ValidationError("El horario de horas extras se superpone con un registro existente.")

        # Validaciones adicionales (se mantienen igual)
        if fecha_inicio > fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior o igual a la fecha de fin.")

        if fecha_inicio == fecha_fin and hora_inicio >= hora_fin:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio si es el mismo día.")

        return cleaned_data