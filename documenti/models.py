from __future__ import annotations
import logging
import os
from typing import Optional

from django.db import models, transaction, IntegrityError
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile, File
from django.contrib.contenttypes.models import ContentType

from anagrafiche.models import Anagrafica, Cliente
from fascicoli.models import Fascicolo
from fascicoli.utils import ensure_archivio_path, build_titolario_parts
from archivio_fisico.models import UnitaFisica
from mygest.storages import NASPathStorage
from .utils import build_document_filename
from titolario.models import TitolarioVoce
from anagrafiche.utils import get_or_generate_cli

nas_storage = NASPathStorage()
logger = logging.getLogger("documenti.protocollazione")
User = get_user_model()

# --- in cima al file dove hai definito documento_upload_to ---
def upload_path(instance, filename):
    # alias per compatibilità con la migrazione 0002 esistente
    return documento_upload_to(instance, filename)


# ============================================
# Utility: percorso di upload temporaneo
# ============================================
def documento_upload_to(instance, filename):
    """
    Percorso provvisorio di upload (sotto MEDIA_ROOT).
    Il file verrà poi spostato nel NAS dentro 'percorso_archivio' in Documento.save().
    Struttura: tmp/<anno>/<cliente_code>/<filename>
    """
    # Anno
    d = getattr(instance, "data_documento", None) or timezone.now().date()
    year = d.year

    # Cliente (anche via fascicolo)
    cli = getattr(instance, "cliente", None)
    if cli is None and getattr(instance, "fascicolo_id", None):
        cli = instance.fascicolo.cliente

    # CLI uniforme (6+2). Se manca il cliente, usa fallback “VARIE”
    if cli:
        anag = getattr(cli, "anagrafica", cli)
        cli_code = get_or_generate_cli(anag)
    else:
        cli_code = "VARIE"
    return f"tmp/{year}/{cli_code}/{filename}"


# ============================================
# Tabella Tipi Documento
# ============================================
class DocumentiTipo(models.Model):
    codice = models.CharField(max_length=20, unique=True, db_index=True)
    nome = models.CharField(
            max_length=120,
            default="Senza nome",
            help_text=_("Nome del tipo di documento (es. Fattura, Contratto, Cedolino, ecc.)")
        )
    estensioni_permesse = models.CharField(
        max_length=120,
        blank=True,
        help_text=_("Estensioni consentite separate da virgola (es. pdf,docx,jpg)")
    )
    pattern_codice = models.CharField(
        max_length=120,
        default="{CLI}_{TIPO}_{DATA}_{SEQ:03d}",
        help_text=_("Pattern per il codice documento: usa {CLI}, {TIPO}, {DATA}, {SEQ}")
    )
    nome_file_pattern = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Pattern nome file: token {id}, {tipo.codice}, {data_documento:%Y%m%d}, "
            "{attr:<codice>}, {slug:descrizione}, {upper:...}/{lower:...}, "
            "{if:attr:<codice>:TESTO}/{ifnot:field:<campo>:TESTO}."
        ),
    )
    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Tipo documento")
        verbose_name_plural = _("Tipi documento")
        ordering = ["codice"]

    def __str__(self):
        return f"{self.codice} - {self.nome}"

# -----------------------------
#  Ubicazioni fisiche archivio
# -----------------------------
class Ubicazione(models.Model):
    codice = models.CharField(max_length=50, unique=True)
    descrizione = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = _("Ubicazione")
        verbose_name_plural = _("Ubicazioni")
        ordering = ["codice"]

    def __str__(self) -> str:
        return f"{self.codice} - {self.descrizione}" if self.descrizione else self.codice


def _safe_slug(source: str) -> str:
    import re
    s = (source or "").upper()
    s = re.sub(r"[^A-Z0-9]+", "", s)
    return s[:10] or "DOC"

# ============================================
# Documento
# ============================================
class Documento(models.Model):
    class Stato(models.TextChoices):
        BOZZA = "bozza", _("Bozza")
        DEFINITIVO = "definitivo", _("Definitivo")
        ARCHIVIATO = "archiviato", _("Archiviato")
        USCITO = "uscito", _("Uscito")
        CONSEGNATO = "consegnato", _("Consegnato")
        SCARICATO = "scaricato", _("Scaricato")

    DIREZIONE = (
        ("IN", "Entrata"),
        ("OUT", "Uscita"),
    )

    codice = models.CharField(max_length=100, unique=True, blank=True)
    tipo = models.ForeignKey(DocumentiTipo, on_delete=models.PROTECT, related_name="documenti")
    fascicolo = models.ForeignKey(Fascicolo, on_delete=models.PROTECT, related_name="documenti", null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="documenti")
    titolario_voce = models.ForeignKey(
        TitolarioVoce,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documenti",
    )

    descrizione = models.CharField(max_length=255)
    data_documento = models.DateField(default=timezone.now)
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.BOZZA, db_index=True)
    digitale = models.BooleanField(
        default=True,
        help_text=_("Se disattivo il documento è cartaceo e richiede una gestione fisica."),
    )

    # Magazzino/protocollo: consenti di escludere carte di lavoro
    tracciabile = models.BooleanField(
        default=True,
        help_text=_("Se disattivo, il documento non entra nel flusso di protocollo/movimentazioni (es. carte di lavoro)")
    )

    # percorso temporaneo nel NAS (verrà rinominato dentro lo storage)
    file = models.FileField(storage=nas_storage, upload_to=documento_upload_to, blank=True, null=True, max_length=500)
    percorso_archivio = models.CharField(max_length=500, blank=True, editable=False)

    tags = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    out_aperto = models.BooleanField(default=False, db_index=True)  # lock applicativo per OUT aperto

    class Meta:
        verbose_name = _("Documento")
        verbose_name_plural = _("Documenti")
        ordering = ["-data_documento", "codice"]
        indexes = [
            models.Index(fields=["cliente", "tipo", "data_documento"]),
            models.Index(fields=["stato"]),
            #models.Index(fields=["cliente", "protocollo_anno", "protocollo_direzione", "protocollo_numero"]),
        ]

    # ============================================
    # Utility interne
    # ============================================
    @staticmethod
    def _cliente_code(cli) -> str:
        """Restituisce il codice CLI normalizzando Cliente/Anagrafica."""
        if cli is None:
            return "VARIE"
        anag = getattr(cli, "anagrafica", cli)
        return get_or_generate_cli(anag)

    def _next_seq(self) -> int:
        """Progressivo per cliente e anno, safe anche su SQLite (retry su race)"""
        anno = self.data_documento.year
        for _ in range(5):
            try:
                with transaction.atomic():
                    counter, _ = DocumentoCounter.objects.get_or_create(
                        cliente=self.cliente, anno=anno, defaults={"last_number": 0}
                    )
                    DocumentoCounter.objects.filter(pk=counter.pk).update(
                        last_number=F("last_number") + 1
                    )
                    counter.refresh_from_db(fields=["last_number"])
                    return counter.last_number
            except IntegrityError:
                continue
        raise RuntimeError("Impossibile generare progressivo documento")

    def _generate_codice(self, seq: int) -> str:
        # Uniforma al pattern dei Fascicoli: {CLI}-{TIT}-{ANNO}-{SEQ:03d}
        cli_code = self._cliente_code(self.cliente)
        anno = self.data_documento.year
        # usa la voce di titolario del documento; in mancanza, fallback alla voce del fascicolo (se presente)
        voce = self.titolario_voce or (self.fascicolo.titolario_voce if self.fascicolo_id else None)
        tit_code = (voce.codice if voce else (self.tipo.codice if self.tipo_id else "NA")).upper()
        pattern = getattr(voce, "pattern_codice", None) or "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
        try:
            return pattern.format(CLI=cli_code, TIT=tit_code, ANNO=anno, SEQ=seq)
        except Exception:
            return f"{cli_code}-{tit_code}-{anno}-{seq:03d}"

    def _build_path(self) -> str:
        """Percorso ASSOLUTO del contenitore del documento nel NAS, coerente con Fascicolo."""
        # 1) Path “del documento” (in base al suo titolario, se presente)
        cli_code = self._cliente_code(self.cliente)
        doc_parts = build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []
        doc_abs = ensure_archivio_path(cli_code, doc_parts, self.data_documento.year)

        # 2) Se legato a un fascicolo, confronta con il path del fascicolo
        if self.fascicolo_id:
            fasc_abs = (self.fascicolo.path_archivio or "").strip()
            # Usa il path fascicolo solo se esiste e coincide col path del documento
            try:
                same = bool(fasc_abs) and os.path.normpath(fasc_abs) == os.path.normpath(doc_abs)
                exists = bool(fasc_abs) and os.path.isdir(fasc_abs)
            except Exception:
                same, exists = False, False
            if same and exists:
                return fasc_abs
        # 3) Default: usa il path calcolato per il documento (case 1: diverso o inesistente; case 2: sempre consentito)
        return doc_abs

    def _rename_file_if_needed(self, original_name: str, only_new: bool):
        if not self.file:
            return
        if only_new and not self._state.adding:
            return

        desired = build_document_filename(self, original_name)

        # cartella finale RELATIVA dentro ARCHIVIO_BASE_PATH
        rel_dest_dir = os.path.relpath(self.percorso_archivio, settings.ARCHIVIO_BASE_PATH)
        # se percorso_archivio è già relativo, evita risalita
        if rel_dest_dir.startswith(".."):
            rel_dest_dir = rel_dest_dir.strip("./")
        new_rel_path = os.path.join(rel_dest_dir, desired)

        current_name = self.file.name  # percorso relativo allo storage
        if current_name == new_rel_path:
            return

        storage = self.file.storage

        # Unicità
        base, ext = os.path.splitext(new_rel_path)
        i = 1
        while getattr(settings, "DOCUMENTI_PATTERN_ENABLE_UNIQUE", True) and storage.exists(new_rel_path):
            new_rel_path = f"{base}_{i}{ext}"
            i += 1

        logger.info(
            "Rinomina file documento id=%s da %s a %s",
            self.pk,
            current_name,
            new_rel_path,
        )

        # rinomina via copia streaming dentro lo storage NAS
        try:
            with storage.open(current_name, "rb") as src, storage.open(new_rel_path, "wb") as dst:
                for chunk in iter(lambda: src.read(64 * 1024), b""):
                    dst.write(chunk)
            try:
                storage.delete(current_name)
            except Exception:
                pass
        except Exception:
            # fallback in memoria
            data = self.file.read()
            storage.save(new_rel_path, ContentFile(data))
            try:
                storage.delete(current_name)
            except Exception:
                pass

        self.file.name = new_rel_path
        super().save(update_fields=["file"])

        logger.info(
            "Rinomina completata documento id=%s nuovo_percorso=%s",
            self.pk,
            new_rel_path,
        )

    def _move_file_into_archivio(self):
        """
        Sposta il file dallo tmp dello storage alla cartella finale calcolata
        da percorso_archivio, mantenendo il basename generato dal pattern.
        """
        if not self.file:
            return

        storage = self.file.storage
        current_name = self.file.name  # percorso relativo nello storage (es. tmp/2021/BOCBRU/...)
        # dir relativa dentro /mnt/archivio
        rel_dest_dir = os.path.relpath(self.percorso_archivio, settings.ARCHIVIO_BASE_PATH).lstrip("./")
        # basename desiderato dal pattern (usa l’attuale basename come input estensione)
        desired_base = build_document_filename(self, os.path.basename(current_name))
        target_rel = os.path.normpath(os.path.join(rel_dest_dir, desired_base))

        # Se già al posto giusto, non fare nulla
        if os.path.normpath(current_name) == target_rel:
            return

        logger.info(
            "Spostamento file documento id=%s da %s a %s",
            self.pk,
            current_name,
            target_rel,
        )

        # Copia nel nuovo path creando le directory (save gestisce le dirs e l'unicità)
        with storage.open(current_name, "rb") as src:
            new_name = storage.save(target_rel, File(src))

        # Elimina l’originale e aggiorna il campo
        try:
            storage.delete(current_name)
        except Exception:
            pass

        self.file.name = new_name
        super().save(update_fields=["file"])

        logger.info(
            "Spostamento completato documento id=%s nuovo_percorso=%s",
            self.pk,
            new_name,
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_name = None
        if self.file and hasattr(self.file, "name"):
            original_name = os.path.basename(self.file.name)

        if is_new and not self.codice:
            seq = self._next_seq()
            self.codice = self._generate_codice(seq)

        # percorso assoluto su /mnt/archivio (usato per calcolare la dir relativa nello storage)
        self.percorso_archivio = self._build_path()

        super().save(*args, **kwargs)

        # rinomina/sposta il file dentro lo storage NAS
        if self.file and original_name:
            self._rename_file_if_needed(
                original_name,
                only_new=getattr(settings, "DOCUMENTI_RENAME_ONLY_NEW", True),
            )

        # Sposta sempre il file dentro percorso_archivio (se presente)
        if self.file:
            self._move_file_into_archivio()

    @property
    def is_cartaceo(self) -> bool:
        return not self.digitale

    @property
    def stato_magazzino(self) -> str:
        if not self.tracciabile:
            return "Non tracciato"
        out_aperto = self.movimenti.filter(direzione="OUT", chiuso=False).exists()
        return "Uscito" if out_aperto else "In giacenza"

    def protocolla_entrata(self, *, quando=None, operatore=None, da_chi: str = "",
                           ubicazione: Optional["UnitaFisica"] = None, causale: str = "", note: str = ""):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_entrata(documento=self, quando=quando, operatore=operatore,
                                                    da_chi=da_chi, ubicazione=ubicazione, causale=causale, note=note)

    def protocolla_uscita(self, *, quando=None, operatore=None, a_chi: str = "",
                          data_rientro_prevista=None, causale: str = "", note: str = "",
                          ubicazione: Optional["UnitaFisica"] = None):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_uscita(documento=self, quando=quando, operatore=operatore,
                                                   a_chi=a_chi, data_rientro_prevista=data_rientro_prevista,
                                                   causale=causale, note=note, ubicazione=ubicazione)

    @property
    def movimento_out_aperto(self):
        return self.movimenti.filter(direzione="OUT", chiuso=False).order_by("-data").first()

    @property
    def collocazione_fisica(self):
        # preferisci il collegamento diretto 1:N
        from archivio_fisico.models import CollocazioneFisica
        return CollocazioneFisica.objects.filter(documento=self, attiva=True)\
                                         .select_related("unita").first()

    @property
    def collocazioni_fisiche_storico(self):
        from archivio_fisico.models import CollocazioneFisica
        return CollocazioneFisica.objects.filter(documento=self).select_related("unita").order_by("-attiva", "-dal", "-id")

    def clean(self):
        super().clean()
        errors = {}
        if not self.digitale and self.fascicolo_id:
            fascicolo = getattr(self, "fascicolo", None)
            # se fascicolo non salvato ancora, evita query imprevedibili
            fascicolo_has_ubicazione = bool(getattr(fascicolo, "ubicazione_id", None)) if fascicolo else False
            if not fascicolo_has_ubicazione:
                errors["fascicolo"] = _("I documenti cartacei possono essere collegati solo a fascicoli con ubicazione fisica.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.codice} - {self.descrizione}"

class DocumentoCounter(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="documento_counters")
    anno = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("cliente", "anno"),)
        indexes = [models.Index(fields=["cliente", "anno"])]
        verbose_name = _("Contatore documenti")
        verbose_name_plural = _("Contatori documenti")

    def __str__(self) -> str:
        return f"{self.cliente} {self.anno}: {self.last_number}"

# -----------------------------
#  Attributi dinamici
# -----------------------------
class AttributoDefinizione(models.Model):
    class TipoDato(models.TextChoices):
        STRING = "string", "Stringa"
        INT = "int", "Intero"
        DECIMAL = "decimal", "Decimale"
        DATE = "date", "Data"
        BOOL = "bool", "Booleano"
        CHOICE = "choice", "Scelta"

    tipo_documento = models.ForeignKey(DocumentiTipo, on_delete=models.CASCADE, related_name="attributi")
    codice = models.SlugField(max_length=50, help_text="Codice univoco per tipo (es. numero_pratica)")
    nome = models.CharField(max_length=120, help_text="Etichetta campo")
    tipo_dato = models.CharField(max_length=10, choices=TipoDato.choices, default=TipoDato.STRING)
    required = models.BooleanField(default=False)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    regex = models.CharField(max_length=200, blank=True, help_text="Regex di validazione opzionale")
    choices = models.CharField(max_length=500, blank=True, help_text="Lista scelte 'valore|etichetta' separate da virgola")
    help_text = models.CharField(max_length=255, blank=True)
    ordine = models.PositiveIntegerField(default=0)
    widget = models.CharField(
        max_length=32, blank=True, default="",
        help_text="Rendering del campo: vuoto=default, 'anagrafica'=select Anagrafica"
    )

    class Meta:
        unique_together = (("tipo_documento", "codice"),)
        ordering = ["tipo_documento", "ordine", "codice"]
        verbose_name = "Attributo (definizione)"
        verbose_name_plural = "Attributi (definizioni)"

    def __str__(self):
        return f"{self.tipo_documento.codice}:{self.codice}"

    def scelte(self):
        # ritorna lista di tuple (value, label)
        out = []
        for part in (self.choices or "").split(","):
            part = part.strip()
            if not part:
                continue
            if "|" in part:
                v, l = part.split("|", 1)
            else:
                v, l = part, part
            out.append((v.strip(), l.strip()))
        return out


class AttributoValore(models.Model):
    documento = models.ForeignKey("Documento", on_delete=models.CASCADE, related_name="attributi_valori")
    definizione = models.ForeignKey(AttributoDefinizione, on_delete=models.CASCADE, related_name="valori")
    # si usa JSON per gestire tipi diversi in modo semplice
    valore = models.JSONField(default=None, null=True, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        unique_together = (("documento", "definizione"),)
        indexes = [models.Index(fields=["documento", "definizione"])]
        verbose_name = "Attributo (valore)"
        verbose_name_plural = "Attributi (valori)"

    def __str__(self):
        return f"{self.documento.codice or self.documento_id} · {self.definizione.codice}={self.valore}"



