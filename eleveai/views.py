from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# ✅ IMPORTAR OS SERIALIZERS
from .serializers import (
    EscolaSerializer,
    ContatoSerializer,
    CalendarioEventoSerializer,
    FAQSerializer,
    DocumentoSerializer,
    DashboardSerializer,
    UsuarioSerializer,
    RegistroSerializer,
    LoginSerializer
)

# ✅ IMPORTAR OS MODELS
from .models import (
    Escola,
    Contato,
    CalendarioEvento,
    FAQ,
    Dashboard,
    Documento
)

print("✅ Views imported successfully")


# ============================================
# AUTENTICAÇÃO - LOGIN, REGISTRO, LOGOUT
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login e obtenção de token"""
    print(f"🔐 Login request received: {request.data}")

    if not request.data:
        return Response(
            {'error': 'Nenhum dado foi enviado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = request.data.get('username')
    password = request.data.get('password')

    print(f"📝 Username: {username}, Password: {'*' * len(password) if password else 'None'}")

    if not username or not password:
        return Response(
            {'error': 'Username e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    print(f"🔍 User authenticated: {user}")

    if not user:
        return Response(
            {'error': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, created = Token.objects.get_or_create(user=user)
    print(f"✅ Token {'criado' if created else 'encontrado'}: {token.key[:20]}...")

    return Response(
        {
            'message': 'Login realizado com sucesso',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    """Registrar novo usuário"""
    print(f"📝 Register request received: {request.data}")

    if not request.data:
        return Response(
            {'error': 'Nenhum dado foi enviado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    password2 = request.data.get('password2')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    print(f"📋 Dados recebidos: username={username}, email={email}")

    if not all([username, email, password, password2]):
        return Response(
            {'error': 'Username, email, password e password2 são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password2:
        return Response(
            {'error': 'As senhas não coincidem'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'error': 'A senha deve ter no mínimo 8 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': f'Username "{username}" já existe'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'error': f'Email "{email}" já está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        print(f"✅ User criado: {user.username}")

        token, created = Token.objects.get_or_create(user=user)
        print(f"✅ Token criado: {token.key[:20]}...")

        return Response(
            {
                'message': 'Usuário criado com sucesso',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {str(e)}")
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
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    """Obter dados do usuário logado"""
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
        return Response(
            {
                'message': 'Perfil atualizado com sucesso',
                'user': serializer.data
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# VIEWSETS - ESCOLAS, CONTATOS, EVENTOS, etc
# ============================================

class EscolaViewSet(viewsets.ModelViewSet):
    serializer_class = EscolaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_escola', 'cnpj', 'cidade']
    ordering_fields = ['nome_escola', 'criado_em']

    def get_queryset(self):
        """Retorna apenas escolas do usuário logado"""
        return Escola.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['get'])
    def atividade(self, request, pk=None):
        escola = self.get_object()
        if escola.usuario != request.user:
            return Response({'erro': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)

        atividades = {
            'ultimos_7_dias': [45, 52, 48, 65, 58, 72, 68]
        }
        return Response(atividades)


class ContatoViewSet(viewsets.ModelViewSet):
    serializer_class = ContatoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas contatos do usuário logado"""
        return Contato.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response({'erro': 'escola_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        contato = Contato.objects.filter(
            usuario=request.user,
            escola_id=escola_id
        ).first()

        if not contato:
            return Response({'erro': 'Contato não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(contato)
        return Response(serializer.data)


class CalendarioEventoViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarioEventoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['evento']
    ordering_fields = ['data']

    def get_queryset(self):
        """Retorna apenas eventos do usuário logado"""
        queryset = CalendarioEvento.objects.filter(usuario=self.request.user)
        escola_id = self.request.query_params.get('escola_id')
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        return queryset

    @action(detail=False, methods=['get'])
    def proximos_eventos(self, request):
        from django.utils import timezone
        escola_id = request.query_params.get('escola_id')

        queryset = CalendarioEvento.objects.filter(
            usuario=request.user,
            data__gte=timezone.now().date()
        )
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        serializer = self.get_serializer(queryset[:5], many=True)
        return Response(serializer.data)


class FAQViewSet(viewsets.ModelViewSet):
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['pergunta', 'categoria']
    ordering_fields = ['categoria', 'criado_em']

    def get_queryset(self):
        """Retorna apenas FAQs do usuário logado"""
        queryset = FAQ.objects.filter(usuario=self.request.user)
        escola_id = self.request.query_params.get('escola_id')
        status_filter = self.request.query_params.get('status')

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class DocumentoViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas documentos do usuário logado"""
        queryset = Documento.objects.filter(usuario=self.request.user)
        escola_id = self.request.query_params.get('escola_id')
        status_filter = self.request.query_params.get('status')

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=False, methods=['get'])
    def nao_processados(self, request):
        escola_id = request.query_params.get('escola_id')
        queryset = Documento.objects.filter(
            usuario=request.user,
            status__in=['pendente', 'erro']
        )

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas dashboards do usuário logado"""
        return Dashboard.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response({'erro': 'escola_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        dashboard = Dashboard.objects.filter(
            usuario=request.user,
            escola_id=escola_id
        ).first()

        if not dashboard:
            return Response({'erro': 'Dashboard não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar usuários (apenas admin)"""
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)