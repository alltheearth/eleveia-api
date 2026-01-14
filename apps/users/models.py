from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class UserProfile(models.Model):
    """Extends Django User with school-specific roles"""

    ROLE_CHOICES = [
        ('manager', 'Gestor da Escola'),
        ('operator', 'Operador'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='user_profiles',
        verbose_name='Escola'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='operator',
        verbose_name='Tipo de Acesso'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        db_table = 'users_userprofile'
        indexes = [
            models.Index(fields=['school', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({self.school.school_name})"

    def is_manager(self):
        return self.role == 'manager'

    def is_operator(self):
        return self.role == 'operator'


@receiver(post_save, sender=User)
def create_user_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)