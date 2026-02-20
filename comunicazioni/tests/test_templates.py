from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from anagrafiche.models import Anagrafica
from comunicazioni.forms import ComunicazioneForm
from comunicazioni.models import Comunicazione
from comunicazioni.models_template import FirmaComunicazione, TemplateComunicazione, TemplateContextField
from comunicazioni.utils_template import merge_contenuti, render_firma_comunicazione, render_template_comunicazione


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class ComunicazioniTemplateViewTests(TestCase):
    def setUp(self):
        static_patch = patch("django.contrib.staticfiles.storage.staticfiles_storage")
        self.mock_static_storage = static_patch.start()
        self.addCleanup(static_patch.stop)
        self.mock_static_storage.url.side_effect = lambda path: f"/static/{path}"
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="pass1234",
            first_name="Test",
            last_name="User",
        )
        self.client.force_login(self.user)
        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="Comunicazioni Test S.p.A.",
            codice_fiscale="10000000009",
            partita_iva="10000000009",
        )
        self.template = TemplateComunicazione.objects.create(
            nome="Avviso pagamento",
            oggetto="Avviso per {{ anagrafica.ragione_sociale }}",
            corpo_testo="Gentile {{ anagrafica.ragione_sociale }},",
            corpo_html="<p>Gentile {{ anagrafica.ragione_sociale }},</p>",
            attivo=True,
        )
        self.firma = FirmaComunicazione.objects.create(
            nome="Firma standard",
            corpo_testo="Lo staff MyGest",
            corpo_html="<p><strong>Lo staff MyGest</strong></p>",
            attivo=True,
        )

    def _base_post_data(self):
        return {
            "tipo": Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            "direzione": Comunicazione.Direzione.OUT,
            "template": str(self.template.pk),
            "firma": str(self.firma.pk),
            "oggetto": "",
            "corpo": "",
            "corpo_html": "",
            "mittente": "",
            "destinatari": "destinatario@example.com",
            "anagrafica": str(self.anagrafica.pk),
            "documento_protocollo": "",
            "contatti_destinatari": [],
            "liste_destinatari": [],
        }

    def test_applica_template_popola_corpo(self):
        url = reverse("comunicazioni:create")
        data = self._base_post_data()
        data["applica_template"] = "1"

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.errors)

        context = {
            "anagrafica": self.anagrafica,
            "operatore": self.user,
            "utente": self.user,
            "user": self.user,
        }
        expected = merge_contenuti(
            render_template_comunicazione(self.template, context),
            render_firma_comunicazione(self.firma, context),
        )

        self.assertEqual(form["oggetto"].value(), expected.oggetto)
        self.assertEqual(form["corpo"].value(), expected.corpo_testo)
        self.assertEqual(form["corpo_html"].value(), expected.corpo_html)

    def test_creazione_comunicazione_con_template_e_firma(self):
        url = reverse("comunicazioni:create")
        context = {
            "anagrafica": self.anagrafica,
            "operatore": self.user,
            "utente": self.user,
            "user": self.user,
        }
        rendered = merge_contenuti(
            render_template_comunicazione(self.template, context),
            render_firma_comunicazione(self.firma, context),
        )

        data = self._base_post_data()
        data.update(
            {
                "oggetto": rendered.oggetto,
                "corpo": rendered.corpo_testo,
                "corpo_html": rendered.corpo_html,
                "mittente": "mittente@example.com",
            }
        )

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        comunicazione = Comunicazione.objects.latest("id")
        self.assertEqual(comunicazione.template, self.template)
        self.assertEqual(comunicazione.firma, self.firma)
        self.assertEqual(comunicazione.corpo, rendered.corpo_testo)
        self.assertEqual(comunicazione.corpo_html, rendered.corpo_html)
        self.assertEqual(comunicazione.oggetto, rendered.oggetto)

    def test_invio_con_corpo_html_invia_alternativa(self):
        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            direzione=Comunicazione.Direzione.OUT,
            oggetto="Comunicazione con HTML",
            corpo="Gentile cliente,",
            corpo_html="<p>Gentile cliente,</p>",
            mittente="mittente@example.com",
            destinatari="destinatario@example.com",
            template=self.template,
            firma=self.firma,
        )

        url = reverse("comunicazioni:send", args=[comunicazione.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        comunicazione.refresh_from_db()
        self.assertEqual(comunicazione.stato, "inviata")
        self.assertIsNotNone(comunicazione.data_invio)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.body, "Gentile cliente,")
        self.assertEqual(message.alternatives[0][1], "text/html")
        self.assertIn("<p>Gentile cliente,</p>", message.alternatives[0][0])

    def test_context_fields_are_saved_and_auto_filled(self):
        TemplateContextField.objects.create(
            template=self.template,
            key="numero_pratica",
            label="Numero pratica",
            field_type=TemplateContextField.FieldType.TEXT,
            required=False,
        )
        TemplateContextField.objects.create(
            template=self.template,
            key="ragione",
            label="Ragione sociale",
            field_type=TemplateContextField.FieldType.TEXT,
            source_path="anagrafica.ragione_sociale",
            required=False,
        )

        url = reverse("comunicazioni:create")
        data = self._base_post_data()
        data.update(
            {
                "oggetto": "Manuale",
                "corpo": "Test corpo",
                "mittente": "mittente@example.com",
            }
        )
        data[ComunicazioneForm.context_field_name("numero_pratica")] = "PR-001"
        data[ComunicazioneForm.context_field_name("ragione")] = ""

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        comunicazione = Comunicazione.objects.latest("id")
        self.assertEqual(comunicazione.dati_template.get("numero_pratica"), "PR-001")
        comunicazione.anagrafica = self.anagrafica
        context = comunicazione.get_template_context()
        self.assertEqual(context["numero_pratica"], "PR-001")
        self.assertEqual(context["ragione"], self.anagrafica.ragione_sociale)

    def test_render_content_applica_firma_senza_template(self):
        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
            direzione=Comunicazione.Direzione.OUT,
            oggetto="Messaggio manuale",
            corpo="Corpo principale",
            mittente="mittente@example.com",
            destinatari="dest@example.com",
            firma=self.firma,
        )

        comunicazione.render_content()

        self.assertIn(self.firma.get_text(), comunicazione.corpo)
        self.assertTrue(comunicazione.corpo.endswith(self.firma.get_text()))
        self.assertIn("Lo staff MyGest", comunicazione.corpo)
        self.assertIn("Lo staff MyGest", comunicazione.corpo_html)
        self.assertIn("<strong>Lo staff MyGest</strong>", comunicazione.corpo_html)