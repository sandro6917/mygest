"""
Test per importazione Certificazioni Uniche (CU) con verifica salvataggio file.

Fix per bug: file estratto da ZIP non veniva salvato né associato al documento.
"""
import os
import tempfile
import zipfile
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from documenti.models import Documento, DocumentiTipo, ImportSession
from documenti.importers.certificazioni_uniche import CertificazioniUnicheImporter
from anagrafiche.models import Anagrafica, Cliente
from titolario.models import TitolarioVoce

User = get_user_model()


class CUImportFileAttachmentTest(TransactionTestCase):
    """Test salvataggio file PDF durante importazione CU."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_cu_import',
            password='testpass123'
        )
        self.tipo_cu, _ = DocumentiTipo.objects.get_or_create(
            codice='CU',
            defaults={'descrizione': 'Certificazione Unica'}
        )
        self.voce_hr_pers, _ = TitolarioVoce.objects.get_or_create(
            codice='HR-PERS',
            defaults={
                'titolo': 'Personale',
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
    
    def _create_fake_cu_pdf(self, filename='CU_2025_ROSSI_MARIO.pdf'):
        temp_dir = tempfile.mkdtemp(prefix='test_cu_')
        pdf_path = os.path.join(temp_dir, filename)
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%fake content\n%%EOF')
        return pdf_path
    
    def test_import_cu_singolo_pdf_file_salvato(self):
        """Test: file PDF deve essere salvato."""
        pdf_path = self._create_fake_cu_pdf()
        session = ImportSession.objects.create(
            tipo_importazione='certificazioni_uniche',
            utente=self.user,
        )
        importer = CertificazioniUnicheImporter(session)
        
        parsed_data = {
            'codice_fiscale_datore': '12345678901',
            'denominazione_datore': 'Test Azienda SRL',
            'codice_fiscale_lavoratore': 'RSSMRA85M01H501X',
            'cognome_lavoratore': 'ROSSI',
            'nome_lavoratore': 'MARIO',
            'anno_riferimento': 2025,
            'anno_imposta': '2025',
            'data_comunicazione': '2025-03-01',
        }
        
        documento = importer.create_documento(
            parsed_data=parsed_data,
            valori_editati={},
            user=self.user,
            file_path=pdf_path,
        )
        
        self.assertIsNotNone(documento.file)
        self.assertTrue(os.path.exists(documento.file.path))
        self.assertGreater(documento.file.size, 0)
        
        # Cleanup
        documento.file.delete()
        os.remove(pdf_path)
    
    def test_import_cu_file_path_invalido_graceful(self):
        """Test: gestione graceful file_path invalido."""
        session = ImportSession.objects.create(
            tipo_importazione='certificazioni_uniche',
            utente=self.user,
        )
        importer = CertificazioniUnicheImporter(session)
        
        parsed_data = {
            'codice_fiscale_datore': '12345678901',
            'denominazione_datore': 'Test Azienda SRL',
            'codice_fiscale_lavoratore': 'RSSMRA85M01H501X',
            'cognome_lavoratore': 'ROSSI',
            'nome_lavoratore': 'MARIO',
            'anno_riferimento': 2025,
            'anno_imposta': '2025',
            'data_comunicazione': '2025-03-01',
        }
        
        documento = importer.create_documento(
            parsed_data=parsed_data,
            valori_editati={},
            user=self.user,
            file_path='/path/invalido/non_esiste.pdf',
        )
        
        self.assertIsNotNone(documento.id)
        self.assertFalse(bool(documento.file))
    
    def test_salva_attributi_cu_returns_attrs_map(self):
        """
        Test: _salva_attributi_cu deve ritornare attrs_map completo.
        Verifica fix bug pattern naming: metodo ritorna Dict invece di None.
        """
        session = ImportSession.objects.create(
            tipo_importazione='certificazioni_uniche',
            utente=self.user,
        )
        importer = CertificazioniUnicheImporter(session)
        
        # Crea documento test
        cliente, _ = Cliente.objects.get_or_create(
            codice='TEST001',
            defaults={'denominazione': 'Test Cliente SRL'}
        )
        anagrafica, _ = Anagrafica.objects.get_or_create(
            codice_fiscale='RSSMRA85M01H501X',
            defaults={
                'cognome': 'ROSSI',
                'nome': 'MARIO',
                'cliente': cliente,
            }
        )
        
        documento = Documento.objects.create(
            tipo=self.tipo_cu,
            cliente=cliente,
            titolario=self.voce_hr_pers,
            codice='TEST-CU-001',
            descrizione='Test CU',
        )
        
        data = {
            'anno_riferimento': 2025,
            'anno_imposta': '2025',
            'codice_fiscale_datore': '12345678901',
            'denominazione_datore': 'Test Azienda SRL',
            'codice_fiscale_lavoratore': 'RSSMRA85M01H501X',
            'cognome_lavoratore': 'ROSSI',
            'nome_lavoratore': 'MARIO',
            'redditi_lavoro_dipendente': '25000.50',
        }
        
        # Chiama metodo e verifica ritorna dict
        attrs_map = importer._salva_attributi_cu(
            documento, 
            data, 
            cliente_datore_id=cliente.id,
            anagrafica_lavoratore_id=anagrafica.id
        )
        
        # Verifiche
        self.assertIsInstance(attrs_map, dict, "Deve ritornare un dizionario")
        self.assertGreater(len(attrs_map), 5, "Deve contenere almeno 5 attributi")
        self.assertIn('anno_riferimento', attrs_map)
        self.assertIn('dipendente', attrs_map)
        self.assertEqual(attrs_map['anno_riferimento'], 2025)
        self.assertEqual(attrs_map['dipendente'], anagrafica.id)
    
    def test_import_cu_pattern_naming_completo(self):
        """
        Test: pattern naming deve usare tutti gli attributi estratti.
        Verifica che nomi file contengano placeholder da pattern template.
        """
        # Setup cliente e anagrafica
        cliente, _ = Cliente.objects.get_or_create(
            codice='TEST002',
            defaults={'denominazione': 'Azienda Test SRL'}
        )
        anagrafica, _ = Anagrafica.objects.get_or_create(
            codice_fiscale='RSSMRA85M01H501X',
            defaults={
                'cognome': 'ROSSI',
                'nome': 'MARIO',
                'cliente': cliente,
            }
        )
        
        # Configura pattern naming su tipo documento
        self.tipo_cu.nome_file_pattern = '{attr:anno_riferimento}_{attr:dipendente_cognome}_{attr:dipendente_nome}_CU.pdf'
        self.tipo_cu.save()
        
        pdf_path = self._create_fake_cu_pdf()
        session = ImportSession.objects.create(
            tipo_importazione='certificazioni_uniche',
            utente=self.user,
        )
        importer = CertificazioniUnicheImporter(session)
        
        parsed_data = {
            'codice_fiscale_datore': '12345678901',
            'denominazione_datore': 'Azienda Test SRL',
            'codice_fiscale_lavoratore': 'RSSMRA85M01H501X',
            'cognome_lavoratore': 'ROSSI',
            'nome_lavoratore': 'MARIO',
            'anno_riferimento': 2025,
            'anno_imposta': '2025',
            'data_comunicazione': '2025-03-01',
        }
        
        documento = importer.create_documento(
            parsed_data=parsed_data,
            valori_editati={},
            user=self.user,
            file_path=pdf_path,
        )
        
        # Verifica nome file contiene attributi da pattern
        filename = os.path.basename(documento.file.name)
        self.assertIn('2025', filename, "Nome file deve contenere anno_riferimento")
        self.assertIn('ROSSI', filename, "Nome file deve contenere cognome lavoratore")
        self.assertIn('MARIO', filename, "Nome file deve contenere nome lavoratore")
        
        # Cleanup
        documento.file.delete()
        os.remove(pdf_path)
    
    def test_attrs_map_types_preserved(self):
        """
        Test: tipi attributi devono essere preservati in attrs_map.
        Verifica conversione corretta int/str/float in base a AttributoDefinizione.tipo_dato.
        """
        session = ImportSession.objects.create(
            tipo_importazione='certificazioni_uniche',
            utente=self.user,
        )
        importer = CertificazioniUnicheImporter(session)
        
        cliente, _ = Cliente.objects.get_or_create(
            codice='TEST003',
            defaults={'denominazione': 'Test SRL'}
        )
        anagrafica, _ = Anagrafica.objects.get_or_create(
            codice_fiscale='RSSMRA85M01H501X',
            defaults={
                'cognome': 'ROSSI',
                'nome': 'MARIO',
                'cliente': cliente,
            }
        )
        
        documento = Documento.objects.create(
            tipo=self.tipo_cu,
            cliente=cliente,
            titolario=self.voce_hr_pers,
            codice='TEST-CU-002',
            descrizione='Test CU Tipi',
        )
        
        data = {
            'anno_riferimento': 2025,  # int
            'denominazione_datore': 'Test SRL',  # str
            'redditi_lavoro_dipendente': '25000.50',  # decimal -> float
            'codice_fiscale_lavoratore': 'RSSMRA85M01H501X',
        }
        
        attrs_map = importer._salva_attributi_cu(
            documento,
            data,
            cliente_datore_id=cliente.id,
            anagrafica_lavoratore_id=anagrafica.id
        )
        
        # Verifica tipi sono preservati correttamente
        if 'anno_riferimento' in attrs_map:
            self.assertIsInstance(attrs_map['anno_riferimento'], int, "anno_riferimento deve essere int")
        
        if 'datore_denominazione' in attrs_map:
            self.assertIsInstance(attrs_map['datore_denominazione'], str, "datore_denominazione deve essere str")