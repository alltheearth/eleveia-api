# apps/contacts/integrations/siga_cache_manager.py
"""
Gerenciador centralizado de cache para integração SIGA - VERSÃO RESILIENTE

Esta versão funciona COM ou SEM Redis disponível:
- Se Redis está disponível: usa cache normalmente
- Se Redis está offline: funciona sem cache (direto do SIGA)

IMPORTANTE: Sempre busca dados do SIGA quando cache falha.
"""

import logging
from typing import List, Dict, Optional
from django.core.cache import cache
from ..services.siga_integration_service import SigaIntegrationService

logger = logging.getLogger(__name__)


class SigaCacheManager:
    """
    Gerenciador centralizado de cache para dados do SIGA.

    RESILIENTE: Funciona mesmo se Redis estiver offline!
    """

    # TTL (Time To Live) em segundos
    TTL_GUARDIANS_GLOBAL = 3600  # 1 hora
    TTL_STUDENTS_GLOBAL = 3600  # 1 hora
    TTL_GUARDIAN_DETAIL = 21600  # 6 horas
    TTL_INVOICES = 1800  # 30 minutos
    TTL_SEARCH = 900  # 15 minutos

    # Padrões de chaves
    KEY_GUARDIANS_ALL = "guardians:school:{school_id}:all"
    KEY_STUDENTS_RELATIONS = "students:school:{school_id}:relations"
    KEY_STUDENTS_ACADEMIC = "students:school:{school_id}:academic"
    KEY_GUARDIAN_DETAIL = "guardian:detail:{guardian_id}:school:{school_id}"
    KEY_STUDENT_INVOICES = "student:invoices:{student_id}"
    KEY_SEARCH = "guardians:search:{query}:school:{school_id}"

    @classmethod
    def _safe_cache_get(cls, cache_key: str) -> Optional[any]:
        """
        Busca do cache com tratamento de erro.

        Se Redis estiver offline, retorna None silenciosamente.

        Args:
            cache_key: Chave do cache

        Returns:
            Valor do cache ou None
        """
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache GET failed for {cache_key}: {e}")
            return None

    @classmethod
    def _safe_cache_set(cls, cache_key: str, value: any, timeout: int) -> None:
        """
        Salva no cache com tratamento de erro.

        Se Redis estiver offline, apenas loga warning.

        Args:
            cache_key: Chave do cache
            value: Valor a cachear
            timeout: TTL em segundos
        """
        try:
            cache.set(cache_key, value, timeout=timeout)
            logger.debug(f"Cache SET: {cache_key} (TTL: {timeout}s)")
        except Exception as e:
            logger.warning(f"Cache SET failed for {cache_key}: {e}")

    @classmethod
    def _safe_cache_delete(cls, cache_key: str) -> None:
        """
        Remove do cache com tratamento de erro.

        Args:
            cache_key: Chave do cache
        """
        try:
            cache.delete(cache_key)
            logger.debug(f"Cache DELETE: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache DELETE failed for {cache_key}: {e}")

    @classmethod
    def get_or_fetch_guardians(
            cls,
            school_id: int,
            token: str
    ) -> List[Dict]:
        """
        Busca guardians com cache (1h TTL).

        RESILIENTE: Se cache falhar, busca direto do SIGA.

        Args:
            school_id: ID da escola
            token: Token de autenticação SIGA

        Returns:
            Lista de guardians
        """
        cache_key = cls.KEY_GUARDIANS_ALL.format(school_id=school_id)

        # Tenta cache (com proteção)
        cached = cls._safe_cache_get(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return cached

        # Cache miss ou erro - busca SIGA
        logger.info(f"Cache MISS: {cache_key} - Fetching from SIGA")
        siga_service = SigaIntegrationService(token)
        data = siga_service.fetch_all_guardians()

        # Tenta armazenar no cache (com proteção)
        cls._safe_cache_set(cache_key, data, timeout=cls.TTL_GUARDIANS_GLOBAL)
        logger.info(f"Fetched {len(data)} guardians from SIGA")

        return data

    @classmethod
    def get_or_fetch_students_relations(
            cls,
            school_id: int,
            token: str
    ) -> List[Dict]:
        """
        Busca students com vínculos familiares (mae_id, pai_id) com cache (1h TTL).

        Args:
            school_id: ID da escola
            token: Token de autenticação SIGA

        Returns:
            Lista de students com vínculos
        """
        cache_key = cls.KEY_STUDENTS_RELATIONS.format(school_id=school_id)

        cached = cls._safe_cache_get(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return cached

        logger.info(f"Cache MISS: {cache_key} - Fetching from SIGA")
        siga_service = SigaIntegrationService(token)
        data = siga_service.fetch_students_relations()

        cls._safe_cache_set(cache_key, data, timeout=cls.TTL_STUDENTS_GLOBAL)
        logger.info(f"Fetched {len(data)} students (relations) from SIGA")

        return data

    @classmethod
    def get_or_fetch_students_academic(
            cls,
            school_id: int,
            token: str
    ) -> List[Dict]:
        """
        Busca students com dados acadêmicos (turma, série) com cache (1h TTL).

        Args:
            school_id: ID da escola
            token: Token de autenticação SIGA

        Returns:
            Lista de students com dados acadêmicos
        """
        cache_key = cls.KEY_STUDENTS_ACADEMIC.format(school_id=school_id)

        cached = cls._safe_cache_get(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return cached

        logger.info(f"Cache MISS: {cache_key} - Fetching from SIGA")
        siga_service = SigaIntegrationService(token)
        data = siga_service.fetch_students_academic()

        cls._safe_cache_set(cache_key, data, timeout=cls.TTL_STUDENTS_GLOBAL)
        logger.info(f"Fetched {len(data)} students (academic) from SIGA")

        return data

    @classmethod
    def get_or_fetch_all_siga_data(
            cls,
            school_id: int,
            token: str
    ) -> Dict[str, List[Dict]]:
        """
        Busca todos os dados necessários das 3 APIs com cache individual.

        Vantagem: Cada API tem seu próprio cache, reduzindo chamadas.

        Args:
            school_id: ID da escola
            token: Token de autenticação SIGA

        Returns:
            Dict com 'guardians', 'students_relations', 'students_academic'
        """
        return {
            'guardians': cls.get_or_fetch_guardians(school_id, token),
            'students_relations': cls.get_or_fetch_students_relations(school_id, token),
            'students_academic': cls.get_or_fetch_students_academic(school_id, token),
        }

    @classmethod
    def get_or_fetch_guardian_detail(
            cls,
            guardian_id: int,
            school_id: int,
            guardian_data: Dict
    ) -> Dict:
        """
        Cacheia guardian detalhado (6h TTL).

        Args:
            guardian_id: ID do guardian
            school_id: ID da escola
            guardian_data: Dados completos do guardian

        Returns:
            Guardian data (do cache ou fornecido)
        """
        cache_key = cls.KEY_GUARDIAN_DETAIL.format(
            guardian_id=guardian_id,
            school_id=school_id
        )

        cached = cls._safe_cache_get(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return cached

        logger.debug(f"Caching guardian detail: {cache_key}")
        cls._safe_cache_set(cache_key, guardian_data, timeout=cls.TTL_GUARDIAN_DETAIL)

        return guardian_data

    @classmethod
    def get_or_set_student_invoices(
            cls,
            student_id: int,
            invoices_data: Optional[List[Dict]] = None
    ) -> Optional[List[Dict]]:
        """
        Cacheia boletos de um aluno (30min TTL).

        Args:
            student_id: ID do aluno
            invoices_data: Dados dos boletos (para SET) ou None (para GET)

        Returns:
            Boletos do cache ou None
        """
        cache_key = cls.KEY_STUDENT_INVOICES.format(student_id=student_id)

        # GET
        if invoices_data is None:
            cached = cls._safe_cache_get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: {cache_key}")
            return cached

        # SET
        logger.debug(f"Caching {len(invoices_data)} invoices for student {student_id}")
        cls._safe_cache_set(cache_key, invoices_data, timeout=cls.TTL_INVOICES)
        return invoices_data

    @classmethod
    def cache_search_results(
            cls,
            school_id: int,
            query: str,
            results: List[Dict]
    ) -> None:
        """
        Cacheia resultados de busca (15min TTL).

        Args:
            school_id: ID da escola
            query: Termo de busca
            results: Resultados da busca
        """
        query_normalized = query.lower().strip()

        cache_key = cls.KEY_SEARCH.format(
            query=query_normalized,
            school_id=school_id
        )

        logger.debug(f"Caching search results: {cache_key} ({len(results)} items)")
        cls._safe_cache_set(cache_key, results, timeout=cls.TTL_SEARCH)

    @classmethod
    def get_cached_search_results(
            cls,
            school_id: int,
            query: str
    ) -> Optional[List[Dict]]:
        """
        Busca resultados de busca no cache.

        Args:
            school_id: ID da escola
            query: Termo de busca

        Returns:
            Resultados em cache ou None
        """
        query_normalized = query.lower().strip()

        cache_key = cls.KEY_SEARCH.format(
            query=query_normalized,
            school_id=school_id
        )

        cached = cls._safe_cache_get(cache_key)
        if cached:
            logger.debug(f"Cache HIT: {cache_key}")
        return cached

    @classmethod
    def invalidate_school_cache(cls, school_id: int) -> None:
        """
        Invalida todo o cache de uma escola.

        Args:
            school_id: ID da escola
        """
        keys_to_delete = [
            cls.KEY_GUARDIANS_ALL.format(school_id=school_id),
            cls.KEY_STUDENTS_RELATIONS.format(school_id=school_id),
            cls.KEY_STUDENTS_ACADEMIC.format(school_id=school_id),
        ]

        for key in keys_to_delete:
            cls._safe_cache_delete(key)
            logger.info(f"Cache invalidated: {key}")

    @classmethod
    def invalidate_guardian_cache(cls, guardian_id: int, school_id: int) -> None:
        """
        Invalida cache de um guardian específico.

        Args:
            guardian_id: ID do guardian
            school_id: ID da escola
        """
        cache_key = cls.KEY_GUARDIAN_DETAIL.format(
            guardian_id=guardian_id,
            school_id=school_id
        )

        cls._safe_cache_delete(cache_key)
        logger.info(f"Guardian cache invalidated: {cache_key}")