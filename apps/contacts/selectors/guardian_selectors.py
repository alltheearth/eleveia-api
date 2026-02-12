# apps/contacts/selectors/guardian_selectors.py

from typing import List, Dict


class GuardianSelector:
    """Filtros e queries para Guardians."""

    @staticmethod
    def filter_by_search(guardians: List[Dict], query: str) -> List[Dict]:
        """Filtra guardians por termo de busca."""
        if not query:
            return guardians

        query_lower = query.lower()
        filtered = []

        for guardian in guardians:
            # Busca no nome
            if query_lower in guardian.get('nome', '').lower():
                filtered.append(guardian)
                continue

            # Busca no CPF
            cpf = guardian.get('cpf', '').replace('.', '').replace('-', '')
            if query_lower in cpf.lower():
                filtered.append(guardian)
                continue

            # Busca no email
            if guardian.get('email') and query_lower in guardian.get('email', '').lower():
                filtered.append(guardian)
                continue

            # Busca nos filhos
            for filho in guardian.get('filhos', []):
                if query_lower in filho.get('nome', '').lower():
                    filtered.append(guardian)
                    break

        return filtered

    @staticmethod
    def filter_by_cpf(guardians: List[Dict], cpf: str) -> List[Dict]:
        """Filtra por CPF exato."""
        if not cpf:
            return guardians

        cpf_clean = cpf.replace('.', '').replace('-', '').strip()
        return [
            g for g in guardians
            if g.get('cpf', '').replace('.', '').replace('-', '') == cpf_clean
        ]

    @staticmethod
    def order_by(guardians: List[Dict], field: str) -> List[Dict]:
        """Ordena guardians por campo."""
        reverse = field.startswith('-')
        field_name = field.lstrip('-')

        if field_name == 'nome':
            return sorted(guardians, key=lambda g: g.get('nome', '').lower(), reverse=reverse)

        return guardians