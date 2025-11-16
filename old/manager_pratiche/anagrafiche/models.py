# anagrafiche/models.py
from __future__ import annotations
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils.text import slugify
from datetime import date
from django.urls import reverse

# ------------------------------
# VALIDATORI
# ------------------------------

_ODD_MAP = {
    **{str(i): v for i, v in zip(range(10), [1,0,5,7,9,13,15,17,19,21])},
    **dict(zip(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
               [1,0,5,7,9,13,15,17,19,21,2,4,18,20,11,3,6,8,12,14,16,10,22,25,24,23]))
}
_EVEN_MAP = {
    **{str(i): i for i in range(10)},
    **{c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
}

def _cf_pf_is_valid(cf: str) -> bool:
    """
    Verifica Codice Fiscale persona fisica (16 caratteri) con controllo del carattere di controllo.
    Regole: lettere/numeri nelle posizioni previste + checksum ufficiale.
    """
    cf = cf.upper()
    if len(cf) != 16:
        return False
    if not all(c.isalnum() for c in cf):
        return False

    # Somma pesata posizioni dispari/parI (1-based indexing)
    s = 0
    for i, ch in enumerate(cf[:15], start=1):
        if i % 2 == 1:  # posizioni dispari
            s += _ODD_MAP.get(ch, -999)
        else:          # posizioni pari
            s += _EVEN_MAP.get(ch, -999)
    if s < 0:
        return False
    expected = chr((s % 26) + ord('A'))
    return cf[15] == expected

def _piva_is_valid(piva: str) -> bool:
    """
    Verifica Partita IVA (11 cifre) secondo la regola ufficiale (mod 10).
    Usata anche per CF numerico (persone giuridiche).
    """
    if len(piva) != 11 or not piva.isdigit():
        return False
    digits = list(map(int, piva))
    # posizioni pari/dispari: algoritmo ministeriale (contando da 0 a sinistra)
    pari = sum(digits[i] for i in range(0, 10, 2))
    dispari = 0
    for i in range(1, 10, 2):
        x = digits[i] * 2
        if x > 9:
            x -= 9
        dispari += x
    check = (10 - ((pari + dispari) % 10)) % 10
    return check == digits[10]

def validate_codice_fiscale(value: str) -> None:
    """
    Valida:
      - CF persona fisica: 16 caratteri alfanumerici con checksum.
      - CF numerico (11 cifre): validato con algoritmo Partita IVA (usato per persone giuridiche).
    """
    if not value:
        raise ValidationError(_("Il codice fiscale è obbligatorio."))
    cf = value.strip().upper()

    # Accettiamo due forme: 16 alfanumerico (PF) oppure 11 numerico (PG)
    if len(cf) == 16:
        if not _cf_pf_is_valid(cf):
            raise ValidationError(_("Codice fiscale (persona fisica) non valido."))
    elif len(cf) == 11 and cf.isdigit():
        if not _piva_is_valid(cf):
            raise ValidationError(_("Codice fiscale numerico/Partita IVA non valido."))
    else:
        raise ValidationError(_("Formato codice fiscale non valido."))

def validate_piva(value: str) -> None:
    if value:
        p = value.strip()
        if not _piva_is_valid(p):
            raise ValidationError(_("Partita IVA non valida (deve avere 11 cifre e checksum corretto)."))

# ------------------------------
# MODEL
# ------------------------------

class Anagrafica(models.Model):
    class TipoSoggetto(models.TextChoices):
        PERSONA_FISICA = "PF", _("Persona fisica")
        PERSONA_GIURIDICA = "PG", _("Persona giuridica")

    tipo = models.CharField(max_length=2, choices=TipoSoggetto.choices, default=TipoSoggetto.PERSONA_FISICA, db_index=True)

    # Dati identificativi
    # PF: nome/cognome; PG: ragione_sociale
    ragione_sociale = models.CharField(max_length=200, blank=True)  # usata per PG
    nome = models.CharField(max_length=120, blank=True)             # usata per PF
    cognome = models.CharField(max_length=120, blank=True)          # usata per PF

    codice_fiscale = models.CharField(
        "Codice fiscale",
        max_length=16,  # 16 per PF; per PG accettiamo 11 cifre ma salviamo comunque qui
        unique=True,
        help_text=_("PF: 16 caratteri; PG: 11 cifre (validato come P.IVA)."),
        validators=[validate_codice_fiscale],
    )
    partita_iva = models.CharField("Partita IVA", max_length=11, blank=True, validators=[validate_piva])

    # Contatti
    pec = models.EmailField(blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    indirizzo = models.CharField(max_length=255, blank=True)

    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = _("Anagrafica")
        verbose_name_plural = _("Anagrafiche")
        ordering = ["tipo", "ragione_sociale", "cognome", "nome"]
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["codice_fiscale"]),
            models.Index(fields=["pec"]),       # nuovo indice
            models.Index(fields=["email"]),     # nuovo indice
            models.Index(fields=["telefono"]),  # nuovo indice
            models.Index(fields=["updated_at"]),  # per “ultime modificate”
        ]
        constraints = [
            # opzionale: unicità P.IVA se presente
            models.UniqueConstraint(
                fields=["partita_iva"],
                name="uniq_partita_iva_non_vuota",
                condition=~models.Q(partita_iva=""),
            ),
            # opzionale: PEC univoca se non vuota
            models.UniqueConstraint(
                fields=["pec"],
                name="uniq_pec_non_vuota",
                condition=~models.Q(pec=""),
            ),
        ]

    def clean(self):
        errors = {}
        # Requisiti minimi coerenti con il tipo
        if self.tipo == self.TipoSoggetto.PERSONA_FISICA:
            if not (self.nome or "").strip():
                errors["nome"] = _("Per le persone fisiche è obbligatorio il Nome.")
            if not (self.cognome or "").strip():
                errors["cognome"] = _("Per le persone fisiche è obbligatorio il Cognome.")
        else:  # PG
            if not (self.ragione_sociale or "").strip():
                errors["ragione_sociale"] = _("Per le persone giuridiche è obbligatoria la Ragione Sociale.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Azzeramento campi non pertinenti in base al tipo
        if self.tipo == self.TipoSoggetto.PERSONA_FISICA:
            self.ragione_sociale = ""
        else:
            self.nome = ""
            self.cognome = ""

        # Normalizzazione campi
        if self.codice_fiscale:
            self.codice_fiscale = self.codice_fiscale.strip().upper()
        if self.partita_iva:
            self.partita_iva = self.partita_iva.strip()
        if self.ragione_sociale:
            self.ragione_sociale = self.ragione_sociale.strip()
        if self.nome:
            self.nome = self.nome.strip().title()
        if self.cognome:
            self.cognome = self.cognome.strip().title()
        if self.pec:
            self.pec = self.pec.strip().lower()
        if self.email:
            self.email = self.email.strip().lower()
        if self.telefono:
            self.telefono = self.telefono.strip()
        if self.indirizzo:
            self.indirizzo = self.indirizzo.strip()
        super().save(*args, **kwargs)

    def display_name(self) -> str:
        return (
            f"{self.cognome} {self.nome}".strip()
            if self.tipo == self.TipoSoggetto.PERSONA_FISICA
            else self.ragione_sociale
        )

    def __str__(self):
        return f"{self.display_name()} ({self.codice_fiscale})"
    
    @property
    def indirizzo_principale(self):
        """
        Restituisce l'indirizzo marcato come principale (indipendentemente dal tipo).
        In caso di più principali (non dovrebbe succedere grazie al vincolo), prende il primo.
        """
        return self.indirizzi.filter(principale=True).first()

    def get_absolute_url(self):
        return reverse("anagrafiche:detail", args=[self.pk])


class AnagraficaDeletion(models.Model):
    original_id = models.IntegerField(db_index=True)
    codice_fiscale = models.CharField(max_length=16)
    display_name = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-deleted_at"]
        verbose_name = "Anagrafica cancellata"
        verbose_name_plural = "Anagrafiche cancellate"

    def __str__(self):
        return f"{self.display_name} ({self.codice_fiscale})"


class Indirizzo(models.Model):
    class TipoIndirizzo(models.TextChoices):
        RESIDENZA = "RES", _("Residenza")
        DOMICILIO = "DOM", _("Domicilio")
        SEDE_LEGALE = "SLE", _("Sede legale")
        SEDE_AMM = "SAM", _("Sede amministrativa")

    anagrafica = models.ForeignKey(
        Anagrafica,
        on_delete=models.CASCADE,
        related_name="indirizzi",
        verbose_name="Anagrafica",
    )
    tipo_indirizzo = models.CharField(
        "Tipo indirizzo",
        max_length=3,
        choices=TipoIndirizzo.choices,
    )

    # Componenti dell’indirizzo
    toponimo = models.CharField("Toponimo (via, viale, piazza…)", max_length=50, blank=True)
    indirizzo = models.CharField("Indirizzo", max_length=255)
    numero_civico = models.CharField("Numero civico", max_length=20, blank=True)
    frazione = models.CharField("Frazione", max_length=100, blank=True)
    cap = models.CharField(  # validazione spostata in clean() per gestire estero
        "CAP",
        max_length=5,
        blank=True,
    )
    comune = models.CharField("Comune", max_length=120)
    provincia = models.CharField("Provincia", max_length=2, blank=True, help_text="Sigla (es. MI)")
    nazione = models.CharField("Nazione", max_length=2, default="IT", help_text="ISO 3166-1 alpha-2 (es. IT)")

    principale = models.BooleanField("Principale", default=False)

    note = models.CharField("Note", max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Indirizzo"
        verbose_name_plural = "Indirizzi"
        indexes = [
            models.Index(fields=["anagrafica", "tipo_indirizzo"]),
            models.Index(fields=["comune", "provincia"]),
        ]
        constraints = [
            # Consente al massimo un indirizzo principale per TIPO all'interno di una stessa anagrafica
            models.UniqueConstraint(
                fields=["anagrafica", "tipo_indirizzo"],
                condition=models.Q(principale=True),
                name="uniq_indirizzo_principale_per_tipo",
            ),
        ]

    def clean(self):
        errors = {}

        # Normalizza per validazione
        naz = (self.nazione or "").strip().upper() or "IT"
        cap = (self.cap or "").strip()
        prov = (self.provincia or "").strip().upper()
        com = (self.comune or "").strip()

        if naz == "IT":
            if not com:
                errors["comune"] = _("Comune obbligatorio per indirizzi italiani.")
            if not cap or not cap.isdigit() or len(cap) != 5:
                errors["cap"] = _("Il CAP italiano deve avere 5 cifre.")
            if not prov or len(prov) != 2 or not prov.isalpha():
                errors["provincia"] = _("La provincia italiana deve essere una sigla di 2 lettere.")
        else:
            # Estero: CAP e provincia opzionali; se forniti, li accettiamo senza formato rigido
            pass

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Normalizzazione campi
        self.toponimo = (self.toponimo or "").strip()
        self.indirizzo = (self.indirizzo or "").strip()
        self.numero_civico = (self.numero_civico or "").strip()
        self.frazione = (self.frazione or "").strip()
        self.cap = (self.cap or "").strip()
        self.comune = (self.comune or "").strip().title()
        self.provincia = (self.provincia or "").strip().upper()
        self.nazione = (self.nazione or "IT").strip().upper()

        with transaction.atomic():
            # Se imposto questo come principale, disattivo gli altri dello stesso tipo per la stessa anagrafica
            if self.principale and self.anagrafica_id:
                qs = type(self).objects.filter(
                    anagrafica_id=self.anagrafica_id,
                    tipo_indirizzo=self.tipo_indirizzo,
                    principale=True,
                )
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                qs.update(principale=False)

            super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.toponimo, self.indirizzo, self.numero_civico]
        riga1 = " ".join(filter(None, parts)).strip()
        riga2 = " - ".join(filter(None, [self.cap, self.comune, self.provincia]))
        return f"{self.get_tipo_indirizzo_display()}: {riga1} ({riga2})"


class ClientiTipo(models.Model):
    """
    Tabella di classificazione dei clienti (es. Privato, Azienda, Ente, PA, VIP, ecc.)
    """
    codice = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("Identificativo breve e univoco (es. PRIV, AZI, ENTE)."),
    )
    descrizione = models.CharField(
        max_length=120,
        db_index=True,  # indice per ricerche/ordinamenti frequenti
        help_text=_("Descrizione leggibile del tipo cliente (es. Privato, Azienda)."),
    )
    # opzionale: slug per URL, derivato dal codice
    slug = models.SlugField(max_length=50, blank=True, editable=False, db_index=True)

    class Meta:
        verbose_name = "Tipo cliente"
        verbose_name_plural = "Tipi cliente"
        ordering = ["descrizione"]

    def save(self, *args, **kwargs):
        # normalizza codice e slug
        if self.codice:
            self.codice = self.codice.strip().upper()
            self.slug = slugify(self.codice)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descrizione} ({self.codice})"


class Cliente(models.Model):
    """
    Estensione 1:1 dell'anagrafica per i soli soggetti che sono clienti.
    """
    anagrafica = models.OneToOneField(
        Anagrafica,
        on_delete=models.CASCADE,
        related_name="cliente",
        verbose_name="Anagrafica",
    )
    cliente_dal = models.DateField("Cliente dal", null=True, blank=True, help_text=_("Data inizio validità come cliente."))
    cliente_al = models.DateField("Cliente al", null=True, blank=True, help_text=_("Data fine validità (opzionale)."))
    tipo_cliente = models.ForeignKey(
        ClientiTipo,
        on_delete=models.PROTECT,
        related_name="clienti",
        verbose_name="Tipo cliente",
        db_column="tipoCliente",
        help_text=_("Classificazione del cliente."),
        null=True,          # <-- ora opzionale
        blank=True,         # <-- ora opzionale
    )

    note = models.CharField("Note", max_length=255, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clienti"
        constraints = [
            # opzionale: garantisce che 'cliente_al' non preceda 'cliente_dal'
            models.CheckConstraint(
                check=models.Q(cliente_dal__isnull=True, cliente_al__isnull=True)
                     | models.Q(cliente_dal__isnull=False, cliente_al__isnull=True)
                     | models.Q(cliente_dal__isnull=False, cliente_al__isnull=False, cliente_al__gte=models.F("cliente_dal")),
                name="cliente_intervallo_date_valido",
            )
        ]
        indexes = [
            models.Index(fields=["anagrafica"]),
            models.Index(fields=["tipo_cliente"]),
        ]

    def clean(self):
        if self.cliente_dal and self.cliente_al and self.cliente_al < self.cliente_dal:
            raise ValidationError(_("La data 'Cliente al' non può precedere 'Cliente dal'."))

    @property
    def is_attivo(self) -> bool:
        """True se oggi cade nell'intervallo di validità (estremi aperti ammessi)."""
        today = date.today()
        start_ok = (self.cliente_dal is None) or (self.cliente_dal <= today)
        end_ok = (self.cliente_al is None) or (today <= self.cliente_al)
        return start_ok and end_ok

    def __str__(self):
        return f"Cliente: {self.anagrafica} - {self.tipo_cliente}"
