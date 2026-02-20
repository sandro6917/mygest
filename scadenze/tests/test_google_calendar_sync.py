from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db.models.signals import post_save, post_delete

from scadenze.models import Scadenza, ScadenzaNotificaLog, ScadenzaOccorrenza, _sync_calendar_after_save, _delete_calendar_event
from scadenze.services import GoogleCalendarSync


@override_settings(
    GOOGLE_CALENDAR_CREDENTIALS_FILE="/tmp/fake-google.json",
    GOOGLE_CALENDAR_DEFAULT_ID="default-calendar-id",
)
class GoogleCalendarSyncTests(TestCase):
    def setUp(self) -> None:
        # Disconnetto i signal per controllo manuale
        post_save.disconnect(
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
        )
        post_delete.disconnect(
            _delete_calendar_event,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_delete_google",
        )
        self.addCleanup(
            post_save.connect,
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
        )
        self.addCleanup(
            post_delete.connect,
            _delete_calendar_event,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_delete_google",
        )
        
        self.start = timezone.now().replace(microsecond=0)
        self.scadenza = Scadenza.objects.create(
            titolo="Verifica sincronizzazione",
            descrizione="Promemoria importante",
            comunicazione_destinatari="team@example.com",
            google_calendar_calendar_id="",
        )
        self.occorrenza = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="Riunione di prova",
            descrizione="Dettagli riunione",
            inizio=self.start,
            fine=self.start + timedelta(hours=2),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["team@example.com"]},
        )

    def test_upsert_occurrence_crea_nuovo_evento(self) -> None:
        """Test: creazione di un nuovo evento su Google Calendar"""
        fake_events = MagicMock()
        fake_events.insert.return_value.execute.return_value = {"id": "event-123"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            called_with: tuple[str, tuple[str, ...]] | None = None

            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                cls.called_with = (filename, tuple(scopes))
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            sync = GoogleCalendarSync()
            sync.upsert_occurrence(self.occorrenza)

        self.assertEqual(
            FakeCredentials.called_with,
            (settings.GOOGLE_CALENDAR_CREDENTIALS_FILE, GoogleCalendarSync.SCOPES),
        )
        fake_service.events.assert_called_once_with()
        fake_events.insert.assert_called_once()
        fake_events.update.assert_not_called()

        _, insert_kwargs = fake_events.insert.call_args
        self.assertEqual(insert_kwargs["calendarId"], "default-calendar-id")
        body = insert_kwargs["body"]
        self.assertEqual(body["summary"], "Riunione di prova")
        self.assertEqual(body["description"], "Dettagli riunione")
        self.assertEqual(body["start"]["timeZone"], settings.TIME_ZONE)
        self.assertEqual(body["start"]["dateTime"], timezone.localtime(self.start).isoformat())
        self.assertEqual(body["end"]["dateTime"], timezone.localtime(self.start + timedelta(hours=2)).isoformat())

        self.occorrenza.refresh_from_db()
        self.assertEqual(self.occorrenza.google_calendar_event_id, "event-123")
        self.assertIsNotNone(self.occorrenza.google_calendar_synced_at)

        log = ScadenzaNotificaLog.objects.filter(
            occorrenza=self.occorrenza,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.payload.get("calendar_id"), "default-calendar-id")

    def test_upsert_occurrence_aggiorna_evento_esistente(self) -> None:
        """Test: aggiornamento di un evento già esistente su Google Calendar"""
        # Preimposta l'ID dell'evento esistente
        self.occorrenza.google_calendar_event_id = "existing-event-456"
        self.occorrenza.save()

        fake_events = MagicMock()
        fake_events.update.return_value.execute.return_value = {"id": "existing-event-456"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            sync = GoogleCalendarSync()
            sync.upsert_occurrence(self.occorrenza)

        # Verifica che sia stato chiamato update e non insert
        fake_events.update.assert_called_once()
        fake_events.insert.assert_not_called()

        _, update_kwargs = fake_events.update.call_args
        self.assertEqual(update_kwargs["calendarId"], "default-calendar-id")
        self.assertEqual(update_kwargs["eventId"], "existing-event-456")
        
        self.occorrenza.refresh_from_db()
        self.assertIsNotNone(self.occorrenza.google_calendar_synced_at)

    def test_delete_occurrence_elimina_evento(self) -> None:
        """Test: eliminazione di un evento da Google Calendar"""
        self.occorrenza.google_calendar_event_id = "event-to-delete"
        self.occorrenza.save()

        fake_events = MagicMock()
        fake_events.delete.return_value.execute.return_value = {}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            sync = GoogleCalendarSync()
            sync.delete_occurrence(self.occorrenza)

        fake_events.delete.assert_called_once()
        _, delete_kwargs = fake_events.delete.call_args
        self.assertEqual(delete_kwargs["calendarId"], "default-calendar-id")
        self.assertEqual(delete_kwargs["eventId"], "event-to-delete")

        # Verifica che sia stato creato un log
        log = ScadenzaNotificaLog.objects.filter(
            occorrenza=self.occorrenza,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
            messaggio__contains="eliminato",
        ).first()
        self.assertIsNotNone(log)

    def test_sync_con_calendario_custom(self) -> None:
        """Test: sincronizzazione con un calendario personalizzato (non default)"""
        self.scadenza.google_calendar_calendar_id = "custom-calendar-id"
        self.scadenza.save()

        fake_events = MagicMock()
        fake_events.insert.return_value.execute.return_value = {"id": "event-789"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            sync = GoogleCalendarSync()
            sync.upsert_occurrence(self.occorrenza)

        _, insert_kwargs = fake_events.insert.call_args
        self.assertEqual(insert_kwargs["calendarId"], "custom-calendar-id")

    def test_signal_automatico_su_save(self) -> None:
        """Test: il signal post_save attiva automaticamente la sincronizzazione"""
        # Riconnetto il signal per questo test
        post_save.connect(
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
        )

        fake_events = MagicMock()
        fake_events.insert.return_value.execute.return_value = {"id": "signal-event"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            # Creo una nuova occorrenza - dovrebbe triggerare il signal
            nuova_occorrenza = ScadenzaOccorrenza.objects.create(
                scadenza=self.scadenza,
                titolo="Test Signal",
                inizio=self.start + timedelta(days=1),
                fine=self.start + timedelta(days=1, hours=1),
                metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
                alert_config={"destinatari": ["test@example.com"]},
            )

        # Verifica che l'evento sia stato creato automaticamente
        fake_events.insert.assert_called_once()
        nuova_occorrenza.refresh_from_db()
        self.assertEqual(nuova_occorrenza.google_calendar_event_id, "signal-event")

        # Disconnetto di nuovo
        post_save.disconnect(
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
        )

    def test_configurazione_mancante_solleva_errore(self) -> None:
        """Test: errore se le credenziali Google non sono configurate"""
        with override_settings(GOOGLE_CALENDAR_CREDENTIALS_FILE=None):
            with self.assertRaises(ImproperlyConfigured):
                GoogleCalendarSync()

    def test_occorrenza_annullata_non_viene_sincronizzata(self) -> None:
        """Test: occorrenze annullate non vengono sincronizzate"""
        self.occorrenza.stato = ScadenzaOccorrenza.Stato.ANNULLATA
        self.occorrenza.save()

        fake_events = MagicMock()
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            # Chiamo direttamente il signal handler
            _sync_calendar_after_save(
                sender=ScadenzaOccorrenza,
                instance=self.occorrenza,
                created=False
            )

        # Non dovrebbe essere chiamato nessun metodo sul servizio
        fake_events.insert.assert_not_called()
        fake_events.update.assert_not_called()

    def test_titolo_e_descrizione_fallback_da_scadenza(self) -> None:
        """Test: se l'occorrenza non ha titolo/descrizione, usa quelli della scadenza"""
        occorrenza_senza_titolo = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="",  # Vuoto
            descrizione="",  # Vuoto
            inizio=self.start + timedelta(days=2),
            fine=self.start + timedelta(days=2, hours=1),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["test@example.com"]},
        )

        fake_events = MagicMock()
        fake_events.insert.return_value.execute.return_value = {"id": "fallback-event"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        with patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build)):
            sync = GoogleCalendarSync()
            sync.upsert_occurrence(occorrenza_senza_titolo)

        _, insert_kwargs = fake_events.insert.call_args
        body = insert_kwargs["body"]
        # Dovrebbe usare il titolo e la descrizione della scadenza
        self.assertEqual(body["summary"], "Verifica sincronizzazione")
        self.assertEqual(body["description"], "Promemoria importante")