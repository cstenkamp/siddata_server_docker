echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('adm', 'no@mail.de', 'password')" | docker exec -i siddata_server_backend_1 python manage.py shell
