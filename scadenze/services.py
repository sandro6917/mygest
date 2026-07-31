from __future__ import annotations

import calendar
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

from .holidays_utils import next_business_day
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


def _shift_to_business_day(dt_aware: datetime) -> datetime:
    """Sposta dt_aware al primo giorno feriale utile, preservando l'orario."""
    shifted_date = next_business_day(dt_aware.date())
    if shifted_date == dt_aware.date():
        return dt_aware
    return dt_aware.replace(year=shifted_date.year, month=shifted_date.month, day=shifted_date.day)


def _advance_to_next_business_day(dt_aware: datetime) -> datetime:
    """Sposta dt_aware al primo giorno feriale STRETTAMENTE successivo alla sua data."""
    shifted_date = next_business_day(dt_aware.date() + timedelta(days=1))
    return dt_aware.replace(year=shifted_date.year, month=shifted_date.month, day=shifted_date.day)


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
        posticipa_festivi: bool | None = None,
        alert_templates: list[dict[str, Any]] | None = None,
    ) -> list[ScadenzaOccorrenza]:
        """Genera le occorrenze della scadenza.

        `posticipa_festivi=None` usa il valore configurato sulla scadenza;
        se esplicito (True/False) vale solo per questa chiamata. `alert_templates`
        (lista di dict con offset_alert/offset_alert_periodo/metodo_alert/alert_config)
        crea un ScadenzaAlert per ciascun template SOLO sulle occorrenze nuove
        create in questo batch; un template non valido fa rollback dell'intero batch.
        """
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
                posticipa_festivi=posticipa_festivi,
                alert_templates=alert_templates,
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
        if freq == rrule.MONTHLY and start_naive.day == calendar.monthrange(
            start_naive.year, start_naive.month
        )[1]:
            # dtstart è l'ultimo giorno del mese (es. 31): senza bymonthday=-1,
            # rrule usa il giorno fisso 31 e salta silenziosamente i mesi più
            # corti (es. aprile) invece di ricadere sull'ultimo giorno del mese,
            # causando occorrenze mancanti nella sequenza generata.
            rule_kwargs["bymonthday"] = -1
        end_aware: datetime | None = None
        if end:
            end_aware = timezone.make_aware(end) if timezone.is_naive(end) else end
            end_naive = timezone.localtime(end_aware).replace(tzinfo=None)
            rule_kwargs["until"] = end_naive
        if count:
            rule_kwargs["count"] = count

        # Log per debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OccurrenceGenerator - freq: {freq}, rule_kwargs: {rule_kwargs}")

        effective_posticipa = (
            self.scadenza.posticipa_festivi if posticipa_festivi is None else posticipa_festivi
        )

        risultati: list[ScadenzaOccorrenza] = []
        nuove_create = 0
        gia_esistenti = 0
        scartate = 0

        with transaction.atomic():
            occorrenze_rrule = list(rrule.rrule(freq, **rule_kwargs))
            logger.info(f"rrule ha generato {len(occorrenze_rrule)} date")

            used_dates: set[datetime] = set()
            for dt in occorrenze_rrule:
                # Converti il datetime naive di rrule in timezone-aware
                dt_aware = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

                if effective_posticipa:
                    dt_aware = _shift_to_business_day(dt_aware)

                # Due date diverse della rrule possono convergere sullo stesso giorno
                # feriale dopo il posticipo festività: senza questo controllo
                # get_or_create le collasserebbe in un solo record (una rata "sparirebbe").
                while dt_aware in used_dates:
                    dt_aware = _advance_to_next_business_day(dt_aware)

                if end_aware and dt_aware > end_aware:
                    scartate += 1
                    logger.warning(
                        f"Occorrenza scartata: {dt_aware} supera la data fine {end_aware} dopo il posticipo"
                    )
                    continue

                used_dates.add(dt_aware)

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
                    self._apply_alert_templates(occ, alert_templates)
                else:
                    gia_esistenti += 1
                    logger.info(f"Occorrenza GIÀ ESISTENTE: {dt_aware}")

        logger.info(
            f"Riepilogo: {nuove_create} create, {gia_esistenti} già esistenti, {scartate} scartate oltre fine periodo"
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
        posticipa_festivi: bool | None = None,
        alert_templates: list[dict[str, Any]] | None = None,
    ) -> list[ScadenzaOccorrenza]:
        configurazione = self.scadenza.periodicita_config or {}
        explicit_dates: Sequence[str] = configurazione.get("dates", [])
        if not explicit_dates:
            raise ValueError("Periodicità personalizzata senza date esplicite.")

        effective_posticipa = (
            self.scadenza.posticipa_festivi if posticipa_festivi is None else posticipa_festivi
        )
        start_aware = timezone.make_aware(start) if timezone.is_naive(start) else start
        end_aware = timezone.make_aware(end) if end and timezone.is_naive(end) else end

        risultati: list[ScadenzaOccorrenza] = []
        with transaction.atomic():
            used_dates: set[datetime] = set()
            for raw in explicit_dates:
                dt = datetime.fromisoformat(raw)
                dt_aware = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

                if effective_posticipa:
                    dt_aware = _shift_to_business_day(dt_aware)

                while dt_aware in used_dates:
                    dt_aware = _advance_to_next_business_day(dt_aware)

                if end_aware and dt_aware > end_aware:
                    continue
                if dt_aware < start_aware:
                    continue

                used_dates.add(dt_aware)

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
                    self._apply_alert_templates(occ, alert_templates)
        return risultati

    def _apply_alert_templates(
        self,
        occorrenza: ScadenzaOccorrenza,
        alert_templates: list[dict[str, Any]] | None,
    ) -> None:
        """Crea un ScadenzaAlert per ciascun template su un'occorrenza appena creata."""
        for tpl in alert_templates or []:
            alert = ScadenzaAlert(
                occorrenza=occorrenza,
                offset_alert=tpl.get("offset_alert", 1),
                offset_alert_periodo=tpl.get("offset_alert_periodo", ScadenzaAlert.TipoPeriodo.GIORNI),
                metodo_alert=tpl.get("metodo_alert", ScadenzaAlert.MetodoAlert.EMAIL),
                alert_config=tpl.get("alert_config") or {},
            )
            alert.full_clean()
            alert.save()


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
            elif alert.metodo_alert == ScadenzaAlert.MetodoAlert.WHATSAPP:
                self._send_whatsapp_alert(alert)
            elif alert.metodo_alert == ScadenzaAlert.MetodoAlert.TELEGRAM:
                self._send_telegram_alert(alert)
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
        
        _evento_errore = {
            "email": ScadenzaNotificaLog.Evento.EMAIL_ERROR,
            "webhook": ScadenzaNotificaLog.Evento.WEBHOOK_ERROR,
            "whatsapp": ScadenzaNotificaLog.Evento.WHATSAPP_ERROR,
            "telegram": ScadenzaNotificaLog.Evento.TELEGRAM_ERROR,
        }
        inviati = []
        for alert in alerts_da_inviare:
            try:
                self.dispatch_alert(alert)
                inviati.append(alert)
            except Exception as exc:
                evento = _evento_errore.get(alert.metodo_alert, ScadenzaNotificaLog.Evento.EMAIL_ERROR)
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occorrenza,
                    evento=evento,
                    esito=False,
                    messaggio=f"Errore invio alert: {exc}",
                )
        
        return inviati

    def dispatch(self, occorrenza: ScadenzaOccorrenza) -> None:
        """Metodo legacy per compatibilità - invia tutti gli alert dell'occorrenza."""
        self.dispatch_occorrenza_alerts(occorrenza)

    def _send_email_alert(self, alert: "ScadenzaAlert") -> None:
        """Crea una Comunicazione e la invia via SMTP."""
        from comunicazioni.models import Comunicazione
        from comunicazioni.utils import invia_comunicazione_programmatica, EmailSendError

        occorrenza = alert.occorrenza
        config = alert.alert_config or {}

        dests = _split_destinatari(occorrenza.scadenza.comunicazione_destinatari)
        dests.extend(_split_destinatari(config.get("destinatari")))
        dedup = sorted({d for d in dests if d})
        if not dedup:
            raise ImproperlyConfigured("Nessun destinatario per la comunicazione di scadenza")

        oggetto = config.get("oggetto_custom") or occorrenza.titolo or occorrenza.scadenza.titolo
        corpo = config.get("corpo_custom") or self._render_corpo_comunicazione(occorrenza, alert)

        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            oggetto=oggetto,
            corpo=corpo,
            destinatari=", ".join(dedup),
        )

        if not occorrenza.comunicazione:
            occorrenza.comunicazione = comunicazione
            occorrenza.save(update_fields=["comunicazione", "aggiornato_il"])

        try:
            invia_comunicazione_programmatica(comunicazione)
        except EmailSendError as exc:
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.EMAIL_ERROR,
                esito=False,
                messaggio=str(exc),
                payload={"alert_id": alert.pk},
            )
            raise

        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio=f"Alert email inviato ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)",
            payload={"destinatari": dedup, "alert_id": alert.pk},
        )

    def _send_whatsapp_alert(self, alert: "ScadenzaAlert") -> None:
        """Invia un alert via WhatsApp Cloud API."""
        from whatsapp.services import WhatsAppCloudClient, WhatsAppAPIError

        occorrenza = alert.occorrenza
        config = alert.alert_config or {}
        numeri = config.get("numeri_telefono") or getattr(settings, "WHATSAPP_ALERT_DEFAULT_NUMBERS", [])
        if not numeri:
            raise ImproperlyConfigured("Nessun numero di telefono per alert WhatsApp")

        corpo = config.get("corpo_custom") or self._render_corpo_comunicazione(occorrenza, alert)

        try:
            client = WhatsAppCloudClient()
            for numero in numeri:
                client.send_text_message(to=numero, body=corpo)
        except WhatsAppAPIError as exc:
            ScadenzaNotificaLog.objects.create(
                occorrenza=occorrenza,
                evento=ScadenzaNotificaLog.Evento.WHATSAPP_ERROR,
                esito=False,
                messaggio=str(exc),
                payload={"numeri": numeri, "alert_id": alert.pk},
            )
            raise

        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio=f"Alert WhatsApp inviato a {len(numeri)} numero/i ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)",
            payload={"numeri": numeri, "alert_id": alert.pk},
        )

    def _send_telegram_alert(self, alert: "ScadenzaAlert") -> None:
        """Invia un alert via Telegram Bot API."""
        requests_mod = _load_requests_module()
        if requests_mod is None:
            raise ImproperlyConfigured("La libreria requests è necessaria per Telegram")

        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise ImproperlyConfigured("TELEGRAM_BOT_TOKEN non configurato")

        occorrenza = alert.occorrenza
        config = alert.alert_config or {}
        chat_ids = config.get("chat_ids") or getattr(settings, "TELEGRAM_ALERT_DEFAULT_CHAT_IDS", [])
        if not chat_ids:
            raise ImproperlyConfigured("Nessun chat_id Telegram configurato")

        testo = config.get("corpo_custom") or self._render_corpo_comunicazione(occorrenza, alert)
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        for chat_id in chat_ids:
            response = requests_mod.post(url, json={"chat_id": chat_id, "text": testo}, timeout=10)
            if response.status_code >= 400:
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occorrenza,
                    evento=ScadenzaNotificaLog.Evento.TELEGRAM_ERROR,
                    esito=False,
                    messaggio=response.text[:200],
                    payload={"chat_id": chat_id, "alert_id": alert.pk},
                )
                raise ImproperlyConfigured(f"Telegram API error {response.status_code}: {response.text[:100]}")

        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio=f"Alert Telegram inviato a {len(chat_ids)} chat ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)",
            payload={"chat_ids": chat_ids, "alert_id": alert.pk},
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
