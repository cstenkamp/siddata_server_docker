import os

ALLOWED_HOSTS = os.getenv("SIDDATA_DJANGO_ALLOWED_HOSTS", [])

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("SIDDATA_DJANGO_DEBUG", True)
