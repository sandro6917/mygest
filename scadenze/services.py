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
    ScadenzaAlert,
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
            raise ValueError(
                "La scadenza non ha periodicità configurata. "
                "Imposta una periodicità (giornaliera, settimanale, mensile o annuale) "
                "prima di generare le occorrenze."
            )
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

        # Assicurati che start sia naive per rrule (richiede datetime naive)
        if timezone.is_aware(start):
            start_naive = timezone.localtime(start).replace(tzinfo=None)
        else:
            start_naive = start

        rule_kwargs: dict[str, Any] = {"dtstart": start_naive, "interval": interval}
        if end:
            if timezone.is_aware(end):
                end_naive = timezone.localtime(end).replace(tzinfo=None)
            else:
                end_naive = end
            rule_kwargs["until"] = end_naive
        if count:
            rule_kwargs["count"] = count

        # Log per debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OccurrenceGenerator - freq: {freq}, rule_kwargs: {rule_kwargs}")
        
        risultati: list[ScadenzaOccorrenza] = []
        nuove_create = 0
        gia_esistenti = 0
        
        with transaction.atomic():
            occorrenze_rrule = list(rrule.rrule(freq, **rule_kwargs))
            logger.info(f"rrule ha generato {len(occorrenze_rrule)} date")
            
            for dt in occorrenze_rrule:
                # Converti il datetime naive di rrule in timezone-aware
                dt_aware = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                occ, created = ScadenzaOccorrenza.objects.get_or_create(
                    scadenza=self.scadenza,
                    inizio=dt_aware,
                    defaults={
                        "metodo_alert": metodo_alert,
                        "offset_alert_minuti": offset_alert_minuti,
                        "alert_config": alert_config,
                        "titolo": self.scadenza.titolo,
                        "descrizione": self.scadenza.descrizione,
                    },
                )
                risultati.append(occ)
                
                if created:
                    nuove_create += 1
                    logger.info(f"Occorrenza CREATA: {dt_aware}")
                    ScadenzaNotificaLog.objects.create(
                        occorrenza=occ,
                        evento=ScadenzaNotificaLog.Evento.MASSIVE_GENERATION,
                        messaggio="Occorrenza generata da periodicità",
                    )
                else:
                    gia_esistenti += 1
                    logger.info(f"Occorrenza GIÀ ESISTENTE: {dt_aware}")
                    
        logger.info(f"Riepilogo: {nuove_create} create, {gia_esistenti} già esistenti")
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
    """Gestisce l'invio degli alert multipli via email, comunicazione e webhook."""

    def __init__(self, *, user=None):
        self.user = user

    def dispatch_alert(self, alert: "ScadenzaAlert") -> None:
        """Invia un singolo alert."""
        from .models import ScadenzaAlert
        
        try:
            if alert.metodo_alert == ScadenzaAlert.MetodoAlert.EMAIL:
                self._send_email_alert(alert)
            elif alert.metodo_alert == ScadenzaAlert.MetodoAlert.WEBHOOK:
                self._send_webhook_alert(alert)
            else:
                raise ValueError(f"Metodo di alert {alert.metodo_alert} non supportato")
            
            alert.mark_sent()
        except Exception as exc:
            alert.mark_failed(error_message=str(exc))
            raise

    def dispatch_occorrenza_alerts(self, occorrenza: ScadenzaOccorrenza) -> list["ScadenzaAlert"]:
        """Invia tutti gli alert programmati per un'occorrenza."""
        from .models import ScadenzaAlert
        
        # Trova tutti gli alert pronti per essere inviati
        now = timezone.now()
        alerts_da_inviare = occorrenza.alerts.filter(
            stato=ScadenzaAlert.Stato.PENDENTE,
            alert_programmata_il__lte=now
        )
        
        inviati = []
        for alert in alerts_da_inviare:
            try:
                self.dispatch_alert(alert)
                inviati.append(alert)
            except Exception as exc:
                # Log dell'errore ma continua con gli altri alert
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occorrenza,
                    evento=ScadenzaNotificaLog.Evento.EMAIL_ERROR if alert.metodo_alert == "email" else ScadenzaNotificaLog.Evento.WEBHOOK_ERROR,
                    esito=False,
                    messaggio=f"Errore invio alert: {exc}",
                )
        
        return inviati

    def dispatch(self, occorrenza: ScadenzaOccorrenza) -> None:
        """Metodo legacy per compatibilità - invia tutti gli alert dell'occorrenza."""
        self.dispatch_occorrenza_alerts(occorrenza)

    def _send_email_alert(self, alert: "ScadenzaAlert") -> None:
        """Invia un alert via email."""
        from comunicazioni.models import Comunicazione
        from .models import ScadenzaAlert
        
        occorrenza = alert.occorrenza
        config = alert.alert_config or {}
        
        dests = _split_destinatari(occorrenza.scadenza.comunicazione_destinatari)
        dests.extend(_split_destinatari(config.get("destinatari")))
        dedup = sorted({d for d in dests if d})
        if not dedup:
            raise ImproperlyConfigured("Nessun destinatario per la comunicazione di scadenza")

        # Supporto per oggetto e corpo personalizzati
        oggetto = config.get("oggetto_custom") or occorrenza.titolo or occorrenza.scadenza.titolo
        corpo = config.get("corpo_custom") or self._render_corpo_comunicazione(occorrenza, alert)

        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            oggetto=oggetto,
            corpo=corpo,
            destinatari=", ".join(dedup),
        )
        
        # Aggiorna l'occorrenza se necessario
        if not occorrenza.comunicazione:
            occorrenza.comunicazione = comunicazione
            occorrenza.save(update_fields=["comunicazione", "aggiornato_il"])

        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio=f"Alert inviato via email ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)",
            payload={"destinatari": dedup, "alert_id": alert.pk},
        )

    def _render_corpo_comunicazione(self, occorrenza: ScadenzaOccorrenza, alert: "ScadenzaAlert" = None) -> str:
        """Renderizza il corpo della comunicazione con supporto per variabili template."""
        # Variabili disponibili per template personalizzati
        context = {
            "titolo": occorrenza.titolo or occorrenza.scadenza.titolo,
            "descrizione": occorrenza.descrizione or occorrenza.scadenza.descrizione,
            "inizio": timezone.localtime(occorrenza.inizio).strftime('%d/%m/%Y %H:%M'),
            "fine": timezone.localtime(occorrenza.fine).strftime('%d/%m/%Y %H:%M') if occorrenza.fine else "N/D",
            "categoria": occorrenza.scadenza.get_categoria_display() if hasattr(occorrenza.scadenza, 'get_categoria_display') else "",
            "priorita": occorrenza.scadenza.get_priorita_display() if hasattr(occorrenza.scadenza, 'get_priorita_display') else "",
        }
        
        if alert:
            context["offset_alert"] = f"{alert.offset_alert} {alert.get_offset_alert_periodo_display()}"
        
        # Template di default
        corpo = (
            f"Scadenza: {context['titolo']}\n"
            f"Quando: {context['inizio']}\n"
            f"Dettagli: {context['descrizione']}"
        )
        
        if alert:
            corpo += f"\n\n[Alert programmato per {context['offset_alert']} prima]"
        
        return corpo

    def _send_webhook_alert(self, alert: "ScadenzaAlert") -> None:
        """Invia un alert via webhook."""
        from .models import ScadenzaAlert
        
        requests_mod = _load_requests_module()
        if requests_mod is None:
            raise ImproperlyConfigured("La libreria requests è necessaria per i webhook")
        
        occorrenza = alert.occorrenza
        config = alert.alert_config or {}
        url = config.get("url")
        if not url:
            raise ImproperlyConfigured("URL webhook mancante")
        
        payload = config.get("payload") or self._build_default_webhook_payload(occorrenza, alert)
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
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
                messaggio=f"Alert webhook inviato ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)",
                payload={"url": url, "alert_id": alert.pk},
            )
        else:
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.WEBHOOK_ERROR,
                esito=False,
                messaggio=response.text[:500],
                payload={"status": response.status_code, "url": url, "alert_id": alert.pk},
            )

    def _build_default_webhook_payload(self, occorrenza: ScadenzaOccorrenza, alert: ScadenzaAlert = None) -> dict[str, Any]:
        payload = {
            "id": occorrenza.pk,
            "scadenza": occorrenza.scadenza_id,
            "titolo": occorrenza.titolo or occorrenza.scadenza.titolo,
            "inizio": timezone.localtime(occorrenza.inizio).isoformat(),
            "fine": timezone.localtime(occorrenza.fine).isoformat() if occorrenza.fine else None,
            "metodo_alert": occorrenza.metodo_alert,
        }
        
        if alert:
            payload["alert"] = {
                "id": alert.pk,
                "offset": alert.offset_alert,
                "periodo": alert.offset_alert_periodo,
                "programmata_il": alert.alert_programmata_il.isoformat() if alert.alert_programmata_il else None,
            }
        
        return payload


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
        
        # Imposta il flag per evitare loop infiniti nel signal
        occorrenza._syncing_calendar = True
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
