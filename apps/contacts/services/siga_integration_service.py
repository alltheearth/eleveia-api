# apps/contacts/services/siga_integration_service.py
import requests
from typing import Dict, Any, List
from django.conf import settings
from django.core.cache import cache


class SigaIntegrationService:
    """
    Service para integração com sistema SIGA.
    REGRA: Isolado, testável, com tratamento de erros.
    """

    BASE_URL = settings.SIGA_API_URL
    TIMEOUT = 10  # segundos
    CACHE_TTL = 300  # 5 minutos

    @classmethod
    def buscar_alunos_por_responsavel(cls, cpf_responsavel: str) -> List[Dict[str, Any]]:
        """
        Busca alunos no SIGA pelo CPF do responsável.

        Args:
            cpf_responsavel: CPF do responsável

        Returns:
            Lista de alunos

        Raises:
            SigaIntegrationError: Se erro na integração
        """
        # Verifica cache
        cache_key = f'siga_alunos_{cpf_responsavel}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            response = requests.get(
                f'{cls.BASE_URL}/responsaveis/{cpf_responsavel}/alunos',
                headers=cls._get_headers(),
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Salva no cache
            cache.set(cache_key, data, cls.CACHE_TTL)

            return data

        except requests.RequestException as e:
            raise SigaIntegrationError(f'Erro ao buscar alunos: {str(e)}')

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Headers para autenticação na API SIGA."""
        return {
            'Authorization': f'Bearer {settings.SIGA_API_TOKEN}',
            'Content-Type': 'application/json'
        }


class SigaIntegrationError(Exception):
    """Exceção customizada para erros de integração."""
    pass