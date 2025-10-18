# eleveai/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Escola(models.Model):
    NIVEIS_CHOICES = [
        ('infantil', 'Educação Infantil'),
        ('fundamental_i', 'Ensino Fundamental I'),
        ('fundamental_ii', 'Ensino Fundamental II'),
        ('medio', 'Ensino Médio'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escolas')

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

    sobre = models.TextField()
    niveis_ensino = models.JSONField(default=dict)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Escola'
        verbose_name_plural = 'Escolas'
        unique_together = ('usuario', 'cnpj')

    def __str__(self):
        return self.nome_escola


class Contato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contatos')
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
        unique_together = ('usuario', 'escola')

    def __str__(self):
        return f"Contato - {self.escola.nome_escola}"


class CalendarioEvento(models.Model):
    TIPO_CHOICES = [
        ('feriado', '📌 Feriado'),
        ('prova', '📝 Prova/Avaliação'),
        ('formatura', '🎓 Formatura'),
        ('evento_cultural', '🎉 Evento Cultural'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos')
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
        unique_together = ('usuario', 'escola', 'data', 'evento')

    def __str__(self):
        return f"{self.evento} - {self.data}"


class FAQ(models.Model):
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='faqs')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='faqs')

    pergunta = models.CharField(max_length=500)
    resposta = models.TextField()
    categoria = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ativa')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-criado_em']
        unique_together = ('usuario', 'escola', 'pergunta')

    def __str__(self):
        return self.pergunta


class Documento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('processado', 'Processado'),
        ('erro', 'Erro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='documentos')

    nome = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='documentos/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        unique_together = ('usuario', 'escola', 'nome')

    def __str__(self):
        return self.nome


class Dashboard(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
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
        unique_together = ('usuario', 'escola')

    def __str__(self):
        return f"Dashboard - {self.escola.nome_escola}"


# Signal para criar token e dashboard
@receiver(post_save, sender=User)
def criar_token_usuario(sender, instance=None, created=False, **kwargs):
    if created:
        from rest_framework.authtoken.models import Token
        Token.objects.create(user=instance)