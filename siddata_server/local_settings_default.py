import os

ALLOWED_HOSTS = eval(os.getenv("SIDDATA_DJANGO_ALLOWED_HOSTS", "[]"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = eval(os.getenv("SIDDATA_DJANGO_DEBUG", "True"))
