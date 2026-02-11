# apps/contacts/views/contact_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from ..models import Contato
from ..serializers import ContatoSerializer, ContatoCreateSerializer
from ..services import ContatoService
from ..selectors import ContatoSelector


class ContatoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Contatos.
    REGRA: Apenas orquestração!
    - Recebe request
    - Chama service/selector
    - Retorna response
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ContatoSerializer

    def get_queryset(self):
        """Usa selector para query otimizada."""
        return ContatoSelector.get_all_ativos()

    def get_serializer_class(self):
        """Serializer específico por ação."""
        if self.action == 'create':
            return ContatoCreateSerializer
        return ContatoSerializer

    def create(self, request, *args, **kwargs):
        """
        Cria novo contato.
        POST /api/contacts/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ Chama o service (lógica de negócio)
        try:
            contato = ContatoService.criar_contato(serializer.validated_data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retorna resposta serializada
        output_serializer = ContatoSerializer(contato)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Atualiza contato existente."""
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        # Chama service
        try:
            contato = ContatoService.atualizar_contato(
                contato_id=kwargs['pk'],
                data=serializer.validated_data
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        output_serializer = ContatoSerializer(contato)
        return Response(output_serializer.data)

    @action(detail=False, methods=['get'])
    def ativos(self, request):
        """
        Endpoint customizado: GET /api/contacts/ativos/
        """
        contatos = ContatoSelector.get_all_ativos()
        serializer = self.get_serializer(contatos, many=True)
        return Response(serializer.data)