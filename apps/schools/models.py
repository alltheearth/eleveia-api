from django.db import models

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
