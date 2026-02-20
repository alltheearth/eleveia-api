# apps/contacts/services/guardian_service.py

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GuardianService — Orquestrador Principal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este é o CÉREBRO da aplicação. Orquestra:
- SigaCacheManager (cache das 3 APIs)
- GuardianAggregatorService (JOIN das APIs)
- InvoiceService (boletos)

Métodos públicos (chamados pelo ViewSet):
- get_guardians_list()   → Lista SEM boletos, COM resumos
- get_guardian_detail()   → Detalhe COM boletos
- get_stats()             → Estatísticas globais
- invalidate_cache()      → Limpa cache

NÃO faz:
- HTTP (ViewSet faz isso)
- Filtros/ordenação (Selectors fazem isso)
- Serialização (Serializers fazem isso)
"""

import logging
from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime

from django.utils import timezone

from ..integrations.siga_cache_manager import SigaCacheManager
from .guardian_aggregator_service import GuardianAggregatorService
from .invoice_service import InvoiceService

logger = logging.getLogger(__name__)


class GuardianService:
    """Serviço de orquestração para Guardians."""

    # Cache key para a lista processada (com resumos)
    CACHE_KEY_LIST = "guardians:school:{school_id}:processed_list"
    CACHE_TTL_LIST = 7200  # 2 horas

    # =================================================================
    # LIST — GET /guardians/
    # =================================================================

    @classmethod
    def get_guardians_list(
        cls,
        school_id: int,
        token: str,
    ) -> List[Dict]:
        """
        Retorna lista de guardians com resumos (SEM boletos individuais).

        Fluxo:
        1. Checa cache da lista processada
        2. Se cache miss → busca 3 APIs SIGA (cada uma com cache próprio)
        3. Agrega (JOIN)
        4. Calcula resumo_financeiro e resumo_documentos por guardian
        5. Cacheia resultado processado (2h)

        Returns:
            Lista de dicts prontos para GuardianListSerializer
        """
        # 1. Tentar cache da lista processada
        cache_key = cls.CACHE_KEY_LIST.format(school_id=school_id)
        cached = SigaCacheManager._safe_cache_get(cache_key)
        if cached:
            logger.info(f"Cache HIT: processed list for school {school_id}")
            return cached

        logger.info(f"Building guardians list for school {school_id}")

        # 2. Buscar dados brutos do SIGA (cada API com cache individual)
        all_data = SigaCacheManager.get_or_fetch_all_siga_data(
            school_id, token
        )

        # 3. Agregar (JOIN das 3 APIs)
        aggregator = GuardianAggregatorService()
        guardians = aggregator.build_guardians_response(
            guardians=all_data['guardians'],
            students_relations=all_data['students_relations'],
            students_academic=all_data['students_academic'],
        )

        # 4. Adicionar resumos (financeiro e documentos)
        for guardian in guardians:
            guardian['resumo_financeiro'] = cls._build_resumo_financeiro_lista(
                guardian
            )
            guardian['resumo_documentos'] = cls._build_resumo_documentos(
                guardian
            )

        # 5. Cachear lista processada
        SigaCacheManager._safe_cache_set(
            cache_key, guardians, cls.CACHE_TTL_LIST
        )

        logger.info(
            f"Built and cached {len(guardians)} guardians for school {school_id}"
        )
        return guardians

    # =================================================================
    # DETAIL — GET /guardians/{id}/
    # =================================================================

    @classmethod
    def get_guardian_detail(
        cls,
        guardian_id: int,
        school_id: int,
        token: str,
        ano_letivo: Optional[str] = None,
        situacao_boleto: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Retorna detalhe completo de um guardian COM boletos.

        Fluxo:
        1. Checa cache do detalhe
        2. Se cache miss → busca guardian da lista + boletos
        3. Aplica filtros de boleto (ano, situação)
        4. Calcula resumos completos
        5. Cacheia detalhe (1h)

        Returns:
            Dict pronto para GuardianDetailSerializer ou None
        """
        logger.info(f"Fetching detail for guardian {guardian_id}")

        # 1. Tentar cache do detalhe (só se sem filtros)
        if not ano_letivo and not situacao_boleto:
            cached = SigaCacheManager._safe_cache_get(
                SigaCacheManager.KEY_GUARDIAN_DETAIL.format(
                    guardian_id=guardian_id, school_id=school_id
                )
            )
            if cached:
                logger.info(f"Cache HIT: detail for guardian {guardian_id}")
                return cached

        # 2. Buscar guardian da lista (já agregado, sem boletos)
        guardians = cls.get_guardians_list(school_id, token)
        guardian = next(
            (g for g in guardians if g['id'] == guardian_id), None
        )

        if not guardian:
            logger.warning(f"Guardian {guardian_id} not found")
            return None

        # Copiar para não mutar o cache da lista
        guardian = {**guardian}

        # 3. Buscar boletos de todos os filhos (paralelo)
        filhos = guardian.get('filhos', [])
        student_ids = [f['id'] for f in filhos if f.get('id')]

        invoices_by_student = InvoiceService.get_multiple_students_invoices(
            student_ids, token
        )

        # 4. Enriquecer cada filho com boletos
        filhos_enriched = []
        for filho in filhos:
            filho = {**filho}  # Copiar para não mutar
            sid = filho.get('id')
            invoices = invoices_by_student.get(sid, [])

            # Aplicar filtros de boletos
            if ano_letivo:
                invoices = [
                    inv for inv in invoices
                    if (inv.get('vencimento') or '').startswith(ano_letivo)
                ]

            if situacao_boleto and situacao_boleto != 'todos':
                invoices = [
                    inv for inv in invoices
                    if inv.get('situacao') == situacao_boleto
                ]

            filho['boletos'] = invoices
            filho['resumo_boletos'] = InvoiceService.calculate_student_summary(
                invoices
            )
            filhos_enriched.append(filho)

        guardian['filhos'] = filhos_enriched

        # 5. Resumo financeiro COMPLETO (com dados de boletos reais)
        guardian['resumo_financeiro'] = cls._build_resumo_financeiro_detalhe(
            filhos_enriched
        )
        guardian['resumo_documentos'] = cls._build_resumo_documentos(guardian)

        # 6. Cachear (só se sem filtros — resultado completo)
        if not ano_letivo and not situacao_boleto:
            SigaCacheManager._safe_cache_set(
                SigaCacheManager.KEY_GUARDIAN_DETAIL.format(
                    guardian_id=guardian_id, school_id=school_id
                ),
                guardian,
                SigaCacheManager.TTL_GUARDIAN_DETAIL,
            )

        logger.info(f"Guardian {guardian_id} detail built successfully")
        return guardian

    # =================================================================
    # STATS — GET /guardians/stats/
    # =================================================================

    @classmethod
    def get_stats(
        cls,
        school_id: int,
        token: str,
    ) -> Dict:
        """
        Calcula estatísticas globais da escola.

        Returns:
            Dict pronto para GuardianStatsSerializer
        """
        logger.info(f"Calculating stats for school {school_id}")

        guardians = cls.get_guardians_list(school_id, token)

        # Contadores
        total_responsaveis = len(guardians)
        total_alunos = sum(len(g.get('filhos', [])) for g in guardians)

        # Financeiro
        inadimplentes = [
            g for g in guardians
            if g.get('resumo_financeiro', {}).get('tem_pendencia', False)
        ]
        em_dia = total_responsaveis - len(inadimplentes)

        valor_pendente = sum(
            float(g.get('resumo_financeiro', {}).get('valor_pendente', 0))
            for g in inadimplentes
        )

        percentual_inadimplencia = (
            round(len(inadimplentes) / total_responsaveis * 100, 1)
            if total_responsaveis > 0 else 0
        )

        # Documentos
        completos = [
            g for g in guardians
            if g.get('resumo_documentos', {}).get('completo', False)
        ]
        incompletos = total_responsaveis - len(completos)

        percentual_completo = (
            round(len(completos) / total_responsaveis * 100, 1)
            if total_responsaveis > 0 else 0
        )

        # Distribuição de parentesco
        parentescos = Counter(
            g.get('parentesco', 'outro') for g in guardians
        )

        return {
            'total_responsaveis': total_responsaveis,
            'total_alunos': total_alunos,

            'financeiro': {
                'total_em_dia': em_dia,
                'total_inadimplentes': len(inadimplentes),
                'percentual_inadimplencia': percentual_inadimplencia,
                'valor_total_pendente': round(valor_pendente, 2),
                'valor_total_recebido': 0,  # Requer busca de boletos
            },

            'documentos': {
                'total_completos': len(completos),
                'total_incompletos': incompletos,
                'percentual_completo': percentual_completo,
            },

            'distribuicao_parentesco': {
                'mae': parentescos.get('mae', 0),
                'pai': parentescos.get('pai', 0),
                'responsavel_principal': parentescos.get(
                    'responsavel_principal', 0
                ),
                'responsavel_secundario': parentescos.get(
                    'responsavel_secundario', 0
                ),
            },

            'ultima_atualizacao': timezone.now().isoformat(),
        }

    # =================================================================
    # REFRESH — POST /guardians/refresh/
    # =================================================================

    @classmethod
    def invalidate_cache(cls, school_id: int) -> None:
        """
        Invalida todo o cache de uma escola.
        Próxima requisição buscará tudo do SIGA.
        """
        logger.info(f"Invalidating all cache for school {school_id}")

        keys_to_delete = [
            # Cache da lista processada
            cls.CACHE_KEY_LIST.format(school_id=school_id),
            # Caches individuais das 3 APIs SIGA
            SigaCacheManager.KEY_GUARDIANS_ALL.format(school_id=school_id),
            SigaCacheManager.KEY_STUDENTS_RELATIONS.format(
                school_id=school_id
            ),
            SigaCacheManager.KEY_STUDENTS_ACADEMIC.format(
                school_id=school_id
            ),
        ]

        for key in keys_to_delete:
            SigaCacheManager._safe_cache_delete(key)

        logger.info(
            f"Invalidated {len(keys_to_delete)} cache keys for school {school_id}"
        )

    # =================================================================
    # HELPERS: Resumos financeiros e documentos
    # =================================================================

    @classmethod
    def _build_resumo_financeiro_lista(cls, guardian: Dict) -> Dict:
        """
        Resumo financeiro para a LISTA (sem dados reais de boletos).

        Na lista, não temos boletos individuais. O resumo é inicialmente
        zerado e será preenchido progressivamente conforme os detalhes
        são acessados e cacheados.

        Se o detalhe já foi acessado antes, o cache do detalhe terá
        os dados reais. Mas na primeira carga, mostramos valores default.
        """
        # Tentar buscar do cache do detalhe (se existir)
        # Isso permite que guardians já visitados mostrem dados reais
        # mesmo na lista
        return {
            'tem_pendencia': False,
            'total_abertos': 0,
            'valor_pendente': 0,
            'proximo_vencimento': None,
        }

    @classmethod
    def _build_resumo_financeiro_detalhe(cls, filhos: List[Dict]) -> Dict:
        """
        Resumo financeiro para o DETALHE (com dados reais de boletos).
        """
        total_abertos = 0
        total_pagos = 0
        total_cancelados = 0
        valor_pendente = 0.0
        valor_pago = 0.0
        proximo_vencimento = None

        for filho in filhos:
            resumo = filho.get('resumo_boletos', {})
            total_abertos += resumo.get('abertos', 0)
            total_pagos += resumo.get('pagos', 0)
            total_cancelados += resumo.get('cancelados', 0)
            valor_pendente += float(resumo.get('valor_pendente', 0))
            valor_pago += float(resumo.get('valor_pago', 0))

            # Encontrar próximo vencimento
            for boleto in filho.get('boletos', []):
                if boleto.get('situacao') == 'ABE':
                    venc = boleto.get('vencimento')
                    if venc:
                        if proximo_vencimento is None or venc < proximo_vencimento:
                            proximo_vencimento = venc

        return {
            'tem_pendencia': total_abertos > 0,
            'total_abertos': total_abertos,
            'valor_pendente': round(valor_pendente, 2),
            'total_pagos': total_pagos,
            'valor_pago': round(valor_pago, 2),
            'total_cancelados': total_cancelados,
        }

    @classmethod
    def _build_resumo_documentos(cls, guardian: Dict) -> Dict:
        """
        Calcula resumo de documentos a partir da lista de docs.
        """
        docs = guardian.get('documentos', [])
        total = len(docs)
        entregues = sum(1 for d in docs if d.get('status') == 'entregue')
        pendentes = total - entregues

        return {
            'total': total,
            'entregues': entregues,
            'pendentes': pendentes,
            'completo': pendentes == 0 and total > 0,
        }