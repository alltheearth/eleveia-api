# apps/storage/serializers.py
from rest_framework import serializers
from .models import StorageFile
from django.conf import settings


class StorageFileSerializer(serializers.ModelSerializer):
    """Serializer para StorageFile"""

    # Campos calculados
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    size_formatted = serializers.CharField(read_only=True)
    full_path = serializers.CharField(read_only=True)
    breadcrumb = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()

    # URL de download (gerada dinamicamente)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = StorageFile
        fields = [
            'id',
            'school',
            'school_name',
            'name',
            'size',
            'size_formatted',
            'mime_type',
            'extension',
            'is_folder',
            'parent_folder',
            'full_path',
            'breadcrumb',
            'children_count',
            'description',
            'tags',
            'is_public',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'download_url',
        ]
        read_only_fields = [
            'id',
            'school',
            'r2_key',
            'r2_bucket',
            'size',
            'mime_type',
            'extension',
            'created_by',
            'created_at',
            'updated_at',
        ]

    def get_created_by_name(self, obj):
        """Nome do usuário que criou"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_breadcrumb(self, obj):
        """Retorna caminho de navegação (breadcrumb)"""
        path = []
        current = obj.parent_folder

        while current:
            path.insert(0, {
                'id': str(current.id),
                'name': current.name,
            })
            current = current.parent_folder

        return path

    def get_children_count(self, obj):
        """Número de arquivos/pastas dentro (se for pasta)"""
        if not obj.is_folder:
            return None
        return obj.get_children().count()

    def get_download_url(self, obj):
        """URL temporária para download (apenas arquivos)"""
        if obj.is_folder:
            return None

        # URL será gerada no endpoint específico
        # Aqui retornamos apenas o endpoint
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                f'/api/v1/storage/{obj.id}/download/'
            )
        return None


class StorageFileUploadSerializer(serializers.Serializer):
    """Serializer para upload de arquivo"""

    file = serializers.FileField(required=True)
    parent_folder_id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    is_public = serializers.BooleanField(required=False, default=False)

    def validate_file(self, value):
        """Valida o arquivo enviado"""
        # Validar tamanho
        if value.size > settings.STORAGE_MAX_FILE_SIZE:
            max_size_mb = settings.STORAGE_MAX_FILE_SIZE / (1024 * 1024)
            raise serializers.ValidationError(
                f'File too large. Maximum size is {max_size_mb}MB.'
            )

        # Validar extensão
        extension = value.name.split('.')[-1].lower()
        if extension not in settings.STORAGE_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'File type not allowed. Allowed: {", ".join(settings.STORAGE_ALLOWED_EXTENSIONS)}'
            )

        return value

    def validate_parent_folder_id(self, value):
        """Valida se a pasta existe"""
        if value:
            try:
                folder = StorageFile.objects.get(id=value, is_folder=True)
                return folder
            except StorageFile.DoesNotExist:
                raise serializers.ValidationError('Parent folder not found.')
        return None


class StorageFolderCreateSerializer(serializers.Serializer):
    """Serializer para criar pasta"""

    name = serializers.CharField(max_length=255, required=True)
    parent_folder_id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        """Valida nome da pasta"""
        # Não permitir caracteres especiais
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_àáâãèéêìíòóôõùúç]+$', value):
            raise serializers.ValidationError(
                'Folder name can only contain letters, numbers, spaces, hyphens and underscores.'
            )
        return value

    def validate_parent_folder_id(self, value):
        """Valida se a pasta pai existe"""
        if value:
            try:
                folder = StorageFile.objects.get(id=value, is_folder=True)
                return folder
            except StorageFile.DoesNotExist:
                raise serializers.ValidationError('Parent folder not found.')
        return None


class StorageFileUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar metadados do arquivo"""

    class Meta:
        model = StorageFile
        fields = ['name', 'description', 'tags', 'is_public']

    def validate_name(self, value):
        """Valida novo nome"""
        if not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')
        return value