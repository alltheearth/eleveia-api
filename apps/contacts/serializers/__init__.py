# apps/contacts/serializers/__init__.py
from .contact_serializer import ContatoSerializer, ContatoCreateSerializer
from .guardian_serializers import GuardianDetailSerializer, StudentSummarySerializer
from .serializers import WhatsAppContactSerializer
from .guardian_unified_serializer import GuardianUnifiedSerializer  # ✨ NOVO

__all__ = [
    'ContatoSerializer',
    'ContatoCreateSerializer',
    'GuardianDetailSerializer',
    'StudentSummarySerializer',
    'WhatsAppContactSerializer',
    'GuardianUnifiedSerializer',  # ✨ NOVO
]