"""
Test per API Archivio Fisico
Esegui con: python manage.py test api.v1.archivio_fisico.tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from archivio_fisico.models import UnitaFisica, OperazioneArchivio, RigaOperazioneArchivio
from anagrafiche.models import Anagrafica
from documenti.models import Documento, DocumentiTipo

User = get_user_model()


class UnitaFisicaAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='test123')
        self.client.force_authenticate(user=self.user)
        
        # Crea unità di test
        self.unita_radice = UnitaFisica.objects.create(
            prefisso_codice='UFF',
            nome='Ufficio Test',
            tipo='ufficio',
            attivo=True
        )

    def test_list_unita(self):
        """Test lista unità fisiche"""
        response = self.client.get('/api/v1/archivio-fisico/unita/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_detail_unita(self):
        """Test dettaglio unità fisica"""
        response = self.client.get(f'/api/v1/archivio-fisico/unita/{self.unita_radice.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Ufficio Test')

    def test_tree_unita(self):
        """Test albero unità fisiche"""
        response = self.client.get('/api/v1/archivio-fisico/unita/tree/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class OperazioneArchivioAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='test123')
        self.client.force_authenticate(user=self.user)
        
        # Crea dati di test
        self.anagrafica = Anagrafica.objects.create(
            codice='TEST001',
            cognome='Rossi',
            nome='Mario'
        )
        
        self.unita = UnitaFisica.objects.create(
            prefisso_codice='UFF',
            nome='Ufficio Test',
            tipo='ufficio',
            attivo=True
        )

    def test_list_operazioni(self):
        """Test lista operazioni"""
        response = self.client.get('/api/v1/archivio-fisico/operazioni/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_operazione(self):
        """Test creazione operazione"""
        data = {
            'tipo_operazione': 'entrata',
            'referente_interno': self.user.id,
            'referente_esterno': self.anagrafica.id,
            'note': 'Test operazione',
            'righe': []
        }
        response = self.client.post('/api/v1/archivio-fisico/operazioni/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filter_operazioni_by_tipo(self):
        """Test filtro per tipo operazione"""
        # Crea operazioni di test
        OperazioneArchivio.objects.create(
            tipo_operazione='entrata',
            referente_interno=self.user
        )
        OperazioneArchivio.objects.create(
            tipo_operazione='uscita',
            referente_interno=self.user
        )
        
        response = self.client.get('/api/v1/archivio-fisico/operazioni/?tipo_operazione=entrata')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for op in response.data['results']:
            self.assertEqual(op['tipo_operazione'], 'entrata')


class DocumentiTracciabiliAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='test123')
        self.client.force_authenticate(user=self.user)

    def test_list_documenti_tracciabili(self):
        """Test lista documenti tracciabili"""
        response = self.client.get('/api/v1/archivio-fisico/documenti-tracciabili/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_documenti(self):
        """Test ricerca documenti"""
        response = self.client.get('/api/v1/archivio-fisico/documenti-tracciabili/?search=TEST')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthorized_access(self):
        """Test accesso non autorizzato"""
        response = self.client.get('/api/v1/archivio-fisico/operazioni/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_access(self):
        """Test accesso autorizzato"""
        user = User.objects.create_user(username='test', password='test123')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v1/archivio-fisico/operazioni/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
