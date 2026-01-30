# apps/storage/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.schools.models import School


class StorageFile(models.Model):
    """
    Metadados de arquivos armazenados no R2.
    Binários ficam no R2, metadados no PostgreSQL.
    """

    MIME_TYPES = [
        ('application/pdf', 'PDF'),
        ('image/jpeg', 'JPEG Image'),
        ('image/png', 'PNG Image'),
        ('image/gif', 'GIF Image'),
        ('image/webp', 'WebP Image'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word Document'),
        ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel Spreadsheet'),
        ('application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint'),
        ('text/plain', 'Text File'),
        ('text/csv', 'CSV File'),
        ('application/zip', 'ZIP Archive'),
    ]

    # ============================================
    # IDENTIFICAÇÃO
    # ============================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='storage_files',
        verbose_name='Escola'
    )

    # ============================================
    # ARQUIVO
    # ============================================
    name = models.CharField(
        max_length=255,
        verbose_name='Nome'
    )

    size = models.BigIntegerField(
        verbose_name='Tamanho (bytes)'
    )

    mime_type = models.CharField(
        max_length=100,
        choices=MIME_TYPES,
        verbose_name='Tipo'
    )

    extension = models.CharField(
        max_length=10,
        verbose_name='Extensão'
    )

    # ============================================
    # LOCALIZAÇÃO NO R2
    # ============================================
    r2_key = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='Chave R2',
        help_text='Caminho único no bucket R2'
    )

    r2_bucket = models.CharField(
        max_length=100,
        verbose_name='Bucket R2',
        help_text='Nome do bucket onde está armazenado'
    )

    # ============================================
    # HIERARQUIA (Estrutura de Pastas Virtual)
    # ============================================
    parent_folder = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Pasta Pai'
    )

    is_folder = models.BooleanField(
        default=False,
        verbose_name='É Pasta?'
    )

    # ============================================
    # METADADOS
    # ============================================
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        verbose_name='Criado por'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    # ============================================
    # PERMISSÕES E VISIBILIDADE
    # ============================================
    is_public = models.BooleanField(
        default=False,
        verbose_name='Público',
        help_text='Se true, gera URLs públicas'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )

    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Tags',
        help_text='Tags separadas por vírgula'
    )

    # ============================================
    # META
    # ============================================
    class Meta:
        db_table = 'storage_files'
        verbose_name = 'Arquivo'
        verbose_name_plural = 'Arquivos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'parent_folder']),
            models.Index(fields=['school', 'is_folder']),
            models.Index(fields=['r2_key']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        folder_icon = '📁' if self.is_folder else '📄'
        return f"{folder_icon} {self.name} ({self.school.school_name})"

    # ============================================
    # PROPERTIES
    # ============================================
    @property
    def full_path(self):
        """Retorna caminho completo (ex: /docs/2024/file.pdf)"""
        if not self.parent_folder:
            return f"/{self.name}"
        return f"{self.parent_folder.full_path}/{self.name}"

    @property
    def size_formatted(self):
        """Retorna tamanho formatado (ex: 1.5 MB)"""
        if self.is_folder:
            return '-'

        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def breadcrumb(self):
        """Retorna lista de ancestrais (para navegação)"""
        path = []
        current = self.parent_folder

        while current:
            path.insert(0, current)
            current = current.parent_folder

        return path

    # ============================================
    # METHODS
    # ============================================
    def get_children(self):
        """Retorna arquivos/pastas filhas"""
        return StorageFile.objects.filter(parent_folder=self)

    def delete_recursive(self):
        """Deleta arquivo/pasta e todos os filhos"""
        if self.is_folder:
            for child in self.get_children():
                child.delete_recursive()
        self.delete()