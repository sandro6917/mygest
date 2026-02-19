"""
ViewSets per API AI Classifier
"""
import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import ClassificationJob, ClassificationResult, ClassifierConfig
from .serializers import (
    ClassificationJobSerializer,
    ClassificationJobCreateSerializer,
    ClassificationResultSerializer,
    ClassificationResultUpdateSerializer,
    ClassifierConfigSerializer,
    ImportDocumentsSerializer,
)
from .services.scanner import DirectoryScanner
from .services.classifier import HybridClassifier

logger = logging.getLogger(__name__)


class ClassificationJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione Classification Jobs.
    
    Endpoints:
    - GET /jobs/ - Lista jobs
    - POST /jobs/ - Crea nuovo job
    - GET /jobs/{id}/ - Dettaglio job
    - POST /jobs/{id}/start/ - Avvia job (scansione + classificazione)
    - DELETE /jobs/{id}/ - Elimina job
    """
    queryset = ClassificationJob.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'created_by']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClassificationJobCreateSerializer
        return ClassificationJobSerializer
    
    def get_queryset(self):
        """Filtra jobs per user corrente (o tutti se staff)"""
        user = self.request.user
        if user.is_staff:
            return ClassificationJob.objects.all()
        return ClassificationJob.objects.filter(created_by=user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Ritorna statistiche aggregate sui jobs.
        Endpoint: GET /api/v1/ai-classifier/jobs/stats/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_jobs': queryset.count(),
            'completed_jobs': queryset.filter(status='completed').count(),
            'failed_jobs': queryset.filter(status='failed').count(),
            'running_jobs': queryset.filter(status='running').count(),
            'pending_jobs': queryset.filter(status='pending').count(),
            'total_files_processed': sum(queryset.values_list('processed_files', flat=True)),
            'total_successful_files': sum(queryset.values_list('successful_files', flat=True)),
            'total_failed_files': sum(queryset.values_list('failed_files', flat=True)),
            'total_imported_documents': ClassificationResult.objects.filter(
                job__in=queryset,
                imported=True
            ).count(),
        }
        
        # Calcola success rate
        if stats['total_files_processed'] > 0:
            stats['success_rate'] = round(
                (stats['total_successful_files'] / stats['total_files_processed']) * 100,
                2
            )
        else:
            stats['success_rate'] = 0.0
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Avvia un job di scansione e classificazione.
        Processo sincrono (può essere lungo per directory grandi).
        """
        job = self.get_object()
        
        # Verifica stato
        if job.status != 'pending':
            return Response(
                {'error': 'Job può essere avviato solo se in stato pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Segna job come running
            job.start()
            
            # Step 1: Scansione directory
            logger.info(f"Avvio scansione directory: {job.directory_path}")
            
            # Ottieni configurazione
            config = ClassifierConfig.get_config()
            
            scanner = DirectoryScanner(
                directory_path=job.directory_path,
                allowed_extensions=config.allowed_extensions,
                max_file_size_mb=config.max_file_size_mb,
                recursive=True
            )
            
            files = scanner.scan()
            job.total_files = len(files)
            job.save(update_fields=['total_files'])
            
            logger.info(f"Trovati {len(files)} file da classificare")
            
            # Step 2: Classificazione
            classifier = HybridClassifier(
                filename_patterns=config.filename_patterns,
                content_patterns=config.content_patterns,
                use_llm=job.use_llm,
                llm_api_key=config.openai_api_key or None,
                llm_model=config.llm_model,
                confidence_threshold=config.confidence_threshold
            )
            
            # Processa file uno alla volta
            for file_info in files:
                try:
                    # Classifica file
                    classification = classifier.classify_file(
                        file_path=file_info['file_path'],
                        file_name=file_info['file_name'],
                        mime_type=file_info['mime_type']
                    )
                    
                    # Crea ClassificationResult
                    result = ClassificationResult.objects.create(
                        job=job,
                        file_path=file_info['file_path'],
                        file_name=file_info['file_name'],
                        file_size=file_info['file_size'],
                        mime_type=file_info['mime_type'],
                        predicted_type=classification['predicted_type'],
                        confidence_score=classification['confidence_score'],
                        confidence_level=classification['confidence_level'],
                        classification_method=classification['classification_method'],
                        extracted_text=classification.get('extracted_text', ''),
                        extracted_metadata=classification.get('extracted_metadata', {}),
                    )
                    
                    job.processed_files += 1
                    job.successful_files += 1
                    job.save(update_fields=['processed_files', 'successful_files'])
                    
                    logger.debug(f"Classificato: {file_info['file_name']} → {classification['predicted_type']}")
                
                except Exception as e:
                    logger.error(f"Errore classificazione {file_info['file_name']}: {e}")
                    job.processed_files += 1
                    job.failed_files += 1
                    job.errors.append({
                        'file': file_info['file_name'],
                        'error': str(e),
                        'timestamp': timezone.now().isoformat()
                    })
                    job.save(update_fields=['processed_files', 'failed_files', 'errors'])
            
            # Step 3: Completa job
            job.complete()
            logger.info(f"Job {job.id} completato: {job.successful_files} success, {job.failed_files} failed")
            
            serializer = self.get_serializer(job)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Errore job {job.id}: {e}", exc_info=True)
            job.fail(str(e))
            return Response(
                {'error': f'Errore durante elaborazione: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClassificationResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione Classification Results.
    
    Endpoints:
    - GET /results/ - Lista risultati (filtrabili per job)
    - GET /results/{id}/ - Dettaglio risultato
    - PATCH /results/{id}/ - Aggiorna classificazione manuale
    - DELETE /results/{id}/ - Elimina risultato
    """
    queryset = ClassificationResult.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job', 'predicted_type', 'confidence_level', 'imported', 'suggested_cliente']
    search_fields = ['file_name', 'file_path', 'notes']
    ordering_fields = ['created_at', 'file_name', 'confidence_score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ClassificationResultUpdateSerializer
        return ClassificationResultSerializer
    
    def get_queryset(self):
        """Filtra results per jobs del user (o tutti se staff)"""
        user = self.request.user
        if user.is_staff:
            return ClassificationResult.objects.select_related(
                'job',
                'suggested_cliente__anagrafica',
                'suggested_fascicolo',
                'suggested_titolario',
                'documento'
            )
        return ClassificationResult.objects.filter(job__created_by=user).select_related(
            'job',
            'suggested_cliente__anagrafica',
            'suggested_fascicolo',
            'suggested_titolario',
            'documento'
        )


class ClassifierConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione Classifier Config (singleton).
    
    Endpoints:
    - GET /config/ - Leggi configurazione
    - PUT /config/{id}/ - Aggiorna configurazione
    """
    queryset = ClassifierConfig.objects.all()
    serializer_class = ClassifierConfigSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']  # No create/delete (singleton)
    
    def get_queryset(self):
        """Ritorna sempre il singleton"""
        config = ClassifierConfig.get_config()
        return ClassifierConfig.objects.filter(pk=config.pk)


class ImportViewSet(viewsets.GenericViewSet):
    """
    ViewSet per importazione batch di risultati classificati in app documenti.
    
    Endpoints:
    - POST /import/documents/ - Importa batch di ClassificationResult come Documenti
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def documents(self, request):
        """
        Importa batch di ClassificationResult come Documenti nell'app documenti.
        
        Body:
        {
            "result_ids": [1, 2, 3],
            "copy_files": true,
            "delete_source": false
        }
        """
        serializer = ImportDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result_ids = serializer.validated_data['result_ids']
        copy_files = serializer.validated_data['copy_files']
        delete_source = serializer.validated_data['delete_source']
        
        # Import logic (da implementare in prossimo step)
        # Per ora, ritorna placeholder
        from .services.importer import DocumentImporter
        
        try:
            importer = DocumentImporter(
                copy_files=copy_files,
                delete_source=delete_source
            )
            
            imported_docs = importer.import_results(result_ids, request.user)
            
            return Response({
                'success': True,
                'imported_count': len(imported_docs),
                'documents': [{'id': doc.id, 'codice': doc.codice} for doc in imported_docs]
            })
        
        except Exception as e:
            logger.error(f"Errore import documenti: {e}", exc_info=True)
            return Response(
                {'error': f'Errore import: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
