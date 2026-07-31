"""
Test per importazione Modelli F24.
"""
import os
import tempfile
import zipfile
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from documenti.models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore, ImportSession
from documenti.importers.f24 import F24Importer
from documenti.parsers.f24_parser import parse_f24_pdf
from anagrafiche.models import Anagrafica, Cliente
from titolario.models import TitolarioVoce

User = get_user_model()


def _create_fake_f24_pdf(codice_fiscale='01110150537', data_scadenza='20/10/2026', directory=None):
    """
    Genera un PDF minimale con reportlab che riproduce il testo effettivamente
    estraibile via pdfplumber da un vero Modello F24 generato da software
    gestionale: le etichette del modulo (CODICE FISCALE, SEZIONE ERARIO, ecc.)
    fanno parte dell'immagine di sfondo e NON compaiono nel testo, solo i
    valori compilati. Include anche un secondo run di 11 cifre ("codice atto",
    più in basso nel modulo) per verificare che il parser prenda il primo
    (leftmost) e non questo, che avrebbe la stessa forma di una P.IVA.
    """
    from reportlab.pdfgen import canvas

    temp_dir = directory or tempfile.mkdtemp(prefix='test_f24_')
    pdf_path = os.path.join(temp_dir, 'f24_test.pdf')

    c = canvas.Canvas(pdf_path)
    c.drawString(50, 800, f"N. rata: 1 /20 Scadenza rata: {data_scadenza}")
    c.drawString(50, 780, ' '.join(codice_fiscale))
    c.drawString(50, 760, "BASE BALL CLUB GROSSETO A")
    c.drawString(50, 740, "GROSSETO G R VIA DEI BARBERI 108")
    c.drawString(50, 700, "9001 2023 139,65")
    c.drawString(50, 680, "5 8 0 1 2 5 7 2 4 1 6 139,65 139,65")  # decoy: codice atto (11 cifre)
    c.drawString(50, 660, "139,65")
    c.save()

    return pdf_path


class F24ParserTest(TestCase):
    """Test unitari sul parser F24."""

    def test_parse_f24_estrae_data_scadenza_e_cf(self):
        pdf_path = _create_fake_f24_pdf()
        try:
            result = parse_f24_pdf(pdf_path)
            self.assertEqual(result['data_scadenza'], '2026-10-20')
            self.assertEqual(result['codice_fiscale'], '01110150537')
        finally:
            os.remove(pdf_path)
            os.rmdir(os.path.dirname(pdf_path))

    def test_parse_f24_layout_con_scadenza_del_e_trattini(self):
        """
        Alcuni software gestionali usano l'etichetta "Scadenza del" (invece di
        "Scadenza rata:") con la data separata da trattini invece di slash
        (es. "Scadenza del 16-02-2026"): deve essere comunque riconosciuta e
        normalizzata in formato ISO.
        """
        temp_dir = tempfile.mkdtemp(prefix='test_f24_v2_')
        pdf_path = os.path.join(temp_dir, 'f24_v2.pdf')
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path)
        c.drawString(50, 800, "Scadenza del 16-02-2026")
        c.drawString(50, 780, "CODICE FISCALE")
        c.drawString(50, 760, "01713960530")
        c.drawString(50, 740, "ARKLABS SOCIETA A RESPONSABILITA LIMITATA TRA PROFESSIONISTI")
        c.drawString(50, 700, "1001 0001 2026 147,86")
        c.drawString(50, 680, "3600 DM10 3604756065 01 2026 306,00")
        c.save()

        try:
            result = parse_f24_pdf(pdf_path)
            self.assertEqual(result['data_scadenza'], '2026-02-16')
            self.assertEqual(result['codice_fiscale'], '01713960530')
        finally:
            os.remove(pdf_path)
            os.rmdir(temp_dir)

    def test_parse_f24_layout_con_scadenza_bare_e_punti_e_cf_persona_fisica(self):
        """
        Terzo layout osservato: etichetta "SCADENZA" da sola (senza "rata"/"del"),
        separatore a punti ("16.07.2026"), etichetta "CODICE FISCALE" presente ma
        senza valore adiacente (il CF persona fisica compare altrove nel testo,
        va trovato via fallback per forma), e importi con spaziatura irregolare
        tra virgola e centesimi (es. "93, 73" invece di "93,73").
        """
        temp_dir = tempfile.mkdtemp(prefix='test_f24_v3_')
        pdf_path = os.path.join(temp_dir, 'f24_v3.pdf')
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path)
        c.drawString(50, 800, "CONTRIBUENTE")
        c.drawString(50, 780, "CODICE FISCALE")
        c.drawString(50, 760, "cognome, denominazione o ragione sociale nome")
        c.drawString(50, 700, "SCADENZA 16.07.2026 Mod. F24")
        c.drawString(50, 680, "M S T P T R 7 9 H 0 4 E 2 0 2 G barrare in caso di anno d'imposta")
        c.drawString(50, 660, "Mastronardi Pietro")
        c.drawString(50, 600, "FIRMA")
        c.drawString(50, 580, "93, 73")
        c.save()

        try:
            result = parse_f24_pdf(pdf_path)
            self.assertEqual(result['data_scadenza'], '2026-07-16')
            self.assertEqual(result['codice_fiscale'], 'MSTPTR79H04E202G')
            self.assertEqual(result['importo_saldo'], '93,73')
            # "nome" (residuo dell'etichetta) non deve essere scambiato per denominazione
            self.assertNotEqual(result['denominazione'], 'nome')
        finally:
            os.remove(pdf_path)
            os.rmdir(temp_dir)

    def test_parse_f24_senza_marcatori_solleva_errore(self):
        temp_dir = tempfile.mkdtemp(prefix='test_f24_invalid_')
        pdf_path = os.path.join(temp_dir, 'non_f24.pdf')
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path)
        c.drawString(50, 800, "Documento qualsiasi")
        c.save()

        try:
            with self.assertRaises(ValueError):
                parse_f24_pdf(pdf_path)
        finally:
            os.remove(pdf_path)
            os.rmdir(temp_dir)


class F24ImportTest(TransactionTestCase):
    """Test importer F24: creazione documento, attributi, cliente."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_f24_import',
            password='testpass123'
        )

        self.tipo_f24, _ = DocumentiTipo.objects.get_or_create(
            codice='F24',
            defaults={'nome': 'Modello di versamento F24', 'estensioni_permesse': 'pdf'}
        )

        for codice_attr, nome, tipo_dato, choices, required in [
            ('data_scadenza', 'Data Scadenza', AttributoDefinizione.TipoDato.DATE, '', False),
            ('Tipo', 'Tipo', AttributoDefinizione.TipoDato.CHOICE, 'Modello, Ricevuta, Quietanza, Scarto', False),
            ('Tipo_pagamento', 'Tipo pagamento', AttributoDefinizione.TipoDato.CHOICE, 'Telematico, Cartaceo, Homebanking', False),
        ]:
            AttributoDefinizione.objects.get_or_create(
                tipo_documento=self.tipo_f24,
                codice=codice_attr,
                defaults={'nome': nome, 'tipo_dato': tipo_dato, 'choices': choices, 'required': required}
            )

        self.anagrafica = Anagrafica.objects.create(
            tipo='PG',
            ragione_sociale='BASEBALL CLUB GROSSETO A',
            codice_fiscale='01110150537',
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)

        self.voce_aftax, _ = TitolarioVoce.objects.get_or_create(
            codice='AF-TAX',
            defaults={'titolo': 'Imposte e tasse'}
        )
        self.titolario_voce, _ = TitolarioVoce.objects.get_or_create(
            codice='F24',
            parent=self.voce_aftax,
            defaults={'titolo': 'Versamenti F24'}
        )

    def _session(self):
        return ImportSession.objects.create(
            tipo_importazione='f24',
            utente=self.user,
        )

    def test_import_f24_pdf_singolo_file_salvato(self):
        pdf_path = _create_fake_f24_pdf()
        importer = F24Importer(self._session())

        # Forza lo storage sul filesystem locale (rediretto da conftest.py a
        # una tmp dir): evita di dipendere da un backend R2 reale in test.
        storage = Documento._meta.get_field('file').storage
        with patch.object(storage, '_r2', None):
            documento = importer.create_documento(
                parsed_data={'codice_fiscale': '01110150537', 'data_scadenza': '2026-10-20'},
                valori_editati={
                    'codice_fiscale': '01110150537',
                    'data_scadenza': '2026-10-20',
                    'denominazione': 'BASEBALL CLUB GROSSETO A',
                },
                user=self.user,
                file_path=pdf_path,
            )

            self.assertIsNotNone(documento.id)
            self.assertEqual(documento.cliente_id, self.cliente.id)
            self.assertTrue(bool(documento.file))
            self.assertTrue(os.path.exists(documento.file.path))

            valori = {
                av.definizione.codice: av.valore
                for av in AttributoValore.objects.filter(documento=documento)
            }
            self.assertEqual(valori['data_scadenza'], '2026-10-20')
            self.assertEqual(valori['Tipo'], 'Modello')
            self.assertIsNone(valori['Tipo_pagamento'])

            documento.file.delete()
        os.remove(pdf_path)
        os.rmdir(os.path.dirname(pdf_path))

    def test_import_f24_cliente_non_trovato_richiede_selezione_manuale(self):
        importer = F24Importer(self._session())

        with self.assertRaises(ValueError):
            importer.create_documento(
                parsed_data={'codice_fiscale': '99999999999', 'data_scadenza': '2026-10-20'},
                valori_editati={
                    'codice_fiscale': '99999999999',
                    'data_scadenza': '2026-10-20',
                    'denominazione': None,
                },
                user=self.user,
                file_path=None,
            )

    def test_import_f24_senza_scadenza_usa_data_odierna_e_valore_null(self):
        """
        Non tutti i modelli F24 riportano una scadenza (es. versamento in unica
        soluzione): in tal caso l'attributo data_scadenza deve restare null e
        data_documento deve usare la data odierna, senza errori.
        """
        importer = F24Importer(self._session())

        storage = Documento._meta.get_field('file').storage
        with patch.object(storage, '_r2', None):
            documento = importer.create_documento(
                parsed_data={'codice_fiscale': '01110150537', 'data_scadenza': None},
                valori_editati={
                    'codice_fiscale': '01110150537',
                    'data_scadenza': None,
                    'denominazione': 'BASEBALL CLUB GROSSETO A',
                    'importo_saldo': '458,19',
                },
                user=self.user,
                file_path=None,
            )

            self.assertIsNotNone(documento.id)
            self.assertEqual(documento.data_documento, timezone.now().date())
            self.assertIn('Scad. n.d.', documento.descrizione)
            self.assertIn('458,19', documento.descrizione)

            valori = {
                av.definizione.codice: av.valore
                for av in AttributoValore.objects.filter(documento=documento)
            }
            self.assertIsNone(valori['data_scadenza'])

    def test_import_f24_zip_multiplo(self):
        temp_dir = tempfile.mkdtemp(prefix='test_f24_zip_')
        pdf1 = _create_fake_f24_pdf(directory=temp_dir)
        os.rename(pdf1, os.path.join(temp_dir, 'f24_1.pdf'))
        pdf2 = _create_fake_f24_pdf(directory=tempfile.mkdtemp(prefix='test_f24_zip2_'))

        zip_path = os.path.join(temp_dir, 'f24_batch.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(os.path.join(temp_dir, 'f24_1.pdf'), 'f24_1.pdf')
            zf.write(pdf2, 'f24_2.pdf')

        importer = F24Importer(self._session())
        documents = importer.extract_documents(zip_path)

        self.assertEqual(len(documents), 2)
        self.assertTrue(all(d['filename'].endswith('.pdf') for d in documents))
