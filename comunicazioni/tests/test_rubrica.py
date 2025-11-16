from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from anagrafiche.models import Anagrafica, EmailContatto, MailingList, MailingListMembership, MailingListIndirizzo
from comunicazioni.forms import ComunicazioneForm
from comunicazioni.models import Comunicazione


class ComunicazioneRubricaFormTests(TestCase):
    def setUp(self):
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="Test S.r.l.",
            codice_fiscale="10000000009",
            partita_iva="10000000009",
        )
        self.contatto = EmailContatto.objects.create(
            anagrafica=self.anagrafica,
            nominativo="Mario Rossi",
            email="mario.rossi@example.com",
            tipo=EmailContatto.Tipo.COMMERCIALE,
            is_preferito=True,
        )
        self.lista = MailingList.objects.create(
            nome="Clienti Premium",
            proprietario=self.anagrafica,
        )
        MailingListMembership.objects.create(mailing_list=self.lista, contatto=self.contatto)
        MailingListIndirizzo.objects.create(mailing_list=self.lista, email="extra@example.com", nominativo="Extra")

    def test_form_unisce_destinatari_con_rubrica(self):
        form = ComunicazioneForm(
            data={
                "tipo": Comunicazione.TipoComunicazione.INFORMATIVA,
                "direzione": Comunicazione.Direzione.OUT,
                "oggetto": "Comunicazione test",
                "corpo": "Test",
                "mittente": "ufficio@example.com",
                "destinatari": "manual@example.com",
                "anagrafica": self.anagrafica.pk,
                "contatti_destinatari": [str(self.contatto.pk)],
                "liste_destinatari": [str(self.lista.pk)],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        comunicazione = form.save()
        destinatari = comunicazione.get_destinatari_lista()
        self.assertIn("manual@example.com", destinatari)
        self.assertIn("mario.rossi@example.com", destinatari)
        self.assertIn("extra@example.com", destinatari)
        self.assertEqual(len(destinatari), len(set(destinatari)))


class ComunicazioniApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("tester", "tester@example.com", "password123")
        self.client.force_login(self.user)
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="API Spa",
            codice_fiscale="20000000007",
            partita_iva="20000000007",
        )
        self.comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
            direzione=Comunicazione.Direzione.OUT,
            oggetto="API",
            corpo="",
            mittente="api@example.com",
            destinatari="dest@example.com",
            anagrafica=self.anagrafica,
        )

    def test_lista_comunicazioni_api(self):
        url = reverse("comunicazioni-api:api-comunicazioni-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertGreaterEqual(len(payload.get("results", [])), 1)
        ids = [item["id"] for item in payload["results"]]
        self.assertIn(self.comunicazione.pk, ids)


class ComunicazioniGraphQLTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("graphql", "graphql@example.com", "password123")
        self.client.force_login(self.user)
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="GraphQL Spa",
            codice_fiscale="30000000005",
            partita_iva="30000000005",
        )
        self.comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
            direzione=Comunicazione.Direzione.IN,
            oggetto="GraphQL",
            corpo="",
            mittente="graphql@example.com",
            destinatari="team@example.com",
            anagrafica=self.anagrafica,
        )

    def test_query_comunicazioni(self):
        query = """
        query {
          tutteLeComunicazioni {
            id
            oggetto
            destinatariCalcolati
          }
        }
        """
        response = self.client.post(
            "/graphql/",
            data={"query": query},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        data = payload.get("data", {})
        comunicazioni = data.get("tutteLeComunicazioni", [])
        self.assertTrue(any(c["oggetto"] == "GraphQL" for c in comunicazioni))