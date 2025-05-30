import os
import sys

sys.path.insert(0, r"C:\DV_APP_IIS\dv_importmoca")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ImportMoca.settings")

from django.core.wsgi import get_wsgi_application
handler = get_wsgi_application()
