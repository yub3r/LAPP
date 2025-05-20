import re
import subprocess
import time
import ipaddress
import concurrent.futures
import asyncio
import telnetlib
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import SWDScriptForm, SWAScriptForm, SWCoreScriptForm
from .models import HistorialEjecucionSWD, HistorialEjecucionSWA, Rack, SwitchDeAcceso, SwitchDeDistribucion, SwitchCore, GrupoVLAN, HistorialEjecucionSWCore
from .swd_script import conectar_telnet, obtener_nombre_host, ejecutar_comandos
from datetime import date
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from config import usuario_sw, contraseña_sw, habilitar_contraseña_sw
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed




# Create your views here.
########################  SCRIPTS  ######################################################  SCRIPTS  ##############################
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
def ejecutar_swcore_script(request):
    if request.method == 'POST':  # Manejar ejecución del script
        form = SWCoreScriptForm(request.POST)
        if form.is_valid():
            grupo_vlan = form.cleaned_data['grupo_vlan']
            accion = form.cleaned_data['accion']
            switch_core_ip = grupo_vlan.switch_core.ip
            usuario = usuario_sw
            contraseña = contraseña_sw
            habilitar_contraseña = habilitar_contraseña_sw
            usuario_django = request.user
            vlans = grupo_vlan.vlans
            nombre_grupo = grupo_vlan.nombre_grupo

            # Mapear acción del usuario a comando técnico
            if accion == "encender":
                comando_accion = "no shutdown"
            elif accion == "apagar":
                comando_accion = "shutdown"
            else:
                return JsonResponse({'status': 'error', 'message': 'Acción no válida.'})

            tn, mensaje_error = conectar_telnet(switch_core_ip, usuario, contraseña, habilitar_contraseña)
            try:
                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                else:
                    comandos = ["configure terminal"]  # Comando inicial
                    if "ARG_06" in nombre_grupo:
                        # Lógica para grupos ARG_06 / Cont X
                        vlan_id = vlans.strip()  # Obtener el ID del puerto Po
                        if vlan_id.isdigit():
                            comandos.append(f"interface Po{vlan_id}")
                            comandos.append(comando_accion)  # Aplicar acción
                        else:
                            return JsonResponse({'status': 'error', 'message': f'Formato de VLAN no válido para {nombre_grupo}. Se esperaba un número.'})
                    else:
                        # Lógica para grupos ARG_01 a ARG_05
                        for rango in vlans.split(","):
                            if "-" in rango:
                                start, end = map(int, rango.split("-"))
                                comandos.append(f"interface range Vl{start}-{end}")
                            else:
                                comandos.append(f"interface Vl{rango}")
                            comandos.append(comando_accion)  # Aplicar acción
                    comandos.append("end")  # Terminar configuración

                    ejecutar_comandos(tn, comandos)  # Ejecutar comandos
                    tn.write(b"exit\n")  # Salir de Telnet
                    tn.close()
                    resultado = f"Ejecución Exitosa. Aplicado a VLANs/Puertos: {vlans}."

                # Guardar en el historial
                HistorialEjecucionSWCore.objects.create(
                    usuario=usuario_django,
                    switch_core=grupo_vlan.switch_core,
                    grupo_vlan=grupo_vlan,
                    accion=accion,  # Guardar la elección del usuario (encender/apagar)
                    resultado=resultado
                )
                return JsonResponse({'status': 'success', 'message': resultado})
            except Exception as e:
                resultado = f"Error durante la ejecución: {str(e)}"
                HistorialEjecucionSWCore.objects.create(
                    usuario=usuario_django,
                    switch_core=grupo_vlan.switch_core,
                    grupo_vlan=grupo_vlan,
                    accion=accion,
                    resultado="Fallido"
                )
                return JsonResponse({'status': 'error', 'message': resultado})
        else:
            return JsonResponse({'status': 'error', 'message': 'Formulario no válido.'})

    # Si el método es GET, renderizar el formulario y el historial
    form = SWCoreScriptForm()
    historial = HistorialEjecucionSWCore.objects.order_by('-fecha_hora_ejecucion')[:30]
    return render(request, 'formulario_swcore_script.html', {'form': form, 'historial': historial})



@login_required
def ejecutar_swd_script(request):
    if request.method == 'POST':
        form = SWDScriptForm(request.POST)
        if form.is_valid():
            nro_swd = int(form.cleaned_data['nro_swd'])
            accion = form.cleaned_data['accion']
            usuario_django = request.user

            try:
                switch_info = SwitchDeDistribucion.objects.get(nro_swd=nro_swd)
                host = switch_info.ip

                special_ips = [
                    "192.168.230.31", "192.168.230.32", "192.168.230.33",
                    "192.168.230.34", "192.168.230.35", "192.168.230.36",
                    "192.168.230.37", "192.168.230.38"
                ]

                tn, mensaje_error = conectar_telnet(host, usuario_sw, contraseña_sw, habilitar_contraseña_sw)

                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                else:
                    hostname = obtener_nombre_host(tn)
                    comandos = ["configure terminal"]

                    if host in special_ips:
                        comandos.append("interface range Gi1/0/1-14")
                        comandos.append("no shutdown" if accion == "encender" else "shutdown")
                        resultado = f"Ejecución Exitosa. Interfaces Gi1-14 {'encendidas' if accion == 'encender' else 'apagadas'} {host}"
                    else:
                        comandos.append("interface range Po1-24")
                        comandos.append("no shutdown" if accion == "encender" else "shutdown")
                        resultado = f"Ejecución Exitosa. Interfaces Po1-24 {'encendidas' if accion == 'encender' else 'apagadas'} {host}"

                    ejecutar_comandos(tn, comandos)
                    tn.read_until(b"#", timeout=10)
                    comandos.append("end")
                    ejecutar_comandos(tn, comandos)
                    tn.write(b"exit\n")
                    tn.close()

                # Guardar siempre el historial, ya sea éxito o fallo
                HistorialEjecucionSWD.objects.create(
                    nro_swd=switch_info,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )

            except SwitchDeDistribucion.DoesNotExist:
                resultado = f"Error: No se encontró el SWD con nro_swd={nro_swd}."
                HistorialEjecucionSWD.objects.create(
                    nro_swd_id=nro_swd,
                    accion=accion,
                    usuario=usuario_django,
                    resultado=resultado
                )

            except Exception as e:
                resultado = f"Error durante la conexión y ejecución de comandos: {str(e)}"
                try:
                    HistorialEjecucionSWD.objects.create(
                        nro_swd_id=nro_swd,
                        accion=accion,
                        usuario=usuario_django,
                        resultado=resultado
                    )
                except Exception as inner_e:
                    print(f"Error guardando historial SWD: {inner_e}")

            return render(request, 'resultado_swd_script.html', {'resultado': resultado})

    else:
        form = SWDScriptForm()

    historial = HistorialEjecucionSWD.objects.order_by('-fecha_hora_ejecucion')[:30]
    return render(request, 'formulario_swd_script.html', {'form': form, 'historial': historial})



@login_required
def ejecutar_swa_script(request):
    if request.method == 'POST':
        form = SWAScriptForm(request.POST)

        nro_rack = request.POST.get('rack')
        form.fields.pop('switches_de_acceso', None)
        form.fields.pop('rack', None)

        if form.is_valid():
            nro_swd = int(form.cleaned_data['nro_swd'])
            accion = form.cleaned_data['accion']
            portchannels_str = form.cleaned_data['portchannels_swa']
            usuario_django = request.user

            try:
                switch_distribucion = SwitchDeDistribucion.objects.get(nro_swd=nro_swd)
                host = switch_distribucion.ip

                tn, mensaje_error = conectar_telnet(host, usuario_sw, contraseña_sw, habilitar_contraseña_sw)

                if tn is None:
                    resultado = f"Fallido. {mensaje_error}"
                else:
                    comandos = ["configure terminal"]
                    portchannels_list = []

                    for portchannel in portchannels_str.split(","):
                        portchannel = portchannel.strip()
                        portchannels_list.append(portchannel)

                        if 21 <= nro_swd <= 28:
                            comandos.append(f"interface Gi1/0/{portchannel}")
                        else:
                            comandos.append(f"interface Port-channel{portchannel}")

                        comandos.append("no shutdown" if accion == "encender" else "shutdown")

                    comandos.append("end")
                    ejecutar_comandos(tn, comandos)
                    tn.write(b"exit\n")
                    tn.close()

                    resultado = f"Ejecución Exitosa. Script completado / SWD {nro_swd}."

                # Guardar historial por cada portchannel
                for portchannel_id in portchannels_list:
                    try:
                        switch_acceso = SwitchDeAcceso.objects.get(portchannel=portchannel_id, nro_rack_id=nro_rack)
                        rack_obj = Rack.objects.get(id=nro_rack)
                        HistorialEjecucionSWA.objects.create(
                            usuario=usuario_django,
                            nro_rack=rack_obj,
                            portchannel=switch_acceso,
                            accion=accion,
                            resultado=resultado
                        )
                    except SwitchDeAcceso.DoesNotExist:
                        print(f"No se encontró el SWA con portchannel {portchannel_id} en el rack {nro_rack}.")

            except SwitchDeDistribucion.DoesNotExist:
                resultado = f"Error: No se encontró el SWD con nro_swd={nro_swd}."
                try:
                    rack_obj = Rack.objects.get(id=nro_rack)
                    HistorialEjecucionSWA.objects.create(
                        usuario=usuario_django,
                        nro_rack=rack_obj,
                        accion=accion,
                        resultado=resultado
                    )
                except Rack.DoesNotExist:
                    print(f"No se encontró el Rack con id={nro_rack} para guardar el historial de error SWA.")

            except Exception as e:
                resultado = f"Error durante la conexión al SWD {nro_swd}: {str(e)}"
                try:
                    rack_obj = Rack.objects.get(id=nro_rack)
                    HistorialEjecucionSWA.objects.create(
                        usuario=usuario_django,
                        nro_rack=rack_obj,
                        accion=accion,
                        resultado=resultado
                    )
                except Exception as inner_e:
                    print(f"Error guardando historial de error de SWA: {inner_e}")

            return render(request, 'resultado_swa_script.html', {'resultado': resultado})

    else:
        form = SWAScriptForm()

    historial = HistorialEjecucionSWA.objects.order_by('-fecha_hora_ejecucion')[:30]
    return render(request, 'formulario_swa_script.html', {'form': form, 'historial': historial})



##################################################CDP NEIGHBORS##########################################################


async def check_reachable_hosts(hosts):
    """Verifica múltiples hosts simultáneamente con fping y devuelve los que están alcanzables."""
    try:
        process = await asyncio.create_subprocess_exec(
            "fping", "-c1", "-t200", *hosts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        results = stdout.decode() + stderr.decode()

        # 🛠 Extraer los hosts que tienen "0% loss"
        reachable_hosts = []
        for line in results.splitlines():
            match = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+:\s+.*0% loss", line)
            if match:
                reachable_hosts.append(match.group(1))

        return reachable_hosts

    except Exception as e:
        print(f"⚠️ Error ejecutando fping: {e}")
        return []


def generar_rango_ips(ip_inicio, ip_final):
    try:
        inicio = ipaddress.IPv4Address(ip_inicio)
        fin = ipaddress.IPv4Address(ip_final)
        if inicio > fin:
            return []
        return [str(ipaddress.IPv4Address(ip)) for ip in range(int(inicio), int(fin) + 1)]
    except ValueError:
        return []

def ejecutar_cdp(host, contraseña_sw):
    """Conecta por Telnet a un host y ejecuta el comando 'show cdp neighbors'."""
    try:
        tn = telnetlib.Telnet(host, timeout=5)
        tn.expect([b"Password: "])
        tn.write(contraseña_sw.encode('utf-8') + b"\n")
        
        tn.write(b"show cdp neighbors\n")
        tn.write(b"exit\n")
        # time.sleep(1)
        tn.sock.settimeout(2)

        output = tn.read_all().decode('utf-8', errors='ignore')


        return output, None  # Retorna la salida y ningún mensaje de error
    except Exception as e:
        return None, str(e)
    
@login_required
def cdp_neighbors_view(request):
    data = []
    if request.method == "POST":
        ip_inicio = request.POST.get("ip_inicio")
        ip_final = request.POST.get("ip_final")
        hosts = generar_rango_ips(ip_inicio, ip_final)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        reachable_hosts = loop.run_until_complete(check_reachable_hosts(hosts))
        # reachable_hosts = check_reachable_hosts([i['host'] for i in data])
        
        for host in hosts:
            host_data = {
                "host": host, "status": "Disable", "device_name": "Desconocido",
                "platform": "WS-C3750X", "fas_47": "Down", "fas_48": "Down", "act": "REV"
            }
            if host not in reachable_hosts:
                data.append(host_data)
                continue
            
            try:
                output, error_message = ejecutar_cdp(host, contraseña_sw)
                if output is None:
                    data.append(host_data)
                    continue
                
                # Captura el 'device_name' antes de la salida de 'show cdp neighbors'
                device_name_match = re.search(r'(\S+)\s*>\s*', output)
                if device_name_match:
                    host_data["device_name"] = device_name_match.group(1)

                neighbors_pattern = re.compile(
                    r'(?P<device_id>\S+)\s*\n\s*'
                    r'(?P<local_interface>Fas \d+/\d+/\d+|Fas \d+/\d+)\s+\d+\s+\S+\s+\S+\s+(?P<platform>\S+)\s+(?P<port_id>Gig \d+/\d+/\d+)',
                    re.MULTILINE
                )

                # Captura el 'Device ID' y actualiza el host_data
                matches = list(neighbors_pattern.finditer(output))
                fas_47, fas_48 = "Down", "Down"  # Inicializa los valores

                if matches:
                    first_match = matches[0]
                    host_data["device_id"] = first_match.group("device_id")
                    
                    for match in matches:
                        local_interface, port_id = match.group("local_interface"), match.group("port_id")
                        
                        if local_interface in ["Fas 0/47", "Fas 1/0/47"]:
                            fas_47 = port_id
                        elif local_interface in ["Fas 0/48", "Fas 1/0/48"]:
                            fas_48 = port_id

                host_data.update({
                    "fas_47": fas_47,
                    "fas_48": fas_48,
                    "status": "Enable"
                })

                # Lógica para determinar el estado de las interfaces
                if fas_47 != "Down" and fas_48 != "Down":
                    num_47 = fas_47.split("/")[-1]
                    num_48 = fas_48.split("/")[-1]

                    if fas_47.startswith("Gig 1/0") and fas_48.startswith("Gig 2/0") and num_47 == num_48:
                        host_data["act"] = "OK"
                    elif fas_47.startswith("Gig 2/0") and fas_48.startswith("Gig 1/0") and num_47 == num_48:
                        host_data["act"] = "INV"
                    else:
                        host_data["act"] = "REV"
                elif fas_47 != "Down" and fas_48 == "Down":
                    host_data["act"] = "REV"
                elif fas_48 != "Down" and fas_47 == "Down":
                    host_data["act"] = "REV"
                else:
                    host_data["act"] = "REV"

                host_data["status"] = "Enable"
                
            except Exception as e:
                print(f"⚠️ Error inesperado con {host}: {e}")
            finally:
                data.append(host_data)
    
        return JsonResponse(data, safe=False)  # Devuelve JSON en lugar de renderizar una plantilla
    
    return render(request, 'cdp_nbr.html', {'data': data})








def ejecutar_interface_status(host, contraseña_sw, habilitar_contraseña_sw):
    """Conecta por Telnet a un host Cisco y ejecuta un 'show interface status' filtrado."""
    device = {
        'device_type': 'cisco_ios_telnet',
        'ip': host,
        'username': '',
        'password': contraseña_sw,
        'secret': habilitar_contraseña_sw,
        'fast_cli': False
    }

    try:
        net_connect = ConnectHandler(**device)
        net_connect.enable()

        # Comando optimizado
        cmd = "show interface status | i Gi1/1/|Gi2/1/"
        output = net_connect.send_command(cmd, expect_string=r"#", delay_factor=1)

        net_connect.disconnect()
        print(f"[{host}] Output recibido ({len(output)} bytes)", flush=True)
        return output, None

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        print(f"[{host}] ERROR Netmiko: {e}", flush=True)
        return None, str(e)
    except Exception as e:
        print(f"[{host}] ERROR general: {e}", flush=True)
        return None, str(e)


def parse_interface_output(output, host):
    """Parsea el output del show interface status filtrado."""
    prom = re.search(r"(\S+?)#", output)
    sw_name = prom.group(1) if prom else host

    iface_re = re.compile(
        r"^(?P<port>Gi[12]/1/\d+)\s+"
        r"(?P<desc>\S*)\s+"
        r"(?P<status>\S+)\s+"
        r"(?P<vlan>\S+)\s+"
        r"(?P<duplex>\S+)\s+"
        r"(?P<speed>\S+)\s+"
        r"(?P<type>.+)$",
        re.MULTILINE
    )

    parsed = []
    for m in iface_re.finditer(output):
        tipo = m.group("type").rstrip("\r")
        parsed.append({
            "ip":         host,
            "swd_name": sw_name,
            "descr":      m.group("desc"),
            "status":     m.group("status"),
            "vlan":       m.group("vlan"),
            "duplex":     m.group("duplex"),
            "type":       tipo,
            "port":       m.group("port"),
        })

    # Si no se encontró nada, agrega una fila vacía
    if not parsed:
        parsed.append({
            "ip":         host,
            "swd_name": sw_name,
            "descr":      "",
            "status":     "",
            "vlan":       "",
            "duplex":     "",
            "type":       "",
            "port":       ""
        })

    return parsed


@login_required
def interface_status_view(request):
    data = []
    filtered_data = []

    # 1) Obtener lista blanca y ordenarla como IPs
    allowed_ips = sorted(
        SwitchDeDistribucion.objects.values_list('ip', flat=True),
        key=lambda ip: list(map(int, ip.split(".")))
    )

    if request.method == "POST":
        ip_inicio = request.POST.get("ip_inicio")
        ip_final = request.POST.get("ip_final")

        # 2) Generar el rango completo que puso el usuario
        all_hosts = generar_rango_ips(ip_inicio, ip_final)

        # 3) Filtrar SOLO los autorizados
        hosts = [h for h in all_hosts if h in allowed_ips]

        # 3a) Agregar los no autorizados (para marcarlos)
        for h in all_hosts:
            if h not in allowed_ips:
                data.append({
                    "ip":         h,
                    "swd_name": "",
                    "descr":      "",
                    "status":     "no autorizado",
                    "vlan":       "",
                    "duplex":     "",
                    "type":       "",
                    "port":       ""
                })

        # 4) Ejecutar fping *solo* contra los autorizados
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        reachable = loop.run_until_complete(check_reachable_hosts(hosts))

        # 5) Ejecutar Telnet solo a los alcanzables autorizados
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(ejecutar_interface_status, host, contraseña_sw, habilitar_contraseña_sw): host
                for host in reachable
            }

            for future in as_completed(futures):
                host = futures[future]
                try:
                    # Esperar máx 10 segundos por host individualmente
                    out, err = future.result(timeout=10)
                except Exception as e:
                    # Si falla por timeout, conexión o cualquier otro error
                    out, err = None, str(e)

                if err or out is None:
                    data.append({
                        "ip":         host,
                        "swd_name": "",
                        "descr":      "",
                        "status":     "error",
                        "vlan":       "",
                        "duplex":     "",
                        "type":       "",
                        "port":       ""
                    })
                else:
                    data.extend(parse_interface_output(out, host))

        # 6) Marcar como 'down' los que no respondieron al ping
        for host in hosts:
            if host not in reachable:
                data.append({
                    "ip":         host,
                    "swd_name": "",
                    "descr":      "",
                    "status":     "down",
                    "vlan":       "",
                    "duplex":     "",
                    "type":       "",
                    "port":       ""
                })

        # 7) Filtrar la data para excluir los "no autorizado"
        filtered_data = [item for item in data if item['status'] != 'no autorizado']

        return JsonResponse(filtered_data, safe=False)

    return render(request, 'interface_status.html', {
        "data": data,
        "allowed_ips": allowed_ips
    })
