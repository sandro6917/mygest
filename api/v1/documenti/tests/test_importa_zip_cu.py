"""
Test per importazione ZIP come documento CU-ZIP
"""
import os
import tempfile
import zipfile
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from titolario.models import TitolarioVoce
from ai_classifier.models import DocumentExtractionTemplate
from api.v1.documenti.importa_zip_cu import importa_zip_come_cu, _salva_attributi_cu_zip

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestImportaZipCU(TestCase):
    """Test suite per importazione ZIP Certificazioni Uniche"""
    
    def setUp(self):
        """Setup iniziale per i test"""
        # Crea user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Crea tipo documento CU-ZIP
        self.tipo_cu_zip = DocumentiTipo.objects.create(
            codice='CU-ZIP',
            nome='Archivio Certificazioni Uniche',
            estensioni_permesse='zip',
            pattern_codice='{CLI}-CUZIP-{ANNO}-{SEQ:03d}',
            nome_file_pattern='Archivio_CU_{attr:anno_imposta}_{cliente.codice}.zip',
            attivo=True
        )
        
        # Crea attributi
        self.attr_anno = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo_cu_zip,
            codice='anno_imposta',
            nome='Anno Imposta',
            tipo_dato=AttributoDefinizione.TipoDato.INT,
            required=True
        )
        self.attr_datore = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo_cu_zip,
            codice='datore',
            nome='Datore',
            tipo_dato=AttributoDefinizione.TipoDato.INT,
            required=False
        )
        self.attr_num = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo_cu_zip,
            codice='num_certificazioni',
            nome='Numero Certificazioni',
            tipo_dato=AttributoDefinizione.TipoDato.INT,
            required=False
        )
        
        # Crea titolario HR-CU
        self.voce_hr = TitolarioVoce.objects.create(
            codice='HR',
            titolo='Human Resources'
        )
        self.voce_cu = TitolarioVoce.objects.create(
            codice='HR-CU',
            titolo='Certificazioni Uniche',
            parent=self.voce_hr
        )
        
        # Crea anagrafica e cliente datore
        self.anagrafica_datore = Anagrafica.objects.create(
            codice_fiscale='12345678901',
            denominazione='ACME SRL'
        )
        self.cliente_datore = Cliente.objects.create(
            anagrafica=self.anagrafica_datore,
            codice='ACME'
        )
    
    def _crea_zip_mock(self, num_pdf=3):
        """Crea un file ZIP mock con PDF fittizi"""
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for i in range(num_pdf):
                zip_file.writestr(f'CU_dipendente_{i+1}.pdf', b'%PDF-1.4 fake content')
        
        zip_buffer.seek(0)
        return SimpleUploadedFile(
            'cu_2024.zip',
            zip_buffer.read(),
            content_type='application/zip'
        )
    
    def test_salva_attributi_cu_zip(self):
        """Test salvataggio attributi CU-ZIP"""
        documento = Documento.objects.create(
            tipo=self.tipo_cu_zip,
            cliente=self.cliente_datore,
            titolario_voce=self.voce_cu,
            descrizione='Test'
        )
        
        dipendenti = ['ROSSI MARIO', 'BIANCHI LUCA']
        
        attrs_map = _salva_attributi_cu_zip(
            documento=documento,
            anno_imposta=2024,
            datore_cliente_id=self.cliente_datore.id,
            datore_cf='12345678901',
            datore_denominazione='ACME SRL',
            num_certificazioni=10,
            dipendenti_lista=dipendenti
        )
        
        self.assertEqual(attrs_map['anno_imposta'], 2024)
        self.assertEqual(attrs_map['num_certificazioni'], 10)
        
        # Verifica attributo salvato
        attr_val = AttributoValore.objects.get(
            documento=documento,
            definizione=self.attr_anno
        )
        self.assertEqual(attr_val.valore, 2024)
    
    def test_importa_zip_cu_file_non_zip(self):
        """Test errore se file non è ZIP"""
        fake_file = SimpleUploadedFile('test.pdf', b'not a zip')
        
        risultato = importa_zip_come_cu(
            zip_file=fake_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertFalse(risultato['success'])
        self.assertIn('non è un archivio ZIP valido', risultato['errori'][0])
    
    def test_importa_zip_cu_tipo_mancante(self):
        """Test errore se tipo CU-ZIP non configurato"""
        # Elimina tipo documento
        self.tipo_cu_zip.delete()
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction
        with patch('api.v1.documenti.importa_zip_cu.ExtractionService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.extract_from_template.return_value = {
                'fields': {
                    'sostituto_cf': '12345678901',
                    'sostituto_denominazione': 'ACME SRL',
                    'anno_imposta': '2024'
                }
            }
            mock_service.return_value = mock_instance
            
            risultato = importa_zip_come_cu(
                zip_file=zip_file,
                azione_duplicati='duplica',
                user=self.user
            )
        
        self.assertFalse(risultato['success'])
        self.assertIn('Tipo documento CU-ZIP non configurato', risultato['errori'][0])
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    def test_importa_zip_cu_creazione_successo(self, mock_service):
        """Test creazione documento CU-ZIP con successo"""
        zip_file = self._crea_zip_mock(num_pdf=5)
        
        # Mock AI extraction
        mock_instance = MagicMock()
        mock_instance.extract_from_template.return_value = {
            'fields': {
                'sostituto_cf': '12345678901',
                'sostituto_denominazione': 'ACME SRL',
                'anno_imposta': '2024',
                'dipendente_cognome': 'ROSSI',
                'dipendente_nome': 'MARIO'
            }
        }
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertTrue(risultato['success'])
        self.assertEqual(risultato['azione'], 'creato')
        self.assertIsNotNone(risultato['documento_id'])
        
        # Verifica documento creato
        documento = Documento.objects.get(id=risultato['documento_id'])
        self.assertEqual(documento.tipo.codice, 'CU-ZIP')
        self.assertEqual(documento.cliente, self.cliente_datore)
        
        # Verifica attributi
        attr_anno = AttributoValore.objects.get(
            documento=documento,
            definizione__codice='anno_imposta'
        )
        self.assertEqual(attr_anno.valore, 2024)
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    def test_importa_zip_cu_duplicato_skip(self, mock_service):
        """Test azione 'skip' con documento duplicato"""
        # Pre-crea documento esistente
        doc_esistente = Documento.objects.create(
            tipo=self.tipo_cu_zip,
            cliente=self.cliente_datore,
            titolario_voce=self.voce_cu,
            descrizione='Archivio CU 2024 esistente',
            data_documento='2025-03-31'
        )
        AttributoValore.objects.create(
            documento=doc_esistente,
            definizione=self.attr_anno,
            valore=2024
        )
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction
        mock_instance = MagicMock()
        mock_instance.extract_from_template.return_value = {
            'fields': {
                'sostituto_cf': '12345678901',
                'sostituto_denominazione': 'ACME SRL',
                'anno_imposta': '2024'
            }
        }
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='skip',
            user=self.user
        )
        
        self.assertFalse(risultato['success'])
        self.assertEqual(risultato['azione'], 'skipped')
        self.assertTrue(risultato['duplicato'])
        self.assertEqual(risultato['duplicato_id'], doc_esistente.id)
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    def test_importa_zip_cu_duplicato_sostituisci(self, mock_service):
        """Test azione 'sostituisci' con documento duplicato"""
        # Pre-crea documento esistente
        doc_esistente = Documento.objects.create(
            tipo=self.tipo_cu_zip,
            cliente=self.cliente_datore,
            titolario_voce=self.voce_cu,
            descrizione='Archivio CU 2024 esistente',
            data_documento='2025-03-31'
        )
        AttributoValore.objects.create(
            documento=doc_esistente,
            definizione=self.attr_anno,
            valore=2024
        )
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction
        mock_instance = MagicMock()
        mock_instance.extract_from_template.return_value = {
            'fields': {
                'sostituto_cf': '12345678901',
                'sostituto_denominazione': 'ACME SRL',
                'anno_imposta': '2024',
                'dipendente_cognome': 'VERDI',
                'dipendente_nome': 'GIUSEPPE'
            }
        }
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='sostituisci',
            user=self.user
        )
        
        self.assertTrue(risultato['success'])
        self.assertEqual(risultato['azione'], 'sostituito')
        self.assertTrue(risultato['duplicato'])
        self.assertEqual(risultato['documento_id'], doc_esistente.id)
        
        # Verifica documento aggiornato
        doc_esistente.refresh_from_db()
        self.assertIn('Archivio CU 2024', doc_esistente.descrizione)
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    @patch('api.v1.documenti.importa_zip_cu.DocumentExtractionTemplate')
    def test_importa_zip_cu_duplicato_duplica(self, mock_template_model, mock_service):
        """Test azione 'duplica' crea nuovo documento anche con duplicato esistente"""
        # Mock template AI
        mock_template = MagicMock()
        mock_template.nome = 'CU Template Test'
        mock_template_model.objects.get.return_value = mock_template
        
        # Pre-crea documento esistente
        doc_esistente = Documento.objects.create(
            tipo=self.tipo_cu_zip,
            cliente=self.cliente_datore,
            titolario_voce=self.voce_cu,
            descrizione='Archivio CU 2024 esistente',
            data_documento='2025-03-31'
        )
        AttributoValore.objects.create(
            documento=doc_esistente,
            definizione=self.attr_anno,
            valore=2024
        )
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction
        mock_instance = MagicMock()
        mock_instance.extract_from_template.return_value = {
            'fields': {
                'sostituto_cf': '12345678901',
                'sostituto_denominazione': 'ACME SRL',
                'anno_imposta': '2024',
                'dipendente_cognome': 'VERDI',
                'dipendente_nome': 'LUCA'
            }
        }
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertTrue(risultato['success'])
        self.assertEqual(risultato['azione'], 'duplicato')
        self.assertTrue(risultato['duplicato'])
        self.assertNotEqual(risultato['documento_id'], doc_esistente.id)
        
        # Verifica 2 documenti esistono
        self.assertEqual(
            Documento.objects.filter(tipo=self.tipo_cu_zip, cliente=self.cliente_datore).count(),
            2
        )
    
    @patch('api.v1.documenti.importa_zip_cu.DocumentExtractionTemplate')
    def test_template_ai_non_configurato(self, mock_template_model):
        """Test errore quando template AI 'CU' non esiste o non è attivo"""
        # Mock template non trovato
        mock_template_model.DoesNotExist = DocumentExtractionTemplate.DoesNotExist
        mock_template_model.objects.get.side_effect = DocumentExtractionTemplate.DoesNotExist
        
        zip_file = self._crea_zip_mock()
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertFalse(risultato['success'])
        self.assertTrue(any('Template AI' in err for err in risultato['errori']))
        self.assertTrue(any('non configurato' in err for err in risultato['errori']))
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    @patch('api.v1.documenti.importa_zip_cu.DocumentExtractionTemplate')
    def test_extraction_ai_fallisce(self, mock_template_model, mock_service):
        """Test errore quando extraction AI fallisce"""
        # Mock template OK
        mock_template = MagicMock()
        mock_template.nome = 'CU Template Test'
        mock_template_model.objects.get.return_value = mock_template
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction che fallisce
        mock_instance = MagicMock()
        mock_instance.extract_from_template.side_effect = Exception("AI service unavailable")
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertFalse(risultato['success'])
        self.assertTrue(any('Impossibile estrarre dati dal primo PDF' in err for err in risultato['errori']))
    
    @patch('api.v1.documenti.importa_zip_cu.ExtractionService')
    @patch('api.v1.documenti.importa_zip_cu.DocumentExtractionTemplate')
    def test_anagrafica_datore_non_trovata(self, mock_template_model, mock_service):
        """Test errore quando anagrafica datore non esiste"""
        # Mock template OK
        mock_template = MagicMock()
        mock_template.nome = 'CU Template Test'
        mock_template_model.objects.get.return_value = mock_template
        
        zip_file = self._crea_zip_mock()
        
        # Mock AI extraction con CF non esistente
        mock_instance = MagicMock()
        mock_instance.extract_from_template.return_value = {
            'fields': {
                'sostituto_cf': '99999999999',  # CF non esiste in anagrafica
                'sostituto_denominazione': 'AZIENDA SCONOSCIUTA',
                'anno_imposta': '2024'
            }
        }
        mock_service.return_value = mock_instance
        
        risultato = importa_zip_come_cu(
            zip_file=zip_file,
            azione_duplicati='duplica',
            user=self.user
        )
        
        self.assertFalse(risultato['success'])
        self.assertTrue(any('non trovato in anagrafica' in err for err in risultato['errori']))


class TestImportaZipCUEndpoint(TestCase):
    """Test per l'endpoint REST API"""
    
    def setUp(self):
        """Setup per test endpoint"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_login(self.user)
    
    def test_endpoint_richiede_autenticazione(self):
        """Test che l'endpoint richiede autenticazione"""
        self.client.logout()
        response = self.client.post('/api/v1/documenti/importa-zip-cu/')
        self.assertEqual(response.status_code, 401)
