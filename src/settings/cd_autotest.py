import os

from settings.settings_base import *
from settings.settings_base import BASE_DIR

ALLOWED_HOSTS = ["127.0.0.1"]
DEBUG = False

STATIC_ROOT = os.path.join(BASE_DIR, "collected_static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
