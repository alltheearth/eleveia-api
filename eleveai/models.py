# eleveai/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# ==========================================
# PERFIL DE USUÁRIO - SISTEMA DE PERMISSÕES
# ==========================================

class PerfilUsuario(models.Model):
    """
    Perfil que define o tipo de acesso do usuário

    TIPOS:
    - gestor: Gerencia a escola (tudo exceto token, CNPJ, nome da escola)
    - operador: Funções administrativas (leads, contatos, eventos, FAQs)
    """
    TIPO_CHOICES = [
        ('gestor', 'Gestor da Escola'),
        ('operador', 'Operador'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    escola = models.ForeignKey(
        'Escola',
        on_delete=models.CASCADE,
        related_name='usuarios',
        help_text='Escola vinculada ao usuário'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='operador',
        help_text='Tipo de acesso do usuário'
    )
    ativo = models.BooleanField(
        default=True,
        help_text='Usuário ativo no sistema'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        indexes = [
            models.Index(fields=['escola', 'tipo']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} ({self.escola.nome_escola})"

    def is_gestor(self):
        """Verifica se é gestor"""
        return self.tipo == 'gestor'

    def is_operador(self):
        """Verifica se é operador"""
        return self.tipo == 'operador'


# ==========================================
# MODELO ESCOLA (ATUALIZADO)
# ==========================================

class Escola(models.Model):
    """Modelo para armazenar informações da escola"""

    # Campos imutáveis (só superuser pode alterar)
    nome_escola = models.CharField(
        max_length=255,
        help_text='Nome da escola (só superuser pode alterar)'
    )
    cnpj = models.CharField(
        max_length=20,
        unique=True,
        help_text='CNPJ da escola (só superuser pode alterar)'
    )
    token_mensagens = models.CharField(
        max_length=40,
        blank=True,
        help_text='Token para mensagens (só superuser pode alterar)'
    )

    # Campos editáveis pelo gestor
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    cep = models.CharField(max_length=10)
    endereco = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    complemento = models.CharField(max_length=255, blank=True)

    sobre = models.TextField(blank=True)
    niveis_ensino = models.JSONField(default=dict, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Escola'
        verbose_name_plural = 'Escolas'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_escola

    @property
    def campos_protegidos(self):
        """Campos que só superuser pode alterar"""
        return ['nome_escola', 'cnpj', 'token_mensagens']


# ==========================================
# OUTROS MODELOS (mantém usuario para compatibilidade)
# ==========================================

class CalendarioEvento(models.Model):
    """Modelo para armazenar eventos do calendário escolar"""
    TIPO_CHOICES = [
        ('feriado', '📌 Feriado'),
        ('prova', '📝 Prova/Avaliação'),
        ('formatura', '🎓 Formatura'),
        ('evento_cultural', '🎉 Evento Cultural'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='eventos'
    )

    data = models.DateField()
    evento = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['data']
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'

    def __str__(self):
        return f"{self.evento} - {self.data}"


class FAQ(models.Model):
    """Modelo para armazenar perguntas frequentes"""
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='faqs',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='faqs'
    )

    pergunta = models.CharField(max_length=500)
    resposta = models.TextField(blank=True)
    categoria = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ativa')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-criado_em']

    def __str__(self):
        return self.pergunta


class Documento(models.Model):
    """Modelo para armazenar documentos da escola"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('processado', 'Processado'),
        ('erro', 'Erro'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documentos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='documentos'
    )

    nome = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='documentos/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return self.nome


class Dashboard(models.Model):
    """Modelo para armazenar dados do dashboard"""
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        null=True,
        blank=True
    )
    escola = models.OneToOneField(
        Escola,
        on_delete=models.CASCADE,
        related_name='dashboard'
    )

    status_agente = models.CharField(max_length=20, default='ativo')
    interacoes_hoje = models.IntegerField(default=0)
    documentos_upload = models.IntegerField(default=0)
    faqs_criadas = models.IntegerField(default=0)

    leads_capturados = models.IntegerField(default=0)
    taxa_resolucao = models.IntegerField(default=0)
    novos_hoje = models.IntegerField(default=0)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'

    def __str__(self):
        return f"Dashboard - {self.escola.nome_escola}"


class Lead(models.Model):
    """Modelo para armazenar leads capturados pelo agente IA"""
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contato', 'Em Contato'),
        ('qualificado', 'Qualificado'),
        ('conversao', 'Conversão'),
        ('perdido', 'Perdido'),
    ]

    ORIGEM_CHOICES = [
        ('site', 'Site'),
        ('whatsapp', 'WhatsApp'),
        ('indicacao', 'Indicação'),
        ('ligacao', 'Ligação'),
        ('email', 'Email'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leads',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='leads'
    )

    nome = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='novo'
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='site'
    )

    observacoes = models.TextField(blank=True)
    interesses = models.JSONField(default=dict, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    contatado_em = models.DateTimeField(null=True, blank=True)
    convertido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['escola', 'status']),
            models.Index(fields=['criado_em']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


class Contato(models.Model):
    """Modelo para armazenar contatos gerais"""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
    ]

    ORIGEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('site', 'Site'),
        ('telefone', 'Telefone'),
        ('presencial', 'Presencial'),
        ('email', 'Email'),
        ('indicacao', 'Indicação'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contatos',
        null=True,
        blank=True
    )
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name='contatos'
    )

    nome = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20)

    data_nascimento = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo'
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='whatsapp'
    )

    ultima_interacao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Contato Geral'
        verbose_name_plural = 'Contatos Gerais'
        indexes = [
            models.Index(fields=['escola', 'status']),
            models.Index(fields=['criado_em']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


# ==========================================
# SIGNALS
# ==========================================

@receiver(post_save, sender=User)
def criar_token_usuario(sender, instance=None, created=False, **kwargs):
    """Cria token automaticamente quando um usuário é criado"""
    if created:
        Token.objects.create(user=instance)
        print(f"✅ Token criado para usuário: {instance.username}")