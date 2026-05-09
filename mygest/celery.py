"""
Celery application per myGest.

Worker:  celery -A mygest worker -l info
Beat:    celery -A mygest beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')

app = Celery('mygest')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
