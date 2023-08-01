import telnetlib
import time

def conectar_telnet(host, usuario, contraseña, habilitar_contraseña):
    try:
        # Conexión al dispositivo mediante telnet
        tn = telnetlib.Telnet(host, timeout=5)

        # Lectura de los mensajes iniciales (hasta el prompt de inicio de sesión)
        output = tn.read_until(b"Username:", timeout=5)
        print(output.decode("utf-8"))

        # Envío del nombre de usuario
        tn.write(usuario.encode("utf-8") + b"\n")

        # Lectura de los mensajes de contraseña (hasta el prompt de contraseña)
        output = tn.read_until(b"Password:", timeout=5)
        print(output.decode("utf-8"))

        # Envío de la contraseña
        tn.write(contraseña.encode("utf-8") + b"\n")

        # Lectura de la respuesta después del inicio de sesión
        output = tn.read_very_eager()
        print(output.decode("utf-8"))

        # Envío del comando "enable" para acceder al modo de privilegios ejecutivos
        tn.write(b"enable\n")

        # Lectura de la solicitud de contraseña de privilegios ejecutivos (hasta el prompt de contraseña de enable)
        output = tn.read_until(b"Password:", timeout=5)
        print(output.decode("utf-8"))

        # Envío de la contraseña de privilegios ejecutivos
        tn.write(habilitar_contraseña.encode("utf-8") + b"\n")

        # Lectura de la respuesta después de ingresar al modo de privilegios ejecutivos
        output = tn.read_very_eager()
        print(output.decode("utf-8"))

        # Configurar el terminal para que muestre toda la información sin interrupciones
        tn.write(b"terminal length 0\n")
        time.sleep(0.5)
        tn.read_very_eager()


        return tn, None  # Retornamos también None como mensaje_error si la conexión fue exitosa

    except (EOFError, ConnectionRefusedError) as e:
        mensaje_error = f"Error de conexión al sw {host}. Verifica que el SW responda al protocolo Telnet."
        return None, mensaje_error

    except TimeoutError as e:
        mensaje_error = f"SWD {host} fuera de línea."
        return None, mensaje_error

    except Exception as e:
        mensaje_error = f"Error desconocido al intentar conectarse al sw {host}: {str(e)}"
        return None, mensaje_error

def obtener_nombre_host(tn):
    tn.write(b"show run | include hostname\n")
    time.sleep(0.5)
    output = tn.read_very_eager()

    # Dividir la salida en líneas
    lines = output.decode("utf-8").splitlines()

    # Buscar el nombre del host en la salida
    for line in lines:
        if "hostname " in line:
            hostname = line.split("hostname ")[1].strip()
            return hostname

    # Si no se encontró el nombre del host, devolver una cadena vacía
    return ""

def exec_command(tn, command):
    tn.write(command.encode('ascii') + b"\n")
    time.sleep(0.2)  # Esperar un segundo para que se complete la ejecución del comando
    return tn.read_very_eager().decode('ascii')

def ejecutar_comandos(tn, comandos):
    for command in comandos:
            result = exec_command(tn, command)
            print(result)  # Opcional: Imprimir la respuesta del dispositivo para cada comando