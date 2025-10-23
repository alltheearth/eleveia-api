# eleveai/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class Escola(models.Model):
    """Modelo para armazenar informações da escola"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escolas', null=True, blank=True)

    nome_escola = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=20, unique=True)
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


class Contato(models.Model):
    """Modelo para armazenar contatos das escolas"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contatos', null=True, blank=True)
    escola = models.OneToOneField(Escola, on_delete=models.CASCADE, related_name='contato')

    email_principal = models.EmailField()
    telefone_principal = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    horario_aula = models.CharField(max_length=50)

    diretor = models.CharField(max_length=255)
    email_diretor = models.EmailField()
    coordenador = models.CharField(max_length=255)
    email_coordenador = models.EmailField()

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'

    def __str__(self):
        return f"Contato - {self.escola.nome_escola}"


class CalendarioEvento(models.Model):
    """Modelo para armazenar eventos do calendário escolar"""
    TIPO_CHOICES = [
        ('feriado', '📌 Feriado'),
        ('prova', '📝 Prova/Avaliação'),
        ('formatura', '🎓 Formatura'),
        ('evento_cultural', '🎉 Evento Cultural'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos', null=True, blank=True)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='eventos')

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

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='faqs', null=True, blank=True)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='faqs')

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

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos', null=True, blank=True)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='documentos')

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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards', null=True, blank=True)
    escola = models.OneToOneField(Escola, on_delete=models.CASCADE, related_name='dashboard')

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


# ========================
# SIGNALS
# ========================

@receiver(post_save, sender=User)
def criar_token_usuario(sender, instance=None, created=False, **kwargs):
    """Cria token automaticamente quando um usuário é criado"""
    if created:
        Token.objects.create(user=instance)
        print(f"✅ Token criado para usuário: {instance.username}")


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

    # Campos adicionais úteis
    observacoes = models.TextField(blank=True)
    interesses = models.JSONField(default=dict, blank=True)  # Ex: {"nivel": "fundamental", "turno": "manha"}

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Campos de controle
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

