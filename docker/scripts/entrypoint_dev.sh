#!/bin/bash

# see https://dev.to/ashiqursuperfly/setting-up-django-app-dockerfile-dockerizing-django-for-deploying-anywhere-4mpc

set -e # exit if errors happen anywhere
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
