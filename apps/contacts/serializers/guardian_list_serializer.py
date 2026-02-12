# apps/contacts/serializers/guardian_list_serializer.py

"""
Serializer LEVE para listagem de guardians.

Usado em: GET /api/v1/contacts/guardians/

Campos incluídos:
- Dados básicos do guardian (nome, CPF, email, telefone)
- Total de filhos (contagem)
- Nomes dos filhos (array simples)

Campos NÃO incluídos:
- Endereço completo
- Dados acadêmicos dos filhos
- Boletos
- Documentos

Objetivo: Performance e payload reduzido
"""

from rest_framework import serializers


class GuardianListSerializer(serializers.Serializer):
    """
    Serializer leve para listagem de guardians.

    Retorna apenas informações essenciais para a lista.
    Para detalhes completos, use GuardianDetailSerializer.
    """

    # Identificação
    id = serializers.IntegerField(
        help_text="ID do guardian no SIGA"
    )

    nome = serializers.CharField(
        max_length=255,
        help_text="Nome completo do guardian"
    )

    # Documentação
    cpf = serializers.CharField(
        max_length=20,
        allow_null=True,
        required=False,
        help_text="CPF formatado (123.456.789-00)"
    )

    # Contato
    email = serializers.EmailField(
        allow_null=True,
        required=False,
        help_text="Email principal"
    )

    telefone = serializers.CharField(
        max_length=20,
        allow_null=True,
        required=False,
        source='celular',
        help_text="Telefone/celular principal"
    )

    whatsapp = serializers.CharField(
        max_length=20,
        allow_null=True,
        required=False,
        source='celular',
        help_text="WhatsApp (igual ao telefone principal)"
    )

    # Resumo de filhos
    total_filhos = serializers.SerializerMethodField(
        help_text="Quantidade total de filhos"
    )

    filhos_nomes = serializers.SerializerMethodField(
        help_text="Lista com nomes dos filhos"
    )

    def get_total_filhos(self, obj) -> int:
        """
        Retorna quantidade de filhos.

        Args:
            obj: Guardian data

        Returns:
            Número de filhos
        """
        return len(obj.get('filhos', []))

    def get_filhos_nomes(self, obj) -> list:
        """
        Retorna lista com nomes dos filhos.

        Args:
            obj: Guardian data

        Returns:
            Lista de nomes (strings)
        """
        return [
            filho.get('nome', '')
            for filho in obj.get('filhos', [])
        ]