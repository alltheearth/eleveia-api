# apps/contacts/selectors/guardian_selectors.py

"""
Selectors para filtros e ordenação de Guardians.

Responsabilidades:
- Filtros em memória
- Buscas (search)
- Ordenação
- Agregações simples

Não faz:
- Modificação de dados
- Lógica de negócio
- Chamadas externas
"""

from typing import List, Dict


class GuardianSelector:
    """Filtros e queries para Guardians."""

    @staticmethod
    def filter_by_search(guardians: List[Dict], query: str) -> List[Dict]:
        """
        Filtra guardians por termo de busca.

        Busca em:
        - Nome do guardian
        - CPF do guardian
        - Email do guardian
        - Nome dos filhos

        Args:
            guardians: Lista de guardians
            query: Termo de busca

        Returns:
            Lista filtrada
        """
        if not query:
            return guardians

        query_lower = query.lower()

        filtered = []
        for guardian in guardians:
            # Busca no nome do guardian
            if query_lower in guardian.get('nome', '').lower():
                filtered.append(guardian)
                continue

            # Busca no CPF (remove formatação)
            cpf = guardian.get('cpf', '').replace('.', '').replace('-', '')
            if query_lower in cpf.lower():
                filtered.append(guardian)
                continue

            # Busca no email
            email = guardian.get('email', '')
            if email and query_lower in email.lower():
                filtered.append(guardian)
                continue

            # Busca no nome dos filhos
            filhos = guardian.get('filhos', [])
            for filho in filhos:
                if query_lower in filho.get('nome', '').lower():
                    filtered.append(guardian)
                    break

        return filtered

    @staticmethod
    def filter_by_cpf(guardians: List[Dict], cpf: str) -> List[Dict]:
        """
        Filtra por CPF exato.

        Args:
            guardians: Lista de guardians
            cpf: CPF a filtrar (com ou sem formatação)

        Returns:
            Lista filtrada (0 ou 1 item)
        """
        if not cpf:
            return guardians

        # Remove formatação
        cpf_clean = cpf.replace('.', '').replace('-', '').strip()

        return [
            g for g in guardians
            if g.get('cpf', '').replace('.', '').replace('-', '') == cpf_clean
        ]

    @staticmethod
    def order_by(guardians: List[Dict], field: str) -> List[Dict]:
        """
        Ordena guardians por campo.

        Args:
            guardians: Lista de guardians
            field: Campo para ordenar ('nome', '-nome')

        Returns:
            Lista ordenada
        """
        reverse = field.startswith('-')
        field_name = field.lstrip('-')

        if field_name == 'nome':
            return sorted(
                guardians,
                key=lambda g: g.get('nome', '').lower(),
                reverse=reverse
            )

        # Default: sem ordenação
        return guardians
