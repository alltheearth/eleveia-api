# apps/contacts/selectors/guardian_selectors.py

"""
Selectors para Guardians.

Responsabilidades:
- Filtros (search, CPF, status financeiro, docs)
- Ordenação
- Nenhuma lógica de negócio
- Nenhuma chamada HTTP

Trabalha com listas de dicts (dados do SIGA, não QuerySets).
"""

from typing import List, Dict


class GuardianSelector:
    """Filtros e ordenação para listas de guardians."""

    # -----------------------------------------------------------------
    # BUSCA TEXTUAL
    # -----------------------------------------------------------------

    @staticmethod
    def filter_by_search(guardians: List[Dict], query: str) -> List[Dict]:
        """
        Busca em nome, CPF, email, telefone e nome dos filhos.

        Case-insensitive. Remove formatação de CPF e telefone.
        """
        if not query:
            return guardians

        q = query.lower().strip()
        # Versão sem formatação para busca em CPF/telefone
        q_digits = ''.join(c for c in q if c.isdigit())

        filtered = []

        for g in guardians:
            # Nome do responsável
            if q in (g.get('nome') or '').lower():
                filtered.append(g)
                continue

            # CPF (sem formatação)
            cpf = (g.get('cpf') or '').replace('.', '').replace('-', '')
            if q_digits and q_digits in cpf:
                filtered.append(g)
                continue

            # Email
            if q in (g.get('email') or '').lower():
                filtered.append(g)
                continue

            # Telefone (sem formatação)
            tel = ''.join(c for c in (g.get('telefone') or '') if c.isdigit())
            if q_digits and q_digits in tel:
                filtered.append(g)
                continue

            # Nome dos filhos
            for filho in g.get('filhos', []):
                if q in (filho.get('nome') or '').lower():
                    filtered.append(g)
                    break

        return filtered

    # -----------------------------------------------------------------
    # FILTRO POR CPF EXATO
    # -----------------------------------------------------------------

    @staticmethod
    def filter_by_cpf(guardians: List[Dict], cpf: str) -> List[Dict]:
        """Filtra por CPF exato (ignora formatação)."""
        if not cpf:
            return guardians

        cpf_clean = cpf.replace('.', '').replace('-', '').strip()

        return [
            g for g in guardians
            if (g.get('cpf') or '').replace('.', '').replace('-', '') == cpf_clean
        ]

    # -----------------------------------------------------------------
    # FILTRO POR STATUS FINANCEIRO
    # -----------------------------------------------------------------

    @staticmethod
    def filter_by_status_financeiro(
        guardians: List[Dict],
        status: str,
    ) -> List[Dict]:
        """
        Filtra por situação financeira.

        Args:
            guardians: Lista de guardians
            status: 'em_dia' ou 'inadimplente'
        """
        if status == 'inadimplente':
            return [
                g for g in guardians
                if g.get('resumo_financeiro', {}).get('tem_pendencia', False)
            ]
        elif status == 'em_dia':
            return [
                g for g in guardians
                if not g.get('resumo_financeiro', {}).get('tem_pendencia', False)
            ]

        return guardians

    # -----------------------------------------------------------------
    # FILTRO POR DOCUMENTOS COMPLETOS
    # -----------------------------------------------------------------

    @staticmethod
    def filter_by_docs_completos(
        guardians: List[Dict],
        completo: bool,
    ) -> List[Dict]:
        """
        Filtra por completude de documentos.

        Args:
            guardians: Lista de guardians
            completo: True = só completos, False = só incompletos
        """
        return [
            g for g in guardians
            if g.get('resumo_documentos', {}).get('completo', False) == completo
        ]

    # -----------------------------------------------------------------
    # ORDENAÇÃO
    # -----------------------------------------------------------------

    @staticmethod
    def order_by(guardians: List[Dict], field: str) -> List[Dict]:
        """
        Ordena guardians por campo.

        Suporta:
        - 'nome' (A-Z)
        - '-nome' (Z-A)
        """
        if not field:
            field = 'nome'

        reverse = field.startswith('-')
        field_name = field.lstrip('-')

        if field_name == 'nome':
            return sorted(
                guardians,
                key=lambda g: (g.get('nome') or '').lower(),
                reverse=reverse,
            )

        # Fallback: retorna sem alterar
        return guardians