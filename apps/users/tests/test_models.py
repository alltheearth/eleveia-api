"""apps/users/tests/test_models.py"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from apps.users.models import PerfilUsuario
from .factories import UserFactory, PerfilUsuarioFactory, EscolaFactory


class TestPerfilUsuarioModel(TestCase):
    """Testes para modelo PerfilUsuario"""

    def setUp(self):
        """Setup para cada teste"""
        self.escola = EscolaFactory()
        self.user = UserFactory()

    def test_create_perfil_operador(self):
        """Testa criação de perfil operador"""
        perfil = PerfilUsuario.objects.create(
            usuario=self.user,
            escola=self.escola,
            tipo='operador'
        )

        assert perfil.is_operador() is True
        assert perfil.is_gestor() is False
        assert perfil.ativo is True

    def test_create_perfil_gestor(self):
        """Testa criação de perfil gestor"""
        perfil = PerfilUsuario.objects.create(
            usuario=self.user,
            escola=self.escola,
            tipo='gestor'
        )

        assert perfil.is_gestor() is True
        assert perfil.is_operador() is False

    def test_perfil_str_method(self):
        """Testa método __str__"""
        perfil = PerfilUsuarioFactory(
            usuario=self.user,
            escola=self.escola,
            tipo='gestor'
        )

        expected = f"{self.user.username} - Gestor da Escola ({self.escola.nome_escola})"
        assert str(perfil) == expected

    def test_perfil_one_to_one_with_user(self):
        """Testa relacionamento OneToOne com User"""
        perfil = PerfilUsuarioFactory(usuario=self.user)

        assert hasattr(self.user, 'perfil')
        assert self.user.perfil == perfil
