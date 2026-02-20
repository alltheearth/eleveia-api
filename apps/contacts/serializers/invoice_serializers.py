# apps/contacts/serializers/invoice_serializers.py

"""
Serializers para endpoints de Boletos e Estatísticas.

ROTAS:
- GET /guardians/{id}/invoices/  → GuardianInvoicesResponseSerializer
- GET /guardians/stats/          → GuardianStatsSerializer
"""

from rest_framework import serializers
from .guardian_serializers import BoletoSerializer


# =====================================================================
# INVOICES — GET /guardians/{id}/invoices/
# =====================================================================

class FilhoInvoicesSerializer(serializers.Serializer):
    """Filho com seus boletos — usado na rota de invoices."""

    id = serializers.IntegerField()
    nome = serializers.CharField()
    matricula = serializers.CharField(allow_null=True, default=None)

    boletos = BoletoSerializer(many=True, default=[])

    resumo = serializers.DictField(default={})
    # resumo contém: total, pagos, abertos, cancelados,
    #                valor_total, valor_pago, valor_pendente


class ResumoGeralInvoicesSerializer(serializers.Serializer):
    """Resumo agregado de todos os filhos."""

    total_filhos = serializers.IntegerField(default=0)
    total_boletos = serializers.IntegerField(default=0)
    total_abertos = serializers.IntegerField(default=0)
    valor_total_pendente = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valor_total_pago = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )


class GuardianInvoicesResponseSerializer(serializers.Serializer):
    """
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    GET /api/v1/contacts/guardians/{id}/invoices/
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Retorna apenas dados financeiros de um guardian.
    Sem dados pessoais, sem endereço — só boletos.

    Suporta filtros:
    - ?ano=2024
    - ?situacao=ABE
    - ?filho_id=2070
    """

    guardian_id = serializers.IntegerField()
    guardian_nome = serializers.CharField()
    ano_filtro = serializers.CharField(allow_null=True, default=None)

    filhos = FilhoInvoicesSerializer(many=True, default=[])
    resumo_geral = ResumoGeralInvoicesSerializer()


# =====================================================================
# STATS — GET /guardians/stats/
# =====================================================================

class FinanceiroStatsSerializer(serializers.Serializer):
    """Estatísticas financeiras globais da escola."""

    total_em_dia = serializers.IntegerField(default=0)
    total_inadimplentes = serializers.IntegerField(default=0)
    percentual_inadimplencia = serializers.DecimalField(
        max_digits=5, decimal_places=1, default=0
    )
    valor_total_pendente = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    valor_total_recebido = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )


class DocumentosStatsSerializer(serializers.Serializer):
    """Estatísticas de documentação da escola."""

    total_completos = serializers.IntegerField(default=0)
    total_incompletos = serializers.IntegerField(default=0)
    percentual_completo = serializers.DecimalField(
        max_digits=5, decimal_places=1, default=0
    )


class DistribuicaoParentescoSerializer(serializers.Serializer):
    """Distribuição de parentesco."""

    mae = serializers.IntegerField(default=0)
    pai = serializers.IntegerField(default=0)
    responsavel_principal = serializers.IntegerField(default=0)
    responsavel_secundario = serializers.IntegerField(default=0)


class GuardianStatsSerializer(serializers.Serializer):
    """
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    GET /api/v1/contacts/guardians/stats/
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Estatísticas globais para dashboard e KPIs.
    """

    total_responsaveis = serializers.IntegerField(default=0)
    total_alunos = serializers.IntegerField(default=0)

    financeiro = FinanceiroStatsSerializer()
    documentos = DocumentosStatsSerializer()
    distribuicao_parentesco = DistribuicaoParentescoSerializer()

    ultima_atualizacao = serializers.DateTimeField(allow_null=True, default=None)