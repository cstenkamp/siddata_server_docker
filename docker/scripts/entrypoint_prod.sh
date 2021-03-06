#!/bin/sh

# see https://dev.to/ashiqursuperfly/setting-up-django-app-dockerfile-dockerizing-django-for-deploying-anywhere-4mpc

set -e # exit if errors happen anywhere

echo "Allowed hosts are:"
python -c "from django.conf import settings; print(settings.ALLOWED_HOSTS)"
python manage.py collectstatic --noinput
python manage.py migrate

uwsgi --socket :8000 --master --enable-threads --module apps.wsgi
