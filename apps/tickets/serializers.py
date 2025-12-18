# eleveai/serializers.py
from rest_framework import serializers

from .models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer para Escola

    CAMPOS PROTEGIDOS (só superuser pode alterar):
    - nome_escola
    - cnpj
    - token_mensagens
    """

    class Meta:
        model = Ticket
        fields = [
            'id', 'title','description', 'title', 'created_at', 'updated_at', 'school', 'status', 'priority'
        ]

