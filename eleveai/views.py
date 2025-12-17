# eleveai/views.py
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


# ==========================================
# VIEWSET - ESCOLA
# ==========================================

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


# ==========================================
# VIEWSETS - RECURSOS OPERACIONAIS
# ==========================================

class CalendarioEventoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Eventos
    Gestor e Operador podem CRUD completo
    """
    queryset = CalendarioEvento.objects.all()
    serializer_class = CalendarioEventoSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['evento']
    ordering_fields = ['data']

    @action(detail=False, methods=['get'])
    def proximos_eventos(self, request):
        """Retorna próximos eventos"""
        queryset = self.get_queryset().filter(
            data__gte=timezone.now().date()
        )[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FAQViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para FAQs
    Gestor e Operador podem CRUD completo
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['pergunta', 'categoria']
    ordering_fields = ['categoria', 'criado_em']


class DocumentoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Documentos
    Gestor e Operador podem CRUD completo
    """
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = [GestorOuOperadorPermission]

    @action(detail=False, methods=['get'])
    def nao_processados(self, request):
        """Documentos pendentes ou com erro"""
        queryset = self.get_queryset().filter(status__in=['pendente', 'erro'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Dashboard
    Todos podem visualizar o dashboard da sua escola
    """
    serializer_class = DashboardSerializer
    permission_classes = [GestorOuOperadorPermission]

    def get_queryset(self):
        """Retorna dashboard da escola do usuário"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Dashboard.objects.all()

        if hasattr(self.request.user, 'perfil'):
            return Dashboard.objects.filter(escola=self.request.user.perfil.escola)

        return Dashboard.objects.none()


class LeadViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Leads
    Gestor e Operador podem CRUD completo
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone']
    ordering_fields = ['nome', 'criado_em', 'status']

    def get_queryset(self):
        """Aplica filtros adicionais"""
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas dos leads"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'novo': queryset.filter(status='novo').count(),
            'contato': queryset.filter(status='contato').count(),
            'qualificado': queryset.filter(status='qualificado').count(),
            'conversao': queryset.filter(status='conversao').count(),
            'perdido': queryset.filter(status='perdido').count(),
        }

        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(criado_em__date=hoje).count()

        if stats['total'] > 0:
            stats['taxa_conversao'] = round(
                (stats['conversao'] / stats['total']) * 100, 2
            )
        else:
            stats['taxa_conversao'] = 0

        return Response(stats)

    @action(detail=True, methods=['post'])
    def mudar_status(self, request, pk=None):
        """Mudar status do lead"""
        lead = self.get_object()
        novo_status = request.data.get('status')

        if novo_status not in dict(Lead.STATUS_CHOICES):
            return Response(
                {'erro': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lead.status = novo_status

        if novo_status == 'contato' and not lead.contatado_em:
            lead.contatado_em = timezone.now()
        elif novo_status == 'conversao' and not lead.convertido_em:
            lead.convertido_em = timezone.now()

        lead.save()
        serializer = self.get_serializer(lead)
        return Response(serializer.data)


class ContatoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Contatos
    Gestor e Operador podem CRUD completo
    """
    queryset = Contato.objects.all()
    serializer_class = ContatoSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone', 'tags']
    ordering_fields = ['nome', 'criado_em', 'status', 'ultima_interacao']

    def get_queryset(self):
        """Aplica filtros adicionais"""
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas dos contatos"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'ativos': queryset.filter(status='ativo').count(),
            'inativos': queryset.filter(status='inativo').count(),
        }

        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(criado_em__date=hoje).count()

        sete_dias_atras = timezone.now() - timedelta(days=7)
        stats['interacoes_recentes'] = queryset.filter(
            ultima_interacao__gte=sete_dias_atras
        ).count()

        return Response(stats)

    @action(detail=True, methods=['post'])
    def registrar_interacao(self, request, pk=None):
        """Registrar última interação"""
        contato = self.get_object()
        contato.ultima_interacao = timezone.now()
        contato.save()
        serializer = self.get_serializer(contato)
        return Response(serializer.data)


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