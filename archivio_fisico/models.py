from __future__ import annotations
from typing import Optional
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify

# --- Movimentazione fisica di fascicoli/documenti protocollati ---
from django.conf import settings
from anagrafiche.models import Anagrafica, Cliente


# Operazione di movimentazione fisica (entrata/uscita/interna)
class OperazioneArchivio(models.Model):
    TIPO = (
        ("entrata", "Entrata"),
        ("uscita", "Uscita"),
        ("interna", "Movimento interno"),
    )
    tipo_operazione = models.CharField(max_length=10, choices=TIPO)
    data_ora = models.DateTimeField(auto_now_add=True)
    referente_interno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="operazioni_archivio_interni"
    )
    referente_esterno = models.ForeignKey(
        Anagrafica, on_delete=models.PROTECT, null=True, blank=True, related_name="operazioni_archivio_esterni",
        help_text="Persona esterna coinvolta (mittente/destinatario), opzionale per movimenti interni."
    )
    note = models.TextField(blank=True)
    verbale_scan = models.FileField(
        upload_to="archivio/operazioni",
        null=True,
        blank=True,
        max_length=500,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"])],
        help_text="Facoltativo: carica la scansione del verbale firmato.",
    )

    class Meta:
        verbose_name = "Operazione archivio fisico"
        verbose_name_plural = "Operazioni archivio fisico"
        ordering = ["-data_ora"]

    def __str__(self):
        return f"{self.get_tipo_operazione_display()} del {self.data_ora:%Y-%m-%d %H:%M}"


# Riga di dettaglio: documenti/fascicoli coinvolti
class RigaOperazioneArchivio(models.Model):
    operazione = models.ForeignKey("archivio_fisico.OperazioneArchivio", on_delete=models.CASCADE, related_name="righe")
    fascicolo = models.ForeignKey("fascicoli.Fascicolo", null=True, blank=True, on_delete=models.PROTECT)
    documento = models.ForeignKey("documenti.Documento", null=True, blank=True, on_delete=models.PROTECT)
    movimento_protocollo = models.ForeignKey(
        "protocollo.MovimentoProtocollo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="righe_operazione_archivio",
        help_text="Movimento di protocollo collegato specifico per la riga.",
    )
    unita_fisica_sorgente = models.ForeignKey(
        "UnitaFisica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="righe_sorgente",
        help_text="Unità di partenza della movimentazione per questa riga.",
    )
    unita_fisica_destinazione = models.ForeignKey(
        "UnitaFisica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="righe_destinazione",
        help_text="Unità di arrivo della movimentazione per questa riga.",
    )
    stato_precedente = models.CharField(max_length=30, blank=True)
    stato_successivo = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Riga operazione archivio fisico"
        verbose_name_plural = "Righe operazioni archivio fisico"

    def clean(self):
        # Solo documenti/fascicoli protocollati possono essere movimentati
        if self.documento and not self.documento.movimenti.exists():
            raise ValidationError("Il documento non risulta protocollato.")
        if self.fascicolo and not self.fascicolo.movimenti_protocollo.exists():
            raise ValidationError("Il fascicolo non risulta protocollato.")
        errors = {}
        if self.documento:
            if self.documento.digitale:
                errors["documento"] = "I documenti digitali non possono essere movimentati in archivio fisico."
            if not self.documento.tracciabile:
                errors["documento"] = "Il documento deve essere tracciabile per partecipare alle operazioni di archivio."
        if self.fascicolo and not self.fascicolo.ubicazione_id:
            errors["fascicolo"] = "Il fascicolo deve avere un'ubicazione fisica per essere movimentato."
        if self.movimento_protocollo_id:
            mov = self.movimento_protocollo
            mov_errors = {}
            if not mov:
                mov_errors["movimento_protocollo"] = "Movimento di protocollo non valido."
            else:
                if self.documento_id and mov.documento_id != self.documento_id:
                    mov_errors["movimento_protocollo"] = "Il movimento selezionato non appartiene al documento indicato."
                if self.fascicolo_id and mov.fascicolo_id != self.fascicolo_id:
                    mov_errors["movimento_protocollo"] = "Il movimento selezionato non appartiene al fascicolo indicato."
                if not self.documento_id and not self.fascicolo_id:
                    mov_errors["movimento_protocollo"] = "Per collegare un movimento di protocollo è necessario specificare un documento o un fascicolo."
            if mov_errors:
                raise ValidationError(mov_errors)
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        target = self.documento or self.fascicolo
        return f"{target} ({self.stato_precedente} → {self.stato_successivo})"

class UnitaFisica(models.Model):
    class Tipo(models.TextChoices):
        UFFICIO = "ufficio", "Ufficio"
        STANZA = "stanza", "Stanza"
        SCAFFALE = "scaffale", "Scaffale"
        MOBILE ="mobile", "Mobile"
        ANTA = "anta", "Anta"
        RIPIANO = "ripiano", "Ripiano"
        CONTENITORE = "contenitore", "Contenitore"
        CARTELLINA = "cartellina", "Cartellina"

    # Mappa: tipo padre -> insiemi di tipi figli ammessi
    TIPO_FIGLI_AMMESSI = {
        Tipo.UFFICIO: {Tipo.STANZA},
        Tipo.STANZA: {Tipo.SCAFFALE, Tipo.MOBILE, Tipo.RIPIANO},
        Tipo.MOBILE: {Tipo.ANTA, Tipo.RIPIANO, Tipo.CONTENITORE},
        Tipo.ANTA: {Tipo.RIPIANO},
        Tipo.SCAFFALE: {Tipo.RIPIANO},
        Tipo.RIPIANO: {Tipo.CONTENITORE},
        Tipo.CONTENITORE: {Tipo.CARTELLINA},
        Tipo.CARTELLINA: set(),
    }

    prefisso_codice = models.SlugField(max_length=50, help_text="Prefisso utilizzato per il codice", db_index=True)
    progressivo_codice = models.PositiveIntegerField(default=0, editable=False)
    codice = models.CharField(max_length=60, unique=True, editable=False)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="figli", on_delete=models.PROTECT)
    ordine = models.PositiveIntegerField(default=0)
    attivo = models.BooleanField(default=True)
    archivio_fisso = models.BooleanField(default=False, help_text="Flag sì/no: unità destinata ad archivio fisso")  # NEW
    note = models.TextField(blank=True)
    full_path = models.CharField(max_length=500, blank=True, editable=False)  # es. UFF/U01/ST/01/SF/A/...
    progressivo = models.CharField(max_length=300, blank=True, default="", editable=False, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unità fisica"
        verbose_name_plural = "Unità fisiche"
        ordering = ["parent__id", "ordine", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["parent", "prefisso_codice", "progressivo_codice"], name="uniq_unita_by_parent_prefisso_progressivo"),
        ]

    def __str__(self):
        return f"{self.tipo_label()} {self.nome}"

    def tipo_label(self) -> str:
        return self.get_tipo_display()

    def ancestors(self) -> list["UnitaFisica"]:
        cur, chain = self.parent, []
        while cur:
            chain.append(cur)
            cur = cur.parent
        return list(reversed(chain))

    def build_full_path(self) -> str:
        parts = [u.codice for u in self.ancestors()] + [self.codice]
        return "/".join(parts)

    def build_progressivo(self) -> str:
        parts = []
        if self.codice:
            parts.append(self.codice.strip())
        if self.nome:
            parts.append(self.nome.strip())
        if self.tipo:
            parts.append(self.get_tipo_display())
        return "-".join(parts)

    def _ensure_codici(self) -> set[str]:
        changed: set[str] = set()
        prefisso = (self.prefisso_codice or "").strip()
        if prefisso != self.prefisso_codice:
            self.prefisso_codice = prefisso
            changed.add("prefisso_codice")
        if not self.prefisso_codice:
            raise ValidationError({"prefisso_codice": "Il prefisso codice è obbligatorio."})

        Model = type(self)
        assigned_progressivo = self.progressivo_codice
        existing = None
        if self.pk:
            existing = Model.objects.filter(pk=self.pk).values("prefisso_codice", "progressivo_codice").first()

        if existing and existing["prefisso_codice"] == self.prefisso_codice:
            assigned_progressivo = existing["progressivo_codice"]
        else:
            qs = Model.objects.filter(prefisso_codice=self.prefisso_codice)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            max_prog = qs.aggregate(max=models.Max("progressivo_codice"))["max"]
            assigned_progressivo = 1 if max_prog is None else max_prog + 1

        if assigned_progressivo != self.progressivo_codice:
            self.progressivo_codice = assigned_progressivo
            changed.add("progressivo_codice")

        new_codice = f"{self.prefisso_codice}{self.progressivo_codice}"
        if new_codice != self.codice:
            self.codice = new_codice
            changed.add("codice")

        return changed

    def clean(self):
        super().clean()
        # vincolo radice: solo UFFICIO può non avere parent
        if self.parent is None and self.tipo != self.Tipo.UFFICIO:
            raise ValidationError({"tipo": "Le unità radice devono essere di tipo UFFICIO."})
        # vincolo figli ammessi in base al tipo del parent
        if self.parent is not None:
            ammessi = self.TIPO_FIGLI_AMMESSI.get(self.parent.tipo, set())
            if self.tipo not in ammessi:
                labels = ", ".join(sorted(self.get_tipo_display() for t in ammessi)) if ammessi else "nessuno"
                raise ValidationError({
                    "tipo": f"Per un {self.parent.get_tipo_display()} sono ammessi solo figli: {labels}."
                })
        # anti-ciclo semplice
        cur = self.parent
        while cur:
            if cur.pk == self.pk and self.pk is not None:
                raise ValidationError({"parent": "Relazione ciclica non consentita."})
            cur = cur.parent

    def save(self, *args, **kwargs):
        changed_codici = self._ensure_codici()
        self.full_clean(exclude=["full_path", "progressivo"])
        self.full_path = self.build_full_path()
        self.progressivo = self.build_progressivo()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.update({"full_path", "progressivo", "updated_at"})
            update_fields.update(changed_codici)
            kwargs["update_fields"] = list(update_fields)
        super().save(*args, **kwargs)
        # aggiorna path dei figli se cambia qualcosa
        for child in self.figli.all():
            if child.full_path != child.build_full_path():
                child.save(update_fields=["full_path", "updated_at"])

class CollocazioneFisica(models.Model):
    # target generico (Documento, Fascicolo, …)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # nuovo: collegamento diretto 1:N con Documento
    documento = models.ForeignKey(
        "documenti.Documento",
        on_delete=models.CASCADE,
        related_name="collocazioni_fisiche",
        null=True, blank=True, db_index=True,
        help_text="Se valorizzato, la collocazione è riferita a un Documento specifico."
    )

    unita = models.ForeignKey(UnitaFisica, on_delete=models.PROTECT, related_name="collocazioni")
    attiva = models.BooleanField(default=True)
    dal = models.DateField(default=timezone.now)
    al = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=250, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Collocazione fisica"
        verbose_name_plural = "Collocazioni fisiche"
        ordering = ["-attiva", "-dal", "-id"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "attiva"]),
            models.Index(fields=["documento", "attiva"]),  # per lookup veloci sul documento
        ]

    def __str__(self):
        target = self.documento or self.content_object
        return f"{target} -> {self.unita} ({'attiva' if self.attiva else 'storico'})"

    def clean(self):
        # vincolo: una sola collocazione attiva per oggetto
        from django.core.exceptions import ValidationError
        if self.attiva:
            if self.documento_id:
                qs = CollocazioneFisica.objects.filter(documento_id=self.documento_id, attiva=True)
            else:
                qs = CollocazioneFisica.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                    attiva=True,
                )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Esiste già una collocazione attiva per questo oggetto.")

    def save(self, *args, **kwargs):
        # se è legata a Documento, sincronizza anche la GFK
        if self.documento_id and (not self.content_type_id or not self.object_id):
            self.content_type = ContentType.objects.get_for_model(type(self.documento))
            self.object_id = self.documento_id
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.attiva:
                if self.documento_id:
                    type(self).objects.filter(documento_id=self.documento_id, attiva=True)\
                        .exclude(pk=self.pk).update(attiva=False, al=timezone.now().date())
                else:
                    type(self).objects.filter(content_type=self.content_type, object_id=self.object_id, attiva=True)\
                        .exclude(pk=self.pk).update(attiva=False, al=timezone.now().date())

class Ubicazione(models.Model):
    codice = models.CharField(max_length=50, unique=True)
    descrizione = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["codice"]
        verbose_name = "Ubicazione"
        verbose_name_plural = "Ubicazioni"

    def __str__(self) -> str:
        if self.descrizione:
            return f"{self.codice} — {self.descrizione}"
        return self.codice


class VerbaleConsegnaTemplate(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    descrizione = models.TextField(blank=True)
    file_template = models.FileField(
        upload_to="archivio_fisico/verbali/",
        validators=[FileExtensionValidator(["docx"])],
        max_length=500,
    )
    filename_pattern = models.CharField(
        max_length=200,
        default="verbale_{operazione_id}_{timestamp:%Y%m%d_%H%M}.docx",
        help_text=(
            "Pattern per il nome del file generato. Token disponibili: "
            "{operazione_id}, {operazione_tipo}, {operazione_tipo_display}, "
            "{timestamp:%Y%m%d}, {template_slug}. Usa sintassi Python format."
        ),
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Se attivo, diventa il template proposto di default per il download.",
    )
    attivo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template verbale di consegna"
        verbose_name_plural = "Template verbali di consegna"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome) or "verbale"
            qs = type(self).objects
            unique_slug = base_slug
            suffix = 1
            while qs.exclude(pk=self.pk).filter(slug=unique_slug).exists():
                suffix += 1
                unique_slug = f"{base_slug}-{suffix}"
            self.slug = unique_slug
        if self.is_default:
            type(self).objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class CatalogoUnitaFisica(models.Model):
    entity_type = models.CharField(max_length=20)
    entity_id = models.BigIntegerField()
    entity_codice = models.CharField(max_length=120)
    entity_descrizione = models.CharField(max_length=255)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.DO_NOTHING,
        db_column="cliente_id",
        related_name="catalogo_unita_fisica",
        db_constraint=False,
        null=True,
        blank=True,
        help_text="Anagrafica collegata alla movimentazione; la vista non applica un vincolo reale.",
    )
    movimento_id = models.BigIntegerField(primary_key=True)
    movimento_anno = models.IntegerField()
    movimento_numero = models.IntegerField()
    movimento_direzione = models.CharField(max_length=3)
    movimento_data = models.DateTimeField()
    destinatario = models.CharField(max_length=255, blank=True)
    ubicazione_id = models.BigIntegerField()
    ubicazione_codice = models.CharField(max_length=60)
    ubicazione_nome = models.CharField(max_length=120)

    class Meta:
        managed = False
        db_table = "vw_catalogo_unitafisica"
        ordering = ["movimento_data", "movimento_id"]

    def __str__(self) -> str:
        return f"{self.entity_type} {self.entity_codice} -> {self.ubicazione_codice}"


class UnitaFisicaSubunita(models.Model):
    """Vista per associare ogni unità fisica ai figli di primo livello."""

    unita_id = models.BigIntegerField()
    unita_codice = models.CharField(max_length=60)
    unita_nome = models.CharField(max_length=120)
    unita_tipo = models.CharField(max_length=20)
    unita_attivo = models.BooleanField()
    unita_archivio_fisso = models.BooleanField()
    unita_full_path = models.CharField(max_length=500)
    unita_progressivo = models.CharField(max_length=300)

    subunita_id = models.BigIntegerField(primary_key=True)
    subunita_codice = models.CharField(max_length=60)
    subunita_nome = models.CharField(max_length=120)
    subunita_tipo = models.CharField(max_length=20)
    subunita_ordine = models.IntegerField()
    subunita_attivo = models.BooleanField()
    subunita_archivio_fisso = models.BooleanField()
    subunita_full_path = models.CharField(max_length=500)
    subunita_progressivo = models.CharField(max_length=300)

    class Meta:
        managed = False
        db_table = "vw_unitafisica_subunita_primo_livello"
        ordering = ["unita_codice", "subunita_ordine", "subunita_codice"]

    def __str__(self) -> str:
        return f"{self.unita_codice} -> {self.subunita_codice}"


class ArchivioFisicoListaStampa(models.Model):
    """Riga della vista vw_archivio_fisico_lista_stampa per costruire la stampa inventariale."""

    node_key = models.CharField(max_length=64, primary_key=True)
    unit_id = models.BigIntegerField()
    unit_parent_id = models.BigIntegerField(null=True, blank=True)
    unit_codice = models.CharField(max_length=60)
    unit_nome = models.CharField(max_length=120)
    unit_tipo = models.CharField(max_length=20)
    unit_attivo = models.BooleanField()
    unit_archivio_fisso = models.BooleanField()
    unit_full_path = models.CharField(max_length=500)
    unit_progressivo = models.CharField(max_length=300)
    node_type = models.CharField(max_length=20)
    node_id = models.BigIntegerField()
    node_label = models.CharField(max_length=255)
    parent_node_type = models.CharField(max_length=20, null=True, blank=True)
    parent_node_id = models.BigIntegerField(null=True, blank=True)
    level = models.IntegerField()
    tree_sort_key = models.TextField()
    tree_path = models.TextField()
    codice = models.CharField(max_length=120, null=True, blank=True)
    titolo = models.CharField(max_length=255, null=True, blank=True)
    descrizione = models.CharField(max_length=255, null=True, blank=True)
    anno = models.IntegerField(null=True, blank=True)
    data_documento = models.DateField(null=True, blank=True)
    cliente_label = models.CharField(max_length=255, null=True, blank=True)
    protocollo_anno = models.IntegerField(null=True, blank=True)
    protocollo_numero = models.IntegerField(null=True, blank=True)
    protocollo_direzione = models.CharField(max_length=3, null=True, blank=True)
    protocollo_data = models.DateField(null=True, blank=True)
    digitale = models.BooleanField(null=True, blank=True)
    tracciabile = models.BooleanField(null=True, blank=True)
    fascicolo_parent_id = models.BigIntegerField(null=True, blank=True)
    documento_fascicolo_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "vw_archivio_fisico_lista_stampa"
        ordering = ["unit_full_path", "tree_sort_key", "node_key"]

    def __str__(self) -> str:
        return f"{self.unit_codice} [{self.node_type}] {self.node_label}"

    @cached_property
    def parent(self) -> "ArchivioFisicoListaStampa | None":
        """Nodo padre all'interno della stessa unità (usato solo per viste ad albero)."""
        if not self.parent_node_type or self.parent_node_id is None:
            return None
        return type(self).objects.filter(
            node_type=self.parent_node_type,
            node_id=self.parent_node_id,
            unit_id=self.unit_id,
        ).order_by("tree_sort_key", "node_key").first()

    @cached_property
    def children(self) -> list["ArchivioFisicoListaStampa"]:
        """Figli diretti ordinati per chiave di stampa."""
        return list(
            type(self).objects.filter(
                parent_node_type=self.node_type,
                parent_node_id=self.node_id,
                unit_id=self.unit_id,
            ).order_by("tree_sort_key", "node_key")
        )
