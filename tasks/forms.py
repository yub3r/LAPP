from django import forms
from .models import Task
from django.utils.safestring import mark_safe

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

    # model = Task
    # fields = ['location', 'zona', 'area', 'tarea']
    # tarea = forms.TypedMultipleChoiceField(
    # choices = TASK,
    # widget = forms.RadioSelect(attrs={'class': 'form-check-inline'})
    # )
