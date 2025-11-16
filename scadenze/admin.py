from __future__ import annotations

from django.contrib import admin

from .models import Scadenza, ScadenzaNotificaLog, ScadenzaOccorrenza, ScadenzaWebhookPayload


class ScadenzaOccorrenzaInline(admin.TabularInline):
    model = ScadenzaOccorrenza
    extra = 1
    fields = (
        "titolo",
        "inizio",
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
        "metodo_alert",
        "stato",
        "alert_programmata_il",
    )
    list_filter = ("metodo_alert", "stato")
    search_fields = ("scadenza__titolo", "titolo")
    autocomplete_fields = ("scadenza", "comunicazione")


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
