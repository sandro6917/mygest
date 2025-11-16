from django.contrib import admin
from .models import MovimentoProtocollo, ProtocolloCounter

@admin.register(MovimentoProtocollo)
class MovimentoProtocolloAdmin(admin.ModelAdmin):
    list_display = ("oggetto", "cliente", "direzione", "anno", "numero", "data", "chiuso")
    list_filter = ("direzione", "chiuso", "anno")
    search_fields = (
        "documento__descrizione",
        "fascicolo__titolo",
        "fascicolo__codice",
        "cliente__ragione_sociale",
        "cliente__cognome",
        "cliente__nome",
        "cliente__codice_fiscale",
        "cliente__codice",
        "destinatario",
    )
    raw_id_fields = ("documento", "fascicolo")
    autocomplete_fields = ("cliente", "ubicazione")

    def oggetto(self, obj):
        return obj.documento or obj.fascicolo
    oggetto.short_description = "Oggetto"
