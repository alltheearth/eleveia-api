"""
Modelos relacionados a usuários e perfis
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


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
        'schools.Escola',  # String reference para evitar circular import
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
# SIGNALS
# ==========================================

@receiver(post_save, sender=User)
def criar_token_usuario(sender, instance=None, created=False, **kwargs):
    """Cria token automaticamente quando um usuário é criado"""
    if created:
        Token.objects.create(user=instance)
        print(f"✅ Token criado para usuário: {instance.username}")