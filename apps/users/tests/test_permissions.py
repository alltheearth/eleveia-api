"""apps/users/tests/test_permissions.py"""
import pytest
from django.test import TestCase, RequestFactory
from core.permissions import GestorOuOperadorPermission
from .factories import UserFactory, PerfilUsuarioFactory, GestorFactory


class TestGestorOuOperadorPermission(TestCase):
    """Testes para GestorOuOperadorPermission"""

    def setUp(self):
        """Setup"""
        self.factory = RequestFactory()
        self.permission = GestorOuOperadorPermission()

    def test_superuser_tem_permissao(self):
        """Testa que superuser tem permissão"""
        user = UserFactory(is_superuser=True)
        request = self.factory.get('/')
        request.user = user

        assert self.permission.has_permission(request, None) is True

    def test_gestor_tem_permissao(self):
        """Testa que gestor tem permissão"""
        perfil = GestorFactory()
        request = self.factory.get('/')
        request.user = perfil.usuario

        assert self.permission.has_permission(request, None) is True

    def test_operador_tem_permissao(self):
        """Testa que operador tem permissão"""
        perfil = PerfilUsuarioFactory(tipo='operador')
        request = self.factory.get('/')
        request.user = perfil.usuario

        assert self.permission.has_permission(request, None) is True

    def test_usuario_sem_perfil_nao_tem_permissao(self):
        """Testa que usuário sem perfil não tem permissão"""
        user = UserFactory()
        request = self.factory.get('/')
        request.user = user

        assert self.permission.has_permission(request, None) is False