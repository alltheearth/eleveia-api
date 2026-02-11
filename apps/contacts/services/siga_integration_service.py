# apps/contacts/services/siga_integration_service.py
import requests
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class SigaIntegrationService:
    """
    Service para integração com sistema SIGA.
    REGRA: Isolado, testável, com tratamento de erros.
    """

    BASE_URL = getattr(settings, 'SIGA_API_URL', 'https://siga.activesoft.com.br/api/v0')
    TIMEOUT = 10  # segundos
    CACHE_TTL = 300  # 5 minutos

    def __init__(self, token: Optional[str] = None):
        """
        Inicializa o service com token de autenticação.

        Args:
            token: Token de autenticação (opcional, pode vir de settings)
        """
        self.token = token or getattr(settings, 'SIGA_API_TOKEN', None)

    def get_all_guardians_enriched(self) -> List[Dict[str, Any]]:
        """
        Busca todos os responsáveis com dados enriquecidos.

        Returns:
            Lista de responsáveis com informações completas

        Raises:
            SigaIntegrationError: Se erro na integração
        """
        try:
            # Buscar responsáveis
            guardians = self._fetch_all_paginated(
                f'{self.BASE_URL}/lista_responsaveis_dados_sensiveis/'
            )

            # Buscar alunos
            students = self._fetch_all_paginated(
                f'{self.BASE_URL}/lista_alunos_dados_sensiveis/'
            )

            # Enriquecer dados
            return self._enrich_guardians_with_students(guardians, students)

        except requests.RequestException as e:
            logger.error(f'Erro ao buscar responsáveis do SIGA: {str(e)}')
            raise SigaIntegrationError(f'Erro ao buscar responsáveis: {str(e)}')

    def buscar_alunos_por_responsavel(self, cpf_responsavel: str) -> List[Dict[str, Any]]:
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
                f'{self.BASE_URL}/responsaveis/{cpf_responsavel}/alunos',
                headers=self._get_headers(),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Salva no cache
            cache.set(cache_key, data, self.CACHE_TTL)

            return data

        except requests.RequestException as e:
            logger.error(f'Erro ao buscar alunos: {str(e)}')
            raise SigaIntegrationError(f'Erro ao buscar alunos: {str(e)}')

    def _fetch_all_paginated(self, url: str) -> List[Dict[str, Any]]:
        """
        Busca todos os resultados paginados de uma URL.

        Args:
            url: URL da API

        Returns:
            Lista com todos os resultados
        """
        headers = self._get_headers()
        all_results = []
        next_url = url

        while next_url:
            response = requests.get(next_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                all_results.extend(data)
                break
            elif isinstance(data, dict):
                all_results.extend(data.get('results', []))
                next_url = data.get('next')
            else:
                break

        return all_results

    def _enrich_guardians_with_students(
            self,
            guardians: List[Dict],
            students: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Enriquece dados dos responsáveis com informações dos alunos.

        Args:
            guardians: Lista de responsáveis
            students: Lista de alunos

        Returns:
            Lista de responsáveis enriquecidos
        """
        from collections import defaultdict

        # Mapear alunos por responsável
        guardian_students_map = defaultdict(list)

        for student in students:
            # Adicionar aluno aos responsáveis
            for key in ['mae_id', 'pai_id', 'responsavel_id', 'responsavel_secundario_id']:
                guardian_id = student.get(key)
                if guardian_id:
                    guardian_students_map[guardian_id].append({
                        'id': student.get('id'),
                        'nome': student.get('nome'),
                        'matricula': student.get('matricula'),
                        'turma': student.get('turma'),
                        'serie': student.get('serie'),
                        'periodo': student.get('periodo'),
                        'status': 'ativo' if student.get('ativo') else 'inativo'
                    })

        # Enriquecer responsáveis
        enriched = []
        for guardian in guardians:
            guardian_id = guardian.get('id')

            enriched_guardian = {
                'id': guardian_id,
                'nome': guardian.get('nome'),
                'cpf': guardian.get('cpf_cnpj'),
                'email': guardian.get('email'),
                'telefone': guardian.get('celular'),
                'telefone_secundario': guardian.get('fone'),
                'whatsapp': guardian.get('celular'),
                'endereco': {
                    'cep': guardian.get('cep'),
                    'logradouro': guardian.get('logradouro'),
                    'numero': guardian.get('numero_residencia'),
                    'complemento': guardian.get('complemento'),
                    'bairro': guardian.get('bairro'),
                    'cidade': guardian.get('cidade'),
                    'estado': guardian.get('uf'),
                },
                'parentesco': guardian.get('parentesco', 'responsavel'),
                'parentesco_display': guardian.get('parentesco_display', 'Responsável'),
                'responsavel_financeiro': guardian.get('responsavel_financeiro', False),
                'responsavel_pedagogico': guardian.get('responsavel_pedagogico', False),
                'filhos': guardian_students_map.get(guardian_id, []),
                'documentos': []  # Pode ser implementado depois
            }

            enriched.append(enriched_guardian)

        return enriched

    def _get_headers(self) -> Dict[str, str]:
        """Headers para autenticação na API SIGA."""
        if not self.token:
            raise SigaIntegrationError('Token de autenticação não configurado')

        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }


class SigaIntegrationError(Exception):
    """Exceção customizada para erros de integração."""
    pass