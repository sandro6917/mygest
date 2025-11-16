from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db.models.signals import post_save

from scadenze.models import Scadenza, ScadenzaNotificaLog, ScadenzaOccorrenza, _sync_calendar_after_save
from scadenze.services import GoogleCalendarSync


@override_settings(
    GOOGLE_CALENDAR_CREDENTIALS_FILE="/tmp/fake-google.json",
    GOOGLE_CALENDAR_DEFAULT_ID="default-calendar-id",
)
class GoogleCalendarSyncTests(TestCase):
    def setUp(self) -> None:
        post_save.disconnect(
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
        )
        self.addCleanup(
            post_save.connect,
            _sync_calendar_after_save,
            sender=ScadenzaOccorrenza,
            dispatch_uid="scadenze_sync_google",
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

    def test_upsert_occurrence_pushes_event_to_google_calendar(self) -> None:
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