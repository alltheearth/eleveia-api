from rest_framework import serializers


class AddressSerializer(serializers.Serializer):
    """Serializer para endereço aninhado do responsável."""
    cep = serializers.CharField(max_length=10, allow_null=True)
    logradouro = serializers.CharField(max_length=255, allow_null=True)
    numero = serializers.CharField(max_length=20, allow_null=True, source='numero_residencia')
    complemento = serializers.CharField(max_length=255, allow_null=True)
    bairro = serializers.CharField(max_length=100, allow_null=True)
    cidade = serializers.CharField(max_length=100, allow_null=True)
    estado = serializers.CharField(max_length=2, allow_null=True, source='uf')


class StudentSummarySerializer(serializers.Serializer):
    """Serializer resumido para alunos vinculados ao responsável."""
    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    turma = serializers.CharField(max_length=100, allow_null=True)
    serie = serializers.CharField(max_length=100, allow_null=True)
    periodo = serializers.CharField(max_length=50, allow_null=True)
    status = serializers.CharField(max_length=50, default='ativo')


class DocumentSerializer(serializers.Serializer):
    """Serializer para documentos do responsável."""
    id = serializers.IntegerField()
    tipo = serializers.CharField(max_length=50)
    nome = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=50)
    data_entrega = serializers.DateField(allow_null=True)


class GuardianDetailSerializer(serializers.Serializer):
    """
    Serializer principal para responsáveis com dados completos.

    Retorna informações do responsável incluindo:
    - Dados pessoais
    - Endereço completo
    - Relacionamento/parentesco
    - Lista de filhos
    - Documentos anexados
    """

    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=14, allow_null=True)
    email = serializers.EmailField(allow_null=True)
    telefone = serializers.CharField(max_length=20, allow_null=True, source='celular')
    telefone_secundario = serializers.CharField(max_length=20, allow_null=True, source='fone')
    whatsapp = serializers.CharField(max_length=20, allow_null=True, source='celular')

    # Endereço aninhado
    endereco = AddressSerializer()

    # Relacionamento
    parentesco = serializers.CharField(max_length=50)
    parentesco_display = serializers.CharField(max_length=100)

    # Responsabilidades
    responsavel_financeiro = serializers.BooleanField(default=False)
    responsavel_pedagogico = serializers.BooleanField(default=False)

    # Relacionamentos aninhados
    filhos = StudentSummarySerializer(many=True)
    documentos = DocumentSerializer(many=True)