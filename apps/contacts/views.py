from .services import ContatoService
from rest_framework import viewsets
# apps/contacts/views.py
from core.pagination import LargePagination

class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    queryset = Contato.objects.select_related('escola', 'usuario')
    pagination_class = LargePagination  # Para este ViewSet específico

    # Agora faz JOIN e traz tudo em 1 query!

    def get_queryset(self):
        """Otimizar queries"""
        queryset = super().get_queryset()

        # select_related para ForeignKeys (1-to-1, Many-to-1)
        queryset = queryset.select_related('escola', 'usuario')

        return queryset


class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):

    @action(detail=True, methods=['post'])
    def registrar_interacao(self, request, pk=None):
        """Registrar última interação"""
        contato = self.get_object()
        contato = ContatoService.registrar_interacao(contato)
        serializer = self.get_serializer(contato)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas dos contatos"""
        escola_id = request.user.perfil.escola_id
        stats = ContatoService.calcular_estatisticas(escola_id)
        return Response(stats)

    from drf_spectacular.utils import extend_schema, OpenApiParameter

    class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):

        @extend_schema(
            summary="Registrar interação com contato",
            description="Registra a data/hora da última interação com o contato",
            responses={200: ContatoSerializer}
        )
        @action(detail=True, methods=['post'])
        def registrar_interacao(self, request, pk=None):
            """Registrar última interação"""


import logging

logger = logging.getLogger('apps.contacts')


class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):

    def create(self, request, *args, **kwargs):
        logger.info(
            f"Criando contato - User: {request.user.id}, Escola: {request.user.perfil.escola_id}"
        )
        return super().create(request, *args, **kwargs)