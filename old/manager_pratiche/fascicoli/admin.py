from django.contrib import admin
from django.db import connection

from .models import Fascicolo


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
    # Campo sicuro sempre presente: permette l’autocomplete per ID esatto
    search_fields = ("id__exact",)
    list_display = ("id",)
