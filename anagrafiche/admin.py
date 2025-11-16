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
)

class IndirizzoInline(admin.TabularInline):
    model = Indirizzo
    extra = 0


class EmailContattoInline(admin.TabularInline):
    model = EmailContatto
    extra = 0

@admin.register(Anagrafica)
class AnagraficaAdmin(admin.ModelAdmin):
    list_display = ("display_name","tipo","codice","codice_fiscale","partita_iva","pec","email","telefono")
    list_filter = ("tipo",)
    search_fields = ("codice","ragione_sociale","cognome","nome","codice_fiscale","partita_iva","pec","email")
    autocomplete_fields = ()
    fieldsets = (
        (None, {"fields": ("tipo","ragione_sociale","nome","cognome")}),
        ("Identificativi", {"fields": ("codice","codice_fiscale","partita_iva")}),
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
    list_display = ("anagrafica", "email", "nominativo", "tipo", "is_preferito", "attivo")
    list_filter = ("tipo", "attivo", "is_preferito")
    search_fields = ("email", "nominativo", "anagrafica__ragione_sociale", "anagrafica__nome", "anagrafica__cognome")
    autocomplete_fields = ("anagrafica",)


class MailingListMembershipInline(admin.TabularInline):
    model = MailingListMembership
    extra = 0
    autocomplete_fields = ("contatto",)


class MailingListIndirizzoInline(admin.TabularInline):
    model = MailingListIndirizzo
    extra = 0


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "proprietario", "attiva")
    list_filter = ("attiva",)
    search_fields = ("nome", "slug", "descrizione", "proprietario__ragione_sociale", "proprietario__nome", "proprietario__cognome")
    autocomplete_fields = ("proprietario",)
    inlines = [MailingListMembershipInline, MailingListIndirizzoInline]


@admin.register(MailingListIndirizzo)
class MailingListIndirizzoAdmin(admin.ModelAdmin):
    list_display = ("mailing_list", "email", "nominativo")
    search_fields = ("email", "nominativo", "mailing_list__nome")










