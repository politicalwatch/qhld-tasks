import os
import ast
import json
import urllib
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger

from tipi_data.repositories.alerts import Alerts, InitiativeAlerts
from tipi_data.repositories.topics import Topics

from .mail import send_email
from .sentence import make_sentence
from .infrastructure.config.settings import get_mail_settings, get_settings


log = get_task_logger(__name__)


@shared_task
def send_alerts():
    def get_topic_shortname(topic_name, topics):
        for topic in topics:
            if topic['name'] == topic_name:
                return topic['shortname']
        return None

    def get_search_query_params(search):
        flat_search = {}
        for key, value in search.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    flat_search[f"{key}[{i}]"] = item
            else:
                flat_search[key] = value
        return urllib.parse.urlencode(flat_search)

    def remove_duplicated_responses(initiatives):
        title_counts = {}
        for initiative in initiatives:
            title_counts[initiative.title] = title_counts.get(initiative.title, 0) + 1
        return [
            initiative for initiative in initiatives
            if not (
                title_counts.get(initiative.title, 0) > 1
                and getattr(initiative, 'initiative_type_alt', None) == 'Respuesta'
            )
        ]

    dirname = get_settings().template_dir or os.path.join(
        os.path.dirname(__file__), 'templates')

    tmpl_qhld = os.path.join(dirname, 'alert_qhld.html')
    tmpl_p2030 = os.path.join(dirname, 'alert_p2030.html')
    template_qhld = open(tmpl_qhld).read()
    template_p2030 = open(tmpl_p2030).read()
    alerts = Alerts.get_validated()
    all_topics = Topics.get_all()
    for alert in alerts:
        alert_to_send = {}
        searches = [s for s in alert.searches if s.validated]
        for search in searches:
            try:
                search_json = json.loads(search.search)
                kb = search_json['knowledgebase']
                initiatives = InitiativeAlerts.by_search(ast.literal_eval(search.dbsearch), kb, exclude_fields=['content'])
                initiatives = remove_duplicated_responses(initiatives)
                if kb not in alert_to_send:
                    alert_to_send[kb] = {
                        'id': alert.id,
                        'searches': []
                    }
                if len(initiatives):
                    alert_to_send[kb]['searches'].append({
                        'hash': search.hash,
                        'search_sentence': make_sentence(search.search),
                        'search_query_params': get_search_query_params(search_json),
                        'initiatives': [
                            {
                                'id': initiative.id,
                                'title': initiative.title,
                                'status': initiative.status,
                                'author_parliamentarygroups': getattr(initiative, 'author_parliamentarygroups', None),
                                'author_deputies': getattr(initiative, 'author_deputies', None),
                                'author_others': getattr(initiative, 'author_others', None),
                                'reason': getattr(initiative, 'reason', None),
                                'initiative_type': initiative.initiative_type,
                                'topics': [get_topic_shortname(topic, all_topics) for item in initiative.tagged if item['knowledgebase'] == kb for topic in item['topics']]
                            }
                            for initiative in initiatives
                            ]
                        })
                else:
                    print(f"No initiatives alerts for {search.search}")
            except Exception as e:
                log.error(f"{alert.email}: {e}")

        for kb in alert_to_send:
            try:
                if not len(alert_to_send[kb]['searches']):
                    continue

                if kb == 'politicas':
                    template = template_qhld
                elif kb == 'ods':
                    template = template_p2030

                mail_settings = get_mail_settings(kb)
                context = {
                    'tipi_name': mail_settings.name,
                    'tipi_description': mail_settings.description,
                    'tipi_color': mail_settings.color,
                    'tipi_email': mail_settings.email,
                    'tipi_frontend': mail_settings.frontend,
                    'tipi_backend': mail_settings.backend,
                    'banner_url': mail_settings.banner_url,
                    'alert': alert_to_send[kb]
                }
                send_email([alert.email],
                           mail_settings.alert_subject,
                           template,
                           mail_settings,
                           context)
            except Exception as e:
                log.error(f"{alert.email}: {e}")

    InitiativeAlerts.clear()
