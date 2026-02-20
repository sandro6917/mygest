from __future__ import annotations

from django.contrib import admin

from .models import Scadenza, ScadenzaAlert, ScadenzaNotificaLog, ScadenzaOccorrenza, ScadenzaWebhookPayload, CodiceTributoF24


class ScadenzaAlertInline(admin.TabularInline):
    """Inline per gestire alert multipli per ogni occorrenza."""
    model = ScadenzaAlert
    extra = 1
    fields = (
        "offset_alert",
        "offset_alert_periodo",
        "metodo_alert",
        "alert_programmata_il",
        "stato",
        "alert_inviata_il",
    )
    readonly_fields = ("alert_programmata_il", "alert_inviata_il")


class ScadenzaOccorrenzaInline(admin.TabularInline):
    model = ScadenzaOccorrenza
    extra = 1
    fields = (
        "titolo",
        "inizio",
        "giornaliera",
        "metodo_alert",
        "offset_alert_minuti",
        "stato",
        "google_calendar_event_id",
    )
    readonly_fields = ("google_calendar_event_id", "alert_inviata_il")


@admin.register(Scadenza)
class ScadenzaAdmin(admin.ModelAdmin):
    list_display = (
        "titolo",
        "stato",
        "priorita",
        "creato_il",
        "aggiornato_il",
    )
    list_filter = (
        "stato",
        "priorita",
        "periodicita",
    )
    search_fields = ("titolo", "descrizione", "categoria")
    filter_horizontal = ("assegnatari", "pratiche", "fascicoli", "documenti")
    inlines = [ScadenzaOccorrenzaInline]


@admin.register(ScadenzaOccorrenza)
class ScadenzaOccorrenzaAdmin(admin.ModelAdmin):
    list_display = (
        "scadenza",
        "inizio",
        "giornaliera",
        "metodo_alert",
        "stato",
        "alert_programmata_il",
    )
    list_filter = ("metodo_alert", "stato", "giornaliera")
    search_fields = ("scadenza__titolo", "titolo")
    autocomplete_fields = ("scadenza", "comunicazione")
    inlines = [ScadenzaAlertInline]


@admin.register(ScadenzaAlert)
class ScadenzaAlertAdmin(admin.ModelAdmin):
    """Admin per gestire gli alert individuali."""
    list_display = (
        "occorrenza",
        "offset_alert",
        "offset_alert_periodo",
        "metodo_alert",
        "alert_programmata_il",
        "stato",
    )
    list_filter = ("metodo_alert", "stato", "offset_alert_periodo")
    search_fields = ("occorrenza__scadenza__titolo", "occorrenza__titolo")
    autocomplete_fields = ("occorrenza",)
    readonly_fields = ("alert_programmata_il", "creato_il", "aggiornato_il")
    fieldsets = (
        ("Occorrenza", {
            "fields": ("occorrenza",)
        }),
        ("Configurazione Alert", {
            "fields": (
                "offset_alert",
                "offset_alert_periodo",
                "metodo_alert",
                "alert_config",
            )
        }),
        ("Stato e Tracking", {
            "fields": (
                "stato",
                "alert_programmata_il",
                "alert_inviata_il",
                "creato_il",
                "aggiornato_il",
            )
        }),
    )


@admin.register(ScadenzaNotificaLog)
class ScadenzaNotificaLogAdmin(admin.ModelAdmin):
    list_display = ("occorrenza", "evento", "esito", "registrato_il")
    list_filter = ("evento", "esito")
    search_fields = ("occorrenza__scadenza__titolo", "messaggio")
    readonly_fields = ("registrato_il",)


@admin.register(ScadenzaWebhookPayload)
class ScadenzaWebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ("occorrenza", "destinazione", "inviato_il", "risposta_status")
    search_fields = ("destinazione",)
    readonly_fields = ("payload", "risposta_body", "inviato_il")


@admin.register(CodiceTributoF24)
class CodiceTributoF24Admin(admin.ModelAdmin):
    list_display = (
        "codice",
        "sezione",
        "descrizione_breve",
        "causale",
        "periodicita",
        "attivo",
        "validita_oggi",
    )
    list_filter = ("sezione", "attivo", "periodicita")
    search_fields = ("codice", "descrizione", "causale")
    readonly_fields = ("data_creazione", "data_modifica")
    
    fieldsets = (
        ("Informazioni Base", {
            "fields": ("codice", "sezione", "descrizione", "causale")
        }),
        ("Dettagli", {
            "fields": ("periodicita", "note")
        }),
        ("Validità", {
            "fields": ("attivo", "data_inizio_validita", "data_fine_validita")
        }),
        ("Metadata", {
            "fields": ("data_creazione", "data_modifica"),
            "classes": ("collapse",)
        }),
    )
    
    def descrizione_breve(self, obj):
        """Mostra solo i primi 50 caratteri della descrizione."""
        return obj.descrizione[:50] + "..." if len(obj.descrizione) > 50 else obj.descrizione
    descrizione_breve.short_description = "Descrizione"
    
    def validita_oggi(self, obj):
        """Mostra se il codice è valido oggi."""
        return "✓" if obj.is_valido_oggi() else "✗"
    validita_oggi.short_description = "Valido oggi"
    validita_oggi.boolean = True
    
    actions = ["attiva_codici", "disattiva_codici"]
    
    def attiva_codici(self, request, queryset):
        """Attiva i codici tributo selezionati."""
        updated = queryset.update(attivo=True)
        self.message_user(request, f"{updated} codici tributo attivati.")
    attiva_codici.short_description = "Attiva codici selezionati"
    
    def disattiva_codici(self, request, queryset):
        """Disattiva i codici tributo selezionati."""
        updated = queryset.update(attivo=False)
        self.message_user(request, f"{updated} codici tributo disattivati.")
    disattiva_codici.short_description = "Disattiva codici selezionati"
