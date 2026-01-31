# ===================================================================
# apps/storage/tests/test_views.py
# ===================================================================
import uuid
from unittest.mock import patch, MagicMock, PropertyMock
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.storage.models import StorageFile
from .factories import (
    SchoolFactory,
    UserProfileFactory,
    StorageFileFactory,
    StorageFolderFactory,
)

# Caminho para mock do R2Service usado nas views
R2_MOCK = 'apps.storage.views.R2Service'


def _make_r2_mock():
    """Retorna um MagicMock pré-configurado que simula R2Service."""
    mock = MagicMock()
    mock.bucket_name = 'test-bucket'
    mock.upload_file.return_value = {'bucket': 'test-bucket', 'key': 'uploads/x.pdf'}
    mock.download_file.return_value = b'fake file content here'
    mock.generate_download_url.return_value = 'https://r2.example.com/signed-download'
    mock.generate_upload_url.return_value = 'https://r2.example.com/signed-upload'
    mock.file_exists.return_value = True
    mock.delete_file.return_value = None
    mock.delete_multiple_files.return_value = None
    return mock


# ===================================================================
# BASE – setup compartilhado
# ===================================================================

class StorageBaseTestCase(APITestCase):
    """Setup comum: escola, usuários com perfis, autenticação."""

    def setUp(self):
        # Escola principal
        self.school = SchoolFactory()

        # Manager da escola
        self.manager_profile = UserProfileFactory(
            school=self.school, manager=True
        )
        self.manager = self.manager_profile.user

        # Operator da escola
        self.operator_profile = UserProfileFactory(
            school=self.school, role='operator'
        )
        self.operator = self.operator_profile.user

        # End user da escola
        self.enduser_profile = UserProfileFactory(
            school=self.school, end_user=True
        )
        self.enduser = self.enduser_profile.user

        # Escola B (isolamento)
        self.school_b = SchoolFactory()
        self.manager_b_profile = UserProfileFactory(
            school=self.school_b, manager=True
        )
        self.manager_b = self.manager_b_profile.user

        # URLs base
        self.base_url = '/api/v1/storage/'

    def _auth(self, user):
        self.client.force_authenticate(user=user)


# ===================================================================
# UPLOAD
# ===================================================================

@patch(R2_MOCK)
class TestUpload(StorageBaseTestCase):

    def _make_file(self, name='test.pdf', content=b'%PDF-fake', content_type='application/pdf'):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def test_upload_sucesso_manager(self, MockR2):
        """Manager faz upload com sucesso."""
        MockR2.return_value = _make_r2_mock()
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}upload/',
            {'file': self._make_file()},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'test.pdf')
        self.assertEqual(response.data['school'], self.school.id)
        self.assertTrue(StorageFile.objects.filter(school=self.school, name='test.pdf').exists())

    def test_upload_sucesso_operator(self, MockR2):
        """Operator também pode fazer upload (é school staff)."""
        MockR2.return_value = _make_r2_mock()
        self._auth(self.operator)

        response = self.client.post(
            f'{self.base_url}upload/',
            {'file': self._make_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_enduser_proibido(self, MockR2):
        """End user não pode fazer upload."""
        self._auth(self.enduser)

        response = self.client.post(
            f'{self.base_url}upload/',
            {'file': self._make_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_sem_arquivo(self, MockR2):
        """Upload sem arquivo retorna 400."""
        self._auth(self.manager)

        response = self.client.post(f'{self.base_url}upload/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_extensao_nao_permitida(self, MockR2):
        """Extensão não permitida retorna 400."""
        self._auth(self.manager)
        bad_file = self._make_file(name='virus.exe', content=b'\x00', content_type='application/exe')

        response = self.client.post(
            f'{self.base_url}upload/',
            {'file': bad_file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_r2_falha_retorna_502(self, MockR2):
        """Falha no R2 retorna 502."""
        from botocore.exceptions import ClientError
        mock_r2 = _make_r2_mock()
        mock_r2.upload_file.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Internal'}}, 'PutObject'
        )
        MockR2.return_value = mock_r2
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}upload/',
            {'file': self._make_file()},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        # Nada deve ter sido criado no banco
        self.assertFalse(StorageFile.objects.filter(school=self.school).exists())

    def test_upload_com_pasta_pai(self, MockR2):
        """Upload dentro de uma pasta existente."""
        MockR2.return_value = _make_r2_mock()
        pasta = StorageFolderFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}upload/',
            {
                'file': self._make_file(),
                'parent_folder_id': str(pasta.id),
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        arquivo = StorageFile.objects.get(school=self.school, name='test.pdf')
        self.assertEqual(arquivo.parent_folder, pasta)


# ===================================================================
# DOWNLOAD
# ===================================================================

@patch(R2_MOCK)
class TestDownload(StorageBaseTestCase):

    def _create_file(self):
        return StorageFileFactory(school=self.school, name='doc.pdf')

    def test_download_streaming_sucesso(self, MockR2):
        """Download retorna streaming com content-disposition."""
        MockR2.return_value = _make_r2_mock()
        arquivo = self._create_file()
        self._auth(self.manager)

        response = self.client.get(f'{self.base_url}{arquivo.id}/download/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
        self.assertIn('doc.pdf', response.get('Content-Disposition', ''))

    def test_download_pasta_retorna_400(self, MockR2):
        """Não é possível baixar uma pasta."""
        pasta = StorageFolderFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.get(f'{self.base_url}{pasta.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_download_escola_outro_retorna_404(self, MockR2):
        """Arquivo de outra escola não é encontrado."""
        arquivo_b = StorageFileFactory(school=self.school_b)
        self._auth(self.manager)  # manager da escola A

        response = self.client.get(f'{self.base_url}{arquivo_b.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_r2_falha_retorna_502(self, MockR2):
        """Falha no R2 durante download retorna 502."""
        from botocore.exceptions import ClientError
        mock_r2 = _make_r2_mock()
        mock_r2.download_file.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}}, 'GetObject'
        )
        MockR2.return_value = mock_r2

        arquivo = self._create_file()
        self._auth(self.manager)

        response = self.client.get(f'{self.base_url}{arquivo.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


# ===================================================================
# PRESIGNED URLs
# ===================================================================

@patch(R2_MOCK)
class TestPresignedUrls(StorageBaseTestCase):

    def test_presigned_download_sucesso(self, MockR2):
        MockR2.return_value = _make_r2_mock()
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.get(f'{self.base_url}{arquivo.id}/presigned-download/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('url', response.data)
        self.assertIn('expires_in', response.data)

    def test_presigned_download_pasta_retorna_400(self, MockR2):
        pasta = StorageFolderFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.get(f'{self.base_url}{pasta.id}/presigned-download/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_presigned_upload_sucesso(self, MockR2):
        MockR2.return_value = _make_r2_mock()
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}presigned-upload/',
            {'filename': 'report.pdf', 'content_type': 'application/pdf'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('url', response.data)
        self.assertIn('r2_key', response.data)

    def test_presigned_upload_extensao_invalida(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}presigned-upload/',
            {'filename': 'hack.bat', 'content_type': 'application/bat'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_presigned_upload_sem_campos_obrigatorios(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}presigned-upload/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ===================================================================
# FINALIZE UPLOAD
# ===================================================================

@patch(R2_MOCK)
class TestFinalizeUpload(StorageBaseTestCase):

    def _payload(self, **overrides):
        base = {
            'r2_key': f'uploads/{uuid.uuid4()}.pdf',
            'r2_bucket': 'test-bucket',
            'filename': 'report.pdf',
            'size': 2048,
            'content_type': 'application/pdf',
        }
        base.update(overrides)
        return base

    def test_finalize_sucesso(self, MockR2):
        MockR2.return_value = _make_r2_mock()
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}finalize-upload/',
            self._payload(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'report.pdf')

    def test_finalize_arquivo_nao_existe_no_r2(self, MockR2):
        mock_r2 = _make_r2_mock()
        mock_r2.file_exists.return_value = False
        MockR2.return_value = mock_r2
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}finalize-upload/',
            self._payload(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not found in storage', response.data['error'])

    def test_finalize_campos_faltantes(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}finalize-upload/',
            {'r2_key': 'x'},  # faltam campos
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finalize_pasta_pai_invalida(self, MockR2):
        MockR2.return_value = _make_r2_mock()
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}finalize-upload/',
            self._payload(parent_folder_id=str(uuid.uuid4())),  # não existe
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Parent folder not found', response.data['error'])


# ===================================================================
# PASTAS
# ===================================================================

@patch(R2_MOCK)
class TestFolders(StorageBaseTestCase):

    def test_criar_pasta_sucesso(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}folders/',
            {'name': 'Documentos'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_folder'])
        self.assertEqual(response.data['name'], 'Documentos')

    def test_criar_pasta_nome_duplicado(self, MockR2):
        StorageFolderFactory(school=self.school, name='Duplicado', parent_folder=None)
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}folders/',
            {'name': 'Duplicado'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_criar_pasta_dentro_de_outra(self, MockR2):
        pai = StorageFolderFactory(school=self.school, name='Pai')
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}folders/',
            {'name': 'Filho', 'parent_folder_id': str(pai.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        filho = StorageFile.objects.get(id=response.data['id'])
        self.assertEqual(filho.parent_folder, pai)

    def test_criar_pasta_enduser_proibido(self, MockR2):
        self._auth(self.enduser)

        response = self.client.post(
            f'{self.base_url}folders/',
            {'name': 'Tentativa'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_criar_pasta_nome_caractere_especial(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}folders/',
            {'name': '../../etc/passwd'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ===================================================================
# ATUALIZAR METADADOS
# ===================================================================

@patch(R2_MOCK)
class TestUpdate(StorageBaseTestCase):

    def test_atualizar_nome_sucesso(self, MockR2):
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/',
            {'name': 'novo_nome.pdf'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        arquivo.refresh_from_db()
        self.assertEqual(arquivo.name, 'novo_nome.pdf')

    def test_atualizar_tags_e_descricao(self, MockR2):
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/',
            {'tags': 'financeiro,2024', 'description': 'Relatório anual'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        arquivo.refresh_from_db()
        self.assertEqual(arquivo.tags, 'financeiro,2024')
        self.assertEqual(arquivo.description, 'Relatório anual')

    def test_atualizar_enduser_proibido(self, MockR2):
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.enduser)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/',
            {'name': 'hack.pdf'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ===================================================================
# MOVER
# ===================================================================

@patch(R2_MOCK)
class TestMove(StorageBaseTestCase):

    def test_mover_arquivo_para_pasta(self, MockR2):
        arquivo = StorageFileFactory(school=self.school, parent_folder=None)
        pasta = StorageFolderFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/move/',
            {'parent_folder_id': str(pasta.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        arquivo.refresh_from_db()
        self.assertEqual(arquivo.parent_folder, pasta)

    def test_mover_arquivo_para_raiz(self, MockR2):
        pasta = StorageFolderFactory(school=self.school)
        arquivo = StorageFileFactory(school=self.school, parent_folder=pasta)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/move/',
            {'parent_folder_id': None},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        arquivo.refresh_from_db()
        self.assertIsNone(arquivo.parent_folder)

    def test_mover_pasta_dentro_de_si_mesma(self, MockR2):
        """Deve retornar erro — moveria para dentro de si."""
        pasta = StorageFolderFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{pasta.id}/move/',
            {'parent_folder_id': str(pasta.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mover_pasta_dentro_de_descendente(self, MockR2):
        """Ciclo: pai → filho → pai (impossível)."""
        pai = StorageFolderFactory(school=self.school)
        filho = StorageFolderFactory(school=self.school, parent_folder=pai)
        self._auth(self.manager)

        # Tenta mover 'pai' dentro de 'filho'
        response = self.client.patch(
            f'{self.base_url}{pai.id}/move/',
            {'parent_folder_id': str(filho.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mover_para_pasta_inexistente(self, MockR2):
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.patch(
            f'{self.base_url}{arquivo.id}/move/',
            {'parent_folder_id': str(uuid.uuid4())},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ===================================================================
# DELETE (individual)
# ===================================================================

@patch(R2_MOCK)
class TestDelete(StorageBaseTestCase):

    def test_deletar_arquivo_sucesso(self, MockR2):
        MockR2.return_value = _make_r2_mock()
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.delete(f'{self.base_url}{arquivo.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StorageFile.objects.filter(id=arquivo.id).exists())

    def test_deletar_pasta_recursiva(self, MockR2):
        """Deletar pasta deve remover todos os filhos e limpar R2."""
        MockR2.return_value = _make_r2_mock()

        pasta = StorageFolderFactory(school=self.school)
        sub_pasta = StorageFolderFactory(school=self.school, parent_folder=pasta)
        arquivo1 = StorageFileFactory(school=self.school, parent_folder=pasta)
        arquivo2 = StorageFileFactory(school=self.school, parent_folder=sub_pasta)

        self._auth(self.manager)
        response = self.client.delete(f'{self.base_url}{pasta.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Tudo deve estar deletado
        self.assertFalse(StorageFile.objects.filter(id__in=[pasta.id, sub_pasta.id, arquivo1.id, arquivo2.id]).exists())

        # R2 deve ter recebido as chaves dos arquivos
        r2_instance = MockR2.return_value
        r2_instance.delete_multiple_files.assert_called_once()
        deleted_keys = r2_instance.delete_multiple_files.call_args[0][0]
        self.assertIn(arquivo1.r2_key, deleted_keys)
        self.assertIn(arquivo2.r2_key, deleted_keys)

    def test_deletar_enduser_proibido(self, MockR2):
        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.enduser)

        response = self.client.delete(f'{self.base_url}{arquivo.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(StorageFile.objects.filter(id=arquivo.id).exists())

    def test_deletar_r2_falha_nao_remove_banco(self, MockR2):
        """Se o R2 falhar, o banco não deve ser alterado."""
        from botocore.exceptions import ClientError
        mock_r2 = _make_r2_mock()
        mock_r2.delete_multiple_files.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Internal'}}, 'DeleteObjects'
        )
        MockR2.return_value = mock_r2

        arquivo = StorageFileFactory(school=self.school)
        self._auth(self.manager)

        response = self.client.delete(f'{self.base_url}{arquivo.id}/')

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        # Arquivo ainda existe no banco
        self.assertTrue(StorageFile.objects.filter(id=arquivo.id).exists())


# ===================================================================
# BULK DELETE
# ===================================================================

@patch(R2_MOCK)
class TestBulkDelete(StorageBaseTestCase):

    def test_bulk_delete_sucesso(self, MockR2):
        MockR2.return_value = _make_r2_mock()

        f1 = StorageFileFactory(school=self.school)
        f2 = StorageFileFactory(school=self.school)
        f3 = StorageFileFactory(school=self.school)  # não incluso

        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}bulk-delete/',
            {'ids': [str(f1.id), str(f2.id)]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 2)
        self.assertFalse(StorageFile.objects.filter(id=f1.id).exists())
        self.assertFalse(StorageFile.objects.filter(id=f2.id).exists())
        self.assertTrue(StorageFile.objects.filter(id=f3.id).exists())  # não foi deletado

    def test_bulk_delete_sem_ids(self, MockR2):
        self._auth(self.manager)

        response = self.client.post(
            f'{self.base_url}bulk-delete/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_ids_de_outra_escola(self, MockR2):
        """IDs de escola diferente não são encontrados."""
        MockR2.return_value = _make_r2_mock()
        arquivo_b = StorageFileFactory(school=self.school_b)
        self._auth(self.manager)  # escola A

        response = self.client.post(
            f'{self.base_url}bulk-delete/',
            {'ids': [str(arquivo_b.id)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Arquivo da escola B intacto
        self.assertTrue(StorageFile.objects.filter(id=arquivo_b.id).exists())

    def test_bulk_delete_enduser_proibido(self, MockR2):
        f1 = StorageFileFactory(school=self.school)
        self._auth(self.enduser)

        response = self.client.post(
            f'{self.base_url}bulk-delete/',
            {'ids': [str(f1.id)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ===================================================================
# ISOLAMENTO DE DADOS ENTRE ESCOLAS
# ===================================================================

@patch(R2_MOCK)
class TestIsolamento(StorageBaseTestCase):

    def test_lista_apenas_escola_propria(self, MockR2):
        """Manager A não vê arquivos da escola B."""
        StorageFileFactory(school=self.school, name='escola_a.pdf')
        StorageFileFactory(school=self.school_b, name='escola_b.pdf')

        self._auth(self.manager)
        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes = [item['name'] for item in response.data['results']]
        self.assertIn('escola_a.pdf', nomes)
        self.assertNotIn('escola_b.pdf', nomes)

    def test_acesso_direto_arquivo_outra_escola_retorna_404(self, MockR2):
        arquivo_b = StorageFileFactory(school=self.school_b)
        self._auth(self.manager)  # escola A

        response = self.client.get(f'{self.base_url}{arquivo_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ===================================================================
# FILTROS E BUSCA
# ===================================================================

@patch(R2_MOCK)
class TestFiltros(StorageBaseTestCase):

    def setUp(self):
        super().setUp()
        self.pasta = StorageFolderFactory(school=self.school, name='Root')
        self.f1 = StorageFileFactory(
            school=self.school, name='relatório.pdf',
            parent_folder=self.pasta, tags='financeiro,2024'
        )
        self.f2 = StorageFileFactory(
            school=self.school, name='foto.jpg',
            parent_folder=None, tags='imagem'
        )
        self.f3 = StorageFolderFactory(
            school=self.school, name='Sub', parent_folder=self.pasta
        )

    def test_filtrar_por_parent_folder(self, MockR2):
        self._auth(self.manager)
        response = self.client.get(
            self.base_url,
            {'parent_folder': str(self.pasta.id)}
        )
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.f1.id), ids)
        self.assertIn(str(self.f3.id), ids)
        self.assertNotIn(str(self.f2.id), ids)

    def test_filtrar_raiz(self, MockR2):
        """parent_folder=null retorna itens na raiz."""
        self._auth(self.manager)
        response = self.client.get(self.base_url, {'parent_folder': 'null'})

        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.f2.id), ids)
        self.assertIn(str(self.pasta.id), ids)  # pasta root está na raiz
        self.assertNotIn(str(self.f1.id), ids)

    def test_filtrar_apenas_pastas(self, MockR2):
        self._auth(self.manager)
        response = self.client.get(self.base_url, {'is_folder': 'true'})

        for item in response.data['results']:
            self.assertTrue(item['is_folder'])

    def test_filtrar_apenas_arquivos(self, MockR2):
        self._auth(self.manager)
        response = self.client.get(self.base_url, {'is_folder': 'false'})

        for item in response.data['results']:
            self.assertFalse(item['is_folder'])

    def test_busca_por_tag(self, MockR2):
        self._auth(self.manager)
        response = self.client.get(self.base_url, {'tags': 'financeiro'})

        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.f1.id), ids)
        self.assertNotIn(str(self.f2.id), ids)

    def test_busca_por_nome(self, MockR2):
        self._auth(self.manager)
        response = self.client.get(self.base_url, {'search': 'relatório'})

        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.f1.id), ids)