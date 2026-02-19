"""
Views per API Pratiche
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from pratiche.models import Pratica, PraticheTipo, PraticaNota
from .serializers import (
    PraticaListSerializer,
    PraticaDetailSerializer,
    PraticaCreateUpdateSerializer,
    PraticheTipoSerializer,
    PraticaNotaSerializer,
)


class PraticaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione pratiche
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'codice', 'oggetto', 'note', 'tag']
    ordering_fields = ['data_apertura', 'data_chiusura', 'codice', 'oggetto']
    ordering = ['-data_apertura']
    filterset_fields = ['tipo', 'cliente', 'stato', 'responsabile', 'periodo_riferimento']
    
    def get_queryset(self):
        qs = Pratica.objects.select_related(
            'tipo', 'cliente', 'cliente__anagrafica', 'responsabile'
        ).prefetch_related('note_collegate')
        
        # Filtri personalizzati
        data_da = self.request.query_params.get('data_apertura_da')
        data_a = self.request.query_params.get('data_apertura_a')
        
        if data_da:
            qs = qs.filter(data_apertura__gte=data_da)
        if data_a:
            qs = qs.filter(data_apertura__lte=data_a)
        
        return qs
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PraticaListSerializer
        elif self.action == 'retrieve':
            return PraticaDetailSerializer
        else:
            return PraticaCreateUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update per restituire pratica completa"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Ricarica l'istanza dal database
        instance.refresh_from_db()
        
        # Restituisci la pratica completa usando PraticaDetailSerializer
        detail_serializer = PraticaDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Override create per restituire pratica completa"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Restituisci la pratica completa usando PraticaDetailSerializer
        detail_serializer = PraticaDetailSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Ricerca pratiche per codice/oggetto"""
        q = request.query_params.get('q', '')
        
        if not q:
            return Response([])
        
        pratiche = self.get_queryset().filter(
            Q(codice__icontains=q) | Q(oggetto__icontains=q)
        )[:20]
        
        serializer = PraticaListSerializer(pratiche, many=True, context={'request': request})
        return Response(serializer.data)


class PraticheTipoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per tipi pratica (sola lettura)
    """
    permission_classes = [IsAuthenticated]
    queryset = PraticheTipo.objects.all().order_by('codice')
    serializer_class = PraticheTipoSerializer
    pagination_class = None  # Disabilita paginazione


class PraticaNotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per note pratiche
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PraticaNotaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['pratica', 'tipo', 'stato']
    ordering_fields = ['data', 'id']
    ordering = ['-data', '-id']
    
    def get_queryset(self):
        qs = PraticaNota.objects.select_related('pratica')
        
        # Filtro per pratica specifica
        pratica_id = self.request.query_params.get('pratica')
        if pratica_id:
            qs = qs.filter(pratica_id=pratica_id)
        
        return qs
    
    def perform_create(self, serializer):
        """Assegna automaticamente la pratica dalla URL"""
        pratica_id = self.request.data.get('pratica')
        if pratica_id:
            serializer.save(pratica_id=pratica_id)
        else:
            serializer.save()
