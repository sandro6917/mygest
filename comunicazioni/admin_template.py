from django.contrib import admin

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

@admin.register(TemplateComunicazione)
class TemplateComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    search_fields = ("nome", "oggetto")
    list_filter = ("attivo",)
    ordering = ("-data_modifica",)
    inlines = [TemplateContextFieldInline]


@admin.register(FirmaComunicazione)
class FirmaComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    search_fields = ("nome",)
    list_filter = ("attivo",)
    ordering = ("nome",)
