
from django import forms
from django.contrib.auth.models import User


class SWDScriptForm(forms.Form):
    num_switch = forms.IntegerField(
        label="Switch de Distribución número:",
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={'pattern': '[0-9]*'}),
    )

    accion = forms.ChoiceField(
        label="",
        choices=[("encender", "Encender Interfaces"), ("apagar", "Apagar Interfaces")],
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}), 
        required=False,
    )




# class SWDScriptForm(forms.Form):
#     num_switch = forms.IntegerField(label="Switch de Distribución número:", min_value=1, max_value=20)
#     accion = forms.ChoiceField(label="Acción a realizar", choices=[("encender", "Encender interfaces"), ("apagar", "Apagar interfaces")])