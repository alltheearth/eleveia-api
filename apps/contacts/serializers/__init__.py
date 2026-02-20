# apps/contacts/serializers/__init__.py

from .contact_serializer import ContatoSerializer, ContatoCreateSerializer
from .guardian_serializers import (
    GuardianListSerializer,
    GuardianDetailSerializer,
    BoletoSerializer,
)
from .invoice_serializers import (
    GuardianInvoicesResponseSerializer,
    GuardianStatsSerializer,
)

__all__ = [
    # Contatos (CRUD local)
    'ContatoSerializer',
    'ContatoCreateSerializer',

    # Guardians (dados do SIGA)
    'GuardianListSerializer',
    'GuardianDetailSerializer',
    'BoletoSerializer',

    # Invoices e Stats
    'GuardianInvoicesResponseSerializer',
    'GuardianStatsSerializer',
]