from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class TemplateComunicazione(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    oggetto = models.CharField(max_length=255)
    corpo_testo = models.TextField(
        blank=True,
        help_text=_("Testo email (plain text), può contenere variabili es. {{ nome_cliente }}"),
    )
    corpo_html = models.TextField(
        blank=True,
        help_text=_("HTML email (opzionale), può contenere variabili es. {{ nome_cliente }}"),
    )
    attivo = models.BooleanField(default=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template comunicazione"
        verbose_name_plural = "Template comunicazioni"
        ordering = ["-data_modifica"]

    def __str__(self):
        return self.nome


class TemplateContextField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", _("Testo (breve)")
        TEXTAREA = "textarea", _("Testo (multilinea)")
        INTEGER = "integer", _("Numero intero")
        DECIMAL = "decimal", _("Numero decimale")
        DATE = "date", _("Data")
        DATETIME = "datetime", _("Data e ora")
        BOOLEAN = "boolean", _("Booleano")
        CHOICE = "choice", _("Scelta singola")

    template = models.ForeignKey(
        TemplateComunicazione,
        on_delete=models.CASCADE,
        related_name="context_fields",
    )
    key = models.SlugField(max_length=100, verbose_name="Chiave variabile")
    label = models.CharField(max_length=120, verbose_name="Etichetta")
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        verbose_name="Tipo campo",
    )
    required = models.BooleanField(default=False, verbose_name="Richiesto")
    help_text = models.TextField(blank=True)
    default_value = models.TextField(blank=True)
    choices = models.TextField(
        blank=True,
        help_text=_("Per le scelte singole, una opzione per riga. Facoltativo: valore|etichetta."),
    )
    source_path = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Percorso attributo da `comunicazione`, es. anagrafica.ragione_sociale"),
    )
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    active = models.BooleanField(default=True, verbose_name="Attivo")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Campo variabile template")
        verbose_name_plural = _("Campi variabili template")
        ordering = ["template", "ordering", "id"]
        constraints = [
            models.UniqueConstraint(fields=["template", "key"], name="uniq_template_context_key"),
        ]

    def __str__(self) -> str:  # pragma: no cover - utile in admin
        template_name = self.template.nome if self.template_id else "-"
        return f"{template_name} · {self.key}"

    @cached_property
    def parsed_choices(self) -> list[tuple[str, str]]:
        options: list[tuple[str, str]] = []
        for raw in (self.choices or "").splitlines():
            option = raw.strip()
            if not option:
                continue
            if "|" in option:
                value, label = option.split("|", 1)
                options.append((value.strip(), label.strip()))
            else:
                options.append((option, option))
        return options

    def get_default_value(self) -> Any:
        if not self.default_value:
            return None
        return self.coerce_value(self.default_value)

    def serialize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if self.field_type == self.FieldType.DECIMAL:
            if isinstance(value, Decimal):
                return format(value, "f")
            return str(value)
        if self.field_type == self.FieldType.DATE and isinstance(value, date):
            return value.isoformat()
        if self.field_type == self.FieldType.DATETIME and isinstance(value, datetime):
            value = timezone.make_naive(value) if timezone.is_aware(value) else value
            return value.isoformat()
        if self.field_type == self.FieldType.BOOLEAN:
            return bool(value)
        return value

    def format_initial(self, value: Any) -> Any:
        if value is None:
            return self.get_default_value()
        if self.field_type == self.FieldType.BOOLEAN:
            return bool(value)
        return value

    def get_source_value(self, comunicazione) -> Any:
        from comunicazioni.models import Comunicazione  # evita import circolare

        if not isinstance(comunicazione, Comunicazione):  # pragma: no cover - sicurezza
            return None
        if not self.source_path:
            return None
        current: Any = comunicazione
        for attr in self.source_path.split("."):
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(attr)
                continue
            try:
                current = getattr(current, attr)
            except AttributeError:
                return None
            if callable(current):
                try:
                    current = current()
                except TypeError:
                    return None
        return current

    def parse_raw_input(self, raw_value: Any) -> Any:
        if raw_value in (None, ""):
            return None
        if self.field_type == self.FieldType.BOOLEAN:
            if isinstance(raw_value, bool):
                return raw_value
            value_str = str(raw_value).strip().lower()
            return value_str in {"1", "true", "on", "yes"}
        if self.field_type == self.FieldType.INTEGER:
            try:
                return int(raw_value)
            except (TypeError, ValueError):
                return None
        if self.field_type == self.FieldType.DECIMAL:
            try:
                return Decimal(str(raw_value))
            except (TypeError, ValueError, ArithmeticError):
                return None
        if self.field_type == self.FieldType.DATE:
            try:
                return date.fromisoformat(str(raw_value))
            except (TypeError, ValueError):
                return None
        if self.field_type == self.FieldType.DATETIME:
            try:
                value = datetime.fromisoformat(str(raw_value))
                if timezone.is_naive(value):
                    value = timezone.make_aware(value, timezone.get_current_timezone())
                return value
            except (TypeError, ValueError):
                return None
        return str(raw_value)

    def coerce_value(self, value: Any) -> Any:
        if value in (None, ""):
            return None
        if self.field_type == self.FieldType.BOOLEAN:
            return str(value).strip().lower() in {"1", "true", "on", "yes"}
        if self.field_type == self.FieldType.INTEGER:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        if self.field_type == self.FieldType.DECIMAL:
            try:
                return Decimal(str(value))
            except (TypeError, ValueError, ArithmeticError):
                return None
        if self.field_type == self.FieldType.DATE:
            try:
                return date.fromisoformat(str(value))
            except (TypeError, ValueError):
                return None
        if self.field_type == self.FieldType.DATETIME:
            try:
                parsed = datetime.fromisoformat(str(value))
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                return parsed
            except (TypeError, ValueError):
                return None
        return str(value)


class FirmaComunicazione(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    corpo_testo = models.TextField(
        blank=True,
        help_text=_("Contenuto firma in plain text, può contenere variabili es. {{ operatore.get_full_name }}"),
    )
    corpo_html = models.TextField(
        blank=True,
        help_text=_("Contenuto firma HTML (opzionale), può contenere variabili come nel testo."),
    )
    attivo = models.BooleanField(default=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Firma comunicazione"
        verbose_name_plural = "Firme comunicazioni"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
