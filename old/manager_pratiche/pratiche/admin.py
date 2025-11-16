from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

from .models import Pratica, PraticheTipo, PraticaRelazione


@admin.register(PraticheTipo)
class PraticheTipoAdmin(admin.ModelAdmin):
    list_display = ("codice", "nome", "prefisso_codice", "pattern_codice")
    search_fields = ("codice", "nome")


class FigliInline(admin.TabularInline):
    model = PraticaRelazione
    fk_name = "parent"
    extra = 0
    autocomplete_fields = ("child",)
    fields = ("child", "tipo", "note")
    verbose_name = "Collegamento a figlio"
    verbose_name_plural = "Collegamenti a figli"


class GenitoriInline(admin.TabularInline):
    model = PraticaRelazione
    fk_name = "child"
    extra = 0
    autocomplete_fields = ("parent",)
    fields = ("parent", "tipo", "note")
    verbose_name = "Collegamento a padre"
    verbose_name_plural = "Collegamenti a padri"


@admin.register(Pratica)
class PraticaAdmin(admin.ModelAdmin):
    """
    Soluzione 1:
    - Nessun campo 'fascicolo' in creazione pratica (relazione OneToOne gestita dal modello Fascicolo).
    - Dopo il salvataggio:
        * se il fascicolo esiste, mostra link alla change view del fascicolo
        * se non esiste, mostra link "Crea fascicolo" con pratica precompilata.
    """
    inlines = [GenitoriInline, FigliInline]

    list_display = (
        "codice",
        "cliente",
        "tipo",
        "oggetto",
        "stato",
        "periodo_key",
        "progressivo",
        "data_apertura",
        "link_fascicolo",
    )
    list_filter = ("stato", "tipo", "periodo_riferimento", "data_apertura")
    search_fields = (
        "codice",
        "oggetto",
        "cliente__anagrafica__ragione_sociale",
        "cliente__anagrafica__nome",
        "cliente__anagrafica__cognome",
        "tag",
    )
    autocomplete_fields = ("cliente", "responsabile", "tipo")

    readonly_fields = ("periodo_key", "progressivo", "data_apertura")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "codice",
                    "cliente",
                    "tipo",
                    "oggetto",
                    "stato",
                    "responsabile",
                    "note",
                    "tag",
                )
            },
        ),
        (
            "Periodo",
            {
                "fields": (
                    "periodo_riferimento",
                    "data_riferimento",
                    "periodo_key",
                    "progressivo",
                )
            },
        ),
        ("Date", {"fields": ("data_apertura", "data_chiusura")}),
    )

    def link_fascicolo(self, obj: Pratica):
        """
        Mostra:
        - link al fascicolo se già presente;
        - altrimenti, link "Crea fascicolo" con ?pratica=<id> preimpostato.
        """
        if not obj.pk:
            return "—"
        # se esiste fascicolo collegato
        if hasattr(obj, "fascicolo") and obj.fascicolo_id:
            url = reverse("admin:fascicoli_fascicolo_change", args=[obj.fascicolo_id])
            return format_html('<a href="{}">{}</a>', url, obj.fascicolo.codice)

        # link per creare un nuovo fascicolo con pratica precompilata
        add_url = reverse("admin:fascicoli_fascicolo_add")
        qs = urlencode({"pratica": obj.pk})
        return format_html('<a href="{}?{}">➕ Crea fascicolo</a>', add_url, qs)

    link_fascicolo.short_description = "Fascicolo"
