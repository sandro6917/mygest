from __future__ import annotations
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from reportlab.lib.pagesizes import A4

from .models import DocumentiTipo, Documento, AttributoDefinizione, AttributoValore
from protocollo.models import ProtocolloCounter, MovimentoProtocollo
from fascicoli.models import Fascicolo
from archivio_fisico.models import UnitaFisica


# -----------------------------
#  Filtri custom
# -----------------------------
class InGiacenzaFilter(admin.SimpleListFilter):
    title = _("stato magazzino")
    parameter_name = "giacenza"

    def lookups(self, request, model_admin):
        return (
            ("in", _("In giacenza")),
            ("out", _("Uscito")),
            ("nt", _("Non tracciato")),
        )

    def queryset(self, request, qs):
        v = self.value()
        if v == "nt":
            return qs.filter(tracciabile=False)
        if v == "in":
            return qs.filter(tracciabile=True).exclude(
                movimenti__direzione="OUT", movimenti__chiuso=False
            )
        if v == "out":
            return qs.filter(
                tracciabile=True, movimenti__direzione="OUT", movimenti__chiuso=False
            )
        return qs


# -----------------------------
#  Form azioni con conferma
# -----------------------------
class UscitaForm(forms.Form):
    a_chi = forms.CharField(label=_("Destinatario"), required=False)
    data_rientro_prevista = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    causale = forms.CharField(required=False)
    note = forms.CharField(required=False, widget=forms.Textarea)
    ubicazione = forms.ModelChoiceField(
        queryset=UnitaFisica.objects.all().order_by("full_path", "nome"),
        required=False,
        label=_("Unità fisica"),
    )


class EntrataForm(forms.Form):
    da_chi = forms.CharField(label=_("Consegnato da"), required=False)
    ubicazione = forms.ModelChoiceField(
        queryset=UnitaFisica.objects.all().order_by("full_path", "nome"),
        required=False,
        label=_("Unità fisica"),
    )
    causale = forms.CharField(required=False)
    note = forms.CharField(required=False, widget=forms.Textarea)


# -----------------------------
#  Admin registro tipi
# -----------------------------
class AttributoDefinizioneInlineForm(forms.ModelForm):
    # Limito il widget a scelte note
    WIDGET_CHOICES = [
        ("", "(default)"),
        ("anagrafica", "Anagrafica (select)"),
    ]
    widget = forms.ChoiceField(choices=WIDGET_CHOICES, required=False)

    class Meta:
        model = AttributoDefinizione
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        widget = (cleaned.get("widget") or "").lower()
        tipo = (cleaned.get("tipo_dato") or "").lower()
        if widget in ("anagrafica", "fk_anagrafica", "anag") and tipo not in ("int", "integer"):
            self.add_error("widget", 'Il widget "anagrafica" è consentito solo per tipo_dato intero.')
        return cleaned

@admin.register(AttributoDefinizione)
class AttributoDefinizioneAdmin(admin.ModelAdmin):
    list_display = ("tipo_documento", "ordine", "codice", "nome", "tipo_dato", "widget", "required")
    list_filter = ("tipo_documento", "tipo_dato", "widget", "required")
    search_fields = ("codice", "nome", "help_text")
    ordering = ("tipo_documento", "ordine", "codice")
    form = AttributoDefinizioneInlineForm

class AttributoDefinizioneInline(admin.TabularInline):
    model = AttributoDefinizione
    form = AttributoDefinizioneInlineForm
    extra = 0
    ordering = ("ordine", "codice")
    fields = ("ordine", "codice", "nome", "tipo_dato", "widget", "required", "help_text")
    show_change_link = True

@admin.register(AttributoValore)
class AttributoValoreAdmin(admin.ModelAdmin):
    list_display = ("documento", "definizione", "valore")
    search_fields = ("documento__codice", "definizione__codice")

@admin.register(DocumentiTipo)
class DocumentiTipoAdmin(admin.ModelAdmin):
    list_display = ("codice", "nome", "attivo")
    list_filter = ("attivo",)
    search_fields = ("codice", "nome")
    inlines = [AttributoDefinizioneInline]

# -----------------------------
#  Admin documenti
# -----------------------------
@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "codice",
        "descrizione",
        "cliente",
        "fascicolo",
        "titolario_voce",
        "stato",
        "stato_magazzino",
        "creato_il",
    )
    list_filter = (
        "stato",
        InGiacenzaFilter,
        "cliente",
        "titolario_voce",
        "fascicolo",
        "data_documento",
    )
    search_fields = (
        "codice",
        "descrizione",
        "cliente__anagrafica__ragione_sociale",
        "cliente__anagrafica__nome",
        "cliente__anagrafica__cognome",
        "fascicolo__codice",
        "fascicolo__titolo",
        "titolario_voce__titolo",
        "titolario_voce__codice",
        "tipo__codice",
        "tipo__nome",
    )
    autocomplete_fields = ("cliente", "fascicolo", "titolario_voce", "tipo")
    readonly_fields = ("codice", "percorso_archivio", "creato_il", "aggiornato_il")

    fieldsets = (
        (None, {"fields": ("codice", "descrizione", "tipo", "stato", "tracciabile")}),
        ("Classificazione", {"fields": ("cliente", "fascicolo", "titolario_voce", "data_documento")}),
        ("File", {"fields": ("file", "percorso_archivio")}),
        ("Altro", {"fields": ("tags", "note", "creato_il", "aggiornato_il")}),
    )

    actions = [
        "stampa_etichetta_dymo",
        "azione_entrata",
        "azione_uscita",
        "stampa_registro_protocollo",
        "esporta_csv_documenti",
    ]

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        fascicolo_param = request.POST.get("fascicolo") or request.GET.get("fascicolo")
        if (obj and obj.fascicolo_id) or fascicolo_param:
            if "cliente" not in ro:
                ro.append("cliente")
        return ro

    def get_changeform_initial_data(self, request):
        """
        Prefill dei campi quando si crea un documento da un fascicolo (via ?fascicolo=<id>).
        Usare questa API evita KeyError sui base_fields nel change view.
        """
        initial = super().get_changeform_initial_data(request)
        fascicolo_id = request.GET.get("fascicolo") or request.GET.get("fascicolo__id__exact")
        if fascicolo_id:
            try:
                from fascicoli.models import Fascicolo
                f = Fascicolo.objects.only("id", "cliente_id", "titolario_voce_id").get(pk=fascicolo_id)
                initial.setdefault("fascicolo", f.id)
                initial.setdefault("cliente", f.cliente_id)
                initial.setdefault("titolario_voce", f.titolario_voce_id)
            except Exception:
                pass
        return initial

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Inizializza i campi partendo da ?fascicolo=<id> in modo sicuro.
        Non accedere a base_fields senza verificarne la presenza.
        """
        form = super().get_form(request, obj, change=change, **kwargs)
        if obj is None:
            fascicolo_id = request.GET.get("fascicolo") or request.GET.get("fascicolo__id__exact")
            if fascicolo_id:
                try:
                    from fascicoli.models import Fascicolo
                    f = Fascicolo.objects.only("id", "cliente_id", "titolario_voce_id").get(pk=fascicolo_id)
                    if "fascicolo" in form.base_fields:
                        form.base_fields["fascicolo"].initial = f.id
                    if "cliente" in form.base_fields:
                        form.base_fields["cliente"].initial = f.cliente_id
                        form.base_fields["cliente"].disabled = True  # opzionale
                    if "titolario_voce" in form.base_fields:
                        form.base_fields["titolario_voce"].initial = f.titolario_voce_id
                except Exception:
                    pass
        else:
            if obj.fascicolo_id and "cliente" in form.base_fields:
                form.base_fields["cliente"].disabled = True
        return form

    # -------------------
    # Etichette Dymo (S0722400 89x36mm)
    # -------------------
    def stampa_etichetta_dymo(self, request, queryset):
        W, H = 89 * mm, 36 * mm
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="etichette_dymo.pdf"'
        p = canvas.Canvas(response, pagesize=(W, H))

        font = "Helvetica"
        left = 5 * mm
        top = 30 * mm
        line = 5 * mm

        for doc in queryset.select_related("cliente", "cliente__anagrafica"):
            cliente = getattr(doc.cliente, "denominazione", "") or getattr(doc.cliente, "ragione_sociale", "") or "—"
            titolo = (doc.descrizione or "")[:50]
            codice = doc.codice or f"DOC-{doc.pk}"

            p.setFont(font, 9)
            p.drawString(left, top, f"{cliente}")
            p.setFont(font, 8)
            p.drawString(left, top - line, f"{titolo}")
            p.setFont(font, 8)
            p.drawString(left, top - (2 * line), f"Codice: {codice}")
            p.showPage()

        p.save()
        return response

    stampa_etichetta_dymo.short_description = "🖨️ Stampa etichetta Dymo (S0722400)"

    # -------------------
    # ENTRATA (con conferma)
    # -------------------
    def azione_entrata(self, request, queryset):
        if "apply" in request.POST:
            form = EntrataForm(request.POST)
            if form.is_valid():
                ok, err = 0, 0
                for doc in queryset.select_related("cliente", "cliente__anagrafica"):
                    try:
                        MovimentoProtocollo.registra_entrata(
                            documento=doc,
                            quando=timezone.now(),
                            operatore=request.user,
                            da_chi=form.cleaned_data.get("da_chi") or "",
                            ubicazione=form.cleaned_data.get("ubicazione"),
                            causale=form.cleaned_data.get("causale") or "",
                            note=form.cleaned_data.get("note") or "",
                        )
                        ok += 1
                    except Exception:
                        err += 1
                messages.success(request, f"Registrate ENTRATE: {ok}. Errori: {err}.")
                return None
        else:
            form = EntrataForm()
        return TemplateResponse(
            request, "admin/movimenti/confirm_entrata.html", {"form": form, "queryset": queryset}
        )

    azione_entrata.short_description = "📥 Registra ENTRATA (rientro/archiviazione)"

    # -------------------
    # USCITA (con conferma)
    # -------------------
    def azione_uscita(self, request, queryset):
        if "apply" in request.POST:
            form = UscitaForm(request.POST)
            if form.is_valid():
                ok, err = 0, 0
                for doc in queryset.select_related("cliente", "cliente__anagrafica"):
                    try:
                        MovimentoProtocollo.registra_uscita(
                            documento=doc,
                            quando=timezone.now(),
                            operatore=request.user,
                            a_chi=form.cleaned_data.get("a_chi") or "",
                            data_rientro_prevista=form.cleaned_data.get("data_rientro_prevista"),
                            causale=form.cleaned_data.get("causale") or "",
                            note=form.cleaned_data.get("note") or "",
                            ubicazione=form.cleaned_data.get("ubicazione"),
                        )
                        ok += 1
                    except Exception:
                        err += 1
                messages.success(request, f"Registrate USCITE: {ok}. Errori: {err}.")
                return None
        else:
            form = UscitaForm()
        return TemplateResponse(
            request, "admin/movimenti/confirm_uscita.html", {"form": form, "queryset": queryset}
        )

    azione_uscita.short_description = "📤 Registra USCITA (consegna/prestito)"

    # -------------------
    # Registro protocollo (PDF per cliente)
    # -------------------
    def stampa_registro_protocollo(self, request, queryset):
        movs = (
            MovimentoProtocollo.objects.filter(documento__in=queryset)
            .select_related("documento", "cliente", "cliente__anagrafica")
            .order_by("cliente__id", "anno", "direzione", "numero")
        )
        if not movs.exists():
            return self._pdf_msg(_("Nessuna movimentazione per i documenti selezionati."))

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="registro_protocollo.pdf"'
        p = canvas.Canvas(response, pagesize=A4)

        margin_left = 18 * mm
        margin_top = 280 * mm
        line = 6 * mm

        def header(cliente_nome):
            p.setFont("Helvetica-Bold", 13)
            p.drawString(margin_left, margin_top + 10 * mm, f"Registro protocollo — {cliente_nome}")
            p.setFont("Helvetica", 10)
            p.drawString(margin_left, margin_top + 6 * mm, f"Generato il {timezone.now().strftime('%d/%m/%Y %H:%M')}")
            p.setFont("Helvetica-Bold", 9)
            y = margin_top
            p.drawString(margin_left, y, "Prot.")
            p.drawString(margin_left + 35 * mm, y, "Data")
            p.drawString(margin_left + 60 * mm, y, "Dir.")
            p.drawString(margin_left + 75 * mm, y, "Titolo documento")
            p.drawString(margin_left + 150 * mm, y, "Note")
            p.setFont("Helvetica", 9)
            return y - line

        current = None
        y = margin_top
        for m in movs:
            nome = getattr(m.cliente, "denominazione", "") or getattr(m.cliente, "ragione_sociale", "")
            if current != nome:
                if current is not None:
                    p.showPage()
                current = nome or "—"
                y = header(current)

            if y < 20 * mm:
                p.showPage()
                y = header(current)

            p.drawString(margin_left, y, m.protocollo_label)
            p.drawString(margin_left + 35 * mm, y, m.data.strftime("%d/%m/%Y %H:%M"))
            p.drawString(margin_left + 60 * mm, y, "IN" if m.direzione == "IN" else "OUT")
            p.drawString(margin_left + 75 * mm, y, (m.documento.descrizione or "")[:60])
            p.drawString(margin_left + 150 * mm, y, (m.causale or "")[:25])
            y -= line

        p.showPage()
        p.save()
        return response

    stampa_registro_protocollo.short_description = "📑 Stampa registro di protocollo (per cliente)"

    # -------------------
    # Esporta CSV
    # -------------------
    def esporta_csv_documenti(self, request, queryset):
        import csv
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="documenti.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Codice", "Descrizione", "Cliente", "Data", "Stato", "Stato magazzino"])
        for doc in queryset.select_related("cliente", "cliente__anagrafica"):
            cliente = getattr(doc.cliente, "denominazione", "") or getattr(doc.cliente, "ragione_sociale", "")
            writer.writerow([
                doc.pk, doc.codice, doc.descrizione, cliente,
                doc.data_documento.strftime("%Y-%m-%d") if doc.data_documento else "",
                doc.stato, doc.stato_magazzino
            ])
        return response

    esporta_csv_documenti.short_description = "⬇️ Esporta documenti in CSV"

    # -------------------
    # Utility PDF messaggio
    # -------------------
    def _pdf_msg(self, text: str):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="info.pdf"'
        p = canvas.Canvas(response, pagesize=A4)
        p.setFont("Helvetica", 12)
        p.drawString(50, 800, text)
        p.showPage()
        p.save()
        return response
