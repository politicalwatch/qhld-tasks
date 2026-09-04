from datetime import timedelta

from celery import Celery

from .infrastructure.config.settings import get_settings


settings = get_settings()

app = Celery("tasks", broker=settings.broker, backend=settings.result_backend)

beat_schedule = {
    "scanned.clean-documents": {
        "task": "scanned.clean_documents",
        "schedule": timedelta(hours=12),
    },
    "scanned.notify-new-documents": {
        "task": "scanned.notify_new_documents",
        "schedule": timedelta(hours=24),
    },
    "validate.clean_emails": {
        "task": "validate.clean_emails",
        "schedule": timedelta(seconds=settings.clean_emails_timeout),
    },
    "validate.clean_alerts_with_past_dates": {
        "task": "validate.clean_alerts_with_past_dates",
        "schedule": timedelta(seconds=settings.clean_emails_timeout),
    },
}

app.conf.beat_schedule = beat_schedule


def init():
    global app
    app = Celery("tasks", broker=settings.broker, backend=settings.result_backend)
    app.conf.beat_schedule = beat_schedule


from .alerts import *
from .tagger import *
from .validate import *
from .scanned import *
