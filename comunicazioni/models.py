from __future__ import annotations

from typing import Any

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _split_emails(value: str) -> list[str]:
    parts = [p.strip() for p in (value or "").replace(";", ",").split(",")]
    return [p for p in parts if p]

class Comunicazione(models.Model):
    class Direzione(models.TextChoices):
        IN = "IN", _("Entrata")
        OUT = "OUT", _("Uscita")

    class TipoComunicazione(models.TextChoices):
        AVVISO_SCADENZA = "AVVISO", _("Avviso scadenza")
        INVIO_DOCUMENTI = "DOCUMENTI", _("Invio documenti")
        INFORMATIVA = "INFORMATIVA", _("Comunicazione informativa")

    tipo = models.CharField(max_length=20, choices=TipoComunicazione.choices, db_index=True)
    direzione = models.CharField(
        max_length=3,
        choices=Direzione.choices,
        default=Direzione.OUT,
        db_index=True,
        help_text=_("Direzione della comunicazione ai fini del protocollo."),
    )
    oggetto = models.CharField(max_length=255)
    corpo = models.TextField(blank=True)
    corpo_html = models.TextField(blank=True, help_text=_("Versione HTML del messaggio, opzionale."))
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_invio = models.DateTimeField(null=True, blank=True, db_index=True)
    mittente = models.EmailField(blank=True, help_text=_("Email mittente (default: impostazioni sistema)"))
    destinatari = models.TextField(help_text=_("Lista destinatari separati da virgola (email/pec)"))
    anagrafica = models.ForeignKey(
        'anagrafiche.Anagrafica',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="comunicazioni",
        help_text=_("Cliente destinatario principale, opzionale se invio multiplo."),
    )
    contatti_destinatari = models.ManyToManyField(
        "anagrafiche.EmailContatto",
        blank=True,
        related_name="comunicazioni_destinatari",
    )
    liste_destinatari = models.ManyToManyField(
        "anagrafiche.MailingList",
        blank=True,
        related_name="comunicazioni_destinatari",
    )
    stato = models.CharField(
        max_length=20,
        choices=[
            ("bozza", "Bozza"),
            ("inviata", "Inviata"),
            ("errore", "Errore invio"),
        ],
        default="bozza",
        db_index=True,
    )
    log_errore = models.TextField(blank=True)
    email_message_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_("Message-ID originale se importata da casella email."),
    )
    importato_il = models.DateTimeField(null=True, blank=True)
    import_source = models.CharField(max_length=120, blank=True)
    documento_protocollo = models.ForeignKey(
        "documenti.Documento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comunicazioni_protocollo",
        help_text=_("Documento da protocollare per questa comunicazione."),
    )
    template = models.ForeignKey(
        "comunicazioni.TemplateComunicazione",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazioni",
        help_text=_("Template utilizzato per generare il contenuto."),
    )
    dati_template = models.JSONField(default=dict, blank=True)
    firma = models.ForeignKey(
        "comunicazioni.FirmaComunicazione",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazioni",
        help_text=_("Firma applicata alla comunicazione."),
    )
    protocollo_movimento = models.OneToOneField(
        "protocollo.MovimentoProtocollo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazione",
        help_text=_("Movimento di protocollo collegato."),
    )

    class Meta:
        verbose_name = _("Comunicazione")
        verbose_name_plural = _("Comunicazioni")
        ordering = ["-data_creazione"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.oggetto} ({self.data_creazione:%Y-%m-%d})"

    def get_absolute_url(self) -> str:
        return reverse("comunicazioni:detail", args=[self.pk])

    def get_update_url(self) -> str:
        return reverse("comunicazioni:edit", args=[self.pk])

    def get_send_url(self) -> str:
        return reverse("comunicazioni:send", args=[self.pk])

    @property
    def edit_url(self) -> str:
        return self.get_update_url()

    @property
    def invia_url(self) -> str:
        return self.get_send_url()

    @property
    def is_protocollata(self) -> bool:
        return self.protocollo_movimento_id is not None

    @property
    def can_protocolla(self) -> bool:
        return not self.is_protocollata and self.documento_protocollo_id is not None

    @property
    def protocollo_label(self) -> str:
        movimento = self.protocollo_movimento
        if movimento is None:
            return ""
        return f"{movimento.anno}/{movimento.numero:06d}"

    def get_destinatari_lista(self) -> list[str]:
        manuali = _split_emails(self.destinatari)
        contatti = [c.email for c in self.contatti_destinatari.filter(attivo=True)]
        liste = []
        for lista in self.liste_destinatari.filter(attiva=True).prefetch_related("contatti", "indirizzi_extra"):
            liste.extend([c.email for c in lista.contatti.filter(attivo=True)])
            liste.extend([extra.email for extra in lista.indirizzi_extra.all()])
        dedup = []
        for email in manuali + contatti + liste:
            if email and email not in dedup:
                dedup.append(email)
        return dedup

    def sync_destinatari_testo(self) -> None:
        emails = _split_emails(self.destinatari)
        extra = [c.email for c in self.contatti_destinatari.all()]
        for lista in self.liste_destinatari.all():
            extra.extend([c.email for c in lista.contatti.all()])
            extra.extend([extra_email.email for extra_email in lista.indirizzi_extra.all()])
        combined = []
        for email in emails + extra:
            if email and email not in combined:
                combined.append(email)
        self.destinatari = ", ".join(combined)
        self.save(update_fields=["destinatari"])

    def get_template_context(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        base: dict[str, Any] = {
            "comunicazione": self,
            "anagrafica": self.anagrafica,
            "documento_protocollo": self.documento_protocollo,
            "destinatari": self.get_destinatari_lista(),
            "oggi": timezone.now(),
        }
        if extra:
            base.update(extra)
        stored_values = self.dati_template or {}
        template = self.template
        if not template:
            for key, value in stored_values.items():
                if value is not None:
                    base[key] = value
            return base
        context_fields = template.context_fields.filter(active=True).order_by("ordering", "id")
        handled_keys: set[str] = set()
        for field in context_fields:
            if field.key in stored_values:
                stored_value = field.coerce_value(stored_values[field.key])
                base[field.key] = stored_value if stored_value is not None else stored_values[field.key]
                handled_keys.add(field.key)
                continue
            source_value = field.get_source_value(self)
            if source_value is not None:
                base.setdefault(field.key, source_value)
                continue
            default_value = field.get_default_value()
            if field.key not in base and default_value is not None:
                base[field.key] = default_value
        for key, value in stored_values.items():
            if key in handled_keys or value is None:
                continue
            base[key] = value
        return base


    # Import per registrare i modelli definiti in moduli separati.
    from .models_template import FirmaComunicazione, TemplateComunicazione  # noqa: E402,F401

class AllegatoComunicazione(models.Model):
    comunicazione = models.ForeignKey(Comunicazione, on_delete=models.CASCADE, related_name="allegati")
    documento = models.ForeignKey("documenti.Documento", on_delete=models.CASCADE, related_name="comunicazioni_allegato")

    class Meta:
        verbose_name = _("Allegato comunicazione")
        verbose_name_plural = _("Allegati comunicazione")
        unique_together = ("comunicazione", "documento")

    def __str__(self):
        return f"{self.comunicazione} -> {self.documento}"


class Mailbox(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    host = models.CharField(max_length=255)
    porta = models.PositiveIntegerField(default=993)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    cartella = models.CharField(max_length=120, default="INBOX")
    usa_ssl = models.BooleanField(default=True)
    usa_starttls = models.BooleanField(default=False)
    attiva = models.BooleanField(default=True)
    filtra_da = models.TextField(
        blank=True,
        help_text=_("Elenco di indirizzi mittente consentiti (uno per riga). Lascia vuoto per accettare tutti."),
    )
    escludi_da = models.TextField(
        blank=True,
        help_text=_("Indirizzi mittente da escludere (uno per riga)."),
    )
    soggetto_contiene = models.TextField(
        blank=True,
        help_text=_("Importa solo se il soggetto contiene almeno una delle parole chiave (una per riga)."),
    )
    ultimi_uid = models.CharField(max_length=120, blank=True)
    ultima_lettura = models.DateTimeField(null=True, blank=True)
    timeout = models.PositiveIntegerField(default=30)
    salva_headers = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Casella IMAP")
        verbose_name_plural = _("Caselle IMAP")
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def allowed_from(self) -> set[str]:
        values = {r.strip().lower() for r in (self.filtra_da or "").splitlines() if r.strip()}
        return values

    def blocked_from(self) -> set[str]:
        values = {r.strip().lower() for r in (self.escludi_da or "").splitlines() if r.strip()}
        return values

    def subject_tokens(self) -> list[str]:
        return [r.strip().lower() for r in (self.soggetto_contiene or "").splitlines() if r.strip()]


class EmailImport(models.Model):
    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE, related_name="email_imports")
    uid = models.CharField(max_length=120, blank=True)
    message_id = models.CharField(max_length=255)
    mittente = models.CharField(max_length=255, blank=True)
    destinatari = models.TextField(blank=True)
    oggetto = models.CharField(max_length=500, blank=True)
    data_messaggio = models.DateTimeField(null=True, blank=True)
    raw_headers = models.TextField(blank=True)
    corpo_testo = models.TextField(blank=True)
    corpo_html = models.TextField(blank=True)
    comunicazione = models.OneToOneField(
        Comunicazione,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_import",
    )
    importato_il = models.DateTimeField(auto_now_add=True)
    errore = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Email importata")
        verbose_name_plural = _("Email importate")
        ordering = ["-importato_il"]
        constraints = [
            models.UniqueConstraint(fields=["mailbox", "message_id"], name="uniq_mailbox_message_id"),
        ]

    def __str__(self) -> str:
        return f"{self.mailbox}: {self.oggetto or self.message_id}"

    @property
    def data_messaggio_or_import(self):
        return self.data_messaggio or self.importato_il
