# apps/contacts/services/__init__.py
from .contact_service import ContatoService
from .siga_integration_service import SigaIntegrationService, SigaIntegrationError

__all__ = [
    'ContatoService',
    'SigaIntegrationService',
    'SigaIntegrationError',
]