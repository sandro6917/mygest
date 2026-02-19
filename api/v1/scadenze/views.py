"""
Views per API Scadenze
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Min, Q
from datetime import timedelta
from collections import defaultdict

from scadenze.models import Scadenza, ScadenzaAlert, ScadenzaOccorrenza
from .serializers import (
    ScadenzaAlertSerializer,
    ScadenzaListSerializer,
    ScadenzaDetailSerializer,
    ScadenzaCreateUpdateSerializer,
    ScadenzaOccorrenzaSerializer,
)
from .filters import ScadenzaFilter, ScadenzaOccorrenzaFilter, ScadenzaAlertFilter


class ScadenzaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione scadenze
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ScadenzaFilter
    search_fields = ['titolo', 'descrizione', 'categoria', 'note_interne']
    ordering_fields = ['creato_il', 'aggiornato_il', 'titolo', 'priorita', 'stato']
    ordering = ['-aggiornato_il']
    
    def get_queryset(self):
        qs = Scadenza.objects.select_related('creato_da')
        
        # Per la list view, aggiungi annotazioni invece di prefetch_related
        if self.action == 'list':
            # Annota il conteggio invece di caricare tutte le occorrenze
            qs = qs.annotate(
                num_assegnatari_count=Count('assegnatari', distinct=True),
                num_occorrenze_count=Count('occorrenze', distinct=True),
                prossima_occorrenza_data=Min(
                    'occorrenze__inizio',
                    filter=Q(
                        occorrenze__inizio__gte=timezone.now(),
                        occorrenze__stato__in=['pending', 'scheduled']
                    )
                )
            )
        else:
            # Per detail view, usa prefetch_related
            qs = qs.prefetch_related(
                'assegnatari',
                'pratiche',
                'fascicoli',
                'documenti'
            )
        
        # Filtri personalizzati
        assegnatario = self.request.query_params.get('assegnatario')
        if assegnatario:
            qs = qs.filter(assegnatari__id=assegnatario)
        
        return qs
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ScadenzaListSerializer
        elif self.action == 'retrieve':
            return ScadenzaDetailSerializer
        else:
            return ScadenzaCreateUpdateSerializer
    
    def perform_create(self, serializer):
        """Imposta l'utente corrente come creatore"""
        serializer.save(creato_da=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistiche(self, request):
        """Restituisce statistiche sulle scadenze"""
        oggi = timezone.now().date()
        sette_giorni = oggi + timedelta(days=7)
        
        # Statistiche per priorità
        priorita_stats = dict(
            Scadenza.objects.values('priorita').annotate(count=Count('id'))
            .values_list('priorita', 'count')
        )
        
        # Statistiche per stato
        stato_stats = dict(
            Scadenza.objects.values('stato').annotate(count=Count('id'))
            .values_list('stato', 'count')
        )
        
        # Andamento mensile (ultimi 12 mesi)
        andamento_mensile = {
            'labels': [],
            'scadenze': [],
            'completate': []
        }
        
        for i in range(11, -1, -1):
            data = oggi - timedelta(days=i*30)
            mese_nome = data.strftime('%b %Y')
            andamento_mensile['labels'].append(mese_nome)
            
            # Conta scadenze del mese
            occorrenze_mese = ScadenzaOccorrenza.objects.filter(
                inizio__year=data.year,
                inizio__month=data.month
            ).count()
            andamento_mensile['scadenze'].append(occorrenze_mese)
            
            # Conta completate del mese
            completate_mese = ScadenzaOccorrenza.objects.filter(
                inizio__year=data.year,
                inizio__month=data.month,
                stato='completed'
            ).count()
            andamento_mensile['completate'].append(completate_mese)
        
        # Top 5 scadenze per numero di occorrenze
        top_scadenze = []
        for scadenza in Scadenza.objects.annotate(
            num_occ=Count('occorrenze')
        ).order_by('-num_occ')[:5]:
            top_scadenze.append({
                'titolo': scadenza.titolo,
                'occorrenze': scadenza.occorrenze.count(),
                'critiche': scadenza.occorrenze.filter(
                    scadenza__priorita__in=['critical', 'high']
                ).count()
            })
        
        # Totali
        totali = {
            'totale_scadenze': Scadenza.objects.count(),
            'scadenze_attive': Scadenza.objects.filter(
                stato__in=['pending', 'in_progress']
            ).count(),
            'completate': Scadenza.objects.filter(stato='completed').count(),
            'in_scadenza': ScadenzaOccorrenza.objects.filter(
                inizio__gte=oggi,
                inizio__lte=sette_giorni,
                stato__in=['pending', 'scheduled']
            ).count()
        }
        
        return Response({
            'priorita': priorita_stats,
            'stato': stato_stats,
            'andamento_mensile': andamento_mensile,
            'top_scadenze': top_scadenze,
            'totali': totali
        })
    
    @action(detail=True, methods=['post'])
    def genera_occorrenze(self, request, pk=None):
        """Genera occorrenze per una scadenza"""
        scadenza = self.get_object()
        
        start = request.data.get('start')
        end = request.data.get('end')
        count = request.data.get('count')
        
        # Log per debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Genera occorrenze - Scadenza: {scadenza.titolo}")
        logger.info(f"Periodicità: {scadenza.periodicita} ({scadenza.get_periodicita_display()})")
        logger.info(f"Intervallo: {scadenza.periodicita_intervallo}")
        logger.info(f"Parametri ricevuti - start: {start}, end: {end}, count: {count}")
        
        if not start and not end and not count:
            return Response(
                {'error': 'Specificare almeno uno tra start, end o count'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Converti le stringhe in datetime se necessario
            if start and isinstance(start, str):
                start = timezone.datetime.fromisoformat(start.replace('Z', '+00:00'))
            if end and isinstance(end, str):
                end = timezone.datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            logger.info(f"Dopo conversione - start: {start}, end: {end}, count: {count}")
            
            occorrenze = scadenza.genera_occorrenze(
                start=start,
                end=end,
                count=int(count) if count else None,
            )
            
            logger.info(f"Occorrenze generate: {len(occorrenze)}")
            
            serializer = ScadenzaOccorrenzaSerializer(occorrenze, many=True)
            
            # Aggiungi informazioni utili nella risposta
            return Response({
                'occorrenze': serializer.data,
                'totale': len(occorrenze),
                'messaggio': f'{len(occorrenze)} occorrenze gestite (alcune potrebbero essere già esistenti)'
            })
        except Exception as e:
            import traceback
            traceback.print_exc()  # Log dell'errore completo
            logger.error(f"Errore nella generazione occorrenze: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ScadenzaOccorrenzaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione occorrenze con filtri avanzati.
    
    ## Filtri Supportati
    
    ### Filtri per Data:
    - `inizio__gte`: Data inizio maggiore o uguale (formato: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
    - `inizio__lte`: Data inizio minore o uguale
    - `inizio__lt`: Data inizio minore di (esclusivo)
    - `inizio__gt`: Data inizio maggiore di (esclusivo)
    - `fine__gte`, `fine__lte`, `fine__lt`, `fine__gt`: Analoghi per data fine
    
    ### Filtri per Stato:
    - `stato`: Singolo stato (es: `pending`, `scheduled`, `completed`, `cancelled`)
    - `stato__in`: Multipli stati separati da virgola (es: `pending,scheduled`)
    
    ### Altri Filtri:
    - `scadenza`: ID della scadenza collegata
    - `metodo_alert`: Metodo di alert (es: `email`, `webhook`)
    
    ### Ordinamento:
    - `ordering`: Campi disponibili: `inizio`, `fine`, `creato_il` (es: `ordering=inizio` o `ordering=-inizio`)
    
    ### Paginazione:
    - `page`: Numero pagina
    - `page_size`: Elementi per pagina (default: impostazione API)
    
    ## Esempi di Utilizzo
    
    ```
    # Occorrenze pending nella prossima settimana
    GET /api/v1/scadenze/occorrenze/?inizio__gte=2026-01-23&inizio__lt=2026-01-30&stato__in=pending,scheduled
    
    # Occorrenze di una specifica scadenza
    GET /api/v1/scadenze/occorrenze/?scadenza=5
    
    # Occorrenze completate ordinate per data
    GET /api/v1/scadenze/occorrenze/?stato=completed&ordering=-inizio
    ```
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScadenzaOccorrenzaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ScadenzaOccorrenzaFilter
    ordering_fields = ['inizio', 'fine', 'creato_il']
    ordering = ['inizio']
    
    def get_queryset(self):
        """
        Ottimizza le query con select_related per ridurre il numero di query al database.
        """
        return ScadenzaOccorrenza.objects.select_related('scadenza')
    
    @action(detail=False, methods=['get'])
    def calendar_events(self, request):
        """Restituisce gli eventi in formato FullCalendar"""
        from datetime import datetime
        
        # Ottieni parametri di data
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        stato = request.query_params.get('stato')
        priorita = request.query_params.get('priorita')
        
        # Filtra occorrenze
        qs = self.get_queryset()
        
        # Converti date in datetime con timezone
        if start:
            start_date = timezone.datetime.strptime(start, '%Y-%m-%d').date()
            qs = qs.filter(inizio__date__gte=start_date)
        if end:
            end_date = timezone.datetime.strptime(end, '%Y-%m-%d').date()
            qs = qs.filter(inizio__date__lte=end_date)
        if stato:
            qs = qs.filter(stato=stato)
        if priorita:
            qs = qs.filter(scadenza__priorita=priorita)
        
        # Colori per priorità
        priority_colors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'critical': '#dc2626'
        }
        
        # Costruisci eventi in formato FullCalendar
        events = []
        for occ in qs:
            color = priority_colors.get(occ.scadenza.priorita, '#6b7280')
            
            events.append({
                'id': occ.id,
                'title': occ.scadenza.titolo,
                'start': occ.inizio.isoformat(),
                'end': occ.fine.isoformat() if occ.fine else None,
                'allDay': occ.giornaliera,
                'url': f'/scadenze/{occ.scadenza.id}',
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'priorita': occ.scadenza.priorita,
                    'stato': occ.stato,
                    'descrizione': occ.scadenza.descrizione or '',
                    'num_alerts': ScadenzaAlert.objects.filter(
                        occorrenza=occ,
                        stato='pending'
                    ).count()
                }
            })
        
        return Response(events)
    
    @action(detail=True, methods=['post'])
    def completa(self, request, pk=None):
        """Marca un'occorrenza come completata"""
        occorrenza = self.get_object()
        occorrenza.stato = ScadenzaOccorrenza.Stato.COMPLETATA
        occorrenza.save()
        
        serializer = self.get_serializer(occorrenza)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def annulla(self, request, pk=None):
        """Annulla un'occorrenza"""
        occorrenza = self.get_object()
        occorrenza.stato = ScadenzaOccorrenza.Stato.ANNULLATA
        occorrenza.save()
        
        serializer = self.get_serializer(occorrenza)
        return Response(serializer.data)


class ScadenzaAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione alert individuali con filtri avanzati.
    
    Filtri supportati:
    - occorrenza: ID dell'occorrenza
    - scadenza: ID della scadenza
    - metodo__in: filtro multiplo per metodo (es: email,whatsapp)
    - attivo: boolean per alert attivi/inattivi
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScadenzaAlertSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ScadenzaAlertFilter
    ordering_fields = ['alert_programmata_il', 'creato_il']
    ordering = ['alert_programmata_il']
    
    def get_queryset(self):
        return ScadenzaAlert.objects.select_related('occorrenza__scadenza')
    
    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """Marca l'alert come inviato"""
        alert = self.get_object()
        alert.mark_sent()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_failed(self, request, pk=None):
        """Marca l'alert come fallito"""
        alert = self.get_object()
        error_message = request.data.get('error_message', '')
        alert.mark_failed(error_message=error_message)
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Restituisce tutti gli alert pendenti pronti per essere inviati"""
        now = timezone.now()
        alerts = self.get_queryset().filter(
            stato=ScadenzaAlert.Stato.PENDENTE,
            alert_programmata_il__lte=now
        )
        
        page = self.paginate_queryset(alerts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


# View per webhook alert interno
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from comunicazioni.models import Comunicazione
from scadenze.models import ScadenzaNotificaLog


@api_view(['POST'])
@permission_classes([AllowAny])  # Accessibile senza autenticazione per webhook
def webhook_alert_receiver(request):
    """
    Endpoint webhook interno per ricevere alert scadenze.
    
    Riceve il payload del webhook e crea una comunicazione nell'app.
    
    POST /api/v1/scadenze/webhook/alert/
    
    Payload atteso:
    {
        "id": <occorrenza_id>,
        "scadenza": <scadenza_id>,
        "titolo": "Titolo scadenza",
        "inizio": "2026-02-15T10:00:00+01:00",
        "alert": {
            "id": <alert_id>,
            "offset_alert": 2,
            "offset_alert_periodo": "hours"
        }
    }
    """
    try:
        payload = request.data
        
        # Estrai dati dal payload
        occorrenza_id = payload.get('id')
        titolo = payload.get('titolo', 'Alert Scadenza')
        inizio = payload.get('inizio')
        alert_info = payload.get('alert', {})
        
        # Recupera l'occorrenza
        try:
            occorrenza = ScadenzaOccorrenza.objects.select_related('scadenza').get(pk=occorrenza_id)
        except ScadenzaOccorrenza.DoesNotExist:
            return Response(
                {'error': 'Occorrenza non trovata'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crea il corpo della comunicazione
        corpo = f"""Alert Scadenza ricevuto via webhook

Scadenza: {titolo}
Data/Ora: {inizio}
Descrizione: {occorrenza.descrizione or occorrenza.scadenza.descrizione or 'N/A'}

Alert configurato: {alert_info.get('offset_alert', 'N/A')} {alert_info.get('offset_alert_periodo', '')} prima
"""
        
        # Crea la comunicazione
        comunicazione = Comunicazione.objects.create(
            tipo=Comunicazione.TipoComunicazione.AVVISO_SCADENZA,
            oggetto=f"🔔 Alert Webhook: {titolo}",
            corpo=corpo,
            destinatari=occorrenza.scadenza.comunicazione_destinatari or "Sistema MyGest"
        )
        
        # Collega comunicazione all'occorrenza se non già presente
        if not occorrenza.comunicazione:
            occorrenza.comunicazione = comunicazione
            occorrenza.save(update_fields=['comunicazione', 'aggiornato_il'])
        
        # Log evento
        ScadenzaNotificaLog.objects.create(
            occorrenza=occorrenza,
            evento=ScadenzaNotificaLog.Evento.ALERT_INVIATO,
            messaggio=f"Alert webhook ricevuto (interno)",
            payload=payload
        )
        
        return Response({
            'status': 'success',
            'message': 'Alert webhook ricevuto e comunicazione creata',
            'comunicazione_id': comunicazione.pk,
            'occorrenza_id': occorrenza.pk
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Log errore
        if occorrenza_id:
            try:
                occorrenza = ScadenzaOccorrenza.objects.get(pk=occorrenza_id)
                ScadenzaNotificaLog.objects.create(
                    occorrenza=occorrenza,
                    evento=ScadenzaNotificaLog.Evento.WEBHOOK_ERROR,
                    esito=False,
                    messaggio=f"Errore webhook interno: {str(e)}",
                    payload=request.data
                )
            except:
                pass
        
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
