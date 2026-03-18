import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maghettoni.settings')

app = Celery('maghettoni')

# Pull config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
