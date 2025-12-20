# apps/users/views.py - ✅ COM DEBUG

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import PerfilUsuario
from .serializers import (
    UsuarioSerializer, PerfilUsuarioSerializer,
    RegistroSerializer, LoginSerializer
)


# ==========================================
# AUTENTICAÇÃO - Function Views
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login e obtenção de token"""
    print("🔐 [LOGIN] Recebendo request de login")
    print(f"📝 [LOGIN] Dados: {request.data}")

    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        print(f"❌ [LOGIN] Validação falhou: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)

    print(f"✅ [LOGIN] Login bem-sucedido para: {user.username}")
    print(f"🔑 [LOGIN] Token gerado: {token.key[:20]}...")

    # Buscar perfil se existir
    perfil_data = None
    if hasattr(user, 'perfil'):
        perfil_data = PerfilUsuarioSerializer(user.perfil).data
        print(f"👤 [LOGIN] Perfil encontrado: {perfil_data}")
    else:
        print("⚠️ [LOGIN] Usuário não tem perfil!")

    response_data = {
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
    }

    print(f"📤 [LOGIN] Enviando resposta com token: {token.key[:20]}...")
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    """Registrar novo usuário"""
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
    print("=" * 50)
    print("👤 [PERFIL] Request recebido")
    print(f"🔑 [PERFIL] User autenticado: {request.user}")
    print(f"🔑 [PERFIL] User ID: {request.user.id}")
    print(f"🔑 [PERFIL] Username: {request.user.username}")

    # Verificar headers
    auth_header = request.META.get('HTTP_AUTHORIZATION', 'Não encontrado')
    print(f"🔐 [PERFIL] Authorization header: {auth_header[:30] if auth_header != 'Não encontrado' else auth_header}...")

    # Verificar se tem perfil
    if hasattr(request.user, 'perfil'):
        print(f"✅ [PERFIL] Usuário TEM perfil")
        print(f"🏫 [PERFIL] Escola: {request.user.perfil.escola.nome_escola}")
    else:
        print(f"⚠️ [PERFIL] Usuário NÃO TEM perfil!")

    serializer = UsuarioSerializer(request.user)
    print(f"📤 [PERFIL] Enviando dados: {serializer.data}")
    print("=" * 50)

    return Response(serializer.data.email)


@api_view(['PUT', 'PATCH'])
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


# ==========================================
# VIEWSETS
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