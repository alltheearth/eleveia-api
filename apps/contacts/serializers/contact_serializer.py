# apps/contacts/serializers/contact_serializer.py
from rest_framework import serializers
from ..models import Contato


class ContatoSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Contato.
    REGRA: Apenas validação de campo e transformação.
    Lógica de negócio vai em Services!
    """

    nome_completo = serializers.ReadOnlyField()  # Propriedade do model

    class Meta:
        model = Contato
        fields = [
            'id', 'nome', 'email', 'telefone',
            'ativo', 'nome_completo', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    # ✅ Validação de campo
    def validate_email(self, value):
        """Validação básica de email."""
        if not value or '@' not in value:
            raise serializers.ValidationError("Email inválido")
        return value.lower()

    # ✅ Validação de objeto
    def validate(self, attrs):
        """Validação entre campos."""
        if attrs.get('telefone') and len(attrs['telefone']) < 10:
            raise serializers.ValidationError({
                'telefone': 'Telefone deve ter ao menos 10 dígitos'
            })
        return attrs


class ContatoCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para criação (pode ter campos adicionais)."""

    class Meta:
        model = Contato
        fields = ['nome', 'email', 'telefone']

    # ❌ NÃO fazer lógica de negócio aqui!
    # def create(self, validated_data):
    #     # Toda lógica vai em ContatoService.criar_contato()