import shutil
import tempfile

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from anagrafiche.models import Anagrafica, Cliente
from comunicazioni.models import Comunicazione
from comunicazioni.services import protocolla_comunicazione as protocolla_comunicazione_service
from documenti.models import DocumentiTipo, Documento


class ProtocollaComunicazioneServiceTests(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="archivio-comunicazioni-")
        self.override = override_settings(ARCHIVIO_BASE_PATH=self.tmpdir)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.tmpdir, ignore_errors=True))

        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="Comunicazioni Test S.p.A.",
            codice_fiscale="10000000009",
            partita_iva="10000000009",
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)
        self.documento_tipo = DocumentiTipo.objects.create(codice="COM", nome="Comunicazione")
        self.documento = Documento.objects.create(
            tipo=self.documento_tipo,
            cliente=self.cliente,
            descrizione="Documento per comunicazione",
            digitale=True,
            tracciabile=True,
        )
        self.comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            direzione=Comunicazione.Direzione.IN,
            oggetto="Richiesta documenti",
            corpo="Test comunicazione",
            mittente="protocollo@example.com",
            destinatari="destinatario@example.com",
            anagrafica=self.anagrafica,
            documento_protocollo=self.documento,
        )

    def test_protocolla_crea_movimento_e_collega(self):
        movimento = protocolla_comunicazione_service(
            self.comunicazione,
            direzione="IN",
            quando=timezone.now(),
            destinatario="Ufficio Protocollo",
            causale="Test automatizzato",
        )

        self.comunicazione.refresh_from_db()
        self.assertIsNotNone(self.comunicazione.protocollo_movimento_id)
        self.assertEqual(self.comunicazione.protocollo_movimento_id, movimento.pk)
        self.assertEqual(movimento.direzione, "IN")
        self.assertEqual(movimento.destinatario, "Ufficio Protocollo")

    def test_senza_documento_generi_errore(self):
        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            direzione=Comunicazione.Direzione.OUT,
            oggetto="Comunicazione senza documento",
            corpo="",
            mittente="protocollo@example.com",
            destinatari="destinatario@example.com",
            anagrafica=self.anagrafica,
        )

        with self.assertRaises(ValidationError):
            protocolla_comunicazione_service(comunicazione)

    def test_non_permette_doppia_protocollazione(self):
        protocolla_comunicazione_service(
            self.comunicazione,
            direzione="IN",
            quando=timezone.now(),
            destinatario="Ufficio Protocollo",
        )

        with self.assertRaises(ValidationError):
            protocolla_comunicazione_service(
                self.comunicazione,
                direzione="IN",
                quando=timezone.now(),
                destinatario="Ufficio Protocollo",
            )
