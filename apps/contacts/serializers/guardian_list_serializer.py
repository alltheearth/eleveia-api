# apps/contacts/serializers/guardian_list_serializer.py

from rest_framework import serializers


class GuardianListSerializer(serializers.Serializer):
    """Serializer leve para listagem de guardians."""

    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=20, allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    telefone = serializers.CharField(max_length=20, allow_null=True, required=False, source='celular')
    whatsapp = serializers.CharField(max_length=20, allow_null=True, required=False, source='celular')
    total_filhos = serializers.SerializerMethodField()
    filhos_nomes = serializers.SerializerMethodField()

    def get_total_filhos(self, obj):
        return len(obj.get('filhos', []))

    def get_filhos_nomes(self, obj):
        return [filho.get('nome', '') for filho in obj.get('filhos', [])]