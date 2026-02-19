"""
Views per API Agent Desktop.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from pathlib import Path

from documenti.models_deletion import FileDeletionRequest
from .serializers import (
    FileDeletionRequestSerializer,
    PendingDeletionSerializer,
    ConfirmDeletionSerializer
)


# ⚠️ PERCORSI PROTETTI - NON VERRANNO MAI ELIMINATI
PROTECTED_PATHS = [
    '/mnt/archivio',           # Archivio documenti MyGest
    '/home/sandro/mygest',     # Progetto MyGest
    '/var/www',                # Web server
    '/opt',                    # Software installato
    '/usr',                    # Sistema
    '/etc',                    # Configurazioni
    '/bin',                    # Eseguibili sistema
    '/sbin',                   # Eseguibili amministrazione
]


def is_protected_path(file_path: str) -> bool:
    """
    Verifica se il path è protetto.
    
    Args:
        file_path: Percorso da verificare
        
    Returns:
        True se il path è protetto
    """
    try:
        path = Path(file_path).resolve()
        path_str = str(path)
        
        for protected in PROTECTED_PATHS:
            if path_str.startswith(protected):
                return True
        return False
    except Exception:
        # In caso di errore, proteggi per sicurezza
        return True


class AgentViewSet(viewsets.ViewSet):
    """
    ViewSet per la gestione delle operazioni dell'agent desktop.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def ping(self, request):
        """
        Endpoint per verificare la connessione dell'agent.
        
        GET /api/v1/agent/ping/
        """
        return Response({
            'status': 'ok',
            'message': 'Agent connesso',
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username
        })
    
    @action(detail=False, methods=['get'], url_path='pending-deletions')
    def pending_deletions(self, request):
        """
        Restituisce la lista delle richieste di eliminazione pendenti.
        
        GET /api/v1/agent/pending-deletions/
        """
        deletions = FileDeletionRequest.objects.filter(
            status=FileDeletionRequest.Status.PENDING
        ).select_related('documento').order_by('created_at')
        
        serializer = PendingDeletionSerializer(deletions, many=True)
        
        return Response({
            'count': deletions.count(),
            'deletions': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='confirm-deletion')
    def confirm_deletion(self, request):
        """
        Conferma l'esito di un'eliminazione.
        
        POST /api/v1/agent/confirm-deletion/
        Body: {
            "deletion_id": 123,
            "success": true,
            "error_message": "..." (opzionale)
        }
        """
        serializer = ConfirmDeletionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deletion_id = serializer.validated_data['deletion_id']
        success = serializer.validated_data['success']
        error_message = serializer.validated_data.get('error_message', '')
        
        try:
            deletion = FileDeletionRequest.objects.get(id=deletion_id)
            
            if success:
                deletion.mark_completed()
                message = f"File eliminato con successo: {deletion.source_path}"
            else:
                deletion.mark_failed(error_message)
                message = f"Eliminazione fallita: {error_message}"
            
            return Response({
                'status': 'ok',
                'message': message,
                'deletion_id': deletion_id,
                'new_status': deletion.status
            })
            
        except FileDeletionRequest.DoesNotExist:
            return Response(
                {'error': f'Richiesta {deletion_id} non trovata'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='request-deletion')
    def request_deletion(self, request):
        """
        Crea una nuova richiesta di eliminazione.
        
        POST /api/v1/agent/request-deletion/
        Body: {
            "documento": 123,
            "source_path": "/path/to/file.pdf",
            "file_size": 1024 (opzionale)
        }
        """
        # ⚠️ VERIFICA PATH PROTETTO
        source_path = request.data.get('source_path', '')
        if is_protected_path(source_path):
            return Response(
                {
                    'error': 'Path protetto',
                    'message': f'Il percorso {source_path} è protetto e non può essere eliminato',
                    'protected_paths': PROTECTED_PATHS
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = FileDeletionRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deletion = serializer.save(requested_by=request.user)
        
        return Response(
            FileDeletionRequestSerializer(deletion).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_status(request):
    """
    Restituisce lo stato generale delle richieste di eliminazione.
    
    GET /api/v1/agent/status/
    """
    stats = {
        'pending': FileDeletionRequest.objects.filter(
            status=FileDeletionRequest.Status.PENDING
        ).count(),
        'completed': FileDeletionRequest.objects.filter(
            status=FileDeletionRequest.Status.COMPLETED
        ).count(),
        'failed': FileDeletionRequest.objects.filter(
            status=FileDeletionRequest.Status.FAILED
        ).count(),
        'total': FileDeletionRequest.objects.count()
    }
    
    # Ultime richieste
    recent = FileDeletionRequest.objects.select_related(
        'documento'
    ).order_by('-created_at')[:10]
    
    recent_serializer = FileDeletionRequestSerializer(recent, many=True)
    
    return Response({
        'stats': stats,
        'recent': recent_serializer.data
    })
