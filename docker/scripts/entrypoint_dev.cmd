python src\manage.py collectstatic --noinput
python src\manage.py migrate
python src\manage.py runserver 0.0.0.0:8000
