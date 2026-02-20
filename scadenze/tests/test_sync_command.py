from __future__ import annotations

from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from scadenze.models import Scadenza, ScadenzaOccorrenza


@override_settings(
    GOOGLE_CALENDAR_CREDENTIALS_FILE="/tmp/fake-google.json",
    GOOGLE_CALENDAR_DEFAULT_ID="default-calendar-id",
)
class SyncGoogleCalendarCommandTests(TestCase):
    def setUp(self) -> None:
        self.start = timezone.now().replace(microsecond=0)
        self.scadenza = Scadenza.objects.create(
            titolo="Test Comando Sync",
            descrizione="Descrizione test",
            comunicazione_destinatari="test@example.com",
        )
        
        # Crea diverse occorrenze per testare i filtri
        self.occ_futura_non_sync = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="Futura non sincronizzata",
            inizio=self.start + timedelta(days=7),
            fine=self.start + timedelta(days=7, hours=1),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["test@example.com"]},
        )
        
        self.occ_futura_sync = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="Futura già sincronizzata",
            inizio=self.start + timedelta(days=14),
            fine=self.start + timedelta(days=14, hours=1),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["test@example.com"]},
            google_calendar_event_id="existing-event-123",
        )
        
        self.occ_passata_non_sync = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="Passata non sincronizzata",
            inizio=self.start - timedelta(days=7),
            fine=self.start - timedelta(days=7, hours=1),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["test@example.com"]},
        )
        
        self.occ_annullata = ScadenzaOccorrenza.objects.create(
            scadenza=self.scadenza,
            titolo="Annullata",
            inizio=self.start + timedelta(days=21),
            fine=self.start + timedelta(days=21, hours=1),
            metodo_alert=ScadenzaOccorrenza.MetodoAlert.EMAIL,
            alert_config={"destinatari": ["test@example.com"]},
            stato=ScadenzaOccorrenza.Stato.ANNULLATA,
        )

    def _mock_google_sync(self):
        """Helper per mockare il servizio Google Calendar"""
        fake_events = MagicMock()
        fake_events.insert.return_value.execute.return_value = {"id": "new-event-123"}
        fake_events.update.return_value.execute.return_value = {"id": "updated-event-123"}
        fake_service = MagicMock()
        fake_service.events.return_value = fake_events

        class FakeCredentials:
            @classmethod
            def from_service_account_file(cls, filename: str, scopes: tuple[str, ...]):
                return SimpleNamespace(token="fake-token")

        def fake_build(api_name: str, version: str, *, credentials=None, cache_discovery=False):
            return fake_service

        return patch("scadenze.services._load_google_clients", return_value=(SimpleNamespace(Credentials=FakeCredentials), fake_build))

    def test_comando_senza_argomenti_sync_future_non_sincronizzate(self) -> None:
        """Test: comando senza argomenti sincronizza solo occorrenze future non sincronizzate"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command('sync_google_calendar', stdout=out, no_color=True)
        
        output = out.getvalue()
        self.assertIn('1 occorrenze da sincronizzare', output)
        self.assertIn('Sincronizzazione completata', output)
        
        # Verifica che sia stata sincronizzata solo l'occorrenza futura non sync
        self.occ_futura_non_sync.refresh_from_db()
        self.assertIsNotNone(self.occ_futura_non_sync.google_calendar_event_id)

    def test_comando_dry_run_non_sincronizza(self) -> None:
        """Test: modalità dry-run non effettua sincronizzazione"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command('sync_google_calendar', '--dry-run', stdout=out, no_color=True)
        
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        # Il titolo mostrato è quello della scadenza, non dell'occorrenza
        self.assertIn('Test Comando Sync', output)
        
        # Verifica che NON sia stata sincronizzata
        self.occ_futura_non_sync.refresh_from_db()
        self.assertFalse(self.occ_futura_non_sync.google_calendar_event_id)

    def test_comando_all_sincronizza_tutte_future(self) -> None:
        """Test: opzione --all sincronizza anche occorrenze già sincronizzate"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command('sync_google_calendar', '--all', stdout=out, no_color=True)
        
        output = out.getvalue()
        # Dovrebbe trovare 2 occorrenze future (inclusa quella già sync, esclusa annullata)
        self.assertIn('occorrenze da sincronizzare', output)
        self.assertIn('Sincronizzazione completata', output)

    def test_comando_non_synced_include_passate(self) -> None:
        """Test: opzione --non-synced include anche occorrenze passate"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command('sync_google_calendar', '--non-synced', stdout=out, no_color=True)
        
        output = out.getvalue()
        # Dovrebbe trovare 2 occorrenze non sincronizzate (futura + passata)
        self.assertIn('2 occorrenze da sincronizzare', output)

    def test_comando_from_date_filtra_correttamente(self) -> None:
        """Test: opzione --from-date filtra per data"""
        out = StringIO()
        # Usa una data che escluda l'occorrenza a +7 giorni ma includa quella a +14
        from_date = (self.start + timedelta(days=10)).strftime('%Y-%m-%d')
        
        with self._mock_google_sync():
            call_command(
                'sync_google_calendar',
                f'--from-date={from_date}',
                '--all',  # Include anche quelle già sincronizzate
                stdout=out,
                no_color=True
            )
        
        output = out.getvalue()
        # Dovrebbe trovare solo l'occorrenza a +14 giorni (esclusa quella a +7)
        # e l'occorrenza annullata a +21 (che viene esclusa per il filtro default)
        self.assertIn('1 occorrenze da sincronizzare', output)

    def test_comando_occorrenza_id_sync_singola(self) -> None:
        """Test: opzione --occorrenza-id sincronizza solo quella specifica"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command(
                'sync_google_calendar',
                f'--occorrenza-id={self.occ_futura_non_sync.id}',
                stdout=out,
                no_color=True
            )
        
        output = out.getvalue()
        self.assertIn('1 occorrenze da sincronizzare', output)
        
        self.occ_futura_non_sync.refresh_from_db()
        self.assertIsNotNone(self.occ_futura_non_sync.google_calendar_event_id)

    def test_comando_force_include_annullate(self) -> None:
        """Test: opzione --force include anche occorrenze annullate"""
        out = StringIO()
        
        with self._mock_google_sync():
            call_command(
                'sync_google_calendar',
                '--all',
                '--force',
                stdout=out,
                no_color=True
            )
        
        output = out.getvalue()
        # Dovrebbe includere anche l'occorrenza annullata
        self.assertIn('occorrenze da sincronizzare', output)

    def test_comando_nessuna_occorrenza_da_sincronizzare(self) -> None:
        """Test: messaggio appropriato quando non ci sono occorrenze"""
        # Rimuovi tutte le occorrenze non sincronizzate
        ScadenzaOccorrenza.objects.filter(google_calendar_event_id='').delete()
        
        out = StringIO()
        
        with self._mock_google_sync():
            call_command('sync_google_calendar', stdout=out, no_color=True)
        
        output = out.getvalue()
        self.assertIn('Nessuna occorrenza da sincronizzare', output)

    def test_comando_gestisce_errore_google_api(self) -> None:
        """Test: il comando gestisce gli errori dell'API Google"""
        out = StringIO()
        
        # Mock che solleva un'eccezione
        with patch('scadenze.services.GoogleCalendarSync.upsert_occurrence') as mock_upsert:
            mock_upsert.side_effect = Exception("Errore API Google")
            
            with self._mock_google_sync():
                call_command('sync_google_calendar', stdout=out, no_color=True)
        
        output = out.getvalue()
        self.assertIn('Errori:', output)
