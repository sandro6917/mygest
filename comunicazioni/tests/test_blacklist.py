import io
from email.message import EmailMessage
import zipfile

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from comunicazioni.admin import EmailImportAdmin
from comunicazioni.models import (
    Comunicazione,
    EmailImport,
    EmailImportBlacklist,
    Mailbox,
)
from comunicazioni.tasks import _should_import


class EmailImportBlacklistAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EmailImportAdmin(EmailImport, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.mailbox = Mailbox.objects.create(
            nome="Support",
            host="imap.example.com",
            porta=993,
            username="support@example.com",
            password="secret",
        )

    def _build_admin_request(self):
        request = self.factory.post("/admin/comunicazioni/emailimport/")
        request.user = self.user
        request.session = self.client.session
        request._messages = FallbackStorage(request)
        return request

    def test_action_adds_unique_senders(self):
        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-1@example.com>",
            mittente="Sender@example.com",
        )
        request = self._build_admin_request()

        queryset = EmailImport.objects.filter(pk=email_import.pk)
        self.admin.aggiungi_mittenti_blacklist(request, queryset)

        self.assertTrue(
            EmailImportBlacklist.objects.filter(email="sender@example.com").exists()
        )

    def test_crea_comunicazione_ricevuta_crea_record_e_allegato(self):
        msg = EmailMessage()
        msg["Subject"] = "Risposta Cliente"
        msg["From"] = "cliente@example.com"
        msg["To"] = "support@example.com"
        msg.set_content("Testo semplice del messaggio")
        msg.add_alternative("<p>HTML body</p>", subtype="html")
        attachment_content = b"allegato di prova"
        msg.add_attachment(attachment_content, maintype="text", subtype="plain", filename="nota.txt")

        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-2@example.com>",
            mittente="cliente@example.com",
            destinatari="support@example.com",
            oggetto="Risposta Cliente",
            raw_message=msg.as_bytes(),
        )

        request = self._build_admin_request()

        queryset = EmailImport.objects.filter(pk=email_import.pk)
        self.admin.crea_comunicazione_ricevuta(request, queryset)

        email_import.refresh_from_db()
        self.assertEqual(email_import.stato_import, "processato")
        self.assertEqual(email_import.processato_da, self.user)
        self.assertIsNotNone(email_import.processato_il)
        self.assertIsNotNone(email_import.comunicazione)

        comunicazione = email_import.comunicazione
        self.assertEqual(comunicazione.stato, "ricevuta")
        self.assertEqual(comunicazione.direzione, Comunicazione.Direzione.IN)
        self.assertTrue(comunicazione.bloccata)
        self.assertEqual(comunicazione.oggetto, "Risposta Cliente")
        self.assertIn("Testo semplice", comunicazione.corpo)
        self.assertIn("HTML body", comunicazione.corpo_html)
        self.assertEqual(comunicazione.email_message_id, "<msg-2@example.com>")

        allegati = list(comunicazione.allegati.all())
        self.assertEqual(len(allegati), 1)
        allegato = allegati[0]
        self.assertEqual(allegato.nome_file, "nota.txt")
        self.assertTrue(allegato.file)
        with allegato.file.open("rb") as handle:
            self.assertEqual(handle.read(), attachment_content)
        allegato.file.delete(save=False)

    def test_crea_comunicazione_ricevuta_genera_nomi_per_allegati_senza_filename(self):
        msg = EmailMessage()
        msg["Subject"] = "Risposta" 
        msg["From"] = "client@example.com"
        msg["To"] = "support@example.com"
        msg.set_content("Body")
        msg.add_attachment(b"uno", maintype="text", subtype="plain", filename="nota.txt")
        msg.add_attachment(b"due", maintype="application", subtype="octet-stream")

        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-3@example.com>",
            mittente="client@example.com",
            destinatari="support@example.com",
            oggetto="Risposta",
            raw_message=msg.as_bytes(),
        )

        request = self._build_admin_request()
        self.admin.crea_comunicazione_ricevuta(request, EmailImport.objects.filter(pk=email_import.pk))

        comunicazione = EmailImport.objects.get(pk=email_import.pk).comunicazione
        allegati = list(comunicazione.allegati.order_by("id"))
        self.assertEqual(len(allegati), 2)
        filenames = [a.nome_file for a in allegati]
        self.assertIn("nota.txt", filenames)
        self.assertTrue(any(name.startswith("allegato-") and name.endswith(".bin") for name in filenames))
        for allegato in allegati:
            allegato.file.delete(save=False)

    def test_crea_comunicazione_ricevuta_salta_email_senza_raw_message(self):
        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-4@example.com>",
            mittente="client@example.com",
        )

        request = self._build_admin_request()
        with self.assertLogs("comunicazioni.admin", level="WARNING") as log_ctx:
            self.admin.crea_comunicazione_ricevuta(request, EmailImport.objects.filter(pk=email_import.pk))

        email_import.refresh_from_db()
        self.assertIsNone(email_import.comunicazione)
        self.assertEqual(email_import.stato_import, "nuovo")

        stored_messages = [m.message for m in list(request._messages)]
        self.assertIn("non ha raw_message", stored_messages[0])
        self.assertIn("Nessuna nuova comunicazione", stored_messages[-1])
        self.assertTrue(any("senza raw_message" in entry for entry in log_ctx.output))

    def test_scarica_eml_restituisce_zip(self):
        msg = EmailMessage()
        msg["Subject"] = "Test"
        msg["From"] = "a@example.com"
        msg["To"] = "b@example.com"
        msg.set_content("Body")
        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-zip@example.com>",
            raw_message=msg.as_bytes(),
        )

        request = self._build_admin_request()
        response = self.admin.scarica_eml(request, EmailImport.objects.filter(pk=email_import.pk))

        self.assertIsNotNone(response)
        self.assertEqual(response["Content-Type"], "application/zip")
        zip_buffer = io.BytesIO(response.content)
        archive = zipfile.ZipFile(zip_buffer)
        names = archive.namelist()
        self.assertEqual(len(names), 1)
        self.assertTrue(names[0].endswith(".eml"))
        self.assertEqual(archive.read(names[0]), msg.as_bytes())

    def test_scarica_eml_senza_raw_message_mostra_warning(self):
        email_import = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<msg-empty@example.com>",
        )

        request = self._build_admin_request()
        with self.assertLogs("comunicazioni.admin", level="WARNING") as log_ctx:
            response = self.admin.scarica_eml(request, EmailImport.objects.filter(pk=email_import.pk))

        self.assertIsNone(response)
        stored_messages = [m.message for m in list(request._messages)]
        self.assertIn("Nessuna email con raw_message", stored_messages[-1])
        self.assertTrue(any("senza raw_message" in entry for entry in log_ctx.output))

    def test_elimina_email_blacklist_case_insensitive(self):
        EmailImportBlacklist.objects.create(email="administrator@pclink.com.eg")
        keep = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<keep@example.com>",
            mittente="ok@example.com",
        )
        delete_me = EmailImport.objects.create(
            mailbox=self.mailbox,
            message_id="<del@example.com>",
            mittente="Administrator@pclink.com.eg",
        )

        request = self._build_admin_request()
        queryset = EmailImport.objects.filter(pk__in=[keep.pk, delete_me.pk])

        self.admin.elimina_email_blacklist(request, queryset)

        self.assertTrue(EmailImport.objects.filter(pk=keep.pk).exists())
        self.assertFalse(EmailImport.objects.filter(pk=delete_me.pk).exists())
        stored_messages = [m.message for m in list(request._messages)]
        self.assertIn("Eliminate 1 email", stored_messages[-1])


class EmailImportBlacklistTaskTests(TestCase):
    def setUp(self):
        self.mailbox = Mailbox.objects.create(
            nome="Info",
            host="imap.example.com",
            porta=993,
            username="info@example.com",
            password="secret",
        )

    def test_should_import_respects_blacklist(self):
        blacklist = {"blocked@example.com"}
        self.assertFalse(
            _should_import(self.mailbox, "blocked@example.com", "Subject", blacklist=blacklist)
        )
        self.assertTrue(
            _should_import(self.mailbox, "ok@example.com", "Subject", blacklist=blacklist)
        )
