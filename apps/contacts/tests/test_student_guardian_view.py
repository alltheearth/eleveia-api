# apps/contacts/tests/test_student_guardian_view.py

from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class StudentGuardianViewTestCase(TestCase):

    def setUp(self):
        # Setup inicial
        pass

    @patch('contacts.services.siga_integration_service.SigaIntegrationService.fetch_all_data')
    def test_get_guardians_success(self, mock_fetch):
        """Testa busca bem-sucedida de responsáveis."""
        # Mock da resposta
        mock_fetch.return_value = {
            'guardians': [...],
            'students_relations': [...],
            'students_academic': [...]
        }

        # Request
        response = self.client.get('/api/v1/contacts/students/guardians/')

        # Asserts
        self.assertEqual(response.status_code, 200)
        self.assertIn('guardians', response.data)