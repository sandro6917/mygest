"""
Test per verificare che i token {attr:} vengano correttamente renderizzati
nei nomi file dei documenti, includendo attributi dinamici salvati dopo la creazione.
"""
import shutil
import tempfile
from datetime import date

from django.test import TestCase, override_settings

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import DocumentiTipo, Documento, AttributoDefinizione, AttributoValore
from documenti.utils import build_document_filename


class DocumentFilenameAttrTokenTests(TestCase):
    """
    Test dei token {attr:} nel pattern dei nomi file.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="archivio-documenti-")
        self.override = override_settings(ARCHIVIO_BASE_PATH=self.tmpdir)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.tmpdir, ignore_errors=True))

        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="ACME S.p.A.",
            codice_fiscale="12345678901",
            partita_iva="12345678901",
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)

    def test_attr_string_token(self):
        """Test token {attr:codice} con attributo stringa."""
        tipo = DocumentiTipo.objects.create(
            codice="PRES",
            nome="Presenze",
            nome_file_pattern="Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice_fiscale}",
        )
        
        # Crea definizioni attributo
        attr_anno = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="anno_riferimento",
            nome="Anno di riferimento",
            tipo_dato="string",
            required=False,
        )
        attr_mese = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="mese_riferimento",
            nome="Mese di riferimento",
            tipo_dato="string",
            required=False,
        )

        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Presenze dicembre 2024",
        )

        # Salva i valori degli attributi
        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_anno,
            valore="2024"
        )
        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_mese,
            valore="12"
        )

        # Test con lettura dal DB (caso normale)
        filename = build_document_filename(documento, "original.pdf")
        self.assertEqual(filename, "Presenze_202412_12345678901.pdf")

    def test_attr_date_token_with_format(self):
        """Test token {attr:data_riferimento:%Y%m%d} con attributo data e formato."""
        tipo = DocumentiTipo.objects.create(
            codice="FAT",
            nome="Fattura",
            nome_file_pattern="Fattura_{attr:data_riferimento:%Y%m%d}_{cliente.anagrafica.codice_fiscale}",
        )
        
        attr_data = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="data_riferimento",
            nome="Data di riferimento",
            tipo_dato="date",
            required=False,
        )

        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Fattura gennaio 2024",
        )

        # Salva il valore dell'attributo (date viene salvato in formato ISO)
        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_data,
            valore="2024-01-15"
        )

        filename = build_document_filename(documento, "original.pdf")
        self.assertEqual(filename, "Fattura_20240115_12345678901.pdf")

    def test_attr_tokens_with_explicit_map(self):
        """Test token {attr:} passando esplicitamente la mappa degli attributi."""
        tipo = DocumentiTipo.objects.create(
            codice="PRES2",
            nome="Presenze",
            nome_file_pattern="Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice_fiscale}",
        )
        
        # Crea definizioni attributo
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="anno_riferimento",
            nome="Anno di riferimento",
            tipo_dato="string",
            required=False,
        )
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="mese_riferimento",
            nome="Mese di riferimento",
            tipo_dato="string",
            required=False,
        )

        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Presenze dicembre 2024",
        )

        # Simula il caso del form: passiamo direttamente la mappa degli attributi
        # PRIMA di salvarli nel DB (per testare che il parametro attrs funzioni)
        attrs_map = {
            "anno_riferimento": "2024",
            "mese_riferimento": "12"
        }

        filename = build_document_filename(documento, "original.pdf", attrs=attrs_map)
        self.assertEqual(filename, "Presenze_202412_12345678901.pdf")

    def test_mixed_tokens(self):
        """Test mix di token {attr:}, {cliente.*} e altri."""
        tipo = DocumentiTipo.objects.create(
            codice="CERT",
            nome="Certificato",
            nome_file_pattern="Cert_{attr:numero}_{data_documento:%Y%m%d}_{cliente.anagrafica.codice_fiscale}",
        )
        
        attr_numero = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="numero",
            nome="Numero certificato",
            tipo_dato="string",
            required=False,
        )

        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Certificato test",
            data_documento=date(2024, 6, 15)
        )

        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_numero,
            valore="A123"
        )

        filename = build_document_filename(documento, "original.pdf")
        self.assertEqual(filename, "Cert_A123_20240615_12345678901.pdf")

    def test_attr_token_missing_value(self):
        """Test token {attr:} quando l'attributo non ha valore."""
        tipo = DocumentiTipo.objects.create(
            codice="DOC",
            nome="Documento",
            nome_file_pattern="Doc_{attr:codice_mancante}_{cliente.anagrafica.codice_fiscale}",
        )
        
        # Definizione esiste ma nessun valore salvato
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="codice_mancante",
            nome="Codice mancante",
            tipo_dato="string",
            required=False,
        )

        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Documento senza attributo",
        )

        filename = build_document_filename(documento, "original.pdf")
        # Quando l'attributo non ha valore, il token viene sostituito con stringa vuota
        # Gli underscore doppi vengono normalizzati a singoli
        self.assertEqual(filename, "Doc_12345678901.pdf")
