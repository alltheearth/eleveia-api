from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Escola
from .serializers import EscolaSerializer
from core.permissions import EscolaPermission

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class EscolaViewSet(viewsets.ModelViewSet):

    @method_decorator(cache_page(60 * 15))  # Cache por 15 minutos
    def list(self, request, *args, **kwargs):
        """Lista escolas com cache"""
        return super().list(request, *args, **kwargs)

    def perform_update(self, serializer):
        """Limpar cache ao atualizar"""
        from django.core.cache import cache
        cache.delete_pattern('views.decorators.cache.*escola*')
        super().perform_update(serializer)