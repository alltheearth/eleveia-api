# apps/contacts/selectors/contact_selector.py
from django.db.models import QuerySet
from ..models import Contato


class ContatoSelector:
    """
    Responsável por LEITURA de dados de Contatos.
    Queries otimizadas com select_related e prefetch_related.
    """

    @staticmethod
    def get_all_ativos() -> QuerySet[Contato]:
        """Retorna todos os contatos ativos."""
        return Contato.objects.filter(ativo=True).order_by('-created_at')

    @staticmethod
    def get_by_email(email: str) -> Contato | None:
        """Busca contato por email."""
        try:
            return Contato.objects.get(email=email)
        except Contato.DoesNotExist:
            return None

    @staticmethod
    def get_by_id(contato_id: int) -> Contato | None:
        """Busca contato por ID."""
        try:
            return Contato.objects.get(id=contato_id)
        except Contato.DoesNotExist:
            return None