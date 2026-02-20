"""
Test per verificare che gli attributi dinamici con widget anagrafica
mostrino correttamente una select autocomplete nel form.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from documenti.models import DocumentiTipo, AttributoDefinizione
from anagrafiche.models import Anagrafica
from django.contrib.auth import get_user_model

User = get_user_model()


class TestAttributiDinamiciWidgetAnagrafica(TestCase):
    """Test per gli attributi dinamici con widget anagrafica"""

    def setUp(self):
        """Setup iniziale"""
        # Crea utente admin
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.client = Client()
        self.client.login(username='admin', password='admin123')

        # Crea tipo documento con attributo dinamico anagrafica
        self.tipo = DocumentiTipo.objects.create(
            codice='TEST_ANAG',
            nome='Test Anagrafica Widget',
            pattern_codice='{CLI}-{ANNO}-{SEQ:04d}'
        )

        # Crea attributo dinamico con widget anagrafica
        self.attr_def = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo,
            codice='beneficiario',
            nome='Beneficiario',
            tipo_dato='int',
            widget='anagrafica',
            required=True,
            ordine=1
        )

        # Crea alcune anagrafiche di test
        self.anag1 = Anagrafica.objects.create(
            tipo='PG',
            ragione_sociale='Test Anagrafica 1',
            codice_fiscale='12345678901'
        )
        self.anag2 = Anagrafica.objects.create(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01H501Z'
        )

    def test_form_contiene_widget_select2(self):
        """Verifica che il form contenga il widget select2 per l'anagrafica"""
        from documenti.forms import DocumentoDinamicoForm

        form = DocumentoDinamicoForm(tipo=self.tipo)

        # Verifica che il campo attributo sia presente
        campo_nome = f'attr_{self.attr_def.codice}'
        self.assertIn(campo_nome, form.fields)

        # Verifica che sia un ModelChoiceField
        from django import forms
        self.assertIsInstance(form.fields[campo_nome], forms.ModelChoiceField)

        # Verifica che il widget abbia la classe select2
        widget = form.fields[campo_nome].widget
        self.assertIn('select2', widget.attrs.get('class', ''))

        # Verifica che abbia gli attributi data per select2
        self.assertIn('data-placeholder', widget.attrs)
        self.assertIn('data-allow-clear', widget.attrs)

    def test_form_rendering_html(self):
        """Verifica che il rendering HTML contenga gli elementi corretti"""
        from documenti.forms import DocumentoDinamicoForm

        form = DocumentoDinamicoForm(tipo=self.tipo)
        campo_nome = f'attr_{self.attr_def.codice}'
        
        # Renderizza il campo
        html = str(form[campo_nome])

        # Verifica che contenga la classe select2
        self.assertIn('select2', html)
        self.assertIn('data-placeholder', html)

        # Verifica che contenga le anagrafiche
        self.assertIn(str(self.anag1.id), html)
        self.assertIn(str(self.anag2.id), html)

    def test_view_nuovo_documento_con_attributo_anagrafica(self):
        """Verifica che la view mostri correttamente il form con l'attributo anagrafica"""
        url = reverse('documenti:nuovo_dinamico')
        
        # Step 1: selezione tipo
        response = self.client.post(url, {
            'step': 'select_type',
            'tipo_id': self.tipo.id
        })
        
        # Verifica che la risposta contenga il form
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'attr_beneficiario')
        self.assertContains(response, 'select2')
        self.assertContains(response, self.anag1.ragione_sociale)

    def test_salvataggio_con_attributo_anagrafica(self):
        """Verifica che il form possa essere salvato con un attributo anagrafica"""
        from documenti.models import Documento, AttributoValore
        from documenti.forms import DocumentoDinamicoForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        from datetime import date

        # Crea un cliente di test
        from anagrafiche.models import Cliente
        cliente = Cliente.objects.create(anagrafica=self.anag2)
        
        # Crea un file di test
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        # Dati del form
        data = {
            'tipo': self.tipo.id,
            'cliente': cliente.id,
            'data_documento': date(2026, 1, 2),
            'descrizione': 'Test documento con anagrafica',
            'digitale': True,
            'stato': 'bozza',
            'tracciabile': False,
            f'attr_beneficiario': self.anag1.id,
        }
        
        files = {'file': test_file}

        # Crea e valida il form
        form = DocumentoDinamicoForm(data=data, files=files, tipo=self.tipo)
        
        # Verifica che il form sia valido
        if not form.is_valid():
            print(f"Errori form: {form.errors}")
        
        self.assertTrue(form.is_valid())
        
        # Salva il documento
        doc = form.save()
        
        # Verifica che l'attributo sia stato salvato
        attr_valore = AttributoValore.objects.filter(
            documento=doc,
            definizione=self.attr_def
        ).first()
        
        self.assertIsNotNone(attr_valore)
        # Il valore dovrebbe essere l'ID dell'anagrafica
        self.assertEqual(int(attr_valore.valore), self.anag1.id)

    def test_modifica_con_attributo_anagrafica(self):
        """Verifica che la modifica funzioni con un attributo anagrafica"""
        from documenti.models import Documento, AttributoValore
        from documenti.forms import DocumentoDinamicoForm
        from datetime import date
        from anagrafiche.models import Cliente
        
        # Crea un cliente di test
        cliente = Cliente.objects.create(anagrafica=self.anag2)

        # Crea un documento con attributo anagrafica
        doc = Documento.objects.create(
            tipo=self.tipo,
            cliente=cliente,
            data_documento=date(2026, 1, 2),
            descrizione='Test modifica',
            digitale=True,
            stato='bozza'
        )

        # Crea l'attributo valore
        AttributoValore.objects.create(
            documento=doc,
            definizione=self.attr_def,
            valore=str(self.anag1.id)
        )

        # Crea il form per la modifica
        form = DocumentoDinamicoForm(instance=doc, tipo=self.tipo)
        campo_nome = f'attr_{self.attr_def.codice}'

        # Verifica che il campo sia inizializzato con l'anagrafica corretta
        self.assertIn(campo_nome, form.fields)
        # Il valore iniziale dovrebbe essere l'istanza Anagrafica
        self.assertEqual(form.initial.get(campo_nome), self.anag1)

    def tearDown(self):
        """Cleanup"""
        # Elimina i file creati durante i test
        from documenti.models import Documento
        for doc in Documento.objects.all():
            if doc.file:
                doc.file.delete()
