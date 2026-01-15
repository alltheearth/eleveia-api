# ===================================================================
# apps/users/models.py - VERSÃO CORRIGIDA SEM CONSTRAINT INVÁLIDA
# ===================================================================
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class UserProfile(models.Model):
    """
    Perfil de usuário com 4 níveis hierárquicos:

    1. SUPERUSER (Django is_superuser) - Não precisa de perfil obrigatório
    2. MANAGER - Gestor da escola
    3. OPERATOR - Operador/Auxiliar da escola
    4. END_USER - Cliente/Aluno/Responsável

    VALIDAÇÃO: Superusers podem ter school=NULL, outros usuários DEVEM ter escola.
    Esta validação é feita em nível de aplicação (clean/save), não no banco de dados.
    """

    ROLE_CHOICES = [
        ('manager', 'Gestor da Escola'),
        ('operator', 'Operador/Auxiliar'),
        ('end_user', 'Usuário Final (Cliente/Aluno)'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Usuário Django vinculado'
    )

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='user_profiles',
        verbose_name='Escola',
        null=True,
        blank=True,
        help_text='Escola vinculada (obrigatório para não-superusers)'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='end_user',
        verbose_name='Nível de Acesso',
        help_text='Define as permissões do usuário'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Usuário ativo no sistema'
    )

    # Metadados adicionais para END_USER
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone',
        help_text='Telefone de contato (especialmente para end_user)'
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Nascimento'
    )

    # Timestamps
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
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]
        # ✅ REMOVIDO: Constraint inválida com joined field
        # A validação agora é feita em clean() e no serializer

    def __str__(self):
        role_display = self.get_role_display()
        school_name = self.school.school_name if self.school else 'Sistema'
        return f"{self.user.username} - {role_display} ({school_name})"

    def clean(self):
        """
        ✅ VALIDAÇÃO EM NÍVEL DE APLICAÇÃO

        Regra de negócio: Superusers não precisam de escola,
        mas usuários normais (manager, operator, end_user) precisam.
        """
        super().clean()

        # Superusers e staff podem não ter escola
        if self.user.is_superuser or self.user.is_staff:
            return

        # Usuários normais DEVEM ter escola
        if not self.school:
            raise ValidationError({
                'school': 'Non-superuser profiles must have a school assigned. '
                          'Only superusers can have no school.'
            })

    def save(self, *args, **kwargs):
        """
        Sobrescreve save() para chamar clean() automaticamente.
        Garante que a validação sempre será executada.
        """
        # Executa validações antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    # ===============================================================
    # MÉTODOS DE VERIFICAÇÃO DE PERMISSÃO
    # ===============================================================

    def is_superuser(self):
        """Verifica se é superusuário Django"""
        return self.user.is_superuser or self.user.is_staff

    def is_manager(self):
        """Verifica se é gestor de escola"""
        return self.role == 'manager' and self.is_active

    def is_operator(self):
        """Verifica se é operador de escola"""
        return self.role == 'operator' and self.is_active

    def is_end_user(self):
        """Verifica se é usuário final"""
        return self.role == 'end_user' and self.is_active

    def is_school_staff(self):
        """Verifica se é staff da escola (manager ou operator)"""
        return self.role in ['manager', 'operator'] and self.is_active

    def can_manage_users(self):
        """Verifica se pode gerenciar outros usuários"""
        return self.is_superuser() or self.is_manager()

    def can_edit_school_data(self):
        """Verifica se pode editar dados não-sensíveis da escola"""
        return self.is_superuser() or self.is_manager()

    def can_edit_protected_fields(self):
        """Verifica se pode editar campos protegidos (CNPJ, nome, etc)"""
        return self.is_superuser()

    def belongs_to_school(self, school_id):
        """Verifica se pertence a uma escola específica"""
        if self.is_superuser():
            return True
        return self.school_id == school_id

    def get_accessible_schools(self):
        """Retorna escolas que o usuário pode acessar"""
        from apps.schools.models import School

        if self.is_superuser():
            return School.objects.all()
        elif self.school:
            return School.objects.filter(id=self.school_id)
        return School.objects.none()


# ===================================================================
# SIGNALS
# ===================================================================

@receiver(post_save, sender=User)
def create_user_token(sender, instance=None, created=False, **kwargs):
    """Cria token automaticamente para novos usuários"""
    if created:
        Token.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_superuser_profile(sender, instance=None, created=False, **kwargs):
    """
    Cria perfil automaticamente para superusers
    (sem escola vinculada, conforme regra de negócio)
    """
    if created and (instance.is_superuser or instance.is_staff):
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(
                user=instance,
                school=None,  # ✅ Superusers não precisam de escola
                role='manager',
                is_active=True
            )