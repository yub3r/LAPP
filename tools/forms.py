
from django import forms
from django.contrib.auth.models import User
from .models import SwitchDeDistribucion, Rack, SwitchDeAcceso


class SWDScriptForm(forms.Form):
    nro_swd = forms.ChoiceField(
        choices=[('', 'Elija un SWD')] + [(swd.nro_swd,
                                           f"SWD {swd.nro_swd}") for swd in SwitchDeDistribucion.objects.all()],
        label="Switch de Distribución",
        widget=forms.Select(attrs={'id': 'nro_swd'}),
        required=True
    )

    accion = forms.ChoiceField(
        label="",
        choices=[("encender", "Encender Interfaces"),
                 ("apagar", "Apagar Interfaces")],
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
        required=True,
        error_messages={
            'required': 'Debe seleccionar una acción.'  # Mensaje de error personalizado
        }
    )


class SWAScriptForm(forms.Form):
    exclude = ['rack']

    nro_swd = forms.ChoiceField(
        choices=[('', 'Elija un SWD')] + [(swd.nro_swd, f"SWD {swd.nro_swd}") for swd in SwitchDeDistribucion.objects.all()],
        label="Switch de Distribución",
        widget=forms.Select(attrs={'id': 'nro_swd'}),
        required=True
    )

    rack = forms.ModelChoiceField(
        queryset=Rack.objects.none(),  # Inicialmente vacío
        label="Rack",
        widget=forms.Select(attrs={'id': 'rack'}),
        required=True
    )

    switches_de_acceso = forms.ModelMultipleChoiceField(
        queryset=SwitchDeAcceso.objects.none(),  # Inicialmente vacío
        label="Switches de Acceso",
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'switches-de-acceso'}),
        required=True
    )

    portchannels_swa = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )


    accion = forms.ChoiceField(
        label="",
        choices=[("encender", "Encender Interfaces"),
                 ("apagar", "Apagar Interfaces")],
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
        required=True,
        error_messages={
            'required': 'Debe seleccionar una acción.'  # Mensaje de error personalizado
        }
    )
