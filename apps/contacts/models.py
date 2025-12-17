from django.db import models
from django.contrib.auth.models import User
from ..schools.models import Escola


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