# apps/contacts/models/contact.py
from django.db import models

class Contato(models.Model):
    """
    Modelo de Contato.
    REGRA: Apenas definição de campos e métodos simples.
    SEM lógica de negócio complexa!
    """
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contatos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['ativo', '-created_at']),
        ]

    def __str__(self):
        return self.nome

    # ✅ OK: Métodos simples de propriedade
    @property
    def nome_completo(self):
        return f"{self.nome} - {self.email}"
