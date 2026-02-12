# apps/contacts/services/invoice_service.py

"""
Serviço para lógica de negócio de Boletos (Invoices).

Responsabilidades:
- Buscar boletos de um aluno
- Buscar boletos de múltiplos alunos (paralelo)
- Calcular resumos financeiros
- Mapear status de boletos

Não faz:
- Renderização HTTP
- Cache (delega para SigaCacheManager)
- Agregação de guardians
"""

import logging
import requests
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone

from ..integrations.siga_cache_manager import SigaCacheManager

logger = logging.getLogger(__name__)


class InvoiceService:
    """Serviço para gerenciamento de boletos."""

    # Mapeamento de status
    STATUS_MAP = {
        'ABE': 'Aberto',
        'LIQ': 'Liquidado',
        'CAN': 'Cancelado',
    }

    @classmethod
    def get_student_invoices(
            cls,
            student_id: int,
            token: str,
            use_cache: bool = True
    ) -> List[Dict]:
        """
        Busca boletos de um aluno específico.

        Args:
            student_id: ID do aluno
            token: Token de autenticação SIGA
            use_cache: Se deve usar cache (default: True)

        Returns:
            Lista de boletos formatados
        """
        # Tenta cache
        if use_cache:
            cached = SigaCacheManager.get_or_set_student_invoices(student_id)
            if cached:
                return cached

        # Busca do SIGA
        try:
            url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {'id_aluno': student_id}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            invoices_raw = data.get('resultados', [])

            # Formata boletos
            invoices_formatted = [
                cls._format_invoice(invoice)
                for invoice in invoices_raw
            ]

            # Cacheia
            if use_cache:
                SigaCacheManager.get_or_set_student_invoices(
                    student_id,
                    invoices_formatted
                )

            logger.info(f"Fetched {len(invoices_formatted)} invoices for student {student_id}")
            return invoices_formatted

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching invoices for student {student_id}: {e}")
            return []

    @classmethod
    def get_multiple_students_invoices(
            cls,
            student_ids: List[int],
            token: str,
            max_workers: int = 10
    ) -> Dict[int, List[Dict]]:
        """
        Busca boletos de múltiplos alunos EM PARALELO.

        Args:
            student_ids: Lista de IDs de alunos
            token: Token de autenticação SIGA
            max_workers: Número de threads paralelas (default: 10)

        Returns:
            Dict mapeando student_id -> lista de boletos
        """
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Cria futures
            future_to_student = {
                executor.submit(cls.get_student_invoices, student_id, token): student_id
                for student_id in student_ids
            }

            # Processa conforme completam
            for future in as_completed(future_to_student):
                student_id = future_to_student[future]
                try:
                    invoices = future.result()
                    results[student_id] = invoices
                except Exception as e:
                    logger.error(f"Error processing student {student_id}: {e}")
                    results[student_id] = []

        logger.info(f"Fetched invoices for {len(results)} students in parallel")
        return results

    @classmethod
    def _format_invoice(cls, invoice_raw: Dict) -> Dict:
        """
        Formata um boleto do formato SIGA para formato API.

        Args:
            invoice_raw: Boleto no formato SIGA

        Returns:
            Boleto formatado
        """
        return {
            # Identificação
            'titulo': invoice_raw.get('titulo'),
            'parcela': invoice_raw.get('parcela_cobranca', '').strip(),

            # Datas (ISO 8601)
            'vencimento': invoice_raw.get('dt_vencimento'),
            'pagamento': invoice_raw.get('dt_pagamento'),
            'emissao': invoice_raw.get('dt_documento'),

            # Valores
            'valor_original': float(invoice_raw.get('valor_documento', 0)),
            'valor_pago': float(invoice_raw.get('valor_recebido_total', 0)),
            'valor_multa': float(invoice_raw.get('valor_recebido_multa', 0)),
            'valor_juros': float(invoice_raw.get('valor_recebido_juros', 0)),

            # Status
            'situacao': invoice_raw.get('situacao_titulo'),
            'situacao_display': cls.STATUS_MAP.get(
                invoice_raw.get('situacao_titulo'),
                'Desconhecido'
            ),

            # Banco
            'banco': invoice_raw.get('nome_banco'),
            'codigo_banco': invoice_raw.get('cod_banco'),
            'agencia': invoice_raw.get('agencia_codigo_beneficiario'),

            # Pagamento
            'linha_digitavel': invoice_raw.get('linha_digitavel'),
            'codigo_barras': invoice_raw.get('codigo_barras'),
            'link_pagamento': invoice_raw.get('link_pagamento'),

            # Aluno (redundante mas útil)
            'aluno_nome': invoice_raw.get('aluno'),
            'aluno_matricula': invoice_raw.get('aluno_matricula'),
        }

    @classmethod
    def calculate_student_summary(cls, invoices: List[Dict]) -> Dict:
        """
        Calcula resumo financeiro de um aluno.

        Args:
            invoices: Lista de boletos do aluno

        Returns:
            Dict com resumo
        """
        total = len(invoices)
        pagos = sum(1 for inv in invoices if inv['situacao'] == 'LIQ')
        abertos = sum(1 for inv in invoices if inv['situacao'] == 'ABE')
        cancelados = sum(1 for inv in invoices if inv['situacao'] == 'CAN')

        valor_total = sum(inv['valor_original'] for inv in invoices)
        valor_pago = sum(inv['valor_pago'] for inv in invoices)
        valor_pendente = sum(
            inv['valor_original']
            for inv in invoices
            if inv['situacao'] == 'ABE'
        )

        return {
            'total': total,
            'pagos': pagos,
            'abertos': abertos,
            'cancelados': cancelados,
            'valor_total': round(valor_total, 2),
            'valor_pago': round(valor_pago, 2),
            'valor_pendente': round(valor_pendente, 2),
        }

    @classmethod
    def calculate_guardian_summary(cls, filhos: List[Dict]) -> Dict:
        """
        Calcula resumo financeiro geral de um guardian (todos os filhos).

        Args:
            filhos: Lista de filhos com campo 'boletos' e 'resumo_boletos'

        Returns:
            Dict com resumo geral
        """
        total_filhos = len(filhos)
        total_boletos = sum(filho.get('resumo_boletos', {}).get('total', 0) for filho in filhos)
        pagos = sum(filho.get('resumo_boletos', {}).get('pagos', 0) for filho in filhos)
        abertos = sum(filho.get('resumo_boletos', {}).get('abertos', 0) for filho in filhos)
        cancelados = sum(filho.get('resumo_boletos', {}).get('cancelados', 0) for filho in filhos)

        valor_total = sum(filho.get('resumo_boletos', {}).get('valor_total', 0) for filho in filhos)
        valor_pago = sum(filho.get('resumo_boletos', {}).get('valor_pago', 0) for filho in filhos)
        valor_pendente = sum(filho.get('resumo_boletos', {}).get('valor_pendente', 0) for filho in filhos)

        return {
            'total_filhos': total_filhos,
            'total_boletos': total_boletos,
            'pagos': pagos,
            'abertos': abertos,
            'cancelados': cancelados,
            'valor_total': round(valor_total, 2),
            'valor_pago': round(valor_pago, 2),
            'valor_pendente': round(valor_pendente, 2),
        }