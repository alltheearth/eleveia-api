# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import StorageFile
from .serializers import StorageFileSerializer
from services.r2_service import R2Service


class StorageFileViewSet(viewsets.ModelViewSet):
    serializer_class = StorageFileSerializer
    parser_classes = [MultiPartParser]

    def get_queryset(self):
        # Isolamento por escola
        return StorageFile.objects.filter(
            school=self.request.user.profile.school
        )

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload de arquivo"""
        file_obj = request.FILES['file']
        parent_folder_id = request.data.get('parent_folder_id')

        school = request.user.profile.school
        r2_service = R2Service(school)

        # Gerar key único
        import uuid
        file_extension = file_obj.name.split('.')[-1]
        r2_key = f"{uuid.uuid4()}.{file_extension}"

        # Upload para R2
        r2_service.upload_file(file_obj, r2_key, file_obj.content_type)

        # Salvar metadados no PostgreSQL
        storage_file = StorageFile.objects.create(
            school=school,
            name=file_obj.name,
            size=file_obj.size,
            mime_type=file_obj.content_type,
            r2_key=r2_key,
            r2_bucket=r2_service.bucket_name,
            parent_folder_id=parent_folder_id,
            created_by=request.user,
        )

        return Response(
            StorageFileSerializer(storage_file).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def download_url(self, request, pk=None):
        """Gera URL temporária para download"""
        file = self.get_object()

        r2_service = R2Service(file.school)
        url = r2_service.generate_download_url(file.r2_key)

        return Response({'url': url})