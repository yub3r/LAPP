# pull official base image
FROM python:3.11.2-alpine3.17

# set work directory
WORKDIR /usr/src/lapp

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
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

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
# COPY ./entrypoint.sh .
# RUN sed -i 's/\r$//g' /usr/src/lapp/entrypoint.sh
# RUN chmod +x /usr/src/lapp/entrypoint.sh

# RUN python manage.py migrate

# copy projec
COPY . .
RUN adduser -D dockuser
RUN chown dockuser:dockuser -R /usr/src/lapp

RUN chmod +x /usr/src/lapp/manage.py
# Install migrations

# run entrypoint.sh
# ENTRYPOINT ["/usr/src/lapp/entrypoint.sh"]













# FROM python:3.11.2-alpine3.17

# ENV PYTHONUMBUFFERED=1

# WORKDIR /code

# RUN apk update \
#     apk add --no-cache \
#     gcc \
#     musl-dev \
#     libffi-dev \
#     libressl-dev \
#     python3-dev \
#     postgresql-libs \
#     && apk add --no-cache --virtual .build-deps \
#     build-base \
#     linux-headers \
#     postgresql-dev \
#     && pip install --upgrade pip 


# COPY . /code/

# RUN pip install -r requirements.txt


CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", ":8000", "--chdir", "djangocrud", "djangocrud.wsgi:application"]
# # CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]