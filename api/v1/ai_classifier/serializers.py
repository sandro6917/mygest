"""
Serializers per AI Classifier API
"""
from rest_framework import serializers
from ai_classifier.models import MLModel, DocumentPrediction, TrainingJob


class MLModelSerializer(serializers.ModelSerializer):
    """
    Serializer per informazioni modello ML.
    """
    trained_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = MLModel
        fields = [
            'id',
            'version',
            'model_type',
            'accuracy',
            'precision',
            'recall',
            'f1_score',
            'training_samples',
            'is_active',
            'trained_at',
            'trained_at_formatted',
        ]
        read_only_fields = fields
    
    def get_trained_at_formatted(self, obj):
        return obj.trained_at.strftime('%Y-%m-%d %H:%M')


class DocumentPredictionSerializer(serializers.ModelSerializer):
    """
    Serializer per predizioni documenti.
    """
    documento_codice = serializers.CharField(
        source='documento.codice',
        read_only=True,
        allow_null=True
    )
    ml_model_version = serializers.CharField(
        source='ml_model.version',
        read_only=True
    )
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentPrediction
        fields = [
            'id',
            'documento',
            'documento_codice',
            'ml_model',
            'ml_model_version',
            'predicted_type',
            'predicted_cliente',
            'predicted_titolario',
            'confidence_tipo',
            'confidence_cliente',
            'confidence_titolario',
            'confidence_scores',
            'extracted_features',
            'user_confirmed',
            'user_corrected',
            'user_feedback',
            'correction_data',
            'created_at',
            'created_at_formatted',
        ]
        read_only_fields = [
            'id',
            'documento_codice',
            'ml_model_version',
            'created_at',
            'created_at_formatted',
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')


class PredictRequestSerializer(serializers.Serializer):
    """
    Serializer per richiesta predizione.
    """
    file = serializers.FileField(
        help_text="File da classificare (PDF, immagine, DOCX, XLSX, ZIP)"
    )
    documento_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID documento associato (opzionale)"
    )
    return_top_n = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=10,
        help_text="Numero top predizioni da ritornare (1-10)"
    )
    min_confidence = serializers.FloatField(
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text="Confidence minima per considerare predizione valida (0-1)"
    )
    save_prediction = serializers.BooleanField(
        default=False,
        help_text="Salva predizione nel database"
    )


class PredictResponseSerializer(serializers.Serializer):
    """
    Serializer per risposta predizione.
    """
    success = serializers.BooleanField()
    predictions = serializers.DictField(allow_null=True)
    metadata = serializers.DictField(allow_null=True)
    model_info = serializers.DictField(allow_null=True)
    error = serializers.CharField(allow_null=True, required=False)
    prediction_id = serializers.IntegerField(allow_null=True, required=False)


class FeedbackSerializer(serializers.Serializer):
    """
    Serializer per feedback utente su predizione.
    """
    confirmed = serializers.BooleanField(
        required=False,
        help_text="True se predizione confermata corretta"
    )
    corrected = serializers.BooleanField(
        required=False,
        help_text="True se predizione corretta dall'utente"
    )
    correct_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Tipo corretto (se corrected=True)"
    )
    correct_cliente = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID cliente corretto (opzionale)"
    )
    correct_titolario = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID titolario corretto (opzionale)"
    )
    feedback_text = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Commento utente (opzionale)"
    )
    add_to_training = serializers.BooleanField(
        default=True,
        help_text="Aggiungi a coda re-training"
    )


class TrainingJobSerializer(serializers.ModelSerializer):
    """
    Serializer per job di training.
    """
    new_model_version = serializers.CharField(
        source='new_model.version',
        read_only=True,
        allow_null=True
    )
    started_at_formatted = serializers.SerializerMethodField()
    completed_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TrainingJob
        fields = [
            'id',
            'status',
            'training_samples_count',
            'new_model',
            'new_model_version',
            'accuracy_improvement',
            'error_message',
            'started_at',
            'started_at_formatted',
            'completed_at',
            'completed_at_formatted',
        ]
        read_only_fields = fields
    
    def get_started_at_formatted(self, obj):
        return obj.started_at.strftime('%Y-%m-%d %H:%M:%S') if obj.started_at else None
    
    def get_completed_at_formatted(self, obj):
        return obj.completed_at.strftime('%Y-%m-%d %H:%M:%S') if obj.completed_at else None
