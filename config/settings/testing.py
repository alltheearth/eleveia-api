"""
Configurações para ambiente de testes
"""
from .base import *

DEBUG = False

# Usar banco em memória para testes mais rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desabilitar migrações em testes para velocidade
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hasher mais rápido para testes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email para memória
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Desabilitar logging em testes
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Media root temporário
MEDIA_ROOT = '/tmp/media_test'

# Static root temporário
STATIC_ROOT = '/tmp/static_test'