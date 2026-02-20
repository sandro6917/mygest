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
        "destinatario_anagrafica__ragione_sociale",
        "destinatario_anagrafica__cognome",
        "destinatario_anagrafica__nome",
        "destinatario_anagrafica__codice_fiscale",
        "destinatario",
        "target_label",
    )
    raw_id_fields = ("documento", "fascicolo")
    autocomplete_fields = ("cliente", "ubicazione", "destinatario_anagrafica")

    def oggetto(self, obj):
        return obj.documento or obj.fascicolo or obj.target_label or obj.target_object
    oggetto.short_description = "Oggetto"
