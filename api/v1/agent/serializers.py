"""
Serializers per API Agent Desktop.
"""

from rest_framework import serializers
from documenti.models_deletion import FileDeletionRequest


class FileDeletionRequestSerializer(serializers.ModelSerializer):
    """Serializer per richieste di eliminazione file."""
    
    documento_codice = serializers.CharField(source='documento.codice', read_only=True)
    
    class Meta:
        model = FileDeletionRequest
        fields = [
            'id',
            'documento',
            'documento_codice',
            'source_path',
            'status',
            'created_at',
            'processed_at',
            'error_message',
            'file_size'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at', 'status']


class PendingDeletionSerializer(serializers.ModelSerializer):
    """Serializer ottimizzato per lista eliminazioni pendenti."""
    
    documento_id = serializers.IntegerField(source='documento.id', read_only=True)
    documento_codice = serializers.CharField(source='documento.codice', read_only=True)
    
    class Meta:
        model = FileDeletionRequest
        fields = [
            'id',
            'documento_id',
            'documento_codice',
            'source_path',
            'created_at',
            'file_size'
        ]


class ConfirmDeletionSerializer(serializers.Serializer):
    """Serializer per conferma eliminazione da parte dell'agent."""
    
    deletion_id = serializers.IntegerField(required=True)
    success = serializers.BooleanField(required=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)
