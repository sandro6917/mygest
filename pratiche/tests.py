from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from anagrafiche.models import Anagrafica, Cliente

from .forms import PraticaForm
from .models import Pratica, PraticheTipo, PraticaRelazione
from scadenze.models import Scadenza as AppScadenza, ScadenzaOccorrenza


def _make_valid_piva(seed: int) -> str:
	base = f"{seed:010d}"  # prime 10 cifre
	digits = [int(ch) for ch in base]
	pari = sum(digits[0::2])
	dispari = 0
	for d in digits[1::2]:
		doubled = d * 2
		if doubled > 9:
			doubled -= 9
		dispari += doubled
	check = (10 - ((pari + dispari) % 10)) % 10
	return f"{base}{check}"


class PraticheAppTests(TestCase):
	def setUp(self) -> None:
		self.tipo = PraticheTipo.objects.create(
			codice="GEN",
			nome="Generica",
		)
		self.cliente1 = self._create_cliente(1)
		self.cliente2 = self._create_cliente(2)

	def _create_cliente(self, idx: int) -> Cliente:
		anag = Anagrafica.objects.create(
			tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
			ragione_sociale=f"Cliente {idx}",
			codice_fiscale=_make_valid_piva(idx),
		)
		return Cliente.objects.create(anagrafica=anag)

	def _create_pratica(self, cliente: Cliente, **overrides) -> Pratica:
		defaults: dict[str, object] = {
			"cliente": cliente,
			"tipo": self.tipo,
			"oggetto": overrides.get("oggetto", "Pratica di test"),
			"periodo_riferimento": overrides.get("periodo_riferimento", Pratica.PeriodoRif.ANNO),
			"data_riferimento": overrides.get("data_riferimento", date(2024, 1, 1)),
			"stato": overrides.get("stato", Pratica.Stato.APERTA),
		}
		defaults.update(overrides)
		return Pratica.objects.create(**defaults)

	def test_pratica_form_creates_relation_with_parent(self) -> None:
		parent = self._create_pratica(self.cliente1)

		form_data = {
			"cliente": str(self.cliente2.pk),
			"tipo": str(self.tipo.pk),
			"oggetto": "Pratica figlia",
			"stato": Pratica.Stato.APERTA,
			"periodo_riferimento": Pratica.PeriodoRif.ANNO,
			"data_riferimento": "2025-01-01",
			"codice": "",
			"responsabile": "",
			"note": "",
			"tag": "",
			"padre": str(parent.pk),
			"tipo_relazione": PraticaRelazione.TIPI[0][0],
			"figli": [],
		}

		form = PraticaForm(data=form_data)
		self.assertTrue(form.is_valid(), form.errors.as_json())
		child = form.save()

		rel = PraticaRelazione.objects.get(parent=parent, child=child)
		self.assertEqual(rel.tipo, PraticaRelazione.TIPI[0][0])
		available_choices = [choice[0] for choice in form.fields["tipo_relazione"].choices if choice[0] != ""]
		expected_choices = [choice[0] for choice in PraticaRelazione._meta.get_field("tipo").choices]
		self.assertSequenceEqual(available_choices, expected_choices)

	def test_progressivo_recomputed_when_group_changes(self) -> None:
		prima = self._create_pratica(self.cliente1, data_riferimento=date(2024, 1, 1))
		seconda = self._create_pratica(self.cliente1, data_riferimento=date(2024, 6, 1), oggetto="Seconda pratica")

		self.assertEqual(prima.progressivo, 1)
		self.assertEqual(seconda.progressivo, 2)

		codice_originale = seconda.codice
		seconda.data_riferimento = date(2025, 1, 1)
		seconda.save()
		seconda.refresh_from_db()

		self.assertEqual(seconda.progressivo, 1)
		self.assertNotEqual(seconda.codice, codice_originale)

		terza = self._create_pratica(self.cliente1, data_riferimento=date(2025, 2, 1), oggetto="Terza pratica")
		self.assertEqual(terza.progressivo, 2)

		prima.refresh_from_db()
		self.assertEqual(prima.progressivo, 1)

	def test_home_view_orders_scadenze(self) -> None:
		pratica = self._create_pratica(self.cliente1)
		now = timezone.now()
		scadenza_late = AppScadenza.objects.create(
			titolo="Scadenza lontana",
			descrizione="",
		)
		scadenza_late.pratiche.add(pratica)
		ScadenzaOccorrenza.objects.create(
			scadenza=scadenza_late,
			titolo="Scadenza lontana",
			inizio=now + timedelta(days=2),
			metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
			alert_config={"destinatari": "test@example.com"},
		)

		scadenza_soon = AppScadenza.objects.create(
			titolo="Scadenza vicina",
			descrizione="",
		)
		scadenza_soon.pratiche.add(pratica)
		occ_soon = ScadenzaOccorrenza.objects.create(
			scadenza=scadenza_soon,
			titolo="Scadenza vicina",
			inizio=now + timedelta(days=1),
			metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
			alert_config={"destinatari": "test@example.com"},
		)

		response = self.client.get(reverse("pratiche:home"))
		self.assertEqual(response.status_code, 200)
		imminenti = list(response.context["imminenti"])
		self.assertEqual([sc.pk for sc in imminenti[:2]], [occ_soon.pk, scadenza_late.occorrenze.first().pk])
		self.assertLessEqual(len(imminenti), 10)
		self.assertEqual(response.context["pratiche_total"], Pratica.objects.count())

	def test_modifica_pratica_dalla_dettaglio_action(self) -> None:
		pratica = self._create_pratica(self.cliente1)
		user = get_user_model().objects.create_user(
			username="operatore",
			email="operatore@example.com",
			password="password-sicura",
			is_staff=True,
		)
		self.client.force_login(user)

		detail_url = reverse("pratiche:dettaglio", args=[pratica.pk])
		mod_url = reverse("pratiche:modifica", args=[pratica.pk])

		response = self.client.get(detail_url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'href="{mod_url}"')

		form_response = self.client.get(mod_url)
		self.assertEqual(form_response.status_code, 200)

		post_data = {
			"cliente": str(pratica.cliente_id),
			"tipo": str(pratica.tipo_id),
			"oggetto": "Pratica aggiornata via test",
			"stato": Pratica.Stato.LAVORAZIONE,
			"responsabile": "",
			"periodo_riferimento": pratica.periodo_riferimento,
			"data_riferimento": pratica.data_riferimento.isoformat(),
			"codice": pratica.codice,
			"data_chiusura": "",
			"note": "Modifica eseguita dal test.",
			"tag": "",
			"padre": "",
			"tipo_relazione": "",
			"figli": [],
		}

		post_response = self.client.post(mod_url, post_data, follow=True)
		self.assertRedirects(post_response, detail_url)

		pratica.refresh_from_db()
		self.assertEqual(pratica.oggetto, "Pratica aggiornata via test")
		self.assertEqual(pratica.stato, Pratica.Stato.LAVORAZIONE)
		self.assertContains(post_response, "Pratica aggiornata correttamente.")
