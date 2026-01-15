# ===================================================================
# apps/users/views.py - VERSÃO COMPLETA E OTIMIZADA
# ===================================================================
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Prefetch

from .models import UserProfile
from .serializers import (
    UserProfileSerializer,
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)
from core.permissions import IsManager, IsSchoolStaff


# ===================================================================
# AUTHENTICATION VIEWS (Function-based) - Endpoints Públicos
# ===================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    📝 Registro de novo usuário

    **Permissões:**
    - Público (AllowAny) - Qualquer um pode se registrar
    - Superusers podem criar usuários sem escola
    - Usuários normais DEVEM fornecer escola e role

    **Body:**
    ```json
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
    ```

    **Response 201:**
    ```json
    {
        "token": "abc123...",
        "user": {...},
        "message": "User registered successfully"
    }
    ```
    """
    serializer = RegisterSerializer(
        data=request.data,
        context={'request': request}
    )

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
    🔐 Login de usuário

    **Permissões:** Público (AllowAny)

    **Body:**
    ```json
    {
        "username": "user",
        "password": "senha123"
    }
    ```

    **Response 200:**
    ```json
    {
        "token": "abc123...",
        "user": {
            "id": 1,
            "username": "user",
            "email": "user@example.com",
            "profile": {...}
        },
        "message": "Login successful"
    }
    ```
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
    🚪 Logout de usuário

    **Permissões:** IsAuthenticated

    Deleta o token de autenticação do usuário.

    **Response 200:**
    ```json
    {
        "message": "Logout successful"
    }
    ```
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
    👤 Retorna perfil do usuário autenticado

    **Permissões:** IsAuthenticated

    **Response 200:**
    ```json
    {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "profile": {
            "id": 1,
            "school": 1,
            "school_name": "Escola ABC",
            "role": "operator",
            "role_display": "Operador/Auxiliar",
            "is_active": true,
            "phone": "11999999999",
            "date_of_birth": "1990-01-01"
        }
    }
    ```
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    ✏️ Atualiza perfil do usuário autenticado

    **Permissões:** IsAuthenticated

    Permite atualizar apenas campos não-críticos.
    Para alterar escola ou role, contate um manager.

    **Body (campos opcionais):**
    ```json
    {
        "first_name": "Novo Nome",
        "last_name": "Novo Sobrenome",
        "email": "novoemail@example.com"
    }
    ```

    **Response 200:**
    ```json
    {
        "user": {...},
        "message": "Profile updated successfully"
    }
    ```
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    🔑 Altera senha do usuário autenticado

    **Permissões:** IsAuthenticated

    **Body:**
    ```json
    {
        "old_password": "senha123",
        "new_password": "novasenha123",
        "new_password2": "novasenha123"
    }
    ```

    **Response 200:**
    ```json
    {
        "message": "Password changed successfully"
    }
    ```
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===================================================================
# USER VIEWSET (para gerenciamento de usuários por managers)
# ===================================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    👥 ViewSet para gerenciamento de usuários

    **Permissões:**
    - LIST/RETRIEVE: Apenas usuários da mesma escola
    - CREATE: Managers podem criar operators e end_users
    - UPDATE: Managers podem editar usuários da escola
    - DELETE: Managers podem deletar usuários da escola

    **Endpoints:**
    - GET    /api/v1/auth/users/          - Lista usuários da escola
    - GET    /api/v1/auth/users/{id}/     - Detalhes de um usuário
    - POST   /api/v1/auth/users/          - Cria novo usuário (managers)
    - PATCH  /api/v1/auth/users/{id}/     - Atualiza usuário (managers)
    - DELETE /api/v1/auth/users/{id}/     - Remove usuário (managers)
    - GET    /api/v1/auth/users/me/       - Dados do usuário autenticado
    - GET    /api/v1/auth/users/stats/    - Estatísticas de usuários (managers)
    """
    queryset = User.objects.select_related('profile__school').prefetch_related(
        Prefetch('profile', queryset=UserProfile.objects.select_related('school'))
    )
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'profile__role', 'profile__is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'email']
    ordering = ['-date_joined']

    def get_queryset(self):
        """
        🔒 Filtra usuários pela escola

        - Superuser: vê todos
        - Manager: vê usuários da sua escola
        - Outros: veem apenas a si mesmos
        """
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser or user.is_staff:
            return self.queryset

        # Manager vê usuários da sua escola
        if hasattr(user, 'profile') and user.profile.is_manager():
            return self.queryset.filter(
                profile__school=user.profile.school
            )

        # Outros veem apenas a si mesmos
        return self.queryset.filter(id=user.id)

    def get_permissions(self):
        """
        🔐 Permissões dinâmicas por action

        - create, update, partial_update, destroy: Apenas managers
        - Demais actions: Apenas autenticados
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManager()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        👤 GET /api/v1/auth/users/me/

        Retorna dados do usuário autenticado
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsManager])
    def stats(self, request):
        """
        📊 GET /api/v1/auth/users/stats/

        **Permissões:** IsManager

        Estatísticas de usuários da escola

        **Response:**
        ```json
        {
            "total": 25,
            "active": 23,
            "inactive": 2,
            "by_role": {
                "manager": 2,
                "operator": 8,
                "end_user": 15
            }
        }
        ```
        """
        queryset = self.get_queryset()

        # Estatísticas básicas
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'inactive': queryset.filter(is_active=False).count(),
        }

        # Usuários por role
        if hasattr(request.user, 'profile'):
            profiles = UserProfile.objects.filter(
                school=request.user.profile.school
            )
            stats['by_role'] = {
                'manager': profiles.filter(role='manager').count(),
                'operator': profiles.filter(role='operator').count(),
                'end_user': profiles.filter(role='end_user').count(),
            }

        return Response(stats)


# ===================================================================
# USER PROFILE VIEWSET
# ===================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    🎭 ViewSet para gerenciamento de perfis de usuários

    **Permissões:**
    - End User: Apenas próprio perfil (read-only)
    - Manager: Todos os perfis da escola (CRUD)
    - Superuser: Todos os perfis (CRUD)

    **Endpoints:**
    - GET    /api/v1/auth/profiles/              - Lista perfis
    - GET    /api/v1/auth/profiles/{id}/         - Detalhes de um perfil
    - POST   /api/v1/auth/profiles/              - Cria perfil (managers)
    - PATCH  /api/v1/auth/profiles/{id}/         - Atualiza perfil
    - DELETE /api/v1/auth/profiles/{id}/         - Remove perfil (managers)
    - GET    /api/v1/auth/profiles/me/           - Perfil do usuário autenticado
    - GET    /api/v1/auth/profiles/school_users/ - Usuários da escola (managers)
    """
    queryset = UserProfile.objects.select_related('user', 'school')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'is_active', 'school']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'user__username']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        🔒 Filtra perfis pela escola

        - Superuser: vê todos
        - Manager: vê todos da escola
        - Outros: veem apenas o próprio
        """
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser or user.is_staff:
            return self.queryset

        # Usuário precisa ter perfil
        if not hasattr(user, 'profile'):
            return UserProfile.objects.none()

        profile = user.profile

        # Manager vê todos da escola
        if profile.is_manager():
            return self.queryset.filter(school=profile.school)

        # Outros veem apenas o próprio
        return self.queryset.filter(user=user)

    def get_permissions(self):
        """
        🔐 Permissões dinâmicas

        - create, destroy: Apenas managers
        - Demais: Autenticados
        """
        if self.action in ['create', 'destroy']:
            return [IsManager()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        👤 GET /api/v1/auth/profiles/me/

        Retorna perfil do usuário autenticado
        """
        if not hasattr(request.user, 'profile'):
            return Response(
                {'error': 'User has no profile'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsManager])
    def school_users(self, request):
        """
        👥 GET /api/v1/auth/profiles/school_users/

        **Permissões:** IsManager

        Lista todos os usuários da escola do manager
        """
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

    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def toggle_active(self, request, pk=None):
        """
        🔄 PATCH /api/v1/auth/profiles/{id}/toggle_active/

        **Permissões:** IsManager

        Ativa/desativa um perfil de usuário
        """
        profile = self.get_object()
        profile.is_active = not profile.is_active
        profile.save()

        return Response({
            'id': profile.id,
            'is_active': profile.is_active,
            'message': f'Profile {"activated" if profile.is_active else "deactivated"}'
        })

    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def change_role(self, request, pk=None):
        """
        🎭 PATCH /api/v1/auth/profiles/{id}/change_role/

        **Permissões:** IsManager

        Altera o role de um usuário

        **Body:**
        ```json
        {
            "role": "operator"  // manager, operator ou end_user
        }
        ```
        """
        profile = self.get_object()
        new_role = request.data.get('role')

        if not new_role:
            return Response(
                {'error': 'Role is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_role not in ['manager', 'operator', 'end_user']:
            return Response(
                {'error': 'Invalid role. Must be: manager, operator or end_user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.role = new_role
        profile.save()

        return Response({
            'id': profile.id,
            'role': profile.role,
            'role_display': profile.get_role_display(),
            'message': f'Role changed to {profile.get_role_display()}'
        })