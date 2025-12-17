from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

# Imports dos models
from .models import (
    Escola, Contato, CalendarioEvento, FAQ, Dashboard,
    Documento, Lead, PerfilUsuario
)

# Imports dos serializers
from .serializers import (
    EscolaSerializer, ContatoSerializer, CalendarioEventoSerializer,
    FAQSerializer, DocumentoSerializer, DashboardSerializer,
    UsuarioSerializer, RegistroSerializer, LoginSerializer,
    LeadSerializer, PerfilUsuarioSerializer
)

# Imports das permissões
from .permissions import (
    EscolaPermission, GestorOuOperadorPermission, ApenasGestorPermission,
    UsuarioEscolaMixin, apenas_superuser, apenas_gestor
)


# ==========================================
# AUTENTICAÇÃO
# ==========================================
class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Usuários
    Apenas leitura - gestão via admin
    """
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Admin vê todos, usuário comum vê apenas ele mesmo"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login e obtenção de token"""
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)

    # Buscar perfil se existir
    perfil_data = None
    if hasattr(user, 'perfil'):
        perfil_data = PerfilUsuarioSerializer(user.perfil).data

    return Response({
        'message': 'Login realizado com sucesso',
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'perfil': perfil_data
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    """
    Registrar novo usuário

    REGRAS:
    - Qualquer um pode se registrar SE informar escola + tipo
    - Superuser pode criar usuários admin (sem escola)
    """
    serializer = RegistroSerializer(data=request.data, context={'request': request})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        # Buscar perfil se foi criado
        perfil_data = None
        if hasattr(user, 'perfil'):
            perfil_data = PerfilUsuarioSerializer(user.perfil).data

        return Response({
            'message': 'Usuário criado com sucesso',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'perfil': perfil_data
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Erro ao criar usuário: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout - deleta o token"""
    try:
        request.user.auth_token.delete()
        return Response(
            {'message': 'Logout realizado com sucesso'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    """Obter dados do usuário logado com perfil"""
    serializer = UsuarioSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def atualizar_perfil(request):
    """Atualizar dados do usuário logado"""
    user = request.user
    serializer = UsuarioSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Perfil atualizado com sucesso',
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

