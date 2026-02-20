from django.contrib import admin
from .models import (
    Anagrafica,
    Indirizzo,
    Cliente,
    ClientiTipo,
    EmailContatto,
    MailingList,
    MailingListMembership,
    MailingListIndirizzo,
    MailingListUnsubscribeToken,
)
from .models_comuni import ComuneItaliano

class IndirizzoInline(admin.TabularInline):
    model = Indirizzo
    extra = 0


class EmailContattoInline(admin.TabularInline):
    model = EmailContatto
    extra = 0

@admin.register(Anagrafica)
class AnagraficaAdmin(admin.ModelAdmin):
    list_display = ("display_name","tipo","codice","codice_fiscale","partita_iva","denominazione_abbreviata","pec","email","telefono")
    list_filter = ("tipo",)
    search_fields = ("codice","ragione_sociale","cognome","nome","codice_fiscale","partita_iva","denominazione_abbreviata","pec","email")
    autocomplete_fields = ()
    fieldsets = (
        (None, {"fields": ("tipo","ragione_sociale","nome","cognome")}),
        ("Identificativi", {"fields": ("codice","codice_fiscale","partita_iva","denominazione_abbreviata")}),
        ("Contatti", {"fields": ("pec","email","telefono","indirizzo")}),
        ("Altro", {"fields": ("note",)}),
    )
    inlines = [IndirizzoInline, EmailContattoInline]

    actions = ["genera_cli"]

    def genera_cli(self, request, queryset):
        # genera il CLI (6+2) solo se mancante; se già presente, lo lascia invariato
        from .utils import get_or_generate_cli
        creati = invariati = 0
        for a in queryset:
            before = (a.codice or "").strip()
            code = get_or_generate_cli(a)
            if not before and code:
                creati += 1
            else:
                invariati += 1
        self.message_user(request, f"CLI generato per {creati} anagrafiche; invariato per {invariati}.")
    genera_cli.short_description = "Genera CLI per le anagrafiche selezionate"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("anagrafica", "tipo_cliente", "codice_destinatario", "cliente_dal", "cliente_al", "is_attivo")
    list_filter = ("tipo_cliente",)
    search_fields = ("anagrafica__ragione_sociale", "anagrafica__nome", "anagrafica__cognome", "codice_destinatario")
    autocomplete_fields = ("anagrafica", "tipo_cliente")
    list_select_related = ("anagrafica", "tipo_cliente")

@admin.register(ClientiTipo)
class ClientiTipoAdmin(admin.ModelAdmin):
    list_display = ("descrizione", "codice")
    search_fields = ("descrizione", "codice")


@admin.register(EmailContatto)
class EmailContattoAdmin(admin.ModelAdmin):
    list_display = ("anagrafica", "email", "nominativo", "tipo", "is_preferito", "attivo", "marketing_consent")
    list_filter = ("tipo", "attivo", "is_preferito", "marketing_consent")
    search_fields = ("email", "nominativo", "anagrafica__ragione_sociale", "anagrafica__nome", "anagrafica__cognome")
    autocomplete_fields = ("anagrafica",)
    readonly_fields = ("marketing_consent_acquired_at",)


class MailingListMembershipInline(admin.TabularInline):
    model = MailingListMembership
    extra = 0
    autocomplete_fields = ("contatto",)
    readonly_fields = ("disiscritto_il",)


class MailingListIndirizzoInline(admin.TabularInline):
    model = MailingListIndirizzo
    extra = 0
    readonly_fields = ("marketing_consent_acquired_at", "disiscritto_il")


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "proprietario", "finalita", "attiva")
    list_filter = ("finalita", "attiva")
    search_fields = ("nome", "slug", "descrizione", "proprietario__ragione_sociale", "proprietario__nome", "proprietario__cognome")
    autocomplete_fields = ("proprietario",)
    inlines = [MailingListMembershipInline, MailingListIndirizzoInline]


@admin.register(MailingListIndirizzo)
class MailingListIndirizzoAdmin(admin.ModelAdmin):
    list_display = ("mailing_list", "email", "nominativo", "marketing_consent")
    search_fields = ("email", "nominativo", "mailing_list__nome")
    list_filter = ("marketing_consent",)


@admin.register(MailingListUnsubscribeToken)
class MailingListUnsubscribeTokenAdmin(admin.ModelAdmin):
    list_display = ("mailing_list", "email", "token", "created_at", "used_at")
    search_fields = ("email", "token", "mailing_list__nome")
    list_filter = ("mailing_list", "used_at")


@admin.register(ComuneItaliano)
class ComuneItalianoAdmin(admin.ModelAdmin):
    list_display = ("nome", "provincia", "cap", "regione", "codice_istat", "codice_belfiore", "flag_capoluogo", "attivo")
    list_filter = ("provincia", "regione", "flag_capoluogo", "attivo")
    search_fields = ("nome", "nome_alternativo", "cap", "codice_istat", "codice_belfiore", "provincia")
    list_per_page = 50
    ordering = ("nome",)
    fieldsets = (
        ("Identificazione", {
            "fields": ("codice_istat", "codice_belfiore", "nome", "nome_alternativo")
        }),
        ("Ubicazione", {
            "fields": ("provincia", "nome_provincia", "regione", "codice_regione", "cap")
        }),
        ("Metadati", {
            "fields": ("flag_capoluogo", "latitudine", "longitudine")
        }),
        ("Gestione", {
            "fields": ("attivo", "note"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at", "updated_at")
    
    actions = ["attiva_comuni", "disattiva_comuni"]
    
    def attiva_comuni(self, request, queryset):
        count = queryset.update(attivo=True)
        self.message_user(request, f"{count} comuni attivati.")
    attiva_comuni.short_description = "Attiva comuni selezionati"
    
    def disattiva_comuni(self, request, queryset):
        count = queryset.update(attivo=False)
        self.message_user(request, f"{count} comuni disattivati.")
    disattiva_comuni.short_description = "Disattiva comuni selezionati"







