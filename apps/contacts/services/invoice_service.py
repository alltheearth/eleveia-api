# apps/contacts/services/invoice_service.py

"""
Serviço de Boletos (Invoices).

Responsabilidades:
- Buscar boletos de alunos na API SIGA
- Formatar dados brutos para o contrato da API
- Calcular resumos financeiros
- Busca paralela para múltiplos alunos
- Filtros por ano, situação e filho

NÃO faz:
- Cache (delega para SigaCacheManager)
- Renderização HTTP
- Agregação de responsáveis
"""

import logging
import requests
from typing import List, Dict, Optional
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..integrations.siga_cache_manager import SigaCacheManager

logger = logging.getLogger(__name__)

# Mapeamento de situação
SITUACAO_DISPLAY = {
    'ABE': 'Aberto',
    'LIQ': 'Liquidado',
    'CAN': 'Cancelado',
}

SIGA_INVOICES_URL = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"


class InvoiceService:
    """Serviço para gerenciamento de boletos."""

    # -----------------------------------------------------------------
    # BUSCA DE BOLETOS (um aluno)
    # -----------------------------------------------------------------

    @classmethod
    def get_student_invoices(
        cls,
        student_id: int,
        token: str,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Busca boletos de um aluno específico.

        Args:
            student_id: ID do aluno no SIGA
            token: Token de autenticação SIGA
            use_cache: Se deve usar cache Redis

        Returns:
            Lista de boletos formatados (contrato BoletoSerializer)
        """
        # Tentar cache
        if use_cache:
            cached = SigaCacheManager.get_or_set_student_invoices(student_id)
            if cached is not None:
                return cached

        # Buscar do SIGA
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                SIGA_INVOICES_URL,
                headers=headers,
                params={'id_aluno': student_id},
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            raw_invoices = data.get('resultados', [])

            # Formatar cada boleto
            formatted = [cls._format_invoice(inv) for inv in raw_invoices]

            # Cachear
            if use_cache:
                SigaCacheManager.get_or_set_student_invoices(
                    student_id, formatted
                )

            logger.debug(
                f"Fetched {len(formatted)} invoices for student {student_id}"
            )
            return formatted

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching invoices for student {student_id}: {e}"
            )
            return []

    # -----------------------------------------------------------------
    # BUSCA DE BOLETOS (múltiplos alunos — PARALELO)
    # -----------------------------------------------------------------

    @classmethod
    def get_multiple_students_invoices(
        cls,
        student_ids: List[int],
        token: str,
        max_workers: int = 10,
    ) -> Dict[int, List[Dict]]:
        """
        Busca boletos de múltiplos alunos em paralelo.

        Args:
            student_ids: Lista de IDs dos alunos
            token: Token SIGA
            max_workers: Threads paralelas (default: 10)

        Returns:
            Dict {student_id: [boletos_formatados]}
        """
        if not student_ids:
            return {}

        result = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(cls.get_student_invoices, sid, token): sid
                for sid in student_ids
            }

            for future in as_completed(futures):
                student_id = futures[future]
                try:
                    invoices = future.result()
                    result[student_id] = invoices
                except Exception as e:
                    logger.error(
                        f"Error fetching invoices for student {student_id}: {e}"
                    )
                    result[student_id] = []

        return result

    # -----------------------------------------------------------------
    # ENDPOINT: GET /guardians/{id}/invoices/
    # -----------------------------------------------------------------

    @classmethod
    def get_guardian_invoices(
        cls,
        guardian_id: int,
        school_id: int,
        token: str,
        ano: Optional[str] = None,
        situacao: Optional[str] = None,
        filho_id: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Busca boletos de um guardian (todos os filhos).
        Usado pela rota GET /guardians/{id}/invoices/

        Returns:
            Dict no formato GuardianInvoicesResponseSerializer ou None
        """
        from .guardian_service import GuardianService

        # Buscar guardian (do cache da lista, sem boletos)
        guardians = GuardianService.get_guardians_list(school_id, token)
        guardian = next(
            (g for g in guardians if g['id'] == guardian_id), None
        )

        if not guardian:
            return None

        filhos = guardian.get('filhos', [])

        # Filtrar por filho específico
        if filho_id:
            filhos = [f for f in filhos if f.get('id') == filho_id]

        # Buscar boletos de todos os filhos
        student_ids = [f['id'] for f in filhos if f.get('id')]
        invoices_by_student = cls.get_multiple_students_invoices(
            student_ids, token
        )

        # Montar resposta
        filhos_response = []
        total_geral = {
            'total_boletos': 0,
            'total_abertos': 0,
            'valor_total_pendente': Decimal('0'),
            'valor_total_pago': Decimal('0'),
        }

        for filho in filhos:
            sid = filho.get('id')
            invoices = invoices_by_student.get(sid, [])

            # Aplicar filtros
            if ano:
                invoices = [
                    inv for inv in invoices
                    if inv.get('vencimento', '').startswith(ano)
                ]

            if situacao and situacao != 'todos':
                invoices = [
                    inv for inv in invoices
                    if inv.get('situacao') == situacao
                ]

            resumo = cls.calculate_student_summary(invoices)

            filhos_response.append({
                'id': sid,
                'nome': filho.get('nome'),
                'matricula': filho.get('matricula'),
                'boletos': invoices,
                'resumo': resumo,
            })

            # Acumular totais
            total_geral['total_boletos'] += resumo.get('total', 0)
            total_geral['total_abertos'] += resumo.get('abertos', 0)
            total_geral['valor_total_pendente'] += Decimal(
                str(resumo.get('valor_pendente', 0))
            )
            total_geral['valor_total_pago'] += Decimal(
                str(resumo.get('valor_pago', 0))
            )

        return {
            'guardian_id': guardian_id,
            'guardian_nome': guardian.get('nome'),
            'ano_filtro': ano,
            'filhos': filhos_response,
            'resumo_geral': {
                'total_filhos': len(filhos_response),
                'total_boletos': total_geral['total_boletos'],
                'total_abertos': total_geral['total_abertos'],
                'valor_total_pendente': float(
                    total_geral['valor_total_pendente']
                ),
                'valor_total_pago': float(total_geral['valor_total_pago']),
            },
        }

    # -----------------------------------------------------------------
    # CÁLCULOS: resumos financeiros
    # -----------------------------------------------------------------

    @classmethod
    def calculate_student_summary(cls, invoices: List[Dict]) -> Dict:
        """
        Calcula resumo financeiro de uma lista de boletos.
        Usado para resumo de cada filho.
        """
        if not invoices:
            return {
                'total': 0,
                'pagos': 0,
                'abertos': 0,
                'cancelados': 0,
                'valor_total': 0,
                'valor_pago': 0,
                'valor_pendente': 0,
            }

        pagos = [i for i in invoices if i.get('situacao') == 'LIQ']
        abertos = [i for i in invoices if i.get('situacao') == 'ABE']
        cancelados = [i for i in invoices if i.get('situacao') == 'CAN']

        valor_total = sum(
            float(i.get('valor', 0) or 0) for i in invoices
        )
        valor_pago = sum(
            float(i.get('valor_pago', 0) or 0) for i in pagos
        )
        valor_pendente = sum(
            float(i.get('valor', 0) or 0) for i in abertos
        )

        return {
            'total': len(invoices),
            'pagos': len(pagos),
            'abertos': len(abertos),
            'cancelados': len(cancelados),
            'valor_total': round(valor_total, 2),
            'valor_pago': round(valor_pago, 2),
            'valor_pendente': round(valor_pendente, 2),
        }

    @classmethod
    def calculate_guardian_summary(cls, filhos: List[Dict]) -> Dict:
        """
        Calcula resumo geral de um guardian (todos os filhos).
        """
        total = pagos = abertos = cancelados = 0
        valor_total = valor_pago = valor_pendente = 0.0

        for filho in filhos:
            resumo = filho.get('resumo_boletos', {})
            total += resumo.get('total', 0)
            pagos += resumo.get('pagos', 0)
            abertos += resumo.get('abertos', 0)
            cancelados += resumo.get('cancelados', 0)
            valor_total += float(resumo.get('valor_total', 0))
            valor_pago += float(resumo.get('valor_pago', 0))
            valor_pendente += float(resumo.get('valor_pendente', 0))

        return {
            'total_boletos': total,
            'total_pagos': pagos,
            'total_abertos': abertos,
            'total_cancelados': cancelados,
            'valor_total': round(valor_total, 2),
            'valor_pago': round(valor_pago, 2),
            'valor_pendente': round(valor_pendente, 2),
        }

    # -----------------------------------------------------------------
    # FORMATAÇÃO: SIGA → contrato da API
    # -----------------------------------------------------------------

    @classmethod
    def _format_invoice(cls, raw: Dict) -> Dict:
        """
        Formata um boleto bruto do SIGA para o contrato BoletoSerializer.

        Mapeamento:
            SIGA                    → API
            titulo                  → numero
            parcela_cobranca        → parcela
            dt_vencimento           → vencimento
            valor_documento         → valor
            valor_recebido_total    → valor_pago
            valor_recebido_multa    → valor_multa
            valor_recebido_juros    → valor_juros
            situacao_titulo         → situacao
            nome_banco              → banco
            linha_digitavel         → linha_digitavel
            link_pagamento          → link_pagamento
            nome_servico            → servico
        """
        situacao = (raw.get('situacao_titulo') or '').strip()

        # Data de vencimento (só data, sem horário)
        vencimento_raw = raw.get('dt_vencimento')
        vencimento = None
        if vencimento_raw:
            vencimento = str(vencimento_raw).split('T')[0]

        return {
            'numero': raw.get('titulo'),
            'parcela': (raw.get('parcela_cobranca') or '').strip(),
            'vencimento': vencimento,
            'valor': float(raw.get('valor_documento', 0) or 0),
            'valor_pago': float(raw.get('valor_recebido_total', 0) or 0),
            'valor_multa': float(raw.get('valor_recebido_multa', 0) or 0),
            'valor_juros': float(raw.get('valor_recebido_juros', 0) or 0),
            'situacao': situacao,
            'situacao_display': SITUACAO_DISPLAY.get(situacao, situacao),
            'banco': raw.get('nome_banco'),
            'linha_digitavel': raw.get('linha_digitavel'),
            'link_pagamento': raw.get('link_pagamento'),
            'servico': raw.get('nome_servico'),
        }