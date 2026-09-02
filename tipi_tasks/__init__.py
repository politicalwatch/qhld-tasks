from datetime import timedelta

from celery import Celery

from . import config


app = Celery("tasks", broker=config.BROKER, backend=config.RESULT_BACKEND)

beat_schedule = {
    "scanned.clean-documents": {
        "task": "tipi_tasks.scanned.clean_documents",
        "schedule": timedelta(hours=12),
    },
    "scanned.notify-new-documents": {
        "task": "tipi_tasks.scanned.notify_new_documents",
        "schedule": timedelta(hours=24),
    },
    "validate.clean_emails": {
        "task": "tipi_tasks.validate.clean_emails",
        "schedule": timedelta(seconds=config.CLEAN_EMAILS_TIMEOUT),
    },
    "validate.clean_alerts_with_past_dates": {
        "task": "tipi_tasks.validate.clean_alerts_with_past_dates",
        "schedule": timedelta(seconds=config.CLEAN_EMAILS_TIMEOUT),
    },
}

app.conf.beat_schedule = beat_schedule


def init():
    global app
    app = Celery("tasks", broker=config.BROKER, backend=config.RESULT_BACKEND)
    app.conf.beat_schedule = beat_schedule


from .alerts import *
from .tagger import *
from .validate import *
from .scanned import *
