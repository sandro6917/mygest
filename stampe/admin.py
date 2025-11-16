from __future__ import annotations
from django.contrib import admin
from .models import StampaFormato, StampaModulo, StampaCampo, StampaLista, StampaColonna

@admin.register(StampaFormato)
class StampaFormatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "larghezza_mm", "altezza_mm", "orientamento", "attivo")
    list_filter = ("orientamento", "attivo")
    search_fields = ("nome", "slug")
    fieldsets = (
        (None, {"fields": ("nome", "slug", "attivo")}),
        ("Dimensioni", {"fields": ("larghezza_mm", "altezza_mm", "orientamento")}),
        ("Margini (mm)", {"fields": ("margine_top_mm", "margine_right_mm", "margine_bottom_mm", "margine_left_mm")}),
        ("Font di default", {"fields": ("font_nome_default", "font_size_default")}),
    )

class StampaCampoInline(admin.TabularInline):
    model = StampaCampo
    extra = 1
    fields = (
        "ordine", "visibile", "tipo",
        "label", "attr_path", "static_value", "template",
        "x_mm", "y_mm", "larghezza_mm",
        "font_nome", "font_size", "bold", "italic", "align", "max_lines",
        # elementi grafici
        "shape_kind", "shape_width_mm", "shape_height_mm", "corner_radius_mm",
        "border_width_pt", "border_color", "fill_color",
        # barcode
        "barcode_standard", "barcode_bar_width_mm", "barcode_height_mm",
        # qrcode
        "qr_size_mm", "qr_error",
    )
    ordering = ("ordine",)

class StampaColonnaInline(admin.TabularInline):
    model = StampaColonna
    extra = 1
    fields = (
        "ordine", "visibile", "tipo", "label", "attr_path", "template",
        "larghezza_mm", "align", "indent_tree",
        "font_nome", "font_size", "max_lines",
        "barcode_standard", "barcode_bar_width_mm", "barcode_height_mm",
        "qr_size_mm", "qr_error",
    )
    ordering = ("ordine",)

@admin.register(StampaModulo)
class StampaModuloAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model_name", "nome", "slug", "formato", "documento_tipo", "is_default", "attivo")
    list_filter = ("app_label", "model_name", "formato", "documento_tipo", "attivo", "is_default")
    search_fields = ("nome", "slug", "app_label", "model_name")
    inlines = [StampaCampoInline]
    fieldsets = (
        (None, {"fields": ("app_label", "model_name", "nome", "slug", "attivo", "is_default", "note")}),
        ("Formato e font", {"fields": ("formato", "font_nome", "font_size")}),
        ("Ambito (solo Documenti)", {"fields": ("documento_tipo",)}),
    )

@admin.register(StampaLista)
class StampaListaAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model_name", "nome", "slug", "formato", "is_default", "attivo")
    list_filter = ("app_label", "model_name", "formato", "attivo", "is_default")
    search_fields = ("nome", "slug", "app_label", "model_name")
    inlines = [StampaColonnaInline]
    fieldsets = (
        (None, {"fields": ("app_label", "model_name", "nome", "slug", "attivo", "is_default", "note")}),
        ("Titolo", {
            "fields": (
                "titolo", "titolo_template",
                ("titolo_x_mm", "titolo_y_mm", "titolo_larghezza_mm"),
                ("titolo_bold", "titolo_italic", "titolo_font_size"),
            )
        }),
        ("Testata e piè di pagina", {
            "fields": (
                "intestazione",
                ("intestazione_x_mm", "intestazione_y_mm", "intestazione_font_size"),
                "piedipagina",
                ("piedipagina_x_mm", "piedipagina_y_mm", "piedipagina_font_size"),
            )
        }),
        ("Formato", {"fields": ("formato",)}),
        ("Filtri e ordinamento", {"fields": ("filter_def", "order_by")}),
        ("Stile tabella", {"fields": ("header_font_name", "header_font_size", "row_font_name", "row_font_size", "row_max_lines", "row_spacing", "row_height_mm")}),
        ("Layout", {
            "fields": (
                "layout",
                ("tree_parent_field", "tree_children_attr"),
                "tree_root_filter", "tree_roots", "tree_order_by",
                "tree_max_depth", "tree_indent_mm",
            )
        }),
    )
