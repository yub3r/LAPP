# Project Context: LAPP

This document provides context for the LAPP project to customize Gemini's interactions.

## Project Overview

LAPP is a web application built with Django. It appears to be a system for managing orders, tasks, and other rural-related functionalities.

## Technologies

*   **Backend:** Django
*   **Asynchronous Tasks:** Celery
*   **Database:** PostgreSQL
*   **Web Server:** Nginx
*   **WSGI Server:** Gunicorn
*   **Containerization:** Docker and docker-compose
*   **Frontend:** Django Templates (HTML)
*   **Operating System:** Ubuntu Server 22.04

## Project Structure

*   `djangocrud/`: Main Django project configuration.
*   `formus/`: Django app for forms.
*   `ruralapp/`: Django app for rural functionalities.
*   `ntc-templates/`: Templates and utilities.
*   `config/`: Gunicorn and Nginx configuration.
*   `BKPs/`: Backups and environment files.
*   `media/`: Media files.
*   `static/`: Static files.
*   `logs/`: Log files.

## Database

*   **Engine:** PostgreSQL 14.18
*   **Host:** 10.45.0.69
*   **Main Database:** postgres
*   **Admin User:** postgres
*   **Key Tables:**
    *   `auth_user`: System users.
    *   `ruralapp_order`: Orders.
    *   `ruralapp_otherdish`, `ruralapp_salad`, `ruralapp_sidedish`: Menu options.
    *   `formus_*`: Forms and responses.
    *   `tasks_*`: Tasks, draws, guards, overtime.
    *   `tools_*`: Network infrastructure and switches.

## Important Files

*   `manage.py`: Django's command-line utility.
*   `requirements.txt`: Python dependencies.
*   `docker-compose.yaml`, `Dockerfile`: Container definitions.
*   `db.sqlite3`: Local development database.
*   `entrypoint.sh`: Container entrypoint script.

## Conventions

*   The project is modular, with functionality separated into Django apps.
*   Database migrations are used to manage schema changes.
*   Backups are stored in the `BKPs/` directory.
*   HTML templates are located in the `templates/` directory within each app.
