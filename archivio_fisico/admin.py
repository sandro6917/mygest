from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count

from .forms import OperazioneArchivioForm, RigaOperazioneArchivioForm
from .models import (
    CollocazioneFisica,
    CatalogoUnitaFisica,
    OperazioneArchivio,
    RigaOperazioneArchivio,
    UnitaFisica,
    Ubicazione,
    VerbaleConsegnaTemplate,
)
from .services import process_operazione_archivio

@admin.register(UnitaFisica)
class UnitaFisicaAdmin(admin.ModelAdmin):
    list_display = ("id","codice", "prefisso_codice", "progressivo_codice", "nome", "progressivo", "full_path")
    search_fields = ("codice", "prefisso_codice", "nome", "progressivo", "full_path")

@admin.register(CollocazioneFisica)
class CollocazioneFisicaAdmin(admin.ModelAdmin):
    list_display = ("id", "unita", "attiva", "dal", "al")
    search_fields = ("unita__codice", "unita__nome", "unita__full_path")
    autocomplete_fields = ("unita",)
    list_select_related = ("unita",)

@admin.register(Ubicazione)
class UbicazioneAdmin(admin.ModelAdmin):
    list_display = ("codice", "descrizione")
    search_fields = ("codice", "descrizione")


@admin.register(VerbaleConsegnaTemplate)
class VerbaleConsegnaTemplateAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "is_default", "attivo", "updated_at")
    list_filter = ("attivo", "is_default")
    search_fields = ("nome", "slug", "descrizione")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CatalogoUnitaFisica)
class CatalogoUnitaFisicaAdmin(admin.ModelAdmin):
    list_display = (
        "movimento_id",
        "entity_type",
        "entity_codice",
        "movimento_direzione",
        "movimento_data",
        "ubicazione_codice",
    )
    list_filter = ("movimento_direzione", "entity_type")
    search_fields = ("entity_codice", "entity_descrizione", "ubicazione_codice", "ubicazione_nome")
    ordering = ("-movimento_data", "movimento_id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RigaOperazioneArchivioInline(admin.TabularInline):
    model = RigaOperazioneArchivio
    form = RigaOperazioneArchivioForm
    extra = 0
    min_num = 1
    autocomplete_fields = (
        "fascicolo",
        "documento",
        "movimento_protocollo",
        "unita_fisica_sorgente",
        "unita_fisica_destinazione",
    )
    fields = (
        "fascicolo",
        "documento",
        "movimento_protocollo",
        "unita_fisica_sorgente",
        "unita_fisica_destinazione",
        "stato_precedente",
        "stato_successivo",
        "note",
    )


@admin.register(OperazioneArchivio)
class OperazioneArchivioAdmin(admin.ModelAdmin):
    form = OperazioneArchivioForm
    inlines = [RigaOperazioneArchivioInline]
    list_display = (
        "id",
        "tipo_operazione",
        "data_ora",
        "referente_interno",
        "referente_esterno",
        "sorgenti_display",
        "destinazioni_display",
        "righe_count",
    )
    list_filter = ("tipo_operazione", "referente_interno")
    search_fields = (
        "note",
        "referente_interno__username",
        "referente_interno__first_name",
        "referente_interno__last_name",
        "referente_esterno__nome",
        "referente_esterno__cognome",
        "referente_esterno__ragione_sociale",
    )
    readonly_fields = ("data_ora",)
    autocomplete_fields = (
        "referente_interno",
        "referente_esterno",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "referente_interno",
            "referente_esterno",
        ).prefetch_related(
            "righe__unita_fisica_sorgente",
            "righe__unita_fisica_destinazione",
        ).annotate(_righe_count=Count("righe"))

    @admin.display(description="Righe")
    def righe_count(self, obj):
        return getattr(obj, "_righe_count", obj.righe.count())

    @admin.display(description="Sorgenti")
    def sorgenti_display(self, obj):
        sorgenti = {
            riga.unita_fisica_sorgente
            for riga in obj.righe.all()
            if getattr(riga, "unita_fisica_sorgente", None)
        }
        if not sorgenti:
            return "-"
        return ", ".join(
            sorted(
                (
                    unita.full_path
                    or getattr(unita, "codice", "")
                    or unita.nome
                    or str(unita.pk)
                )
                for unita in sorgenti
            )
        )

    @admin.display(description="Destinazioni")
    def destinazioni_display(self, obj):
        destinazioni = {
            riga.unita_fisica_destinazione
            for riga in obj.righe.all()
            if getattr(riga, "unita_fisica_destinazione", None)
        }
        if not destinazioni:
            return "-"
        return ", ".join(
            sorted(
                (
                    unita.full_path
                    or getattr(unita, "codice", "")
                    or unita.nome
                    or str(unita.pk)
                )
                for unita in destinazioni
            )
        )

    def save_related(self, request, form, formsets, change):
        try:
            with transaction.atomic():
                super().save_related(request, form, formsets, change)
                process_operazione_archivio(form.instance)
        except ValidationError as exc:
            form.add_error(None, exc)
            messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
            raise
