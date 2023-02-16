FROM python:3.11.2-alpine3.17

ENV PYTHONUMBUFFERED=1


WORKDIR /app

RUN apk update \
    RUN apk add --no-cache \
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

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

COPY ./ ./

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]