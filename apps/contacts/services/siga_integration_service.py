import logging
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class SigaIntegrationService:
    """
    Service para integração com a API do SIGA Activesoft.

    Responsável por:
    - Autenticação na API externa
    - Busca paginada de dados
    - Cache de resultados
    - Transformação e enriquecimento de dados
    """

    BASE_URL = "https://siga.activesoft.com.br/api/v0"
    CACHE_TIMEOUT = 300  # 5 minutos

    # Mapeamento de parentesco baseado nos IDs de relacionamento
    PARENTESCO_MAP = {
        'mae': {'key': 'mae', 'display': 'Mãe'},
        'pai': {'key': 'pai', 'display': 'Pai'},
        'responsavel': {'key': 'responsavel', 'display': 'Responsável Legal'},
        'responsavel_secundario': {'key': 'responsavel_secundario', 'display': 'Responsável Secundário'},
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_auth_token(self) -> Optional[str]:
        """
        Obtém token de autenticação da API SIGA.

        Returns:
            str: Token de autenticação ou None em caso de erro
        """
        cache_key = 'siga_auth_token'
        token = cache.get(cache_key)

        if token:
            return token

        try:
            response = self.session.post(
                f"{self.BASE_URL}/auth/login/",
                json={
                    'username': settings.SIGA_USERNAME,
                    'password': settings.SIGA_PASSWORD
                },
                timeout=10
            )
            response.raise_for_status()

            token = response.json().get('token')
            cache.set(cache_key, token, timeout=3600)  # Cache por 1 hora

            return token

        except requests.RequestException as e:
            logger.error(f"Erro ao obter token SIGA: {e}")
            return None

    def _fetch_all_paginated(
            self,
            url: str,
            token: str,
            cache_key: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca todos os registros de um endpoint paginado.

        Args:
            url: URL do endpoint
            token: Token de autenticação
            cache_key: Chave para cache (opcional)

        Returns:
            List[Dict]: Lista com todos os registros
        """
        if cache_key:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Dados obtidos do cache: {cache_key}")
                return cached_data

        all_data = []
        headers = {'Authorization': f'Bearer {token}'}

        try:
            while url:
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                results = data.get('results', []) if isinstance(data, dict) else data
                all_data.extend(results)

                # Próxima página
                url = data.get('next') if isinstance(data, dict) else None

            if cache_key:
                cache.set(cache_key, all_data, timeout=self.CACHE_TIMEOUT)

            return all_data

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar dados paginados de {url}: {e}")
            return []

    def fetch_guardians(self) -> List[Dict]:
        """Busca todos os responsáveis da API SIGA."""
        token = self.get_auth_token()
        if not token:
            return []

        return self._fetch_all_paginated(
            f"{self.BASE_URL}/lista_responsaveis_dados_sensiveis/",
            token,
            cache_key='siga_guardians_all'
        )

    def fetch_students(self) -> List[Dict]:
        """Busca todos os alunos da API SIGA."""
        token = self.get_auth_token()
        if not token:
            return []

        return self._fetch_all_paginated(
            f"{self.BASE_URL}/lista_alunos_dados_sensiveis/",
            token,
            cache_key='siga_students_all'
        )

    def _determine_parentesco(
            self,
            guardian_id: int,
            student: Dict
    ) -> Tuple[str, str]:
        """
        Determina o tipo de parentesco entre responsável e aluno.

        Args:
            guardian_id: ID do responsável
            student: Dados do aluno

        Returns:
            Tuple[str, str]: (chave_parentesco, display_parentesco)
        """
        if student.get('mae') == guardian_id:
            return 'mae', 'Mãe'
        elif student.get('pai') == guardian_id:
            return 'pai', 'Pai'
        elif student.get('responsavel_id') == guardian_id:
            return 'responsavel', 'Responsável Legal'
        elif student.get('responsavel_secundario_id') == guardian_id:
            return 'responsavel_secundario', 'Responsável Secundário'
        else:
            return 'outro', 'Outro'

    def _build_student_summary(self, student: Dict) -> Dict:
        """
        Constrói resumo dos dados do aluno para o serializer.

        Args:
            student: Dados brutos do aluno da API

        Returns:
            Dict: Dados formatados do aluno
        """
        return {
            'id': student['id'],
            'nome': student['nome'],
            'turma': student.get('turma_nome'),  # Você precisará adicionar esse campo
            'serie': student.get('serie_nome'),  # Você precisará adicionar esse campo
            'periodo': student.get('periodo'),  # Você precisará adicionar esse campo
            'status': 'ativo',  # Lógica de status pode ser refinada
        }

    def _build_address_data(self, guardian: Dict) -> Dict:
        """
        Extrai e formata dados de endereço do responsável.

        Args:
            guardian: Dados brutos do responsável

        Returns:
            Dict: Dados de endereço formatados
        """
        return {
            'cep': guardian.get('cep'),
            'logradouro': guardian.get('logradouro'),
            'numero_residencia': None,  # Não existe no retorno atual, extrair do logradouro?
            'complemento': guardian.get('complemento'),
            'bairro': guardian.get('bairro'),
            'cidade': guardian.get('cidade'),
            'uf': guardian.get('uf'),
        }

    def _get_guardian_documents(self, guardian_id: int) -> List[Dict]:
        """
        Busca documentos do responsável.

        NOTA: Endpoint de documentos não foi fornecido nos exemplos.
        Você precisará implementar quando tiver acesso ao endpoint correto.

        Args:
            guardian_id: ID do responsável

        Returns:
            List[Dict]: Lista de documentos
        """
        # TODO: Implementar quando endpoint estiver disponível
        # Exemplo fictício:
        return [
            {
                'id': 1,
                'tipo': 'RG',
                'nome': 'RG do Responsável',
                'status': 'aprovado',
                'data_entrega': '2026-01-15',
            },
            {
                'id': 2,
                'tipo': 'CPF',
                'nome': 'CPF do Responsável',
                'status': 'aprovado',
                'data_entrega': '2026-01-15',
            },
        ]

    def enrich_guardian_with_students(
            self,
            guardian: Dict,
            all_students: List[Dict]
    ) -> Dict:
        """
        Enriquece dados do responsável com lista de filhos.

        Args:
            guardian: Dados do responsável
            all_students: Lista completa de alunos

        Returns:
            Dict: Dados enriquecidos do responsável
        """
        guardian_id = guardian['id']

        # Encontrar todos os filhos deste responsável
        children = []
        for student in all_students:
            # Verificar se este responsável está vinculado ao aluno
            if guardian_id in [
                student.get('mae'),
                student.get('pai'),
                student.get('responsavel_id'),
                student.get('responsavel_secundario_id')
            ]:
                children.append(self._build_student_summary(student))

        # Determinar parentesco baseado no primeiro filho
        # (pode ser refinado se necessário)
        parentesco, parentesco_display = ('outro', 'Outro')
        if children and all_students:
            first_child = next(
                (s for s in all_students if s['id'] == children[0]['id']),
                None
            )
            if first_child:
                parentesco, parentesco_display = self._determine_parentesco(
                    guardian_id,
                    first_child
                )

        # Determinar responsabilidades
        # Lógica pode ser refinada baseada em regras de negócio
        is_primary = any(
            guardian_id == s.get('responsavel_id')
            for s in all_students
            if s['id'] in [c['id'] for c in children]
        )

        return {
            'id': guardian['id'],
            'nome': guardian['nome'],
            'cpf': guardian.get('cpf'),
            'email': guardian.get('email'),
            'celular': guardian.get('celular'),
            'fone': guardian.get('fone'),
            'endereco': self._build_address_data(guardian),
            'parentesco': parentesco,
            'parentesco_display': parentesco_display,
            'responsavel_financeiro': is_primary,
            'responsavel_pedagogico': is_primary,
            'filhos': children,
            'documentos': self._get_guardian_documents(guardian_id),
        }

    def get_all_guardians_enriched(self) -> List[Dict]:
        """
        Retorna todos os responsáveis com dados enriquecidos.

        Returns:
            List[Dict]: Lista de responsáveis com filhos e documentos
        """
        guardians = self.fetch_guardians()
        students = self.fetch_students()

        # Filtrar apenas responsáveis que têm filhos
        enriched_guardians = []
        for guardian in guardians:
            enriched = self.enrich_guardian_with_students(guardian, students)

            # Incluir apenas se tiver filhos
            if enriched['filhos']:
                enriched_guardians.append(enriched)

        return enriched_guardians