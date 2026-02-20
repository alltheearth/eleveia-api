# apps/contacts/serializers/guardian_serializers.py

"""
Serializers DEFINITIVOS para Guardians (Responsáveis).

CONTRATO: O que está aqui = o que o frontend recebe.
          O frontend NÃO precisa de adapter/transformação.

Dois níveis:
- GuardianListSerializer  → GET /guardians/       (cards, SEM boletos)
- GuardianDetailSerializer → GET /guardians/{id}/  (completo, COM boletos)

Compartilham sub-serializers para consistência.
"""

from rest_framework import serializers


# =====================================================================
# SUB-SERIALIZERS COMPARTILHADOS
# =====================================================================

class EnderecoSerializer(serializers.Serializer):
    """
    Endereço do responsável.
    Usado tanto na lista quanto no detalhe.
    """
    logradouro = serializers.CharField(allow_null=True, default=None)
    complemento = serializers.CharField(allow_null=True, default=None)
    bairro = serializers.CharField(allow_null=True, default=None)
    cidade = serializers.CharField(allow_null=True, default=None)
    uf = serializers.CharField(allow_null=True, default=None)
    cep = serializers.CharField(allow_null=True, default=None)


class ResumoFinanceiroSerializer(serializers.Serializer):
    """
    Resumo financeiro para o CARD da lista.
    Não inclui boletos individuais — só totalizadores.
    """
    tem_pendencia = serializers.BooleanField(default=False)
    total_abertos = serializers.IntegerField(default=0)
    valor_pendente = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    proximo_vencimento = serializers.CharField(allow_null=True, default=None)


class ResumoDocumentosSerializer(serializers.Serializer):
    """
    Resumo de documentos para o CARD da lista.
    """
    total = serializers.IntegerField(default=0)
    entregues = serializers.IntegerField(default=0)
    pendentes = serializers.IntegerField(default=0)
    completo = serializers.BooleanField(default=False)


# =====================================================================
# SERIALIZERS DE FILHOS
# =====================================================================

class FilhoResumoSerializer(serializers.Serializer):
    """
    Filho resumido — usado na LISTA.
    Só nome, turma, série, período, status. Sem boletos.
    """
    id = serializers.IntegerField()
    nome = serializers.CharField()
    turma = serializers.CharField(allow_null=True, default=None)
    serie = serializers.CharField(allow_null=True, default=None)
    turma_nome = serializers.CharField(allow_null=True, default=None)
    periodo = serializers.CharField(allow_null=True, default=None)
    status = serializers.CharField(default='ativo')


class ResumoBoletosPorFilhoSerializer(serializers.Serializer):
    """
    Totalizadores de boletos de UM filho.
    Usado no detalhe, dentro de cada filho.
    """
    total = serializers.IntegerField(default=0)
    pagos = serializers.IntegerField(default=0)
    abertos = serializers.IntegerField(default=0)
    cancelados = serializers.IntegerField(default=0)
    valor_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valor_pago = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valor_pendente = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )


class BoletoSerializer(serializers.Serializer):
    """
    Um boleto individual.
    Só aparece no DETALHE (dentro de cada filho).
    """
    numero = serializers.IntegerField()
    parcela = serializers.CharField()
    vencimento = serializers.CharField(allow_null=True, default=None)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valor_multa = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    valor_juros = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    situacao = serializers.CharField()  # ABE, LIQ, CAN
    situacao_display = serializers.CharField()
    banco = serializers.CharField(allow_null=True, default=None)
    linha_digitavel = serializers.CharField(allow_null=True, default=None)
    link_pagamento = serializers.CharField(allow_null=True, default=None)
    servico = serializers.CharField(allow_null=True, default=None)


class FilhoDetalheSerializer(serializers.Serializer):
    """
    Filho completo — usado no DETALHE.
    Inclui matrícula, foto, boletos e resumo.
    """
    id = serializers.IntegerField()
    nome = serializers.CharField()
    matricula = serializers.CharField(allow_null=True, default=None)
    turma = serializers.CharField(allow_null=True, default=None)
    serie = serializers.CharField(allow_null=True, default=None)
    turma_nome = serializers.CharField(allow_null=True, default=None)
    periodo = serializers.CharField(allow_null=True, default=None)
    status = serializers.CharField(default='ativo')
    url_foto = serializers.CharField(allow_null=True, default=None)
    boletos = BoletoSerializer(many=True, default=[])
    resumo_boletos = ResumoBoletosPorFilhoSerializer(default={})


class DocumentoSerializer(serializers.Serializer):
    """
    Um documento do responsável.
    Só aparece no DETALHE.
    """
    id = serializers.IntegerField()
    tipo = serializers.CharField()
    nome = serializers.CharField()
    status = serializers.CharField(allow_null=True, default='pendente')
    data_entrega = serializers.CharField(allow_null=True, default=None)


# =====================================================================
# SERIALIZERS PRINCIPAIS
# =====================================================================

class GuardianListSerializer(serializers.Serializer):
    """
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    LISTA — GET /api/v1/contacts/guardians/
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Usado para renderizar CARDS na página de contatos.

    Inclui:
    ✓ Dados pessoais básicos
    ✓ Endereço
    ✓ Parentesco
    ✓ Filhos (resumido: nome + turma + status)
    ✓ Resumo financeiro (tem pendência? valor?)
    ✓ Resumo de documentos (completo? quantos faltam?)

    NÃO inclui:
    ✗ Boletos individuais
    ✗ Dados sensíveis (RG, data nascimento, profissão)
    ✗ Matrícula e foto dos filhos
    """

    # Dados pessoais básicos
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField(allow_null=True, default=None)
    email = serializers.CharField(allow_null=True, default=None)
    telefone = serializers.CharField(allow_null=True, default=None)
    sexo = serializers.CharField(allow_null=True, default=None)

    # Endereço
    endereco = EnderecoSerializer()

    # Parentesco
    parentesco = serializers.CharField()
    parentesco_display = serializers.CharField()

    # Filhos (resumido)
    filhos = FilhoResumoSerializer(many=True, default=[])

    # Resumos (calculados)
    resumo_financeiro = ResumoFinanceiroSerializer()
    resumo_documentos = ResumoDocumentosSerializer()


class ResumoFinanceiroCompletoSerializer(serializers.Serializer):
    """
    Resumo financeiro expandido — só no DETALHE.
    Inclui totais de pagos e cancelados além dos abertos.
    """
    tem_pendencia = serializers.BooleanField(default=False)
    total_abertos = serializers.IntegerField(default=0)
    valor_pendente = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    total_pagos = serializers.IntegerField(default=0)
    valor_pago = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    total_cancelados = serializers.IntegerField(default=0)


class GuardianDetailSerializer(serializers.Serializer):
    """
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    DETALHE — GET /api/v1/contacts/guardians/{id}/
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Usado quando o usuário clica num card para ver tudo.

    Inclui TUDO da lista +:
    ✓ Dados sensíveis (RG, nascimento, profissão, etc.)
    ✓ Telefone fixo
    ✓ Filhos com matrícula, foto, boletos individuais
    ✓ Documentos detalhados
    ✓ Resumo financeiro expandido
    """

    # Dados pessoais (básicos — mesmos da lista)
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField(allow_null=True, default=None)
    email = serializers.CharField(allow_null=True, default=None)
    telefone = serializers.CharField(allow_null=True, default=None)
    sexo = serializers.CharField(allow_null=True, default=None)

    # Dados pessoais (extras — SÓ no detalhe)
    telefone_fixo = serializers.CharField(allow_null=True, default=None)
    data_nascimento = serializers.CharField(allow_null=True, default=None)
    estado_civil = serializers.CharField(allow_null=True, default=None)
    rg = serializers.CharField(allow_null=True, default=None)
    rg_orgao = serializers.CharField(allow_null=True, default=None)
    profissao = serializers.CharField(allow_null=True, default=None)
    local_trabalho = serializers.CharField(allow_null=True, default=None)

    # Endereço
    endereco = EnderecoSerializer()

    # Parentesco
    parentesco = serializers.CharField()
    parentesco_display = serializers.CharField()

    # Filhos (completo, COM boletos)
    filhos = FilhoDetalheSerializer(many=True, default=[])

    # Documentos detalhados
    documentos = DocumentoSerializer(many=True, default=[])

    # Resumos (expandidos)
    resumo_financeiro = ResumoFinanceiroCompletoSerializer()
    resumo_documentos = ResumoDocumentosSerializer()