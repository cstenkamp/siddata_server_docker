import os

from settings.settings_base import *
from settings.settings_base import BASE_DIR

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = ["*"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"
