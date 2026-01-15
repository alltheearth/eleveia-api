# ===================================================================
# apps/users/views.py - VERSÃO CORRIGIDA E COMPLETA
# ===================================================================
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import UserProfile
from .serializers import (
    UserProfileSerializer,
    UserSerializer,
    RegisterSerializer,
    LoginSerializer
)
from core.permissions import IsManager


# ===================================================================
# AUTHENTICATION VIEWS (Function-based)
# ===================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Registro de novo usuário.

    Body:
    {
        "username": "novouser",
        "email": "user@example.com",
        "password": "senha123",
        "password2": "senha123",
        "first_name": "Nome",
        "last_name": "Sobrenome",
        "school_id": 1,  // obrigatório para não-superusers
        "role": "operator"  // manager, operator ou end_user
    }
    """
    serializer = RegisterSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login de usuário.

    Body:
    {
        "username": "user",
        "password": "senha123"
    }
    """
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout de usuário.
    Deleta o token de autenticação.
    """
    try:
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Retorna perfil do usuário autenticado.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Atualiza perfil do usuário autenticado.

    Body (campos opcionais):
    {
        "first_name": "Novo Nome",
        "last_name": "Novo Sobrenome",
        "email": "novoemail@example.com"
    }
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===================================================================
# USER VIEWSET (para gerenciamento de usuários por managers)
# ===================================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de usuários.

    Permissões:
    - LIST/RETRIEVE: Apenas usuários da mesma escola
    - CREATE: Managers podem criar operators e end_users
    - UPDATE: Managers podem editar usuários da escola
    - DELETE: Managers podem deletar usuários da escola
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtra usuários pela escola"""
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser or user.is_staff:
            return User.objects.all()

        # Manager vê usuários da sua escola
        if hasattr(user, 'profile'):
            if user.profile.is_manager():
                return User.objects.filter(
                    profile__school=user.profile.school
                )

        # Outros veem apenas a si mesmos
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        """Permissões dinâmicas"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManager()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna dados do usuário autenticado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# ===================================================================
# USER PROFILE VIEWSET
# ===================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de perfis de usuários.

    Permissões:
    - End User: Apenas próprio perfil (read-only)
    - Manager: Todos os perfis da escola
    - Superuser: Todos os perfis
    """
    queryset = UserProfile.objects.select_related('user', 'school')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtra perfis pela escola"""
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser or user.is_staff:
            return UserProfile.objects.all()

        # Usuário precisa ter perfil
        if not hasattr(user, 'profile'):
            return UserProfile.objects.none()

        profile = user.profile

        # Manager vê todos da escola
        if profile.is_manager():
            return UserProfile.objects.filter(school=profile.school)

        # Outros veem apenas o próprio
        return UserProfile.objects.filter(user=user)

    def get_permissions(self):
        """Permissões dinâmicas"""
        if self.action in ['create', 'destroy']:
            return [IsManager()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna perfil do usuário autenticado"""
        if not hasattr(request.user, 'profile'):
            return Response(
                {'error': 'User has no profile'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def school_users(self, request):
        """Lista usuários da escola (apenas managers)"""
        if not hasattr(request.user, 'profile'):
            return Response(
                {'error': 'No profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.profile.is_manager():
            return Response(
                {'error': 'Only managers can view all school users'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)