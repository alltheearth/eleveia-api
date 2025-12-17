from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.filters import SearchFilter, OrderingFilter


# Imports dos models
from .models import (
    Escola
)

# Imports dos serializers
from .serializers import (
    EscolaSerializer
)

class EscolaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Escola

    PERMISSÕES:
    - Criar: Apenas superuser
    - Ler: Superuser (todas) ou usuários vinculados (sua escola)
    - Editar: Superuser (tudo) ou Gestor (campos não protegidos)
    - Deletar: Apenas superuser
    """
    serializer_class = EscolaSerializer
    permission_classes = [EscolaPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_escola', 'cnpj', 'cidade']
    ordering_fields = ['nome_escola', 'criado_em']

    def get_queryset(self):
        """Retorna escolas conforme permissão"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Escola.objects.all()

        if hasattr(self.request.user, 'perfil'):
            return Escola.objects.filter(id=self.request.user.perfil.escola.id)

        return Escola.objects.none()

    @action(detail=True, methods=['get'])
    def usuarios(self, request, pk=None):
        """Listar usuários da escola"""
        escola = self.get_object()
        usuarios = PerfilUsuario.objects.filter(escola=escola)
        serializer = PerfilUsuarioSerializer(usuarios, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @apenas_superuser
    def gerar_token(self, request, pk=None):
        """Gerar novo token de mensagens (apenas superuser)"""
        import secrets
        escola = self.get_object()
        escola.token_mensagens = secrets.token_urlsafe(30)
        escola.save()
        return Response({
            'message': 'Token gerado com sucesso',
            'token': escola.token_mensagens
        })