from django.contrib import admin, messages
from django.db import models

from .models import AllegatoComunicazione, Comunicazione, EmailImport, Mailbox
from .models_template import FirmaComunicazione, TemplateComunicazione, TemplateContextField
class TemplateContextFieldInline(admin.TabularInline):
    model = TemplateContextField
    extra = 0
    fields = (
        "ordering",
        "active",
        "key",
        "label",
        "field_type",
        "required",
        "default_value",
        "choices",
        "source_path",
        "help_text",
    )
    ordering = ("ordering", "id")
    show_change_link = True

from .tasks import sincronizza_mailbox

@admin.register(Comunicazione)
class ComunicazioneAdmin(admin.ModelAdmin):
    list_display = (
        "oggetto",
        "tipo",
        "direzione",
        "anagrafica",
        "data_creazione",
        "stato",
        "protocollo_display",
        "import_source",
    )
    search_fields = ("oggetto", "destinatari", "corpo", "protocollo_movimento__numero", "email_message_id")
    list_filter = ("tipo", "direzione", "stato", "data_creazione", "import_source")
    date_hierarchy = "data_creazione"
    autocomplete_fields = ("anagrafica", "documento_protocollo")
    readonly_fields = ("protocollo_movimento", "importato_il", "import_source", "email_message_id")
    filter_horizontal = ("contatti_destinatari", "liste_destinatari")

    def protocollo_display(self, obj):
        return obj.protocollo_label or "—"

    protocollo_display.short_description = "Protocollo"

@admin.register(AllegatoComunicazione)
class AllegatoComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("comunicazione", "documento")
    search_fields = ("comunicazione__oggetto", "documento__codice")


@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    list_display = ("nome", "host", "username", "cartella", "attiva", "ultima_lettura")
    list_filter = ("attiva",)
    search_fields = ("nome", "host", "username")
    actions = ("importa_email",)

    @admin.action(description="Importa nuove email dalle caselle selezionate")
    def importa_email(self, request, queryset):
        total_imported = 0
        for mailbox in queryset:
            try:
                total_imported += sincronizza_mailbox(mailbox)
            except Exception as exc:
                messages.error(request, f"Errore importando {mailbox.nome}: {exc}")
        if total_imported:
            messages.success(request, f"Importate {total_imported} nuove email.")
        else:
            messages.warning(request, "Nessuna nuova email trovata.")


@admin.register(EmailImport)
class EmailImportAdmin(admin.ModelAdmin):
    list_display = ("mailbox", "oggetto", "mittente", "importato_il", "comunicazione")
    list_filter = ("mailbox",)
    search_fields = ("oggetto", "mittente", "destinatari", "message_id")
    autocomplete_fields = ("mailbox", "comunicazione")
    actions = ("elimina_comunicazioni_collegate",)

    @admin.action(description="Elimina le comunicazioni collegate alle email selezionate")
    def elimina_comunicazioni_collegate(self, request, queryset):
        deleted = 0
        for email_import in queryset.select_related("comunicazione"):
            comunicazione = email_import.comunicazione
            if not comunicazione:
                continue
            try:
                comunicazione.delete()
                deleted += 1
            except Exception as exc:
                messages.error(request, f"Errore eliminando la comunicazione {comunicazione.pk}: {exc}")
        if deleted:
            messages.success(request, f"Eliminate {deleted} comunicazioni collegate.")
        else:
            messages.warning(request, "Nessuna comunicazione collegata trovata da eliminare.")


@admin.register(TemplateComunicazione)
class TemplateComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    list_filter = ("attivo", "data_modifica")
    search_fields = ("nome", "oggetto", "corpo_testo", "corpo_html")
    ordering = ("-data_modifica",)
    readonly_fields = ("data_creazione", "data_modifica")
    inlines = [TemplateContextFieldInline]
    fieldsets = (
        (None, {"fields": ("nome", "attivo")} ),
        ("Contenuto", {"fields": ("oggetto", "corpo_testo", "corpo_html")} ),
        ("Tracciamento", {"fields": ("data_creazione", "data_modifica"), "classes": ("collapse",)} ),
    )
    formfield_overrides = {
        models.TextField: {
            "widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 10, "cols": 100}),
        }
    }


@admin.register(FirmaComunicazione)
class FirmaComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    list_filter = ("attivo",)
    search_fields = ("nome", "corpo_testo", "corpo_html")
    ordering = ("nome",)
    readonly_fields = ("data_creazione", "data_modifica")
    fieldsets = (
        (None, {"fields": ("nome", "attivo")} ),
        ("Contenuto", {"fields": ("corpo_testo", "corpo_html")} ),
        ("Tracciamento", {"fields": ("data_creazione", "data_modifica"), "classes": ("collapse",)} ),
    )
    formfield_overrides = {
        models.TextField: {
            "widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 8, "cols": 100}),
        }
    }
