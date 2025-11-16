from django.contrib import admin
from .models import Anagrafica, Indirizzo, Cliente, ClientiTipo

class IndirizzoInline(admin.TabularInline):
    model = Indirizzo
    extra = 0

@admin.register(Anagrafica)
class AnagraficaAdmin(admin.ModelAdmin):
    list_display = ("display_name","tipo","codice_fiscale","partita_iva","pec","email","telefono")
    list_filter = ("tipo",)
    search_fields = ("ragione_sociale","cognome","nome","codice_fiscale","partita_iva","pec","email")
    autocomplete_fields = ()
    fieldsets = (
        (None, {"fields": ("tipo","ragione_sociale","nome","cognome")}),
        ("Identificativi", {"fields": ("codice_fiscale","partita_iva")}),
        ("Contatti", {"fields": ("pec","email","telefono","indirizzo")}),
        ("Altro", {"fields": ("note",)}),
    )
    inlines = [IndirizzoInline]

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("anagrafica", "tipo_cliente", "cliente_dal", "cliente_al", "is_attivo")
    list_filter = ("tipo_cliente",)
    search_fields = ("anagrafica__ragione_sociale", "anagrafica__nome", "anagrafica__cognome")
    autocomplete_fields = ("anagrafica", "tipo_cliente")
    list_select_related = ("anagrafica", "tipo_cliente")

@admin.register(ClientiTipo)
class ClientiTipoAdmin(admin.ModelAdmin):
    list_display = ("descrizione", "codice")
    search_fields = ("descrizione", "codice")










