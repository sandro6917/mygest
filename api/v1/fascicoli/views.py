"""
Views per API Fascicoli
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from archivio_fisico.models import UnitaFisica
from .serializers import (
    FascicoloListSerializer,
    FascicoloDetailSerializer,
    FascicoloWriteSerializer,
    TitolarioVoceSerializer,
    UnitaFisicaSerializer,
)


class FascicoloViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione fascicoli
    
    list: Lista fascicoli con filtri
    retrieve: Dettaglio fascicolo
    create: Crea nuovo fascicolo
    update/partial_update: Modifica fascicolo
    destroy: Elimina fascicolo
    
    Azioni personalizzate:
    - sottofascicoli: Lista sottofascicoli di un fascicolo
    - stats: Statistiche generali sui fascicoli
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'codice', 'titolo', 'note']
    ordering_fields = ['anno', 'progressivo', 'codice', 'created_at']
    ordering = ['-anno', '-progressivo']
    filterset_fields = ['anno', 'stato', 'cliente', 'titolario_voce', 'parent', 'ubicazione']
    
    def get_queryset(self):
        qs = Fascicolo.objects.select_related(
            'cliente', 'cliente__anagrafica', 'titolario_voce', 
            'parent', 'ubicazione'
        ).prefetch_related('pratiche', 'sottofascicoli')
        
        # Filtro per fascicoli radice (parent is null)
        parent_param = self.request.query_params.get('parent')
        if parent_param == 'null':
            qs = qs.filter(parent__isnull=True)
        
        # Filtro per fascicoli con documenti con file (per allegati comunicazioni)
        con_file = self.request.query_params.get('con_file')
        if con_file == 'true':
            from documenti.models import Documento
            qs = qs.filter(
                documenti__file__isnull=False
            ).distinct()
        
        return qs
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FascicoloListSerializer
        elif self.action == 'retrieve':
            return FascicoloDetailSerializer
        else:
            return FascicoloWriteSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update per restituire fascicolo completo"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Ricarica l'istanza dal database
        instance.refresh_from_db()
        
        # Restituisci il fascicolo completo
        detail_serializer = FascicoloDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Override create per restituire fascicolo completo"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Restituisci il fascicolo completo
        detail_serializer = FascicoloDetailSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def sottofascicoli(self, request, pk=None):
        """
        Restituisce la lista dei sottofascicoli di un fascicolo
        """
        fascicolo = self.get_object()
        sottofascicoli = fascicolo.sottofascicoli.all()
        serializer = FascicoloListSerializer(sottofascicoli, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def movimenti(self, request, pk=None):
        """
        Restituisce lo storico dei movimenti protocollo di un fascicolo
        """
        from protocollo.models import MovimentoProtocollo
        
        fascicolo = self.get_object()
        movimenti = MovimentoProtocollo.objects.filter(
            fascicolo=fascicolo
        ).select_related(
            'operatore', 'ubicazione'
        ).order_by('-quando')
        
        # Serializzazione manuale dei movimenti
        data = []
        for mov in movimenti:
            movimento_data = {
                'id': mov.id,
                'fascicolo': mov.fascicolo_id,
                'tipo': mov.tipo,
                'quando': mov.quando,
                'operatore': mov.operatore_id,
                'operatore_nome': mov.operatore.get_full_name() if mov.operatore else None,
                'da_chi': mov.da_chi or '',
                'a_chi': mov.a_chi or '',
                'causale': mov.causale or '',
                'note': mov.note or '',
                'data_rientro_prevista': mov.data_rientro_prevista,
                'data_rientro_effettiva': mov.data_rientro_effettiva,
                'ubicazione': mov.ubicazione_id,
            }
            
            if mov.ubicazione:
                movimento_data['ubicazione_detail'] = {
                    'id': mov.ubicazione.id,
                    'tipo': mov.ubicazione.tipo,
                    'codice': mov.ubicazione.codice,
                    'descrizione': mov.ubicazione.descrizione,
                    'posizione': mov.ubicazione.posizione or '',
                    'full_path': mov.ubicazione.full_path or '',
                }
            
            data.append(movimento_data)
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def registra_entrata(self, request, pk=None):
        """
        Registra un movimento di entrata per il fascicolo
        """
        fascicolo = self.get_object()
        
        # Parametri dal request
        quando = request.data.get('quando')
        da_chi = request.data.get('da_chi', '')
        causale = request.data.get('causale', '')
        note = request.data.get('note', '')
        ubicazione_id = request.data.get('ubicazione')
        
        ubicazione = None
        if ubicazione_id:
            try:
                ubicazione = UnitaFisica.objects.get(id=ubicazione_id)
            except UnitaFisica.DoesNotExist:
                return Response(
                    {'error': 'Ubicazione non trovata'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Registra il movimento
        movimento = fascicolo.protocolla_entrata(
            quando=quando,
            operatore=request.user,
            da_chi=da_chi,
            ubicazione=ubicazione,
            causale=causale,
            note=note
        )
        
        return Response({
            'id': movimento.id,
            'tipo': movimento.tipo,
            'quando': movimento.quando,
            'message': 'Movimento di entrata registrato con successo'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def registra_uscita(self, request, pk=None):
        """
        Registra un movimento di uscita per il fascicolo
        """
        fascicolo = self.get_object()
        
        # Parametri dal request
        quando = request.data.get('quando')
        a_chi = request.data.get('a_chi', '')
        causale = request.data.get('causale', '')
        note = request.data.get('note', '')
        data_rientro_prevista = request.data.get('data_rientro_prevista')
        ubicazione_id = request.data.get('ubicazione')
        
        ubicazione = None
        if ubicazione_id:
            try:
                ubicazione = UnitaFisica.objects.get(id=ubicazione_id)
            except UnitaFisica.DoesNotExist:
                return Response(
                    {'error': 'Ubicazione non trovata'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Registra il movimento
        movimento = fascicolo.protocolla_uscita(
            quando=quando,
            operatore=request.user,
            a_chi=a_chi,
            data_rientro_prevista=data_rientro_prevista,
            causale=causale,
            note=note,
            ubicazione=ubicazione
        )
        
        return Response({
            'id': movimento.id,
            'tipo': movimento.tipo,
            'quando': movimento.quando,
            'message': 'Movimento di uscita registrato con successo'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Restituisce statistiche generali sui fascicoli
        """
        from django.db.models import Count
        
        total = Fascicolo.objects.count()
        by_stato = dict(
            Fascicolo.objects.values('stato').annotate(count=Count('id')).values_list('stato', 'count')
        )
        by_anno = dict(
            Fascicolo.objects.values('anno').annotate(count=Count('id')).order_by('-anno').values_list('anno', 'count')[:5]
        )
        
        return Response({
            'total': total,
            'by_stato': by_stato,
            'by_anno': by_anno,
        })
    
    @action(detail=True, methods=['get'])
    def fascicoli_collegabili(self, request, pk=None):
        """
        Restituisce lista fascicoli collegabili (per relazione M2M):
        - Escludi il fascicolo corrente
        - Escludi i sottofascicoli del fascicolo corrente
        - Escludi fascicoli già collegati
        """
        fascicolo = self.get_object()
        
        # Raccoglie IDs da escludere
        ids_da_escludere = {fascicolo.pk}
        
        # Escludi sottofascicoli
        sottofascicoli_ids = fascicolo.sottofascicoli.values_list('id', flat=True)
        ids_da_escludere.update(sottofascicoli_ids)
        
        # Escludi fascicoli già collegati
        collegati_ids = fascicolo.fascicoli_collegati.values_list('id', flat=True)
        ids_da_escludere.update(collegati_ids)
        
        # Query per fascicoli collegabili
        collegabili = Fascicolo.objects.exclude(
            id__in=ids_da_escludere
        ).select_related(
            'cliente', 'cliente__anagrafica', 'titolario_voce'
        ).order_by('-anno', '-progressivo')
        
        # Filtri opzionali
        search = request.query_params.get('search')
        if search:
            collegabili = collegabili.filter(
                Q(codice__icontains=search) | 
                Q(titolo__icontains=search) |
                Q(cliente__anagrafica__nome__icontains=search) |
                Q(cliente__anagrafica__cognome__icontains=search)
            )
        
        anno = request.query_params.get('anno')
        if anno:
            collegabili = collegabili.filter(anno=anno)
        
        cliente = request.query_params.get('cliente')
        if cliente:
            collegabili = collegabili.filter(cliente_id=cliente)
        
        titolario = request.query_params.get('titolario')
        if titolario:
            collegabili = collegabili.filter(titolario_voce_id=titolario)
        
        # Limita risultati
        collegabili = collegabili[:100]
        
        serializer = FascicoloListSerializer(collegabili, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sottofascicoli_collegabili(self, request, pk=None):
        """
        Restituisce lista fascicoli collegabili come sottofascicoli:
        - Stesso cliente, titolario e anno
        - parent__isnull=True (non già collegati come sottofascicoli)
        - Escludi il fascicolo corrente
        """
        fascicolo = self.get_object()
        
        collegabili = Fascicolo.objects.filter(
            cliente=fascicolo.cliente,
            titolario_voce=fascicolo.titolario_voce,
            anno=fascicolo.anno,
            parent__isnull=True
        ).exclude(pk=fascicolo.pk).select_related(
            'cliente', 'cliente__anagrafica', 'titolario_voce'
        ).order_by('-progressivo')[:20]
        
        serializer = FascicoloListSerializer(collegabili, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def collega_fascicolo(self, request, pk=None):
        """
        Collega un fascicolo a questo fascicolo (relazione M2M)
        
        Body:
        {
            "fascicolo_id": <ID del fascicolo da collegare>
        }
        """
        fascicolo = self.get_object()
        fascicolo_da_collegare_id = request.data.get('fascicolo_id')
        
        if not fascicolo_da_collegare_id:
            return Response(
                {'error': 'fascicolo_id è richiesto'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fascicolo_da_collegare = Fascicolo.objects.get(id=fascicolo_da_collegare_id)
        except Fascicolo.DoesNotExist:
            return Response(
                {'error': 'Fascicolo non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validazioni
        if fascicolo_da_collegare.id == fascicolo.id:
            return Response(
                {'error': 'Non puoi collegare un fascicolo a se stesso'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifica se è un sottofascicolo
        if fascicolo_da_collegare.parent_id == fascicolo.id:
            return Response(
                {'error': 'Questo fascicolo è già un sottofascicolo'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifica se è già collegato
        if fascicolo.fascicoli_collegati.filter(id=fascicolo_da_collegare.id).exists():
            return Response(
                {'error': 'Fascicolo già collegato'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Effettua il collegamento
        fascicolo.fascicoli_collegati.add(fascicolo_da_collegare)
        
        return Response({
            'success': True,
            'message': f'Fascicolo {fascicolo_da_collegare.codice} collegato con successo'
        })
    
    @action(detail=True, methods=['post'])
    def scollega_fascicolo(self, request, pk=None):
        """
        Scollega un fascicolo da questo fascicolo (relazione M2M)
        
        Body:
        {
            "fascicolo_id": <ID del fascicolo da scollegare>
        }
        """
        fascicolo = self.get_object()
        fascicolo_da_scollegare_id = request.data.get('fascicolo_id')
        
        if not fascicolo_da_scollegare_id:
            return Response(
                {'error': 'fascicolo_id è richiesto'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fascicolo_da_scollegare = Fascicolo.objects.get(id=fascicolo_da_scollegare_id)
        except Fascicolo.DoesNotExist:
            return Response(
                {'error': 'Fascicolo non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Effettua lo scollegamento
        fascicolo.fascicoli_collegati.remove(fascicolo_da_scollegare)
        
        return Response({
            'success': True,
            'message': f'Fascicolo {fascicolo_da_scollegare.codice} scollegato con successo'
        })


class TitolarioVoceViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione voci titolario
    
    list: Lista voci titolario con filtri
    retrieve: Dettaglio voce
    create: Crea nuova voce (anche intestata ad anagrafica)
    update/partial_update: Modifica voce
    destroy: Elimina voce
    
    Azioni personalizzate:
    - voci_radice: Lista voci di primo livello (parent=null)
    - figli: Lista figli di una voce
    - anagrafiche_disponibili: Anagrafiche che possono essere intestate
    - crea_voce_intestata: Helper per creare voce intestata ad anagrafica
    """
    queryset = TitolarioVoce.objects.select_related('parent', 'anagrafica').all()
    serializer_class = TitolarioVoceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disabilita paginazione per autocomplete
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'consente_intestazione', 'anagrafica']
    search_fields = ['id', 'codice', 'titolo', 'anagrafica__nome', 'anagrafica__cognome']
    ordering_fields = ['codice', 'titolo']
    ordering = ['codice']
    
    @action(detail=False, methods=['get'])
    def voci_radice(self, request):
        """Ritorna solo voci di primo livello (parent=null)"""
        voci = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(voci, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def figli(self, request, pk=None):
        """Ritorna i figli diretti di una voce"""
        voce = self.get_object()
        figli = voce.figli.select_related('anagrafica').all()
        serializer = self.get_serializer(figli, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def anagrafiche_disponibili(self, request, pk=None):
        """
        Ritorna anagrafiche che possono essere intestate a questa voce.
        Funziona solo se la voce ha consente_intestazione=True.
        """
        voce = self.get_object()
        
        if not voce.consente_intestazione:
            return Response(
                {'error': 'Questa voce non consente intestazione ad anagrafiche'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        anagrafiche_qs = voce.get_anagrafiche_disponibili()
        
        if anagrafiche_qs is None:
            return Response({'results': []})
        
        # Serializza anagrafiche
        from anagrafiche.models import Anagrafica
        data = []
        for ana in anagrafiche_qs[:100]:  # Limita a 100 risultati
            data.append({
                'id': ana.id,
                'codice': ana.codice,
                'nome': ana.nome,
                'tipo': ana.tipo,
            })
        
        return Response({'results': data})
    
    @action(detail=True, methods=['post'])
    def crea_voce_intestata(self, request, pk=None):
        """
        Helper per creare una voce intestata ad un'anagrafica sotto questa voce.
        
        Body:
        {
            "anagrafica_id": <ID>,
            "titolo": "<Titolo opzionale, default: nome anagrafica>",
            "pattern_codice": "<Pattern opzionale>"
        }
        """
        parent_voce = self.get_object()
        
        # Verifica che parent consenta intestazione
        if not parent_voce.consente_intestazione:
            return Response(
                {'error': 'Questa voce non consente intestazione ad anagrafiche'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        anagrafica_id = request.data.get('anagrafica_id')
        if not anagrafica_id:
            return Response(
                {'error': 'anagrafica_id è richiesto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifica anagrafica esiste
        from anagrafiche.models import Anagrafica
        try:
            anagrafica = Anagrafica.objects.get(id=anagrafica_id)
        except Anagrafica.DoesNotExist:
            return Response(
                {'error': 'Anagrafica non trovata'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verifica che non esista già voce intestata a questa anagrafica sotto questo parent
        if TitolarioVoce.objects.filter(parent=parent_voce, anagrafica=anagrafica).exists():
            return Response(
                {'error': f'Esiste già una voce intestata a {anagrafica.nome} sotto {parent_voce}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crea voce intestata
        titolo = request.data.get('titolo', anagrafica.nome)
        codice = anagrafica.codice
        pattern_codice = request.data.get('pattern_codice', '{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}')
        
        nuova_voce = TitolarioVoce.objects.create(
            codice=codice,
            titolo=titolo,
            parent=parent_voce,
            anagrafica=anagrafica,
            pattern_codice=pattern_codice,
            consente_intestazione=False  # Le voci intestate non consentono a loro volta intestazione
        )
        
        serializer = self.get_serializer(nuova_voce)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def crea_voci_bulk(self, request, pk=None):
        """
        Crea voci intestate in modalità bulk per più anagrafiche.
        
        Body:
        {
            "anagrafica_ids": [<ID1>, <ID2>, ...],  // Opzionale: lista IDs specifici
            "tutte_disponibili": true,               // Opzionale: crea per tutte le disponibili
            "crea_sottovoci": true,                  // Opzionale: crea anche sotto-voci standard
            "pattern_codice": "<pattern>",           // Opzionale
            "dry_run": false                         // Opzionale: simula senza salvare
        }
        
        Response:
        {
            "voci_create": 10,
            "sottovoci_create": 40,
            "gia_esistenti": 2,
            "errori": [],
            "voci": [...]  // Lista voci create (se non dry_run)
        }
        """
        from django.db import transaction
        from anagrafiche.models import Anagrafica
        
        parent_voce = self.get_object()
        
        # Verifica che parent consenta intestazione
        if not parent_voce.consente_intestazione:
            return Response(
                {'error': 'Questa voce non consente intestazione ad anagrafiche'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parametri
        anagrafica_ids = request.data.get('anagrafica_ids', [])
        tutte_disponibili = request.data.get('tutte_disponibili', False)
        crea_sottovoci = request.data.get('crea_sottovoci', False)
        pattern_codice = request.data.get('pattern_codice', '{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}')
        dry_run = request.data.get('dry_run', False)
        
        # Determina anagrafiche da processare
        if tutte_disponibili:
            anagrafiche = parent_voce.get_anagrafiche_disponibili()
            if anagrafiche is None:
                anagrafiche = Anagrafica.objects.none()
        elif anagrafica_ids:
            anagrafiche = Anagrafica.objects.filter(id__in=anagrafica_ids)
        else:
            return Response(
                {'error': 'Specificare anagrafica_ids o tutte_disponibili=true'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtra solo anagrafiche con codice valido
        anagrafiche = anagrafiche.exclude(codice__isnull=True).exclude(codice='')
        
        if not anagrafiche.exists():
            return Response({
                'voci_create': 0,
                'sottovoci_create': 0,
                'gia_esistenti': 0,
                'errori': [],
                'message': 'Nessuna anagrafica disponibile'
            })
        
        # Template sotto-voci standard
        SOTTO_VOCI_TEMPLATE = [
            ('BP', 'Buste Paga', '{CLI}-{ANA}-BP-{ANNO}-{SEQ:03d}'),
            ('CONTR', 'Contratti', '{CLI}-{ANA}-CONTR-{ANNO}-{SEQ:03d}'),
            ('CU', 'Certificazione Unica', '{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}'),
            ('DOC', 'Documenti Vari', '{CLI}-{ANA}-DOC-{ANNO}-{SEQ:03d}'),
        ]
        
        # Contatori
        totale_create = 0
        totale_gia_esistenti = 0
        totale_sottovoci = 0
        errori = []
        voci_create_data = []
        
        with transaction.atomic():
            for anagrafica in anagrafiche:
                # Verifica se esiste già
                if TitolarioVoce.objects.filter(parent=parent_voce, anagrafica=anagrafica).exists():
                    totale_gia_esistenti += 1
                    continue
                
                try:
                    # Crea voce intestata
                    if not dry_run:
                        nuova_voce = TitolarioVoce.objects.create(
                            codice=anagrafica.codice,
                            titolo=f"Dossier {anagrafica.display_name()}",
                            parent=parent_voce,
                            anagrafica=anagrafica,
                            pattern_codice=pattern_codice,
                            consente_intestazione=False
                        )
                        
                        voci_create_data.append({
                            'id': nuova_voce.id,
                            'codice': nuova_voce.codice,
                            'titolo': nuova_voce.titolo,
                            'anagrafica_id': anagrafica.id,
                            'anagrafica_nome': anagrafica.display_name(),
                        })
                    else:
                        nuova_voce = None
                        voci_create_data.append({
                            'codice': anagrafica.codice,
                            'titolo': f"Dossier {anagrafica.display_name()}",
                            'anagrafica_nome': anagrafica.display_name(),
                            'dry_run': True
                        })
                    
                    totale_create += 1
                    
                    # Crea sotto-voci se richiesto
                    if crea_sottovoci and not dry_run and nuova_voce:
                        for sv_codice, sv_titolo, sv_pattern in SOTTO_VOCI_TEMPLATE:
                            try:
                                TitolarioVoce.objects.create(
                                    codice=sv_codice,
                                    titolo=sv_titolo,
                                    parent=nuova_voce,
                                    pattern_codice=sv_pattern,
                                    consente_intestazione=False
                                )
                                totale_sottovoci += 1
                            except Exception as e:
                                errori.append({
                                    'anagrafica': anagrafica.display_name(),
                                    'sottovoce': sv_titolo,
                                    'errore': str(e)
                                })
                    
                    elif crea_sottovoci and dry_run:
                        totale_sottovoci += len(SOTTO_VOCI_TEMPLATE)
                
                except Exception as e:
                    errori.append({
                        'anagrafica': anagrafica.display_name(),
                        'errore': str(e)
                    })
            
            # Se dry_run, rollback
            if dry_run:
                transaction.set_rollback(True)
        
        response_data = {
            'voci_create': totale_create,
            'sottovoci_create': totale_sottovoci,
            'gia_esistenti': totale_gia_esistenti,
            'errori': errori,
            'voci': voci_create_data if not dry_run else [],
            'dry_run': dry_run
        }
        
        if dry_run:
            response_data['message'] = 'Dry-run completato: nessuna modifica salvata'
        
        return Response(response_data, status=status.HTTP_201_CREATED if totale_create > 0 else status.HTTP_200_OK)
