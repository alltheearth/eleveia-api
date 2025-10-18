from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento
from .serializers import (
    EscolaSerializer, ContatoSerializer, CalendarioEventoSerializer,
    FAQSerializer, DocumentoSerializer, DashboardSerializer
)
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .serializers import UsuarioSerializer, RegistroSerializer, LoginSerializer



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


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    """Registrar novo usuário"""
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.get(user=user)
        return Response({
            'message': 'Usuário criado com sucesso',
            'token': token.key,
            'user': UsuarioSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login e obtenção de token"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token = Token.objects.get(user=user)
        return Response({
            'message': 'Login realizado com sucesso',
            'token': token.key,
            'user': UsuarioSerializer(user).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout - deleta o token"""
    try:
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout realizado com sucesso'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({
            'message': 'Perfil atualizado com sucesso',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar usuários (apenas admin)"""
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)