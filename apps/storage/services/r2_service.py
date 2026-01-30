# services/r2_service.py
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from typing import BinaryIO, Optional
import logging

logger = logging.getLogger(__name__)


class R2Service:
    """
    Serviço para interagir com Cloudflare R2 (S3-compatible).

    Cada escola tem seu próprio bucket isolado.
    """

    def __init__(self, school):
        """
        Inicializa serviço R2 para uma escola específica.

        Args:
            school: Instância do modelo School
        """
        self.school = school
        self.bucket_name = f"{settings.R2_BUCKET_PREFIX}-{school.id}"

        # Cliente S3-compatible para R2
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            ),
        )

        # Garantir que bucket existe
        self._ensure_bucket_exists()

    # ============================================
    # BUCKET MANAGEMENT
    # ============================================

    def _ensure_bucket_exists(self):
        """Cria bucket se não existir"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ Bucket exists: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == '404':
                # Bucket não existe, criar
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"✅ Bucket created: {self.bucket_name}")

                    # Configurar CORS (opcional, mas recomendado)
                    self._configure_cors()

                except ClientError as create_error:
                    logger.error(f"❌ Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"❌ Error checking bucket: {e}")
                raise

    def _configure_cors(self):
        """Configura CORS para o bucket (permite frontend acessar)"""
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': ['*'],  # Em prod, especifique seu domínio
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }

        try:
            self.client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            logger.info(f"✅ CORS configured for {self.bucket_name}")
        except ClientError as e:
            logger.warning(f"⚠️ Failed to configure CORS: {e}")

    # ============================================
    # FILE OPERATIONS
    # ============================================

    def upload_file(
            self,
            file_obj: BinaryIO,
            key: str,
            content_type: str,
            metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload arquivo para R2.

        Args:
            file_obj: Objeto de arquivo (Django UploadedFile ou file-like)
            key: Caminho no bucket (ex: docs/2024/file.pdf)
            content_type: MIME type (ex: application/pdf)
            metadata: Metadados extras (opcional)

        Returns:
            dict com informações do upload

        Raises:
            ClientError: Se upload falhar
        """
        try:
            # Metadados padrão
            upload_metadata = {
                'school-id': str(self.school.id),
                'school-name': self.school.school_name,
            }

            # Adicionar metadados customizados
            if metadata:
                upload_metadata.update(metadata)

            # Upload
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_obj,
                ContentType=content_type,
                Metadata=upload_metadata
            )

            logger.info(f"✅ File uploaded: {key} to {self.bucket_name}")

            return {
                'bucket': self.bucket_name,
                'key': key,
                'url': f"{settings.R2_ENDPOINT_URL}/{self.bucket_name}/{key}"
            }

        except ClientError as e:
            logger.error(f"❌ Upload failed: {e}")
            raise

    def download_file(self, key: str) -> bytes:
        """
        Baixa arquivo do R2.

        Args:
            key: Caminho do arquivo no bucket

        Returns:
            bytes: Conteúdo do arquivo
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            return response['Body'].read()

        except ClientError as e:
            logger.error(f"❌ Download failed: {e}")
            raise

    def delete_file(self, key: str):
        """
        Deleta arquivo do R2.

        Args:
            key: Caminho do arquivo no bucket
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.info(f"✅ File deleted: {key} from {self.bucket_name}")

        except ClientError as e:
            logger.error(f"❌ Delete failed: {e}")
            raise

    def file_exists(self, key: str) -> bool:
        """
        Verifica se arquivo existe no R2.

        Args:
            key: Caminho do arquivo

        Returns:
            bool: True se existe
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False

    # ============================================
    # PRESIGNED URLs (Temporárias)
    # ============================================

    def generate_download_url(
            self,
            key: str,
            expires_in: int = 3600,
            filename: Optional[str] = None
    ) -> str:
        """
        Gera URL temporária para download direto (sem passar pelo Django).

        Args:
            key: Caminho do arquivo
            expires_in: Tempo de expiração em segundos (default: 1 hora)
            filename: Nome do arquivo para download (opcional)

        Returns:
            str: URL assinada temporária
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': key
            }

            # Se especificar filename, força download com esse nome
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

            url = self.client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )

            return url

        except ClientError as e:
            logger.error(f"❌ Failed to generate URL: {e}")
            raise

    def generate_upload_url(
            self,
            key: str,
            content_type: str,
            expires_in: int = 3600
    ) -> str:
        """
        Gera URL temporária para upload direto do frontend (sem passar pelo Django).

        Args:
            key: Caminho onde arquivo será salvo
            content_type: MIME type
            expires_in: Tempo de expiração em segundos

        Returns:
            str: URL assinada para PUT
        """
        try:
            url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )

            return url

        except ClientError as e:
            logger.error(f"❌ Failed to generate upload URL: {e}")
            raise

    # ============================================
    # LIST FILES (Use com cuidado - prefira PostgreSQL)
    # ============================================

    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        Lista arquivos no R2 (use apenas para debug/admin).

        Para uso normal, consulte o PostgreSQL (StorageFile model).

        Args:
            prefix: Prefixo para filtrar (ex: docs/)
            max_keys: Número máximo de resultados

        Returns:
            list: Lista de objetos
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            return response.get('Contents', [])

        except ClientError as e:
            logger.error(f"❌ List failed: {e}")
            raise

    # ============================================
    # BULK OPERATIONS
    # ============================================

    def delete_multiple_files(self, keys: list):
        """
        Deleta múltiplos arquivos de uma vez.

        Args:
            keys: Lista de chaves (paths) para deletar
        """
        if not keys:
            return

        try:
            objects = [{'Key': key} for key in keys]

            self.client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )

            logger.info(f"✅ {len(keys)} files deleted from {self.bucket_name}")

        except ClientError as e:
            logger.error(f"❌ Bulk delete failed: {e}")
            raise