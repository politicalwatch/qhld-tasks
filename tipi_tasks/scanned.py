from datetime import datetime, timedelta
import time
from celery import shared_task
from tipi_data.repositories.scanned import Scanned
from .infrastructure.config.settings import get_mail_settings, get_settings
import os
from .mail import send_email


@shared_task
def clean_documents():
    Scanned.delete_expired(datetime.today())


@shared_task
def notify_new_documents():
    ONE_DAY_IN_SECONDS = 60 * 60 * 24
    creation = time.mktime(datetime.now().timetuple()) - ONE_DAY_IN_SECONDS
    creation_date = datetime.fromtimestamp(creation)

    scans = Scanned.get_unverified_since(creation_date)

    if len(scans) == 0:
        return

    dirname = get_settings().template_dir or os.path.join(
        os.path.dirname(__file__), "templates")

    tmpl = os.path.join(dirname, "new_documents.html")
    template = open(tmpl).read()

    mail_settings = get_mail_settings('escaner')
    context = {
        "tipi_name": mail_settings.name,
        "banner_url": mail_settings.banner_url,
        "tipi_frontend": mail_settings.frontend,
        "documents": scans,
    }

    send_email(
        ["info@politicalwatch.es"],
        "Nuevos documentos no verificados",
        template,
        mail_settings,
        context,
    )
