from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Scadenza(models.Model):
    """Modello principale per le scadenze trasversali."""

    class Stato(models.TextChoices):
        BOZZA = "bozza", _("Bozza")
        ATTIVA = "attiva", _("Attiva")
        COMPLETATA = "completata", _("Completata")
        ARCHIVIATA = "archiviata", _("Archiviata")

    class Priorita(models.TextChoices):
        BASSA = "low", _("Bassa")
        MEDIA = "medium", _("Media")
        ALTA = "high", _("Alta")
        CRITICA = "critical", _("Critica")

    class Periodicita(models.TextChoices):
        NESSUNA = "none", _("Senza periodicità")
        GIORNALIERA = "daily", _("Giornaliera")
        SETTIMANALE = "weekly", _("Settimanale")
        MENSILE = "monthly", _("Mensile")
        ANNUALE = "yearly", _("Annuale")
        PERSONALIZZATA = "custom", _("Personalizzata (config JSON)")

    titolo = models.CharField(max_length=255)
    descrizione = models.TextField(blank=True)
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.ATTIVA, db_index=True)
    priorita = models.CharField(max_length=20, choices=Priorita.choices, default=Priorita.MEDIA, db_index=True)
    categoria = models.CharField(max_length=120, blank=True)
    note_interne = models.TextField(blank=True)

    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="scadenze_create",
        null=True,
        blank=True,
    )
    assegnatari = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="scadenze_assegnate",
        blank=True,
    )

    pratiche = models.ManyToManyField(
        "pratiche.Pratica",
        related_name="scadenze",
        blank=True,
    )
    fascicoli = models.ManyToManyField(
        "fascicoli.Fascicolo",
        related_name="scadenze",
        blank=True,
    )
    documenti = models.ManyToManyField(
        "documenti.Documento",
        related_name="scadenze",
        blank=True,
    )

    comunicazione_destinatari = models.TextField(
        blank=True,
        help_text=_("Destinatari predefiniti per l'avviso via app Comunicazioni."),
    )
    comunicazione_modello = models.CharField(
        max_length=120,
        blank=True,
        help_text=_("Codice o slug di modello applicativo per generare il corpo della comunicazione."),
    )

    periodicita = models.CharField(
        max_length=20,
        choices=Periodicita.choices,
        default=Periodicita.NESSUNA,
        help_text=_("Impostazione generica utilizzata dalle procedure massive."),
    )
    periodicita_intervallo = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Intervallo della periodicità (es: ogni 2 settimane)."),
    )
    periodicita_config = JSONField(
        default=dict,
        blank=True,
        help_text=_("Parametri aggiuntivi per la generazione delle occorrenze."),
    )

    google_calendar_calendar_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Identificativo del calendario Google da usare (lascia vuoto per default)."),
    )
    google_calendar_synced_at = models.DateTimeField(null=True, blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Scadenza")
        verbose_name_plural = _("Scadenze")
        ordering = ["-aggiornato_il", "titolo"]
        indexes = [
            models.Index(fields=["stato", "priorita"]),
            models.Index(fields=["creato_il"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - for readability only
        return self.titolo

    @property
    def prossima_occorrenza(self) -> "ScadenzaOccorrenza | None":
        now = timezone.now()
        return (
            self.occorrenze.filter(stato__in=[
                ScadenzaOccorrenza.Stato.PENDENTE,
                ScadenzaOccorrenza.Stato.PROGRAMMATA,
            ], inizio__gte=now)
            .order_by("inizio")
            .first()
        )

    def genera_occorrenze_massive(
        self,
        *,
        start: datetime,
        end: datetime | None = None,
    count: int | None = None,
    offset_alert_minuti: int = 0,
    metodo_alert: str = "email",
        alert_config: dict[str, Any] | None = None,
    ) -> list["ScadenzaOccorrenza"]:
        """Genera occorrenze basandosi sui parametri di periodicità della scadenza."""
        from .services import OccurrenceGenerator

        generator = OccurrenceGenerator(self)
        metodo = metodo_alert or ScadenzaOccorrenza.MetodoAlert.EMAIL
        return generator.generate(
            start=start,
            end=end,
            count=count,
            interval=self.periodicita_intervallo,
            metodo_alert=metodo,
            offset_alert_minuti=offset_alert_minuti,
            alert_config=alert_config or {},
        )


class ScadenzaOccorrenza(models.Model):
    """Occorrenza puntuale con canale di alert e sincronizzazione esterna."""

    class MetodoAlert(models.TextChoices):
        EMAIL = "email", _("Email")
        WEBHOOK = "webhook", _("Webhook")

    class Stato(models.TextChoices):
        PENDENTE = "pending", _("In attesa")
        PROGRAMMATA = "scheduled", _("Programmato per invio alert")
        NOTIFICATA = "alerted", _("Alert inviato")
        COMPLETATA = "completed", _("Completa")
        ANNULLATA = "cancelled", _("Annullata")

    scadenza = models.ForeignKey(
        Scadenza,
        on_delete=models.CASCADE,
        related_name="occorrenze",
    )
    titolo = models.CharField(max_length=255, blank=True)
    descrizione = models.TextField(blank=True)
    inizio = models.DateTimeField(db_index=True)
    fine = models.DateTimeField(null=True, blank=True)

    metodo_alert = models.CharField(
        max_length=20,
        choices=MetodoAlert.choices,
        default=MetodoAlert.EMAIL,
        db_index=True,
    )
    offset_alert_minuti = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Minuti di anticipo per la notifica."),
    )
    alert_config = JSONField(default=dict, blank=True)
    alert_programmata_il = models.DateTimeField(null=True, blank=True, db_index=True)
    alert_inviata_il = models.DateTimeField(null=True, blank=True)

    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.PENDENTE, db_index=True)
    comunicazione = models.ForeignKey(
        "comunicazioni.Comunicazione",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scadenze_occorrenze",
    )

    google_calendar_event_id = models.CharField(max_length=255, blank=True)
    google_calendar_synced_at = models.DateTimeField(null=True, blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Occorrenza scadenza")
        verbose_name_plural = _("Occorrenze scadenze")
        ordering = ["inizio"]
        indexes = [
            models.Index(fields=["scadenza", "inizio"]),
            models.Index(fields=["stato"]),
            models.Index(fields=["alert_programmata_il"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - readability only
        base = self.titolo or self.scadenza.titolo
        return f"{base} @ {self.inizio:%Y-%m-%d %H:%M}"

    def clean(self) -> None:
        super().clean()
        if self.fine and self.fine < self.inizio:
            raise ValidationError({"fine": _("La data di fine non può precedere l'inizio.")})
        if self.metodo_alert == self.MetodoAlert.EMAIL:
            destinatari = (self.alert_config or {}).get("destinatari")
            if not destinatari and not self.scadenza.comunicazione_destinatari:
                raise ValidationError({
                    "alert_config": _("Specificare almeno un destinatario email oppure configurare la scadenza."),
                })
        if self.metodo_alert == self.MetodoAlert.WEBHOOK:
            url = (self.alert_config or {}).get("url")
            if not url:
                raise ValidationError({
                    "alert_config": _("URL webhook obbligatoria per questo metodo di alert."),
                })

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.inizio and self.offset_alert_minuti is not None:
            self.alert_programmata_il = self.inizio - timedelta(minutes=self.offset_alert_minuti)
        super().save(*args, **kwargs)

    def mark_alert_sent(self, *, timestamp: datetime | None = None) -> None:
        timestamp = timestamp or timezone.now()
        self.alert_inviata_il = timestamp
        self.stato = self.Stato.NOTIFICATA
        self.save(update_fields=["alert_inviata_il", "stato", "aggiornato_il"])

    def mark_completed(self, *, timestamp: datetime | None = None) -> None:
        timestamp = timestamp or timezone.now()
        self.stato = self.Stato.COMPLETATA
        self.alert_inviata_il = self.alert_inviata_il or timestamp
        self.save(update_fields=["stato", "alert_inviata_il", "aggiornato_il"])


class ScadenzaNotificaLog(models.Model):
    """Log strutturato per tenere traccia delle comunicazioni inviate."""

    class Evento(models.TextChoices):
        CALENDAR_SYNC = "calendar_sync", _("Sincronizzazione calendario")
        ALERT_PROGRAMMATO = "alert_scheduled", _("Alert programmato")
        ALERT_INVIATO = "alert_sent", _("Alert inviato")
        WEBHOOK_ERROR = "webhook_error", _("Errore webhook")
        EMAIL_ERROR = "email_error", _("Errore email")
        MASSIVE_GENERATION = "bulk_generation", _("Generazione massiva")

    occorrenza = models.ForeignKey(
        ScadenzaOccorrenza,
        on_delete=models.CASCADE,
        related_name="log_eventi",
    )
    evento = models.CharField(max_length=40, choices=Evento.choices, db_index=True)
    esito = models.BooleanField(default=True)
    messaggio = models.TextField(blank=True)
    payload = JSONField(default=dict, blank=True)
    registrato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Log notifica scadenza")
        verbose_name_plural = _("Log notifiche scadenze")
        ordering = ["-registrato_il"]
        indexes = [
            models.Index(fields=["evento", "registrato_il"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_evento_display()} ({'OK' if self.esito else 'KO'})"


class ScadenzaWebhookPayload(models.Model):
    """Conserva il payload inviato ai webhook per audit e retry."""

    occorrenza = models.ForeignKey(
        ScadenzaOccorrenza,
        on_delete=models.CASCADE,
        related_name="payload_webhook",
    )
    inviato_il = models.DateTimeField(auto_now_add=True)
    destinazione = models.URLField()
    payload = JSONField(default=dict, blank=True)
    risposta_status = models.PositiveIntegerField(null=True, blank=True)
    risposta_body = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Payload webhook scadenza")
        verbose_name_plural = _("Payload webhook scadenze")
        ordering = ["-inviato_il"]


def _sync_calendar_after_save(sender, instance: ScadenzaOccorrenza, created: bool, **_: Any) -> None:
    """Trigger asincrono per mantenere allineato Google Calendar."""
    from .services import GoogleCalendarSync

    if instance.stato in {
        ScadenzaOccorrenza.Stato.ANNULLATA,
    }:
        return
    try:
        sync = GoogleCalendarSync()
        sync.upsert_occurrence(instance)
    except Exception as exc:  # pragma: no cover - solo logging
        ScadenzaNotificaLog.objects.create(
            occorrenza=instance,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
            esito=False,
            messaggio=str(exc),
        )


def _delete_calendar_event(sender, instance: ScadenzaOccorrenza, **_: Any) -> None:
    from .services import GoogleCalendarSync

    if not instance.google_calendar_event_id:
        return
    try:
        sync = GoogleCalendarSync()
        sync.delete_occurrence(instance)
    except Exception as exc:  # pragma: no cover
        ScadenzaNotificaLog.objects.create(
            occorrenza=instance,
            evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
            esito=False,
            messaggio=f"Delete failed: {exc}",
        )


from django.db.models.signals import post_delete, post_save  # noqa: E402  pylint: disable=wrong-import-position

post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_sync_google")
post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_delete_google")
