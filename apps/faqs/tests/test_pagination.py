# ===================================================================
# apps/faqs/tests/test_pagination.py
# ===================================================================
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.tests.factories import UserFactory, PerfilUsuarioFactory, EscolaFactory
from apps.faqs.models import FAQ


class TestFAQPagination(TestCase):
    """Testes para paginação customizada de FAQs"""

    def setUp(self):
        """Setup para testes"""
        self.client = APIClient()

        # Criar escola e usuário autenticado
        self.escola = EscolaFactory()
        self.perfil = PerfilUsuarioFactory(escola=self.escola, tipo='gestor')
        self.user = self.perfil.usuario

        # Autenticar
        self.client.force_authenticate(user=self.user)

        # Criar 30 FAQs para testar paginação
        for i in range(30):
            FAQ.objects.create(
                school=self.escola,
                question=f'Pergunta {i + 1}',
                answer=f'Resposta {i + 1}',
                category='Teste',
                status='active',
                created_by=self.user
            )

    def test_pagination_default_20_items(self):
        """Testa paginação padrão com 20 itens"""
        response = self.client.get('/api/v1/faqs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['count'], 30)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_pagination_15_items(self):
        """Testa paginação com 15 itens"""
        response = self.client.get('/api/v1/faqs/?page_size=15')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 15)
        self.assertEqual(response.data['count'], 30)

    def test_pagination_25_items(self):
        """Testa paginação com 25 itens"""
        response = self.client.get('/api/v1/faqs/?page_size=25')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 25)

    def test_pagination_invalid_value_uses_default(self):
        """Testa que valores inválidos usam o padrão"""
        response = self.client.get('/api/v1/faqs/?page_size=100')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Deve retornar 20 (padrão) ao invés de 100
        self.assertEqual(len(response.data['results']), 20)

    def test_pagination_page_2(self):
        """Testa navegação para página 2"""
        response = self.client.get('/api/v1/faqs/?page=2&page_size=15')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 15)
        self.assertIsNotNone(response.data['previous'])

    def test_pagination_last_page_partial(self):
        """Testa última página com itens parciais"""
        response = self.client.get('/api/v1/faqs/?page=2&page_size=25')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Página 1: 25 itens, Página 2: 5 itens restantes
        self.assertEqual(len(response.data['results']), 5)

    def test_pagination_does_not_affect_other_endpoints(self):
        """Verifica que paginação não afeta outros endpoints"""
        # Este teste assumiria que outros endpoints usam paginação diferente
        # Por exemplo, contatos com paginação padrão do settings (250)
        pass