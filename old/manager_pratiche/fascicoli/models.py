from __future__ import annotations

import os
from typing import List, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from anagrafiche.models import Anagrafica
from pratiche.models import Pratica
# Alias per compatibilità test: espone "Cliente" dal modulo anagrafiche
from anagrafiche.models import Anagrafica as Cliente

from django.db import IntegrityError
from django.db.models import F, Q

from .utils import ensure_archivio_path
from titolario.models import TitolarioVoce  # NUOVO: import dal nuovo app
from archivio_fisico.models import CollocazioneFisica  # NEW


# ==============================
# Fascicolo
# ==============================
class Fascicolo(models.Model):
    class Stato(models.TextChoices):
        CORRENTE = "corrente", _("Archivio corrente")
        STORICO = "storico", _("Archivio storico")
        CHIUSO = "chiuso", _("Chiuso")
        DEPOSITO = "deposito", _("Deposito")
        ARCHIVIO_IN_DEPOSITO = "archivio_deposito", _("Archivio in deposito")

    # Collegamenti
    pratica = models.OneToOneField(
        Pratica,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fascicolo",
        help_text=_("Se indicata, il cliente viene ereditato dalla pratica."),
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="sottofascicoli"
    )

    # Dati anagrafici / classificazione
    cliente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name="fascicoli")
    titolario_voce = models.ForeignKey(TitolarioVoce, on_delete=models.PROTECT, related_name="fascicoli")

    anno = models.PositiveIntegerField()
    titolo = models.CharField(max_length=200)

    # Codice e progressivi
    codice = models.CharField(max_length=80, unique=True, blank=True)
    progressivo = models.PositiveIntegerField(default=0, editable=False)
    sub_progressivo = models.PositiveIntegerField(default=0, editable=False)

    # Stato e metadati
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.CORRENTE)
    note = models.TextField(blank=True)
    # Ubicazione (archivio fisico) opzionale
    ubicazione = models.ForeignKey(
        CollocazioneFisica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fascicoli",
    )
    retention_anni = models.PositiveIntegerField(default=10)

    # Protocollo (opzionale)
    protocollo_numero = models.CharField(max_length=50, blank=True)
    protocollo_data = models.DateField(null=True, blank=True)

    # Percorso su NAS (ASSOLUTO) memorizzato per velocità/debug
    path_archivio = models.CharField(max_length=500, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Fascicolo")
        verbose_name_plural = _("Fascicoli")
        indexes = [
            models.Index(fields=["cliente", "titolario_voce", "anno", "progressivo"]),
            models.Index(fields=["parent", "sub_progressivo"]),
        ]
        constraints = [
            # Se root: sub_progressivo deve essere 0; se ha parent: progressivo deve essere 0
            models.CheckConstraint(
                check=Q(parent__isnull=True, sub_progressivo=0) | Q(parent__isnull=False, progressivo=0),
                name="chk_progressivi_coerenti",
            ),
            models.CheckConstraint(check=Q(progressivo__gte=0) & Q(sub_progressivo__gte=0), name="chk_progressivi_pos"),
        ]

    # -----------------
    # Utility interne
    # -----------------
    @staticmethod
    def _cliente_code(cliente: Anagrafica) -> str:
        """Restituisce il codice cliente usato nelle directory."""
        code = getattr(cliente, "codice", None)
        if code:
            return code
        # fallback minimale per PF: cognome+iniziale, es. ROSSIM
        cognome = (getattr(cliente, "cognome", "") or "").strip().upper()
        nome = (getattr(cliente, "nome", "") or "").strip().upper()
        return (cognome + (nome[:1] if nome else "")) or "CLIENTE"

    def _titolario_parts(self) -> List[str]:
        return self.titolario_voce.titolario_parts_for_fs()

    def _next_progressivo_main(self) -> int:
        for _ in range(5):
            try:
                with transaction.atomic():
                    c, _ = FascicoloCounter.objects.get_or_create(
                        cliente=self.cliente,
                        titolario_voce=self.titolario_voce,
                        anno=self.anno,
                        defaults={"last_number": 0},
                    )
                    FascicoloCounter.objects.filter(pk=c.pk).update(last_number=F("last_number") + 1)
                    c.refresh_from_db(fields=["last_number"])
                    return c.last_number
            except IntegrityError:
                continue
        raise RuntimeError("Impossibile generare progressivo fascicolo")

    def _next_sub_progressivo(self) -> int:
        with transaction.atomic():
            c, _ = SottofascicoloCounter.objects.get_or_create(parent=self)
            SottofascicoloCounter.objects.filter(pk=c.pk).update(last_number=F("last_number") + 1)
            c.refresh_from_db(fields=["last_number"])
            return c.last_number

    def build_archivio_dir_abs(self) -> str:
        """Percorso ASSOLUTO dove vive il fascicolo sul NAS (unificato con Documento)."""
        cli_code = self._cliente_code(self.cliente)
        parts = [p.replace(os.sep, "-") for p in self._titolario_parts()]
        return ensure_archivio_path(cli_code, parts, self.anno)

    # -------------
    # Salvataggio
    # -------------
    def save(self, *args, **kwargs):
        with transaction.atomic():
            creating = self._state.adding

            # Eredita cliente da pratica se non impostato esplicitamente
            if self.pratica and not self.cliente_id:
                self.cliente = self.pratica.cliente

            if creating:
                if self.parent_id:
                    if not self.sub_progressivo:
                        self.sub_progressivo = self._next_sub_progressivo()
                    seq = self.sub_progressivo
                else:
                    if not self.progressivo:
                        self.progressivo = self._next_progressivo_main()
                    seq = self.progressivo
                if not self.codice:
                    pattern = self.titolario_voce.pattern_codice or "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
                    cli = self._cliente_code(self.cliente)
                    tit = self.titolario_voce.codice
                    self.codice = pattern.format(CLI=cli, TIT=tit, ANNO=self.anno, SEQ=seq)

            # Validazione completa
            self.full_clean()
            super().save(*args, **kwargs)

            dest_dir = self.build_archivio_dir_abs()

            def _apply_fs():
                os.makedirs(dest_dir, exist_ok=True)
                type(self).objects.filter(pk=self.pk).update(path_archivio=dest_dir)
            transaction.on_commit(_apply_fs)

    def clean(self):
        # cliente da pratica, se non impostato
        if self.pratica and not self.cliente_id:
            self.cliente = self.pratica.cliente

        errors = {}

        # Impedisci modifiche che cambierebbero il path dopo la creazione
        if self.pk and not self._state.adding:
            try:
                original = type(self).objects.only("cliente_id", "titolario_voce_id", "anno").get(pk=self.pk)
            except type(self).DoesNotExist:
                original = None
            if original:
                if self.cliente_id != original.cliente_id:
                    errors["cliente"] = _("Il cliente non può essere modificato dopo la creazione.")
                if self.titolario_voce_id != original.titolario_voce_id:
                    errors["titolario_voce"] = _("La voce di titolario non può essere modificata dopo la creazione.")
                if self.anno != original.anno:
                    errors["anno"] = _("L'anno non può essere modificato dopo la creazione.")

        if self.parent_id:
            if self.parent_id == self.pk:
                errors["parent"] = _("Il fascicolo non può essere parent di se stesso.")
            else:
                if self.parent.cliente_id != self.cliente_id:
                    errors["cliente"] = _("Il cliente deve coincidere con quello del parent.")
                if self.parent.titolario_voce_id != self.titolario_voce_id:
                    errors["titolario_voce"] = _("La voce di titolario deve coincidere con quella del parent.")
                if self.parent.anno != self.anno:
                    errors["anno"] = _("L'anno deve coincidere con quello del parent.")
        if self.anno <= 0:
            errors["anno"] = _("Anno non valido.")
        if errors:
            raise ValidationError(errors)

    def protocolla(self, numero: str, data):
        self.protocollo_numero = numero
        self.protocollo_data = data
        self.save(update_fields=["protocollo_numero", "protocollo_data"])

    def __str__(self) -> str:
        return f"{self.codice or 'FASC'} - {self.titolo}"


class FascicoloCounter(models.Model):
    cliente = models.ForeignKey(Anagrafica, on_delete=models.CASCADE, related_name="fascicolo_counters")
    titolario_voce = models.ForeignKey(TitolarioVoce, on_delete=models.CASCADE, related_name="fascicolo_counters")
    anno = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cliente", "titolario_voce", "anno"],
                name="uniq_fascicolo_counter_key",
            )
        ]
        indexes = [models.Index(fields=["cliente", "titolario_voce", "anno"])]

    def __str__(self):
        return f"{self.cliente}-{self.titolario_voce}-{self.anno}: {self.last_number}"


class SottofascicoloCounter(models.Model):
    parent = models.OneToOneField("Fascicolo", on_delete=models.CASCADE, related_name="sub_counter")
    last_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.parent} -> {self.last_number}"
