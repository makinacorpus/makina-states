from base import *

DEBUG = False
TEMPLATE_DEBUG = False
STATIC_URL = "/static/"
STATIC_ROOT = "{{ pillar['apps']['ode_frontend']['static_root'] }}"
SECRET_KEY = "{{ pillar['apps']['ode_frontend']['secret_key'] }}"
MEDIA_ROOT = os.path.join(STATIC_ROOT, "media")

# Enable cache busting
STATICFILES_STORAGE = 'django_ode.storage.Storage'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': "{{ pillar['database']['name'] }}",
        'USER': "{{ pillar['database']['username'] }}",
        'PASSWORD': "{{ pillar['database']['password'] }}",
        'HOST': 'localhost',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ADMINS = (
    {% for admin in pillar.get('admins', []) %}
    ("{{ admin['name'] }}", "{{ admin['email'] }}"),
    {% endfor %}
)

ACCOUNTS_MODERATOR_EMAILS = [
    {% for email in pillar.get('moderator_emails', []) %}
    '{{ email }}',
    {% endfor %}
]

ALLOWED_HOSTS = [
    {% for allowed_host in pillar.get('allowed_hosts', []) %}
    '{{ allowed_host }}',
    {% endfor %}
]

DEFAULT_FROM_EMAIL = "{{ pillar['default_from_email'] }}"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EVENT_API_BASE_URL = "http://localhost:{{ pillar['apps']['ode_api']['port'] }}"
SOURCES_ENDPOINT = EVENT_API_BASE_URL + '/v1/sources'
EVENTS_ENDPOINT = EVENT_API_BASE_URL + '/v1/events'
