from django.shortcuts import render, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import SWDScriptForm, SWAScriptForm
from .models import HistorialEjecucionSWD, HistorialEjecucionSWA, Rack, SwitchDeAcceso, SwitchDeDistribucion
from .swd_script import conectar_telnet, obtener_nombre_host, ejecutar_comandos
from datetime import date
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from config import usuario_sw, contraseña_sw, habilitar_contraseña_sw  


# Create your views here.
########################  SCRIPTS  ######################################################  SCRIPTS  ##############################
@login_required
def ejecutar_swd_script(request):    
    if request.method == 'POST':
        form = SWDScriptForm(request.POST)

        if form.is_valid():

            nro_swd = int(form.cleaned_data['nro_swd'])
            accion = form.cleaned_data['accion']

            # Construir la dirección IP del dispositivo Cisco
            host_base = "192.168.230."
            host = f"{host_base}{nro_swd}"

            # Obtener los valores de usuario, contraseña y habilitar_contraseña del script
            usuario = usuario_sw
            contraseña = contraseña_sw
            habilitar_contraseña = habilitar_contraseña_sw
            usuario_django = request.user if request.user.is_authenticated else None

            # Conexión telnet al switch
            tn, mensaje_error = conectar_telnet(host, usuario, contraseña, habilitar_contraseña)

            try:
                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                    print(resultado)  # Agregar print para mostrar mensaje de error
                else:
                    # Obtener el nombre del host del switch
                    hostname = obtener_nombre_host(tn)
                    print(f"Hostname: {hostname}")  # Agregar print para mostrar el nombre del host


                    # Ejecutar los comandos según la acción seleccionada
                    if accion == "encender":
                        comandos = ["configure terminal"]
                        comandos.append("interface range po1-24")
                        comandos.append("no shutdown")
                        comandos.append("end")
                        ejecutar_comandos(tn, comandos)
                    elif accion == "apagar":
                        comandos = ["configure terminal"]
                        comandos.append("interface range po1-24")
                        comandos.append("shutdown")
                        comandos.append("end")
                        ejecutar_comandos(tn, comandos)

                    tn.write(b"exit\n")
                    tn.close()
                    resultado = f"Ejecución Exitosa. Script completado."
                    # print(resultado)  # Agregar print para mostrar mensaje de éxito
                
                switch_de_distribucion = SwitchDeDistribucion.objects.get(nro_swd=nro_swd)
                # Guardar registro de ejecución en el historial

                historial_ejecucion = HistorialEjecucionSWD(
                    nro_swd=switch_de_distribucion,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )
                historial_ejecucion.save()

            except Exception as e:
                resultado = f"Error durante la conexión y ejecución de comandos: {str(e)}"
                # Si ocurre una excepción, guardamos el resultado como "fallido" en el historial
                resultado = "Ejecución Fallida."
                # print(resultado)  # Agregar print para mostrar mensaje de error


                switch_de_distribucion = SwitchDeDistribucion.objects.get(nro_swd=nro_swd)
                # Guardar registro de ejecución en el historial

                historial_ejecucion = HistorialEjecucionSWD(
                    nro_swd=switch_de_distribucion,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )
                historial_ejecucion.save()
            
            
            historial = HistorialEjecucionSWD.objects.order_by('-fecha_hora_ejecucion')[:30]


            return render(request, 'resultado_swd_script.html', {'resultado': resultado})

    else:
        form = SWDScriptForm()

    # Obtener el historial de ejecuciones para mostrar en el formulario
    historial = HistorialEjecucionSWD.objects.order_by('-fecha_hora_ejecucion')[:30]

    return render(request, 'formulario_swd_script.html', {'form': form, 'historial': historial})



def cargar_racks(request):
    switch_id = request.GET.get('switch_id')
    racks = Rack.objects.filter(nro_swd=switch_id).order_by('nro_rack')
    rack_list = [{'id': rack.pk, 'nombre': str(rack)} for rack in racks]
    return JsonResponse({'racks': rack_list})

def cargar_switches_acceso(request):
    rack_id = request.GET.get('rack_id')
    switches_acceso = SwitchDeAcceso.objects.filter(nro_rack=rack_id).order_by('-portchannel')
    switch_list = [{'nro': switch.portchannel, 'nombre': str(switch)} for switch in switches_acceso]
    return JsonResponse({'switches_acceso': switch_list})


@login_required
def ejecutar_swa_script(request):
    if request.method == 'POST':
        form = SWAScriptForm(request.POST)


        # nro_rack = form.cleaned_data['rack']
        nro_rack  = request.POST.get('rack')
        form.fields.pop('switches_de_acceso', None)
        form.fields.pop('rack', None)

        if form.is_valid():
            nro_swd = int(form.cleaned_data['nro_swd'])
            accion = form.cleaned_data['accion']
            portchannels = form.cleaned_data['portchannels_swa']  # Obtén los Port-channels seleccionados



            switch_distribucion = get_object_or_404(SwitchDeDistribucion, nro_swd=nro_swd)

            # Construir la dirección IP del dispositivo Cisco
            host = f"192.168.230.{switch_distribucion.nro_swd}"

            # Obtener los valores de usuario, contraseña y habilitar_contraseña del script
            usuario = usuario_sw
            contraseña = contraseña_sw
            habilitar_contraseña = habilitar_contraseña_sw
            usuario_django = request.user if request.user.is_authenticated else None

            # Conexión telnet al switch
            tn, mensaje_error = conectar_telnet(host, usuario, contraseña, habilitar_contraseña)

            try:
                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                else:
                    # Ejecutar los comandos según la acción seleccionada en cada Port-channel seleccionado
                    comandos = ["configure terminal"]
                    portchannels_list = []
                    for portchannel in portchannels.split(","):
                        comandos.append(f"interface Port-channel{portchannel}")
                        if accion == "encender":
                            comandos.append("no shutdown")
                        elif accion == "apagar":
                            comandos.append("shutdown")
                        portchannels_list.append(portchannel)
                    comandos.append("end")
                    ejecutar_comandos(tn, comandos)

                    tn.write(b"exit\n")
                    tn.close()
                    resultado = f"Ejecución Exitosa. Script completado."
                
                for portchannel_id in portchannels_list:
                    switch_acceso = get_object_or_404(SwitchDeAcceso, id=portchannel_id)
                    rack = get_object_or_404(Rack, nro_rack=nro_rack)
                    historial_ejecucion = HistorialEjecucionSWA(
                        usuario=usuario_django,
                        nro_rack=rack,  # Guarda el número de rack en lugar del número de switch
                        portchannel=switch_acceso,
                        accion=accion,
                        resultado=resultado
                    )
                    historial_ejecucion.save()

            except Exception as e:
                resultado = f"Error durante la conexión y ejecución de comandos: {str(e)}"
                resultado = "Ejecución fallida."

                for portchannel_id in portchannels_list:
                    switch_acceso = get_object_or_404(SwitchDeAcceso, id=portchannel_id)
                    rack = get_object_or_404(Rack, nro_rack=nro_rack)
                    historial_ejecucion = HistorialEjecucionSWA(
                        usuario=usuario_django,
                        nro_rack=rack,  # Guarda el número de rack en lugar del número de switch
                        portchannel=switch_acceso,
                        accion=accion,
                        resultado=resultado
                    )
                    historial_ejecucion.save()

            # Obtener los últimos 10 registros del historial de ejecuciones
            historial = HistorialEjecucionSWA.objects.order_by('-fecha_hora_ejecucion')[:30]
            return render(request, 'resultado_swa_script.html', {'resultado': resultado})

    else:
        form = SWAScriptForm()
    historial = HistorialEjecucionSWA.objects.order_by('-fecha_hora_ejecucion')[:30]

    return render(request, 'formulario_swa_script.html', {'form': form, 'historial': historial})