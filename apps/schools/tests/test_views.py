# apps/contacts/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.tests.factories import UserFactory, PerfilUsuarioFactory, EscolaFactory
from .factories import ContatoFactory


class TestContatoViewSet(APITestCase):
    """Testes para ContatoViewSet"""

    def setUp(self):
        """Setup para cada teste"""
        self.escola = EscolaFactory()
        self.perfil = PerfilUsuarioFactory(escola=self.escola, tipo='gestor')
        self.user = self.perfil.usuario
        self.client.force_authenticate(user=self.user)

        self.url_list = reverse('contato-list')

    def test_listar_contatos_sucesso(self):
        """Testa listagem de contatos"""
        # Criar contatos da escola do usuário
        ContatoFactory.create_batch(5, escola=self.escola)

        # Criar contatos de outra escola (não devem aparecer)
        outra_escola = EscolaFactory()
        ContatoFactory.create_batch(3, escola=outra_escola)

        response = self.client.get(self.url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5  # Apenas contatos da sua escola

    def test_criar_contato_sucesso(self):
        """Testa criação de contato"""
        data = {
            'nome': 'João Silva',
            'email': 'joao@example.com',
            'telefone': '11999999999',
            'status': 'ativo',
            'origem': 'whatsapp',
        }

        response = self.client.post(self.url_list, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nome'] == 'João Silva'
        assert response.data['escola'] == self.escola.id

    def test_registrar_interacao(self):
        """Testa registro de interação"""
        contato = ContatoFactory(escola=self.escola)
        url = reverse('contato-registrar-interacao', args=[contato.id])

        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK

        contato.refresh_from_db()
        assert contato.ultima_interacao is not None

    def test_usuario_sem_perfil_nao_acessa(self):
        """Testa que usuário sem perfil não tem acesso"""
        user_sem_perfil = UserFactory()
        self.client.force_authenticate(user=user_sem_perfil)

        response = self.client.get(self.url_list)

        assert response.status_code == status.HTTP_403_FORBIDDEN