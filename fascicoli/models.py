from __future__ import annotations

import os
from typing import List, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from anagrafiche.models import Anagrafica
from pratiche.models import Pratica
# Alias per compatibilità test: espone "Cliente" dal modulo anagrafiche
from anagrafiche.models import Anagrafica as Cliente
from archivio_fisico.models import UnitaFisica

from django.db import IntegrityError
from django.db.models import F, Q

from .utils import ensure_archivio_path, build_titolario_parts
from titolario.models import TitolarioVoce  # NUOVO: import dal nuovo app
# rimosso: CollocazioneFisica
from anagrafiche.utils import get_or_generate_cli


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
        SCARICATO = "scaricato", _("Scaricato")

    # Collegamenti
    # rimuoverai il vecchio campo 'pratica' dopo la migrazione dati
    # pratica = models.ForeignKey("pratiche.Pratica", null=True, blank=True, on_delete=models.SET_NULL)

    pratiche = models.ManyToManyField(
        "pratiche.Pratica",
        related_name="fascicoli",
        blank=True,
    )

    @property
    def pratica(self) -> Optional["Pratica"]:
        # Evita l’accesso al M2M prima che l’istanza sia salvata
        if not getattr(self, "pk", None):
            return None
        return self.pratiche.first()

    @property
    def pratica_id(self) -> Optional[int]:
        if not getattr(self, "pk", None):
            return None
        return self.pratiche.values_list("id", flat=True).first()

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="sottofascicoli"
    )

    # Fascicoli collegati (relazione many-to-many)
    fascicoli_collegati = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="collegato_da",
        help_text=_("Altri fascicoli collegati a questo fascicolo")
    )

    # Dati anagrafici / classificazione
    cliente = models.ForeignKey("anagrafiche.Cliente", null=True, blank=True, on_delete=models.SET_NULL)
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
    # Ubicazione (archivio fisico) opzionale: Unità fisica
    ubicazione = models.ForeignKey(
        UnitaFisica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fascicoli",
    )
    retention_anni = models.PositiveIntegerField(default=10)

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
    def _cliente_code(cliente_obj) -> str:
        """Codice cliente (CLI) uniforme a 8 caratteri; accetta Cliente o Anagrafica."""
        anag = getattr(cliente_obj, "anagrafica", cliente_obj)
        return get_or_generate_cli(anag)

    def _titolario_parts(self) -> List[str]:
        return build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []

    def _counter_party_kwargs(self):
        """
        Restituisce i kwargs corretti per FascicoloCounter in base al FK atteso:
        - se il contatore ha 'cliente'->Cliente usa self.cliente
        - se il contatore ha 'cliente'->Anagrafica usa self.cliente.anagrafica
        - se ha 'anagrafica' usa sempre l'Anagrafica collegata al Cliente
        """
        kwargs = {}
        try:
            # importa a runtime per evitare problemi d’ordine
            Counter = FascicoloCounter  # definito nello stesso modulo
            party_cliente = getattr(self, "cliente", None)
            party_anag = getattr(party_cliente, "anagrafica", None)

            # prova con 'cliente', poi con 'anagrafica'
            for field_name in ("cliente", "anagrafica"):
                try:
                    f = Counter._meta.get_field(field_name)
                except Exception:
                    continue
                target_model = f.remote_field.model._meta.model_name  # 'cliente' o 'anagrafica'
                if field_name == "cliente":
                    kwargs["cliente"] = party_cliente if target_model == "cliente" else party_anag
                else:
                    kwargs["anagrafica"] = party_anag if target_model == "anagrafica" else party_cliente
                break
        except Exception:
            pass
        return kwargs

    def _next_progressivo_main(self):
        year = getattr(self, "anno", None) or timezone.now().year
        # Chiave completa per il contatore
        key = dict(anno=year, titolario_voce=self.titolario_voce)
        key.update(self._counter_party_kwargs())
        # Crea se manca (last_number=0), poi incrementa in modo atomico
        c, _ = FascicoloCounter.objects.get_or_create(**key, defaults={"last_number": 0})
        type(c).objects.filter(pk=c.pk).update(last_number=F("last_number") + 1)
        c.refresh_from_db(fields=["last_number"])
        return c.last_number

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
        if self.pratica_id and not self.cliente_id and getattr(self.pratica, "cliente_id", None):
            self.cliente_id = self.pratica.cliente_id
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
                    
                    # Gestisci placeholder {ANA} per voci intestate ad anagrafiche
                    ana = ""
                    if self.titolario_voce.anagrafica:
                        ana = self.titolario_voce.anagrafica.codice
                    
                    # Supporta tutti i placeholder: {CLI}, {TIT}, {ANNO}, {SEQ}, {ANA}
                    self.codice = pattern.format(
                        CLI=cli, 
                        TIT=tit, 
                        ANNO=self.anno, 
                        SEQ=seq,
                        ANA=ana
                    )

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

    def protocolla_entrata(self, *, quando=None, operatore=None, da_chi: str = "",
                           destinatario_anagrafica=None,
                           ubicazione: Optional["UnitaFisica"] = None, causale: str = "", note: str = ""):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_entrata(fascicolo=self, quando=quando, operatore=operatore,
                                                    da_chi=da_chi, destinatario_anagrafica=destinatario_anagrafica,
                                                    ubicazione=ubicazione, causale=causale, note=note)

    def protocolla_uscita(self, *, quando=None, operatore=None, a_chi: str = "",
                          data_rientro_prevista=None, causale: str = "", note: str = "",
                          ubicazione: Optional["UnitaFisica"] = None,
                          destinatario_anagrafica=None):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_uscita(fascicolo=self, quando=quando, operatore=operatore,
                                                   a_chi=a_chi, destinatario_anagrafica=destinatario_anagrafica,
                                                   data_rientro_prevista=data_rientro_prevista,
                                                   causale=causale, note=note, ubicazione=ubicazione)

    def __str__(self) -> str:
        return f"{self.codice or 'FASC'} - {self.titolo}"

    @property
    def ubicazione_full_path(self) -> str:
        if self.ubicazione and hasattr(self.ubicazione, "full_path"):
            return self.ubicazione.full_path or ""
        return ""


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
