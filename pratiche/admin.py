from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages
from django.shortcuts import redirect
from django import forms

from .models import Pratica, PraticheTipo, PraticaRelazione
from fascicoli.models import TitolarioVoce, Fascicolo
from scadenze.models import Scadenza as AppScadenza


@admin.register(PraticheTipo)
class PraticheTipoAdmin(admin.ModelAdmin):
    list_display = ("codice", "nome", "prefisso_codice", "pattern_codice")
    search_fields = ("codice", "nome")


class FigliInline(admin.TabularInline):
    model = PraticaRelazione
    fk_name = "parent"
    extra = 0
    autocomplete_fields = ("child",)
    fields = ("child", "tipo", "note")
    verbose_name = "Collegamento a figlio"
    verbose_name_plural = "Collegamenti a figli"
    show_change_link = True


class GenitoriInline(admin.TabularInline):
    model = PraticaRelazione
    fk_name = "child"
    extra = 0
    autocomplete_fields = ("parent",)
    fields = ("parent", "tipo", "note")
    verbose_name = "Collegamento a padre"
    verbose_name_plural = "Collegamenti a padri"
    show_change_link = True


class ModificaTitolarioForm(forms.Form):
    titolario_voce = forms.ModelChoiceField(
        queryset=TitolarioVoce.objects.all(),
        label="Nuovo titolario",
        required=True,
    )


def modifica_titolario_pratica(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = ModificaTitolarioForm(request.POST)
        if form.is_valid():
            titolario_voce = form.cleaned_data["titolario_voce"]
            count = 0
            for pratica in queryset:
                old_pk = pratica.pk
                # Duplica la pratica
                pratica.pk = None
                pratica.codice = ""
                pratica.progressivo = 0
                pratica.save()
                nuova_pratica = pratica

                # Duplica fascicoli (solo cambia titolario)
                for fascicolo in Fascicolo.objects.filter(pratiche=old_pk):
                    old_fascicolo_pk = fascicolo.pk
                    fascicolo.pk = None
                    fascicolo.titolario_voce = titolario_voce
                    fascicolo.save()
                    fascicolo.pratiche.set([nuova_pratica])

                # Duplica note
                for nota in nuova_pratica.note_collegate.model.objects.filter(pratica=old_pk):
                    nota.pk = None
                    nota.pratica = nuova_pratica
                    nota.save()

                scadenze_originali = list(AppScadenza.objects.filter(pratiche=old_pk))

                # Duplica relazioni in uscita (parent → child)
                for rel in PraticaRelazione.objects.filter(parent=old_pk):
                    PraticaRelazione.objects.create(
                        parent=nuova_pratica,
                        child=rel.child,
                        tipo=rel.tipo,
                        note=rel.note,
                    )
                # Duplica relazioni in entrata (parent ← child)
                for rel in PraticaRelazione.objects.filter(child=old_pk):
                    PraticaRelazione.objects.create(
                        parent=rel.parent,
                        child=nuova_pratica,
                        tipo=rel.tipo,
                        note=rel.note,
                    )

                for scad in scadenze_originali:
                    scad.pratiche.add(nuova_pratica)
                    scad.pratiche.remove(old_pk)

                # Cancella la pratica di partenza
                Pratica.objects.filter(pk=old_pk).delete()
                count += 1

            messages.success(
                request,
                f"{count} pratica/e duplicate con nuovo titolario e collegamenti copiati. Pratiche originali eliminate."
            )
            return redirect(request.get_full_path())
    else:
        form = ModificaTitolarioForm()

    return admin.helpers.render_to_response(
        request,
        "admin/modifica_titolario_pratica.html",
        {"form": form, "pratiche": queryset},
    )


modifica_titolario_pratica.short_description = "Duplica e cambia titolario (con copia collegamenti ed elimina originale)"


@admin.register(Pratica)
class PraticaAdmin(admin.ModelAdmin):
    inlines = [GenitoriInline, FigliInline]
    list_display = (
        "codice",
        "cliente",
        "tipo",
        "oggetto",
        "stato",
        "periodo_key",
        "progressivo",
        "data_apertura",
        "link_fascicolo",
    )
    list_filter = ("stato", "tipo", "periodo_riferimento", "data_apertura")
    search_fields = (
        "codice",
        "oggetto",
        "cliente__anagrafica__ragione_sociale",
        "cliente__anagrafica__nome",
        "cliente__anagrafica__cognome",
        "tag",
    )
    autocomplete_fields = ("cliente", "responsabile", "tipo")
    readonly_fields = ("periodo_key", "progressivo", "data_apertura")
    list_select_related = ("cliente__anagrafica", "tipo", "responsabile")
    ordering = ("-data_apertura", "codice")
    date_hierarchy = "data_apertura"
    search_help_text = "Cerca per codice, oggetto, cliente o tag."

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "codice",
                    "cliente",
                    "tipo",
                    "oggetto",
                    "stato",
                    "responsabile",
                    "note",
                    "tag",
                )
            },
        ),
        (
            "Periodo",
            {
                "fields": (
                    "periodo_riferimento",
                    "data_riferimento",
                    "periodo_key",
                    "progressivo",
                )
            },
        ),
        ("Date", {"fields": ("data_apertura", "data_chiusura")}),
    )

    @admin.display(description="Fascicolo", ordering="fascicolo__codice")
    def link_fascicolo(self, obj: Pratica):
        """
        Mostra:
        - link al fascicolo se già presente;
        - altrimenti, link "Crea fascicolo" con ?pratica=<id> preimpostato.
        """
        if not obj.pk:
            return "—"
        # se esiste fascicolo collegato
        if hasattr(obj, "fascicolo") and obj.fascicolo_id:
            url = reverse("admin:fascicoli_fascicolo_change", args=[obj.fascicolo_id])
            return format_html('<a href="{}">{}</a>', url, obj.fascicolo.codice)

        # link per creare un nuovo fascicolo con pratica precompilata
        add_url = reverse("admin:fascicoli_fascicolo_add")
        qs = urlencode({"pratica": obj.pk})
        return format_html('<a href="{}?{}">➕ Crea fascicolo</a>', add_url, qs)

    link_fascicolo.short_description = "Fascicolo"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "cliente__anagrafica",
            "tipo",
            "responsabile",
        ).prefetch_related("fascicoli")

    actions = [modifica_titolario_pratica]

