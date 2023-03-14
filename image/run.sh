#!/bin/sh 

cd /app

export DJANGO_SETTINGS_MODULE=presign.settings
export DJANGO_CONFIGURATION=Production

python manage.py migrate

python manage.py collectstatic --noinput

if [ ! -z "$PRESIGN_SUPERUSER_NAME"  ] && [ ! -z "$PRESIGN_SUPERUSER_PASS" ]; then
    python manage.py create_superuser_if_not_exists --user "$PRESIGN_SUPERUSER_NAME" --pass "$PRESIGN_SUPERUSER_PASS"
fi

gunicorn presign.wsgi -b 0.0.0.0:8000
