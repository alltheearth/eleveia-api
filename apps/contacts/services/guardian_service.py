# apps/contacts/services/guardian_service.py

"""
Serviço para lógica de negócio de Guardians.

Responsabilidades:
- Orquestrar busca de guardians (SIGA + Cache + Aggregator)
- Enriquecer guardians com boletos
- Aplicar regras de negócio
- Gerenciar cache estratégico

Não faz:
- Renderização HTTP
- Filtros (delega para Selectors)
- Validação de serializers
"""

import logging
from typing import List, Dict, Optional

from ..integrations.siga_cache_manager import SigaCacheManager
from .guardian_aggregator_service import GuardianAggregatorService
from .invoice_service import InvoiceService

logger = logging.getLogger(__name__)


class GuardianService:
    """Serviço para orquestração de Guardians."""

    @classmethod
    def get_guardians_list(
            cls,
            school_id: int,
            token: str
    ) -> List[Dict]:
        """
        Busca lista de guardians (SEM boletos).

        Fluxo:
        1. Busca dados do SIGA (com cache individual por API)
        2. Agrega dados (JOIN)
        3. Retorna guardians enriquecidos

        Args:
            school_id: ID da escola
            token: Token de autenticação SIGA

        Returns:
            Lista de guardians enriquecidos (sem boletos)
        """
        logger.info(f"Fetching guardians list for school {school_id}")

        # 1. Busca dados SIGA (com cache)
        all_data = SigaCacheManager.get_or_fetch_all_siga_data(school_id, token)

        # 2. Agrega
        aggregator = GuardianAggregatorService()
        guardians = aggregator.build_guardians_response(
            guardians=all_data['guardians'],
            students_relations=all_data['students_relations'],
            students_academic=all_data['students_academic']
        )

        logger.info(f"Fetched {len(guardians)} guardians for school {school_id}")
        return guardians

    @classmethod
    def get_guardian_detail(
            cls,
            guardian_id: int,
            school_id: int,
            token: str,
            include_invoices: bool = True
    ) -> Optional[Dict]:
        """
        Busca detalhes completos de um guardian (COM boletos).

        Fluxo:
        1. Busca lista de guardians
        2. Encontra o guardian específico
        3. Enriquece com boletos (paralelo)
        4. Calcula resumos
        5. Cacheia detalhes (6h)

        Args:
            guardian_id: ID do guardian
            school_id: ID da escola
            token: Token de autenticação SIGA
            include_invoices: Se deve incluir boletos (default: True)

        Returns:
            Guardian completo ou None se não encontrado
        """
        logger.info(f"Fetching guardian detail: {guardian_id} (school: {school_id})")

        # 1. Busca lista de guardians
        guardians = cls.get_guardians_list(school_id, token)

        # 2. Encontra o guardian
        guardian = next((g for g in guardians if g['id'] == guardian_id), None)

        if not guardian:
            logger.warning(f"Guardian {guardian_id} not found in school {school_id}")
            return None

        # 3. Enriquece com boletos (se solicitado)
        if include_invoices:
            guardian = cls._enrich_with_invoices(guardian, token)

        # 4. Cacheia detalhes (6h)
        SigaCacheManager.get_or_fetch_guardian_detail(
            guardian_id=guardian_id,
            school_id=school_id,
            guardian_data=guardian
        )

        logger.info(f"Guardian {guardian_id} fetched successfully")
        return guardian

    @classmethod
    def _enrich_with_invoices(cls, guardian: Dict, token: str) -> Dict:
        """
        Enriquece guardian com boletos de todos os filhos.

        Args:
            guardian: Dados do guardian
            token: Token SIGA

        Returns:
            Guardian enriquecido com boletos
        """
        filhos = guardian.get('filhos', [])

        if not filhos:
            logger.info(f"Guardian {guardian['id']} has no children")
            guardian['resumo_geral_boletos'] = cls._empty_summary()
            return guardian

        # Busca boletos em paralelo
        student_ids = [filho['id'] for filho in filhos]
        invoices_by_student = InvoiceService.get_multiple_students_invoices(
            student_ids=student_ids,
            token=token,
            max_workers=10
        )

        # Adiciona boletos a cada filho
        for filho in filhos:
            student_id = filho['id']
            invoices = invoices_by_student.get(student_id, [])

            filho['boletos'] = invoices
            filho['resumo_boletos'] = InvoiceService.calculate_student_summary(invoices)

        # Calcula resumo geral
        guardian['resumo_geral_boletos'] = InvoiceService.calculate_guardian_summary(filhos)

        logger.info(
            f"Enriched guardian {guardian['id']} with invoices "
            f"({guardian['resumo_geral_boletos']['total_boletos']} total)"
        )

        return guardian

    @classmethod
    def _empty_summary(cls) -> Dict:
        """Retorna resumo vazio (quando guardian não tem filhos)."""
        return {
            'total_filhos': 0,
            'total_boletos': 0,
            'pagos': 0,
            'abertos': 0,
            'cancelados': 0,
            'valor_total': 0.0,
            'valor_pago': 0.0,
            'valor_pendente': 0.0,
        }