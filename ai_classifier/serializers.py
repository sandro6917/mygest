"""
Serializers per API AI Classifier
"""
from rest_framework import serializers
from .models import ClassificationJob, ClassificationResult, ClassifierConfig


class ClassificationJobSerializer(serializers.ModelSerializer):
    """Serializer per ClassificationJob (lettura)"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ClassificationJob
        fields = [
            'id',
            'directory_path',
            'status',
            'status_display',
            'created_at',
            'started_at',
            'completed_at',
            'total_files',
            'processed_files',
            'successful_files',
            'failed_files',
            'progress_percentage',
            'errors',
            'use_llm',
            'llm_provider',
            'created_by',
            'created_by_username',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'started_at',
            'completed_at',
            'total_files',
            'processed_files',
            'successful_files',
            'failed_files',
            'errors',
            'created_by',
        ]


class ClassificationJobCreateSerializer(serializers.ModelSerializer):
    """Serializer per creazione ClassificationJob"""
    
    class Meta:
        model = ClassificationJob
        fields = [
            'directory_path',
            'use_llm',
            'llm_provider',
        ]
    
    def validate_directory_path(self, value):
        """Valida che directory_path sia accessibile"""
        from .utils.file_handlers import PathValidator
        
        if not PathValidator.is_valid_path(value):
            raise serializers.ValidationError(
                f"Directory non valida o inaccessibile: {value}"
            )
        
        return PathValidator.normalize_path(value)
    
    def create(self, validated_data):
        """Crea job e assegna user corrente"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ClassificationResultSerializer(serializers.ModelSerializer):
    """Serializer per ClassificationResult"""
    
    predicted_type_display = serializers.CharField(source='get_predicted_type_display', read_only=True)
    confidence_level_display = serializers.CharField(source='get_confidence_level_display', read_only=True)
    
    # Nested info (opzionale)
    suggested_cliente_nome = serializers.CharField(
        source='suggested_cliente.anagrafica.nome',
        read_only=True,
        allow_null=True
    )
    suggested_fascicolo_nome = serializers.CharField(
        source='suggested_fascicolo.nome',
        read_only=True,
        allow_null=True
    )
    documento_codice = serializers.CharField(
        source='documento.codice',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ClassificationResult
        fields = [
            'id',
            'job',
            'file_path',
            'file_name',
            'file_size',
            'mime_type',
            'predicted_type',
            'predicted_type_display',
            'confidence_level',
            'confidence_level_display',
            'confidence_score',
            'classification_method',
            'extracted_text',
            'extracted_metadata',
            'suggested_cliente',
            'suggested_cliente_nome',
            'suggested_fascicolo',
            'suggested_fascicolo_nome',
            'suggested_titolario',
            'imported',
            'documento',
            'documento_codice',
            'imported_at',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'imported_at',
        ]


class ClassificationResultUpdateSerializer(serializers.ModelSerializer):
    """Serializer per aggiornamento manuale ClassificationResult"""
    
    class Meta:
        model = ClassificationResult
        fields = [
            'predicted_type',
            'confidence_score',
            'suggested_cliente',
            'suggested_fascicolo',
            'suggested_titolario',
            'notes',
        ]
    
    def validate_confidence_score(self, value):
        """Valida confidence_score"""
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError("Confidence score deve essere tra 0.0 e 1.0")
        return value


class ClassifierConfigSerializer(serializers.ModelSerializer):
    """Serializer per ClassifierConfig"""
    
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = ClassifierConfig
        fields = [
            'id',
            'openai_api_key',
            'default_llm_provider',
            'llm_model',
            'llm_temperature',
            'llm_max_tokens',
            'confidence_threshold',
            'filename_patterns',
            'content_patterns',
            'max_file_size_mb',
            'allowed_extensions',
            'updated_at',
            'updated_by',
            'updated_by_username',
        ]
        read_only_fields = ['id', 'updated_at', 'updated_by']
        extra_kwargs = {
            'openai_api_key': {'write_only': True}  # Non esporre API key in read
        }
    
    def validate_llm_temperature(self, value):
        """Valida temperature"""
        if not (0.0 <= value <= 2.0):
            raise serializers.ValidationError("Temperature deve essere tra 0.0 e 2.0")
        return value
    
    def validate_confidence_threshold(self, value):
        """Valida confidence threshold"""
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError("Confidence threshold deve essere tra 0.0 e 1.0")
        return value
    
    def validate_filename_patterns(self, value):
        """Valida filename patterns"""
        from .utils.validators import ConfigValidator
        
        if not ConfigValidator.validate_patterns(value):
            raise serializers.ValidationError("Filename patterns non validi")
        return value
    
    def validate_content_patterns(self, value):
        """Valida content patterns"""
        from .utils.validators import ConfigValidator
        
        if not ConfigValidator.validate_patterns(value):
            raise serializers.ValidationError("Content patterns non validi")
        return value
    
    def update(self, instance, validated_data):
        """Aggiorna config e traccia user"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ImportDocumentsSerializer(serializers.Serializer):
    """Serializer per importazione batch documenti"""
    
    result_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Lista di ID ClassificationResult da importare"
    )
    
    # Opzioni importazione
    copy_files = serializers.BooleanField(
        default=True,
        help_text="Se True, copia file nel NAS. Se False, crea solo record documento."
    )
    delete_source = serializers.BooleanField(
        default=False,
        help_text="Se True, elimina file sorgente dopo import (solo se copy_files=True)"
    )
    
    def validate_result_ids(self, value):
        """Valida che i result ID esistano e non siano già importati"""
        if not value:
            raise serializers.ValidationError("Devi fornire almeno un result ID")
        
        # Verifica esistenza
        results = ClassificationResult.objects.filter(id__in=value)
        if results.count() != len(value):
            raise serializers.ValidationError("Alcuni result ID non esistono")
        
        # Verifica non già importati
        already_imported = results.filter(imported=True)
        if already_imported.exists():
            raise serializers.ValidationError(
                f"{already_imported.count()} risultati già importati"
            )
        
        return value
