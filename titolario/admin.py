from __future__ import annotations
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import TitolarioVoce


@admin.register(TitolarioVoce)
class TitolarioVoceAdmin(admin.ModelAdmin):
    list_display = ("id", "codice", "titolo")
    search_fields = ("codice", "titolo")
