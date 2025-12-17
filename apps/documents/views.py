from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


# Imports dos models
from .models import (

    Documento
)

# Imports dos serializers
from .serializers import (
 DocumentoSerializer,
)

class DocumentoViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Documentos
    Gestor e Operador podem CRUD completo
    """
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = [GestorOuOperadorPermission]

    @action(detail=False, methods=['get'])
    def nao_processados(self, request):
        """Documentos pendentes ou com erro"""
        queryset = self.get_queryset().filter(status__in=['pendente', 'erro'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
