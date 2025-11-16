from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Sequence

from dateutil import rrule
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from .models import (
    Scadenza,
    ScadenzaNotificaLog,
    ScadenzaOccorrenza,
    ScadenzaWebhookPayload,
)


def _load_requests_module():
    try:
        return importlib.import_module("requests")
    except ModuleNotFoundError:
        return None


def _load_google_clients():
    try:
        service_account_mod = importlib.import_module("google.oauth2.service_account")
        discovery_mod = importlib.import_module("googleapiclient.discovery")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ImproperlyConfigured("google-api-python-client non installato") from exc
    return service_account_mod, discovery_mod.build


@dataclass(slots=True)
class OccurrenceResult:
    occorrenza: ScadenzaOccorrenza
    created: bool


class OccurrenceGenerator:
    """Genera occorrenze serializzando la logica di periodicità."""

    FREQ_MAP = {
        Scadenza.Periodicita.GIORNALIERA: rrule.DAILY,
        Scadenza.Periodicita.SETTIMANALE: rrule.WEEKLY,
        Scadenza.Periodicita.MENSILE: rrule.MONTHLY,
        Scadenza.Periodicita.ANNUALE: rrule.YEARLY,
    }

    def __init__(self, scadenza: Scadenza):
        self.scadenza = scadenza

    def generate(
        self,
        *,
        start: datetime,
        end: datetime | None,
        count: int | None,
        interval: int,
        metodo_alert: str,
        offset_alert_minuti: int,
        alert_config: dict[str, Any],
    ) -> list[ScadenzaOccorrenza]:
        if self.scadenza.periodicita == Scadenza.Periodicita.NESSUNA:
            raise ValueError("La scadenza non ha periodicità configurata.")
        if self.scadenza.periodicita == Scadenza.Periodicita.PERSONALIZZATA:
            return self._generate_custom(
                start=start,
                end=end,
                count=count,
                metodo_alert=metodo_alert,
                offset_alert_minuti=offset_alert_minuti,
                alert_config=alert_config,
            )
        freq = self.FREQ_MAP.get(self.scadenza.periodicita)
        if freq is None:
            raise ValueError(f"Periodicità {self.scadenza.periodicita} non supportata")

        rule_kwargs: dict[str, Any] = {"dtstart": start, "interval": interval}
        if end:
            rule_kwargs["until"] = end
        if count:
            rule_kwargs["count"] = count

        risultati: list[ScadenzaOccorrenza] = []
        with transaction.atomic():
            for dt in rrule.rrule(freq, **rule_kwargs):
                occ, _ = ScadenzaOccorrenza.objects.get_or_create(
                    scadenza=self.scadenza,
                    inizio=timezone.make_aware(dt) if timezone.is_naive(dt) else dt,
                    defaults={
                        "metodo_alert": metodo_alert,
                        "offset_alert_minuti": offset_alert_minuti,
                        "alert_config": alert_config,
                        "titolo": self.scadenza.titolo,
                        "descrizione": self.scadenza.descrizione,
                    },
                )
                risultati.append(occ)
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occ,
                    evento=ScadenzaNotificaLog.Evento.MASSIVE_GENERATION,
                    messaggio="Occorrenza generata da periodicità",
                )
        return risultati

    def _generate_custom(
        self,
        *,
        start: datetime,
        end: datetime | None,
        count: int | None,
        metodo_alert: str,
        offset_alert_minuti: int,
        alert_config: dict[str, Any],
    ) -> list[ScadenzaOccorrenza]:
        configurazione = self.scadenza.periodicita_config or {}
        explicit_dates: Sequence[str] = configurazione.get("dates", [])
        if not explicit_dates:
            raise ValueError("Periodicità personalizzata senza date esplicite.")

        risultati: list[ScadenzaOccorrenza] = []
        with transaction.atomic():
            for raw in explicit_dates:
                dt = datetime.fromisoformat(raw)
                if end and dt > end:
                    continue
                if dt < start:
                    continue
                occ, _ = ScadenzaOccorrenza.objects.get_or_create(
                    scadenza=self.scadenza,
                    inizio=timezone.make_aware(dt) if timezone.is_naive(dt) else dt,
                    defaults={
                        "metodo_alert": metodo_alert,
                        "offset_alert_minuti": offset_alert_minuti,
                        "alert_config": alert_config,
                        "titolo": self.scadenza.titolo,
                        "descrizione": self.scadenza.descrizione,
                    },
                )
                risultati.append(occ)
        return risultati


class AlertDispatcher:
    """Gestisce l'invio degli alert via email, comunicazione e webhook."""

    def __init__(self, *, user=None):
        self.user = user

    def dispatch(self, occorrenza: ScadenzaOccorrenza) -> None:
        if occorrenza.metodo_alert == ScadenzaOccorrenza.MetodoAlert.EMAIL:
            self._send_email_alert(occorrenza)
        elif occorrenza.metodo_alert == ScadenzaOccorrenza.MetodoAlert.WEBHOOK:
            self._send_webhook_alert(occorrenza)
        else:
            raise ValueError(f"Metodo di alert {occorrenza.metodo_alert} non supportato")

    def _send_email_alert(self, occorrenza: ScadenzaOccorrenza) -> None:
        from comunicazioni.models import Comunicazione

        dests = _split_destinatari(occorrenza.scadenza.comunicazione_destinatari)
        dests.extend(_split_destinatari((occorrenza.alert_config or {}).get("destinatari")))
        dedup = sorted({d for d in dests if d})
        if not dedup:
            raise ImproperlyConfigured("Nessun destinatario per la comunicazione di scadenza")

        body = self._render_corpo_comunicazione(occorrenza)

        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            oggetto=occorrenza.titolo or occorrenza.scadenza.titolo,
            corpo=body,
            destinatari=", ".join(dedup),
        )
        occorrenza.comunicazione = comunicazione
        occorrenza.stato = ScadenzaOccorrenza.Stato.NOTIFICATA
        occorrenza.alert_inviata_il = timezone.now()
        occorrenza.save(update_fields=["comunicazione", "stato", "alert_inviata_il", "aggiornato_il"])

        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio="Avviso registrato nell'app Comunicazioni",
            payload={"destinatari": dedup},
        )

    def _render_corpo_comunicazione(self, occorrenza: ScadenzaOccorrenza) -> str:
        return (
            f"Scadenza: {occorrenza.titolo or occorrenza.scadenza.titolo}\n"
            f"Quando: {timezone.localtime(occorrenza.inizio).strftime('%d/%m/%Y %H:%M')}\n"
            f"Dettagli: {occorrenza.descrizione or occorrenza.scadenza.descrizione}"
        )

    def _send_webhook_alert(self, occorrenza: ScadenzaOccorrenza) -> None:
        requests_mod = _load_requests_module()
        if requests_mod is None:
            raise ImproperlyConfigured("La libreria requests è necessaria per i webhook")
        config = occorrenza.alert_config or {}
        url = config.get("url")
        if not url:
            raise ImproperlyConfigured("URL webhook mancante")
        payload = config.get("payload") or self._build_default_webhook_payload(occorrenza)
        headers = {"Content-Type": "application/json"}
        response = requests_mod.post(url, data=json.dumps(payload), headers=headers, timeout=config.get("timeout", 10))
        ScadenzaWebhookPayload.objects.create(
            occorrenza=occorrenza,
            destinazione=url,
            payload=payload,
            risposta_status=response.status_code,
            risposta_body=response.text[:2000],
        )
        if 200 <= response.status_code < 300:
            occorrenza.mark_alert_sent()
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
                payload={"url": url},
            )
        else:
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.WEBHOOK_ERROR,
                esito=False,
                messaggio=response.text[:500],
                payload={"status": response.status_code, "url": url},
            )

    def _build_default_webhook_payload(self, occorrenza: ScadenzaOccorrenza) -> dict[str, Any]:
        return {
            "id": occorrenza.pk,
            "scadenza": occorrenza.scadenza_id,
            "titolo": occorrenza.titolo or occorrenza.scadenza.titolo,
            "inizio": timezone.localtime(occorrenza.inizio).isoformat(),
            "fine": timezone.localtime(occorrenza.fine).isoformat() if occorrenza.fine else None,
            "metodo_alert": occorrenza.metodo_alert,
        }


class GoogleCalendarSync:
    """Wrapper per sincronizzare le occorrenze sul calendario Google."""

    SCOPES = ("https://www.googleapis.com/auth/calendar",)

    def __init__(self):
        self.credentials_file = getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_FILE", None)
        self.default_calendar_id = getattr(settings, "GOOGLE_CALENDAR_DEFAULT_ID", None)
        if not self.credentials_file:
            raise ImproperlyConfigured("GOOGLE_CALENDAR_CREDENTIALS_FILE non configurato nelle settings")
        self._service_account_mod, self._build_func = _load_google_clients()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            creds = self._service_account_mod.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES,
            )
            self._service = self._build_func("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def upsert_occurrence(self, occorrenza: ScadenzaOccorrenza) -> None:
        calendar_id = occorrenza.scadenza.google_calendar_calendar_id or self.default_calendar_id
        if not calendar_id:
            raise ImproperlyConfigured("Nessun calendar ID configurato")
        body = self._build_event_body(occorrenza)
        service = self.service.events()
        if occorrenza.google_calendar_event_id:
            event = service.update(
                calendarId=calendar_id,
                eventId=occorrenza.google_calendar_event_id,
                body=body,
            ).execute()
        else:
            event = service.insert(calendarId=calendar_id, body=body).execute()
            occorrenza.google_calendar_event_id = event["id"]
        occorrenza.google_calendar_synced_at = timezone.now()
        occorrenza.save(update_fields=["google_calendar_event_id", "google_calendar_synced_at", "aggiornato_il"])
        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
            payload={"calendar_id": calendar_id},
        )

    def delete_occurrence(self, occorrenza: ScadenzaOccorrenza) -> None:
        calendar_id = occorrenza.scadenza.google_calendar_calendar_id or self.default_calendar_id
        if not calendar_id:
            return
        if not occorrenza.google_calendar_event_id:
            return
        self.service.events().delete(
            calendarId=calendar_id,
            eventId=occorrenza.google_calendar_event_id,
        ).execute()
        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
            messaggio="Evento eliminato",
        )

    def _build_event_body(self, occorrenza: ScadenzaOccorrenza) -> dict[str, Any]:
        start_dt = timezone.localtime(occorrenza.inizio)
        end_dt = timezone.localtime(occorrenza.fine or occorrenza.inizio + timedelta(hours=1))
        return {
            "summary": occorrenza.titolo or occorrenza.scadenza.titolo,
            "description": occorrenza.descrizione or occorrenza.scadenza.descrizione,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": settings.TIME_ZONE,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": settings.TIME_ZONE,
            },
        }


def _split_destinatari(value: Iterable[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.replace(";", ",")
        return [p.strip() for p in raw.split(",") if p.strip()]
    result: list[str] = []
    for item in value:
        if item:
            result.extend(_split_destinatari(item))
    return result
