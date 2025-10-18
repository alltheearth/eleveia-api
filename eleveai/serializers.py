from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Escola, Contato, CalendarioEvento, FAQ, Dashboard, Documento
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class EscolaSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Escola
        fields = [
            'id', 'usuario_id', 'nome_escola', 'cnpj', 'telefone', 'email',
            'website', 'logo', 'cep', 'endereco', 'cidade', 'estado', 'complemento',
            'sobre', 'niveis_ensino', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'criado_em', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class ContatoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'usuario_id', 'escola', 'email_principal', 'telefone_principal',
            'whatsapp', 'instagram', 'facebook', 'horario_aula', 'diretor',
            'email_diretor', 'coordenador', 'email_coordenador', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'atualizado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class CalendarioEventoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = CalendarioEvento
        fields = ['id', 'usuario_id', 'escola', 'data', 'evento', 'tipo', 'criado_em']
        read_only_fields = ['usuario_id', 'criado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class FAQSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = FAQ
        fields = ['id', 'usuario_id', 'escola', 'pergunta', 'resposta', 'categoria', 'status', 'criado_em']
        read_only_fields = ['usuario_id', 'criado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DocumentoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Documento
        fields = ['id', 'usuario_id', 'escola', 'nome', 'arquivo', 'status', 'criado_em']
        read_only_fields = ['usuario_id', 'criado_em']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class DashboardSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            'id', 'usuario_id', 'escola', 'status_agente', 'interacoes_hoje',
            'documentos_upload', 'faqs_criadas', 'leads_capturados', 'taxa_resolucao',
            'novos_hoje', 'atualizado_em'
        ]
        read_only_fields = ['usuario_id', 'atualizado_em']



@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Cria token automaticamente quando um usuário é criado"""
    if created:
        Token.objects.create(user=instance)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Credenciais inválidas.")
        data['user'] = user
        return data