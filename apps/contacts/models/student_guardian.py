# apps/contacts/models/student_guardian.py
from django.db import models


class StudentGuardian(models.Model):
    """
    Modelo intermediário entre Student e Guardian.
    Permite informações adicionais sobre o relacionamento.
    """

    class TipoResponsabilidade(models.TextChoices):
        FINANCEIRO = 'FIN', 'Responsável Financeiro'
        PEDAGOGICO = 'PED', 'Responsável Pedagógico'
        EMERGENCIA = 'EMG', 'Contato de Emergência'
        TODOS = 'ALL', 'Todos os Tipos'

    student = models.ForeignKey(
        'contacts.Student',
        on_delete=models.CASCADE,
        verbose_name='Aluno'
    )

    guardian = models.ForeignKey(
        'contacts.Guardian',
        on_delete=models.CASCADE,
        verbose_name='Responsável'
    )

    tipo_responsabilidade = models.CharField(
        max_length=3,
        choices=TipoResponsabilidade.choices,
        default=TipoResponsabilidade.TODOS,
        verbose_name='Tipo de Responsabilidade'
    )

    prioridade = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Prioridade de Contato',
        help_text='1 = Principal, 2 = Secundário, etc.'
    )

    autorizado_buscar = models.BooleanField(
        default=True,
        verbose_name='Autorizado a Buscar Aluno'
    )

    receber_notificacoes = models.BooleanField(
        default=True,
        verbose_name='Receber Notificações'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_guardians'
        verbose_name = 'Vínculo Aluno-Responsável'
        verbose_name_plural = 'Vínculos Aluno-Responsável'
        unique_together = [['student', 'guardian']]
        ordering = ['student', 'prioridade']

        indexes = [
            models.Index(fields=['student', 'prioridade']),
            models.Index(fields=['guardian', 'receber_notificacoes']),
        ]

    def __str__(self):
        return f"{self.student.nome_completo} -> {self.guardian.nome_completo}"