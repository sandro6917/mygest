"""Test per posticipo festività italiane e alert multipli in batch nella generazione occorrenze."""
import pytest
from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from model_bakery import baker

from scadenze.holidays_utils import easter_sunday, is_italian_holiday, next_business_day
from scadenze.models import Scadenza, ScadenzaAlert, ScadenzaOccorrenza


class TestItalianHolidays:
    def test_easter_known_dates(self):
        assert easter_sunday(2024) == date(2024, 3, 31)
        assert easter_sunday(2025) == date(2025, 4, 20)
        assert easter_sunday(2026) == date(2026, 4, 5)

    def test_fixed_holidays(self):
        assert is_italian_holiday(date(2026, 1, 1))
        assert is_italian_holiday(date(2026, 4, 25))
        assert is_italian_holiday(date(2026, 12, 25))
        assert not is_italian_holiday(date(2026, 3, 10))

    def test_pasquetta_is_holiday(self):
        pasquetta = easter_sunday(2026) + timedelta(days=1)
        assert is_italian_holiday(pasquetta)

    def test_next_business_day_noop_on_business_day(self):
        # 2026-03-10 è un martedì feriale non festivo
        d = date(2026, 3, 10)
        assert next_business_day(d) == d

    def test_next_business_day_skips_weekend(self):
        saturday = date(2025, 8, 16)
        assert next_business_day(saturday) == date(2025, 8, 18)

    def test_next_business_day_skips_holiday(self):
        capodanno = date(2026, 1, 1)  # giovedì festivo
        assert next_business_day(capodanno) == date(2026, 1, 2)


@pytest.mark.django_db
class TestOccurrenceGenerationPostponement:
    def test_generate_shifts_holiday_to_next_business_day(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            posticipa_festivi=True,
        )
        start = timezone.make_aware(datetime(2026, 1, 1, 9, 0))  # Capodanno
        occorrenze = scadenza.genera_occorrenze(start=start, count=1)
        assert len(occorrenze) == 1
        assert occorrenze[0].inizio.date() == date(2026, 1, 2)
        assert occorrenze[0].inizio.date().weekday() < 5

    def test_generate_keeps_date_when_posticipa_disabled(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            posticipa_festivi=False,
        )
        start = timezone.make_aware(datetime(2026, 1, 1, 9, 0))
        occorrenze = scadenza.genera_occorrenze(start=start, count=1)
        assert occorrenze[0].inizio.date() == date(2026, 1, 1)

    def test_generate_override_posticipa_per_call(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            posticipa_festivi=True,
        )
        start = timezone.make_aware(datetime(2026, 1, 1, 9, 0))
        occorrenze = scadenza.genera_occorrenze(start=start, count=1, posticipa_festivi=False)
        assert occorrenze[0].inizio.date() == date(2026, 1, 1)

    def test_generate_monthly_last_day_does_not_skip_short_months(self):
        # Periodicità trimestrale con dtstart l'ultimo giorno del mese (31/01):
        # senza bymonthday=-1, rrule salta silenziosamente aprile (30 giorni)
        # perché il "giorno 31" non esiste in quel mese.
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=3,
            posticipa_festivi=False,
        )
        start = timezone.make_aware(datetime(2026, 1, 31, 9, 0))
        occorrenze = scadenza.genera_occorrenze(start=start, count=4)
        assert [occ.inizio.date() for occ in occorrenze] == [
            date(2026, 1, 31),
            date(2026, 4, 30),
            date(2026, 7, 31),
            date(2026, 10, 31),
        ]


@pytest.mark.django_db
class TestBatchAlertTemplates:
    def test_alert_templates_applied_to_all_new_occurrences(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            comunicazione_destinatari="test@example.com",
        )
        templates = [
            {"offset_alert": 3, "offset_alert_periodo": "days", "metodo_alert": "email"},
            {"offset_alert": 1, "offset_alert_periodo": "hours", "metodo_alert": "email"},
        ]
        occorrenze = scadenza.genera_occorrenze(
            start=timezone.now(), count=4, alert_templates=templates
        )
        assert len(occorrenze) == 4
        for occ in occorrenze:
            assert occ.alerts.count() == 2

    def test_invalid_alert_template_rolls_back_whole_batch(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            comunicazione_destinatari="",
        )
        # email senza destinatari e senza comunicazione_destinatari sulla scadenza -> invalido
        templates = [{"offset_alert": 1, "offset_alert_periodo": "days", "metodo_alert": "email"}]
        with pytest.raises(ValidationError):
            scadenza.genera_occorrenze(start=timezone.now(), count=2, alert_templates=templates)
        assert ScadenzaOccorrenza.objects.filter(scadenza=scadenza).count() == 0

    def test_alert_templates_not_duplicated_on_existing_occurrence(self):
        scadenza = baker.make(
            Scadenza,
            periodicita=Scadenza.Periodicita.MENSILE,
            periodicita_intervallo=1,
            comunicazione_destinatari="test@example.com",
        )
        start = timezone.now()
        # Prima generazione senza alert
        occorrenze = scadenza.genera_occorrenze(start=start, count=2)
        assert all(occ.alerts.count() == 0 for occ in occorrenze)

        # Riesecuzione con lo stesso start: get_or_create ritrova le occorrenze esistenti,
        # gli alert_templates non devono essere applicati a occorrenze non nuove.
        templates = [{"offset_alert": 1, "offset_alert_periodo": "days", "metodo_alert": "email"}]
        occorrenze_2 = scadenza.genera_occorrenze(start=start, count=2, alert_templates=templates)
        assert len(occorrenze_2) == 2
        for occ in occorrenze_2:
            occ.refresh_from_db()
            assert occ.alerts.count() == 0
