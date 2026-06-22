import os
import json
from datetime import datetime, date, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger

from tipi_data.repositories.alerts import Alerts

from .mail import send_email
from .sentence import make_sentence
from . import config


log = get_task_logger(__name__)


def get_project_name(kb):
    names = {"politicas": "QHLD", "ods": "Parlamento2030"}

    return names[kb]


@shared_task
def send_validation_emails():
    if getattr(config, "TEMPLATE_DIR") and config.TEMPLATE_DIR:
        dirname = config.TEMPLATE_DIR
    else:
        dirname = os.path.join(os.path.dirname(__file__), "templates")

    tmpl = os.path.join(dirname, "validation.html")
    template = open(tmpl).read()

    # getting all users that've not validated searches
    alerts = Alerts.get_with_unvalidated_searches()
    for alert in alerts:
        searches = [s for s in alert.searches
                    if not s.validated and s.validation_email_sent is not True]
        for search in searches:
            time_passed = (datetime.now() - search.created).days
            timeout = config.VALIDATION_TIMEOUT - time_passed
            search_json = json.loads(search.search)
            kb = (
                search_json["knowledgebase"]
                if "knowledgebase" in search_json
                else "politicas"
            )
            mail_config = config.mail_config(kb)
            context = {
                "tipi_name": get_project_name(kb),
                "tipi_email": mail_config["FROM"],
                "search_sentence": make_sentence(search.search),
                "validate_url": "{}/emails/validate/{}/{}".format(
                    mail_config["BACKEND"], alert.id, search.hash
                ),
                "timeout": timeout,
            }
            send_email(
                [alert.email],
                mail_config["VALIDATION_SUBJECT"],
                template,
                mail_config,
                context,
            )
            search.validation_email_sent = True
            search.validation_email_sent_date = datetime.now()
        Alerts.save(alert)


@shared_task
def clean_emails():
    alerts = Alerts.get_with_unvalidated_searches()
    timeout = datetime.now() - timedelta(days=config.VALIDATION_TIMEOUT)
    for alert in alerts:
        searches = [s for s in alert.searches if not s.validated]
        for search in searches:
            if search.created > timeout:
                continue
            Alerts.remove_search(search.hash)

    # Remove emails without searches
    Alerts.delete_empty()


@shared_task
def clean_alerts_with_past_dates():
    alerts = Alerts.get_validated()
    for alert in alerts:
        searches = [s for s in alert.searches if s.validated]
        for search in searches:
            search_obj = json.loads(search.search)
            if "enddate" in search_obj.keys():
                if str(date.today()) < search_obj["enddate"]:
                    continue
                Alerts.remove_search(search.hash)

    # Remove emails without searches
    Alerts.delete_empty()
