from rest_framework import serializers
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento

class ContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = [
            'id', 'email_principal', 'telefone_principal', 'whatsapp',
            'instagram', 'facebook', 'horario_aula', 'diretor',
            'email_diretor', 'coordenador', 'email_coordenador'
        ]


class CalendarioEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarioEvento
        fields = ['id', 'data', 'evento', 'tipo', 'criado_em']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'pergunta', 'resposta', 'categoria', 'status', 'criado_em']


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ['id', 'nome', 'arquivo', 'status', 'criado_em']


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = [
            'id', 'status_agente', 'interacoes_hoje', 'documentos_upload',
            'faqs_criadas', 'leads_capturados', 'taxa_resolucao', 'novos_hoje'
        ]


class EscolaSerializer(serializers.ModelSerializer):
    contato = ContatoSerializer(read_only=True)
    dashboard = DashboardSerializer(read_only=True)
    
    class Meta:
        model = Escola
        fields = [
            'id', 'nome_escola', 'cnpj', 'telefone', 'email', 'website',
            'logo', 'cep', 'endereco', 'cidade', 'estado', 'complemento',
            'sobre', 'niveis_ensino', 'contato', 'dashboard', 'criado_em'
        ]


class EscolaDetailSerializer(serializers.ModelSerializer):
    contato = ContatoSerializer(read_only=True)
    dashboard = DashboardSerializer(read_only=True)
    eventos = CalendarioEventoSerializer(read_only=True, many=True)
    faqs = FAQSerializer(read_only=True, many=True)
    documentos = DocumentoSerializer(read_only=True, many=True)
    
    class Meta:
        model = Escola
        fields = [
            'id', 'nome_escola', 'cnpj', 'telefone', 'email', 'website',
            'logo', 'cep', 'endereco', 'cidade', 'estado', 'complemento',
            'sobre', 'niveis_ensino', 'contato', 'dashboard', 'eventos',
            'faqs', 'documentos', 'criado_em', 'atualizado_em'
        ]