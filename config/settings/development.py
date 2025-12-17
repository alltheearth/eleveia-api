"""
Configurações para ambiente de desenvolvimento
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Adicionar BrowsableAPIRenderer para desenvolvimento
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Email para console (desenvolvimento)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging mais verboso em desenvolvimento
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'