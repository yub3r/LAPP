
from django import forms
from django.contrib.auth.models import User
from .models import SwitchDeDistribucion, Rack, SwitchDeAcceso, GrupoVLAN


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




class SWCoreScriptForm(forms.Form):
    grupo_vlan = forms.ModelChoiceField(
        # queryset=GrupoVLAN.objects.all(),
        queryset=GrupoVLAN.objects.filter(id__range=(1, 5)),
        label="Módulo",
        required=True,
        help_text="Seleccione el Modulo o Container."
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
    # accion = forms.ChoiceField(
    #     choices=[
    #         ("shutdown", "Apagar (shutdown)"),
    #         ("no shutdown", "Encender (no shutdown)"),
    #     ],
    #     label="Acción",
    #     required=True,
    #     help_text="Seleccione la acción a realizar en el rango de VLANs."
    # )