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