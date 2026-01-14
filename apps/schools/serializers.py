from rest_framework import serializers
from .models import (
    Escola
)

class EscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = [...]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'token_mensagens': {'write_only': True},  # Nunca retornar em GET
        }

    def to_representation(self, instance):
        """Customizar representação para ocultar dados sensíveis"""
        data = super().to_representation(instance)

        request = self.context.get('request')

        # Se não for superuser, ocultar token
        if request and not (request.user.is_superuser or request.user.is_staff):
            data.pop('token_mensagens', None)

        return data