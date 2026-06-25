from os import environ as env


DEBUG = env.get('DEBUG', 'False') == 'True'
BROKER = env.get('BROKER', 'redis://redis:6379/2')
RESULT_BACKEND = env.get('RESULT_BACKEND', 'redis://redis:6379/3')

TEMPLATE_DIR = env.get('TEMPLATE_DIR', None)
# validation timeout in days
VALIDATION_TIMEOUT = int(env.get('VALIDATION_TIMEOUT', '30'))
# Timeout to run the clean email task every X seconds
CLEAN_EMAILS_TIMEOUT = int(env.get('CLEAN_EMAILS_TIMEOUT', '300'))

ALERT_BANNER_URL = env.get('ALERT_BANNER_URL', '')

CACHE_REDIS_DB = int(env.get('CACHE_REDIS_DB_NAME', '8'))
CACHE_REDIS_HOST = env.get('CACHE_REDIS_HOST', 'redis')
CACHE_REDIS_PORT = int(env.get('CACHE_REDIS_PORT', '6379'))

SCANNED_TEXT_EXCERPT_SIZE = int(env.get('SCANNED_TEXT_EXCERPT_SIZE', '500'))

def mail_config(kb):
    roots = {
            'politicas': 'TIPI',
            'ods': 'P2030',
            'escaner': 'SCANNER'
            }

    fields = [
            'NAME',
            'FROM',
            'DESCRIPTION',
            'EMAIL',
            'FRONTEND',
            'BACKEND',
            'COLOR',
            'API',
            'BANNER_URL',
            'ALERT_SUBJECT',
            'VALIDATION_SUBJECT',
            ]

    root = roots[kb]
    configuration = {}

    for field in fields:
        key = root + '_' + field
        configuration[field] = env.get(key)

    return configuration
