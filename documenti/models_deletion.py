"""
API per la gestione delle richieste di eliminazione file da parte dell'agent desktop.

Endpoints:
- POST /api/v1/agent/request-deletion/ - Crea richiesta eliminazione
- GET /api/v1/agent/pending-deletions/ - Lista richieste pendenti
- POST /api/v1/agent/confirm-deletion/ - Conferma eliminazione
- GET /api/v1/agent/ping/ - Verifica connessione
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class FileDeletionRequest(models.Model):
    """
    Richiesta di eliminazione di un file dal filesystem locale.
    
    Workflow:
    1. L'utente carica un documento e spunta "Elimina file originale"
    2. Viene creato un FileDeletionRequest con status=PENDING
    3. L'agent desktop controlla periodicamente le richieste PENDING
    4. L'agent elimina il file e aggiorna status=COMPLETED o FAILED
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'In attesa'
        COMPLETED = 'completed', 'Completato'
        FAILED = 'failed', 'Fallito'
        CANCELLED = 'cancelled', 'Annullato'
    
    # Documento associato
    documento = models.ForeignKey(
        'documenti.Documento',
        on_delete=models.CASCADE,
        related_name='deletion_requests'
    )
    
    # Percorso del file originale da eliminare
    source_path = models.CharField(
        max_length=1000,
        help_text="Percorso completo del file sul filesystem locale"
    )
    
    # Utente che ha richiesto l'eliminazione
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='file_deletion_requests'
    )
    
    # Stato della richiesta
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Dettagli errore (se fallita)
    error_message = models.TextField(blank=True)
    
    # Metadati aggiuntivi
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Dimensione del file in bytes"
    )
    
    class Meta:
        verbose_name = "Richiesta eliminazione file"
        verbose_name_plural = "Richieste eliminazione file"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['documento', 'status']),
        ]
    
    def __str__(self):
        return f"Deletion #{self.id} - {self.documento.codice} - {self.status}"
    
    def mark_completed(self):
        """Marca la richiesta come completata."""
        self.status = self.Status.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_failed(self, error_message: str):
        """Marca la richiesta come fallita."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])
    
    def cancel(self):
        """Annulla la richiesta."""
        self.status = self.Status.CANCELLED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
