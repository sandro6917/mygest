from django.apps import apps
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.db import connection, transaction
from django.template.response import TemplateResponse

from .models import Fascicolo, TitolarioVoce


def _has_titolario_table() -> bool:
    try:
        tables = set(connection.introspection.table_names())
        return "vocititolario" in tables or "titolario_titolariovoce" in tables
    except Exception:
        return False


class SubFascicoloInline(admin.TabularInline):
    model = Fascicolo
    fk_name = "parent"
    extra = 0
    fields = ("codice", "titolo", "stato", "sub_progressivo")
    readonly_fields = ("codice", "sub_progressivo")
    show_change_link = True


@admin.register(Fascicolo)
class FascicoloAdmin(admin.ModelAdmin):
    list_display = (
        "codice",
        "titolo",
        "cliente",
        "titolario_voce",
        "anno",
        "stato",
        "parent",
        "progressivo",
        "sub_progressivo",
        "ubicazione_display",
        "has_path",
    )
    list_filter = ("stato", "anno")
    search_fields = (
        "codice",
        "titolo",
        "cliente__anagrafica__ragione_sociale",
        "cliente__anagrafica__cognome",
        "cliente__anagrafica__nome",
        "ubicazione__codice",
        "ubicazione__nome",
        "ubicazione__full_path",
    )
    list_select_related = ("cliente", "titolario_voce", "parent", "ubicazione")
    autocomplete_fields = ("cliente", "titolario_voce", "parent", "ubicazione")
    date_hierarchy = "created_at"
    ordering = ("cliente", "anno", "codice")

    readonly_fields = (
        "codice",
        "progressivo",
        "sub_progressivo",
        "path_archivio",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (None, {"fields": ("cliente", "titolario_voce", "titolo", "stato")}),
        ("Gerarchia", {"fields": ("parent", "progressivo", "sub_progressivo")}),
        ("Identificativi", {"fields": ("codice", "anno", "retention_anni")}),
        ("Archivio", {"fields": ("ubicazione", "path_archivio")}),
        ("Note", {"fields": ("note",)}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    inlines = [SubFascicoloInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # evita join a tabelle mancanti in ambienti senza migrazioni titolario
        if _has_titolario_table():
            return qs.select_related("cliente", "titolario_voce", "parent", "ubicazione")
        return qs.select_related("cliente", "parent", "ubicazione")

    def ubicazione_display(self, obj: Fascicolo):
        return getattr(obj.ubicazione, "full_path", "") or getattr(obj.ubicazione, "nome", "") or ""
    ubicazione_display.short_description = "Ubicazione"

    def has_path(self, obj: Fascicolo) -> bool:
        return bool((obj.path_archivio or "").strip())
    has_path.boolean = True
    has_path.short_description = "Path"

    actions = ("crea_directory_archivio", "modifica_titolario_fascicolo")

    def crea_directory_archivio(self, request, queryset):
        # Forza la creazione/aggiornamento del path archivio delegando alla save del modello
        creati = 0
        for f in queryset:
            before = (f.path_archivio or "").strip()
            f.save()  # la logica del modello crea/aggiorna la dir e path_archivio
            after = (f.path_archivio or "").strip()
            if after and after != before:
                creati += 1
        self.message_user(request, f"Directory archivio create/aggiornate per {creati} fascicoli.")
    crea_directory_archivio.short_description = "Crea/Aggiorna directory di archivio"

    @admin.action(description="Duplica e cambia titolario (con copia collegamenti ed elimina originale)")
    def modifica_titolario_fascicolo(self, request, queryset):
        if request.POST.get("apply"):
            form = ModificaTitolarioFascicoloForm(request.POST)
            if form.is_valid():
                new_titolario = form.cleaned_data["titolario_voce"]
                Documento = apps.get_model("documenti", "Documento")
                MovimentoProtocollo = apps.get_model("protocollo", "MovimentoProtocollo")
                RigaOperazioneArchivio = apps.get_model("archivio_fisico", "RigaOperazioneArchivio")

                success_count = 0
                error_count = 0

                for originale in queryset.select_related("parent", "cliente", "titolario_voce"):
                    if originale.parent_id and originale.parent.titolario_voce_id != new_titolario.pk:
                        self.message_user(
                            request,
                            f"Impossibile aggiornare {originale}: il parent ha un titolario differente.",
                            level=messages.ERROR,
                        )
                        error_count += 1
                        continue

                    if originale.sottofascicoli.exists():
                        self.message_user(
                            request,
                            f"Impossibile aggiornare {originale}: presenta sottofascicoli. Gestirli prima dell'operazione.",
                            level=messages.ERROR,
                        )
                        error_count += 1
                        continue

                    try:
                        with transaction.atomic():
                            clone = Fascicolo()
                            for field in Fascicolo._meta.concrete_fields:
                                if field.primary_key or field.attname in {"codice", "progressivo", "sub_progressivo", "path_archivio"}:
                                    continue
                                setattr(clone, field.attname, getattr(originale, field.attname))

                            old_titolario_id = originale.titolario_voce_id
                            clone.titolario_voce = new_titolario
                            clone.codice = ""
                            clone.progressivo = 0
                            clone.sub_progressivo = 0
                            clone.path_archivio = ""
                            clone.save()

                            clone.pratiche.set(originale.pratiche.all())

                            Documento.objects.filter(fascicolo=originale).update(fascicolo=clone)
                            MovimentoProtocollo.objects.filter(fascicolo=originale).update(fascicolo=clone)
                            RigaOperazioneArchivio.objects.filter(fascicolo=originale).update(fascicolo=clone)
                            Documento.objects.filter(fascicolo=clone, titolario_voce_id=old_titolario_id).update(titolario_voce=new_titolario)

                            originale.delete()
                            success_count += 1
                    except Exception as exc:
                        error_count += 1
                        self.message_user(
                            request,
                            f"Errore durante la duplicazione del fascicolo {originale}: {exc}",
                            level=messages.ERROR,
                        )

                if success_count and not error_count:
                    self.message_user(request, f"{success_count} fascicolo/i duplicati con il nuovo titolario.")
                elif success_count and error_count:
                    self.message_user(
                        request,
                        f"{success_count} fascicolo/i duplicati. {error_count} operazione/i non riuscite.",
                        level=messages.WARNING,
                    )
                elif not success_count and not error_count:
                    self.message_user(request, "Nessuna operazione eseguita.", level=messages.INFO)
                return None
        else:
            form = ModificaTitolarioFascicoloForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "fascicoli": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": "modifica_titolario_fascicolo",
            "opts": self.model._meta,
            "title": "Duplica fascicolo e cambia titolario",
        }
        return TemplateResponse(request, "admin/modifica_titolario_fascicolo.html", context)


class ModificaTitolarioFascicoloForm(forms.Form):
    titolario_voce = forms.ModelChoiceField(
        queryset=TitolarioVoce.objects.all(),
        label="Nuovo titolario",
        required=True,
    )
