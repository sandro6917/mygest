import shutil
import tempfile

from django.test import TestCase, override_settings

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import DocumentiTipo, Documento
from documenti.utils import build_document_filename


class DocumentFilenamePatternClienteTokenTests(TestCase):
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

    def test_cliente_denominazione_token(self):
        tipo = DocumentiTipo.objects.create(
            codice="DOC",
            nome="Documento",
            nome_file_pattern="Contratto_{cliente.denominazione}",
        )
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Contratto Test",
        )

        filename = build_document_filename(documento, "original.pdf")
        self.assertEqual(filename, "Contratto_ACME S.p.A..pdf")

    def test_cliente_nested_attr_token(self):
        tipo = DocumentiTipo.objects.create(
            codice="DOC2",
            nome="Documento",
            nome_file_pattern="CF_{cliente.anagrafica.codice_fiscale}",
        )
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Documento CF",
        )

        filename = build_document_filename(documento, "scan.pdf")
        self.assertEqual(filename, "CF_12345678901.pdf")
