# apps/contacts/services/siga_integration_service.py

import requests
import logging
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# ⭐ EXCEÇÃO CUSTOMIZADA
class SigaIntegrationError(Exception):
    """
    Exceção customizada para erros de integração com SIGA.
    """
    pass


class SigaIntegrationService:
    """
    Serviço de integração com APIs do SIGA.
    Responsável por buscar dados brutos das 3 APIs necessárias.
    """

    BASE_URL = "https://siga.activesoft.com.br/api/v0"
    TIMEOUT = 30  # segundos

    def __init__(self, token: str):
        """
        Args:
            token: Application token da escola
        """
        self.token = token
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Cria session com retry automático para resiliência.
        """
        session = requests.Session()

        # Retry: 3 tentativas, backoff exponencial
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """
        Retorna headers padrão para requisições.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def fetch_all_guardians(self) -> List[Dict]:
        """
        Busca todos os responsáveis.

        Returns:
            Lista de dicionários com dados dos responsáveis

        Raises:
            requests.exceptions.RequestException: Em caso de erro na API
        """
        url = f"{self.BASE_URL}/lista_responsaveis_dados_sensiveis/"

        try:
            logger.info(f"Fetching guardians from {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched {len(data)} guardians")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching guardians from {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching guardians: {str(e)}")
            raise

    def fetch_students_relations(self) -> List[Dict]:
        """
        Busca alunos com vínculos familiares (mae_id, pai_id, etc).

        Returns:
            Lista de dicionários com dados dos alunos e vínculos

        Raises:
            requests.exceptions.RequestException: Em caso de erro na API
        """
        url = f"{self.BASE_URL}/lista_alunos_dados_sensiveis/"

        try:
            logger.info(f"Fetching students relations from {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched {len(data)} students (relations)")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching students relations from {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching students relations: {str(e)}")
            raise

    def fetch_students_academic(self) -> List[Dict]:
        """
        Busca dados acadêmicos dos alunos (turma, série, status).

        Returns:
            Lista de dicionários com dados acadêmicos

        Raises:
            requests.exceptions.RequestException: Em caso de erro na API
        """
        url = f"{self.BASE_URL}/acesso/alunos/"

        try:
            logger.info(f"Fetching students academic data from {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched {len(data)} students (academic)")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching students academic from {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching students academic: {str(e)}")
            raise

    def fetch_all_data(self) -> Dict[str, List[Dict]]:
        """
        Busca todos os dados necessários das 3 APIs.

        Returns:
            Dict com chaves: guardians, students_relations, students_academic

        Raises:
            requests.exceptions.RequestException: Em caso de erro em qualquer API
        """
        try:
            guardians = self.fetch_all_guardians()
            students_relations = self.fetch_students_relations()
            students_academic = self.fetch_students_academic()

            return {
                'guardians': guardians,
                'students_relations': students_relations,
                'students_academic': students_academic
            }

        except requests.exceptions.RequestException:
            raise