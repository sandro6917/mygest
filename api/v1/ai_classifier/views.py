"""
Views per AI Classifier API
"""
import logging
import os
import tempfile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import RBACPermission
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from ai_classifier.models import MLModel, DocumentPrediction, TrainingQueue, TrainingJob
from ai_classifier.services.ml.predictor import Predictor
from .serializers import (
    MLModelSerializer,
    DocumentPredictionSerializer,
    PredictRequestSerializer,
    PredictResponseSerializer,
    FeedbackSerializer,
    TrainingJobSerializer,
)

logger = logging.getLogger(__name__)


class MLModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per visualizzazione modelli ML.
    
    Endpoints:
    - GET /api/v1/ai-classifier/models/ - Lista modelli
    - GET /api/v1/ai-classifier/models/{id}/ - Dettaglio modello
    - GET /api/v1/ai-classifier/models/active/ - Modello attivo
    """
    queryset = MLModel.objects.all().order_by('-trained_at')
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Ritorna il modello attualmente attivo.
        """
        active_model = MLModel.objects.filter(is_active=True).first()
        
        if not active_model:
            return Response(
                {'error': 'Nessun modello attivo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(active_model)
        return Response(serializer.data)


class DocumentPredictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione predizioni documenti.
    
    Endpoints:
    - GET /api/v1/ai-classifier/predictions/ - Lista predizioni
    - GET /api/v1/ai-classifier/predictions/{id}/ - Dettaglio predizione
    - POST /api/v1/ai-classifier/predictions/{id}/feedback/ - Feedback utente
    """
    serializer_class = DocumentPredictionSerializer
    permission_classes = [RBACPermission]
    filterset_fields = ['documento', 'ml_model', 'predicted_type', 'user_confirmed', 'user_corrected']
    search_fields = ['predicted_type', 'documento__codice']
    ordering_fields = ['created_at', 'confidence_tipo']
    
    def get_queryset(self):
        qs = DocumentPrediction.objects.all().order_by('-created_at')
        
        # RBAC: filtra per clienti accessibili via documento
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            if not profile.can_view_all:
                accessible_clients_ids = profile.get_accessible_clients_ids()
                if accessible_clients_ids is not None:
                    qs = qs.filter(documento__cliente_id__in=accessible_clients_ids)
        
        return qs
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """
        Registra feedback utente su predizione.
        
        Body:
        {
            "confirmed": true/false,
            "corrected": true/false,
            "correct_type": "TIPO",
            "feedback_text": "...",
            "add_to_training": true
        }
        """
        prediction = self.get_object()
        serializer = FeedbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Usa il metodo del modello per submit feedback
            prediction.submit_feedback(
                confirmed=data.get('confirmed', False),
                corrected=data.get('corrected', False),
                correct_type=data.get('correct_type'),
                correct_cliente_id=data.get('correct_cliente'),
                correct_titolario_id=data.get('correct_titolario'),
                feedback_text=data.get('feedback_text'),
                add_to_training=data.get('add_to_training', True),
            )
            
            return Response({
                'success': True,
                'message': 'Feedback registrato con successo',
                'prediction_id': prediction.id,
            })
        
        except Exception as e:
            logger.error(f"Errore registrazione feedback: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PredictViewSet(viewsets.ViewSet):
    """
    ViewSet per predizioni ML su file uploadati.
    
    Endpoints:
    - POST /api/v1/ai-classifier/predict/ - Predici tipo documento da file
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request):
        """
        Predice tipo documento da file uploadato.
        
        Multipart form-data:
        - file: File da classificare
        - documento_id: (opzionale) ID documento associato
        - return_top_n: (default 3) Numero top predizioni
        - min_confidence: (default 0.0) Confidence minima
        - save_prediction: (default false) Salva in DB
        
        Returns:
        {
            "success": true,
            "predictions": {
                "tipo": {
                    "top_prediction": "F24",
                    "confidence": 0.99,
                    "all_predictions": [["F24", 0.99], ...]
                }
            },
            "metadata": {...},
            "model_info": {...},
            "prediction_id": 123  // se save_prediction=true
        }
        """
        # Valida input
        input_serializer = PredictRequestSerializer(data=request.data)
        
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = input_serializer.validated_data
        uploaded_file = data['file']
        documento_id = data.get('documento_id')
        return_top_n = data.get('return_top_n', 3)
        min_confidence = data.get('min_confidence', 0.0)
        save_prediction = data.get('save_prediction', False)
        
        # Salva file temporaneo
        temp_path = None
        
        try:
            # Crea file temporaneo
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                temp_path = tmp_file.name
            
            logger.info(f"📁 File uploadato: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Inizializza predictor
            predictor = Predictor()
            
            if not predictor.ml_model:
                return Response(
                    {'error': 'Nessun modello ML attivo disponibile'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Fa predizione
            if save_prediction and documento_id:
                result, prediction_obj = predictor.predict_and_save(
                    file_path=temp_path,
                    documento_id=documento_id,
                    filename=uploaded_file.name,
                )
                
                if prediction_obj:
                    result['prediction_id'] = prediction_obj.id
            else:
                result = predictor.predict(
                    file_path=temp_path,
                    filename=uploaded_file.name,
                    return_top_n=return_top_n,
                    min_confidence=min_confidence,
                )
            
            # Serializza risposta
            response_serializer = PredictResponseSerializer(data=result)
            
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                # Ritorna comunque il risultato anche se serializer fallisce
                return Response(result)
        
        except Exception as e:
            logger.error(f"❌ Errore predizione: {e}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'predictions': None,
                    'metadata': None,
                    'model_info': None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        finally:
            # Pulisci file temporaneo
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"⚠️ Errore pulizia temp file: {e}")


class TrainingJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per visualizzazione job di training.
    
    Endpoints:
    - GET /api/v1/ai-classifier/training-jobs/ - Lista job
    - GET /api/v1/ai-classifier/training-jobs/{id}/ - Dettaglio job
    - GET /api/v1/ai-classifier/training-jobs/latest/ - Ultimo job
    """
    queryset = TrainingJob.objects.all().order_by('-started_at')
    serializer_class = TrainingJobSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Ritorna l'ultimo job di training.
        """
        latest_job = TrainingJob.objects.order_by('-started_at').first()
        
        if not latest_job:
            return Response(
                {'error': 'Nessun job di training trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(latest_job)
        return Response(serializer.data)
