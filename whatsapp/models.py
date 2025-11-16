from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class WhatsAppBusinessAccount(models.Model):
    name = models.CharField(max_length=120, unique=True)
    phone_number_id = models.CharField(max_length=64, unique=True)
    business_account_id = models.CharField(max_length=64, blank=True)
    access_token = models.TextField()
    verify_token = models.CharField(max_length=128)
    app_secret = models.CharField(max_length=128, blank=True)
    api_version = models.CharField(max_length=16, default="v20.0")
    is_default = models.BooleanField(default=False, db_index=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Account Business WhatsApp"
        verbose_name_plural = "Account Business WhatsApp"
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="unique_whatsapp_default_account",
            )
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone_number_id})"

    def save(self, *args, **kwargs):  # type: ignore[override]
        with transaction.atomic():
            if self.is_default:
                type(self).objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
            super().save(*args, **kwargs)

    @property
    def graph_endpoint(self) -> str:
        base_url = getattr(settings, "WHATSAPP_CLOUD_BASE_URL", "https://graph.facebook.com")
        version = self.api_version or getattr(settings, "WHATSAPP_CLOUD_API_VERSION", "v20.0")
        return f"{base_url.rstrip('/')}/{version}"


class WhatsAppContact(models.Model):
    anagrafica = models.ForeignKey(
        "anagrafiche.Anagrafica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_contacts",
    )
    wa_id = models.CharField(max_length=64, unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    display_name = models.CharField(max_length=120, blank=True)
    verified_name = models.CharField(max_length=120, blank=True)
    blocked = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contatto WhatsApp"
        verbose_name_plural = "Contatti WhatsApp"
        ordering = ["display_name", "wa_id"]

    def __str__(self) -> str:
        return self.display_name or self.wa_id

    @property
    def label(self) -> str:
        base = self.display_name or self.verified_name or self.wa_id
        if self.phone_number and self.phone_number != self.wa_id:
            return f"{base} ({self.phone_number})"
        return base


class WhatsAppConversation(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Aperta"
        CLOSED = "closed", "Chiusa"
        ARCHIVED = "archived", "Archiviata"

    account = models.ForeignKey(
        WhatsAppBusinessAccount,
        on_delete=models.PROTECT,
        related_name="conversations",
    )
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    conversation_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversazione WhatsApp"
        verbose_name_plural = "Conversazioni WhatsApp"
        indexes = [
            models.Index(fields=["account", "contact", "status"]),
            models.Index(fields=["conversation_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "contact"],
                condition=models.Q(status="open"),
                name="whatsapp_one_open_conversation_per_contact",
            )
        ]
        ordering = ["-last_message_at", "-opened_at"]

    def __str__(self) -> str:
        return f"{self.contact} [{self.get_status_display()}]"

    def mark_closed(self, when: Optional[datetime] = None) -> None:
        when = when or timezone.now()
        self.status = self.Status.CLOSED
        self.closed_at = when
        self.save(update_fields=["status", "closed_at", "updated_at"])

    def touch(self, when: Optional[datetime] = None) -> None:
        when = when or timezone.now()
        self.last_message_at = when
        self.save(update_fields=["last_message_at", "updated_at"])


class WhatsAppMessage(models.Model):
    class Direction(models.TextChoices):
        OUTGOING = "outgoing", "In uscita"
        INCOMING = "incoming", "In entrata"

    class MessageType(models.TextChoices):
        TEXT = "text", "Testo"
        TEMPLATE = "template", "Template"
        IMAGE = "image", "Immagine"
        DOCUMENT = "document", "Documento"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"
        BUTTON = "button", "Pulsante"
        SYSTEM = "system", "Sistema"
        UNKNOWN = "unknown", "Sconosciuto"

    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accettato"
        SENT = "sent", "Inviato"
        DELIVERED = "delivered", "Consegnato"
        READ = "read", "Letto"
        FAILED = "failed", "Fallito"
        RECEIVED = "received", "Ricevuto"

    account = models.ForeignKey(
        WhatsAppBusinessAccount,
        on_delete=models.PROTECT,
        related_name="messages",
    )
    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    message_id = models.CharField(max_length=128, unique=True)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    message_type = models.CharField(max_length=16, choices=MessageType.choices, default=MessageType.UNKNOWN)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACCEPTED)
    body = models.TextField(blank=True)
    caption = models.TextField(blank=True)
    media_id = models.CharField(max_length=128, blank=True)
    context_message_id = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    error_code = models.IntegerField(null=True, blank=True)
    error_title = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Messaggio WhatsApp"
        verbose_name_plural = "Messaggi WhatsApp"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "status"]),
            models.Index(fields=["contact", "direction"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        direction = self.get_direction_display()
        return f"{direction}: {self.body[:60]}" if self.body else f"{direction}: {self.message_id}"

    def mark_status(self, status: str, when: Optional[datetime] = None) -> None:
        when = when or timezone.now()
        self.status = status
        timestamp_field = {
            self.Status.SENT: "sent_at",
            self.Status.DELIVERED: "delivered_at",
            self.Status.READ: "read_at",
            self.Status.RECEIVED: "received_at",
        }.get(status)
        update_fields = ["status", "updated_at"]
        if timestamp_field:
            setattr(self, timestamp_field, when)
            update_fields.append(timestamp_field)
        self.save(update_fields=update_fields)

    @property
    def is_outgoing(self) -> bool:
        return self.direction == self.Direction.OUTGOING

    @property
    def is_incoming(self) -> bool:
        return self.direction == self.Direction.INCOMING
