"""
Test unitari per AI Import System
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image
import io

from documenti.models import DocumentiTipo
from ai_classifier.models import (
    DocumentExtractionTemplate,
    ExtractionTemplatePage,
    ExtractionTemplateZone,
    ExtractionFieldMapping,
    AIPredictionFeedback,
)

User = get_user_model()


class DocumentExtractionTemplateTestCase(TestCase):
    """Test per DocumentExtractionTemplate model"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.tipo_doc = DocumentiTipo.objects.create(
            codice='TEST',
            descrizione='Tipo Test',
            categoria='GENERICO'
        )
    
    def test_create_template(self):
        """Test creazione template"""
        template = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Test Template',
            descrizione='Template di test',
            numero_pagine=1,
            attivo=True,
            priorita=10,
            creato_da=self.user
        )
        
        self.assertEqual(template.nome, 'Test Template')
        self.assertTrue(template.attivo)
        self.assertEqual(template.priorita, 10)
        self.assertEqual(str(template), f"{self.tipo_doc.codice} - Test Template")
    
    def test_template_unique_constraint(self):
        """Test vincolo unique (tipo_documento, nome)"""
        DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Test Template',
            creato_da=self.user
        )
        
        # Tentativo di creare template duplicato
        with self.assertRaises(Exception):
            DocumentExtractionTemplate.objects.create(
                tipo_documento=self.tipo_doc,
                nome='Test Template',  # Stesso nome
                creato_da=self.user
            )


class ExtractionTemplatePageTestCase(TestCase):
    """Test per ExtractionTemplatePage model"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.tipo_doc = DocumentiTipo.objects.create(codice='TEST', descrizione='Tipo Test')
        self.template = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Test Template',
            creato_da=self.user
        )
    
    def test_create_page(self):
        """Test creazione pagina template"""
        # Crea immagine di test
        img = Image.new('RGB', (800, 1200), color='white')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        page = ExtractionTemplatePage.objects.create(
            template=self.template,
            numero_pagina=1,
            immagine_template=ContentFile(img_io.read(), name='test.png'),
            larghezza=800,
            altezza=1200
        )
        
        self.assertEqual(page.numero_pagina, 1)
        self.assertEqual(page.larghezza, 800)
        self.assertEqual(page.altezza, 1200)
        self.assertEqual(str(page), f"{self.template.nome} - Pagina 1")


class ExtractionTemplateZoneTestCase(TestCase):
    """Test per ExtractionTemplateZone model"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.tipo_doc = DocumentiTipo.objects.create(codice='TEST', descrizione='Tipo Test')
        self.template = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Test Template',
            creato_da=self.user
        )
        
        img = Image.new('RGB', (800, 1200), color='white')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        self.page = ExtractionTemplatePage.objects.create(
            template=self.template,
            numero_pagina=1,
            immagine_template=ContentFile(img_io.read(), name='test.png'),
            larghezza=800,
            altezza=1200
        )
    
    def test_create_zone(self):
        """Test creazione zona estrazione"""
        zone = ExtractionTemplateZone.objects.create(
            pagina=self.page,
            nome_campo='codice_fiscale',
            etichetta='Codice Fiscale',
            x_percent=10.0,
            y_percent=15.0,
            width_percent=30.0,
            height_percent=5.0,
            tipo_dato='codice_fiscale',
            obbligatorio=True,
            ordine=1
        )
        
        self.assertEqual(zone.nome_campo, 'codice_fiscale')
        self.assertTrue(zone.obbligatorio)
        self.assertEqual(zone.tipo_dato, 'codice_fiscale')
    
    def test_absolute_coordinates(self):
        """Test calcolo coordinate assolute"""
        zone = ExtractionTemplateZone.objects.create(
            pagina=self.page,
            nome_campo='test_field',
            etichetta='Test Field',
            x_percent=10.0,   # 10% di 800 = 80
            y_percent=20.0,   # 20% di 1200 = 240
            width_percent=25.0,  # 25% di 800 = 200
            height_percent=5.0,   # 5% di 1200 = 60
            tipo_dato='text',
            ordine=1
        )
        
        coords = zone.get_absolute_coordinates()
        
        self.assertEqual(coords['x'], 80)
        self.assertEqual(coords['y'], 240)
        self.assertEqual(coords['width'], 200)
        self.assertEqual(coords['height'], 60)


class ExtractionFieldMappingTestCase(TestCase):
    """Test per ExtractionFieldMapping model"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.tipo_doc = DocumentiTipo.objects.create(codice='TEST', descrizione='Tipo Test')
        self.template = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Test Template',
            creato_da=self.user
        )
    
    def test_create_mapping(self):
        """Test creazione mapping campo"""
        mapping = ExtractionFieldMapping.objects.create(
            template=self.template,
            nome_campo_template='codice_fiscale',
            tipo_campo_destinazione='attribute',
            nome_campo_destinazione='attributo:cf',
            funzione_trasformazione='normalize_cf',
        )
        
        self.assertEqual(mapping.nome_campo_template, 'codice_fiscale')
        self.assertEqual(mapping.tipo_campo_destinazione, 'attribute')
        self.assertEqual(str(mapping), 'codice_fiscale → attributo:cf')
    
    def test_mapping_types(self):
        """Test diversi tipi di mapping"""
        # Mapping a campo modello
        mapping1 = ExtractionFieldMapping.objects.create(
            template=self.template,
            nome_campo_template='data_doc',
            tipo_campo_destinazione='field',
            nome_campo_destinazione='data_documento'
        )
        self.assertEqual(mapping1.tipo_campo_destinazione, 'field')
        
        # Mapping a note
        mapping2 = ExtractionFieldMapping.objects.create(
            template=self.template,
            nome_campo_template='note_estratte',
            tipo_campo_destinazione='note',
            nome_campo_destinazione='note'
        )
        self.assertEqual(mapping2.tipo_campo_destinazione, 'note')


class AIPredictionFeedbackTestCase(TestCase):
    """Test per AIPredictionFeedback model"""
    
    def setUp(self):
        """Setup test data"""
        from documenti.models import Documento, Cliente
        from anagrafiche.models import Anagrafica
        
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Crea tipo documento
        self.tipo_doc1 = DocumentiTipo.objects.create(codice='TEST1', descrizione='Tipo 1')
        self.tipo_doc2 = DocumentiTipo.objects.create(codice='TEST2', descrizione='Tipo 2')
        
        # Crea cliente e documento
        anagrafica = Anagrafica.objects.create(
            nome='Test',
            tipo='PF',
            codice_fiscale='RSSMRA80A01H501X'
        )
        cliente = Cliente.objects.create(anagrafica=anagrafica)
        
        self.documento = Documento.objects.create(
            tipo=self.tipo_doc1,
            cliente=cliente,
            titolo='Documento Test'
        )
    
    def test_create_feedback_correct(self):
        """Test feedback predizione corretta"""
        feedback = AIPredictionFeedback.objects.create(
            documento=self.documento,
            tipo_predetto=self.tipo_doc1,
            tipo_confermato=self.tipo_doc1,  # Stesso tipo = corretta
            confidence_predizione=0.95,
            top_3_predizioni=[
                {'tipo_id': self.tipo_doc1.id, 'codice': 'TEST1', 'confidence': 0.95},
                {'tipo_id': self.tipo_doc2.id, 'codice': 'TEST2', 'confidence': 0.03},
            ],
            utente=self.user
        )
        
        self.assertTrue(feedback.predizione_corretta)
        self.assertEqual(feedback.confidence_predizione, 0.95)
    
    def test_create_feedback_incorrect(self):
        """Test feedback predizione errata"""
        feedback = AIPredictionFeedback.objects.create(
            documento=self.documento,
            tipo_predetto=self.tipo_doc1,
            tipo_confermato=self.tipo_doc2,  # Tipo diverso = errata
            confidence_predizione=0.80,
            top_3_predizioni=[],
            utente=self.user
        )
        
        self.assertFalse(feedback.predizione_corretta)


class ModelMetaTestCase(TestCase):
    """Test per Meta class e ordinamenti"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.tipo_doc = DocumentiTipo.objects.create(codice='TEST', descrizione='Tipo Test')
    
    def test_template_ordering(self):
        """Test ordinamento template per priorità"""
        template1 = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Template A',
            priorita=5,
            creato_da=self.user
        )
        template2 = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Template B',
            priorita=10,
            creato_da=self.user
        )
        template3 = DocumentExtractionTemplate.objects.create(
            tipo_documento=self.tipo_doc,
            nome='Template C',
            priorita=1,
            creato_da=self.user
        )
        
        # Ordinamento: -priorita, -creato_il
        templates = list(DocumentExtractionTemplate.objects.all())
        
        self.assertEqual(templates[0].id, template2.id)  # Priorità 10
        self.assertEqual(templates[1].id, template1.id)  # Priorità 5
        self.assertEqual(templates[2].id, template3.id)  # Priorità 1
