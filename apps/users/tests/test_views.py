"""apps/users/tests/test_views.py"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .factories import UserFactory, EscolaFactory, PerfilUsuarioFactory


class TestRegistroView(APITestCase):
    """Testes para view de registro"""

    def setUp(self):
        """Setup"""
        self.url = reverse('registro')
        self.escola = EscolaFactory()

    def test_registro_sucesso_operador(self):
        """Testa registro bem-sucedido de operador"""
        data = {
            'username': 'novouser',
            'email': 'novo@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'escola_id': self.escola.id,
            'tipo_perfil': 'operador'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user' in response.data

    def test_registro_senhas_diferentes(self):
        """Testa registro com senhas diferentes"""
        data = {
            'username': 'novouser',
            'email': 'novo@test.com',
            'password': 'senha123',
            'password2': 'senha456',
            'escola_id': self.escola.id,
            'tipo_perfil': 'operador'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_registro_sem_escola(self):
        """Testa registro sem escola (deve falhar)"""
        data = {
            'username': 'novouser',
            'email': 'novo@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'tipo_perfil': 'operador'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'escola_id' in response.data


class TestLoginView(APITestCase):
    """Testes para view de login"""

    def setUp(self):
        """Setup"""
        self.url = reverse('login')
        self.user = UserFactory(password='test123')

    def test_login_sucesso(self):
        """Testa login bem-sucedido"""
        data = {
            'username': self.user.username,
            'password': 'test123'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert response.data['user']['username'] == self.user.username

    def test_login_senha_incorreta(self):
        """Testa login com senha incorreta"""
        data = {
            'username': self.user.username,
            'password': 'senhaerrada'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_usuario_inexistente(self):
        """Testa login com usuário inexistente"""
        data = {
            'username': 'naoexiste',
            'password': 'qualquer'
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST