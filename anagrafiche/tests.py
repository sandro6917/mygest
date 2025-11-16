from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comunicazioni.models import Comunicazione
from anagrafiche.views import _resolve_cliente_relation, _extract_anagrafica_id
from anagrafiche.models import Cliente, Anagrafica
from documenti.models import Documento
from pratiche.models import Pratica


class SelectRelatedHelpersTests(TestCase):
	def test_resolve_cliente_relation_for_documento(self):
		select_fields, filter_key, targets_cliente = _resolve_cliente_relation(Documento)
		self.assertEqual(select_fields, ["cliente", "cliente__anagrafica"])
		self.assertEqual(filter_key, "cliente__anagrafica")
		self.assertTrue(targets_cliente)

	def test_resolve_cliente_relation_for_pratica(self):
		select_fields, filter_key, targets_cliente = _resolve_cliente_relation(Pratica)
		self.assertEqual(select_fields, ["cliente", "cliente__anagrafica"])
		self.assertEqual(filter_key, "cliente__anagrafica")
		self.assertTrue(targets_cliente)

	def test_resolve_cliente_relation_for_model_without_cliente_field(self):
		select_fields, filter_key, targets_cliente = _resolve_cliente_relation(Cliente)
		self.assertEqual(select_fields, [])
		self.assertIsNone(filter_key)
		self.assertFalse(targets_cliente)

	def test_extract_anagrafica_id_from_cliente_relation(self):
		dummy_cliente = SimpleNamespace(anagrafica_id=55)
		instance = SimpleNamespace(cliente=dummy_cliente, cliente_id=None)
		self.assertEqual(
			_extract_anagrafica_id(instance, relation_targets_cliente=True),
			55,
		)

	def test_extract_anagrafica_id_from_direct_field(self):
		instance = SimpleNamespace(cliente_id=77)
		self.assertEqual(
			_extract_anagrafica_id(instance, relation_targets_cliente=False),
			77,
		)

	def test_extract_anagrafica_id_fallback_to_related_object(self):
		related = SimpleNamespace(id=12)
		instance = SimpleNamespace(cliente=None, cliente_id=None)
		setattr(instance, "cliente", related)
		self.assertEqual(
			_extract_anagrafica_id(instance, relation_targets_cliente=False),
			12,
		)


class AnagraficaDetailCommunicationsTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="detail-user",
			password="pass1234",
		)
		self.client.force_login(self.user)
		self.anagrafica = Anagrafica.objects.create(
			tipo=Anagrafica.TipoSoggetto.PERSONA_FISICA,
			nome="Mario",
			cognome="Rossi",
			codice_fiscale="RSSMRA80A01H501U",
		)

	def test_comunicazioni_in_context_ordered_desc(self):
		base_time = timezone.now()
		recent = Comunicazione.objects.create(
			anagrafica=self.anagrafica,
			tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
			direzione=Comunicazione.Direzione.OUT,
			oggetto="Invio documentazione",
			destinatari="dest@example.com",
			data_invio=base_time,
		)
		slightly_older = Comunicazione.objects.create(
			anagrafica=self.anagrafica,
			tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
			direzione=Comunicazione.Direzione.IN,
			oggetto="Richiesta informazioni",
			destinatari="dest@example.com",
			data_invio=base_time - timedelta(hours=1),
		)
		without_send = Comunicazione.objects.create(
			anagrafica=self.anagrafica,
			tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
			direzione=Comunicazione.Direzione.OUT,
			oggetto="Bozza comunicazione",
			destinatari="dest@example.com",
		)
		Comunicazione.objects.filter(pk=without_send.pk).update(
			data_creazione=base_time - timedelta(days=2)
		)
		without_send.refresh_from_db()

		url = reverse("anagrafiche:detail", args=[self.anagrafica.pk])
		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)
		comunicazioni = list(response.context["comunicazioni"])
		self.assertGreaterEqual(len(comunicazioni), 3)
		self.assertEqual(
			[c.pk for c in comunicazioni[:3]],
			[recent.pk, slightly_older.pk, without_send.pk],
		)
		self.assertTrue(hasattr(comunicazioni[0], "data_riferimento"))
		self.assertEqual(
			comunicazioni[-1].data_riferimento,
			comunicazioni[-1].data_creazione,
		)
