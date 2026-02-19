"""
Views per API Protocollo
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from protocollo.models import MovimentoProtocollo, ProtocolloCounter
from documenti.models import Documento
from fascicoli.models import Fascicolo
from archivio_fisico.models import UnitaFisica
from .serializers import (
    MovimentoProtocolloListSerializer,
    MovimentoProtocolloDetailSerializer,
    ProtocolloCounterSerializer,
    ProtocollazioneInputSerializer
)


class MovimentoProtocolloViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per gestione movimenti protocollo
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovimentoProtocolloDetailSerializer
        return MovimentoProtocolloListSerializer
    
    def get_queryset(self):
        queryset = MovimentoProtocollo.objects.select_related(
            'documento', 'fascicolo', 'cliente', 'operatore', 'ubicazione', 'destinatario_anagrafica'
        ).all()
        
        # Filtri
        documento_id = self.request.query_params.get('documento')
        fascicolo_id = self.request.query_params.get('fascicolo')
        direzione = self.request.query_params.get('direzione')
        anno = self.request.query_params.get('anno')
        cliente_id = self.request.query_params.get('cliente')
        chiuso = self.request.query_params.get('chiuso')
        
        if documento_id:
            queryset = queryset.filter(documento_id=documento_id)
        if fascicolo_id:
            queryset = queryset.filter(fascicolo_id=fascicolo_id)
        if direzione:
            queryset = queryset.filter(direzione=direzione)
        if anno:
            queryset = queryset.filter(anno=anno)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if chiuso is not None:
            queryset = queryset.filter(chiuso=chiuso.lower() == 'true')
        
        return queryset.order_by('-data')

    def _resolve_ubicazione(self, data):
        if data.get('ubicazione_id'):
            return UnitaFisica.objects.get(pk=data['ubicazione_id'])
        return None

    def _protocolla(self, *, data, request_user, documento=None, fascicolo=None, target=None, ubicazione=None):
        direzione = data['direzione']
        quando = data.get('quando') or timezone.now()
        destinatario_anagrafica = (
            data.get('a_chi_anagrafica') if direzione == 'OUT' else data.get('da_chi_anagrafica')
        )
        if direzione == 'OUT':
            movimento = MovimentoProtocollo.registra_uscita(
                target=target,
                documento=documento,
                fascicolo=fascicolo,
                quando=quando,
                operatore=request_user,
                a_chi=data.get('a_chi', ''),
                destinatario_anagrafica=destinatario_anagrafica,
                data_rientro_prevista=data.get('data_rientro_prevista'),
                causale=data.get('causale', ''),
                note=data.get('note', ''),
                ubicazione=ubicazione
            )
        else:
            movimento = MovimentoProtocollo.registra_entrata(
                target=target,
                documento=documento,
                fascicolo=fascicolo,
                quando=quando,
                operatore=request_user,
                da_chi=data.get('da_chi', ''),
                destinatario_anagrafica=destinatario_anagrafica,
                ubicazione=ubicazione,
                causale=data.get('causale', ''),
                note=data.get('note', '')
            )
        return direzione, movimento

    def _get_generic_target(self, target_type: str, target_id: str):
        if not target_type or not target_id:
            raise ValueError('target_type e target_id sono obbligatori')
        if '.' not in target_type:
            raise ValueError('target_type deve avere formato app_label.ModelName')
        app_label, model_name = target_type.split('.', 1)
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
        except ContentType.DoesNotExist:
            raise ValueError('target_type non valido')
        model_class = content_type.model_class()
        if model_class is None:
            raise ValueError('target_type non valido')
        return get_object_or_404(model_class, pk=target_id)
    
    @action(detail=False, methods=['post'], url_path='protocolla-documento/(?P<documento_id>[^/.]+)')
    def protocolla_documento(self, request, documento_id=None):
        """
        Protocolla un documento (IN o OUT)
        """
        documento = get_object_or_404(Documento, pk=documento_id)
        
        serializer = ProtocollazioneInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        ubicazione = self._resolve_ubicazione(data)
        
        try:
            direzione, movimento = self._protocolla(
                data=data,
                request_user=request.user,
                documento=documento,
                ubicazione=ubicazione
            )
            
            response_serializer = MovimentoProtocolloDetailSerializer(movimento)
            return Response({
                'success': True,
                'message': f'Documento protocollato {direzione}',
                'movimento': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='protocolla-fascicolo/(?P<fascicolo_id>[^/.]+)')
    def protocolla_fascicolo(self, request, fascicolo_id=None):
        """
        Protocolla un fascicolo (IN o OUT)
        """
        fascicolo = get_object_or_404(Fascicolo, pk=fascicolo_id)
        
        serializer = ProtocollazioneInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        ubicazione = self._resolve_ubicazione(data)
        
        try:
            direzione, movimento = self._protocolla(
                data=data,
                request_user=request.user,
                fascicolo=fascicolo,
                ubicazione=ubicazione
            )
            
            response_serializer = MovimentoProtocolloDetailSerializer(movimento)
            return Response({
                'success': True,
                'message': f'Fascicolo protocollato {direzione}',
                'movimento': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='protocolla-target')
    def protocolla_target(self, request):
        serializer = ProtocollazioneInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            target_obj = self._get_generic_target(data.get('target_type'), data.get('target_id'))
        except ValueError as exc:
            return Response({'success': False, 'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        ubicazione = self._resolve_ubicazione(data)

        try:
            direzione, movimento = self._protocolla(
                data=data,
                request_user=request.user,
                target=target_obj,
                ubicazione=ubicazione
            )
            response_serializer = MovimentoProtocolloDetailSerializer(movimento)
            return Response({
                'success': True,
                'message': f'Oggetto protocollato {direzione}',
                'movimento': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProtocolloCounterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per contatori protocollo
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProtocolloCounterSerializer
    
    def get_queryset(self):
        queryset = ProtocolloCounter.objects.select_related('cliente').all()
        
        # Filtri
        cliente_id = self.request.query_params.get('cliente')
        anno = self.request.query_params.get('anno')
        direzione = self.request.query_params.get('direzione')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if anno:
            queryset = queryset.filter(anno=anno)
        if direzione:
            queryset = queryset.filter(direzione=direzione)
        
        return queryset.order_by('-anno', 'cliente', 'direzione')
