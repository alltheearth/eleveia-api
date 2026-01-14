"""
config/settings/development.py
FIXED VERSION - Resolves LOGGING KeyError
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
# FIX: Ensure 'root' key exists before trying to modify it
if 'root' in LOGGING:
    LOGGING['root']['level'] = 'DEBUG'

if 'loggers' in LOGGING and 'apps' in LOGGING['loggers']:
    LOGGING['loggers']['apps']['level'] = 'DEBUG'