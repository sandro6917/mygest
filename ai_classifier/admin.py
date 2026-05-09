"""
Django Admin per AI Classifier
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClassificationJob, 
    ClassificationResult, 
    ClassifierConfig, 
    TrainingExample,
    MLModel,
    DocumentPrediction,
    TrainingQueue,
    TrainingJob,
)


@admin.register(ClassificationJob)
class ClassificationJobAdmin(admin.ModelAdmin):
    """Admin per ClassificationJob"""
    
    list_display = [
        'id',
        'directory_path',
        'status',
        'created_by',
        'created_at',
        'total_files',
        'processed_files',
        'successful_files',
        'failed_files',
    ]
    list_filter = ['status', 'created_at', 'use_llm']
    search_fields = ['directory_path']
    readonly_fields = [
        'id',
        'created_at',
        'started_at',
        'completed_at',
        'total_files',
        'processed_files',
        'successful_files',
        'failed_files',
        'errors',
        'progress_percentage',
    ]
    
    fieldsets = (
        ('Info Job', {
            'fields': ('id', 'directory_path', 'status', 'created_by')
        }),
        ('Opzioni', {
            'fields': ('use_llm', 'llm_provider')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Statistiche', {
            'fields': (
                'total_files',
                'processed_files',
                'successful_files',
                'failed_files',
                'progress_percentage',
            )
        }),
        ('Errori', {
            'fields': ('errors',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disabilita creazione manuale da admin (usa API)"""
        return False


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    """Admin per ClassificationResult"""
    
    list_display = [
        'id',
        'file_name',
        'job',
        'predicted_type',
        'confidence_level',
        'confidence_score',
        'classification_method',
        'imported',
        'created_at',
    ]
    list_filter = [
        'predicted_type',
        'confidence_level',
        'classification_method',
        'imported',
        'created_at',
    ]
    search_fields = ['file_name', 'file_path', 'notes']
    readonly_fields = [
        'id',
        'job',
        'file_path',
        'file_name',
        'file_size',
        'mime_type',
        'extracted_text',
        'extracted_metadata',
        'classification_method',
        'created_at',
        'updated_at',
        'imported_at',
    ]
    
    fieldsets = (
        ('File Info', {
            'fields': ('id', 'job', 'file_path', 'file_name', 'file_size', 'mime_type')
        }),
        ('Classificazione', {
            'fields': (
                'predicted_type',
                'confidence_score',
                'confidence_level',
                'classification_method',
            )
        }),
        ('Testo Estratto', {
            'fields': ('extracted_text',),
            'classes': ('collapse',)
        }),
        ('Metadata Estratti', {
            'fields': ('extracted_metadata',),
            'classes': ('collapse',)
        }),
        ('Suggerimenti Importazione', {
            'fields': (
                'suggested_cliente',
                'suggested_fascicolo',
                'suggested_titolario',
            )
        }),
        ('Importazione', {
            'fields': ('imported', 'documento', 'imported_at')
        }),
        ('Note', {
            'fields': ('notes',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Disabilita creazione manuale da admin"""
        return False


@admin.register(ClassifierConfig)
class ClassifierConfigAdmin(admin.ModelAdmin):
    """Admin per ClassifierConfig (singleton)"""
    
    list_display = ['id', 'default_llm_provider', 'llm_model', 'confidence_threshold', 'updated_at']
    readonly_fields = ['id', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('LLM Configuration', {
            'fields': (
                'default_llm_provider',
                'llm_model',
                'llm_temperature',
                'llm_max_tokens',
            )
        }),
        ('Classification Settings', {
            'fields': (
                'confidence_threshold',
                'filename_patterns',
                'content_patterns',
            )
        }),
        ('File Settings', {
            'fields': (
                'max_file_size_mb',
                'allowed_extensions',
            )
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by')
        }),
    )
    
    def has_add_permission(self, request):
        """Singleton: non permettere creazione multipla"""
        if ClassifierConfig.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Proteggi singleton dalla cancellazione"""
        return False


@admin.register(TrainingExample)
class TrainingExampleAdmin(admin.ModelAdmin):
    """Admin per TrainingExample - Gestione esempi di training"""
    
    list_display = [
        'id',
        'file_name_display',
        'document_type',
        'is_active',
        'priority',
        'created_at',
        'created_by',
    ]
    list_filter = ['document_type', 'is_active', 'priority', 'created_at']
    search_fields = ['file_name', 'description', 'extracted_text']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('File di Esempio', {
            'fields': ('file_name', 'file_path')
        }),
        ('Classificazione', {
            'fields': ('document_type', 'description')
        }),
        ('Contenuto Estratto', {
            'fields': ('extracted_text', 'extracted_metadata'),
            'classes': ('collapse',)  # Collassato di default
        }),
        ('Configurazione', {
            'fields': ('is_active', 'priority')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def file_name_display(self, obj):
        """Mostra nome file con icona se attivo"""
        if obj.is_active:
            return format_html('✅ {}', obj.file_name)
        return format_html('⭕ {}', obj.file_name)
    file_name_display.short_description = 'Nome File'
    
    def save_model(self, request, obj, form, change):
        """Auto-assegna utente creazione"""
        if not change:  # Nuovo oggetto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_examples', 'deactivate_examples', 'set_high_priority']
    
    def activate_examples(self, request, queryset):
        """Attiva esempi selezionati"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} esempi attivati')
    activate_examples.short_description = 'Attiva esempi selezionati'
    
    def deactivate_examples(self, request, queryset):
        """Disattiva esempi selezionati"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} esempi disattivati')
    deactivate_examples.short_description = 'Disattiva esempi selezionati'
    
    def set_high_priority(self, request, queryset):
        """Imposta priorità alta"""
        updated = queryset.update(priority=10)
        self.message_user(request, f'{updated} esempi impostati con priorità alta')
    set_high_priority.short_description = 'Imposta priorità alta (10)'


# ============================================================================
# ADMIN PER NUOVI MODELLI ML
# ============================================================================

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    """Admin per MLModel - Versioning modelli addestrati"""
    
    list_display = [
        'version_badge',
        'model_type',
        'accuracy_badge',
        'training_samples',
        'trained_at',
        'is_active',
    ]
    list_filter = ['model_type', 'is_active', 'trained_at']
    search_fields = ['version', 'notes']
    readonly_fields = [
        'trained_at',
        'activated_at',
        'training_stats_display',
    ]
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('version', 'model_type', 'is_active')
        }),
        ('File Modello', {
            'fields': (
                'model_file_path',
                'vectorizer_file_path',
                'label_encoder_file_path',
            )
        }),
        ('Metriche', {
            'fields': (
                'accuracy',
                'precision',
                'recall',
                'f1_score',
            )
        }),
        ('Dati Training', {
            'fields': (
                'training_samples',
                'training_stats_display',
            )
        }),
        ('Timestamp', {
            'fields': ('trained_at', 'activated_at')
        }),
        ('Note', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def version_badge(self, obj):
        """Badge versione con icona stato"""
        icon = "🟢" if obj.is_active else "⚪"
        color = "success" if obj.is_active else "secondary"
        return format_html(
            '{} <span class="badge badge-{}">{}</span>',
            icon, color, obj.version
        )
    version_badge.short_description = 'Versione'
    
    def accuracy_badge(self, obj):
        """Badge accuracy colorato"""
        percentage = obj.accuracy * 100
        if percentage >= 85:
            color = "success"
        elif percentage >= 70:
            color = "warning"
        else:
            color = "danger"
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, f"{percentage:.1f}%"
        )
    accuracy_badge.short_description = 'Accuracy'
    
    def training_stats_display(self, obj):
        """Visualizza statistiche training formattate"""
        if not obj.training_stats:
            return "-"
        
        stats_html = "<ul>"
        for key, value in obj.training_stats.items():
            stats_html += f"<li><strong>{key}:</strong> {value}</li>"
        stats_html += "</ul>"
        return format_html(stats_html)
    training_stats_display.short_description = 'Statistiche Training'
    
    actions = ['activate_model']
    
    def activate_model(self, request, queryset):
        """Attiva modello selezionato"""
        if queryset.count() > 1:
            self.message_user(request, 'Seleziona un solo modello da attivare', level='error')
            return
        
        model = queryset.first()
        model.activate()
        self.message_user(request, f'✅ Modello {model.version} attivato')
    activate_model.short_description = 'Attiva modello selezionato'


@admin.register(DocumentPrediction)
class DocumentPredictionAdmin(admin.ModelAdmin):
    """Admin per DocumentPrediction - Predizioni e feedback"""
    
    list_display = [
        'id',
        'documento_link',
        'predicted_type',
        'type_confidence_badge',
        'user_feedback_badge',
        'ml_model',
        'used_for_training',
        'created_at',
    ]
    list_filter = [
        'user_feedback',
        'user_confirmed',
        'user_corrected',
        'used_for_training',
        'predicted_type',
        'ml_model',
        'created_at',
    ]
    search_fields = [
        'documento__id',
        'documento__codice',
        'original_filename',
        'file_hash',
    ]
    readonly_fields = [
        'documento',
        'created_at',
        'feedback_at',
        'correction_data_display',
        'extracted_features_display',
    ]
    
    fieldsets = (
        ('Documento', {
            'fields': ('documento', 'original_filename', 'file_hash')
        }),
        ('Predizioni ML', {
            'fields': (
                'predicted_type',
                'predicted_cliente',
                'predicted_titolario',
                'predicted_data_documento',
                'predicted_metadata',
            )
        }),
        ('Confidence Scores', {
            'fields': (
                'type_confidence',
                'cliente_confidence',
                'titolario_confidence',
            )
        }),
        ('Feedback Utente', {
            'fields': (
                'user_confirmed',
                'user_corrected',
                'user_feedback',
                'user_notes',
                'correction_data_display',
            )
        }),
        ('ML Info', {
            'fields': (
                'ml_model',
                'extracted_features_display',
                'used_for_training',
            )
        }),
        ('Timestamp', {
            'fields': ('created_at', 'feedback_at')
        }),
    )
    
    def documento_link(self, obj):
        """Link al documento"""
        return format_html(
            '<a href="/admin/documenti/documento/{}/change/">Doc #{}</a>',
            obj.documento.id, obj.documento.id
        )
    documento_link.short_description = 'Documento'
    
    def type_confidence_badge(self, obj):
        """Badge confidence colorato"""
        percentage = obj.type_confidence * 100
        if percentage >= 90:
            color = "success"
        elif percentage >= 70:
            color = "warning"
        else:
            color = "danger"
        return format_html(
            '<span class="badge badge-{}">{:.0f}%</span>',
            color, percentage
        )
    type_confidence_badge.short_description = 'Confidence'
    
    def user_feedback_badge(self, obj):
        """Badge feedback utente"""
        if not obj.user_feedback:
            return "-"
        
        icons = {
            'correct': ('✅', 'success'),
            'incorrect': ('❌', 'danger'),
            'partially_correct': ('⚠️', 'warning'),
        }
        icon, color = icons.get(obj.user_feedback, ('❓', 'secondary'))
        return format_html(
            '{} <span class="badge badge-{}">{}</span>',
            icon, color, obj.get_user_feedback_display()
        )
    user_feedback_badge.short_description = 'Feedback'
    
    def correction_data_display(self, obj):
        """Visualizza correzioni formattate"""
        if not obj.correction_data:
            return "-"
        
        html = "<table><tr><th>Campo</th><th>Predetto</th><th>Corretto</th></tr>"
        for campo, data in obj.correction_data.items():
            html += f"<tr><td><strong>{campo}</strong></td><td>{data.get('predicted', '-')}</td><td>{data.get('actual', '-')}</td></tr>"
        html += "</table>"
        return format_html(html)
    correction_data_display.short_description = 'Correzioni'
    
    def extracted_features_display(self, obj):
        """Visualizza features estratte (sample)"""
        if not obj.extracted_features:
            return "-"
        
        # Mostra solo alcune chiavi per brevità
        sample_keys = ['tfidf_dim', 'ner_entities', 'patterns_matched']
        html = "<ul>"
        for key in sample_keys:
            if key in obj.extracted_features:
                value = obj.extracted_features[key]
                html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return format_html(html)
    extracted_features_display.short_description = 'Features (sample)'


@admin.register(TrainingQueue)
class TrainingQueueAdmin(admin.ModelAdmin):
    """Admin per TrainingQueue - Coda re-training"""
    
    list_display = [
        'id',
        'prediction_link',
        'queued_at',
        'processed',
        'processed_at',
        'training_job_link',
    ]
    list_filter = ['processed', 'queued_at']
    search_fields = ['prediction__documento__id', 'prediction__documento__codice']
    readonly_fields = ['queued_at', 'processed_at']
    
    def prediction_link(self, obj):
        """Link alla predizione"""
        return format_html(
            '<a href="/admin/ai_classifier/documentprediction/{}/change/">Pred #{}</a>',
            obj.prediction.id, obj.prediction.id
        )
    prediction_link.short_description = 'Predizione'
    
    def training_job_link(self, obj):
        """Link al training job"""
        if not obj.training_job:
            return "-"
        return format_html(
            '<a href="/admin/ai_classifier/trainingjob/{}/change/">Job #{}</a>',
            obj.training_job.id, obj.training_job.id
        )
    training_job_link.short_description = 'Training Job'


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    """Admin per TrainingJob - Jobs re-training"""
    
    list_display = [
        'id',
        'status_badge',
        'started_at',
        'completed_at',
        'training_samples_count',
        'new_samples_count',
        'accuracy_improvement_badge',
        'triggered_by',
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['new_model__version', 'logs']
    readonly_fields = [
        'started_at',
        'completed_at',
        'logs_display',
        'errors_display',
    ]
    
    fieldsets = (
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'triggered_by')
        }),
        ('Modelli', {
            'fields': ('previous_model', 'new_model')
        }),
        ('Statistiche', {
            'fields': (
                'training_samples_count',
                'new_samples_count',
                'accuracy_improvement',
            )
        }),
        ('Logs', {
            'fields': ('logs_display',),
            'classes': ('collapse',)
        }),
        ('Errori', {
            'fields': ('errors_display',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Badge status colorato"""
        icons = {
            'running': ('⏳', 'info'),
            'completed': ('✅', 'success'),
            'failed': ('❌', 'danger'),
        }
        icon, color = icons.get(obj.status, ('❓', 'secondary'))
        return format_html(
            '{} <span class="badge badge-{}">{}</span>',
            icon, color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def accuracy_improvement_badge(self, obj):
        """Badge miglioramento accuracy"""
        if obj.accuracy_improvement is None:
            return "-"
        
        percentage = obj.accuracy_improvement * 100
        if percentage > 0:
            color = "success"
            icon = "📈"
        elif percentage < 0:
            color = "danger"
            icon = "📉"
        else:
            color = "secondary"
            icon = "➡️"
        
        return format_html(
            '{} <span class="badge badge-{}">{:+.2f}%</span>',
            icon, color, percentage
        )
    accuracy_improvement_badge.short_description = 'Δ Accuracy'
    
    def logs_display(self, obj):
        """Visualizza logs formattati"""
        if not obj.logs:
            return "-"
        return format_html('<pre>{}</pre>', obj.logs[:5000])  # Max 5000 char
    logs_display.short_description = 'Logs'
    
    def errors_display(self, obj):
        """Visualizza errori formattati"""
        if not obj.errors:
            return "Nessun errore"
        
        html = "<ul>"
        for error in obj.errors:
            html += f"<li><strong>{error.get('timestamp', 'N/A')}:</strong> {error.get('message', '')}</li>"
        html += "</ul>"
        return format_html(html)
    errors_display.short_description = 'Errori'
    
    def has_add_permission(self, request):
        """Disabilita creazione manuale (usa management command)"""
        return False
