import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from anagrafiche.models import Anagrafica, Cliente
from archivio_fisico.models import UnitaFisica
from documenti.models import Documento, DocumentiTipo
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo, ProtocolloCounter
from titolario.models import TitolarioVoce


class MovimentoProtocolloClienteNormalizationTests(TestCase):
	def setUp(self):
		self.tmpdir = tempfile.mkdtemp(prefix="archivio-test-")
		self.override = override_settings(ARCHIVIO_BASE_PATH=self.tmpdir)
		self.override.enable()
		self.addCleanup(self.override.disable)
		self.addCleanup(lambda: shutil.rmtree(self.tmpdir, ignore_errors=True))

		self.user = get_user_model().objects.create_user("tester", "tester@example.com", "password")
		self.anagrafica = Anagrafica.objects.create(
			tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
			ragione_sociale="Libera Cooperativa Agricola Buriano",
			codice_fiscale="10000000009",
			partita_iva="10000000009",
		)
		self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)
		self.voce = TitolarioVoce.objects.create(codice="A01", titolo="Archivio")
		self.fascicolo = Fascicolo.objects.create(
			cliente=self.cliente,
			titolario_voce=self.voce,
			anno=timezone.now().year,
			titolo="Fascicolo Test",
		)
		self.documento_tipo = DocumentiTipo.objects.create(codice="TEST", nome="Documento Test")
		self.today = timezone.now().date()

	def _create_documento_cartaceo(self, *, codice: str = "DOC-001") -> Documento:
		return Documento.objects.create(
			codice=codice,
			tipo=self.documento_tipo,
			fascicolo=self.fascicolo,
			cliente=self.cliente,
			titolario_voce=self.voce,
			descrizione="Documento cartaceo",
			data_documento=self.today,
			stato=Documento.Stato.DEFINITIVO,
			digitale=False,
		)

	def test_registra_entrata_risoluzione_cliente_da_fascicolo(self):
		movimento = MovimentoProtocollo.registra_entrata(
			fascicolo=self.fascicolo,
			quando=timezone.now(),
			operatore=self.user,
			da_chi="Ufficio Protocollo",
		)

		self.assertEqual(movimento.cliente, self.anagrafica)
		counter = ProtocolloCounter.objects.get(
			cliente=self.anagrafica,
			anno=movimento.anno,
			direzione="IN",
		)
		self.assertEqual(counter.last_number, movimento.numero)

	def test_registra_uscita_risoluzione_cliente_da_fascicolo(self):
		movimento = MovimentoProtocollo.registra_uscita(
			fascicolo=self.fascicolo,
			quando=timezone.now(),
			operatore=self.user,
			a_chi="Esterno",
		)

		self.assertEqual(movimento.cliente, self.anagrafica)
		counter = ProtocolloCounter.objects.get(
			cliente=self.anagrafica,
			anno=movimento.anno,
			direzione="OUT",
		)
		self.assertEqual(counter.last_number, movimento.numero)

	def test_registra_entrata_documento_fascicolato_senza_protocollo_richiede_ubicazione(self):
		documento = self._create_documento_cartaceo()
		with self.assertRaisesMessage(
			ValidationError,
			"Per i documenti cartacei collegati a un fascicolo senza protocollo è obbligatorio indicare l'ubicazione.",
		):
			MovimentoProtocollo.registra_entrata(
				documento=documento,
				quando=timezone.now(),
				operatore=self.user,
				da_chi="Ufficio Protocollo",
			)

	def test_registra_entrata_documento_fascicolato_senza_protocollo_con_ubicazione(self):
		documento = self._create_documento_cartaceo(codice="DOC-002")
		unita = UnitaFisica.objects.create(
			prefisso_codice="UF",
			nome="Archivio Centrale",
			tipo=UnitaFisica.Tipo.UFFICIO,
		)

		movimento = MovimentoProtocollo.registra_entrata(
			documento=documento,
			quando=timezone.now(),
			operatore=self.user,
			da_chi="Ufficio Protocollo",
			ubicazione=unita,
		)

		self.assertEqual(movimento.ubicazione, unita)
		self.assertEqual(movimento.documento, documento)
