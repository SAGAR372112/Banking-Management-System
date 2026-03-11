"""WSGI config for bank_management project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bank_management.settings.production")
application = get_wsgi_application()
