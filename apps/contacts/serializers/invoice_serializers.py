# apps/contacts/serializers/invoice_serializers.py

from rest_framework import serializers


class InvoiceSerializer(serializers.Serializer):
    """Serializer para boletos."""

    titulo = serializers.IntegerField()
    parcela = serializers.CharField(max_length=20)
    vencimento = serializers.DateTimeField(allow_null=True, required=False)
    pagamento = serializers.DateTimeField(allow_null=True, required=False)
    emissao = serializers.DateTimeField(allow_null=True, required=False)
    valor_original = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_multa = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_juros = serializers.DecimalField(max_digits=10, decimal_places=2)
    situacao = serializers.CharField(max_length=3)
    situacao_display = serializers.CharField(max_length=50)
    banco = serializers.CharField(max_length=100, allow_null=True, required=False)
    linha_digitavel = serializers.CharField(max_length=100, allow_null=True, required=False)
    link_pagamento = serializers.URLField(allow_null=True, required=False)


class InvoiceSummarySerializer(serializers.Serializer):
    """Serializer para resumo de boletos."""

    total = serializers.IntegerField()
    pagos = serializers.IntegerField()
    abertos = serializers.IntegerField()
    cancelados = serializers.IntegerField()
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_pendente = serializers.DecimalField(max_digits=10, decimal_places=2)