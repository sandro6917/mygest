from __future__ import annotations

import logging
from typing import Optional

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)


class ClassificationJob(models.Model):
    """
    Job di scansione e classificazione di una directory.
    Ogni job traccia lo stato di elaborazione e i risultati.
    """
    STATUS_CHOICES = [
        ('pending', _('In attesa')),
        ('running', _('In esecuzione')),
        ('completed', _('Completato')),
        ('failed', _('Fallito')),
    ]
    
    id = models.AutoField(primary_key=True)
    directory_path = models.CharField(
        max_length=500,
        verbose_name=_("Percorso directory"),
        help_text=_("Path assoluto o UNC della directory da scansionare")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Stato")
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Creato il"))
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Avviato il"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completato il"))
    
    # Statistiche
    total_files = models.IntegerField(default=0, verbose_name=_("Totale file"))
    processed_files = models.IntegerField(default=0, verbose_name=_("File processati"))
    successful_files = models.IntegerField(default=0, verbose_name=_("File classificati con successo"))
    failed_files = models.IntegerField(default=0, verbose_name=_("File falliti"))
    
    # Errori (JSON array)
    errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Errori"),
        help_text=_("Lista di errori occorsi durante l'elaborazione")
    )
    
    # Opzioni di classificazione
    use_llm = models.BooleanField(
        default=True,
        verbose_name=_("Usa LLM"),
        help_text=_("Se attivo, usa LLM per classificare file ambigui")
    )
    llm_provider = models.CharField(
        max_length=50,
        default='openai',
        verbose_name=_("Provider LLM"),
        help_text=_("Provider LLM da utilizzare (openai, anthropic, local)")
    )
    
    # Utente che ha creato il job
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Creato da")
    )
    
    class Meta:
        verbose_name = _("Job Classificazione")
        verbose_name_plural = _("Jobs Classificazione")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"Job #{self.id} - {self.directory_path} ({self.get_status_display()})"
    
    def clean(self):
        """Validazione modello"""
        if not self.directory_path:
            raise ValidationError({'directory_path': _("Il percorso directory è obbligatorio")})
    
    def start(self):
        """Avvia il job"""
        if self.status != 'pending':
            raise ValidationError(_("Il job può essere avviato solo se in stato 'pending'"))
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete(self):
        """Completa il job con successo"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def fail(self, error_message: str):
        """Segna il job come fallito"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.errors.append({
                'timestamp': timezone.now().isoformat(),
                'message': error_message
            })
        self.save(update_fields=['status', 'completed_at', 'errors'])
    
    @property
    def progress_percentage(self) -> float:
        """Calcola la percentuale di completamento"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100


class ClassificationResult(models.Model):
    """
    Risultato della classificazione di un singolo file.
    Contiene il tipo predetto, metadata estratti e suggerimenti per importazione.
    """
    # Tipologie documenti MyGest
    TYPE_CHOICES = [
        ('CED', _('Cedolino')),
        ('UNI', _('Unilav')),
        ('DIC', _('Dichiarazione Fiscale')),
        ('BIL', _('Bilancio')),
        ('F24', _('F24')),
        ('EST', _('Estratto Conto')),
        ('FAT', _('Fattura')),
        ('CON', _('Contratto')),
        ('COR', _('Corrispondenza')),
        ('PRO', _('Protocollo')),
        ('ALT', _('Altro')),
    ]
    
    CONFIDENCE_CHOICES = [
        ('high', _('Alta (>80%)')),
        ('medium', _('Media (50-80%)')),
        ('low', _('Bassa (<50%)')),
    ]
    
    job = models.ForeignKey(
        ClassificationJob,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_("Job")
    )
    
    # Informazioni file
    file_path = models.CharField(
        max_length=500,
        verbose_name=_("Percorso file"),
        help_text=_("Path assoluto o relativo del file originale")
    )
    file_name = models.CharField(max_length=255, verbose_name=_("Nome file"))
    file_size = models.BigIntegerField(verbose_name=_("Dimensione (bytes)"))
    mime_type = models.CharField(max_length=100, verbose_name=_("MIME type"))
    
    # Classificazione
    predicted_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name=_("Tipo predetto")
    )
    confidence_level = models.CharField(
        max_length=20,
        choices=CONFIDENCE_CHOICES,
        verbose_name=_("Livello confidenza")
    )
    confidence_score = models.FloatField(
        verbose_name=_("Score confidenza"),
        help_text=_("Valore da 0.0 a 1.0")
    )
    
    # Metodo classificazione
    classification_method = models.CharField(
        max_length=50,
        default='rule',
        verbose_name=_("Metodo"),
        help_text=_("Metodo usato: rule (pattern), llm, manual")
    )
    
    # Testo estratto (per PDF)
    extracted_text = models.TextField(
        blank=True,
        verbose_name=_("Testo estratto"),
        help_text=_("Testo estratto da PDF o OCR")
    )
    
    # Metadata estratti (JSON)
    extracted_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata estratti"),
        help_text=_("Metadata come data, importo, CF, PIVA, etc.")
    )
    
    # Suggerimenti per importazione in app documenti
    suggested_cliente = models.ForeignKey(
        'anagrafiche.Cliente',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Cliente suggerito")
    )
    suggested_fascicolo = models.ForeignKey(
        'fascicoli.Fascicolo',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Fascicolo suggerito")
    )
    suggested_titolario = models.ForeignKey(
        'titolario.TitolarioVoce',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Titolario suggerito")
    )
    
    # Stato importazione
    imported = models.BooleanField(
        default=False,
        verbose_name=_("Importato"),
        help_text=_("Se True, il file è stato importato in app documenti")
    )
    documento = models.ForeignKey(
        'documenti.Documento',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Documento creato")
    )
    imported_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Importato il")
    )
    
    # Note manuali
    notes = models.TextField(
        blank=True,
        verbose_name=_("Note"),
        help_text=_("Note aggiuntive o correzioni manuali")
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Creato il"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aggiornato il"))
    
    class Meta:
        verbose_name = _("Risultato Classificazione")
        verbose_name_plural = _("Risultati Classificazione")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', 'imported']),
            models.Index(fields=['predicted_type', 'confidence_level']),
            models.Index(fields=['suggested_cliente']),
        ]
    
    def __str__(self) -> str:
        return f"{self.file_name} → {self.get_predicted_type_display()} ({self.confidence_score:.2%})"
    
    def mark_as_imported(self, documento):
        """Segna il risultato come importato"""
        self.imported = True
        self.documento = documento
        self.imported_at = timezone.now()
        self.save(update_fields=['imported', 'documento', 'imported_at'])


class ClassifierConfig(models.Model):
    """
    Configurazione globale del classificatore.
    Singleton pattern - esiste una sola istanza.
    """
    
    # API Keys (NOTE: In produzione, salvare criptate o in variabili ambiente)
    openai_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("OpenAI API Key"),
        help_text=_("Chiave API OpenAI (lasciare vuoto per usare env var)")
    )
    
    # LLM Settings
    default_llm_provider = models.CharField(
        max_length=50,
        default='openai',
        verbose_name=_("Provider LLM di default")
    )
    llm_model = models.CharField(
        max_length=100,
        default='gpt-4o-mini',
        verbose_name=_("Modello LLM"),
        help_text=_("Modello OpenAI da usare (es: gpt-4o-mini, gpt-4)")
    )
    llm_temperature = models.FloatField(
        default=0.1,
        verbose_name=_("Temperature LLM"),
        help_text=_("Temperatura per LLM (0.0 = deterministico, 1.0 = creativo)")
    )
    llm_max_tokens = models.IntegerField(
        default=500,
        verbose_name=_("Max tokens LLM"),
        help_text=_("Massimo numero di token per risposta LLM")
    )
    
    # Classificazione
    confidence_threshold = models.FloatField(
        default=0.7,
        verbose_name=_("Soglia confidenza"),
        help_text=_("Soglia minima di confidenza per classificazione automatica")
    )
    
    # Pattern matching rules per classificazione rule-based (JSON)
    filename_patterns = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Pattern filename"),
        help_text=_(
            "Dizionario {tipo: [pattern1, pattern2]} per matching filename. "
            "Es: {'CED': ['cedolino', 'payslip'], 'UNI': ['unilav', 'comunicazione']}"
        )
    )
    
    content_patterns = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Pattern contenuto"),
        help_text=_(
            "Dizionario {tipo: [keyword1, keyword2]} per matching testo estratto. "
            "Es: {'F24': ['modello f24', 'codice tributo'], 'BIL': ['bilancio', 'stato patrimoniale']}"
        )
    )
    
    # File settings
    max_file_size_mb = models.IntegerField(
        default=50,
        verbose_name=_("Dimensione max file (MB)"),
        help_text=_("Dimensione massima file processabili in MB")
    )
    allowed_extensions = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Estensioni permesse"),
        help_text=_("Lista estensioni file permesse (es: ['.pdf', '.jpg', '.png'])")
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aggiornato il"))
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Aggiornato da")
    )
    
    class Meta:
        verbose_name = _("Configurazione Classificatore")
        verbose_name_plural = _("Configurazione Classificatore")
    
    def __str__(self) -> str:
        return f"Configurazione Classificatore (LLM: {self.llm_model})"
    
    def save(self, *args, **kwargs):
        """Singleton pattern: permette una sola istanza"""
        if not self.pk and ClassifierConfig.objects.exists():
            # Se già esiste una configurazione, aggiorna quella
            existing = ClassifierConfig.objects.first()
            self.pk = existing.pk
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls) -> ClassifierConfig:
        """Ottiene l'istanza di configurazione (crea se non esiste)"""
        config, created = cls.objects.get_or_create(pk=1)
        if created:
            # Imposta valori di default iniziali
            config.filename_patterns = {
                'CED': ['cedolino', 'payslip', 'busta paga'],
                'UNI': ['unilav', 'comunicazione obbligatoria', 'co_'],
                'DIC': ['dichiarazione', 'modello 730', 'modello redditi', 'unico'],
                'BIL': ['bilancio', 'stato patrimoniale', 'conto economico'],
                'F24': ['f24', 'modello f24', 'delega'],
                'EST': ['estratto conto', 'movimenti', 'saldo'],
            }
            config.content_patterns = {
                'CED': ['cedolino paga', 'retribuzione', 'periodo di paga'],
                'UNI': ['unificata lav', 'comunicazione obbligatoria'],
                'DIC': ['agenzia delle entrate', 'dichiarazione dei redditi'],
                'BIL': ['bilancio di esercizio', 'attivo', 'passivo'],
                'F24': ['codice tributo', 'anno di riferimento', 'importi a debito'],
                'EST': ['data operazione', 'dare', 'avere', 'saldo contabile'],
            }
            config.allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.docx']
            config.save()
        return config


class TrainingExample(models.Model):
    """
    Esempio di training per Few-Shot Learning.
    Documenti di esempio usati per istruire l'AI sulla classificazione.
    """
    id = models.AutoField(primary_key=True)
    
    # File di esempio
    file_name = models.CharField(
        max_length=255,
        verbose_name=_("Nome file"),
        help_text=_("Nome del file di esempio")
    )
    file_path = models.CharField(
        max_length=500,
        verbose_name=_("Percorso file"),
        help_text=_("Path assoluto del file di esempio"),
        blank=True,
        null=True
    )
    
    # Classificazione corretta
    document_type = models.CharField(
        max_length=10,
        verbose_name=_("Tipo documento"),
        help_text=_("Codice tipo documento (es. CED, UNI, DIC)")
    )
    
    # Testo estratto (cached per performance)
    extracted_text = models.TextField(
        verbose_name=_("Testo estratto"),
        help_text=_("Testo estratto dal documento"),
        blank=True
    )
    
    # Metadata estratti
    extracted_metadata = models.JSONField(
        default=dict,
        verbose_name=_("Metadata estratti"),
        blank=True
    )
    
    # Note descrittive
    description = models.TextField(
        verbose_name=_("Descrizione"),
        help_text=_("Descrizione delle caratteristiche distintive del documento"),
        blank=True
    )
    
    # Attivo/disattivo
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Attivo"),
        help_text=_("Se disattivato, l'esempio non viene usato nel training")
    )
    
    # Priorità (esempi con priorità alta vengono mostrati per primi)
    priority = models.IntegerField(
        default=0,
        verbose_name=_("Priorità"),
        help_text=_("Priorità dell'esempio (più alto = più importante)")
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Creato il"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aggiornato il"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_examples',
        verbose_name=_("Creato da")
    )
    
    class Meta:
        verbose_name = _("Esempio di Training")
        verbose_name_plural = _("Esempi di Training")
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['document_type', 'is_active']),
            models.Index(fields=['-priority']),
        ]
    
    def __str__(self):
        return f"{self.file_name} → {self.document_type}"
    
    @classmethod
    def get_examples_for_type(cls, document_type: str, limit: int = 3) -> list:
        """
        Ottiene esempi di training per un tipo specifico.
        
        Args:
            document_type: Codice tipo documento
            limit: Numero massimo di esempi da ritornare
            
        Returns:
            Lista di dizionari con file_name, text, metadata
        """
        examples = cls.objects.filter(
            document_type=document_type,
            is_active=True
        ).order_by('-priority', '-created_at')[:limit]
        
        return [
            {
                'file_name': ex.file_name,
                'text': ex.extracted_text[:500] if ex.extracted_text else '',  # Prime 500 chars
                'type': ex.document_type,
                'description': ex.description
            }
            for ex in examples
        ]
    
    @classmethod
    def get_all_active_examples(cls, max_per_type: int = 2) -> dict:
        """
        Ottiene esempi attivi per tutti i tipi.
        
        Args:
            max_per_type: Numero massimo di esempi per tipo
            
        Returns:
            Dict {tipo: [esempi]}
        """
        examples_by_type = {}
        
        # Raggruppa per tipo
        all_examples = cls.objects.filter(is_active=True).order_by(
            'document_type', '-priority', '-created_at'
        )
        
        for example in all_examples:
            doc_type = example.document_type
            if doc_type not in examples_by_type:
                examples_by_type[doc_type] = []
            
            if len(examples_by_type[doc_type]) < max_per_type:
                examples_by_type[doc_type].append({
                    'file_name': example.file_name,
                    'text': example.extracted_text[:500] if example.extracted_text else '',
                    'description': example.description
                })
        
        return examples_by_type
