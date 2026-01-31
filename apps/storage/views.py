# ===================================================================
# apps/storage/views.py
# ===================================================================
import uuid
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import StreamingHttpResponse
from django.utils.http import http_date
from botocore.exceptions import ClientError

from core.mixins import SchoolIsolationMixin
from core.permissions import IsSchoolStaff, ReadOnlyOrSchoolStaff

from .models import StorageFile
from .serializers import (
    StorageFileSerializer,
    StorageFileUploadSerializer,
    StorageFolderCreateSerializer,
    StorageFileUpdateSerializer,
)
from .services.r2_service import R2Service

logger = logging.getLogger(__name__)


# ===================================================================
# HELPERS
# ===================================================================

def _get_r2(school):
    """Instancia R2Service para a escola."""
    return R2Service(school)


def _extract_extension(filename: str) -> str:
    """Extrai extensão do nome do arquivo (sem ponto, lowercase)."""
    parts = filename.rsplit('.', 1)
    return parts[-1].lower() if len(parts) > 1 else ''


def _collect_r2_keys(folder: StorageFile) -> list[str]:
    """
    Percorre recursivamente uma pasta e coleta todas as chaves R2
    dos arquivos (não-pastas) contidos nela.
    Usado antes de deletar uma pasta para limpar o R2.
    """
    keys = []
    stack = [folder]

    while stack:
        current = stack.pop()
        children = StorageFile.objects.filter(parent_folder=current)

        for child in children:
            if child.is_folder:
                stack.append(child)
            else:
                keys.append(child.r2_key)

    # Se o próprio objeto não for pasta (chamada direta em arquivo)
    if not folder.is_folder and folder.r2_key:
        keys.append(folder.r2_key)

    return keys


# ===================================================================
# VIEWSET
# ===================================================================

class StorageFileViewSet(SchoolIsolationMixin, viewsets.ModelViewSet):
    """
    Gestão de arquivos e pastas no Cloudflare R2.

    Isolamento: usuários veem apenas arquivos da própria escola.
    Permissões: staff da escola pode criar/editar/deletar; end_users só leem.

    Endpoints customizados:
        POST   /upload/                     – Upload de arquivo
        GET    /download/{id}/              – Download (streaming)
        GET    /{id}/presigned-download/    – URL temporária para download direto
        POST   /presigned-upload/           – URL temporária para upload direto pelo frontend
        POST   /folders/                    – Criar pasta
        PATCH  /{id}/move/                  – Mover arquivo/pasta para outra pasta
        POST   /bulk-delete/               – Deletar múltiplos arquivos/pastas
    """

    queryset = StorageFile.objects.select_related('school', 'created_by', 'parent_folder')
    serializer_class = StorageFileSerializer
    permission_classes = [ReadOnlyOrSchoolStaff]
    parser_classes = [MultiPartParser, JSONParser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'tags', 'description']
    ordering_fields = ['name', 'created_at', 'size']
    ordering = ['-created_at']

    # ------------------------------------------------------------------
    # QUERYSET – filtros adicionais via query params
    # ------------------------------------------------------------------

    def get_queryset(self):
        """
        Herda isolamento de escola do SchoolIsolationMixin.
        Adiciona filtros opcionais:
            ?parent_folder=<uuid|null>
            ?is_folder=true|false
            ?tags=<tag>
        """
        qs = super().get_queryset()

        # Filtrar por pasta pai
        parent = self.request.query_params.get('parent_folder')
        if parent is not None:
            if parent.lower() in ('null', ''):
                qs = qs.filter(parent_folder__isnull=True)
            else:
                qs = qs.filter(parent_folder_id=parent)

        # Filtrar por tipo (pasta ou arquivo)
        is_folder = self.request.query_params.get('is_folder')
        if is_folder is not None:
            qs = qs.filter(is_folder=is_folder.lower() in ('true', '1'))

        # Filtrar por tag
        tag = self.request.query_params.get('tags')
        if tag:
            # tags é um campo CSV; busca por substring
            qs = qs.filter(tags__icontains=tag)

        return qs

    # ------------------------------------------------------------------
    # SERIALIZER por action
    # ------------------------------------------------------------------

    def get_serializer_class(self):
        if self.action == 'upload':
            return StorageFileUploadSerializer
        if self.action == 'create_folder':
            return StorageFolderCreateSerializer
        if self.action in ('partial_update', 'update'):
            return StorageFileUpdateSerializer
        return StorageFileSerializer

    # ------------------------------------------------------------------
    # UPLOAD
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='upload', url_name='upload')
    def upload(self, request):
        """
        Upload de arquivo via multipart/form-data.

        Fields:
            file              (required) – arquivo
            parent_folder_id  (optional) – UUID da pasta pai
            description       (optional)
            tags              (optional) – CSV
            is_public         (optional) – bool
        """
        serializer = StorageFileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data['file']
        parent_folder = serializer.validated_data.get('parent_folder_id')  # já é instância ou None
        description = serializer.validated_data.get('description', '')
        tags = serializer.validated_data.get('tags', '')
        is_public = serializer.validated_data.get('is_public', False)

        school = request.user.profile.school

        # Gera chave única no R2
        extension = _extract_extension(file_obj.name)
        r2_key = f"uploads/{uuid.uuid4()}.{extension}" if extension else f"uploads/{uuid.uuid4()}"

        try:
            r2 = _get_r2(school)
            r2.upload_file(
                file_obj=file_obj,
                key=r2_key,
                content_type=file_obj.content_type,
                metadata={
                    'original-name': file_obj.name,
                    'uploaded-by': request.user.username,
                }
            )
        except ClientError as e:
            logger.error("R2 upload failed: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to upload file to storage.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Persiste metadados no PostgreSQL
        storage_file = StorageFile.objects.create(
            school=school,
            name=file_obj.name,
            size=file_obj.size,
            mime_type=file_obj.content_type,
            extension=extension,
            r2_key=r2_key,
            r2_bucket=r2.bucket_name,
            parent_folder=parent_folder,
            is_folder=False,
            is_public=is_public,
            description=description,
            tags=tags,
            created_by=request.user,
        )

        return Response(
            StorageFileSerializer(storage_file, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------------------------------------------------------
    # DOWNLOAD (streaming)
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'], url_path='download', url_name='download')
    def download(self, request, pk=None):
        """
        Baixa o conteúdo do arquivo diretamente via streaming HTTP.
        Útil quando o cliente não pode usar presigned URLs.
        """
        file_obj = self.get_object()  # já aplica permissões + isolamento

        if file_obj.is_folder:
            return Response(
                {'error': 'Cannot download a folder.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            r2 = _get_r2(file_obj.school)
            content = r2.download_file(file_obj.r2_key)
        except ClientError as e:
            logger.error("R2 download failed for key=%s: %s", file_obj.r2_key, e, exc_info=True)
            return Response(
                {'error': 'File not found in storage.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        def content_iterator():
            """Yield em chunks para não carregar tudo na memória de uma vez."""
            chunk_size = 8192
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]

        response = StreamingHttpResponse(
            streaming_content=content_iterator(),
            content_type=file_obj.mime_type or 'application/octet-stream',
        )
        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
        response['Content-Length'] = str(file_obj.size)
        return response

    # ------------------------------------------------------------------
    # PRESIGNED DOWNLOAD URL
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get'], url_path='presigned-download', url_name='presigned-download')
    def presigned_download(self, request, pk=None):
        """
        Retorna uma URL temporária (presigned) para download direto do R2,
        sem passar pelo Django novamente. Expiração padrão: 1 hora.

        Query params:
            expires_in  (opcional) – segundos até expirar (max 604800 = 7 dias)
        """
        file_obj = self.get_object()

        if file_obj.is_folder:
            return Response(
                {'error': 'Cannot generate download URL for a folder.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expires_in = int(request.query_params.get('expires_in', 3600))
        # Limita máximo 7 dias
        expires_in = min(expires_in, 604800)

        try:
            r2 = _get_r2(file_obj.school)
            url = r2.generate_download_url(
                key=file_obj.r2_key,
                expires_in=expires_in,
                filename=file_obj.name,
            )
        except ClientError as e:
            logger.error("Presigned URL generation failed: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to generate download URL.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({
            'url': url,
            'expires_in': expires_in,
            'filename': file_obj.name,
        })

    # ------------------------------------------------------------------
    # PRESIGNED UPLOAD URL (upload direto pelo frontend)
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='presigned-upload', url_name='presigned-upload')
    def presigned_upload(self, request):
        """
        Gera uma URL presigned para o frontend fazer upload diretamente no R2,
        sem passar pelo Django. Após o upload, o frontend deve chamar
        POST /finalize-upload/ com os metadados para criar o registro no banco.

        Body:
            filename      (required)
            content_type  (required)
            parent_folder_id (optional)
            expires_in    (optional, default 3600)
        """
        filename = request.data.get('filename')
        content_type = request.data.get('content_type')

        if not filename or not content_type:
            return Response(
                {'error': 'filename and content_type are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida extensão
        from django.conf import settings
        extension = _extract_extension(filename)
        if extension not in settings.STORAGE_ALLOWED_EXTENSIONS:
            return Response(
                {'error': f'Extension not allowed. Allowed: {settings.STORAGE_ALLOWED_EXTENSIONS}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expires_in = int(request.data.get('expires_in', 3600))
        expires_in = min(expires_in, 3600)  # máximo 1h para upload

        r2_key = f"uploads/{uuid.uuid4()}.{extension}" if extension else f"uploads/{uuid.uuid4()}"
        school = request.user.profile.school

        try:
            r2 = _get_r2(school)
            url = r2.generate_upload_url(
                key=r2_key,
                content_type=content_type,
                expires_in=expires_in,
            )
        except ClientError as e:
            logger.error("Presigned upload URL generation failed: %s", e, exc_info=True)
            return Response(
                {'error': 'Failed to generate upload URL.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({
            'url': url,
            'r2_key': r2_key,
            'r2_bucket': r2.bucket_name,
            'expires_in': expires_in,
        })

    # ------------------------------------------------------------------
    # FINALIZE UPLOAD (após presigned upload pelo frontend)
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='finalize-upload', url_name='finalize-upload')
    def finalize_upload(self, request):
        """
        Após o frontend ter feito upload via presigned URL, esta chamada
        cria o registro de metadados no PostgreSQL.

        Body:
            r2_key           (required)
            r2_bucket        (required)
            filename         (required)
            size             (required)  – tamanho em bytes
            content_type     (required)
            parent_folder_id (optional)
            description      (optional)
            tags             (optional)
            is_public        (optional)
        """
        required = ['r2_key', 'r2_bucket', 'filename', 'size', 'content_type']
        missing = [f for f in required if not request.data.get(f)]
        if missing:
            return Response(
                {'error': f'Missing required fields: {missing}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        school = request.user.profile.school
        r2_key = request.data['r2_key']

        # Segurança: verifica se o arquivo realmente existe no R2 da escola
        try:
            r2 = _get_r2(school)
            if not r2.file_exists(r2_key):
                return Response(
                    {'error': 'File not found in storage. Upload may have failed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ClientError as e:
            logger.error("R2 file_exists check failed: %s", e, exc_info=True)
            return Response(
                {'error': 'Storage verification failed.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Valida parent_folder se fornecido
        parent_folder = None
        parent_id = request.data.get('parent_folder_id')
        if parent_id:
            try:
                parent_folder = StorageFile.objects.get(
                    id=parent_id,
                    school=school,
                    is_folder=True,
                )
            except StorageFile.DoesNotExist:
                return Response(
                    {'error': 'Parent folder not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        filename = request.data['filename']
        extension = _extract_extension(filename)

        storage_file = StorageFile.objects.create(
            school=school,
            name=filename,
            size=int(request.data['size']),
            mime_type=request.data['content_type'],
            extension=extension,
            r2_key=r2_key,
            r2_bucket=request.data['r2_bucket'],
            parent_folder=parent_folder,
            is_folder=False,
            is_public=request.data.get('is_public', False),
            description=request.data.get('description', ''),
            tags=request.data.get('tags', ''),
            created_by=request.user,
        )

        return Response(
            StorageFileSerializer(storage_file, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------------------------------------------------------
    # CRIAR PASTA
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='folders', url_name='create-folder')
    def create_folder(self, request):
        """
        Cria uma pasta virtual (não existe no R2, só no PostgreSQL).

        Body:
            name             (required)
            parent_folder_id (optional) – UUID da pasta pai
            description      (optional)
        """
        serializer = StorageFolderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        school = request.user.profile.school
        parent_folder = serializer.validated_data.get('parent_folder_id')  # instância ou None

        # Previne nome duplicado na mesma pasta pai
        duplicate = StorageFile.objects.filter(
            school=school,
            parent_folder=parent_folder,
            name=serializer.validated_data['name'],
            is_folder=True,
        ).exists()

        if duplicate:
            return Response(
                {'error': 'A folder with this name already exists in this location.'},
                status=status.HTTP_409_CONFLICT
            )

        folder = StorageFile.objects.create(
            school=school,
            name=serializer.validated_data['name'],
            size=0,
            mime_type='application/folder',
            extension='',
            r2_key='',          # pastas não têm chave R2
            r2_bucket='',
            parent_folder=parent_folder,
            is_folder=True,
            description=serializer.validated_data.get('description', ''),
            created_by=request.user,
        )

        return Response(
            StorageFileSerializer(folder, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------------------------------------------------------
    # ATUALIZAR METADADOS (nome, descrição, tags, is_public)
    # ------------------------------------------------------------------

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /{id}/
        Atualiza campos de metadados do arquivo/pasta.
        Campos editáveis: name, description, tags, is_public
        """
        instance = self.get_object()
        serializer = StorageFileUpdateSerializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            StorageFileSerializer(instance, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    # ------------------------------------------------------------------
    # MOVER arquivo/pasta para outra pasta
    # ------------------------------------------------------------------

    @action(detail=True, methods=['patch'], url_path='move', url_name='move')
    def move(self, request, pk=None):
        """
        Move um arquivo ou pasta para uma pasta diferente.

        Body:
            parent_folder_id  – UUID da nova pasta pai (null = raiz)
        """
        instance = self.get_object()
        school = request.user.profile.school

        new_parent_id = request.data.get('parent_folder_id')

        # Permite mover para a raiz (null)
        new_parent = None
        if new_parent_id is not None and str(new_parent_id).lower() not in ('null', ''):
            try:
                new_parent = StorageFile.objects.get(
                    id=new_parent_id,
                    school=school,
                    is_folder=True,
                )
            except StorageFile.DoesNotExist:
                return Response(
                    {'error': 'Target folder not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Previne mover uma pasta dentro de si mesma ou de um descendente
            if instance.is_folder:
                # Percorre ancestrais do destino
                current = new_parent
                while current:
                    if current.id == instance.id:
                        return Response(
                            {'error': 'Cannot move a folder inside itself or its descendants.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    current = current.parent_folder

        instance.parent_folder = new_parent
        instance.save()

        return Response(
            StorageFileSerializer(instance, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    # ------------------------------------------------------------------
    # DELETE – sobrescreve o padrão para limpar R2
    # ------------------------------------------------------------------

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /{id}/
        Remove arquivo ou pasta. Para pastas, deleta recursivamente
        todos os filhos e limpa os arquivos correspondentes no R2.
        """
        instance = self.get_object()
        school = instance.school

        # Coleta todas as chaves R2 a deletar
        r2_keys = _collect_r2_keys(instance)

        # Remove do R2 (se houver chaves)
        if r2_keys:
            try:
                r2 = _get_r2(school)
                r2.delete_multiple_files(r2_keys)
            except ClientError as e:
                logger.error("R2 bulk delete failed: %s", e, exc_info=True)
                return Response(
                    {'error': 'Failed to delete files from storage. Database records were NOT removed.'},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        # Remove do banco (CASCADE cuida dos filhos da pasta)
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # BULK DELETE
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='bulk-delete', url_name='bulk-delete')
    def bulk_delete(self, request):
        """
        Deleta múltiplos arquivos/pastas de uma vez.

        Body:
            ids  (required) – lista de UUIDs
        """
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response(
                {'error': 'ids must be a non-empty list of UUIDs.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        school = request.user.profile.school

        # Filtra apenas itens da escola do usuário
        instances = StorageFile.objects.filter(
            id__in=ids,
            school=school,
        )

        if not instances.exists():
            return Response(
                {'error': 'No matching files found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Coleta todas as chaves R2 (inclui recursivo para pastas)
        all_r2_keys = []
        for item in instances:
            all_r2_keys.extend(_collect_r2_keys(item))

        # Remove do R2
        if all_r2_keys:
            try:
                r2 = _get_r2(school)
                r2.delete_multiple_files(all_r2_keys)
            except ClientError as e:
                logger.error("R2 bulk delete failed: %s", e, exc_info=True)
                return Response(
                    {'error': 'Failed to delete files from storage.'},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        # Remove do banco
        deleted_count, _ = instances.delete()

        return Response({
            'deleted': deleted_count,
            'r2_files_removed': len(all_r2_keys),
        }, status=status.HTTP_200_OK)