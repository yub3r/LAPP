from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import SWDScriptForm
from .models import HistorialEjecucionSWD
from .swd_script import conectar_telnet, obtener_nombre_host, ejecutar_comandos
from datetime import date
from django.contrib.auth import get_user_model

# Create your views here.
########################  SCRIPTS  ######################################################  SCRIPTS  ##############################
@login_required
def ejecutar_swd_script(request):    
    if request.method == 'POST':
        form = SWDScriptForm(request.POST)

        if form.is_valid():

            num_switch = form.cleaned_data['num_switch']
            accion = form.cleaned_data['accion']

            # Construir la dirección IP del dispositivo Cisco
            host_base = "192.168.230."
            host = f"{host_base}{num_switch}"

            # Obtener los valores de usuario, contraseña y habilitar_contraseña del script
            usuario = "admin"
            contraseña = "hashrate1!!$"
            habilitar_contraseña = "hashrate1!!$"
            usuario_django = request.user if request.user.is_authenticated else None

            # Conexión telnet al switch
            tn, mensaje_error = conectar_telnet(host, usuario, contraseña, habilitar_contraseña)

            try:
                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                else:
                    # Obtener el nombre del host del switch
                    hostname = obtener_nombre_host(tn)


                    # Ejecutar los comandos según la acción seleccionada
                    if accion == "encender":
                        comandos = ["configure terminal"]
                        for i in range(1, 25):
                            comandos.append(f"interface Port-channel{i}")
                            comandos.append("no shutdown")
                        comandos.append("end")
                        ejecutar_comandos(tn, comandos)
                    elif accion == "apagar":
                        comandos = ["configure terminal"]
                        for i in range(1, 25):
                            comandos.append(f"interface Port-channel{i}")
                            comandos.append("shutdown")
                        comandos.append("end")
                        ejecutar_comandos(tn, comandos)

                    tn.write(b"exit\n")
                    tn.close()
                    resultado = "Exitoso. Ejecución del script completado."
                
                # Guardar registro de ejecución en el historial
                    # resultado = "Exitoso"
                historial_ejecucion = HistorialEjecucionSWD(
                    num_switch=num_switch,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )
                historial_ejecucion.save()

            except Exception as e:
                resultado = f"Error durante la conexión y ejecución de comandos: {str(e)}"
                # Si ocurre una excepción, guardamos el resultado como "fallido" en el historial
                resultado = "Fallido"
                historial_ejecucion = HistorialEjecucionSWD(
                    num_switch=num_switch,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )
                historial_ejecucion.save()
            
            # Obtener los últimos 10 registros del historial de ejecuciones
            historial = HistorialEjecucionSWD.objects.order_by('-fecha_hora_ejecucion')[:20]


            return render(request, 'resultado_swd_script.html', {'resultado': resultado})

    else:
        form = SWDScriptForm()

    # Obtener el historial de ejecuciones para mostrar en el formulario
    historial = HistorialEjecucionSWD.objects.order_by('-fecha_hora_ejecucion')[:20]

    return render(request, 'formulario_swd_script.html', {'form': form, 'historial': historial})