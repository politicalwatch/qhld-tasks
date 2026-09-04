import sparkpost
from jinja2 import Environment, select_autoescape, Template
from .infrastructure.config.settings import MailSettings, get_settings

status_mapping = {
    "Aprobada": "completed",
    "Respondida": "completed",
    "Celebrada": "completed",
    "Convalidada": "completed",
    "Convertida en otra": "completed",
    "Acumulada en otra": "completed",
    "En tramitación": "neutral",
    "Desconocida": "neutral",
    "No admitida a trámite": "error",
    "No debatida": "error",
    "Caducada": "error",
    "Rechazada": "error",
    "Derogada": "error",
    "Retirada": "error",
    "No celebrada": "error"
}

ods_color_mapping = {
    'ODS 1': '#eb1c2d',
    'ODS 2': '#d3a029',
    'ODS 3': '#4c9f38',
    'ODS 4': '#c52333',
    'ODS 5': '#ed4135',
    'ODS 6': '#00aed9',
    'ODS 7': '#fdb713',
    'ODS 8': '#8f1838',
    'ODS 9': '#f06a38',
    'ODS 10': '#dd1367',
    'ODS 11': '#f69c39',
    'ODS 12': '#cf8d2a',
    'ODS 13': '#48773e',
    'ODS 14': '#007dbc',
    'ODS 15': '#5cb84d',
    'ODS 16': '#02558b',
    'ODS 17': '#183668',
}

legislative_type_ids = ["120", "121", "122", "123", "124", "125", "127", "130", "131", "132"]
political_orientiation_type_ids = ["161", "162", "171", "173","200", "201", "225", "430"]

def is_in(value, array):
    return value in array

def is_not_in(value, array):
    return value not in array

env = Environment(autoescape=select_autoescape(['html', 'xml']))
env.tests['in'] = is_in
env.tests['not_in'] = is_not_in

def sparkpost_email(recipients, subject, template, mail_settings: MailSettings, context={}):
    template = env.from_string(template)
    try:
        html = template.render(**context, status_mapping=status_mapping, ods_color_mapping=ods_color_mapping, legislative_type_ids=legislative_type_ids, political_orientiation_type_ids=political_orientiation_type_ids)
    except Exception as e:
        print(f"Template error: {e}")
    sp = sparkpost.SparkPost(mail_settings.api)
    sp.transmissions.send(
        recipients=recipients,
        from_email='{} <{}>'.format(mail_settings.name, mail_settings.sender),
        subject=subject,
        html=html,
        track_opens=True,
        track_clicks=True
    )


def debug_email(recipients, subject, template, mail_settings: MailSettings, context={}):
    print("New email:")
    print("from: {}".format(mail_settings.sender))
    print("to: {}".format(recipients))
    print("subject: {}".format(subject))
    template = Template(template)
    print(template.render(**context))


def send_email(*args, **kwargs):
    if get_settings().debug:
        return debug_email(*args, **kwargs)
    return sparkpost_email(*args, **kwargs)
