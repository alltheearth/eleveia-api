from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento
from .serializers import (
    EscolaSerializer, EscolaDetailSerializer, ContatoSerializer,
    CalendarioEventoSerializer, FAQSerializer, DashboardSerializer, DocumentoSerializer
)

class EscolaViewSet(viewsets.ModelViewSet):
    queryset = Escola.objects.all()
    serializer_class = EscolaSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_escola', 'cnpj', 'cidade']
    ordering_fields = ['nome_escola', 'criado_em']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EscolaDetailSerializer
        return EscolaSerializer
    
    @action(detail=True, methods=['get'])
    def atividade(self, request, pk=None):
        escola = self.get_object()
        atividades = {
            'ultimos_7_dias': [45, 52, 48, 65, 58, 72, 68]
        }
        return Response(atividades)


class ContatoViewSet(viewsets.ModelViewSet):
    queryset = Contato.objects.all()
    serializer_class = ContatoSerializer
    
    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response({'erro': 'escola_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        contato = Contato.objects.filter(escola_id=escola_id).first()
        if not contato:
            return Response({'erro': 'Contato não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(contato)
        return Response(serializer.data)


class CalendarioEventoViewSet(viewsets.ModelViewSet):
    queryset = CalendarioEvento.objects.all()
    serializer_class = CalendarioEventoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['evento']
    ordering_fields = ['data']
    
    def get_queryset(self):
        queryset = CalendarioEvento.objects.all()
        escola_id = self.request.query_params.get('escola_id')
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def proximos_eventos(self, request):
        from django.utils import timezone
        escola_id = request.query_params.get('escola_id')
        
        queryset = CalendarioEvento.objects.filter(data__gte=timezone.now().date())
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        
        serializer = self.get_serializer(queryset[:5], many=True)
        return Response(serializer.data)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['pergunta', 'categoria']
    ordering_fields = ['categoria', 'criado_em']
    
    def get_queryset(self):
        queryset = FAQ.objects.all()
        escola_id = self.request.query_params.get('escola_id')
        status_filter = self.request.query_params.get('status')
        
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    
    def get_queryset(self):
        queryset = Documento.objects.all()
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
        queryset = Documento.objects.filter(status__in=['pendente', 'erro'])
        
        if escola_id:
            queryset = queryset.filter(escola_id=escola_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    
    @action(detail=False, methods=['get'])
    def by_escola(self, request):
        escola_id = request.query_params.get('escola_id')
        if not escola_id:
            return Response({'erro': 'escola_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        dashboard = Dashboard.objects.filter(escola_id=escola_id).first()
        if not dashboard:
            return Response({'erro': 'Dashboard não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

