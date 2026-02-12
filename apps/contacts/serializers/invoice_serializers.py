# apps/contacts/serializers/invoice_serializers.py

"""
Serializers para Boletos (Invoices).

Responsabilidades:
- Formatação de datas
- Formatação de valores monetários
- Mapeamento de status
- Campos computados
"""

from rest_framework import serializers


class InvoiceSerializer(serializers.Serializer):
    """
    Serializer para boletos (invoices).

    Formata dados de boletos para consumo do frontend.
    """

    # Identificação
    titulo = serializers.IntegerField(
        help_text="Número do título/boleto"
    )

    parcela = serializers.CharField(
        max_length=20,
        help_text="Parcela (ex: '01/12')"
    )

    # Datas (ISO 8601)
    vencimento = serializers.DateTimeField(
        allow_null=True,
        required=False,
        help_text="Data de vencimento"
    )

    pagamento = serializers.DateTimeField(
        allow_null=True,
        required=False,
        help_text="Data de pagamento (null se não pago)"
    )

    emissao = serializers.DateTimeField(
        allow_null=True,
        required=False,
        help_text="Data de emissão"
    )

    # Valores
    valor_original = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor original do boleto"
    )

    valor_pago = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor efetivamente pago"
    )

    valor_multa = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor da multa"
    )

    valor_juros = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor dos juros"
    )

    # Status
    situacao = serializers.CharField(
        max_length=3,
        help_text="Código da situação (ABE/LIQ/CAN)"
    )

    situacao_display = serializers.CharField(
        max_length=50,
        help_text="Situação formatada (Aberto/Liquidado/Cancelado)"
    )

    # Banco
    banco = serializers.CharField(
        max_length=100,
        allow_null=True,
        required=False,
        help_text="Nome do banco"
    )

    codigo_banco = serializers.CharField(
        max_length=10,
        allow_null=True,
        required=False,
        help_text="Código do banco"
    )

    agencia = serializers.CharField(
        max_length=50,
        allow_null=True,
        required=False,
        help_text="Agência e código do beneficiário"
    )

    # Pagamento
    linha_digitavel = serializers.CharField(
        max_length=100,
        allow_null=True,
        required=False,
        help_text="Linha digitável do boleto"
    )

    codigo_barras = serializers.CharField(
        max_length=100,
        allow_null=True,
        required=False,
        help_text="Código de barras"
    )

    link_pagamento = serializers.URLField(
        allow_null=True,
        required=False,
        help_text="URL para pagamento online"
    )

    # Aluno (redundante mas útil)
    aluno_nome = serializers.CharField(
        max_length=255,
        allow_null=True,
        required=False,
        help_text="Nome do aluno"
    )

    aluno_matricula = serializers.CharField(
        max_length=50,
        allow_null=True,
        required=False,
        help_text="Matrícula do aluno"
    )


class InvoiceSummarySerializer(serializers.Serializer):
    """
    Serializer para resumo de boletos.

    Usado em resumos por aluno ou por guardian.
    """

    total = serializers.IntegerField(
        help_text="Total de boletos"
    )

    pagos = serializers.IntegerField(
        help_text="Boletos pagos (LIQ)"
    )

    abertos = serializers.IntegerField(
        help_text="Boletos em aberto (ABE)"
    )

    cancelados = serializers.IntegerField(
        help_text="Boletos cancelados (CAN)"
    )

    valor_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor total de todos os boletos"
    )

    valor_pago = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor total pago"
    )

    valor_pendente = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor pendente (em aberto)"
    )


class StudentWithInvoicesSerializer(serializers.Serializer):
    """
    Serializer para aluno COM boletos.

    Usado no endpoint de detalhes do guardian.
    """

    # Identificação
    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    matricula = serializers.CharField(max_length=50, allow_null=True)
    data_nascimento = serializers.DateField(allow_null=True, required=False)
    sexo = serializers.CharField(max_length=1, allow_null=True, required=False)

    # Acadêmico
    turma = serializers.CharField(max_length=100, allow_null=True, required=False)
    serie = serializers.CharField(max_length=100, allow_null=True, required=False)
    curso = serializers.CharField(max_length=100, allow_null=True, required=False)
    periodo = serializers.CharField(max_length=50, allow_null=True, required=False)
    status = serializers.CharField(max_length=50)

    # Relacionamento
    parentesco = serializers.CharField(max_length=50)
    parentesco_display = serializers.CharField(max_length=100)

    # Boletos
    boletos = InvoiceSerializer(many=True)
    resumo_boletos = InvoiceSummarySerializer()