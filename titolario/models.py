from __future__ import annotations
from typing import List, Optional
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class TitolarioVoce(models.Model):
    codice = models.CharField(max_length=30)
    titolo = models.CharField(max_length=200)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="figli")
    pattern_codice = models.CharField(
        max_length=120,
        default="{CLI}-{TIT}-{ANNO}-{SEQ:03d}",
        help_text=_("Pattern codice fascicolo: usa {CLI}, {TIT}, {ANNO}, {SEQ:03d}, {ANA}"),
    )
    
    # NUOVI CAMPI: Intestazione ad Anagrafica
    consente_intestazione = models.BooleanField(
        default=False,
        verbose_name=_("Consente intestazione"),
        help_text=_("Se True, consente di creare sotto-voci intestate ad anagrafiche")
    )
    anagrafica = models.ForeignKey(
        'anagrafiche.Anagrafica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='voci_titolario',
        verbose_name=_("Anagrafica intestataria"),
        help_text=_("Anagrafica a cui è intestata questa voce (opzionale)")
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
        if self.anagrafica:
            return f"{self.codice} - {self.titolo} ({self.anagrafica.nome})"
        return f"{self.codice} - {self.titolo}"
    
    def clean(self):
        """Validazione business rules per voci intestate ad anagrafiche"""
        errors = {}
        
        # REGOLA 1: Se ha anagrafica, deve avere un parent che consente intestazione
        if self.anagrafica:
            if not self.parent:
                errors['anagrafica'] = _(
                    "Una voce intestata ad anagrafica deve avere un parent."
                )
            elif not self.parent.consente_intestazione:
                errors['anagrafica'] = _(
                    "Il parent selezionato non consente voci intestate ad anagrafiche. "
                    "Seleziona una voce con 'Consente intestazione' attivo."
                )
        
        # REGOLA 2: Se consente_intestazione=True, NON può avere anagrafica
        if self.consente_intestazione and self.anagrafica:
            errors['consente_intestazione'] = _(
                "Una voce non può contemporaneamente consentire intestazione "
                "ed essere essa stessa intestata ad un'anagrafica."
            )
        
        # REGOLA 3: Evita loop circolari nella gerarchia
        if self.parent and self.pk:
            node = self.parent
            while node:
                if node.pk == self.pk:
                    errors['parent'] = _("Riferimento circolare nella gerarchia del titolario.")
                    break
                node = node.parent
        
        # REGOLA 4: Limita profondità massima (opzionale, per performance)
        if self.parent:
            depth = 0
            node = self.parent
            while node:
                depth += 1
                if depth > 6:  # Max 6 livelli
                    errors['parent'] = _("Profondità massima del titolario superata (max 6 livelli).")
                    break
                node = node.parent
        
        # REGOLA 5: Unicità anagrafica per parent (stesso parent + stessa anagrafica)
        if self.anagrafica and self.parent:
            existing = TitolarioVoce.objects.filter(
                parent=self.parent,
                anagrafica=self.anagrafica
            ).exclude(pk=self.pk if self.pk else None)
            
            if existing.exists():
                errors['anagrafica'] = _(
                    f"Esiste già una voce intestata a '{self.anagrafica.nome}' "
                    f"sotto il parent '{self.parent}'."
                )
        
        if errors:
            raise ValidationError(errors)


    def codice_gerarchico(self) -> str:
        """
        Genera codice gerarchico completo (es. 'HR/HR-PERS/ROSMAR01')
        """
        return f"{self.parent.codice_gerarchico()}/{self.codice}" if self.parent else self.codice
    
    def is_voce_intestata(self) -> bool:
        """Verifica se questa voce è intestata ad un'anagrafica"""
        return self.anagrafica is not None
    
    def get_anagrafiche_disponibili(self):
        """
        Ritorna QuerySet di anagrafiche che NON hanno già una voce
        intestata sotto questo parent (se consente_intestazione=True)
        """
        if not self.consente_intestazione:
            return None
        
        from anagrafiche.models import Anagrafica
        
        # Escludi anagrafiche che hanno già una voce sotto questo parent
        anagrafiche_gia_usate = TitolarioVoce.objects.filter(
            parent=self,
            anagrafica__isnull=False
        ).values_list('anagrafica_id', flat=True)
        
        return Anagrafica.objects.exclude(id__in=anagrafiche_gia_usate)


    def titolario_parts_for_fs(self) -> List[str]:
        parts: List[str] = []
        node: Optional["TitolarioVoce"] = self
        while node:
            parts.append(f"{node.codice}_{node.titolo}".replace(" ", "_"))
            node = node.parent
        return list(reversed(parts))
