# apps/contacts/utils/guardian_filters.py

from typing import List, Dict, Any


class GuardianFilterService:
    """
    Service para aplicar filtros em responsáveis.

    Como os dados vêm de API externa (não QuerySet Django),
    aplicamos filtros manualmente em listas Python.

    Filtros disponíveis:
    - search: Nome do responsável OU nome dos filhos
    - email: Email exato do responsável
    - cpf: CPF do responsável (com ou sem formatação)
    - telefone: Telefone do responsável (com ou sem formatação)
    - tem_boleto_aberto: True/False
    - tem_doc_faltando: True/False
    """

    @staticmethod
    def apply_filters(
            guardians: List[Dict[str, Any]],
            filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Aplica múltiplos filtros em lista de responsáveis.

        Args:
            guardians: Lista de responsáveis
            filters: Dict com filtros {campo: valor}

        Returns:
            Lista filtrada
        """
        filtered = guardians

        # Aplicar cada filtro sequencialmente
        if filters.get('search'):
            filtered = GuardianFilterService._filter_search(
                filtered,
                filters['search']
            )

        if filters.get('email'):
            filtered = GuardianFilterService._filter_email(
                filtered,
                filters['email']
            )

        if filters.get('cpf'):
            filtered = GuardianFilterService._filter_cpf(
                filtered,
                filters['cpf']
            )

        if filters.get('telefone'):
            filtered = GuardianFilterService._filter_telefone(
                filtered,
                filters['telefone']
            )

        if filters.get('tem_boleto_aberto') is not None:
            filtered = GuardianFilterService._filter_boleto_aberto(
                filtered,
                filters['tem_boleto_aberto']
            )

        if filters.get('tem_doc_faltando') is not None:
            filtered = GuardianFilterService._filter_doc_faltando(
                filtered,
                filters['tem_doc_faltando']
            )

        return filtered

    @staticmethod
    def _filter_search(
            guardians: List[Dict[str, Any]],
            search_term: str
    ) -> List[Dict[str, Any]]:
        """
        Busca por nome do responsável OU nome dos filhos.

        Args:
            guardians: Lista de responsáveis
            search_term: Termo de busca

        Returns:
            Lista filtrada
        """
        search_lower = search_term.lower().strip()

        if not search_lower:
            return guardians

        filtered = []

        for guardian in guardians:
            # Buscar no nome do responsável
            if search_lower in guardian.get('nome', '').lower():
                filtered.append(guardian)
                continue

            # Buscar no CPF (sem formatação)
            cpf_clean = guardian.get('cpf', '').replace('.', '').replace('-', '')
            if search_lower in cpf_clean.lower():
                filtered.append(guardian)
                continue

            # Buscar no email
            if search_lower in guardian.get('email', '').lower():
                filtered.append(guardian)
                continue

            # Buscar no telefone (sem formatação)
            telefone_clean = guardian.get('telefone', '').replace('(', '').replace(')', '').replace('-', '').replace(
                ' ', '')
            if search_lower in telefone_clean:
                filtered.append(guardian)
                continue

            # Buscar no nome dos filhos
            for child in guardian.get('filhos', []):
                if search_lower in child.get('nome', '').lower():
                    filtered.append(guardian)
                    break

        return filtered

    @staticmethod
    def _filter_email(
            guardians: List[Dict[str, Any]],
            email: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra por email exato (case-insensitive).

        Args:
            guardians: Lista de responsáveis
            email: Email para buscar

        Returns:
            Lista filtrada
        """
        email_lower = email.lower().strip()

        return [
            g for g in guardians
            if g.get('email', '').lower() == email_lower
        ]

    @staticmethod
    def _filter_cpf(
            guardians: List[Dict[str, Any]],
            cpf: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra por CPF (remove formatação antes de comparar).

        Args:
            guardians: Lista de responsáveis
            cpf: CPF para buscar (com ou sem formatação)

        Returns:
            Lista filtrada
        """
        # Remover formatação do CPF buscado
        cpf_clean = cpf.replace('.', '').replace('-', '').strip()

        filtered = []

        for guardian in guardians:
            # Remover formatação do CPF do responsável
            guardian_cpf = guardian.get('cpf', '')
            guardian_cpf_clean = guardian_cpf.replace('.', '').replace('-', '')

            if cpf_clean == guardian_cpf_clean:
                filtered.append(guardian)

        return filtered

    @staticmethod
    def _filter_telefone(
            guardians: List[Dict[str, Any]],
            telefone: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra por telefone (remove formatação antes de comparar).

        Args:
            guardians: Lista de responsáveis
            telefone: Telefone para buscar (com ou sem formatação)

        Returns:
            Lista filtrada
        """
        # Remover formatação do telefone buscado
        telefone_clean = (
            telefone
            .replace('(', '')
            .replace(')', '')
            .replace('-', '')
            .replace(' ', '')
            .strip()
        )

        filtered = []

        for guardian in guardians:
            # Remover formatação do telefone do responsável
            guardian_tel = guardian.get('telefone', '')
            guardian_tel_clean = (
                guardian_tel
                .replace('(', '')
                .replace(')', '')
                .replace('-', '')
                .replace(' ', '')
            )

            if telefone_clean in guardian_tel_clean:
                filtered.append(guardian)

        return filtered

    @staticmethod
    def _filter_boleto_aberto(
            guardians: List[Dict[str, Any]],
            tem_boleto: bool
    ) -> List[Dict[str, Any]]:
        """
        Filtra por situação de boletos abertos.

        Args:
            guardians: Lista de responsáveis
            tem_boleto: True = com boletos abertos, False = sem

        Returns:
            Lista filtrada
        """
        return [
            g for g in guardians
            if g.get('situacao', {}).get('tem_boleto_aberto') == tem_boleto
        ]

    @staticmethod
    def _filter_doc_faltando(
            guardians: List[Dict[str, Any]],
            tem_doc: bool
    ) -> List[Dict[str, Any]]:
        """
        Filtra por situação de documentos faltantes.

        Args:
            guardians: Lista de responsáveis
            tem_doc: True = com docs faltando, False = sem

        Returns:
            Lista filtrada
        """
        return [
            g for g in guardians
            if g.get('situacao', {}).get('tem_doc_faltando') == tem_doc
        ]