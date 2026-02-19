"""
Django Admin per AI Classifier
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ClassificationJob, ClassificationResult, ClassifierConfig, TrainingExample


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
                'openai_api_key',
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
