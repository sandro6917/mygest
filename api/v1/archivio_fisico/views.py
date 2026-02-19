"""
Views API per Archivio Fisico
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone

from archivio_fisico.models import (
    OperazioneArchivio,
    RigaOperazioneArchivio,
    UnitaFisica,
    CollocazioneFisica,
    VerbaleConsegnaTemplate,
)
from archivio_fisico.services import process_operazione_archivio
from archivio_fisico.word_templates import render_verbale_consegna
from archivio_fisico.pdf import render_etichette_unita, render_etichetta_dymo
from documenti.models import Documento
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo
from stampe.services import render_lista_pdf, get_lista_for
from django.contrib.contenttypes.models import ContentType
from io import BytesIO

from .serializers import (
    OperazioneArchivioListSerializer,
    OperazioneArchivioDetailSerializer,
    OperazioneArchivioCreateSerializer,
    RigaOperazioneArchivioSerializer,
    RigaOperazioneArchivioCreateSerializer,
    UnitaFisicaSimpleSerializer,
    UnitaFisicaDetailSerializer,
    CollocazioneFisicaSerializer,
    VerbaleConsegnaTemplateSerializer,
    DocumentoSimpleSerializer,
    FascicoloSimpleSerializer,
    MovimentoProtocolloSimpleSerializer,
)


class UnitaFisicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire le unità fisiche dell'archivio
    """
    queryset = UnitaFisica.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disabilita paginazione per caricare tutte le unità
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'attivo', 'archivio_fisso', 'parent']
    search_fields = ['codice', 'nome', 'full_path']
    ordering_fields = ['codice', 'nome', 'ordine', 'created_at']
    ordering = ['parent__id', 'ordine', 'nome']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UnitaFisicaDetailSerializer
        return UnitaFisicaSimpleSerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Ritorna la struttura ad albero delle unità fisiche
        """
        def build_tree_node(unita):
            return {
                'id': unita.id,
                'codice': unita.codice,
                'nome': unita.nome,
                'tipo': unita.tipo,
                'tipo_display': unita.get_tipo_display(),
                'attivo': unita.attivo,
                'archivio_fisso': unita.archivio_fisso,
                'full_path': unita.full_path,
                'children': [build_tree_node(child) for child in unita.figli.filter(attivo=True)]
            }

        # Ottieni le radici (senza parent)
        roots = UnitaFisica.objects.filter(parent__isnull=True, attivo=True).prefetch_related('figli')
        tree = [build_tree_node(root) for root in roots]
        
        return Response(tree)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Ritorna i figli diretti di un'unità fisica
        """
        unita = self.get_object()
        children = unita.figli.all()
        serializer = UnitaFisicaSimpleSerializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """
        Ritorna gli antenati di un'unità fisica
        """
        unita = self.get_object()
        ancestors = unita.ancestors()
        serializer = UnitaFisicaSimpleSerializer(ancestors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def radici(self, request):
        """
        Ritorna solo le unità radice (senza parent)
        """
        radici = UnitaFisica.objects.filter(parent__isnull=True, attivo=True)
        serializer = UnitaFisicaSimpleSerializer(radici, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stampa_etichetta(self, request, pk=None):
        """
        Genera e ritorna un PDF con l'etichetta dell'unità fisica
        Ottimizzato per Dymo LabelWriter 450 - Completamente configurato da database
        Tutti i campi, coordinate, QR code, ecc. vengono letti da StampaModulo/StampaCampo
        """
        unita = self.get_object()
        
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        # TUTTO dal database - nessuna configurazione via query params
        return render_etichetta_dymo(unita, base_url=base_url)

    @action(detail=True, methods=['get'])
    def stampa_lista_contenuti(self, request, pk=None):
        """
        Genera e ritorna un PDF con la lista degli oggetti contenuti nell'unità fisica.
        Supporta cinque tipi di liste:
        - LST_OBJ: sottounità (UnitaFisica) - albero completo con archivio_fisso=True
        - LST_SUBUNITA_DIRETTE: sottounità dirette con archivio_fisso=True (UnitaFisica)
        - LST_FASCICOLI_UBICAZIONE: fascicoli (Fascicolo)
        - LST_DOCUMENTI_UBICAZIONE: documenti (Documento)
        - LST_CONTENITORI: contenitori mobili (UnitaFisica con archivio_fisso=False)
        """
        from django.http import Http404
        
        unita = self.get_object()
        
        try:
            # Determina quale lista stampare e il ContentType corrispondente
            lista_slug = request.GET.get("lista", "LST_OBJ")
            
            # Mappa slug -> (app_label, model_name)
            lista_models = {
                "LST_OBJ": ("archivio_fisico", "unitafisica"),
                "LST_SUBUNITA_DIRETTE": ("archivio_fisico", "unitafisica"),
                "LST_FASCICOLI_UBICAZIONE": ("fascicoli", "fascicolo"),
                "LST_DOCUMENTI_UBICAZIONE": ("documenti", "documento"),
                "LST_CONTENITORI": ("archivio_fisico", "unitafisica"),
            }
            
            if lista_slug not in lista_models:
                # Fallback: prova con UnitaFisica
                app_label, model_name = "archivio_fisico", "unitafisica"
            else:
                app_label, model_name = lista_models[lista_slug]
            
            # Ottieni il ContentType corretto
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
            
            # Cerca la StampaLista
            lista = get_lista_for(ct, lista_slug)
            
            # Parametri per il filtro: mostra contenuti di questa unità
            params = {
                "unita_id": str(pk),
            }
            params.update(request.GET.dict())
            
            # Genera il PDF
            pdf_bytes = render_lista_pdf(ct, lista, params, extra_context={"unita": unita})
            
            # Ritorna come FileResponse
            filename = f"contenuti_unita_{unita.codice}_{pk}.pdf"
            return FileResponse(
                BytesIO(pdf_bytes),
                filename=filename,
                content_type="application/pdf"
            )
        except Http404 as e:
            from rest_framework.response import Response
            return Response(
                {
                    "error": str(e),
                    "message": "Configurazione StampaLista non trovata nel database.",
                    "setup_required": {
                        "app_label": "archivio_fisico",
                        "model_name": "unitafisica",
                        "slug": lista_slug,
                    },
                    "instructions": "Creare la configurazione in Django Admin -> Stampe -> Liste di stampa"
                },
                status=404
            )

    @action(detail=True, methods=['get'])
    def stampa_copertina(self, request, pk=None):
        """
        Genera e ritorna un PDF copertina A4 per l'unità fisica.
        La copertina è configurata completamente da database (StampaModulo/StampaCampo).
        """
        from stampe.services import render_modulo_pdf, get_modulo_or_404
        
        unita = self.get_object()
        
        # Cerca il modulo di stampa per la copertina
        try:
            modulo = get_modulo_or_404(
                app_label="archivio_fisico",
                model="unitafisica",
                slug="COPERTINA_UNITA"
            )
        except Exception as e:
            from rest_framework.response import Response
            return Response(
                {
                    "error": "Configurazione copertina non trovata",
                    "message": str(e),
                    "instructions": "Eseguire lo script: python scripts/setup_copertina_unita.py"
                },
                status=404
            )
        
        # Genera il PDF usando il sistema di rendering dei moduli
        pdf_bytes = render_modulo_pdf(unita, modulo)
        
        # Ritorna come FileResponse
        filename = f"copertina_{unita.codice}_{pk}.pdf"
        return FileResponse(
            BytesIO(pdf_bytes),
            filename=filename,
            content_type="application/pdf"
        )

    @action(detail=True, methods=['get'])
    def stampa_copertina_a3(self, request, pk=None):
        """
        Genera e ritorna un PDF copertina A3 ORIZZONTALE per l'unità fisica.
        La copertina è configurata completamente da database (StampaModulo/StampaCampo).
        """
        from stampe.services import render_modulo_pdf, get_modulo_or_404
        
        unita = self.get_object()
        
        # Cerca il modulo di stampa per la copertina A3
        try:
            modulo = get_modulo_or_404(
                app_label="archivio_fisico",
                model="unitafisica",
                slug="COPERTINA_UNITA_A3"
            )
        except Exception as e:
            from rest_framework.response import Response
            return Response(
                {
                    "error": "Configurazione copertina A3 non trovata",
                    "message": str(e),
                    "instructions": "Eseguire lo script: python scripts/setup_copertina_unita_a3.py"
                },
                status=404
            )
        
        # Genera il PDF usando il sistema di rendering dei moduli
        pdf_bytes = render_modulo_pdf(unita, modulo)
        
        # Ritorna come FileResponse
        filename = f"copertina_a3_{unita.codice}_{pk}.pdf"
        return FileResponse(
            BytesIO(pdf_bytes),
            filename=filename,
            content_type="application/pdf"
        )

    @action(detail=True, methods=['get'])
    def stampa_fascicoli_documenti(self, request, pk=None):
        """
        Genera un PDF con l'elenco combinato di fascicoli e documenti
        dell'unità fisica, ordinati per tipo e poi per data.
        """
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from django.utils import timezone
        
        unita = self.get_object()
        
        # Recupera fascicoli e documenti
        fascicoli = Fascicolo.objects.filter(ubicazione_id=pk).select_related('cliente', 'titolario_voce')
        documenti = Documento.objects.filter(ubicazione_id=pk).select_related('cliente', 'fascicolo', 'titolario_voce')
        
        # Verifica se ci sono elementi da visualizzare
        if not fascicoli.exists() and not documenti.exists():
            return Response(
                {
                    "message": f"Nessun fascicolo o documento trovato per l'unità {unita.codice} - {unita.nome}",
                    "unita_id": pk,
                    "fascicoli": 0,
                    "documenti": 0,
                },
                status=200
            )
        
        # Prepara i dati combinati
        items = []
        
        for f in fascicoli:
            items.append({
                'tipo': 'Fascicolo',
                'codice': f.codice or '',
                'oggetto': f.titolo or '',
                'cliente': f.cliente.denominazione if f.cliente else '',
                'data': f.created_at.strftime('%d/%m/%Y') if f.created_at else '',
                'titolario': str(f.titolario_voce) if f.titolario_voce else '',
            })
        
        for d in documenti:
            items.append({
                'tipo': 'Documento',
                'codice': d.codice or '',
                'oggetto': d.descrizione or '',
                'cliente': d.cliente.denominazione if d.cliente else '',
                'data': d.data_documento.strftime('%d/%m/%Y') if d.data_documento else '',
                'titolario': str(d.titolario_voce) if d.titolario_voce else '',
            })
        
        # Ordina per tipo e poi per data
        items.sort(key=lambda x: (x['tipo'], x['data']))
        
        # Crea PDF
        buf = BytesIO()
        page_size = landscape(A4)
        c = canvas.Canvas(buf, pagesize=page_size)
        width, height = page_size
        
        # Margini
        ml = 10 * mm
        mr = 10 * mm
        mt = 10 * mm
        mb = 10 * mm
        
        y = height - mt
        
        # Titolo
        c.setFont("Helvetica-Bold", 14)
        c.drawString(ml, y, f"Fascicoli e Documenti - Unità: {unita.codice} - {unita.nome}")
        y -= 20
        
        # Data stampa
        c.setFont("Helvetica", 9)
        now = timezone.now()
        c.drawString(ml, y, f"Data stampa: {now.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        
        # Intestazione tabella
        c.setFont("Helvetica-Bold", 9)
        x = ml
        col_widths = [25*mm, 40*mm, 70*mm, 50*mm, 25*mm, 50*mm]
        headers = ['Tipo', 'Codice', 'Oggetto', 'Cliente', 'Data', 'Titolario']
        
        for i, header in enumerate(headers):
            c.drawString(x, y, header)
            x += col_widths[i]
        
        y -= 12
        
        # Linea separatore
        c.line(ml, y, width - mr, y)
        y -= 8
        
        # Righe dati
        c.setFont("Helvetica", 8)
        for item in items:
            if y < mb + 20:  # Nuova pagina se necessario
                c.showPage()
                y = height - mt
                c.setFont("Helvetica", 8)
            
            x = ml
            values = [
                item['tipo'],
                item['codice'][:20] if len(item['codice']) > 20 else item['codice'],
                item['oggetto'][:50] if len(item['oggetto']) > 50 else item['oggetto'],
                item['cliente'][:30] if len(item['cliente']) > 30 else item['cliente'],
                item['data'],
                item['titolario'][:30] if len(item['titolario']) > 30 else item['titolario'],
            ]
            
            for i, val in enumerate(values):
                c.drawString(x, y, val)
                x += col_widths[i]
            
            y -= 10
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(ml, mb, f"Totale: {len(items)} elementi ({sum(1 for x in items if x['tipo']=='Fascicolo')} fascicoli, {sum(1 for x in items if x['tipo']=='Documento')} documenti)")
        
        c.showPage()
        c.save()
        
        # Ottieni il contenuto del buffer
        pdf_bytes = buf.getvalue()
        
        # Ritorna PDF come HttpResponse
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="fascicoli_documenti_{unita.codice}_{pk}.pdf"'
        return response


class OperazioneArchivioViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire le operazioni di archivio fisico
    """
    queryset = OperazioneArchivio.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_operazione', 'referente_interno', 'referente_esterno']
    search_fields = ['note', 'referente_esterno__cognome', 'referente_esterno__nome']
    ordering_fields = ['data_ora', 'tipo_operazione']
    ordering = ['-data_ora']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OperazioneArchivioDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OperazioneArchivioCreateSerializer
        return OperazioneArchivioListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'referente_interno',
            'referente_esterno'
        ).prefetch_related(
            Prefetch(
                'righe',
                queryset=RigaOperazioneArchivio.objects.select_related(
                    'documento', 'fascicolo', 'movimento_protocollo',
                    'unita_fisica_sorgente', 'unita_fisica_destinazione'
                )
            )
        )
        
        # Filtro per data
        data_dal = self.request.query_params.get('data_dal')
        data_al = self.request.query_params.get('data_al')
        
        if data_dal:
            queryset = queryset.filter(data_ora__gte=data_dal)
        if data_al:
            queryset = queryset.filter(data_ora__lte=data_al)
        
        return queryset

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Processa un'operazione di archivio (aggiorna stati e collocazioni)
        """
        operazione = self.get_object()
        
        try:
            process_operazione_archivio(operazione)
            return Response({
                'status': 'success',
                'message': 'Operazione processata con successo'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def verbale(self, request, pk=None):
        """
        Genera il verbale di consegna in formato DOCX
        """
        operazione = self.get_object()
        template_slug = request.query_params.get('template')
        
        try:
            if template_slug:
                template = get_object_or_404(VerbaleConsegnaTemplate, slug=template_slug, attivo=True)
            else:
                # Usa il primo template attivo come default
                template = VerbaleConsegnaTemplate.objects.filter(attivo=True).first()
                if not template:
                    return Response({
                        'status': 'error',
                        'message': 'Nessun template disponibile per la generazione del verbale'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            docx_bytes, filename = render_verbale_consegna(template, operazione)
            
            response = HttpResponse(
                docx_bytes,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"ERRORE nella generazione del verbale:")
            print(f"Operazione ID: {pk}")
            print(f"Template slug: {template_slug}")
            print(f"Errore: {str(e)}")
            print(f"Traceback completo:")
            traceback.print_exc()
            print(f"{'='*60}\n")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def templates(self, request):
        """
        Ritorna i template disponibili per i verbali
        """
        templates = VerbaleConsegnaTemplate.objects.filter(attivo=True)
        serializer = VerbaleConsegnaTemplateSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def utenti(self, request):
        """
        Ritorna la lista degli utenti attivi per il referente interno
        """
        from django.contrib.auth import get_user_model
        from .serializers import UserSimpleSerializer
        
        User = get_user_model()
        utenti = User.objects.filter(is_active=True).order_by('last_name', 'first_name', 'username')
        serializer = UserSimpleSerializer(utenti, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def utenti(self, request):
        """
        Ritorna la lista degli utenti per il campo referente_interno
        """
        from django.contrib.auth import get_user_model
        from .serializers import UserSimpleSerializer
        
        User = get_user_model()
        utenti = User.objects.filter(is_active=True).order_by('last_name', 'first_name', 'username')
        serializer = UserSimpleSerializer(utenti, many=True)
        return Response(serializer.data)


class RigaOperazioneArchivioViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire le righe delle operazioni di archivio
    """
    queryset = RigaOperazioneArchivio.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['operazione', 'documento', 'fascicolo']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RigaOperazioneArchivioCreateSerializer
        return RigaOperazioneArchivioSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'documento', 'fascicolo', 'movimento_protocollo',
            'unita_fisica_sorgente', 'unita_fisica_destinazione', 'operazione'
        )
        return queryset

    def perform_create(self, serializer):
        """
        Al salvataggio della riga, aggiorna l'ubicazione del documento/fascicolo
        con il valore di unita_fisica_destinazione (A Unità)
        """
        riga = serializer.save()
        
        # Aggiorna ubicazione documento o fascicolo
        if riga.unita_fisica_destinazione:
            if riga.documento:
                riga.documento.ubicazione = riga.unita_fisica_destinazione
                riga.documento.save(update_fields=['ubicazione'])
            elif riga.fascicolo:
                riga.fascicolo.ubicazione = riga.unita_fisica_destinazione
                riga.fascicolo.save(update_fields=['ubicazione'])

    def perform_update(self, serializer):
        """
        Anche nell'aggiornamento, aggiorna l'ubicazione
        """
        riga = serializer.save()
        
        # Aggiorna ubicazione documento o fascicolo
        if riga.unita_fisica_destinazione:
            if riga.documento:
                riga.documento.ubicazione = riga.unita_fisica_destinazione
                riga.documento.save(update_fields=['ubicazione'])
            elif riga.fascicolo:
                riga.fascicolo.ubicazione = riga.unita_fisica_destinazione
                riga.fascicolo.save(update_fields=['ubicazione'])


class CollocazioneFisicaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per visualizzare le collocazioni fisiche
    """
    queryset = CollocazioneFisica.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CollocazioneFisicaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['unita', 'documento', 'attiva']
    ordering_fields = ['dal', 'al', 'created_at']
    ordering = ['-dal']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('unita', 'documento', 'content_type')
        
        # Filtro per solo collocazioni attive
        solo_attive = self.request.query_params.get('solo_attive')
        if solo_attive and solo_attive.lower() == 'true':
            queryset = queryset.filter(attiva=True)
        
        return queryset


class DocumentoTracciabileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per cercare documenti tracciabili con filtri avanzati per stato operazioni
    """
    queryset = Documento.objects.filter(tracciabile=True, digitale=False)
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentoSimpleSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['codice', 'descrizione']
    filterset_fields = ['stato', 'tipo', 'fascicolo']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Ottimizzazione: carica l'ubicazione in un'unica query
        queryset = queryset.select_related('ubicazione', 'tipo', 'cliente__anagrafica', 'fascicolo__cliente__anagrafica')
        
        # Filtro per referente esterno (anagrafica)
        referente_esterno_id = self.request.query_params.get('referente_esterno')
        if referente_esterno_id:
            from django.db.models import Q
            # Documenti collegati direttamente al cliente o tramite fascicolo
            queryset = queryset.filter(
                Q(cliente__anagrafica_id=referente_esterno_id) |
                Q(fascicolo__cliente__anagrafica_id=referente_esterno_id)
            )
        
        # Filtro per stato operazione
        stato_op = self.request.query_params.get('stato_operazione')
        if stato_op:
            from django.db.models import Q, OuterRef, Subquery, Max
            
            # Subquery per ottenere l'ultima operazione (esclusi movimenti interni)
            ultima_op = RigaOperazioneArchivio.objects.filter(
                documento=OuterRef('pk'),
                operazione__tipo_operazione__in=['entrata', 'uscita']
            ).order_by('-operazione__data_ora').values('operazione__tipo_operazione')[:1]
            
            queryset = queryset.annotate(
                ultimo_tipo_op=Subquery(ultima_op)
            )
            
            if stato_op == 'latenti':
                # Documenti senza operazioni
                queryset = queryset.filter(ultimo_tipo_op__isnull=True)
            elif stato_op == 'in_giacenza':
                # Ultima operazione = entrata
                queryset = queryset.filter(ultimo_tipo_op='entrata')
            elif stato_op == 'scaricati':
                # Ultima operazione = uscita
                queryset = queryset.filter(ultimo_tipo_op='uscita')
        
        return queryset


class FascicoloTracciabileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per cercare fascicoli con filtri avanzati per stato operazioni
    """
    queryset = Fascicolo.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FascicoloSimpleSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['codice', 'titolo']
    filterset_fields = ['stato', 'anno', 'cliente']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Ottimizzazione: carica l'ubicazione e il cliente in un'unica query
        queryset = queryset.select_related('ubicazione', 'cliente__anagrafica')
        
        # Filtro per referente esterno (anagrafica)
        referente_esterno_id = self.request.query_params.get('referente_esterno')
        if referente_esterno_id:
            queryset = queryset.filter(cliente__anagrafica_id=referente_esterno_id)
        
        # Filtro per stato operazione
        stato_op = self.request.query_params.get('stato_operazione')
        if stato_op:
            from django.db.models import Q, OuterRef, Subquery
            
            # Subquery per ottenere l'ultima operazione (esclusi movimenti interni)
            ultima_op = RigaOperazioneArchivio.objects.filter(
                fascicolo=OuterRef('pk'),
                operazione__tipo_operazione__in=['entrata', 'uscita']
            ).order_by('-operazione__data_ora').values('operazione__tipo_operazione')[:1]
            
            queryset = queryset.annotate(
                ultimo_tipo_op=Subquery(ultima_op)
            )
            
            if stato_op == 'latenti':
                # Fascicoli senza operazioni
                queryset = queryset.filter(ultimo_tipo_op__isnull=True)
            elif stato_op == 'in_giacenza':
                # Ultima operazione = entrata
                queryset = queryset.filter(ultimo_tipo_op='entrata')
            elif stato_op == 'scaricati':
                # Ultima operazione = uscita
                queryset = queryset.filter(ultimo_tipo_op='uscita')
        
        return queryset


class MovimentoProtocolloViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per cercare movimenti di protocollo
    """
    queryset = MovimentoProtocollo.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MovimentoProtocolloSimpleSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['numero', 'oggetto']
    filterset_fields = ['tipo', 'anno', 'documento', 'fascicolo']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro per documento o fascicolo
        documento_id = self.request.query_params.get('documento_id')
        fascicolo_id = self.request.query_params.get('fascicolo_id')
        
        if documento_id:
            queryset = queryset.filter(documento_id=documento_id)
        if fascicolo_id:
            queryset = queryset.filter(fascicolo_id=fascicolo_id)
        
        return queryset
