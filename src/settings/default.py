import os

from settings.settings_base import *

ALLOWED_HOSTS = eval(os.getenv("SIDDATA_ALLOWED_HOSTS", "") or "[]")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = eval(os.getenv("SIDDATA_DEBUG", "") or "True")
