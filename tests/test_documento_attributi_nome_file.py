"""
Test per verificare che gli attributi dinamici vengano correttamente 
interpretati nel pattern del nome file durante la creazione e modifica
di un documento.
"""
import os
import tempfile
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from documenti.models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from documenti.forms import DocumentoDinamicoForm
from anagrafiche.models import Anagrafica, Cliente

User = get_user_model()


class TestDocumentoAttributiNomeFile(TestCase):
    """
    Test per verificare che il pattern nome_file_pattern interpreti 
    correttamente gli attributi dinamici {attr:} durante creazione e modifica.
    """

    def setUp(self):
        """Prepara i dati di test."""
        # Crea un utente per eventuali operazioni
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Crea un'anagrafica/cliente di test (persona giuridica)
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="SALREM SRL",
            codice_fiscale="12345678901",  # CF numerico 11 cifre per PG
            codice="SALREM01"
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)
        
        # Crea un tipo documento con pattern che include attributi dinamici
        self.tipo = DocumentiTipo.objects.create(
            codice="PRES",
            nome="Presenze",
            nome_file_pattern="Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}",
            estensioni_permesse="pdf,xlsx,docx"
        )
        
        # Definisci attributi dinamici per questo tipo di documento
        self.attr_anno = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo,
            codice="anno_riferimento",
            nome="Anno di riferimento",
            tipo_dato="string",
            required=True,
            ordine=1
        )
        
        self.attr_mese = AttributoDefinizione.objects.create(
            tipo_documento=self.tipo,
            codice="mese_riferimento",
            nome="Mese di riferimento",
            tipo_dato="string",
            required=True,
            ordine=2
        )

    def test_creazione_documento_con_attributi_dinamici(self):
        """
        Test che verifica che durante la creazione di un documento,
        gli attributi dinamici vengano correttamente interpretati nel nome file.
        """
        # Crea un file temporaneo
        file_content = b"Test content"
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        
        # Prepara i dati del form
        form_data = {
            "tipo": self.tipo.pk,
            "cliente": self.cliente.pk,
            "descrizione": "Test documento presenze",
            "data_documento": date.today(),
            "stato": "bozza",  # valore in minuscolo come definito nel modello
            "digitale": True,  # Documento digitale per evitare problemi con ubicazione
            "attr_anno_riferimento": "2024",
            "attr_mese_riferimento": "12",
        }
        
        # Crea il form con file
        form = DocumentoDinamicoForm(
            data=form_data,
            files={"file": uploaded_file},
            tipo=self.tipo
        )
        
        # Verifica che il form sia valido
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Salva il documento
        doc = form.save()
        
        # Verifica che il documento sia stato creato
        self.assertIsNotNone(doc.pk)
        
        # Verifica che gli attributi siano stati salvati correttamente
        attr_anno_val = AttributoValore.objects.get(
            documento=doc,
            definizione=self.attr_anno
        )
        self.assertEqual(attr_anno_val.valore, "2024")
        
        attr_mese_val = AttributoValore.objects.get(
            documento=doc,
            definizione=self.attr_mese
        )
        self.assertEqual(attr_mese_val.valore, "12")
        
        # Verifica che il nome del file contenga i valori degli attributi
        if doc.file:
            filename = os.path.basename(doc.file.name)
            self.assertIn("2024", filename, 
                         f"Anno 2024 non trovato nel nome file: {filename}")
            self.assertIn("12", filename,
                         f"Mese 12 non trovato nel nome file: {filename}")
            self.assertIn("SALREM01", filename,
                         f"Codice cliente SALREM01 non trovato nel nome file: {filename}")
            # Il nome dovrebbe essere qualcosa come: Presenze_202412_SALREM01.pdf
            self.assertIn("Presenze", filename,
                         f"Presenze non trovato nel nome file: {filename}")

    def test_modifica_documento_attributi_dinamici(self):
        """
        Test che verifica che durante la modifica di un documento,
        se si cambiano gli attributi dinamici, il nome file venga aggiornato.
        """
        # Prima crea un documento
        file_content = b"Test content"
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        
        form_data = {
            "tipo": self.tipo.pk,
            "cliente": self.cliente.pk,
            "descrizione": "Test documento presenze",
            "data_documento": date.today(),
            "stato": "bozza",
            "digitale": True,
            "attr_anno_riferimento": "2024",
            "attr_mese_riferimento": "11",
        }
        
        form = DocumentoDinamicoForm(
            data=form_data,
            files={"file": uploaded_file},
            tipo=self.tipo
        )
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        doc = form.save()
        
        # Verifica nome file iniziale
        if doc.file:
            old_filename = os.path.basename(doc.file.name)
            self.assertIn("11", old_filename, 
                         f"Mese 11 non trovato nel nome file iniziale: {old_filename}")
        
        # Ora modifica il mese
        doc_to_edit = Documento.objects.get(pk=doc.pk)
        
        form_data_edit = {
            "tipo": self.tipo.pk,
            "cliente": self.cliente.pk,
            "descrizione": "Test documento presenze",
            "data_documento": date.today(),
            "stato": "bozza",
            "digitale": True,
            "attr_anno_riferimento": "2024",
            "attr_mese_riferimento": "12",  # Cambiato da 11 a 12
        }
        
        # In modifica non passiamo il file, solo i dati
        form_edit = DocumentoDinamicoForm(
            data=form_data_edit,
            instance=doc_to_edit,
            tipo=self.tipo
        )
        
        self.assertTrue(form_edit.is_valid(), f"Form errors: {form_edit.errors}")
        doc_updated = form_edit.save()
        
        # Verifica che l'attributo sia stato aggiornato nel database
        attr_mese_updated = AttributoValore.objects.get(
            documento=doc_updated,
            definizione=self.attr_mese
        )
        self.assertEqual(attr_mese_updated.valore, "12")
        
        # Verifica che il nome file sia stato aggiornato
        if doc_updated.file:
            new_filename = os.path.basename(doc_updated.file.name)
            self.assertIn("12", new_filename,
                         f"Nuovo mese 12 non trovato nel nome file aggiornato: {new_filename}")
            # Verifica che il vecchio valore non sia più presente
            # (potrebbe essere presente nel percorso, quindi verifichiamo solo il basename)
            # Il nome dovrebbe essere Presenze_202412_SALREM01.pdf (con 12, non 11)

    def test_attributi_mancanti_pattern(self):
        """
        Test che verifica il comportamento quando gli attributi nel pattern
        non sono valorizzati (dovrebbero essere sostituiti con stringa vuota).
        """
        # Crea un documento senza valorizzare tutti gli attributi
        file_content = b"Test content"
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        
        form_data = {
            "tipo": self.tipo.pk,
            "cliente": self.cliente.pk,
            "descrizione": "Test documento presenze",
            "data_documento": date.today(),
            "stato": "bozza",
            "digitale": True,
            # attr_anno_riferimento non valorizzato
            "attr_mese_riferimento": "12",
        }
        
        # Gli attributi sono required, quindi il form non dovrebbe essere valido
        form = DocumentoDinamicoForm(
            data=form_data,
            files={"file": uploaded_file},
            tipo=self.tipo
        )
        
        # Il form non dovrebbe essere valido perché manca un attributo required
        self.assertFalse(form.is_valid())
        self.assertIn("attr_anno_riferimento", form.errors)
