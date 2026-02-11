from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

User = get_user_model()


class StudentGuardianViewTestCase(TestCase):
    """Testes para StudentGuardianView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Mock data
        self.mock_guardians = [
            {
                'id': 1,
                'nome': 'Maria Silva',
                'cpf': '123.456.789-00',
                'email': 'maria@email.com',
                'celular': '(11) 99999-8888',
                'fone': '(11) 3333-4444',
                'cep': '01234-567',
                'logradouro': 'Rua das Flores',
                'bairro': 'Jardim',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'complemento': 'Apto 45',
                'filhos': [
                    {
                        'id': 1,
                        'nome': 'João Silva',
                        'turma': '3º A',
                        'serie': '3º Ano',
                        'periodo': 'manha',
                        'status': 'ativo'
                    }
                ],
                'documentos': [],
                'parentesco': 'mae',
                'parentesco_display': 'Mãe',
                'responsavel_financeiro': True,
                'responsavel_pedagogico': True,
                'endereco': {
                    'cep': '01234-567',
                    'logradouro': 'Rua das Flores',
                    'numero': None,
                    'complemento': 'Apto 45',
                    'bairro': 'Jardim',
                    'cidade': 'São Paulo',
                    'uf': 'SP',
                }
            }
        ]

    @patch('contacts.services.siga_integration_service.SigaIntegrationService.get_all_guardians_enriched')
    def test_list_guardians_success(self, mock_get_guardians):
        """Testa listagem bem-sucedida de responsáveis."""
        mock_get_guardians.return_value = self.mock_guardians

        response = self.client.get('/api/v1/contacts/guardians/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Maria Silva')

    def test_list_guardians_unauthenticated(self):
        """Testa acesso sem autenticação."""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/v1/contacts/guardians/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('contacts.services.siga_integration_service.SigaIntegrationService.get_all_guardians_enriched')
    def test_list_guardians_api_error(self, mock_get_guardians):
        """Testa tratamento de erro da API externa."""
        mock_get_guardians.side_effect = Exception('API Error')

        response = self.client.get('/api/v1/contacts/guardians/')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)