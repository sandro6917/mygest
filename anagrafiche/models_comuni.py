"""
Model per archivio comuni italiani basato su dati ISTAT/Belfiore.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ComuneItaliano(models.Model):
    """
    Archivio dei comuni italiani con dati ISTAT.
    Struttura basata sul file gi_comuni_cap.json.
    """
    # Codici identificativi
    codice_istat = models.CharField(
        "Codice ISTAT",
        max_length=6,
        unique=True,
        db_index=True,
        help_text="Codice ISTAT a 6 cifre del comune"
    )
    codice_belfiore = models.CharField(
        "Codice catastale (Belfiore)",
        max_length=4,
        db_index=True,
        help_text="Codice catastale del comune"
    )
    
    # Denominazione
    nome = models.CharField(
        "Nome comune",
        max_length=120,
        db_index=True,
        help_text="Denominazione ufficiale italiana"
    )
    nome_alternativo = models.CharField(
        "Nome alternativo",
        max_length=120,
        blank=True,
        help_text="Denominazione italiana alternativa"
    )
    
    # Ubicazione amministrativa
    provincia = models.CharField(
        "Provincia",
        max_length=2,
        db_index=True,
        help_text="Sigla provincia (es. MI, RM)"
    )
    nome_provincia = models.CharField(
        "Nome provincia",
        max_length=120,
        help_text="Denominazione completa provincia"
    )
    regione = models.CharField(
        "Regione",
        max_length=120,
        db_index=True
    )
    codice_regione = models.CharField(
        "Codice regione",
        max_length=2,
        help_text="Codice ISTAT regione"
    )
    
    # CAP
    cap = models.CharField(
        "CAP",
        max_length=5,
        db_index=True,
        help_text="Codice Avviamento Postale"
    )
    
    # Metadati
    flag_capoluogo = models.CharField(
        "Capoluogo",
        max_length=2,
        default="NO",
        choices=[("SI", "Sì"), ("NO", "No")],
        help_text="Indica se è capoluogo di provincia/città metropolitana"
    )
    
    # Coordinate geografiche
    latitudine = models.DecimalField(
        "Latitudine",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    longitudine = models.DecimalField(
        "Longitudine",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    
    # Campi opzionali per gestione soppressioni/fusioni
    attivo = models.BooleanField(
        "Attivo",
        default=True,
        db_index=True,
        help_text="False per comuni soppressi o fusi"
    )
    note = models.TextField(
        "Note",
        blank=True,
        help_text="Note su soppressioni, fusioni, variazioni"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Comune italiano")
        verbose_name_plural = _("Comuni italiani")
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome", "provincia"]),
            models.Index(fields=["provincia", "nome"]),
            models.Index(fields=["cap"]),
            models.Index(fields=["codice_belfiore"]),
            models.Index(fields=["attivo", "provincia"]),
        ]
        constraints = [
            # Nota: codice_istat è unique, ma alcuni comuni possono avere
            # più CAP diversi (stessa entry ripetuta nel JSON con CAP diversi)
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.provincia}) - {self.cap}"
    
    @property
    def denominazione_completa(self):
        """Nome comune con provincia per display."""
        return f"{self.nome} ({self.provincia})"
    
    @property
    def denominazione_estesa(self):
        """Nome comune, provincia e CAP."""
        return f"{self.nome} ({self.provincia}) - CAP {self.cap}"
