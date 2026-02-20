from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from anagrafiche.models import (
    Anagrafica,
    EmailContatto,
    MailingList,
    MailingListMembership,
    MailingListUnsubscribeToken,
)
from comunicazioni.models import Comunicazione


class MailingListPrivacyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("op", "op@example.com", "pass1234")
        self.client.force_login(self.user)
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="Cliente Spa",
            codice_fiscale="12345678901",
            partita_iva="12345678901",
        )
        self.contact_ok = EmailContatto.objects.create(
            anagrafica=self.anagrafica,
            nominativo="Consentito",
            email="ok@example.com",
            marketing_consent=True,
        )
        self.contact_no = EmailContatto.objects.create(
            anagrafica=self.anagrafica,
            nominativo="NoConsenso",
            email="no@example.com",
            marketing_consent=False,
        )
        self.lista = MailingList.objects.create(
            nome="Marketing",
            finalita=MailingList.Finalita.MARKETING,
        )
        MailingListMembership.objects.create(mailing_list=self.lista, contatto=self.contact_ok)
        MailingListMembership.objects.create(mailing_list=self.lista, contatto=self.contact_no)

    def test_marketing_list_filters_contacts_without_consent(self):
        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
            direzione=Comunicazione.Direzione.OUT,
            oggetto="Test",
            corpo="",
            destinatari="",
        )
        comunicazione.liste_destinatari.add(self.lista)
        destinatari = comunicazione.get_destinatari_lista()
        self.assertIn("ok@example.com", destinatari)
        self.assertNotIn("no@example.com", destinatari)

    def test_preference_request_creates_token(self):
        url = reverse("comunicazioni:mailinglist-preferences")
        resp = self.client.post(url, {"email": "ok@example.com", "lista": self.lista.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(MailingListUnsubscribeToken.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        token = MailingListUnsubscribeToken.objects.first()
        self.assertIn(str(token.token), mail.outbox[0].body)

    def test_unsubscribe_flow_revokes_consent(self):
        token = self.lista.issue_unsubscribe_token(contatto=self.contact_ok)
        url = reverse("comunicazioni:unsubscribe-confirm", args=[token.token])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.contact_ok.refresh_from_db()
        self.assertFalse(self.contact_ok.marketing_consent)
        membership = MailingListMembership.objects.get(mailing_list=self.lista, contatto=self.contact_ok)
        self.assertIsNotNone(membership.disiscritto_il)
        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)
