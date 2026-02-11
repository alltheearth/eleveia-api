# apps/contacts/models/student.py
from django.db import models


class Student(models.Model):
    """
    Modelo de Estudante/Aluno.
    """

    # Campos
    nome_completo = models.CharField(max_length=200)
    data_nascimento = models.DateField()
    matricula = models.CharField(max_length=50, unique=True)

    # Relacionamento Many-to-Many com Guardian
    guardians = models.ManyToManyField(
        'contacts.Guardian',
        through='StudentGuardian',
        related_name='students',
        verbose_name='Responsáveis'
    )

    # Controle
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['nome_completo']

        indexes = [
            models.Index(fields=['matricula']),
            models.Index(fields=['ativo', '-created_at']),
        ]

    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"

    @property
    def idade(self):
        """Calcula idade do aluno."""
        from datetime import date
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
                (hoje.month, hoje.day) <
                (self.data_nascimento.month, self.data_nascimento.day)
        )