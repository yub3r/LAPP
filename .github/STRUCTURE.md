# Estructura de Carpetas y Archivos

Este archivo documenta la estructura principal del proyecto para facilitar la navegación y el entendimiento del contexto.

## Carpetas principales
- djangocrud/: Configuración y lógica principal de Django
- formus/: App Django para formularios
- ruralapp/: App Django para funcionalidades rurales
- ntc-templates/: Plantillas y utilidades adicionales
- config/: Configuración de gunicorn y nginx
- BKPs/: Backups y archivos de entorno
- media/: Archivos multimedia
- static/: Archivos estáticos
- logs/: Archivos de log

## Archivos principales
- manage.py: Comando principal de Django
- requirements.txt: Dependencias
- docker-compose.yaml y Dockerfile: Contenedores
- db.sqlite3: Base de datos local (desarrollo)
- entrypoint.sh: Script de entrada para contenedores

## Notas
- Los templates HTML se encuentran en las carpetas templates/ dentro de cada app.
- Los archivos de configuración de nginx y gunicorn están en config/
- Los backups de la base de datos y dependencias están en BKPs/
