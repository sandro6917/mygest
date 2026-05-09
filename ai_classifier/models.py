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


# ============================================================================
# NUOVI MODELLI PER ML AUTO-APPRENDIMENTO
# ============================================================================

class MLModel(models.Model):
    """
    Versioning dei modelli ML addestrati.
    Tiene traccia di ogni versione del modello con relative metriche.
    """
    MODEL_TYPE_CHOICES = [
        ('random_forest', _('Random Forest')),
        ('logistic_regression', _('Logistic Regression')),
        ('svm', _('SVM')),
        ('naive_bayes', _('Naive Bayes')),
    ]
    
    version = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Versione"),
        help_text=_("Versione semantica (es. v1.0.0, v1.1.0)")
    )
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPE_CHOICES,
        default='random_forest',
        verbose_name=_("Tipo modello")
    )
    
    # Path file modello
    model_file_path = models.CharField(
        max_length=500,
        verbose_name=_("Path modello"),
        help_text=_("Path al file .pkl del modello su NAS")
    )
    vectorizer_file_path = models.CharField(
        max_length=500,
        verbose_name=_("Path vectorizer"),
        help_text=_("Path al file .pkl del TF-IDF vectorizer su NAS")
    )
    label_encoder_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Path label encoder"),
        help_text=_("Path ai file .pkl dei label encoders (tipo, cliente, titolario)")
    )
    
    # Metriche di training
    accuracy = models.FloatField(verbose_name=_("Accuracy"))
    precision = models.FloatField(verbose_name=_("Precision"))
    recall = models.FloatField(verbose_name=_("Recall"))
    f1_score = models.FloatField(verbose_name=_("F1 Score"))
    
    # Dati training
    training_samples = models.IntegerField(
        verbose_name=_("Campioni training"),
        help_text=_("Numero di documenti usati per il training")
    )
    training_stats = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Statistiche training"),
        help_text=_("Distribuzione classi, parametri modello, etc.")
    )
    
    # Status
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Attivo"),
        help_text=_("Solo un modello può essere attivo alla volta")
    )
    trained_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Addestrato il")
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Attivato il")
    )
    
    # Note
    notes = models.TextField(
        blank=True,
        verbose_name=_("Note"),
        help_text=_("Note sul training, cambiamenti, esperimenti")
    )
    
    class Meta:
        verbose_name = _("Modello ML")
        verbose_name_plural = _("Modelli ML")
        ordering = ['-trained_at']
        indexes = [
            models.Index(fields=['is_active', '-trained_at']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self) -> str:
        status = "🟢 ATTIVO" if self.is_active else "⚪"
        return f"{status} {self.version} - {self.model_type} (Acc: {self.accuracy:.2%})"
    
    def clean(self):
        """Validazione modello"""
        # Accuracy, precision, recall, f1 devono essere tra 0 e 1
        for field_name in ['accuracy', 'precision', 'recall', 'f1_score']:
            value = getattr(self, field_name, None)
            if value is not None and not (0 <= value <= 1):
                raise ValidationError({
                    field_name: _(f"{field_name} deve essere tra 0 e 1")
                })
    
    def activate(self):
        """Attiva questo modello e disattiva gli altri"""
        # Disattiva tutti gli altri modelli
        MLModel.objects.filter(is_active=True).update(
            is_active=False,
            activated_at=None
        )
        # Attiva questo
        self.is_active = True
        self.activated_at = timezone.now()
        self.save(update_fields=['is_active', 'activated_at'])
        logger.info(f"✅ Modello {self.version} attivato")
    
    @classmethod
    def get_active_model(cls) -> Optional['MLModel']:
        """Restituisce il modello attualmente attivo"""
        return cls.objects.filter(is_active=True).first()


class DocumentPrediction(models.Model):
    """
    Predizioni fatte dal sistema ML + feedback utente.
    Usato per il feedback loop e re-training.
    """
    FEEDBACK_CHOICES = [
        ('correct', _('Corretto')),
        ('incorrect', _('Errato')),
        ('partially_correct', _('Parzialmente corretto')),
    ]
    
    # Documento creato
    documento = models.OneToOneField(
        'documenti.Documento',
        on_delete=models.CASCADE,
        related_name='ml_prediction',
        verbose_name=_("Documento")
    )
    
    # File originale (per deduplica)
    original_filename = models.CharField(
        max_length=500,
        verbose_name=_("Filename originale")
    )
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_("Hash file"),
        help_text=_("SHA256 del contenuto per deduplica")
    )
    
    # --- Predizioni ML ---
    predicted_type = models.ForeignKey(
        'documenti.DocumentiTipo',
        related_name='ml_predictions',
        on_delete=models.CASCADE,
        verbose_name=_("Tipo predetto")
    )
    predicted_cliente = models.ForeignKey(
        'anagrafiche.Cliente',
        null=True,
        blank=True,
        related_name='ml_predictions',
        on_delete=models.SET_NULL,
        verbose_name=_("Cliente predetto")
    )
    predicted_titolario = models.ForeignKey(
        'titolario.TitolarioVoce',
        null=True,
        blank=True,
        related_name='ml_predictions',
        on_delete=models.SET_NULL,
        verbose_name=_("Titolario predetto")
    )
    predicted_data_documento = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data documento predetta")
    )
    predicted_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Altri metadata predetti"),
        help_text=_("Importi, numeri documento, CF, P.IVA, etc.")
    )
    
    # --- Confidence Scores ---
    type_confidence = models.FloatField(
        verbose_name=_("Confidence tipo"),
        help_text=_("Score 0-1 per il tipo documento")
    )
    cliente_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Confidence cliente")
    )
    titolario_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Confidence titolario")
    )
    
    # --- User Feedback ---
    user_confirmed = models.BooleanField(
        default=False,
        verbose_name=_("Utente ha confermato"),
        help_text=_("True se l'utente ha accettato tutte le predizioni")
    )
    user_corrected = models.BooleanField(
        default=False,
        verbose_name=_("Utente ha corretto"),
        help_text=_("True se l'utente ha modificato almeno una predizione")
    )
    correction_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Dati correzione"),
        help_text=_("Dettaglio delle correzioni: {campo: {predicted: X, actual: Y}}")
    )
    
    # Feedback esplicito
    user_feedback = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Feedback utente")
    )
    user_notes = models.TextField(
        blank=True,
        verbose_name=_("Note utente"),
        help_text=_("Note libere dell'utente sul risultato")
    )
    
    # --- ML Model usato ---
    ml_model = models.ForeignKey(
        MLModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='predictions',
        verbose_name=_("Modello ML")
    )
    
    # --- Features estratte (salvate per re-training) ---
    extracted_features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Features estratte"),
        help_text=_("TF-IDF vector, NER entities, patterns matched, etc.")
    )
    
    # --- Timestamp ---
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creato il")
    )
    feedback_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Feedback ricevuto il")
    )
    
    # --- Training usage ---
    used_for_training = models.BooleanField(
        default=False,
        verbose_name=_("Usato per training"),
        help_text=_("True se questo esempio è stato incluso in un re-training")
    )
    
    class Meta:
        verbose_name = _("Predizione Documento")
        verbose_name_plural = _("Predizioni Documenti")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file_hash']),
            models.Index(fields=['user_feedback', 'used_for_training']),
            models.Index(fields=['ml_model', '-created_at']),
            models.Index(fields=['-type_confidence']),
        ]
    
    def __str__(self) -> str:
        feedback_icon = {
            'correct': '✅',
            'incorrect': '❌',
            'partially_correct': '⚠️',
        }.get(self.user_feedback, '❓')
        return f"{feedback_icon} Doc #{self.documento.id} - {self.predicted_type.codice} ({self.type_confidence:.0%})"
    
    def submit_feedback(self, feedback_type: str, corrections: dict = None, notes: str = ""):
        """Registra feedback utente"""
        self.user_feedback = feedback_type
        self.feedback_at = timezone.now()
        self.user_notes = notes
        
        if feedback_type == 'correct':
            self.user_confirmed = True
        elif feedback_type in ['incorrect', 'partially_correct']:
            self.user_corrected = True
            if corrections:
                self.correction_data = corrections
        
        self.save()
        logger.info(f"📝 Feedback ricevuto per Doc #{self.documento.id}: {feedback_type}")
        
        # Aggiungi a coda training se correzione
        if self.user_corrected:
            TrainingQueue.objects.get_or_create(prediction=self)


class TrainingQueue(models.Model):
    """
    Coda di esempi per il prossimo re-training.
    Accumula predizioni con feedback per batch training.
    """
    prediction = models.ForeignKey(
        DocumentPrediction,
        on_delete=models.CASCADE,
        related_name='training_queue_entries',
        verbose_name=_("Predizione")
    )
    queued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Accodato il")
    )
    processed = models.BooleanField(
        default=False,
        verbose_name=_("Processato"),
        help_text=_("True se incluso in un training job")
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Processato il")
    )
    training_job = models.ForeignKey(
        'TrainingJob',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='queue_entries',
        verbose_name=_("Job training")
    )
    
    class Meta:
        verbose_name = _("Coda Training")
        verbose_name_plural = _("Code Training")
        ordering = ['queued_at']
        indexes = [
            models.Index(fields=['processed', 'queued_at']),
        ]
    
    def __str__(self) -> str:
        status = "✅" if self.processed else "⏳"
        return f"{status} Queue #{self.id} - Doc #{self.prediction.documento.id}"


class TrainingJob(models.Model):
    """
    Job di re-training periodico.
    Traccia ogni esecuzione del training con risultati.
    """
    STATUS_CHOICES = [
        ('running', _('In esecuzione')),
        ('completed', _('Completato')),
        ('failed', _('Fallito')),
    ]
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Avviato il")
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completato il")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running',
        verbose_name=_("Stato")
    )
    
    # Risultati
    new_model = models.ForeignKey(
        MLModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='training_jobs',
        verbose_name=_("Nuovo modello")
    )
    previous_model = models.ForeignKey(
        MLModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='previous_for_jobs',
        verbose_name=_("Modello precedente")
    )
    
    training_samples_count = models.IntegerField(
        default=0,
        verbose_name=_("Campioni training"),
        help_text=_("Numero totale di documenti usati (vecchi + nuovi)")
    )
    new_samples_count = models.IntegerField(
        default=0,
        verbose_name=_("Nuovi campioni"),
        help_text=_("Numero di nuovi documenti dalla coda")
    )
    
    accuracy_improvement = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Miglioramento accuracy"),
        help_text=_("Differenza accuracy: nuovo modello - vecchio modello")
    )
    
    # Logs e errori
    logs = models.TextField(
        blank=True,
        verbose_name=_("Log"),
        help_text=_("Log completo dell'esecuzione training")
    )
    errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Errori")
    )
    
    # Automatico o manuale
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Avviato da"),
        help_text=_("Null se automatico (cron)")
    )
    
    class Meta:
        verbose_name = _("Job Training")
        verbose_name_plural = _("Jobs Training")
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self) -> str:
        status_icons = {
            'running': '⏳',
            'completed': '✅',
            'failed': '❌',
        }
        icon = status_icons.get(self.status, '❓')
        improvement = f" (+{self.accuracy_improvement:.2%})" if self.accuracy_improvement else ""
        return f"{icon} Training Job #{self.id} - {self.started_at:%Y-%m-%d %H:%M}{improvement}"
    
    def complete(self, new_model: MLModel, accuracy_improvement: float):
        """Completa il job con successo"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.new_model = new_model
        self.accuracy_improvement = accuracy_improvement
        self.save()
        logger.info(f"✅ Training job #{self.id} completato. Accuracy migliorata di {accuracy_improvement:.2%}")
    
    def fail(self, error_message: str):
        """Segna il job come fallito"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.errors.append({
            'timestamp': timezone.now().isoformat(),
            'message': error_message
        })
        self.save()
        logger.error(f"❌ Training job #{self.id} fallito: {error_message}")


# =============================================================================
# AI IMPORT & TEMPLATE MODELS
# =============================================================================

class DocumentExtractionTemplate(models.Model):
    """
    Template per estrazione dati da documenti di un tipo specifico.
    Contiene immagini/PDF template con zone evidenziate per l'estrazione OCR.
    """
    tipo_documento = models.ForeignKey(
        'documenti.DocumentiTipo',
        on_delete=models.CASCADE,
        related_name='extraction_templates',
        verbose_name=_("Tipo Documento")
    )
    nome = models.CharField(
        max_length=200,
        verbose_name=_("Nome Template"),
        help_text=_("Nome descrittivo del template (es. 'UNILAV Standard 2026')")
    )
    descrizione = models.TextField(
        blank=True,
        verbose_name=_("Descrizione"),
        help_text=_("Descrizione dettagliata del template e quando usarlo")
    )
    
    # Template files (può avere più pagine)
    numero_pagine = models.IntegerField(
        default=1,
        verbose_name=_("Numero Pagine"),
        help_text=_("Numero di pagine del template")
    )
    
    # Metadata
    attivo = models.BooleanField(
        default=True,
        verbose_name=_("Attivo"),
        help_text=_("Se False, il template non verrà usato per l'estrazione")
    )
    priorita = models.IntegerField(
        default=0,
        verbose_name=_("Priorità"),
        help_text=_("Ordine di preferenza (maggiore = più priorità)")
    )
    
    # Timestamp
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name=_("Creato il"))
    aggiornato_il = models.DateTimeField(auto_now=True, verbose_name=_("Aggiornato il"))
    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates_creati',
        verbose_name=_("Creato da")
    )
    
    class Meta:
        verbose_name = _("Template Estrazione")
        verbose_name_plural = _("Template Estrazione")
        ordering = ['-priorita', '-creato_il']
        unique_together = [('tipo_documento', 'nome')]
    
    def __str__(self):
        return f"{self.tipo_documento.codice} - {self.nome}"


class ExtractionTemplatePage(models.Model):
    """
    Singola pagina di un template di estrazione.
    Contiene l'immagine template e le zone di estrazione.
    """
    template = models.ForeignKey(
        DocumentExtractionTemplate,
        on_delete=models.CASCADE,
        related_name='pagine',
        verbose_name=_("Template")
    )
    numero_pagina = models.IntegerField(
        verbose_name=_("Numero Pagina"),
        help_text=_("Numero progressivo della pagina (1-based)")
    )
    immagine_template = models.ImageField(
        upload_to='extraction_templates/%Y/%m/',
        verbose_name=_("Immagine Template"),
        help_text=_("Immagine della pagina con zone evidenziate")
    )
    
    # Dimensioni immagine template (per calcolo coordinate)
    larghezza = models.IntegerField(
        verbose_name=_("Larghezza (px)"),
        help_text=_("Larghezza dell'immagine template in pixel")
    )
    altezza = models.IntegerField(
        verbose_name=_("Altezza (px)"),
        help_text=_("Altezza dell'immagine template in pixel")
    )
    
    class Meta:
        verbose_name = _("Pagina Template")
        verbose_name_plural = _("Pagine Template")
        ordering = ['template', 'numero_pagina']
        unique_together = [('template', 'numero_pagina')]
    
    def __str__(self):
        return f"{self.template.nome} - Pagina {self.numero_pagina}"


class ExtractionTemplateZone(models.Model):
    """
    Zona di estrazione in una pagina template.
    Definisce un'area rettangolare da cui estrarre dati specifici.
    """
    TIPO_DATO_CHOICES = [
        ('text', _('Testo')),
        ('codice_fiscale', _('Codice Fiscale')),
        ('partita_iva', _('Partita IVA')),
        ('date', _('Data')),
        ('decimal', _('Numero Decimale')),
        ('integer', _('Numero Intero')),
        ('email', _('Email')),
        ('phone', _('Telefono')),
        ('currency', _('Importo Valuta')),
    ]
    
    pagina = models.ForeignKey(
        ExtractionTemplatePage,
        on_delete=models.CASCADE,
        related_name='zone',
        verbose_name=_("Pagina Template")
    )
    
    # Identificazione zona
    nome_campo = models.CharField(
        max_length=100,
        verbose_name=_("Nome Campo"),
        help_text=_("Nome identificativo del campo da estrarre (es. 'codice_fiscale_datore')")
    )
    etichetta = models.CharField(
        max_length=200,
        verbose_name=_("Etichetta"),
        help_text=_("Etichetta human-readable (es. 'Codice Fiscale Datore di Lavoro')")
    )
    
    # Coordinate zona (percentuali rispetto a larghezza/altezza template)
    x_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("X (%)"),
        help_text=_("Posizione X in percentuale (0-100)")
    )
    y_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Y (%)"),
        help_text=_("Posizione Y in percentuale (0-100)")
    )
    width_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Larghezza (%)"),
        help_text=_("Larghezza in percentuale (0-100)")
    )
    height_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Altezza (%)"),
        help_text=_("Altezza in percentuale (0-100)")
    )
    
    # Tipo dato e validazione
    tipo_dato = models.CharField(
        max_length=20,
        choices=TIPO_DATO_CHOICES,
        default='text',
        verbose_name=_("Tipo Dato")
    )
    obbligatorio = models.BooleanField(
        default=False,
        verbose_name=_("Obbligatorio"),
        help_text=_("Se True, l'estrazione fallisce se questo campo è vuoto")
    )
    
    # Pattern validazione (regex opzionale)
    pattern_validazione = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Pattern Validazione"),
        help_text=_("Espressione regolare per validare il dato estratto (opzionale)")
    )
    
    # Ordine visualizzazione
    ordine = models.IntegerField(
        default=0,
        verbose_name=_("Ordine"),
        help_text=_("Ordine di visualizzazione nel form")
    )
    
    class Meta:
        verbose_name = _("Zona Estrazione")
        verbose_name_plural = _("Zone Estrazione")
        ordering = ['pagina', 'ordine', 'nome_campo']
        unique_together = [('pagina', 'nome_campo')]
    
    def __str__(self):
        return f"{self.pagina.template.nome} - {self.etichetta}"
    
    def get_absolute_coordinates(self):
        """Calcola coordinate assolute basate sulle dimensioni del template"""
        return {
            'x': int(float(self.x_percent) * self.pagina.larghezza / 100),
            'y': int(float(self.y_percent) * self.pagina.altezza / 100),
            'width': int(float(self.width_percent) * self.pagina.larghezza / 100),
            'height': int(float(self.height_percent) * self.pagina.altezza / 100),
        }


class ExtractionFieldMapping(models.Model):
    """
    Mapping tra campi estratti dal template e campi del modello Documento.
    Definisce come i dati estratti vengono mappati sui campi del form.
    """
    TIPO_CAMPO_CHOICES = [
        ('field', _('Campo Modello')),
        ('attribute', _('Attributo Dinamico')),
        ('note', _('Note')),
        ('metadata', _('Metadata')),
    ]
    
    template = models.ForeignKey(
        DocumentExtractionTemplate,
        on_delete=models.CASCADE,
        related_name='mapping_campi',
        verbose_name=_("Template")
    )
    
    # Campo sorgente (dal template)
    nome_campo_template = models.CharField(
        max_length=100,
        verbose_name=_("Nome Campo Template"),
        help_text=_("Nome del campo nel template (deve corrispondere a una zona)")
    )
    
    # Campo destinazione
    tipo_campo_destinazione = models.CharField(
        max_length=20,
        choices=TIPO_CAMPO_CHOICES,
        verbose_name=_("Tipo Campo Destinazione")
    )
    nome_campo_destinazione = models.CharField(
        max_length=200,
        verbose_name=_("Nome Campo Destinazione"),
        help_text=_("Nome del campo nel modello (es. 'data_documento', 'cliente.codice_fiscale', 'attributo:retribuzione')")
    )
    
    # Trasformazione dati (opzionale)
    funzione_trasformazione = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Funzione Trasformazione"),
        help_text=_("Nome funzione per trasformare il dato (es. 'parse_date_it', 'normalize_cf')")
    )
    
    # Formato dato estratto
    formato_input = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Formato Input"),
        help_text=_("Formato del dato estratto (es. 'DD/MM/YYYY' per date)")
    )
    
    # Default se estrazione fallisce
    valore_default = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Valore Default"),
        help_text=_("Valore da usare se l'estrazione fallisce")
    )
    
    class Meta:
        verbose_name = _("Mapping Campo")
        verbose_name_plural = _("Mapping Campi")
        ordering = ['template', 'nome_campo_template']
        unique_together = [('template', 'nome_campo_template')]
    
    def __str__(self):
        return f"{self.nome_campo_template} → {self.nome_campo_destinazione}"


class AIPredictionFeedback(models.Model):
    """
    Feedback sulla predizione del tipo documento.
    Traccia predizioni corrette/errate per migliorare il training.
    """
    # Documento originale
    documento = models.ForeignKey(
        'documenti.Documento',
        on_delete=models.CASCADE,
        related_name='ai_feedback',
        verbose_name=_("Documento")
    )
    
    # Predizione AI
    tipo_predetto = models.ForeignKey(
        'documenti.DocumentiTipo',
        on_delete=models.CASCADE,
        related_name='predizioni_ai',
        verbose_name=_("Tipo Predetto AI")
    )
    confidence_predizione = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        verbose_name=_("Confidence Predizione"),
        help_text=_("Probabilità della predizione (0-1)")
    )
    top_3_predizioni = models.JSONField(
        default=list,
        verbose_name=_("Top 3 Predizioni"),
        help_text=_("Lista delle 3 predizioni più probabili con confidence")
    )
    
    # Tipo confermato dall'utente
    tipo_confermato = models.ForeignKey(
        'documenti.DocumentiTipo',
        on_delete=models.CASCADE,
        related_name='conferme_utente',
        verbose_name=_("Tipo Confermato Utente")
    )
    
    # Feedback
    predizione_corretta = models.BooleanField(
        verbose_name=_("Predizione Corretta"),
        help_text=_("True se tipo_predetto == tipo_confermato")
    )
    
    # Dati estratti (per training futuro)
    dati_estratti_ai = models.JSONField(
        default=dict,
        verbose_name=_("Dati Estratti AI"),
        help_text=_("Dati estratti automaticamente dall'AI")
    )
    
    # Metadati
    utente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Utente"),
        help_text=_("Utente che ha confermato il tipo")
    )
    data_predizione = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data Predizione")
    )
    
    # Training status
    usato_per_training = models.BooleanField(
        default=False,
        verbose_name=_("Usato per Training"),
        help_text=_("True se questo feedback è già stato usato per il re-training")
    )
    training_job = models.ForeignKey(
        'TrainingJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_usati',
        verbose_name=_("Training Job")
    )
    
    class Meta:
        verbose_name = _("Feedback Predizione AI")
        verbose_name_plural = _("Feedback Predizioni AI")
        ordering = ['-data_predizione']
        indexes = [
            models.Index(fields=['-data_predizione']),
            models.Index(fields=['predizione_corretta']),
            models.Index(fields=['usato_per_training']),
        ]
    
    def __str__(self):
        status = "✅" if self.predizione_corretta else "❌"
        return f"{status} {self.documento.codice}: {self.tipo_predetto.codice} → {self.tipo_confermato.codice}"
    
    def save(self, *args, **kwargs):
        # Auto-calcola se la predizione è corretta
        self.predizione_corretta = (self.tipo_predetto_id == self.tipo_confermato_id)
        super().save(*args, **kwargs)


class ExtractionCorrection(models.Model):
    """
    Correzione manuale di un campo estratto automaticamente.
    Traccia le modifiche dell'utente per migliorare l'estrazione futura.
    """
    feedback = models.ForeignKey(
        AIPredictionFeedback,
        on_delete=models.CASCADE,
        related_name='correzioni',
        verbose_name=_("Feedback AI")
    )
    
    # Campo corretto
    nome_campo = models.CharField(
        max_length=100,
        verbose_name=_("Nome Campo"),
        help_text=_("Nome del campo corretto")
    )
    
    # Valori
    valore_estratto = models.TextField(
        verbose_name=_("Valore Estratto AI"),
        help_text=_("Valore estratto automaticamente")
    )
    valore_corretto = models.TextField(
        verbose_name=_("Valore Corretto Utente"),
        help_text=_("Valore corretto dall'utente")
    )
    
    # Confidence originale
    confidence_estrazione = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Confidence Estrazione"),
        help_text=_("Confidence dell'estrazione OCR (se disponibile)")
    )
    
    # Metadati
    data_correzione = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data Correzione")
    )
    
    # Training status
    usato_per_training = models.BooleanField(
        default=False,
        verbose_name=_("Usato per Training")
    )
    
    class Meta:
        verbose_name = _("Correzione Estrazione")
        verbose_name_plural = _("Correzioni Estrazione")
        ordering = ['-data_correzione']
        indexes = [
            models.Index(fields=['nome_campo']),
            models.Index(fields=['usato_per_training']),
        ]
    
    def __str__(self):
        return f"{self.nome_campo}: '{self.valore_estratto}' → '{self.valore_corretto}'"
