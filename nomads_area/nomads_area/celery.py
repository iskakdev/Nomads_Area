import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nomads_area.settings")

app = Celery("nomads_area")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
