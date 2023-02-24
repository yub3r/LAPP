FROM python:3.11.2-alpine3.17

ENV PYTHONUMBUFFERED=1

WORKDIR /code

RUN apk update \
    apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    libressl-dev \
    python3-dev \
    postgresql-libs \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    linux-headers \
    postgresql-dev \
    && pip install --upgrade pip 


COPY . /code/

RUN pip install -r requirements.txt


CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", ":8000", "--chdir", "djangocrud", "djangocrud.wsgi:application"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]