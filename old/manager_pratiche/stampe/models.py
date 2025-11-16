from __future__ import annotations
from django.db import models

class StampaFormato(models.Model):
    class Orientamento(models.TextChoices):
        PORTRAIT = "P", "Verticale (portrait)"
        LANDSCAPE = "L", "Orizzontale (landscape)"

    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    larghezza_mm = models.FloatField(help_text="Larghezza pagina in millimetri")
    altezza_mm = models.FloatField(help_text="Altezza pagina in millimetri")
    orientamento = models.CharField(max_length=1, choices=Orientamento.choices, default=Orientamento.PORTRAIT)

    margine_top_mm = models.FloatField(default=5.0)
    margine_right_mm = models.FloatField(default=5.0)
    margine_bottom_mm = models.FloatField(default=5.0)
    margine_left_mm = models.FloatField(default=5.0)

    font_nome_default = models.CharField(max_length=64, default="Helvetica")
    font_size_default = models.FloatField(default=10.0)

    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Formato di stampa"
        verbose_name_plural = "Formati di stampa"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.larghezza_mm}x{self.altezza_mm} mm)"


class StampaModulo(models.Model):
    app_label = models.CharField(max_length=50, help_text="Esempio: documenti, anagrafiche, pratiche…")
    model_name = models.CharField(max_length=50, help_text="Model name in minuscolo, es: documento")
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    formato = models.ForeignKey(StampaFormato, on_delete=models.PROTECT, related_name="moduli")
    is_default = models.BooleanField(default=False, help_text="Usa come modulo predefinito per app+model")
    note = models.TextField(blank=True)

    # Scoping per Documenti: FK al tipo documento (vuoto per altre entità)
    documento_tipo = models.ForeignKey(
        "documenti.DocumentiTipo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="moduli_stampa",
        help_text="Se valorizzato, il modulo è valido solo per questo tipo documento",
    )

    font_nome = models.CharField(max_length=64, blank=True, help_text="Se vuoto usa il font del formato")
    font_size = models.FloatField(null=True, blank=True, help_text="Se vuoto usa la dimensione del formato")

    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Modulo di stampa"
        verbose_name_plural = "Moduli di stampa"
        ordering = ["app_label", "model_name", "nome"]
        unique_together = [("app_label", "model_name", "slug")]

    def __str__(self) -> str:
        return f"{self.app_label}.{self.model_name} • {self.nome}"


class StampaCampo(models.Model):
    class Tipo(models.TextChoices):
        STATIC = "static", "Testo statico"
        ATTR = "attr", "Campo da oggetto (path)"
        TEMPLATE = "template", "Template Python format"
        BARCODE = "barcode", "Barcode"
        QRCODE = "qrcode", "QR Code"

    class Align(models.TextChoices):
        LEFT = "left", "Sinistra"
        CENTER = "center", "Centro"
        RIGHT = "right", "Destra"

    modulo = models.ForeignKey(StampaModulo, on_delete=models.CASCADE, related_name="campi")
    ordine = models.PositiveIntegerField(default=0, db_index=True)
    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.ATTR)

    # contenuto
    label = models.CharField(max_length=120, blank=True, help_text="Etichetta (opzionale)")
    attr_path = models.CharField(max_length=200, blank=True, help_text="Percorso attributo (es. cliente.ragione_sociale)")
    static_value = models.TextField(blank=True, help_text="Valore per testo statico")
    template = models.CharField(max_length=400, blank=True, help_text="Python format, es: 'CF: {cliente.codice_fiscale}'")

    # posizionamento in mm (origine: angolo superiore sinistro)
    x_mm = models.FloatField(help_text="Ascissa da sinistra (mm)")
    y_mm = models.FloatField(help_text="Ordinata dall'alto (mm)")
    larghezza_mm = models.FloatField(null=True, blank=True, help_text="Larghezza area testo (wrapping). Vuoto = riga singola senza wrapping")

    # stile
    font_nome = models.CharField(max_length=64, blank=True)
    font_size = models.FloatField(null=True, blank=True)
    bold = models.BooleanField(default=False)
    italic = models.BooleanField(default=False)
    align = models.CharField(max_length=10, choices=Align.choices, default=Align.LEFT)
    max_lines = models.PositiveIntegerField(default=1)

    # specifici per barcode
    BARCODE_CHOICES = (
        ("code128", "Code128"),
        ("code39", "Code39"),
        ("ean13", "EAN-13"),
    )
    barcode_standard = models.CharField(max_length=16, choices=BARCODE_CHOICES, default="code128", blank=True)
    barcode_bar_width_mm = models.FloatField(default=0.3, help_text="Spessore barre (mm)")
    barcode_height_mm = models.FloatField(default=12.0, help_text="Altezza barre (mm)")

    # specifici per QR
    QR_ERR_CHOICES = (("L", "L"), ("M", "M"), ("Q", "Q"), ("H", "H"))
    qr_size_mm = models.FloatField(default=24.0, help_text="Lato del QR (mm)")
    qr_error = models.CharField(max_length=1, choices=QR_ERR_CHOICES, default="M", blank=True)

    visibile = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Campo modulo"
        verbose_name_plural = "Campi modulo"
        ordering = ["modulo", "ordine", "id"]

    def __str__(self) -> str:
        return f"{self.modulo.slug} • {self.label or self.attr_path or self.template or self.tipo}"


class StampaLista(models.Model):
    app_label = models.CharField(max_length=50, help_text="Esempio: documenti, anagrafiche, pratiche…")
    model_name = models.CharField(max_length=50, help_text="Model name in minuscolo, es: documento")
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    formato = models.ForeignKey(StampaFormato, on_delete=models.PROTECT, related_name="liste")
    is_default = models.BooleanField(default=False, help_text="Usa come lista predefinita per app+model")
    note = models.TextField(blank=True)

    # Filtri/ordinamenti in JSON (mappano direttamente i lookup Django)
    filter_def = models.JSONField(default=dict, blank=True, help_text='Esempio: {"cliente_id": ":cliente", "stato__in": ["APERTO","CHIUSO"]}')
    order_by = models.JSONField(default=list, blank=True, help_text='Lista di field per ordering, es. ["-data", "codice"]')

    # Stile intestazione/righe
    header_font_name = models.CharField(max_length=64, default="Helvetica-Bold", blank=True)
    header_font_size = models.FloatField(default=9.0)
    row_font_name = models.CharField(max_length=64, default="Helvetica", blank=True)
    row_font_size = models.FloatField(default=9.0)
    row_max_lines = models.PositiveIntegerField(default=2, help_text="Max righe per cella")
    row_spacing = models.FloatField(default=1.2, help_text="Moltiplicatore interlinea (es. 1.2)")
    row_height_mm = models.FloatField(null=True, blank=True, help_text="Altezza riga forzata (mm). Vuoto = calcolo automatico approssimato")

    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Lista di stampa"
        verbose_name_plural = "Liste di stampa"
        ordering = ["app_label", "model_name", "nome"]
        unique_together = [("app_label", "model_name", "slug")]

    def __str__(self) -> str:
        return f"{self.app_label}.{self.model_name} • {self.nome}"


class StampaColonna(models.Model):
    class Tipo(models.TextChoices):
        TEXT = "text", "Testo (ATTR)"
        TEMPLATE = "template", "Template Python format"
        BARCODE = "barcode", "Barcode"
        QRCODE = "qrcode", "QR Code"

    class Align(models.TextChoices):
        LEFT = "left", "Sinistra"
        CENTER = "center", "Centro"
        RIGHT = "right", "Destra"

    lista = models.ForeignKey(StampaLista, on_delete=models.CASCADE, related_name="colonne")
    ordine = models.PositiveIntegerField(default=0, db_index=True)

    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.TEXT)
    label = models.CharField(max_length=120, help_text="Intestazione colonna")
    attr_path = models.CharField(max_length=200, blank=True, help_text="Percorso attributo (es. cliente.ragione_sociale)")
    template = models.CharField(max_length=400, blank=True, help_text="Python format, es: 'CF: {obj.cliente.codice_fiscale}'")

    # dimensioni/posizionamento
    larghezza_mm = models.FloatField(help_text="Larghezza colonna (mm)")
    align = models.CharField(max_length=10, choices=Align.choices, default=Align.LEFT)

    # stile cella
    font_nome = models.CharField(max_length=64, blank=True)
    font_size = models.FloatField(null=True, blank=True)
    max_lines = models.PositiveIntegerField(null=True, blank=True)

    # barcode/qr
    BARCODE_CHOICES = (("code128", "Code128"), ("code39", "Code39"), ("ean13", "EAN-13"))
    barcode_standard = models.CharField(max_length=16, choices=BARCODE_CHOICES, default="code128", blank=True)
    barcode_bar_width_mm = models.FloatField(default=0.3)
    barcode_height_mm = models.FloatField(default=10.0)
    QR_ERR_CHOICES = (("L", "L"), ("M", "M"), ("Q", "Q"), ("H", "H"))
    qr_size_mm = models.FloatField(default=12.0)
    qr_error = models.CharField(max_length=1, choices=QR_ERR_CHOICES, default="M", blank=True)

    visibile = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Colonna lista"
        verbose_name_plural = "Colonne lista"
        ordering = ["lista", "ordine", "id"]

    def __str__(self) -> str:
        return f"{self.lista.slug} • {self.label}"
