from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from .models import UnitaFisica, CollocazioneFisica
from .pdf import render_etichette_unita  # generator PDF

@admin.register(UnitaFisica)
class UnitaFisicaAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "codice", "nome", "parent", "ordine", "attivo", "etichetta_pdf_btn")
    list_filter = ("tipo", "attivo")
    search_fields = ("codice", "nome", "full_path")
    autocomplete_fields = ("parent",)
    ordering = ("parent__id", "ordine", "nome")

    def etichetta_pdf_btn(self, obj: UnitaFisica):
        url = reverse("stampe:etichetta", args=("archivio_fisico", "unitafisica", obj.pk))
        url += "?action=preview&size=dymo_99012"
        return format_html('<a class="button" target="_blank" href="{}">Etichetta PDF</a>', url)
    etichetta_pdf_btn.short_description = "Etichetta"

@admin.register(CollocazioneFisica)
class CollocazioneFisicaAdmin(admin.ModelAdmin):
    list_display = ("id", "content_type", "object_id", "unita", "attiva", "dal", "al", "etichetta_pdf_btn")
    list_filter = ("attiva", "unita__tipo")
    search_fields = ("note",)
    autocomplete_fields = ("unita",)

    def etichetta_pdf_btn(self, obj: CollocazioneFisica):
        if not obj.unita_id:
            return "—"
        url = reverse("stampe:etichetta", args=("archivio_fisico", "unitafisica", obj.unita_id))
        url += "?action=preview&size=dymo_99012"
        return format_html('<a class="button" target="_blank" href="{}">Etichetta PDF</a>', url)
    etichetta_pdf_btn.short_description = "Etichetta"
