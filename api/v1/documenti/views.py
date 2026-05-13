"""
Views per API Documenti
"""
import logging
import os
import tempfile
import shutil

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import RBACPermission
from django.http import FileResponse, Http404
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator

from documenti.models import Documento, DocumentiTipo, AttributoDefinizione
from anagrafiche.models import Anagrafica, Cliente
from archivio_fisico.models import UnitaFisica
from titolario.models import TitolarioVoce
from .filters import DocumentoFilter
from .serializers import (
    DocumentoListSerializer,
    DocumentoDetailSerializer,
    DocumentoCreateUpdateSerializer,
    DocumentiTipoSerializer,
    AttributoDefinizioneSerializer,
    ImportaCedoliniSerializer,
    CedoliniImportPreviewSerializer,
    CedoliniImportConfirmSerializer,
    UnilavImportPreviewSerializer,
    UnilavImportConfirmSerializer,
)

logger = logging.getLogger(__name__)


class AllowSignedTokenOrAuthenticated(BasePermission):
    """
    Permission che permette accesso se:
    - L'utente è autenticato (JWT/Session)
    - OPPURE c'è un token signed valido nell'URL
    """
    def has_permission(self, request, view):
        # Se già autenticato, OK
        if request.user and request.user.is_authenticated:
            return True
        
        # Altrimenti verifica se c'è un token signed
        from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
        
        token = request.GET.get('token')
        if not token:
            return False
        
        try:
            signer = TimestampSigner()
            unsigned_value = signer.unsign(token, max_age=300)  # 5 minuti
            # Token format: "{session_uuid}:{doc_uuid}:{user_id}"
            token_parts = unsigned_value.split(':')
            if len(token_parts) == 3:
                # Imposta l'utente nel request per uso successivo
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    request.user = User.objects.get(id=int(token_parts[2]))
                    return True
                except User.DoesNotExist:
                    pass
        except (SignatureExpired, BadSignature, ValueError):
            pass
        
        return False


def _mappa_tipo_comunicazione_unilav(modello: str = None, tipologia_contrattuale: str = None, tipo_comunicazione: str = None) -> str:
    """
    Mappa il modello UNILAV o la tipologia contrattuale estratta dal PDF 
    a uno dei valori validi per l'attributo 'tipo' (Assunzione, Proroga, Trasformazione, Cessazione).
    
    Args:
        modello: Modello UNILAV dal PDF (es. "UniLav/Instaurazione", "UniLav/Proroga")
        tipologia_contrattuale: Tipo contratto estratto dal PDF (es. "LAVORO A TEMPO DETERMINATO")
        tipo_comunicazione: Tipo comunicazione (es. "Comunicazione Obbligatoria")
        
    Returns:
        Uno dei valori validi: "Assunzione", "Proroga", "Trasformazione", "Cessazione"
    """
    # PRIORITÀ 1: Usa il campo "modello" se presente (più affidabile)
    if modello:
        modello_upper = modello.upper()
        if 'INSTAURAZIONE' in modello_upper or 'ASSUNZIONE' in modello_upper:
            return 'Assunzione'
        elif 'PROROGA' in modello_upper:
            return 'Proroga'
        elif 'TRASFORMAZIONE' in modello_upper:
            return 'Trasformazione'
        elif 'CESSAZIONE' in modello_upper or 'CESSIONE' in modello_upper:
            return 'Cessazione'
    
    # PRIORITÀ 2: Se tipo_comunicazione contiene un valore valido, usalo
    if tipo_comunicazione:
        tipo_upper = tipo_comunicazione.upper()
        if 'ASSUNZIONE' in tipo_upper or 'INSTAURAZIONE' in tipo_upper:
            return 'Assunzione'
        elif 'PROROGA' in tipo_upper:
            return 'Proroga'
        elif 'TRASFORMAZIONE' in tipo_upper:
            return 'Trasformazione'
        elif 'CESSAZIONE' in tipo_upper or 'CESSIONE' in tipo_upper:
            return 'Cessazione'
    
    # PRIORITÀ 3: Usa tipologia_contrattuale per inferire (meno affidabile)
    if tipologia_contrattuale:
        tipo_upper = tipologia_contrattuale.upper()
        
        # Mapping basato su keywords
        if 'DETERMINATO' in tipo_upper or 'TEMPO DETERMINATO' in tipo_upper:
            # Contratti a tempo determinato sono generalmente assunzioni
            return 'Assunzione'
        elif 'INDETERMINATO' in tipo_upper or 'TEMPO INDETERMINATO' in tipo_upper:
            return 'Assunzione'
        elif 'APPRENDISTATO' in tipo_upper:
            return 'Assunzione'
        elif 'SOMMINISTRAZIONE' in tipo_upper:
            return 'Assunzione'
        elif 'TIROCINIO' in tipo_upper or 'STAGE' in tipo_upper:
            return 'Assunzione'
    
    # Default: Assunzione (valore più comune)
    logger.warning(
        f"Impossibile mappare tipo comunicazione UNILAV: "
        f"modello='{modello}', "
        f"tipo_comunicazione='{tipo_comunicazione}', "
        f"tipologia_contrattuale='{tipologia_contrattuale}'. "
        f"Uso default: 'Assunzione'"
    )
    return 'Assunzione'


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione documenti con RBAC.
    
    Isolamento dati:
    - ADMIN/MANAGER: tutti i documenti
    - OPERATORE/VIEWER: solo documenti dei clienti assegnati
    """
    permission_classes = [RBACPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentoFilter
    search_fields = ['id', 'codice', 'descrizione', 'tags', 'note', 'ubicazione__codice', 'ubicazione__nome', 'ubicazione__full_path']
    ordering_fields = ['data_documento', 'codice', 'creato_il', 'aggiornato_il']
    ordering = ['-data_documento']
    
    def get_queryset(self):
        qs = Documento.objects.select_related(
            'tipo', 'cliente', 'cliente__anagrafica', 'fascicolo',
            'titolario_voce', 'ubicazione'
        ).prefetch_related('attributi_valori', 'attributi_valori__definizione')
        
        # RBAC Filtering
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            
            # ADMIN/MANAGER: vedono tutto
            if profile.can_view_all:
                return qs
            
            # OPERATORE/VIEWER: solo documenti clienti assegnati
            accessible_clients_ids = profile.get_accessible_clients_ids()
            if accessible_clients_ids is not None:
                qs = qs.filter(cliente_id__in=accessible_clients_ids)
        
        return qs
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentoListSerializer
        elif self.action == 'retrieve':
            return DocumentoDetailSerializer
        else:
            return DocumentoCreateUpdateSerializer
    
    def perform_create(self, serializer):
        """Crea documento e restituisce versione completa"""
        serializer.save()
    
    def perform_update(self, serializer):
        """Aggiorna documento"""
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Override update per restituire documento completo con attributi"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Ricarica l'istanza dal database per avere i dati aggiornati
        instance.refresh_from_db()
        
        # Restituisci il documento completo con attributi usando DocumentoDetailSerializer
        detail_serializer = DocumentoDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Override create per restituire documento completo con attributi"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Assicura che i campi DateField siano convertiti correttamente dal database
        if serializer.instance is not None:
            serializer.instance.refresh_from_db()
        
        # Restituisci il documento completo con attributi usando DocumentoDetailSerializer
        detail_serializer = DocumentoDetailSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download file documento"""
        documento = self.get_object()
        
        if not documento.file:
            return Response(
                {'detail': 'Nessun file associato al documento'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                documento.file.open('rb'),
                as_attachment=True,
                filename=documento.file.name.split('/')[-1]
            )
        except Exception as e:
            return Response(
                {'detail': f'Errore nel download del file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview file documento (visualizza inline nel browser)"""
        documento = self.get_object()
        
        if not documento.file:
            return Response(
                {'detail': 'Nessun file associato al documento'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Determina il content type dal nome del file
            import mimetypes
            content_type, _ = mimetypes.guess_type(documento.file.name)
            
            response = FileResponse(
                documento.file.open('rb'),
                as_attachment=False,  # Non forzare il download
                content_type=content_type or 'application/octet-stream'
            )
            
            # Aggiungi header per permettere la visualizzazione inline
            response['Content-Disposition'] = f'inline; filename="{documento.file.name.split("/")[-1]}"'
            
            return response
        except Exception as e:
            return Response(
                {'detail': f'Errore nel caricamento del file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def protocolla(self, request, pk=None):
        """Protocolla documento"""
        documento = self.get_object()
        
        direzione = (request.data.get('direzione') or 'IN').upper()
        destinatario = request.data.get('destinatario', '')
        note = request.data.get('note', '')
        causale = request.data.get('causale', '')
        data_rientro_prevista = request.data.get('data_rientro_prevista')
        destinatario_anagrafica = None
        ubicazione = None

        try:
            if request.data.get('destinatario_anagrafica'):
                destinatario_anagrafica = Anagrafica.objects.get(pk=request.data['destinatario_anagrafica'])
        except (Anagrafica.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Anagrafica destinatario non trovata.'}, status=status.HTTP_400_BAD_REQUEST)

        ubicazione_id = request.data.get('ubicazione') or request.data.get('ubicazione_id')
        if ubicazione_id:
            try:
                ubicazione = UnitaFisica.objects.get(pk=ubicazione_id)
            except (UnitaFisica.DoesNotExist, ValueError, TypeError):
                return Response({'detail': 'Ubicazione non trovata.'}, status=status.HTTP_400_BAD_REQUEST)

        if data_rientro_prevista:
            from datetime import datetime
            try:
                data_rientro_prevista = datetime.strptime(data_rientro_prevista, '%Y-%m-%d').date()
            except ValueError:
                return Response({'detail': 'Formato data rientro previsto non valido (YYYY-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from protocollo.models import MovimentoProtocollo

            if direzione == 'OUT':
                MovimentoProtocollo.registra_uscita(
                    documento=documento,
                    quando=None,
                    operatore=request.user,
                    a_chi=destinatario,
                    destinatario_anagrafica=destinatario_anagrafica,
                    data_rientro_prevista=data_rientro_prevista,
                    causale=causale,
                    note=note,
                    ubicazione=ubicazione,
                )
            else:
                MovimentoProtocollo.registra_entrata(
                    documento=documento,
                    quando=None,
                    operatore=request.user,
                    da_chi=destinatario,
                    destinatario_anagrafica=destinatario_anagrafica,
                    ubicazione=ubicazione,
                    causale=causale,
                    note=note,
                )

            detail_serializer = DocumentoDetailSerializer(documento, context={'request': request})
            return Response(detail_serializer.data)

        except Exception as e:
            return Response(
                {'detail': f'Errore nella protocollazione: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Ricerca documenti per codice/descrizione"""
        q = request.query_params.get('q', '')
        
        if not q:
            return Response([])
        
        documenti = self.get_queryset().filter(
            Q(codice__icontains=q) | Q(descrizione__icontains=q)
        )[:20]
        
        serializer = DocumentoListSerializer(documenti, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def importa_unilav_preview(self, request):
        """
        Step 1: Analizza PDF UNILAV e restituisce anteprima dati estratti.
        
        Endpoint: POST /api/v1/documenti/importa-unilav-preview/
        
        Request Body (multipart/form-data):
            - file: File PDF UNILAV
        
        Response:
            {
                "datore": {
                    "codice_fiscale": "...",
                    "tipo": "PF" | "PG",
                    "ragione_sociale": "...",
                    "email": "...",
                    ...
                    "esiste": true,
                    "anagrafica_id": 123,
                    "cliente_id": 456
                },
                "lavoratore": {
                    "codice_fiscale": "...",
                    "cognome": "...",
                    "nome": "...",
                    ...
                    "esiste": true,
                    "anagrafica_id": 789
                },
                "documento": {
                    "codice_comunicazione": "...",
                    "data_comunicazione": "...",
                    "data_da": "...",
                    "data_a": "...",
                    ...
                },
                "file_temp_path": "/tmp/unilav_xxx.pdf"
            }
        """
        serializer = UnilavImportPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pdf_file = serializer.validated_data['file']
        
        # Salva temporaneamente il file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, pdf_file.name)
        
        with open(temp_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)
        
        try:
            # Parse PDF UNILAV
            from documenti.parsers.unilav_parser import parse_unilav_pdf
            parsed_data = parse_unilav_pdf(temp_path)
            
            # Prepara dati datore di lavoro
            datore_data = parsed_data['datore']
            cf_datore = datore_data['codice_fiscale']
            
            # Determina tipo anagrafica datore (PF o PG in base a lunghezza CF)
            tipo_datore = 'PF' if len(cf_datore) == 16 else 'PG'
            
            datore_response = {
                'codice_fiscale': cf_datore,
                'tipo': tipo_datore,
                'crea_se_non_esiste': True,
                'crea_cliente': True,
            }
            
            if tipo_datore == 'PG':
                datore_response['ragione_sociale'] = datore_data['denominazione']
            else:
                # Per PF proviamo a estrarre cognome/nome dalla denominazione
                parti = datore_data['denominazione'].split(' ', 1)
                datore_response['cognome'] = parti[0] if len(parti) > 0 else datore_data['denominazione']
                datore_response['nome'] = parti[1] if len(parti) > 1 else ''
            
            datore_response.update({
                'email': datore_data.get('email'),
                'telefono': datore_data.get('telefono'),
                'comune': datore_data.get('comune_sede_legale'),
                'cap': datore_data.get('cap_sede_legale'),
                'indirizzo': datore_data.get('indirizzo_sede_legale'),
            })
            
            # Verifica se anagrafica datore esiste già
            try:
                anagrafica_datore = Anagrafica.objects.get(codice_fiscale=cf_datore)
                datore_response['esiste'] = True
                datore_response['anagrafica_id'] = anagrafica_datore.id
                
                # Verifica se è anche cliente
                try:
                    cliente_datore = Cliente.objects.get(anagrafica=anagrafica_datore)
                    datore_response['cliente_id'] = cliente_datore.id
                except Cliente.DoesNotExist:
                    datore_response['cliente_id'] = None
            except Anagrafica.DoesNotExist:
                datore_response['esiste'] = False
                datore_response['anagrafica_id'] = None
                datore_response['cliente_id'] = None
            
            # Prepara dati lavoratore
            lavoratore_data = parsed_data['lavoratore']
            cf_lavoratore = lavoratore_data['codice_fiscale']
            
            lavoratore_response = {
                'codice_fiscale': cf_lavoratore,
                'tipo': 'PF',
                'cognome': lavoratore_data['cognome'],
                'nome': lavoratore_data['nome'],
                'sesso': lavoratore_data.get('sesso'),
                'data_nascita': lavoratore_data.get('data_nascita'),
                'comune_nascita': lavoratore_data.get('comune_nascita'),
                'comune': lavoratore_data.get('comune_domicilio'),
                'cap': lavoratore_data.get('cap_domicilio'),
                'indirizzo': lavoratore_data.get('indirizzo_domicilio'),
                'crea_se_non_esiste': True,
                'crea_cliente': False,
            }
            
            # Verifica se anagrafica lavoratore esiste già
            try:
                anagrafica_lavoratore = Anagrafica.objects.get(codice_fiscale=cf_lavoratore)
                lavoratore_response['esiste'] = True
                lavoratore_response['anagrafica_id'] = anagrafica_lavoratore.id
            except Anagrafica.DoesNotExist:
                lavoratore_response['esiste'] = False
                lavoratore_response['anagrafica_id'] = None
            
            # Prepara dati documento UNILAV
            unilav_data = parsed_data['unilav']
            
            # Mappa tipo comunicazione a uno dei valori validi della SELECT
            # Usa il campo "modello" come priorità principale
            tipo_mappato = _mappa_tipo_comunicazione_unilav(
                modello=unilav_data.get('modello'),
                tipologia_contrattuale=unilav_data.get('tipologia_contrattuale'),
                tipo_comunicazione=unilav_data.get('tipo_comunicazione')
            )
            
            documento_response = {
                'codice_comunicazione': unilav_data['codice_comunicazione'],
                'tipo_comunicazione': unilav_data.get('tipo_comunicazione'),
                'modello': unilav_data.get('modello'),
                'data_comunicazione': unilav_data['data_comunicazione'],
                'centro_impiego': unilav_data.get('centro_impiego'),
                'provincia_impiego': unilav_data.get('provincia_impiego'),
                'dipendente': lavoratore_response.get('anagrafica_id'),
                'tipo': tipo_mappato,  # Valore mappato per la SELECT
                'data_da': unilav_data.get('data_inizio_rapporto'),
                'data_a': unilav_data.get('data_fine_rapporto'),
                'data_proroga': unilav_data.get('data_proroga'),
                'data_trasformazione': unilav_data.get('data_trasformazione'),
                'causa_trasformazione': unilav_data.get('causa_trasformazione'),
                'ente_previdenziale': unilav_data.get('ente_previdenziale'),
                'codice_ente_previdenziale': unilav_data.get('codice_ente_previdenziale'),
                'pat_inail': unilav_data.get('pat_inail'),
                'qualifica': unilav_data.get('qualifica_professionale'),
                'contratto_collettivo': unilav_data.get('contratto_collettivo'),
                'livello': unilav_data.get('livello_inquadramento'),
                'retribuzione': unilav_data.get('retribuzione'),
                'ore_settimanali': unilav_data.get('ore_settimanali'),
                'tipo_orario': unilav_data.get('tipo_orario'),
            }
            
            # CONTROLLO DUPLICATI: Verifica se esiste già un documento UNILAV con stesso codice_comunicazione
            from documenti.models import AttributoValore, AttributoDefinizione
            
            documento_esistente = None
            codice_com = unilav_data['codice_comunicazione']
            
            try:
                # Cerca tipo documento UNILAV
                tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
                
                # Cerca definizione attributo codice_comunicazione
                attr_def = AttributoDefinizione.objects.get(
                    tipo_documento=tipo_unilav,
                    codice='codice_comunicazione'
                )
                
                # Cerca documenti con stesso codice_comunicazione
                attr_valore = AttributoValore.objects.filter(
                    definizione=attr_def,
                    valore=codice_com
                ).select_related('documento', 'documento__cliente', 'documento__cliente__anagrafica').first()
                
                if attr_valore:
                    doc = attr_valore.documento
                    documento_esistente = {
                        'id': doc.id,
                        'codice': doc.codice,
                        'descrizione': doc.descrizione,
                        'data_documento': doc.data_documento.isoformat() if doc.data_documento else None,
                        'cliente_id': doc.cliente_id,
                        'cliente_nome': doc.cliente.anagrafica.display_name() if doc.cliente else None,
                        'url': f'/documenti/{doc.id}/',
                        # Attributi attuali per diff
                        'attributi_attuali': {
                            'tipo': None,
                            'data_da': None,
                            'data_a': None,
                            'qualifica': None,
                            'contratto_collettivo': None,
                            'livello': None,
                            'retribuzione': None,
                        }
                    }
                    
                    # Carica attributi attuali del documento esistente per diff
                    for attr_val in doc.attributi_valori.all():
                        codice_attr = attr_val.definizione.codice
                        if codice_attr in documento_esistente['attributi_attuali']:
                            documento_esistente['attributi_attuali'][codice_attr] = attr_val.valore
                    
                    print(f"⚠️  DUPLICATO RILEVATO: Documento UNILAV {codice_com} già esistente (ID: {doc.id})")
                    
            except (DocumentiTipo.DoesNotExist, AttributoDefinizione.DoesNotExist):
                # Tipo o attributo non configurato, ignora controllo duplicati
                print(f"⚠️  Impossibile verificare duplicati: tipo UNILAV o attributo codice_comunicazione non configurato")
            
            response_data = {
                'datore': datore_response,
                'lavoratore': lavoratore_response,
                'documento': documento_response,
                'file_temp_path': temp_path,
            }
            
            # Aggiungi informazioni duplicato se trovato
            if documento_esistente:
                response_data['duplicato'] = True
                response_data['documento_esistente'] = documento_esistente
            else:
                response_data['duplicato'] = False
            
            return Response(response_data)
            
        except Exception as e:
            # Pulizia file temporaneo in caso di errore
            print("\n" + "="*80)
            print(f"✗ ERRORE PREVIEW UNILAV:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Messaggio: {str(e)}")
            import traceback
            print("Traceback:")
            traceback.print_exc()
            print("="*80 + "\n")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            return Response(
                {'detail': f'Errore nell\'analisi del PDF: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def importa_unilav_confirm(self, request):
        """
        Step 2: Conferma e importa definitivamente i dati UNILAV.
        
        Endpoint: POST /api/v1/documenti/importa-unilav-confirm/
        
        Request Body (application/json):
            {
                "datore": { ... },
                "lavoratore": { ... },
                "documento": { ... },
                "file_path": "/tmp/unilav_xxx.pdf"
            }
        
        Response:
            {
                "success": true,
                "anagrafica_datore_id": 123,
                "cliente_id": 456,
                "anagrafica_lavoratore_id": 789,
                "documento_id": 999,
                "message": "UNILAV importato con successo"
            }
        """
        # Log dati ricevuti per debug
        print("\n" + "="*80)
        print("=== UNILAV CONFIRM REQUEST ===")
        print(f"Request data keys: {list(request.data.keys())}")
        print(f"File path presente: {'file_path' in request.data}")
        print(f"File temp path presente: {'file_temp_path' in request.data}")
        print("="*80 + "\n")
        
        serializer = UnilavImportConfirmSerializer(data=request.data)
        
        print(f"Serializer creato: {serializer.__class__.__name__}")
        print(f"Prima di is_valid()...")
        
        if not serializer.is_valid():
            # Log errori di validazione per debug
            print("\n" + "="*80)
            print("ERRORI VALIDAZIONE UNILAV:")
            print(serializer.errors)
            print("="*80 + "\n")
            logger.error(f"Errori validazione UNILAV confirm: {serializer.errors}")
            logger.error(f"Dati ricevuti completi: {request.data}")
            return Response(
                {
                    'detail': 'Errore validazione dati',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print("✓ Serializer is_valid() passato!")
        print(f"Validated data keys: {list(serializer.validated_data.keys())}")
        print(f"file_path in validated_data: {serializer.validated_data.get('file_path')}")
        
        datore_data = serializer.validated_data['datore']
        lavoratore_data = serializer.validated_data['lavoratore']
        documento_data = serializer.validated_data['documento']
        file_path = serializer.validated_data['file_path']
        azione = serializer.validated_data.get('azione', 'crea')
        documento_id_esistente = serializer.validated_data.get('documento_id_esistente')
        
        print(f"✓ Dati estratti da validated_data")
        print(f"  - Azione: {azione}")
        if azione == 'sovrascrivi':
            print(f"  - Documento ID da sovrascrivere: {documento_id_esistente}")
        print(f"  - datore CF: {datore_data.get('codice_fiscale')}")
        print(f"  - lavoratore CF: {lavoratore_data.get('codice_fiscale')}")
        print(f"  - file_path: {file_path}")
        
        # Verifica che il file temporaneo esista ancora
        print(f"Verifica esistenza file: {file_path}")
        if not os.path.exists(file_path):
            print(f"✗ File non trovato: {file_path}")
            return Response(
                {'detail': 'File temporaneo non trovato. Ricarica il PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        print(f"✓ File esiste")
        
        try:
            print("\n" + "="*80)
            print("INIZIO TRANSAZIONE DATABASE")
            print("="*80)
            from django.db import transaction
            
            with transaction.atomic():
                print("\n1. Gestione anagrafica/cliente DATORE...")
                # 1. Crea/Recupera anagrafica datore
                # IMPORTANTE: Se l'anagrafica esiste già (stesso CF), viene RIUTILIZZATA senza modifiche.
                # NON vengono sovrascritti i dati esistenti (ragione_sociale, nome, cognome, etc.)
                anagrafica_datore = None
                cliente_datore = None
                
                try:
                    # Cerca anagrafica esistente per codice fiscale
                    anagrafica_datore = Anagrafica.objects.get(
                        codice_fiscale=datore_data['codice_fiscale']
                    )
                    # Anagrafica trovata: viene riutilizzata così com'è
                except Anagrafica.DoesNotExist:
                    # Anagrafica non esiste: crea nuova solo se richiesto
                    if datore_data.get('crea_se_non_esiste', True):
                        # Crea nuova anagrafica
                        anagrafica_datore = Anagrafica.objects.create(
                            codice_fiscale=datore_data['codice_fiscale'],
                            tipo=datore_data['tipo'],
                            ragione_sociale=datore_data.get('ragione_sociale', ''),
                            cognome=datore_data.get('cognome', ''),
                            nome=datore_data.get('nome', ''),
                        )
                
                if not anagrafica_datore:
                    raise ValueError("Anagrafica datore non trovata e creazione disabilitata")
                
                # Crea cliente se richiesto
                if datore_data.get('crea_cliente', True):
                    cliente_datore, _ = Cliente.objects.get_or_create(
                        anagrafica=anagrafica_datore
                    )
                else:
                    try:
                        cliente_datore = Cliente.objects.get(anagrafica=anagrafica_datore)
                    except Cliente.DoesNotExist:
                        raise ValueError("Il datore deve essere un cliente esistente")
                
                # 2. Crea/Recupera anagrafica lavoratore
                # IMPORTANTE: Se l'anagrafica esiste già (stesso CF), viene RIUTILIZZATA senza modifiche.
                # NON vengono sovrascritti i dati esistenti (cognome, nome, data_nascita, etc.)
                anagrafica_lavoratore = None
                
                try:
                    # Cerca anagrafica esistente per codice fiscale
                    anagrafica_lavoratore = Anagrafica.objects.get(
                        codice_fiscale=lavoratore_data['codice_fiscale']
                    )
                    # Anagrafica trovata: viene riutilizzata così com'è
                except Anagrafica.DoesNotExist:
                    # Anagrafica non esiste: crea nuova solo se richiesto
                    if lavoratore_data.get('crea_se_non_esiste', True):
                        anagrafica_lavoratore = Anagrafica.objects.create(
                            codice_fiscale=lavoratore_data['codice_fiscale'],
                            tipo='PF',
                            cognome=lavoratore_data['cognome'],
                            nome=lavoratore_data['nome'],
                            # Note: sesso e data_nascita non sono campi del modello Anagrafica
                            # Eventualmente verranno gestiti tramite attributi dinamici o estensioni future
                        )
                
                if not anagrafica_lavoratore:
                    raise ValueError("Anagrafica lavoratore non trovata e creazione disabilitata")
                
                # 3. Verifica esistenza tipo documento UNILAV
                try:
                    tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
                except DocumentiTipo.DoesNotExist:
                    raise ValueError(
                        "Tipo documento UNILAV non configurato. "
                        "Contatta l'amministratore per creare il tipo documento."
                    )
                
                # 3.bis Crea/Trova voce titolario intestata al dipendente
                # Parent: HR-PERS (Dossier personale)
                # Sottovoce: Codice anagrafica dipendente (es. CONSLI01)
                # Titolo: "Dossier {Cognome} {Nome}"
                voce_dipendente = None
                try:
                    voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
                    
                    # IMPORTANTE: Genera codice anagrafica se non presente PRIMA di cercare la voce
                    if not anagrafica_lavoratore.codice:
                        from anagrafiche.utils import get_or_generate_cli
                        get_or_generate_cli(anagrafica_lavoratore)
                        anagrafica_lavoratore.refresh_from_db()
                    
                    # Cerca voce titolario per CODICE (non per anagrafica)
                    # Questo evita duplicati se la voce esiste ma non è collegata all'anagrafica
                    voce_dipendente = TitolarioVoce.objects.filter(
                        parent=voce_hr_pers,
                        codice=anagrafica_lavoratore.codice
                    ).first()
                    
                    if not voce_dipendente:
                        # Crea nuova voce intestata
                        voce_dipendente = TitolarioVoce.objects.create(
                            codice=anagrafica_lavoratore.codice,
                            titolo=f"Dossier {anagrafica_lavoratore.display_name()}",
                            parent=voce_hr_pers,
                            anagrafica=anagrafica_lavoratore,
                            pattern_codice='{CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}',
                            consente_intestazione=False
                        )
                        print(f"✓ Creata voce titolario: {voce_dipendente.codice} - {voce_dipendente.titolo}")
                        logger.info(f"Creata voce titolario per dipendente: {voce_dipendente.codice} - {voce_dipendente.titolo}")
                    else:
                        # Voce trovata: aggiorna anagrafica se non collegata
                        if voce_dipendente.anagrafica_id != anagrafica_lavoratore.id:
                            voce_dipendente.anagrafica = anagrafica_lavoratore
                            voce_dipendente.save(update_fields=['anagrafica'])
                            print(f"✓ Voce titolario esistente aggiornata con anagrafica: {voce_dipendente.codice}")
                        else:
                            print(f"✓ Voce titolario esistente riutilizzata: {voce_dipendente.codice}")
                        logger.info(f"Trovata voce titolario esistente per dipendente: {voce_dipendente.codice}")
                        
                except TitolarioVoce.DoesNotExist:
                    logger.warning("Voce titolario HR-PERS non trovata. Documento verrà creato senza voce titolario.")
                    voce_dipendente = None
                
                # 4. Gestione creazione/sovrascrittura documento
                from datetime import datetime
                
                # Estrai tipo comunicazione dal documento_data (già mappato)
                tipo_comunicazione_display = documento_data.get('tipo', 'Assunzione')
                descrizione = f"UNILAV {tipo_comunicazione_display} {documento_data['codice_comunicazione']} - {anagrafica_lavoratore.display_name()}"
                
                # AZIONE: SOVRASCRIVI
                if azione == 'sovrascrivi' and documento_id_esistente:
                    print(f"\n🔄 SOVRASCRITTURA documento esistente ID: {documento_id_esistente}")
                    
                    try:
                        documento = Documento.objects.get(id=documento_id_esistente, tipo=tipo_unilav)
                        
                        # Salva valori precedenti per audit log
                        valori_precedenti = {
                            'descrizione': documento.descrizione,
                            'data_documento': str(documento.data_documento) if documento.data_documento else None,
                            'cliente_id': documento.cliente_id,
                            'file': documento.file.name if documento.file else None,
                        }
                        
                        # Aggiorna campi documento
                        documento.cliente = cliente_datore
                        documento.titolario_voce = voce_dipendente
                        documento.descrizione = descrizione
                        documento.data_documento = documento_data['data_comunicazione']
                        documento.save()
                        
                        # Sostituisci file PDF
                        if documento.file:
                            documento.file.delete(save=False)
                        
                        with open(file_path, 'rb') as f:
                            from django.core.files import File
                            documento.file.save(
                                os.path.basename(file_path),
                                File(f),
                                save=True
                            )
                        
                        # AUDIT LOG
                        print(f"📝 AUDIT: Documento {documento.id} sovrascritto")
                        print(f"  Utente: {request.user.username if request.user.is_authenticated else 'Anonimo'}")
                        print(f"  Data: {datetime.now()}")
                        print(f"  Valori precedenti: {valori_precedenti}")
                        
                        logger.warning(
                            f"AUDIT SOVRASCRITTURA UNILAV - "
                            f"Documento ID: {documento.id} - "
                            f"Utente: {request.user.username if request.user.is_authenticated else 'Anonimo'} - "
                            f"Codice comunicazione: {documento_data['codice_comunicazione']} - "
                            f"File precedente: {valori_precedenti['file']}"
                        )
                        
                    except Documento.DoesNotExist:
                        raise ValueError(f"Documento ID {documento_id_esistente} non trovato o non è UNILAV")
                
                # AZIONE: DUPLICA (crea consapevolmente duplicato)
                elif azione == 'duplica':
                    print(f"\n⚠️  DUPLICAZIONE CONSAPEVOLE: Creazione documento duplicato")
                    logger.warning(
                        f"AUDIT DUPLICAZIONE UNILAV - "
                        f"Utente: {request.user.username if request.user.is_authenticated else 'Anonimo'} - "
                        f"Codice comunicazione: {documento_data['codice_comunicazione']} - "
                        f"Duplicato creato consapevolmente"
                    )
                    
                    documento = Documento.objects.create(
                        tipo=tipo_unilav,
                        cliente=cliente_datore,
                        titolario_voce=voce_dipendente,
                        descrizione=descrizione,
                        data_documento=documento_data['data_comunicazione'],
                        digitale=True,
                        tracciabile=True,
                        stato='definitivo',
                        ubicazione=None,
                    )
                    
                    # Salva file PDF
                    with open(file_path, 'rb') as f:
                        from django.core.files import File
                        documento.file.save(
                            os.path.basename(file_path),
                            File(f),
                            save=True
                        )
                
                # AZIONE: CREA (nuovo documento)
                else:
                    print(f"✓ Creazione nuovo documento: {descrizione}")
                    
                    documento = Documento.objects.create(
                        tipo=tipo_unilav,
                        cliente=cliente_datore,
                        titolario_voce=voce_dipendente,
                        descrizione=descrizione,
                        data_documento=documento_data['data_comunicazione'],
                        digitale=True,
                        tracciabile=True,
                        stato='definitivo',
                        ubicazione=None,
                    )
                    
                    # Salva file PDF
                    with open(file_path, 'rb') as f:
                        from django.core.files import File
                        documento.file.save(
                            os.path.basename(file_path),
                            File(f),
                            save=True
                        )
                
                # 5. Salva/aggiorna attributi dinamici
                # ATTRIBUTI DINAMICI (salvati in AttributoValore):
                # - codice_comunicazione: Codice identificativo UNILAV
                # - dipendente: ID anagrafica lavoratore (FK Anagrafica)
                # - tipo: Tipologia contrattuale (es. "Assunzione", "Proroga", etc.)
                # - data_comunicazione: Data della comunicazione UNILAV
                # - data_da: Data inizio rapporto di lavoro
                # - data_a: Data fine rapporto di lavoro
                # - data_proroga: Data fine proroga (solo per comunicazioni di proroga)
                
                from documenti.models import AttributoValore, AttributoDefinizione
                
                # Mappa attributi UNILAV
                attributi_map = {
                    'codice_comunicazione': documento_data['codice_comunicazione'],
                    'dipendente': anagrafica_lavoratore.id,
                    'tipo': documento_data.get('tipo'),
                    'data_comunicazione': documento_data.get('data_comunicazione'),
                    'data_da': documento_data.get('data_da'),
                    'data_a': documento_data.get('data_a'),
                    'data_proroga': documento_data.get('data_proroga'),
                }
                
                print(f"\n📋 DEBUG: Attributi da salvare:")
                for key, val in attributi_map.items():
                    print(f"   - {key}: {val} (tipo: {type(val).__name__})")
                
                for codice_attr, valore in attributi_map.items():
                    if valore is not None:
                        try:
                            definizione = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_unilav,
                                codice=codice_attr
                            )
                            
                            # Usa update_or_create per gestire sia creazione che sovrascrittura
                            attr_obj, created = AttributoValore.objects.update_or_create(
                                documento=documento,
                                definizione=definizione,
                                defaults={'valore': str(valore)}
                            )
                            action = "creato" if created else "aggiornato"
                            print(f"   ✓ Attributo '{codice_attr}' {action}: {valore}")
                        except AttributoDefinizione.DoesNotExist:
                            # Attributo non configurato, skip
                            print(f"   ⚠ Attributo '{codice_attr}' non configurato nel DB, saltato")
                            pass
                    else:
                        print(f"   - Attributo '{codice_attr}' saltato (valore None)")
                
                # 6. Aggiungi dati extra nelle NOTE del documento
                # DATI AGGIUNTIVI (non come attributi dinamici, ma in campo 'note'):
                # - qualifica: Qualifica professionale
                # - contratto_collettivo: CCNL applicato
                # - livello: Livello di inquadramento
                # - retribuzione: Retribuzione concordata
                # - ore_settimanali: Ore di lavoro settimanali
                # - tipo_orario: Tipologia orario (es. "Tempo pieno")
                # - data_trasformazione: Data trasformazione (per tipo Trasformazione)
                # - causa_trasformazione: Motivo trasformazione
                
                note_extra = []
                
                # Dati trasformazione (solo per tipo Trasformazione)
                if documento_data.get('data_trasformazione'):
                    note_extra.append(f"Data Trasformazione: {documento_data['data_trasformazione']}")
                if documento_data.get('causa_trasformazione'):
                    note_extra.append(f"Causa Trasformazione: {documento_data['causa_trasformazione']}")
                
                # Altri dati aggiuntivi
                if documento_data.get('qualifica'):
                    note_extra.append(f"Qualifica: {documento_data['qualifica']}")
                if documento_data.get('contratto_collettivo'):
                    note_extra.append(f"CCNL: {documento_data['contratto_collettivo']}")
                if documento_data.get('livello'):
                    note_extra.append(f"Livello: {documento_data['livello']}")
                if documento_data.get('retribuzione'):
                    note_extra.append(f"Retribuzione: {documento_data['retribuzione']}")
                if documento_data.get('ore_settimanali'):
                    note_extra.append(f"Ore settimanali: {documento_data['ore_settimanali']}")
                if documento_data.get('tipo_orario'):
                    note_extra.append(f"Tipo orario: {documento_data['tipo_orario']}")
                
                if note_extra:
                    documento.note = '\n'.join(note_extra)
                    documento.save()
                
                # Pulizia file temporaneo
                try:
                    os.remove(file_path)
                    temp_dir = os.path.dirname(file_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                except:
                    pass
                
                return Response({
                    'success': True,
                    'anagrafica_datore_id': anagrafica_datore.id,
                    'cliente_id': cliente_datore.id,
                    'anagrafica_lavoratore_id': anagrafica_lavoratore.id,
                    'documento_id': documento.id,
                    'message': 'UNILAV importato con successo'
                })
                
        except Exception as e:
            # Pulizia file temporaneo in caso di errore
            print("\n" + "="*80)
            print(f"✗ ERRORE DURANTE IMPORTAZIONE:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Messaggio: {str(e)}")
            import traceback
            print("Traceback completo:")
            traceback.print_exc()
            print("="*80 + "\n")
            
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                temp_dir = os.path.dirname(file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            
            return Response(
                {'detail': f'Errore nell\'importazione: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def importa_cedolini_preview(self, request):
        """
        Step 1: Analizza file (ZIP o PDF) e restituisce preview dati estratti.
        
        Endpoint: POST /api/v1/documenti/importa-cedolini-preview/
        
        Request Body (multipart/form-data):
            - file: File ZIP o PDF singolo
        
        Response:
            {
                "temp_dir": "/tmp/cedolini_XXX",
                "totale": 10,
                "validi": [...],  # Cedolini processabili
                "duplicati": [...],  # Cedolini già esistenti
                "errori": [...],  # File non processabili
                "statistiche": {
                    "nuovi_datori": 2,
                    "nuovi_dipendenti": 5,
                    "totale_validi": 8,
                    "totale_duplicati": 2,
                    "totale_errori": 0
                }
            }
        """
        import tempfile
        import zipfile
        import shutil
        import os
        from documenti.parsers.cedolino_parser import parse_cedolino_pdf
        from anagrafiche.models import Anagrafica
        from documenti.models import AttributoValore, AttributoDefinizione
        
        serializer = CedoliniImportPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        temp_dir = None
        
        try:
            # Determina tipo file
            filename_lower = file.name.lower()
            is_zip = filename_lower.endswith('.zip')
            is_pdf = filename_lower.endswith('.pdf')
            
            # Crea directory temporanea
            temp_dir = tempfile.mkdtemp(prefix='cedolini_')
            logger.info(f"Directory temporanea creata: {temp_dir}")
            
            if is_zip:
                # Salva ZIP
                zip_path = os.path.join(temp_dir, 'upload.zip')
                with open(zip_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                
                # Valida ZIP prima di estrarre
                try:
                    with zipfile.ZipFile(zip_path) as zf:
                        # Controlla numero file PDF
                        pdf_files_in_zip = [f for f in zf.namelist() if f.lower().endswith('.pdf')]
                        
                        if len(pdf_files_in_zip) == 0:
                            return Response(
                                {'detail': 'Il file ZIP non contiene file PDF'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        if len(pdf_files_in_zip) > 200:
                            return Response(
                                {'detail': f'Troppi file PDF nel ZIP ({len(pdf_files_in_zip)}). Massimo 200 consentiti.'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Controlla dimensione totale
                        total_size = sum(zf.getinfo(f).file_size for f in pdf_files_in_zip)
                        max_total_size = 500 * 1024 * 1024  # 500MB
                        
                        if total_size > max_total_size:
                            return Response(
                                {'detail': f'Dimensione totale file PDF troppo grande ({total_size / 1024 / 1024:.1f}MB). Massimo 500MB.'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Test integrità ZIP
                        bad_file = zf.testzip()
                        if bad_file:
                            return Response(
                                {'detail': f'ZIP corrotto. File problematico: {bad_file}'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                
                except zipfile.BadZipFile:
                    return Response(
                        {'detail': 'File ZIP non valido o corrotto'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Estrai ZIP
                extract_dir = os.path.join(temp_dir, 'extracted')
                os.makedirs(extract_dir, exist_ok=True)
                
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(extract_dir)
                
                logger.info(f"ZIP estratto in: {extract_dir}")
                
                # Lista PDF estratti
                pdf_paths = []
                for root, dirs, files in os.walk(extract_dir):
                    for filename in files:
                        if filename.lower().endswith('.pdf'):
                            pdf_paths.append(os.path.join(root, filename))
                
            else:
                # PDF singolo
                pdf_path = os.path.join(temp_dir, file.name)
                with open(pdf_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                
                pdf_paths = [pdf_path]
                logger.info(f"PDF singolo salvato: {pdf_path}")
            
            logger.info(f"Totale PDF da processare: {len(pdf_paths)}")
            
            # Processa ogni PDF
            validi = []
            duplicati = []
            errori = []
            
            # Carica tipo documento BPAG
            try:
                tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
            except DocumentiTipo.DoesNotExist:
                # Cleanup
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return Response(
                    {'detail': 'Tipo documento BPAG non configurato. Eseguire: python manage.py setup_cedolini'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            for pdf_path in pdf_paths:
                try:
                    # Parse PDF
                    parsed = parse_cedolino_pdf(pdf_path)
                    
                    # Match datore esistente (cerca per CF o P.IVA)
                    from django.db.models import Q
                    datore_cf = parsed['datore']['codice_fiscale']
                    datore_esistente = Anagrafica.objects.filter(
                        Q(codice_fiscale=datore_cf) | Q(partita_iva=datore_cf)
                    ).first()
                    
                    # Match dipendente esistente
                    dipendente_cf = parsed['lavoratore']['codice_fiscale']
                    dipendente_esistente = Anagrafica.objects.filter(
                        codice_fiscale=dipendente_cf
                    ).first()
                    
                    # Controlla se cedolino è duplicato
                    is_duplicato = False
                    documento_duplicato_id = None
                    
                    # Strategia duplicazione: priorità numero_cedolino + data_ora, fallback dipendente + periodo
                    numero_cedolino = parsed['cedolino'].get('numero_cedolino')
                    data_ora_cedolino = parsed['cedolino'].get('data_ora_cedolino')
                    
                    if numero_cedolino and data_ora_cedolino:
                        # Cerca per numero cedolino + data/ora (chiave univoca primaria)
                        try:
                            attr_def_numero = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='numero_cedolino'
                            )
                            attr_def_dataora = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='data_ora_cedolino'
                            )
                            
                            # Cerca documenti BPAG con stesso numero + data/ora
                            documenti_candidati = Documento.objects.filter(
                                tipo=tipo_bpag
                            ).prefetch_related('attributi_valori')
                            
                            for doc in documenti_candidati:
                                attributi = {av.definizione.codice: av.valore for av in doc.attributi_valori.all()}
                                
                                if (attributi.get('numero_cedolino') == numero_cedolino and
                                    attributi.get('data_ora_cedolino') == data_ora_cedolino):
                                    is_duplicato = True
                                    documento_duplicato_id = doc.id
                                    break
                        
                        except AttributoDefinizione.DoesNotExist:
                            # Attributi numero/dataora non configurati, usa fallback
                            pass
                    
                    # Fallback: cerca per dipendente + anno + mese + mensilità (logica precedente)
                    if not is_duplicato and dipendente_esistente:
                        try:
                            attr_def_dipendente = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='dipendente'
                            )
                            attr_def_anno = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='anno_riferimento'
                            )
                            attr_def_mese = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='mese_riferimento'
                            )
                            attr_def_mensilita = AttributoDefinizione.objects.get(
                                tipo_documento=tipo_bpag,
                                codice='mensilita'
                            )
                            
                            # Cerca documenti candidati (stesso anno)
                            anno = parsed['cedolino']['anno']
                            mese = parsed['cedolino']['mese']
                            mensilita = parsed['cedolino']['mensilita']
                            
                            documenti_anno = Documento.objects.filter(
                                tipo=tipo_bpag,
                                data_documento__year=anno
                            ).prefetch_related('attributi_valori')
                            
                            for doc in documenti_anno:
                                attributi = {av.definizione_id: av.valore for av in doc.attributi_valori.all()}
                                
                                # Verifica match attributi
                                if (attributi.get(attr_def_dipendente.id) == str(dipendente_esistente.id) and
                                    attributi.get(attr_def_mese.id) == str(mese) and
                                    attributi.get(attr_def_mensilita.id) == str(mensilita)):
                                    is_duplicato = True
                                    documento_duplicato_id = doc.id
                                    break
                        
                        except AttributoDefinizione.DoesNotExist:
                            pass  # Attributi non configurati, skip controllo duplicati
                    
                    # Costruisci oggetto preview
                    cedolino_preview = {
                        'filename': os.path.basename(pdf_path),
                        'pdf_path': pdf_path,  # Path completo per riuso in confirm
                        'datore': {
                            'codice_fiscale': parsed['datore']['codice_fiscale'],
                            'ragione_sociale': parsed['datore']['ragione_sociale'],
                            'indirizzo': parsed['datore']['indirizzo'],
                            'esistente': datore_esistente is not None,
                            'anagrafica_id': datore_esistente.id if datore_esistente else None,
                        },
                        'lavoratore': {
                            'codice_fiscale': parsed['lavoratore']['codice_fiscale'],
                            'cognome': parsed['lavoratore']['cognome'],
                            'nome': parsed['lavoratore']['nome'],
                            'matricola': parsed['lavoratore']['matricola'],
                            'esistente': dipendente_esistente is not None,
                            'anagrafica_id': dipendente_esistente.id if dipendente_esistente else None,
                        },
                        'cedolino': {
                            'anno': parsed['cedolino']['anno'],
                            'mese': parsed['cedolino']['mese'],
                            'mensilita': parsed['cedolino']['mensilita'],
                            'periodo': parsed['cedolino']['periodo'],
                            'livello': parsed['cedolino']['livello'],
                            'data_documento': parsed['cedolino']['data_documento'].isoformat(),
                        },
                        'duplicato': is_duplicato,
                        'documento_duplicato_id': documento_duplicato_id,
                        # Mappatura dati per visualizzazione preview
                        'attributi_db': {
                            'tipo': 'Libro Unico',
                            'anno_riferimento': parsed['cedolino']['anno'],
                            'mese_riferimento': parsed['cedolino']['mese'],
                            'mensilita': parsed['cedolino']['mensilita'],
                            'dipendente': f"{parsed['lavoratore']['cognome']} {parsed['lavoratore']['nome']}",
                        },
                        'dati_note': {
                            'matricola': parsed['lavoratore'].get('matricola'),
                            'matricola_inps': parsed['lavoratore'].get('matricola_inps'),
                            'data_nascita': parsed['lavoratore'].get('data_nascita'),
                            'data_assunzione': parsed['lavoratore'].get('data_assunzione'),
                            'data_cessazione': parsed['lavoratore'].get('data_cessazione'),
                            'livello': parsed['cedolino'].get('livello'),
                            'netto': parsed['cedolino'].get('netto'),
                            'numero_cedolino': parsed['cedolino'].get('numero_cedolino'),
                            'data_ora_cedolino': parsed['cedolino'].get('data_ora_cedolino'),
                        },
                    }
                    
                    if is_duplicato:
                        duplicati.append(cedolino_preview)
                    else:
                        validi.append(cedolino_preview)
                
                except Exception as e:
                    logger.error(f"Errore processando {os.path.basename(pdf_path)}: {e}", exc_info=True)
                    errori.append({
                        'filename': os.path.basename(pdf_path),
                        'error': str(e)
                    })
            
            # Calcola statistiche aggregate
            nuovi_datori = len(set(
                c['datore']['codice_fiscale']
                for c in validi + duplicati
                if not c['datore']['esistente']
            ))
            
            nuovi_dipendenti = len(set(
                c['lavoratore']['codice_fiscale']
                for c in validi + duplicati
                if not c['lavoratore']['esistente']
            ))
            
            response_data = {
                'temp_dir': temp_dir,
                'totale': len(validi) + len(duplicati) + len(errori),
                'validi': validi,
                'duplicati': duplicati,
                'errori': errori,
                'statistiche': {
                    'nuovi_datori': nuovi_datori,
                    'nuovi_dipendenti': nuovi_dipendenti,
                    'totale_validi': len(validi),
                    'totale_duplicati': len(duplicati),
                    'totale_errori': len(errori),
                }
            }
            
            logger.info(
                f"Preview completata: {len(validi)} validi, "
                f"{len(duplicati)} duplicati, {len(errori)} errori"
            )
            
            return Response(response_data)
        
        except Exception as e:
            # Cleanup in caso errore
            logger.error(f"Errore durante preview cedolini: {e}", exc_info=True)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return Response(
                {'detail': f'Errore durante l\'analisi: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def importa_cedolini_confirm(self, request):
        """
        Step 2: Conferma e importa cedolini da preview.
        
        Endpoint: POST /api/v1/documenti/importa-cedolini-confirm/
        
        Request Body (application/json):
            {
                "temp_dir": "/tmp/cedolini_XXX",
                "cedolini": [...],  # Lista cedolini da preview
                "fascicolo": 123,  # Opzionale: ID fascicolo target
                "duplicate_policy": "skip"  # skip | replace | add
            }
        
        Response:
            {
                "created": 8,
                "replaced": 0,
                "skipped": 2,
                "errors": [],
                "documenti": [...]
            }
        """
        import os
        import shutil
        from django.db import transaction
        from anagrafiche.models import Anagrafica, Cliente
        from anagrafiche.utils import get_or_generate_cli
        from fascicoli.models import Fascicolo
        from titolario.models import TitolarioVoce
        from documenti.models import AttributoValore, AttributoDefinizione
        from django.core.files import File
        
        serializer = CedoliniImportConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        temp_dir = serializer.validated_data['temp_dir']
        cedolini = serializer.validated_data['cedolini']
        fascicolo_id = serializer.validated_data.get('fascicolo')
        duplicate_policy = serializer.validated_data.get('duplicate_policy', 'skip')
        
        # Verifica esistenza temp_dir
        if not os.path.exists(temp_dir):
            return Response(
                {'detail': 'Sessione scaduta. Ricarica il file e riprova.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fascicolo target (se specificato)
        fascicolo_target = None
        if fascicolo_id:
            try:
                fascicolo_target = Fascicolo.objects.get(id=fascicolo_id)
            except Fascicolo.DoesNotExist:
                return Response(
                    {'detail': f'Fascicolo ID {fascicolo_id} non trovato'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Carica configurazioni
        try:
            tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
            voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
        except DocumentiTipo.DoesNotExist:
            return Response(
                {'detail': 'Tipo documento BPAG non configurato'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TitolarioVoce.DoesNotExist:
            return Response(
                {'detail': 'Voce titolario HR-PERS non trovata'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        risultati = {
            'created': 0,
            'replaced': 0,
            'skipped': 0,
            'errors': [],
            'documenti': []
        }
        
        try:
            # Importa ogni cedolino
            for cedolino_data in cedolini:
                try:
                    with transaction.atomic():
                        # 1. Crea/trova anagrafica datore
                        datore_cf = cedolino_data['datore']['codice_fiscale']
                        datore_anagrafica = Anagrafica.objects.filter(codice_fiscale=datore_cf).first()
                        
                        if not datore_anagrafica:
                            # Determina tipo (PG se 11 cifre, PF se 16)
                            tipo_datore = 'PG' if len(datore_cf) == 11 else 'PF'
                            
                            datore_anagrafica = Anagrafica(
                                tipo=tipo_datore,
                                codice_fiscale=datore_cf,
                            )
                            
                            if tipo_datore == 'PG':
                                datore_anagrafica.denominazione = cedolino_data['datore'].get('ragione_sociale') or 'Azienda'
                            else:
                                # PF: estrai nome/cognome da ragione sociale (best effort)
                                rag_soc = cedolino_data['datore'].get('ragione_sociale', '')
                                parts = rag_soc.split(' ', 1)
                                datore_anagrafica.cognome = parts[0] if parts else 'Datore'
                                datore_anagrafica.nome = parts[1] if len(parts) > 1 else ''
                            
                            datore_anagrafica.save()
                            get_or_generate_cli(datore_anagrafica)
                            datore_anagrafica.refresh_from_db()
                            logger.info(f"Creata anagrafica datore: {datore_anagrafica.display_name()}")
                        
                        # 2. Crea/trova cliente datore
                        cliente_datore, created = Cliente.objects.get_or_create(anagrafica=datore_anagrafica)
                        if created:
                            logger.info(f"Creato cliente datore: {cliente_datore}")
                        
                        # 3. Crea/trova anagrafica dipendente
                        dipendente_cf = cedolino_data['lavoratore']['codice_fiscale']
                        dipendente_anagrafica = Anagrafica.objects.filter(codice_fiscale=dipendente_cf).first()
                        
                        if not dipendente_anagrafica:
                            dipendente_anagrafica = Anagrafica(
                                tipo='PF',
                                codice_fiscale=dipendente_cf,
                                cognome=cedolino_data['lavoratore']['cognome'],
                                nome=cedolino_data['lavoratore']['nome'],
                            )
                            dipendente_anagrafica.save()
                            get_or_generate_cli(dipendente_anagrafica)
                            dipendente_anagrafica.refresh_from_db()
                            logger.info(f"Creata anagrafica dipendente: {dipendente_anagrafica.display_name()}")
                        
                        # 4. Crea/trova voce titolario intestata dipendente
                        if not dipendente_anagrafica.codice:
                            get_or_generate_cli(dipendente_anagrafica)
                            dipendente_anagrafica.refresh_from_db()
                        
                        voce_dipendente = TitolarioVoce.objects.filter(
                            parent=voce_hr_pers,
                            codice=dipendente_anagrafica.codice
                        ).first()
                        
                        if not voce_dipendente:
                            voce_dipendente = TitolarioVoce.objects.create(
                                codice=dipendente_anagrafica.codice,
                                titolo=f"Dossier {dipendente_anagrafica.display_name()}",
                                parent=voce_hr_pers,
                                anagrafica=dipendente_anagrafica,
                                pattern_codice='{CLI}-{ANA}-BPAG-{ANNO}-{SEQ:03d}',
                                consente_intestazione=False
                            )
                            logger.info(f"Creata voce titolario: {voce_dipendente.codice}")
                        elif voce_dipendente.anagrafica_id != dipendente_anagrafica.id:
                            voce_dipendente.anagrafica = dipendente_anagrafica
                            voce_dipendente.save(update_fields=['anagrafica'])
                        
                        # 5. Determina fascicolo
                        if fascicolo_target:
                            fascicolo = fascicolo_target
                        else:
                            # Fascicolo automatico: "Paghe {mese} {anno}"
                            anno = cedolino_data['cedolino']['anno']
                            mese = cedolino_data['cedolino']['mese']
                            
                            mesi_abbr = {
                                1: 'gen', 2: 'feb', 3: 'mar', 4: 'apr',
                                5: 'mag', 6: 'giu', 7: 'lug', 8: 'ago',
                                9: 'set', 10: 'ott', 11: 'nov', 12: 'dic',
                            }
                            mese_nome = mesi_abbr.get(mese, 'gen')
                            titolo_fascicolo = f"Paghe {mese_nome} {anno}"
                            
                            # Cerca fascicolo esistente per cliente + periodo
                            fascicolo = Fascicolo.objects.filter(
                                cliente=cliente_datore,
                                anno=anno,
                                titolo__icontains=f"{mese_nome} {anno}"
                            ).first()
                            
                            if not fascicolo:
                                # Crea fascicolo (usa voce PAG se esiste, altrimenti nessuna voce)
                                voce_pag = TitolarioVoce.objects.filter(codice='PAG').first()
                                
                                fascicolo = Fascicolo.objects.create(
                                    cliente=cliente_datore,
                                    titolario_voce=voce_pag,
                                    titolo=titolo_fascicolo,
                                    anno=anno,
                                    ubicazione=None,
                                )
                                logger.info(f"Creato fascicolo: {fascicolo.titolo}")
                        
                        # 6. Controlla duplicato e gestisci policy
                        documento_esistente = None
                        if cedolino_data.get('duplicato') and cedolino_data.get('documento_duplicato_id'):
                            try:
                                documento_esistente = Documento.objects.get(id=cedolino_data['documento_duplicato_id'])
                            except Documento.DoesNotExist:
                                pass
                        
                        if documento_esistente:
                            if duplicate_policy == 'skip':
                                risultati['skipped'] += 1
                                logger.info(f"Cedolino saltato (duplicato): {cedolino_data['filename']}")
                                continue  # Salta questo cedolino
                            
                            elif duplicate_policy == 'replace':
                                # Sostituisci documento esistente
                                documento = documento_esistente
                                
                                # Elimina vecchio file
                                if documento.file:
                                    try:
                                        documento.file.delete(save=False)
                                    except:
                                        pass
                                
                                # Aggiorna campi
                                documento.descrizione = f"Cedolino {cedolino_data['lavoratore']['cognome'].upper()} {cedolino_data['lavoratore']['nome'].upper()} - {cedolino_data['cedolino']['periodo']}"
                                documento.data_documento = cedolino_data['cedolino']['data_documento']
                                documento.fascicolo = fascicolo
                                documento.titolario_voce = voce_dipendente
                                
                                # Carica nuovo file
                                pdf_path = cedolino_data['pdf_path']
                                with open(pdf_path, 'rb') as f:
                                    documento.file.save(os.path.basename(pdf_path), File(f), save=False)
                                
                                documento.save()
                                
                                # Aggiorna attributi (delete + ricrea)
                                AttributoValore.objects.filter(documento=documento).delete()
                                
                                risultati['replaced'] += 1
                                action = 'sostituito'
                        
                        # Crea nuovo documento (duplicate_policy='add' O nessun duplicato)
                        if not documento_esistente or duplicate_policy == 'add':
                            # Crea documento
                            from datetime import datetime
                            
                            descrizione = f"Cedolino {cedolino_data['lavoratore']['cognome'].upper()} {cedolino_data['lavoratore']['nome'].upper()} - {cedolino_data['cedolino']['periodo']}"
                            
                            documento = Documento(
                                tipo=tipo_bpag,
                                cliente=cliente_datore,
                                fascicolo=fascicolo,
                                titolario_voce=voce_dipendente,
                                descrizione=descrizione,
                                data_documento=cedolino_data['cedolino']['data_documento'],
                                stato=Documento.Stato.DEFINITIVO,
                                digitale=True,
                                tracciabile=True,
                            )
                            
                            # Carica file PDF
                            pdf_path = cedolino_data['pdf_path']
                            with open(pdf_path, 'rb') as f:
                                documento.file.save(os.path.basename(pdf_path), File(f), save=False)
                            
                            documento.save()
                            
                            risultati['created'] += 1
                            action = 'creato'
                        
                        # 7. Salva attributi dinamici
                        attributi_def = {
                            attr.codice: attr
                            for attr in AttributoDefinizione.objects.filter(tipo_documento=tipo_bpag)
                        }
                        
                        valori_attributi = {
                            'tipo': 'Libro Unico',
                            'anno_riferimento': cedolino_data['cedolino']['anno'],
                            'mese_riferimento': cedolino_data['cedolino']['mese'],
                            'mensilita': cedolino_data['cedolino']['mensilita'],
                            'dipendente': dipendente_anagrafica.id,
                        }
                        
                        for codice, valore in valori_attributi.items():
                            if codice in attributi_def:
                                AttributoValore.objects.create(
                                    documento=documento,
                                    definizione=attributi_def[codice],
                                    valore=str(valore)
                                )
                        
                        # 8. Rigenera codice se usa attributi
                        if '{ATTR:' in (voce_dipendente.pattern_codice or ''):
                            documento.rigenera_codice_con_attributi()
                        
                        # Aggiungi a risultati
                        risultati['documenti'].append({
                            'id': documento.id,
                            'codice': documento.codice,
                            'descrizione': documento.descrizione,
                            'filename': cedolino_data['filename'],
                            'action': action,
                        })
                        
                        logger.info(f"Cedolino {action}: {documento.codice}")
                
                except Exception as e:
                    logger.error(f"Errore importando {cedolino_data['filename']}: {e}", exc_info=True)
                    risultati['errors'].append({
                        'filename': cedolino_data['filename'],
                        'error': str(e)
                    })
            
            return Response(risultati)
        
        finally:
            # Cleanup directory temporanea
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Directory temporanea eliminata: {temp_dir}")
    
    @action(detail=False, methods=['post'])
    def importa_cedolini(self, request):
        """
        Importa cedolini paga da file ZIP.
        
        Endpoint: POST /api/v1/documenti/importa-cedolini/
        
        Request Body (multipart/form-data):
            - file: File ZIP contenente i cedolini PDF
            - duplicate_policy: (opzionale) Gestione duplicati: 'skip' | 'replace' | 'add'
                * skip: Non importare se documento già esiste (default)
                * replace: Sostituire documento esistente
                * add: Aggiungere comunque il documento (crea duplicato)
        
        Response:
            {
                "created": 6,
                "replaced": 0,
                "skipped": 0,
                "errors": [],
                "warnings": [],
                "documenti": [
                    {"id": 123, "codice": "CLI001-BPAG-2025-001", "descrizione": "...", "filename": "..."},
                    ...
                ]
            }
        """
        serializer = ImportaCedoliniSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        zip_file = serializer.validated_data['file']
        duplicate_policy = serializer.validated_data.get('duplicate_policy', 'skip')
        
        # Importa cedolini usando la classe CedolinoImporter
        from documenti.import_cedolini import CedolinoImporter
        
        importer = CedolinoImporter(
            zip_file, 
            user=request.user,
            duplicate_policy=duplicate_policy
        )
        risultati = importer.importa()
        
        # Determina status code
        total_processed = risultati.get('created', 0) + risultati.get('replaced', 0) + risultati.get('skipped', 0)
        if total_processed == 0 and risultati['errors']:
            status_code = status.HTTP_400_BAD_REQUEST
        elif risultati['errors']:
            status_code = status.HTTP_207_MULTI_STATUS  # Partial success
        else:
            status_code = status.HTTP_201_CREATED
        
        return Response(risultati, status=status_code)

    @action(
        detail=False, 
        methods=['post'], 
        url_path='importa-zip-libro-unico',
        parser_classes=[MultiPartParser, FormParser]
    )
    def importa_zip_libro_unico(self, request):
        """
        Importa un file ZIP contenente cedolini come singolo documento LIBUNI.
        
        POST /api/v1/documenti/importa-zip-libro-unico/
        
        Body (multipart/form-data):
            - file: ZIP file (opzionale se fornito session_uuid)
            - session_uuid: UUID sessione import (opzionale se fornito file)
            - azione_duplicati: 'sostituisci' | 'duplica' | 'skip' (default: 'duplica')
        
        Response:
            {
                "success": true,
                "documento_id": 123,
                "duplicato": false,
                "azione": "creato",  # o "sostituito", "duplicato", "skipped"
                "metadati": {
                    "titolo": "Libro Unico Aprile 2025 - ARKLABS SRL",
                    "periodo": "Aprile 2025",
                    "anno": 2025,
                    "mese": 4,
                    "cliente": "ARKLABS SRL",
                    "num_cedolini": 15,
                    "dipendenti": ["Mario Rossi", "Luca Bianchi", ...]
                },
                "errori": []
            }
        """
        from .importa_libro_unico import importa_zip_come_libro_unico
        from .serializers import ImportaZipLibroUnicoSerializer
        from documenti.models import ImportSession
        
        serializer = ImportaZipLibroUnicoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zip_file = serializer.validated_data.get('file')
        session_uuid = serializer.validated_data.get('session_uuid')
        azione_duplicati = serializer.validated_data.get('azione_duplicati', 'duplica')
        
        # Se fornito session_uuid, recupera il file originale dalla sessione
        if session_uuid:
            try:
                session = ImportSession.objects.get(uuid=session_uuid)
                if not session.file_originale:
                    return Response(
                        {'errori': ['La sessione non ha un file originale associato']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Usa direttamente il file dalla sessione
                zip_file = session.file_originale
                logger.info(f"Importazione ZIP libro unico da sessione {session_uuid}: {zip_file.name}, azione={azione_duplicati}")
            except ImportSession.DoesNotExist:
                return Response(
                    {'errori': ['Sessione di import non trovata']},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            logger.info(f"Importazione ZIP libro unico da file uploadato: {zip_file.name}, azione={azione_duplicati}")
        
        # Esegui importazione
        try:
            risultato = importa_zip_come_libro_unico(
                zip_file=zip_file,
                azione_duplicati=azione_duplicati,
                user=request.user
            )
        except Exception as e:
            logger.error(f"Errore importazione ZIP libro unico: {e}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'errori': [f"Errore durante l'importazione: {str(e)}"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if risultato['success']:
            return Response(risultato, status=status.HTTP_201_CREATED)
        else:
            return Response(
                risultato,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(
        detail=False,
        methods=['post'],
        url_path='importa-zip-cu',
        parser_classes=[MultiPartParser, FormParser]
    )
    def importa_zip_cu(self, request):
        """
        Importa un file ZIP contenente certificazioni uniche come singolo documento CU-ZIP.
        
        POST /api/v1/documenti/importa-zip-cu/
        
        Body (multipart/form-data):
            - file: ZIP file (opzionale se fornito session_uuid)
            - session_uuid: UUID sessione import (opzionale se fornito file)
            - azione_duplicati: 'sostituisci' | 'duplica' | 'skip' (default: 'duplica')
        
        Response:
            {
                "success": true,
                "documento_id": 789,
                "duplicato": false,
                "azione": "creato",  # o "sostituito", "duplicato", "skipped"
                "metadati": {
                    "titolo": "Archivio CU 2025 - ACME SRL",
                    "anno_imposta": 2025,
                    "datore": "ACME SRL",
                    "datore_cf": "12345678901",
                    "num_certificazioni": 45,
                    "dipendenti": ["BIANCHI LUCA", "ROSSI MARIO", ...]
                },
                "errori": []
            }
        """
        from .importa_zip_cu import importa_zip_come_cu
        from .serializers import ImportaZipCUSerializer
        from documenti.models import ImportSession
        
        serializer = ImportaZipCUSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zip_file = serializer.validated_data.get('file')
        session_uuid = serializer.validated_data.get('session_uuid')
        azione_duplicati = serializer.validated_data.get('azione_duplicati', 'duplica')
        
        # Se fornito session_uuid, recupera il file originale dalla sessione
        if session_uuid:
            try:
                session = ImportSession.objects.get(uuid=session_uuid)
                if not session.file_originale:
                    return Response(
                        {'errori': ['La sessione non ha un file originale associato']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Usa direttamente il file dalla sessione
                zip_file = session.file_originale
                logger.info(f"Importazione ZIP CU da sessione {session_uuid}: {zip_file.name}, azione={azione_duplicati}")
            except ImportSession.DoesNotExist:
                return Response(
                    {'errori': ['Sessione di import non trovata']},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            logger.info(f"Importazione ZIP CU da file uploadato: {zip_file.name}, azione={azione_duplicati}")
        
        # Esegui importazione
        try:
            risultato = importa_zip_come_cu(
                zip_file=zip_file,
                azione_duplicati=azione_duplicati,
                user=request.user
            )
        except Exception as e:
            logger.error(f"Errore importazione ZIP CU: {e}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'errori': [f"Errore durante l'importazione: {str(e)}"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if risultato['success']:
            return Response(risultato, status=status.HTTP_201_CREATED)
        else:
            return Response(
                risultato,
                status=status.HTTP_400_BAD_REQUEST
            )


class DocumentiTipoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet per tipi documento (sola lettura)
    """
    permission_classes = [IsAuthenticated]
    queryset = DocumentiTipo.objects.filter(attivo=True).order_by('codice')
    serializer_class = DocumentiTipoSerializer
    pagination_class = None  # Disabilita paginazione per lista tipi
    
    def get_queryset(self):
        """
        Filtra help in base ai permessi utente.
        Admin vedono tutto, altri solo help completi/parziali.
        """
        queryset = super().get_queryset()
        
        # Admin vedono tutto
        if self.request.user.is_staff or self.request.user.is_superuser:
            return queryset
        
        # Non-admin vedono solo help visibili pubblicamente
        # Filtra in Python dopo perché il check è su JSONField
        return queryset  # Filtro applicato nel serializer
    
    @action(detail=True, methods=['get'])
    def attributi(self, request, pk=None):
        """Ottieni attributi per tipo documento"""
        tipo = self.get_object()
        attributi = AttributoDefinizione.objects.filter(
            tipo_documento=tipo
        ).order_by('ordine', 'codice')
        serializer = AttributoDefinizioneSerializer(attributi, many=True)
        return Response({
            'tipo': DocumentiTipoSerializer(tipo).data,
            'attributi': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def with_help(self, request):
        """
        Lista tipi documento con help configurato.
        Admin vedono tutti, altri solo quelli pubblici.
        """
        from documenti.help_builder import get_help_status, is_help_visible_to_public
        
        queryset = self.get_queryset()
        is_admin = request.user.is_staff or request.user.is_superuser
        
        # Filtra tipi con help
        tipi_con_help = []
        for tipo in queryset:
            if not tipo.help_data:
                continue
            
            # Admin vedono tutto
            if is_admin:
                tipi_con_help.append(tipo)
            # Non-admin solo help pubblici
            elif is_help_visible_to_public(tipo.help_data):
                tipi_con_help.append(tipo)
        
        serializer = self.get_serializer(tipi_con_help, many=True)
        return Response({
            'count': len(tipi_con_help),
            'is_admin': is_admin,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def missing_help(self, request):
        """
        Lista tipi documento senza help configurato.
        Solo per admin.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'detail': 'Solo amministratori possono vedere questa lista'},
                status=403
            )
        
        queryset = self.get_queryset()
        tipi_senza_help = [
            tipo for tipo in queryset 
            if not tipo.help_data or len(tipo.help_data) == 0
        ]
        
        serializer = self.get_serializer(tipi_senza_help, many=True)
        return Response({
            'count': len(tipi_senza_help),
            'results': serializer.data
        })


# ============================================
# ViewSet per Import Sessions
# ============================================

from documenti.models import ImportSession, ImportSessionDocument
from documenti.importers import ImporterRegistry
from .serializers import (
    ImportSessionListSerializer,
    ImportSessionDetailSerializer,
    ImportSessionCreateSerializer,
    ImportSessionDocumentSerializer,
    ImportDocumentUpdateSerializer,
    ImportDocumentCreateSerializer,
    ImporterTypeSerializer,
)


class ImportSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione sessioni di importazione.
    
    Endpoints:
    - GET /import-sessions/ - Lista sessioni utente
    - POST /import-sessions/ - Crea nuova sessione (upload file)
    - GET /import-sessions/{uuid}/ - Dettaglio sessione con documenti
    - DELETE /import-sessions/{uuid}/ - Elimina sessione
    - GET /import-sessions/types/ - Lista tipi importazione disponibili
    - GET /import-sessions/{uuid}/documents/ - Lista documenti sessione
    - GET /import-sessions/{uuid}/documents/{doc_uuid}/ - Dettaglio documento
    - PATCH /import-sessions/{uuid}/documents/{doc_uuid}/ - Aggiorna valori editabili
    - POST /import-sessions/{uuid}/documents/{doc_uuid}/create/ - Crea documento
    - POST /import-sessions/{uuid}/documents/{doc_uuid}/skip/ - Salta documento
    """
    
    permission_classes = [RBACPermission]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Lista solo sessioni dell'utente corrente (già filtrato per user)"""
        return ImportSession.objects.filter(
            utente=self.request.user
        ).prefetch_related('documents')
    
    def get_serializer_class(self):
        """Serializer diverso per list/detail"""
        if self.action == 'list':
            return ImportSessionListSerializer
        elif self.action == 'create':
            return ImportSessionCreateSerializer
        else:
            return ImportSessionDetailSerializer
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """
        GET /api/v1/import-sessions/types/
        
        Lista tipi di importazione disponibili con info su estensioni supportate.
        """
        types_info = ImporterRegistry.get_all_types()
        serializer = ImporterTypeSerializer(types_info, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/v1/import-sessions/
        
        Crea nuova sessione di importazione:
        1. Salva file caricato
        2. Estrae documenti (se ZIP)
        3. Parsa ogni documento
        4. Ritorna sessione con lista documenti
        
        Body:
            tipo_importazione: str (cedolini, unilav, f24, etc.)
            file: File (PDF o ZIP)
        """
        print("=" * 80)
        print("🚀 ImportSessionViewSet.create() AVVIATO")
        print("=" * 80)
        logger.info("🚀 ImportSessionViewSet.create() AVVIATO")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tipo = serializer.validated_data['tipo_importazione']
        file = serializer.validated_data['file']
        
        print(f"📁 File upload: {file.name}, tipo: {tipo}")
        logger.info(f"📁 File upload: {file.name}, tipo: {tipo}")
        
        try:
            # Crea sessione
            session = ImportSession.objects.create(
                tipo_importazione=tipo,
                file_originale=file,
                file_originale_nome=file.name,
                utente=request.user,
            )
            
            logger.info(
                f"Creata sessione {session.uuid} per utente {request.user.username}: "
                f"{tipo} - {file.name}"
            )
            
            # Recupera importer
            importer_class = ImporterRegistry.get_importer(tipo)
            importer = importer_class(session)
            
            # Estrai documenti dal file
            try:
                print(f"📦 EXTRACT: Avvio estrazione documenti da {file.name}...")
                logger.info(f"📦 Avvio estrazione documenti da {file.name}...")

                # Scarica dal storage (locale o R2) in un temp file per il processing locale
                ext = os.path.splitext(session.file_originale_nome)[1].lower() or '.bin'
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as _tmp:
                    _tmp_path = _tmp.name
                try:
                    with session.file_originale.open('rb') as _src:
                        with open(_tmp_path, 'wb') as _dst:
                            shutil.copyfileobj(_src, _dst)
                    extracted_docs = importer.extract_documents(_tmp_path)
                finally:
                    if os.path.exists(_tmp_path):
                        os.unlink(_tmp_path)

                print(f"✅ EXTRACT: Estratti {len(extracted_docs)} documenti")
                logger.info(f"✅ Estratti {len(extracted_docs)} documenti da {file.name}")
            except Exception as e:
                logger.error(f"❌ Errore estrazione documenti: {e}", exc_info=True)
                session.delete()
                return Response(
                    {'error': f'Errore estrazione documenti: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crea ImportSessionDocument per ogni file estratto
            print(f"📝 CREATE: Creazione di {len(extracted_docs)} ImportSessionDocument...")
            logger.info(f"📝 Creazione di {len(extracted_docs)} ImportSessionDocument...")
            session_docs = []
            for idx, doc_info in enumerate(extracted_docs):
                print(f"   CREATE: {idx+1}/{len(extracted_docs)}: {doc_info['filename']}")
                logger.debug(f"   Creando ImportSessionDocument {idx+1}/{len(extracted_docs)}: {doc_info['filename']}")
                session_doc = ImportSessionDocument.objects.create(
                    session=session,
                    filename=doc_info['filename'],
                    file_path=doc_info['file_path'],
                    file_size=doc_info.get('file_size', 0),
                    ordine=doc_info.get('ordine', 0),
                )
                session_docs.append(session_doc)
            
            print(f"✅ CREATE: Creati {len(session_docs)} ImportSessionDocument")
            print(f"🔄 PARSE: Avvio parsing di {len(session_docs)} documenti...")
            logger.info(f"✅ Creati {len(session_docs)} ImportSessionDocument")
            logger.info(f"🔄 Avvio parsing di {len(session_docs)} documenti...")
            
            # Parsa ogni documento
            for session_doc in session_docs:
                try:
                    print(f"🔄 PARSE: Inizio parsing {session_doc.filename}")
                    logger.info(f"🔄 Inizio parsing: {session_doc.filename}")
                    parse_result = importer.parse_document(
                        session_doc.file_path,
                        session_doc.filename
                    )
                    print(f"✅ PARSE: parse_document() terminato per {session_doc.filename}")
                    logger.info(f"✅ parse_document() completato per {session_doc.filename}")
                    logger.debug(f"   parse_result type: {type(parse_result)}, success: {parse_result.success if parse_result else 'None'}")
                    
                    if parse_result.success:
                        session_doc.parsed_data = parse_result.parsed_data
                        session_doc.anagrafiche_reperite = parse_result.anagrafiche_reperite
                        session_doc.valori_editabili = parse_result.valori_editabili
                        session_doc.mappatura_db = parse_result.mappatura_db
                        session_doc.parsed_at = timezone.now()
                        
                        print(f"💾 SAVE: Salvando {session_doc.filename}...")
                        logger.info(f"💾 Salvando documento parsato: {session_doc.filename}...")
                        try:
                            session_doc.save()
                            print(f"✅ SAVE: OK per {session_doc.filename}")
                            logger.info(f"✅ Parsed OK: {session_doc.filename}")
                        except Exception as e_save:
                            print(f"❌ SAVE: ERRORE per {session_doc.filename}: {e_save}")
                            logger.error(f"❌ ERRORE SAVE documento {session_doc.filename}: {e_save}", exc_info=True)
                            raise
                    else:
                        print(f"⚠️  PARSE: Errore per {session_doc.filename}: {parse_result.error_message}")
                        session_doc.mark_as_error(
                            parse_result.error_message,
                            parse_result.error_traceback
                        )
                        logger.warning(f"Errore parsing {session_doc.filename}: {parse_result.error_message}")
                    
                except Exception as e:
                    print(f"❌ EXCEPTION: {session_doc.filename}: {e}")
                    import traceback
                    error_traceback = traceback.format_exc()
                    session_doc.mark_as_error(str(e), error_traceback)
                    logger.error(f"Eccezione parsing {session_doc.filename}: {e}")
            
            # Aggiorna statistiche sessione
            print(f"🎯 FINALE: Parsing completato, salvataggio sessione...")
            logger.info(f"Parsing completato per {len(session_docs)} documenti. Salvataggio sessione...")
            session.save()
            print(f"✅ FINALE: Sessione salvata, preparazione risposta...")
            logger.info(f"✅ Sessione {session.uuid} salvata. Preparazione risposta HTTP...")
            
            # Ritorna dettaglio sessione
            try:
                print(f"📤 SERIALIZER: Serializzazione sessione...")
                output_serializer = ImportSessionDetailSerializer(session)
                print(f"✅ SERIALIZER: OK, invio risposta HTTP 201...")
                logger.info("✅ Serializzazione completata. Invio risposta al client...")
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e_ser:
                logger.error(f"❌ ERRORE SERIALIZZAZIONE: {e_ser}", exc_info=True)
                raise
            
        except Exception as e:
            logger.error(f"Errore creazione sessione: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Errore creazione sessione: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, uuid=None):
        """
        DELETE /api/v1/import-sessions/{uuid}/
        
        Elimina sessione e cleanup file temporanei.
        """
        session = self.get_object()
        
        # Cleanup temp directory
        import shutil
        if session.temp_dir and os.path.exists(session.temp_dir):
            try:
                shutil.rmtree(session.temp_dir)
                logger.info(f"Rimossa directory temporanea: {session.temp_dir}")
            except Exception as e:
                logger.warning(f"Errore rimozione temp_dir {session.temp_dir}: {e}")
        
        session.delete()
        logger.info(f"Eliminata sessione {uuid}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, uuid=None):
        """
        GET /api/v1/import-sessions/{uuid}/documents/
        
        Lista documenti della sessione con filtro opzionale per stato.
        
        Query params:
            stato: pending|imported|skipped|error
        """
        session = self.get_object()
        documents = session.documents.all()
        
        # Filtro per stato
        stato = request.query_params.get('stato')
        if stato:
            documents = documents.filter(stato=stato)
        
        serializer = ImportSessionDocumentSerializer(
            documents, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='documents/(?P<doc_uuid>[^/.]+)')
    def document_detail(self, request, uuid=None, doc_uuid=None):
        """
        GET /api/v1/import-sessions/{uuid}/documents/{doc_uuid}/
        
        Dettaglio singolo documento della sessione.
        """
        session = self.get_object()
        try:
            document = session.documents.get(uuid=doc_uuid)
        except ImportSessionDocument.DoesNotExist:
            return Response(
                {'error': 'Documento non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ImportSessionDocumentSerializer(
            document,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='check-duplicates')
    def check_duplicates(self, request, uuid=None):
        """
        GET /api/v1/import-sessions/{uuid}/check-duplicates/
        
        Verifica duplicati per tutti i documenti pending della sessione in batch.
        
        Returns:
            {
              "duplicates": {
                "doc_uuid_1": {
                  "is_duplicate": true,
                  "duplicate_info": {...}
                },
                "doc_uuid_2": {
                  "is_duplicate": false
                }
              }
            }
        """
        session = self.get_object()
        
        # Solo documenti pending (non già importati/skippati)
        pending_docs = session.documents.filter(stato='pending')
        
        result = {'duplicates': {}}
        
        for doc in pending_docs:
            try:
                # Recupera importer
                importer_class = ImporterRegistry.get_importer(session.tipo_importazione)
                importer = importer_class(session)
                
                # Verifica duplicato usando il servizio generico
                duplicate_info = importer.check_duplicate(
                    parsed_data=doc.parsed_data,
                    valori_editabili=doc.valori_editabili
                )
                
                result['duplicates'][str(doc.uuid)] = duplicate_info
                
            except Exception as e:
                logger.error(f"Errore check duplicato per {doc.uuid}: {e}")
                result['duplicates'][str(doc.uuid)] = {
                    'is_duplicate': False,
                    'error': str(e)
                }
        
        return Response(result)
    
    @action(detail=True, methods=['patch'], url_path='documents/(?P<doc_uuid>[^/.]+)')
    def update_document(self, request, uuid=None, doc_uuid=None):
        """
        PATCH /api/v1/import-sessions/{uuid}/documents/{doc_uuid}/
        
        Aggiorna valori editabili del documento (modifiche utente prima importazione).
        
        Body:
            valori_editabili: dict
        """
        session = self.get_object()
        try:
            document = session.documents.get(uuid=doc_uuid)
        except ImportSessionDocument.DoesNotExist:
            return Response(
                {'error': 'Documento non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ImportDocumentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Aggiorna valori editabili
        document.valori_editabili = serializer.validated_data['valori_editabili']
        document.save()
        
        logger.info(f"Aggiornati valori editabili per documento {doc_uuid}")
        
        output_serializer = ImportSessionDocumentSerializer(document)
        return Response(output_serializer.data)
    
    @action(detail=True, methods=['post'], url_path='documents/(?P<doc_uuid>[^/.]+)/create')
    def create_document(self, request, uuid=None, doc_uuid=None):
        """
        POST /api/v1/import-sessions/{uuid}/documents/{doc_uuid}/create/
        
        Crea documento nel DB dal documento parsato.
        
        Body (opzionale):
            valori_editabili: dict (override valori parsati)
            cliente_id: int (opzionale)
            fascicolo_id: int (opzionale)
        """
        session = self.get_object()
        try:
            session_doc = session.documents.get(uuid=doc_uuid)
        except ImportSessionDocument.DoesNotExist:
            return Response(
                {'error': 'Documento non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verifica stato
        if session_doc.stato != 'pending':
            return Response(
                {'error': f'Documento già processato (stato: {session_doc.get_stato_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ImportDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Merge valori editabili
        valori_editabili = {
            **session_doc.valori_editabili,
            **serializer.validated_data.get('valori_editabili', {})
        }
        
        # Policy gestione duplicati
        duplicate_policy = serializer.validated_data.get('duplicate_policy', 'skip')
        
        try:
            # Recupera importer e crea documento
            importer_class = ImporterRegistry.get_importer(session.tipo_importazione)
            importer = importer_class(session)
            
            # Verifica duplicati se policy non è 'add' (aggiungi sempre)
            if duplicate_policy != 'add':
                # Check duplicato
                if hasattr(importer, 'check_duplicate'):
                    duplicate_result = importer.check_duplicate(
                        parsed_data=session_doc.parsed_data,
                        valori_editabili=valori_editabili
                    )
                    
                    if duplicate_result and duplicate_result.get('is_duplicate'):
                        # Se policy è 'skip', restituisci 409 Conflict
                        if duplicate_policy == 'skip':
                            return Response({
                                'error': 'Documento duplicato',
                                'error_type': 'duplicate',
                                'duplicate_info': duplicate_result.get('duplicate_info'),
                                'message': 'Documento già presente. Seleziona una policy diversa per continuare.'
                            }, status=status.HTTP_409_CONFLICT)
                        
                        # Se policy è 'replace', elimina documento esistente
                        elif duplicate_policy == 'replace':
                            try:
                                from documenti.models import Documento
                                doc_id = duplicate_result.get('duplicate_info', {}).get('id')
                                if doc_id:
                                    doc_esistente = Documento.objects.get(id=doc_id)
                                    logger.info(f"Elimino documento esistente {doc_esistente.codice} (ID={doc_id}) per sostituzione")
                                    doc_esistente.delete()
                            except Exception as e_del:
                                logger.error(f"Errore eliminazione documento esistente: {e_del}")
                                return Response({
                                    'error': f'Errore eliminazione documento esistente: {str(e_del)}'
                                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            documento = importer.create_documento(
                parsed_data=session_doc.parsed_data,
                valori_editati=valori_editabili,
                user=request.user,
                cliente_id=serializer.validated_data.get('cliente_id'),
                fascicolo_id=serializer.validated_data.get('fascicolo_id'),
                file_path=session_doc.file_path,  # Passa il path del file originale
            )
            
            # Marca come importato
            session_doc.mark_as_imported(documento)
            
            logger.info(f"Creato documento {documento.id} da session_doc {doc_uuid}")
            
            return Response({
                'success': True,
                'documento': {
                    'id': documento.id,
                    'codice': documento.codice,
                    'descrizione': documento.descrizione,
                    'tipo': documento.tipo.codice if documento.tipo else None,
                },
                'session_document': ImportSessionDocumentSerializer(
                    session_doc,
                    context={'request': request}
                ).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            from documenti.importers.cedolini import DocumentoDuplicatoError
            
            logger.error(f"Errore creazione documento da {doc_uuid}: {e}")
            
            # ✅ Gestione specifica per duplicati (NON marcare come errore)
            if isinstance(e, DocumentoDuplicatoError):
                # Non marchiamo come errore - l'utente può riprovare o skippare
                return Response({
                    'error': str(e),
                    'error_type': 'duplicate',
                    'duplicate_info': {
                        'id': e.documento_esistente.id if e.documento_esistente else None,
                        'codice': e.dettagli.get('codice'),
                        'numero_cedolino': e.dettagli.get('numero_cedolino'),
                        'data_ora_cedolino': e.dettagli.get('data_ora_cedolino'),
                        'confidence': e.dettagli.get('confidence'),
                        'matched_fields': e.dettagli.get('matched_fields'),
                    }
                }, status=status.HTTP_409_CONFLICT)  # 409 = Conflict (più appropriato per duplicati)
            
            # Altri errori: marca come errore e restituisci traceback
            error_traceback = traceback.format_exc()
            session_doc.mark_as_error(str(e), error_traceback)
            
            return Response(
                {'error': str(e), 'traceback': error_traceback},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='documents/(?P<doc_uuid>[^/.]+)/skip')
    def skip_document(self, request, uuid=None, doc_uuid=None):
        """
        POST /api/v1/import-sessions/{uuid}/documents/{doc_uuid}/skip/
        
        Salta importazione del documento.
        """
        session = self.get_object()
        try:
            session_doc = session.documents.get(uuid=doc_uuid)
        except ImportSessionDocument.DoesNotExist:
            return Response(
                {'error': 'Documento non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        session_doc.mark_as_skipped()
        logger.info(f"Documento {doc_uuid} saltato")
        
        output_serializer = ImportSessionDocumentSerializer(
            session_doc,
            context={'request': request}
        )
        return Response(output_serializer.data)
    
    @method_decorator(xframe_options_exempt)
    @action(
        detail=True, 
        methods=['get'], 
        url_path='documents/(?P<doc_uuid>[^/.]+)/preview',
        permission_classes=[AllowSignedTokenOrAuthenticated]
    )
    def preview_document_file(self, request, uuid=None, doc_uuid=None):
        """
        GET /api/v1/import-sessions/{uuid}/documents/{doc_uuid}/preview/?token=<signed_token>
        
        Serve il file PDF per preview in browser.
        
        Autenticazione: Accetta token signed nell'URL (per iframe) oppure 
        autenticazione normale (JWT/Session).
        
        La validazione dell'autenticazione è gestita da AllowSignedTokenOrAuthenticated.
        """
        from django.http import FileResponse, Http404
        from django.core.signing import TimestampSigner, BadSignature
        import mimetypes
        
        # Se c'è un token nell'URL, verifica che corrisponda agli UUID
        token = request.GET.get('token')
        if token:
            try:
                signer = TimestampSigner()
                unsigned_value = signer.unsign(token, max_age=300)
                token_parts = unsigned_value.split(':')
                if len(token_parts) == 3:
                    token_session_uuid, token_doc_uuid, _ = token_parts
                    if token_session_uuid != str(uuid) or token_doc_uuid != str(doc_uuid):
                        raise Http404("Token non corrisponde alla risorsa richiesta")
            except (BadSignature, ValueError):
                raise Http404("Token non valido")
        
        # Recupera la sessione (permission già verificata)
        session = self.get_object()
        try:
            session_doc = session.documents.get(uuid=doc_uuid)
        except ImportSessionDocument.DoesNotExist:
            raise Http404("Documento non trovato")
        
        # Verifica che il file esista
        if not session_doc.file_path or not os.path.exists(session_doc.file_path):
            raise Http404("File non trovato")
        
        # Determina content type
        content_type, _ = mimetypes.guess_type(session_doc.file_path)
        if not content_type:
            content_type = 'application/pdf'
        
        # Apri file e restituisci response
        try:
            file_handle = open(session_doc.file_path, 'rb')
            response = FileResponse(file_handle, content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{session_doc.filename}"'
            return response
        except Exception as e:
            logger.error(f"Errore apertura file {session_doc.file_path}: {e}")
            raise Http404("Errore apertura file")



