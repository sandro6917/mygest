from __future__ import annotations
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from anagrafiche.models import Anagrafica


# ==============================
# Tipo Pratica
# ==============================
class PraticheTipo(models.Model):
    codice = models.CharField(max_length=20, unique=True, db_index=True)
    nome = models.CharField(max_length=120)
    prefisso_codice = models.CharField(max_length=20, blank=True)
    pattern_codice = models.CharField(
        max_length=120,
        default="{CLI}-{TIPO}-{PER}-{SEQ:04d}",
        help_text=_("Pattern del codice: usa {CLI}, {TIPO}, {PER}, {SEQ:04d}")
    )

    class Meta:
        verbose_name = _("Tipo pratica")
        verbose_name_plural = _("Tipi pratica")
        ordering = ["codice"]

    def __str__(self):
        return f"{self.codice} - {self.nome}"


# ==============================
# Pratiche
# ==============================
class Pratica(models.Model):
    class Stato(models.TextChoices):
        APERTA = "aperta", _("Aperta")
        LAVORAZIONE = "lavorazione", _("In lavorazione")
        ATTESA = "attesa", _("In attesa")
        CHIUSA = "chiusa", _("Chiusa")

    class PeriodoRif(models.TextChoices):
        ANNO = "anno", _("Anno (YYYY)")
        ANNOMESE = "annomese", _("Anno-Mese (YYYYMM)")
        ANNOMESEGIORNO = "annomesegiorno", _("Anno-Mese-Giorno (YYYYMMDD)")

    # 🔹 Relazioni padre/figlio multiple
    #genitori = models.ManyToManyField(
    #    "self",
    #    through="PraticaRelazione",
    #    symmetrical=False,
    #    related_name="figli",
    #    blank=True,
    #    help_text=_("Pratiche da cui questa dipende o a cui è collegata come figlia.")
    #)

    # figli = pratiche "child" collegate a questa come "parent"
    figli = models.ManyToManyField(
        'self',
        through='PraticaRelazione',
        through_fields=('parent', 'child'),
        symmetrical=False,
        related_name='genitori',
        blank=True,
    )

    # 🔹 Dati principali
    codice = models.CharField(max_length=60, unique=True, blank=True)
    cliente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name="pratiche")
    tipo = models.ForeignKey(PraticheTipo, on_delete=models.PROTECT, related_name="pratiche")

    oggetto = models.CharField(max_length=255)
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.APERTA, db_index=True)
    responsabile = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="pratiche", null=True, blank=True)

    periodo_riferimento = models.CharField(max_length=20, choices=PeriodoRif.choices, default=PeriodoRif.ANNO, db_index=True)
    data_riferimento = models.DateField(default=timezone.now)

    periodo_key = models.CharField(max_length=8, db_index=True, editable=False)
    progressivo = models.PositiveIntegerField(default=0, editable=False)

    data_apertura = models.DateField(auto_now_add=True)
    data_chiusura = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    tag = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _("Pratica")
        verbose_name_plural = _("Pratiche")
        ordering = ["-data_apertura", "codice"]
        constraints = [
            models.UniqueConstraint(
                fields=["cliente","tipo","periodo_key","progressivo"],
                name="uniq_pratica_gruppo_prog",
            ),
        ]
        indexes = [
            models.Index(fields=["cliente","tipo","periodo_key"]),
            models.Index(fields=["stato"]),
        ]
    # ==============================
    # UTILITÀ NOMENCLATURA
    # ==============================
    @staticmethod
    def _cliente_code(cli: Anagrafica) -> str:
        cf = (cli.codice_fiscale or "").upper()
        if cli.tipo == "PG":
            base = cf[-5:] if cf.isdigit() and len(cf) >= 5 else (cli.ragione_sociale or "CLI").split()[0][:8].upper()
        else:
            base = f"{(cli.cognome or 'CLI')[:6]}{(cli.nome or '')[:1]}".upper()
        return base.replace(" ", "")

    def _build_periodo_key(self) -> str:
        d = self.data_riferimento
        if self.periodo_riferimento == self.PeriodoRif.ANNO:
            return f"{d.year:04d}"
        if self.periodo_riferimento == self.PeriodoRif.ANNOMESE:
            return f"{d.year:04d}{d.month:02d}"
        return f"{d.year:04d}{d.month:02d}{d.day:02d}"

    def _next_progressivo(self) -> int:
        last = (
            Pratica.objects.filter(cliente=self.cliente, tipo=self.tipo, periodo_key=self.periodo_key)
            .order_by("-progressivo")
            .values_list("progressivo", flat=True)
            .first()
        )
        return (last or 0) + 1

    def _format_codice(self, seq: int) -> str:
        cli_code = self._cliente_code(self.cliente)
        tipo_code = (self.tipo.prefisso_codice or self.tipo.codice).upper()
        per = self.periodo_key
        pattern = self.tipo.pattern_codice or "{CLI}-{TIPO}-{PER}-{SEQ:04d}"
        try:
            return pattern.format(CLI=cli_code, TIPO=tipo_code, PER=per, SEQ=seq)
        except Exception:
            return f"{cli_code}-{tipo_code}-{per}-{seq:04d}"

    # ==============================
    # VALIDAZIONE E SALVATAGGIO
    # ==============================
    def clean(self):
        if not self.cliente_id:
            raise ValidationError(_("Cliente obbligatorio."))
        if not self.tipo_id:
            raise ValidationError(_("Tipo pratica obbligatorio."))
        if not self.data_riferimento:
            raise ValidationError(_("Data di riferimento obbligatoria."))
        self.periodo_key = self._build_periodo_key()

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        creating = self._state.adding
        if creating and not self.progressivo:
            self.progressivo = self._next_progressivo()
        if not self.codice:
            self.codice = self._format_codice(self.progressivo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codice} - {self.oggetto}"

    # ==============================
    # FASCICOLO ASSOCIATO
    # ==============================
    def get_or_create_fascicolo(self, *, titolo=None, titolario_voce=None, anno=None):
        from fascicoli.models import Fascicolo, TitolarioVoce
        if hasattr(self, "fascicolo") and self.fascicolo_id:
            return self.fascicolo, False
        titolo = titolo or f"Fascicolo {self.codice}"
        anno = anno or self.data_riferimento.year
        if titolario_voce is None:
            titolario_voce = TitolarioVoce.objects.order_by("id").first()
            if titolario_voce is None:
                raise ValidationError("Nessuna voce di titolario disponibile.")
        fasc = Fascicolo.objects.create(
            pratica=self,
            titolo=titolo,
            titolario_voce=titolario_voce,
            anno=anno,
            cliente=self.cliente,
        )
        return fasc, True


# ==============================
# Relazioni tra pratiche
# ==============================
class PraticaRelazione(models.Model):
    TIPI = (
        ('dipendenza', 'Dipendenza'),
        ('collaborazione', 'Collaborazione'),
        # aggiungi altri tipi se servono
    )

    parent = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='relazioni_uscita',
    )
    child = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='relazioni_entrata',
    )
    tipo = models.CharField(max_length=32, choices=TIPI)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [("parent", "child")]
        indexes = [models.Index(fields=["parent"]), models.Index(fields=["child"])]

        constraints = [
            models.UniqueConstraint(
            fields=['parent', 'child', 'tipo'],
            name='uniq_relazione_parent_child_tipo',
            ),
        ]

    def clean(self):
        if self.parent_id == self.child_id:
            raise ValidationError(_("Una pratica non può essere collegata a se stessa."))

    def __str__(self):
        return f"{self.parent.codice} → {self.child.codice} ({self.tipo})"
