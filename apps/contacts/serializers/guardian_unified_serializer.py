# apps/contacts/serializers/guardian_unified_serializer.py

from rest_framework import serializers


class InvoiceSerializer(serializers.Serializer):
    """Serializer para boletos dos alunos."""

    invoice_number = serializers.CharField(max_length=100, allow_null=True)
    bank = serializers.CharField(max_length=255, allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    payment_date = serializers.DateField(allow_null=True)
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True
    )
    received_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True
    )
    status_code = serializers.CharField(max_length=10)
    status_display = serializers.CharField(max_length=50)
    installment = serializers.CharField(max_length=20, allow_null=True)
    digitable_line = serializers.CharField(max_length=255, allow_null=True)
    payment_url = serializers.URLField(max_length=500, allow_null=True)


class DocumentoFaltanteSerializer(serializers.Serializer):
    """Serializer para documentos faltantes dos alunos."""

    tipo = serializers.CharField(max_length=50)
    nome = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=50, allow_null=True)


class StudentWithInvoicesSerializer(serializers.Serializer):
    """Serializer para alunos com boletos integrados."""

    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    turma = serializers.CharField(max_length=100, allow_null=True, required=False)
    serie = serializers.CharField(max_length=100, allow_null=True, required=False)
    periodo = serializers.CharField(max_length=50, allow_null=True, required=False)
    status = serializers.CharField(max_length=50, default='ativo')

    # ✨ NOVO: Boletos do filho
    boletos = InvoiceSerializer(many=True)

    # ✨ NOVO: Documentos faltantes (vazio por hora)
    documentos_faltantes = DocumentoFaltanteSerializer(many=True)


class AddressSerializer(serializers.Serializer):
    """Serializer para endereço do responsável."""

    cep = serializers.CharField(max_length=10, allow_null=True, required=False)
    logradouro = serializers.CharField(max_length=255, allow_null=True, required=False)
    numero = serializers.CharField(max_length=20, allow_null=True, required=False)
    complemento = serializers.CharField(max_length=255, allow_null=True, required=False)
    bairro = serializers.CharField(max_length=100, allow_null=True, required=False)
    cidade = serializers.CharField(max_length=100, allow_null=True, required=False)
    estado = serializers.CharField(max_length=2, allow_null=True, required=False)


class DocumentoResponsavelSerializer(serializers.Serializer):
    """Serializer para documentos do responsável."""

    id = serializers.IntegerField()
    tipo = serializers.CharField(max_length=50)
    nome = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=50, allow_null=True, required=False)
    data_entrega = serializers.DateField(allow_null=True, required=False, default=None)


class DocumentosEstruturadosSerializer(serializers.Serializer):
    """Estrutura de documentos: responsável + alunos."""

    responsavel = DocumentoResponsavelSerializer(many=True)
    aluno = DocumentoFaltanteSerializer(many=True)  # Vazio por hora


class SituacaoSerializer(serializers.Serializer):
    """Serializer para situação agregada do responsável."""

    tem_boleto_aberto = serializers.BooleanField()
    tem_doc_faltando = serializers.BooleanField()
    total_boletos_abertos = serializers.IntegerField()
    valor_total_aberto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    total_docs_faltando = serializers.IntegerField()


class GuardianUnifiedSerializer(serializers.Serializer):
    """
    ✨ SERIALIZER UNIFICADO - Responsáveis com tudo!

    Retorna:
    - Dados pessoais do responsável
    - Endereço completo
    - Relacionamento/parentesco
    - Situação agregada (boletos, docs)
    - Lista de filhos COM boletos
    - Documentos (responsável + alunos)
    """

    # Dados pessoais
    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=14, allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    telefone = serializers.CharField(max_length=20, allow_null=True, required=False)

    # Endereço
    endereco = AddressSerializer()

    # Relacionamento
    parentesco = serializers.CharField(max_length=50)
    parentesco_display = serializers.CharField(max_length=100)

    # Responsabilidades
    responsavel_financeiro = serializers.BooleanField(default=False)
    responsavel_pedagogico = serializers.BooleanField(default=False)

    # ✨ NOVO: Situação agregada
    situacao = SituacaoSerializer()

    # ✨ Filhos com boletos
    filhos = StudentWithInvoicesSerializer(many=True)

    # ✨ Documentos estruturados
    documentos = DocumentosEstruturadosSerializer()