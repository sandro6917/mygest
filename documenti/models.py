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

# ============================================
# Utility: voce di titolario default
# ============================================
def get_or_create_default_titolario() -> TitolarioVoce:
    """
    Ottiene o crea la voce di titolario di default '99 - Varie'
    per documenti senza classificazione specifica.
    """
    default_voce, created = TitolarioVoce.objects.get_or_create(
        codice="99",
        parent=None,
        defaults={
            "titolo": "Varie",
            "pattern_codice": "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
        }
    )
    if created:
        logger.info("Creata voce di titolario default: 99 - Varie")
    return default_voce


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
            "{attr:<codice>}, {attr:<codice>.<campo_anagrafica>}, {cliente.<campo>}, "
            "{slug:descrizione}, {upper:...}/{lower:...}, "
            "{if:attr:<codice>:TESTO}/{ifnot:field:<campo>:TESTO}. "
            "Es: {attr:dipendente.codice} per accedere al codice dell'anagrafica collegata."
        ),
    )
    attivo = models.BooleanField(default=True)
    
    # ============================================
    # CAMPI HELP / DOCUMENTAZIONE
    # ============================================
    help_data = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        verbose_name=_("Dati Help"),
        help_text=_(
            "Struttura JSON contenente tutta la documentazione per questo tipo di documento. "
            "Include: descrizione_breve, quando_usare, campi_obbligatori, attributi_dinamici, "
            "guida_compilazione, pattern_codice, archiviazione, workflow, note_speciali, faq, risorse_correlate"
        )
    )
    help_ordine = models.IntegerField(
        default=0,
        verbose_name=_("Ordine visualizzazione help"),
        help_text=_("Ordine di visualizzazione nella sezione help (0 = primo)")
    )
    
    # ============================================
    # RILEVAMENTO DUPLICATI
    # ============================================
    duplicate_detection_config = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        verbose_name=_("Configurazione rilevamento duplicati"),
        help_text=_(
            "Criteri per identificare documenti duplicati. "
            "Struttura JSON: {'enabled': bool, 'strategy': str, 'fields': [...], 'scope': {...}}. "
            "Esempio: {'enabled': true, 'strategy': 'exact_match', "
            "'fields': [{'type': 'attribute', 'code': 'numero_cedolino'}]}"
        )
    )

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

    ubicazione = models.ForeignKey(
        UnitaFisica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documenti",
        help_text=_("Unità fisica corrente (solo per documenti cartacei)."),
    )
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
        """
        Genera il codice documento secondo il pattern definito.
        
        Supporta placeholder:
        - {CLI}: Codice cliente
        - {TIT}: Codice titolario
        - {ANNO}: Anno documento
        - {SEQ}: Sequenziale (con formato opzionale es. {SEQ:03d})
        - {ANA}: Codice anagrafica (per voci intestate)
        - {ATTR:<codice>}: Attributo dinamico del tipo documento
        - {ATTR:<codice>.<campo>}: Campo di un attributo anagrafica
        
        Esempi pattern:
        - {CLI}-{TIT}-{ANNO}-{SEQ:03d}
        - {CLI}-{ATTR:dipendente.codice}-{ANNO}-{SEQ:02d}
        - {ATTR:tipo}-{ANNO}{SEQ:04d}
        """
        cli_code = self._cliente_code(self.cliente)
        anno = self.data_documento.year
        
        # usa la voce di titolario del documento; in mancanza, fallback alla voce del fascicolo (se presente)
        voce = self.titolario_voce or (self.fascicolo.titolario_voce if self.fascicolo_id else None)
        tit_code = (voce.codice if voce else (self.tipo.codice if self.tipo_id else "NA")).upper()
        pattern = getattr(voce, "pattern_codice", None) or "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
        
        # Gestisci placeholder {ANA} per voci intestate ad anagrafiche
        ana_code = ""
        if voce and hasattr(voce, 'anagrafica') and voce.anagrafica:
            ana_code = voce.anagrafica.codice
        
        # Prepara valori base
        values = {
            'CLI': cli_code,
            'TIT': tit_code,
            'ANNO': anno,
            'SEQ': seq,
            'ANA': ana_code
        }
        
        # Gestisci attributi dinamici {ATTR:codice} o {ATTR:codice.campo}
        # Cerca tutti i pattern {ATTR:...}
        import re
        attr_pattern = re.compile(r'\{ATTR:([^}]+)\}')
        attr_matches = attr_pattern.findall(pattern)
        
        if attr_matches and self.pk:
            # Carica attributi del documento
            attr_values = {}
            for av in AttributoValore.objects.filter(documento=self).select_related('definizione'):
                attr_values[av.definizione.codice] = av.valore
            
            # Risolvi ogni {ATTR:...}
            for attr_spec in attr_matches:
                parts = attr_spec.split('.', 1)
                attr_code = parts[0]
                attr_field = parts[1] if len(parts) > 1 else None
                
                value = attr_values.get(attr_code, '')
                
                # Se c'è un campo specificato (es. dipendente.codice)
                if attr_field and value:
                    try:
                        # Controlla se il valore è un ID di anagrafica
                        from anagrafiche.models import Anagrafica
                        anagrafica = Anagrafica.objects.filter(id=int(value)).first()
                        if anagrafica:
                            value = getattr(anagrafica, attr_field, '')
                    except (ValueError, AttributeError):
                        pass
                
                # Aggiungi al dict dei valori
                pattern = pattern.replace(f'{{ATTR:{attr_spec}}}', f'{{ATTR_{attr_spec.replace(".", "_")}}}')
                values[f'ATTR_{attr_spec.replace(".", "_")}'] = value or ''
        
        try:
            return pattern.format(**values)
        except Exception as e:
            logger.warning(f"Errore formattando pattern codice '{pattern}': {e}")
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

    def _rename_file_if_needed(self, original_name: str, only_new: bool, attrs=None):
        """
        Rinomina il file secondo il pattern del tipo documento.
        
        :param original_name: nome file originale
        :param only_new: se True, rinomina solo i nuovi documenti
        :param attrs: dizionario opzionale di attributi (codice -> valore). Se None, vengono letti dal DB.
        """
        logger.info(
            "_rename_file_if_needed chiamato: doc.id=%s, only_new=%s, attrs_passed=%s, attrs_map=%s",
            self.pk,
            only_new,
            'YES' if attrs is not None else 'NO',
            attrs
        )
        
        if not self.file:
            logger.debug("_rename_file_if_needed: nessun file, skip")
            return
        if only_new and not self._state.adding:
            logger.debug("_rename_file_if_needed: only_new=True ma documento non nuovo, skip")
            return

        desired = build_document_filename(self, original_name, attrs=attrs)
        
        logger.info(
            "_rename_file_if_needed: nome desiderato=%s (da original_name=%s)",
            desired,
            original_name
        )

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

    def _move_file_into_archivio(self, attrs=None):
        """
        Sposta o copia il file dallo tmp dello storage alla cartella finale calcolata
        da percorso_archivio, mantenendo il basename generato dal pattern.
        L'operazione (copy/move) viene determinata dall'attributo _file_operation.
        
        :param attrs: dizionario opzionale di attributi (codice -> valore). Se None, vengono letti dal DB.
        """
        if not self.file:
            logger.debug("_move_file_into_archivio: nessun file presente")
            return

        storage = self.file.storage
        current_name = self.file.name  # percorso relativo nello storage (es. tmp/2021/BOCBRU/...)
        
        # Ottieni l'operazione scelta dall'utente (default: copy per retrocompatibilità)
        file_operation = getattr(self, '_file_operation', 'copy')
        logger.info(
            "_move_file_into_archivio: documento id=%s, file_operation=%s, hasattr=%s",
            self.pk,
            file_operation,
            hasattr(self, '_file_operation')
        )
        
        # dir relativa dentro /mnt/archivio
        rel_dest_dir = os.path.relpath(self.percorso_archivio, settings.ARCHIVIO_BASE_PATH).lstrip("./")
        # basename desiderato dal pattern (usa l'attuale basename come input estensione)
        # Passa la mappa degli attributi per evitare cache stale
        desired_base = build_document_filename(self, os.path.basename(current_name), attrs=attrs)
        target_rel = os.path.normpath(os.path.join(rel_dest_dir, desired_base))

        # Se già al posto giusto, non fare nulla
        if os.path.normpath(current_name) == target_rel:
            logger.debug(
                "File già nella posizione corretta: %s",
                current_name
            )
            return

        operation_label = "Spostamento" if file_operation == 'move' else "Copia"
        logger.info(
            "%s file documento id=%s da %s a %s",
            operation_label,
            self.pk,
            current_name,
            target_rel,
        )

        # Copia nel nuovo path creando le directory (save gestisce le dirs e l'unicità)
        with storage.open(current_name, "rb") as src:
            new_name = storage.save(target_rel, File(src))

        # Elimina l'originale solo se l'operazione è 'move'
        if file_operation == 'move':
            try:
                storage.delete(current_name)
                logger.info(
                    "File originale eliminato: %s",
                    current_name,
                )
            except Exception as e:
                logger.warning(
                    "Impossibile eliminare il file originale %s: %s",
                    current_name,
                    str(e),
                )
        else:
            logger.info(
                "File originale mantenuto: %s",
                current_name,
            )

        self.file.name = new_name
        super().save(update_fields=["file"])

        logger.info(
            "%s completato documento id=%s nuovo_percorso=%s",
            operation_label,
            self.pk,
            new_name,
        )
    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        original_name = None
        if self.file and hasattr(self.file, "name"):
            original_name = os.path.basename(self.file.name)

        # Verifica se il titolario è cambiato (per spostare il file)
        titolario_changed = False
        old_percorso = None
        if not is_new and self.pk:
            try:
                old_doc = type(self).objects.only("titolario_voce_id", "percorso_archivio").get(pk=self.pk)
                if old_doc.titolario_voce_id != self.titolario_voce_id:
                    titolario_changed = True
                    old_percorso = old_doc.percorso_archivio
                    logger.info(
                        "Documento id=%s: titolario_voce cambiato da %s a %s",
                        self.pk,
                        old_doc.titolario_voce_id,
                        self.titolario_voce_id
                    )
            except type(self).DoesNotExist:
                pass

        if is_new and not self.codice:
            seq = self._next_seq()
            self.codice = self._generate_codice(seq)

        # percorso assoluto su /mnt/archivio (usato per calcolare la dir relativa nello storage)
        self.percorso_archivio = self._build_path()

        super().save(*args, **kwargs)

        # rinomina/sposta il file dentro lo storage NAS
        # SKIP se il form ha impostato _skip_auto_rename (perché gestirà la rinomina dopo il salvataggio degli attributi)
        skip_auto_operations = getattr(self, '_skip_auto_rename', False)
        
        if self.file and original_name and not skip_auto_operations:
            self._rename_file_if_needed(
                original_name,
                only_new=getattr(settings, "DOCUMENTI_RENAME_ONLY_NEW", True),
            )

        # Se il titolario è cambiato e c'è un file, spostalo nella nuova directory
        if titolario_changed and self.file and old_percorso and old_percorso != self.percorso_archivio:
            logger.info(
                "Documento id=%s: spostamento file da %s a %s",
                self.pk,
                old_percorso,
                self.percorso_archivio
            )
            self._move_file_into_archivio()
        # Altrimenti, sposta sempre il file dentro percorso_archivio (se presente)
        # SKIP se il form gestirà lo spostamento dopo il salvataggio degli attributi
        elif self.file and not skip_auto_operations:
            self._move_file_into_archivio()

    def rigenera_codice_con_attributi(self):
        """
        Rigenera il codice documento dopo il salvataggio degli attributi.
        
        Utile quando il pattern_codice utilizza attributi dinamici (es. {ATTR:dipendente.codice})
        che non sono disponibili al momento della creazione iniziale del documento.
        
        NOTA: Questo metodo può essere chiamato solo DOPO che il documento è stato salvato
        e gli attributi sono stati creati.
        """
        if not self.pk:
            raise ValueError("Il documento deve essere salvato prima di rigenerare il codice")
        
        # Rigenera il codice usando il sequenziale attuale
        # Estrai il numero sequenziale dal codice attuale
        import re
        match = re.search(r'-(\d+)$', self.codice)
        if match:
            seq = int(match.group(1))
        else:
            # Fallback: usa il progressivo attuale
            anno = self.data_documento.year
            try:
                counter = DocumentoCounter.objects.get(cliente=self.cliente, anno=anno)
                seq = counter.last_number
            except DocumentoCounter.DoesNotExist:
                seq = 1
        
        nuovo_codice = self._generate_codice(seq)
        
        if nuovo_codice != self.codice:
            logger.info(
                f"Rigenerazione codice documento ID={self.pk}: {self.codice} → {nuovo_codice}"
            )
            self.codice = nuovo_codice
            self.save(update_fields=['codice'])
    
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
                           destinatario_anagrafica=None,
                           ubicazione: Optional["UnitaFisica"] = None, causale: str = "", note: str = ""):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_entrata(documento=self, quando=quando, operatore=operatore,
                                                    da_chi=da_chi, destinatario_anagrafica=destinatario_anagrafica,
                                                    ubicazione=ubicazione, causale=causale, note=note)

    def protocolla_uscita(self, *, quando=None, operatore=None, a_chi: str = "",
                          data_rientro_prevista=None, causale: str = "", note: str = "",
                          ubicazione: Optional["UnitaFisica"] = None,
                          destinatario_anagrafica=None):
        from protocollo.models import MovimentoProtocollo
        return MovimentoProtocollo.registra_uscita(documento=self, quando=quando, operatore=operatore,
                                                   a_chi=a_chi, destinatario_anagrafica=destinatario_anagrafica,
                                                   data_rientro_prevista=data_rientro_prevista,
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
        fascicolo = getattr(self, "fascicolo", None)
        documento_ubicazione_id = getattr(self, "ubicazione_id", None)

        if self.digitale:
            if documento_ubicazione_id:
                errors["ubicazione"] = _("I documenti digitali non prevedono un'ubicazione fisica.")
            self.ubicazione = None
        else:
            if fascicolo and getattr(fascicolo, "ubicazione_id", None):
                if documento_ubicazione_id and documento_ubicazione_id != fascicolo.ubicazione_id:
                    errors["ubicazione"] = _("Per i documenti cartacei fascicolati l'ubicazione deve coincidere con quella del fascicolo.")
                else:
                    # Allinea automaticamente l'ubicazione al fascicolo se non impostata
                    self.ubicazione_id = fascicolo.ubicazione_id
            elif fascicolo and not getattr(fascicolo, "ubicazione_id", None):
                errors["fascicolo"] = _("I documenti cartacei possono essere collegati solo a fascicoli con ubicazione fisica.")
            elif not documento_ubicazione_id:
                errors["ubicazione"] = _("I documenti cartacei non fascicolati richiedono un'ubicazione fisica.")
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


# ============================================
# Sessioni di Importazione
# ============================================

import uuid
from datetime import timedelta


class ImportSession(models.Model):
    """
    Sessione di importazione multi-documento.
    Traccia l'intero processo di importazione con audit trail completo.
    """
    
    TIPO_CHOICES = [
        ('cedolini', 'Cedolini Paga'),
        ('unilav', 'Comunicazioni UNILAV'),
        ('f24', 'Modelli F24'),
        ('dichiarazioni_fiscali', 'Dichiarazioni Fiscali'),
        ('contratti', 'Contratti'),
        ('fatture', 'Fatture'),
    ]
    
    STATO_CHOICES = [
        ('active', 'Attiva'),
        ('completed', 'Completata'),
        ('expired', 'Scaduta'),
    ]
    
    # Identificazione
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    tipo_importazione = models.CharField(max_length=50, choices=TIPO_CHOICES, db_index=True)
    
    # File originale
    file_originale = models.FileField(
        upload_to='import_sessions/%Y/%m/',
        storage=nas_storage,
        help_text="File ZIP o singolo documento caricato dall'utente"
    )
    file_originale_nome = models.CharField(max_length=500)
    
    # Statistiche
    num_documenti_totali = models.IntegerField(default=0)
    num_documenti_importati = models.IntegerField(default=0)
    num_documenti_saltati = models.IntegerField(default=0)
    num_documenti_errore = models.IntegerField(default=0)
    
    # Stato
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='active', db_index=True)
    
    # Tracking utente
    utente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='import_sessions',
        help_text="Utente che ha avviato l'importazione"
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="Scadenza sessione (default +48h). Dopo questa data la sessione viene eliminata automaticamente."
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Storage temporaneo
    temp_dir = models.CharField(
        max_length=500,
        blank=True,
        help_text="Directory temporanea dove sono estratti i file (viene pulita dopo expire)"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['utente', '-created_at']),
            models.Index(fields=['stato', 'expires_at']),
            models.Index(fields=['tipo_importazione', '-created_at']),
        ]
        verbose_name = "Sessione di Importazione"
        verbose_name_plural = "Sessioni di Importazione"
    
    def __str__(self):
        return f"{self.get_tipo_importazione_display()} - {self.uuid} ({self.get_stato_display()})"
    
    def save(self, *args, **kwargs):
        # Imposta scadenza automatica se non specificata
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        
        # Aggiorna contatori
        if self.pk:
            self.num_documenti_totali = self.documents.count()
            self.num_documenti_importati = self.documents.filter(stato='imported').count()
            self.num_documenti_saltati = self.documents.filter(stato='skipped').count()
            self.num_documenti_errore = self.documents.filter(stato='error').count()
        
        super().save(*args, **kwargs)
    
    def mark_as_completed(self):
        """Marca la sessione come completata"""
        self.stato = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_as_expired(self):
        """Marca la sessione come scaduta"""
        self.stato = 'expired'
        self.save()
    
    @property
    def is_active(self):
        """Verifica se la sessione è ancora attiva"""
        return self.stato == 'active' and self.expires_at > timezone.now()
    
    @property
    def progress_percentage(self):
        """Calcola percentuale completamento"""
        if self.num_documenti_totali == 0:
            return 0
        processed = self.num_documenti_importati + self.num_documenti_saltati + self.num_documenti_errore
        return int((processed / self.num_documenti_totali) * 100)


class ImportSessionDocument(models.Model):
    """
    Singolo documento estratto da una sessione di importazione.
    Mantiene stato parsing, dati estratti, errori, e collegamento al documento finale.
    """
    
    STATO_CHOICES = [
        ('pending', 'Da importare'),
        ('imported', 'Importato'),
        ('skipped', 'Saltato'),
        ('error', 'Errore'),
    ]
    
    # Relazione con sessione
    session = models.ForeignKey(
        ImportSession,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    # Identificazione
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    
    # File info
    filename = models.CharField(max_length=500)
    file_path = models.CharField(
        max_length=1000,
        help_text="Path assoluto o relativo al temp_dir della sessione"
    )
    file_size = models.IntegerField(default=0, help_text="Dimensione file in bytes")
    
    # Dati parsing
    parsed_data = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Dati estratti dal parser (struttura dipende dal tipo importazione)"
    )
    
    anagrafiche_reperite = models.JSONField(
        default=list,
        encoder=DjangoJSONEncoder,
        help_text="Lista anagrafiche trovate nel DB: [{id, cf, nome, match_type, ruolo}]"
    )
    
    valori_editabili = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Campi che l'utente può modificare prima dell'importazione"
    )
    
    mappatura_db = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Preview dei campi che verranno salvati nel DB (tipo, attributi, note_preview)"
    )
    
    # Stato
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='pending', db_index=True)
    ordine = models.IntegerField(
        default=0,
        help_text="Posizione nella lista documenti (per ordinamento UI)"
    )
    
    # Risultato importazione
    documento_creato = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_source',
        help_text="Documento creato dopo l'importazione"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Messaggio errore user-friendly"
    )
    
    error_traceback = models.TextField(
        blank=True,
        help_text="Traceback completo per debugging"
    )
    
    # Timestamp
    parsed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando è stato parsato il documento"
    )
    
    imported_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando è stato importato/creato il documento"
    )
    
    class Meta:
        ordering = ['session', 'ordine', 'filename']
        indexes = [
            models.Index(fields=['session', 'stato']),
            models.Index(fields=['uuid']),
            models.Index(fields=['session', 'ordine']),
        ]
        verbose_name = "Documento Sessione Importazione"
        verbose_name_plural = "Documenti Sessione Importazione"
    
    def __str__(self):
        return f"{self.filename} ({self.get_stato_display()})"
    
    def mark_as_imported(self, documento: Documento):
        """Marca documento come importato con successo"""
        self.stato = 'imported'
        self.documento_creato = documento
        self.imported_at = timezone.now()
        self.error_message = ''
        self.error_traceback = ''
        self.save()
        
        # Aggiorna statistiche sessione
        self.session.save()
    
    def mark_as_skipped(self):
        """Marca documento come saltato dall'utente"""
        self.stato = 'skipped'
        self.save()
        
        # Aggiorna statistiche sessione
        self.session.save()
    
    def mark_as_error(self, error_message: str, traceback: str = ''):
        """Marca documento come errore"""
        self.stato = 'error'
        self.error_message = error_message
        self.error_traceback = traceback
        self.save()
        
        # Aggiorna statistiche sessione
        self.session.save()



