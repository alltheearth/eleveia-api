from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


# eleveai/views.py - ADICIONAR ao arquivo existente

# Adicione este import no topo do arquivo
from .models import Contato  # Adicionar junto com os outros imports de models
from .serializers import ContatoSerializer  # Adicionar junto com os outros imports de serializers


# ✅ IMPORTAR AS PERMISSÕES PERSONALIZADAS
from .permissions import IsOwnerOrAdmin, IsAdminOrReadOnly

# IsOwnerOrAdmin: Usuários podem fazer CRUD completo (criar, ler, editar, deletar) em seus dados
# IsAdminOrReadOnly: Apenas leitura para usuários comuns, tudo para admin

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
    LoginSerializer,
    Lead,
    LeadSerializer
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
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
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
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_escola', 'cnpj', 'cidade']
    ordering_fields = ['nome_escola', 'criado_em']

    def get_queryset(self):
        """
        Retorna todas as escolas para admin,
        apenas escolas do usuário para usuários comuns
        """
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Escola.objects.all()
        return Escola.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['get'])
    def atividade(self, request, pk=None):
        escola = self.get_object()

        # Verifica permissão
        if not (request.user.is_superuser or request.user.is_staff):
            if escola.usuario != request.user:
                return Response(
                    {'erro': 'Acesso negado'},
                    status=status.HTTP_403_FORBIDDEN
                )

        atividades = {
            'ultimos_7_dias': [45, 52, 48, 65, 58, 72, 68]
        }
        return Response(atividades)


"""class ContatoViewSet(viewsets.ModelViewSet):
    serializer_class = ContatoSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        """"Admin vê tudo, usuário comum vê apenas seus contatos""""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Contato.objects.all()
        return Contato.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response(
                {'erro': 'escola_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Busca o contato
        if request.user.is_superuser or request.user.is_staff:
            contato = Contato.objects.filter(escola_id=escola_id).first()
        else:
            contato = Contato.objects.filter(
                usuario=request.user,
                escola_id=escola_id
            ).first()

        if not contato:
            return Response(
                {'erro': 'Contato não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(contato)
        return Response(serializer.data)
"""

class CalendarioEventoViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarioEventoSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['evento']
    ordering_fields = ['data']

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas seus eventos"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = CalendarioEvento.objects.all()
        else:
            queryset = CalendarioEvento.objects.filter(usuario=self.request.user)

        escola_id = self.request.query_params.get('escola_id')
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        return queryset

    @action(detail=False, methods=['get'])
    def proximos_eventos(self, request):
        escola_id = request.query_params.get('escola_id')

        if request.user.is_superuser or request.user.is_staff:
            queryset = CalendarioEvento.objects.filter(
                data__gte=timezone.now().date()
            )
        else:
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
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['pergunta', 'categoria']
    ordering_fields = ['categoria', 'criado_em']

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas suas FAQs"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = FAQ.objects.all()
        else:
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
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas seus documentos"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = Documento.objects.all()
        else:
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

        if request.user.is_superuser or request.user.is_staff:
            queryset = Documento.objects.filter(status__in=['pendente', 'erro'])
        else:
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
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas seus dashboards"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Dashboard.objects.all()
        return Dashboard.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response(
                {'erro': 'escola_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Busca o dashboard
        if request.user.is_superuser or request.user.is_staff:
            dashboard = Dashboard.objects.filter(escola_id=escola_id).first()
        else:
            dashboard = Dashboard.objects.filter(
                usuario=request.user,
                escola_id=escola_id
            ).first()

        if not dashboard:
            return Response(
                {'erro': 'Dashboard não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar usuários (apenas admin tem acesso completo)"""
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Admin vê todos, usuário comum vê apenas ele mesmo"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar Leads"""
    serializer_class = LeadSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone']
    ordering_fields = ['nome', 'criado_em', 'status']

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas seus leads"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(usuario=self.request.user)

        # Filtros via query params
        escola_id = self.request.query_params.get('escola_id')
        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas dos leads"""
        escola_id = request.query_params.get('escola_id')

        if request.user.is_superuser or request.user.is_staff:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        stats = {
            'total': queryset.count(),
            'novo': queryset.filter(status='novo').count(),
            'contato': queryset.filter(status='contato').count(),
            'qualificado': queryset.filter(status='qualificado').count(),
            'conversao': queryset.filter(status='conversao').count(),
            'perdido': queryset.filter(status='perdido').count(),
        }

        # Estatísticas por origem
        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        # Novos hoje
        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(
            criado_em__date=hoje
        ).count()

        # Taxa de conversão
        if stats['total'] > 0:
            stats['taxa_conversao'] = round(
                (stats['conversao'] / stats['total']) * 100, 2
            )
        else:
            stats['taxa_conversao'] = 0

        return Response(stats)

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna leads mais recentes"""
        escola_id = request.query_params.get('escola_id')
        limit = int(request.query_params.get('limit', 10))

        if request.user.is_superuser or request.user.is_staff:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        queryset = queryset.order_by('-criado_em')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mudar_status(self, request, pk=None):
        """Endpoint dedicado para mudar status do lead"""
        lead = self.get_object()
        novo_status = request.data.get('status')

        if novo_status not in dict(Lead.STATUS_CHOICES):
            return Response(
                {'erro': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lead.status = novo_status

        # Atualizar timestamps conforme status
        if novo_status == 'contato' and not lead.contatado_em:
            lead.contatado_em = timezone.now()
        elif novo_status == 'conversao' and not lead.convertido_em:
            lead.convertido_em = timezone.now()

        lead.save()

        serializer = self.get_serializer(lead)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def exportar_csv(self, request):
        """Exportar leads para CSV"""
        import csv
        from django.http import HttpResponse

        escola_id = request.data.get('escola_id')

        if request.user.is_superuser or request.user.is_staff:
            queryset = Lead.objects.all()
        else:
            queryset = Lead.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nome', 'Email', 'Telefone', 'Status',
            'Origem', 'Escola', 'Data Cadastro'
        ])

        for lead in queryset:
            writer.writerow([
                lead.id,
                lead.nome,
                lead.email,
                lead.telefone,
                lead.get_status_display(),
                lead.get_origem_display(),
                lead.escola.nome_escola,
                lead.criado_em.strftime('%d/%m/%Y %H:%M')
            ])

        return response

class ContatoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar Contatos Gerais"""
    serializer_class = ContatoSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone', 'tags']
    ordering_fields = ['nome', 'criado_em', 'status', 'ultima_interacao']

    def get_queryset(self):
        """Admin vê tudo, usuário comum vê apenas seus contatos"""
        if self.request.user.is_superuser or self.request.user.is_staff:
            queryset = Contato.objects.all()
        else:
            queryset = Contato.objects.filter(usuario=self.request.user)

        # Filtros via query params
        escola_id = self.request.query_params.get('escola_id')
        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas dos contatos"""
        escola_id = request.query_params.get('escola_id')

        if request.user.is_superuser or request.user.is_staff:
            queryset = Contato.objects.all()
        else:
            queryset = Contato.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        stats = {
            'total': queryset.count(),
            'ativos': queryset.filter(status='ativo').count(),
            'inativos': queryset.filter(status='inativo').count(),
        }

        # Estatísticas por origem
        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        # Novos hoje
        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(
            criado_em__date=hoje
        ).count()

        # Contatos com interação recente (últimos 7 dias)
        sete_dias_atras = timezone.now() - timedelta(days=7)
        stats['interacoes_recentes'] = queryset.filter(
            ultima_interacao__gte=sete_dias_atras
        ).count()

        return Response(stats)

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna contatos mais recentes"""
        escola_id = request.query_params.get('escola_id')
        limit = int(request.query_params.get('limit', 10))

        if request.user.is_superuser or request.user.is_staff:
            queryset = Contato.objects.all()
        else:
            queryset = Contato.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        queryset = queryset.order_by('-criado_em')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def registrar_interacao(self, request, pk=None):
        """Endpoint dedicado para registrar última interação"""
        contato = self.get_object()

        contato.ultima_interacao = timezone.now()
        contato.save()

        serializer = self.get_serializer(contato)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mudar_status(self, request, pk=None):
        """Endpoint dedicado para mudar status do contato"""
        contato = self.get_object()
        novo_status = request.data.get('status')

        if novo_status not in dict(Contato.STATUS_CHOICES):
            return Response(
                {'erro': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        contato.status = novo_status
        contato.save()

        serializer = self.get_serializer(contato)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def exportar_csv(self, request):
        """Exportar contatos para CSV"""
        import csv
        from django.http import HttpResponse

        escola_id = request.data.get('escola_id')

        if request.user.is_superuser or request.user.is_staff:
            queryset = Contato.objects.all()
        else:
            queryset = Contato.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contatos.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nome', 'Email', 'Telefone', 'Status',
            'Origem', 'Data Nascimento', 'Escola',
            'Última Interação', 'Data Cadastro', 'Tags'
        ])

        for contato in queryset:
            writer.writerow([
                contato.id,
                contato.nome,
                contato.email,
                contato.telefone,
                contato.get_status_display(),
                contato.get_origem_display(),
                contato.data_nascimento.strftime('%d/%m/%Y') if contato.data_nascimento else '',
                contato.escola.nome_escola,
                contato.ultima_interacao.strftime('%d/%m/%Y %H:%M') if contato.ultima_interacao else '',
                contato.criado_em.strftime('%d/%m/%Y %H:%M'),
                contato.tags
            ])

        return response

    @action(detail=False, methods=['get'])
    def por_tag(self, request):
        """Buscar contatos por tag específica"""
        tag = request.query_params.get('tag')
        escola_id = request.query_params.get('escola_id')

        if not tag:
            return Response(
                {'erro': 'Tag é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.is_superuser or request.user.is_staff:
            queryset = Contato.objects.all()
        else:
            queryset = Contato.objects.filter(usuario=request.user)

        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)

        # Buscar contatos que contenham a tag
        queryset = queryset.filter(tags__icontains=tag)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)