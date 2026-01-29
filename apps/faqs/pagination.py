# ===================================================================
# apps/faqs/pagination.py - PAGINAÇÃO CUSTOMIZADA PARA FAQs
# ===================================================================
from rest_framework.pagination import PageNumberPagination


class FAQPagination(PageNumberPagination):
    """
    Paginação customizada para FAQs.

    Permite ao usuário escolher entre 15, 20 ou 25 itens por página.

    Uso:
    - GET /api/v1/faqs/?page=1&page_size=20

    Padrões:
    - page_size padrão: 20
    - Opções disponíveis: 15, 20, 25
    - Máximo permitido: 25
    """

    # Tamanho padrão da página
    page_size = 20

    # Nome do query parameter para o usuário customizar
    page_size_query_param = 'page_size'

    # Máximo permitido (segurança)
    max_page_size = 25

    # Opcional: Validar valores permitidos
    def get_page_size(self, request):
        """
        Valida e retorna o page_size.

        Se o usuário passar um valor não permitido (ex: 30, 100),
        usa o padrão (20).
        """
        page_size = super().get_page_size(request)

        # Lista de valores permitidos
        allowed_sizes = [15, 20, 25]

        # Se o valor não está na lista, usa o padrão
        if page_size not in allowed_sizes:
            return self.page_size

        return page_size