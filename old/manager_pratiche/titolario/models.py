from __future__ import annotations
from typing import List, Optional
from django.db import models
from django.utils.translation import gettext_lazy as _

class TitolarioVoce(models.Model):
    codice = models.CharField(max_length=30)
    titolo = models.CharField(max_length=200)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="figli")
    pattern_codice = models.CharField(
        max_length=120,
        default="{CLI}-{TIT}-{ANNO}-{SEQ:03d}",
        help_text=_("Pattern codice fascicolo: usa {CLI}, {TIT}, {ANNO}, {SEQ:03d}"),
    )

    class Meta:
        verbose_name = _("Voce di titolario")
        verbose_name_plural = _("Voci di titolario")
        constraints = [
            models.UniqueConstraint(fields=["parent", "codice"], name="uniq_titolario_codice_per_parent")
        ]
        ordering = ["id"]
        db_table = "vocititolario"

    def __str__(self) -> str:
        return f"{self.codice} - {self.titolo}"

    def codice_gerarchico(self) -> str:
        return f"{self.parent.codice_gerarchico()}/{self.codice}" if self.parent else self.codice

    def titolario_parts_for_fs(self) -> List[str]:
        parts: List[str] = []
        node: Optional["TitolarioVoce"] = self
        while node:
            parts.append(f"{node.codice}_{node.titolo}".replace(" ", "_"))
            node = node.parent
        return list(reversed(parts))
