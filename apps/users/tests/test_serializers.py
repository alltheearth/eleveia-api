"""apps/users/tests/test_serializers.py"""
import pytest
from django.test import TestCase
from apps.users.serializers import RegistroSerializer, LoginSerializer
from .factories import UserFactory, EscolaFactory


class TestRegistroSerializer(TestCase):
    """Testes para RegistroSerializer"""

    def setUp(self):
        """Setup"""
        self.escola = EscolaFactory()

    def test_validacao_senhas_diferentes(self):
        """Testa validação de senhas diferentes"""
        data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'senha123',
            'password2': 'senha456',
            'escola_id': self.escola.id,
            'tipo_perfil': 'operador'
        }

        serializer = RegistroSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_validacao_username_duplicado(self):
        """Testa validação de username duplicado"""
        user = UserFactory(username='existing')

        data = {
            'username': 'existing',
            'email': 'new@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'escola_id': self.escola.id,
            'tipo_perfil': 'operador'
        }

        serializer = RegistroSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'username' in serializer.errors
