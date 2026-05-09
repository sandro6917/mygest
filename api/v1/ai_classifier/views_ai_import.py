"""
Views per AI-Assisted Document Import
"""
import logging
import os
import tempfile
import re
from decimal import Decimal
from typing import Dict, List, Any
from PIL import Image
import pdfplumber

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from ai_classifier.models import (
    DocumentExtractionTemplate,
    ExtractionTemplatePage,
    ExtractionTemplateZone,
    ExtractionFieldMapping,
    AIPredictionFeedback,
    ExtractionCorrection,
    MLModel,
)
from ai_classifier.services.ml.predictor import Predictor
from ai_classifier.services.ml.ocr_service import OCRService
from documenti.models import Documento, DocumentiTipo, AttributoDefinizione
from .transformations import get_available_transformations

from .serializers_ai_import import (
    DocumentExtractionTemplateSerializer,
    ExtractionTemplatePageSerializer,
    ExtractionTemplateZoneSerializer,
    ExtractionFieldMappingSerializer,
    AIPredictionFeedbackSerializer,
    ExtractionCorrectionSerializer,
    UploadDocumentRequestSerializer,
    UploadDocumentResponseSerializer,
    PredictTypeRequestSerializer,
    PredictTypeResponseSerializer,
    PredictionResultSerializer,
    ExtractDataRequestSerializer,
    ExtractDataResponseSerializer,
    ExtractedFieldSerializer,
    ConfirmPredictionRequestSerializer,
    SaveFeedbackRequestSerializer,
    CreateTemplatePageRequestSerializer,
    CreateTemplateZoneRequestSerializer,
)

logger = logging.getLogger(__name__)


class AIImportViewSet(viewsets.ViewSet):
    """
    ViewSet per AI-Assisted Document Import.
    
    Workflow:
    1. upload() - Upload file e OCR
    2. predict() - Predizione tipo documento (top 3)
    3. extract() - Estrazione dati da template
    4. confirm_prediction() - Salva conferma utente
    5. save_feedback() - Salva correzioni campi
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload documento e estrazione testo OCR.
        
        POST /api/v1/ai-import/upload/
        
        Request:
            - file: File documento (PDF, immagine, etc.)
            - filename: Nome file originale (opzionale)
        
        Response:
            - temp_file_path: Path temporaneo del file
            - ocr_text: Testo estratto
            - page_count: Numero pagine
            - ocr_method: Metodo OCR usato
        """
        serializer = UploadDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        filename = serializer.validated_data.get('filename') or uploaded_file.name
        
        try:
            # Salva file temporaneo
            temp_dir = tempfile.gettempdir()
            temp_filename = f"ai_import_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            with open(temp_path, 'wb+') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
            
            logger.info(f"📄 File temporaneo salvato: {temp_path}")
            
            # Estrai testo OCR
            ocr_service = OCRService()
            ocr_result = ocr_service.extract_text_from_file(temp_path)
            
            if not ocr_result.get('success'):
                return Response(
                    {
                        'error': 'Errore estrazione OCR',
                        'details': ocr_result.get('error', 'Errore sconosciuto')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_data = {
                'temp_file_path': temp_path,
                'ocr_text': ocr_result['text'],
                'page_count': ocr_result.get('page_count', 1),
                'ocr_method': ocr_result.get('method', 'unknown'),
            }
            
            logger.info(f"✅ OCR completato: {len(ocr_result['text'])} caratteri, metodo={ocr_result.get('method')}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Errore upload/OCR: {e}", exc_info=True)
            
            # Pulisci file temporaneo in caso di errore
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
            return Response(
                {'error': f'Errore durante upload: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def predict(self, request):
        """
        Predizione tipo documento (top 3 con confidence).
        
        POST /api/v1/ai-import/predict/
        
        Request:
            - temp_file_path: Path file temporaneo (opzionale)
            - ocr_text: Testo OCR già estratto (opzionale)
            - filename: Nome file originale (opzionale)
        
        Response:
            - predictions: Top 3 predizioni [
                {tipo_documento_id, codice, descrizione, confidence, has_template}
              ]
            - model_version: Versione modello ML usato
            - total_types: Totale tipi documento
        """
        serializer = PredictTypeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        temp_file_path = serializer.validated_data.get('temp_file_path')
        ocr_text = serializer.validated_data.get('ocr_text')
        filename = serializer.validated_data.get('filename', '')
        
        try:
            # Se non c'è testo OCR, estrailo dal file
            if not ocr_text and temp_file_path:
                if not os.path.exists(temp_file_path):
                    return Response(
                        {'error': 'File temporaneo non trovato'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                ocr_service = OCRService()
                ocr_result = ocr_service.extract_text_from_file(temp_file_path)
                
                if not ocr_result.get('success'):
                    return Response(
                        {'error': 'Errore estrazione testo'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                ocr_text = ocr_result['text']
            
            # Predizione tipo documento
            predictor = Predictor()
            
            # Ottieni modello attivo
            active_model = MLModel.objects.filter(is_active=True).first()
            if not active_model:
                return Response(
                    {'error': 'Nessun modello ML attivo'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Predici (ottieni top 3)
            prediction_result = predictor.predict_with_probabilities(
                text=ocr_text,
                filename=filename,
                top_k=3
            )
            
            if not prediction_result or 'predictions' not in prediction_result:
                return Response(
                    {'error': 'Errore predizione'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Arricchisci predizioni con info template
            predictions = []
            for pred in prediction_result['predictions']:
                tipo_id = pred['tipo_documento_id']
                
                # Verifica se esiste template attivo per questo tipo
                has_template = DocumentExtractionTemplate.objects.filter(
                    tipo_documento_id=tipo_id,
                    attivo=True
                ).exists()
                
                predictions.append({
                    'tipo_documento_id': tipo_id,
                    'tipo_documento_codice': pred['codice'],
                    'tipo_documento_descrizione': pred['descrizione'],
                    'confidence': pred['confidence'],
                    'has_template': has_template,
                })
            
            response_data = {
                'predictions': predictions,
                'model_version': active_model.version,
                'total_types': DocumentiTipo.objects.count(),
            }
            
            logger.info(f"✅ Predizione completata: Top 1 = {predictions[0]['tipo_documento_codice']} ({predictions[0]['confidence']:.2%})")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Errore predizione: {e}", exc_info=True)
            return Response(
                {'error': f'Errore durante predizione: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def extract(self, request):
        """
        Estrazione dati da template.
        
        POST /api/v1/ai-import/extract/
        
        Request:
            - temp_file_path: Path file temporaneo
            - tipo_documento_id: ID tipo documento confermato
            - template_id: ID template specifico (opzionale)
        
        Response:
            - template_id: Template usato
            - template_nome: Nome template
            - campi_estratti: Lista campi estratti [
                {nome_campo, etichetta, valore, tipo_dato, confidence, mapping, validazione_ok, errore_validazione}
              ]
            - note_generate: Note auto-generate
            - estrazione_completa: True se tutti i campi obbligatori OK
        """
        serializer = ExtractDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        temp_file_path = serializer.validated_data['temp_file_path']
        tipo_documento_id = serializer.validated_data['tipo_documento_id']
        template_id = serializer.validated_data.get('template_id')
        
        try:
            # Verifica file
            if not os.path.exists(temp_file_path):
                return Response(
                    {'error': 'File temporaneo non trovato'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Trova template
            if template_id:
                template = DocumentExtractionTemplate.objects.filter(
                    id=template_id,
                    tipo_documento_id=tipo_documento_id,
                    attivo=True
                ).first()
            else:
                # Usa template con priorità maggiore
                template = DocumentExtractionTemplate.objects.filter(
                    tipo_documento_id=tipo_documento_id,
                    attivo=True
                ).order_by('-priorita').first()
            
            if not template:
                return Response(
                    {
                        'error': 'Nessun template attivo trovato',
                        'tipo_documento_id': tipo_documento_id,
                        'template_id': template_id,
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Estrai dati da zone template
            extraction_service = ExtractionService()
            extracted_data = extraction_service.extract_from_template(
                file_path=temp_file_path,
                template=template
            )
            
            # Genera note automatiche
            note_generate = self._generate_extraction_notes(
                extracted_data['campi_estratti'],
                template.tipo_documento.codice
            )
            
            response_data = {
                'template_id': template.id,
                'template_nome': template.nome,
                'campi_estratti': extracted_data['campi_estratti'],
                'note_generate': note_generate,
                'estrazione_completa': extracted_data['estrazione_completa'],
            }
            
            logger.info(f"✅ Estrazione completata: template={template.nome}, campi={len(extracted_data['campi_estratti'])}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione: {e}", exc_info=True)
            return Response(
                {'error': f'Errore durante estrazione: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def confirm_prediction(self, request):
        """
        Salva conferma predizione utente.
        
        POST /api/v1/ai-import/confirm-prediction/
        
        Request:
            - documento_id: ID documento creato
            - tipo_predetto_id: ID tipo predetto AI
            - tipo_confermato_id: ID tipo confermato utente
            - confidence_predizione: Confidence predizione
            - top_3_predizioni: Lista top 3
            - dati_estratti_ai: Dati estratti (opzionale)
        
        Response:
            - feedback_id: ID feedback creato
            - predizione_corretta: True/False
        """
        serializer = ConfirmPredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                feedback = AIPredictionFeedback.objects.create(
                    documento_id=serializer.validated_data['documento_id'],
                    tipo_predetto_id=serializer.validated_data['tipo_predetto_id'],
                    tipo_confermato_id=serializer.validated_data['tipo_confermato_id'],
                    confidence_predizione=serializer.validated_data['confidence_predizione'],
                    top_3_predizioni=serializer.validated_data['top_3_predizioni'],
                    dati_estratti_ai=serializer.validated_data.get('dati_estratti_ai', {}),
                    utente=request.user,
                )
                
                logger.info(
                    f"✅ Feedback salvato: doc={feedback.documento.codice}, "
                    f"predetto={feedback.tipo_predetto.codice}, "
                    f"confermato={feedback.tipo_confermato.codice}, "
                    f"corretto={feedback.predizione_corretta}"
                )
                
                return Response(
                    {
                        'feedback_id': feedback.id,
                        'predizione_corretta': feedback.predizione_corretta,
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"❌ Errore salvataggio feedback: {e}", exc_info=True)
            return Response(
                {'error': f'Errore salvataggio feedback: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def save_feedback(self, request):
        """
        Salva correzioni campi estratti.
        
        POST /api/v1/ai-import/save-feedback/
        
        Request:
            - feedback_id: ID feedback predizione
            - correzioni: Lista correzioni [{nome_campo, valore_estratto, valore_corretto, confidence_estrazione}]
        
        Response:
            - correzioni_salvate: Numero correzioni salvate
        """
        serializer = SaveFeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        feedback_id = serializer.validated_data['feedback_id']
        correzioni_data = serializer.validated_data.get('correzioni', [])
        
        try:
            # Verifica feedback esiste
            feedback = AIPredictionFeedback.objects.filter(id=feedback_id).first()
            if not feedback:
                return Response(
                    {'error': 'Feedback non trovato'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with transaction.atomic():
                correzioni_create = []
                
                for corr_data in correzioni_data:
                    # Solo se valore estratto != valore corretto
                    if corr_data['valore_estratto'] != corr_data['valore_corretto']:
                        correzione = ExtractionCorrection.objects.create(
                            feedback=feedback,
                            nome_campo=corr_data['nome_campo'],
                            valore_estratto=corr_data['valore_estratto'],
                            valore_corretto=corr_data['valore_corretto'],
                            confidence_estrazione=corr_data.get('confidence_estrazione'),
                        )
                        correzioni_create.append(correzione)
                
                logger.info(
                    f"✅ Correzioni salvate: feedback_id={feedback_id}, "
                    f"correzioni={len(correzioni_create)}/{len(correzioni_data)}"
                )
                
                return Response(
                    {'correzioni_salvate': len(correzioni_create)},
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"❌ Errore salvataggio correzioni: {e}", exc_info=True)
            return Response(
                {'error': f'Errore salvataggio correzioni: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_extraction_notes(self, campi_estratti: List[Dict], tipo_codice: str) -> str:
        """
        Genera note automatiche dai campi estratti.
        
        Formato:
        === DATI ESTRATTI AI ({tipo_codice}) ===
        
        Campo 1: valore1
        Campo 2: valore2
        ...
        
        [Auto-generato il YYYY-MM-DD HH:MM]
        """
        lines = [
            f"=== DATI ESTRATTI AI ({tipo_codice}) ===",
            "",
        ]
        
        for campo in campi_estratti:
            if campo.get('valore'):
                etichetta = campo['etichetta']
                valore = campo['valore']
                lines.append(f"{etichetta}: {valore}")
        
        lines.append("")
        lines.append(f"[Auto-generato il {timezone.now().strftime('%Y-%m-%d %H:%M')}]")
        
        return "\n".join(lines)


class TemplateManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione template di estrazione.
    
    CRUD completo per:
    - DocumentExtractionTemplate
    - ExtractionTemplatePage
    - ExtractionTemplateZone
    - ExtractionFieldMapping
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Override per filtrare per tipo modello"""
        # Per custom actions, restituisci sempre il queryset completo
        return DocumentExtractionTemplate.objects.select_related(
            'tipo_documento',
            'creato_da'
        ).prefetch_related(
            'pagine__zone',
            'mapping_campi'
        ).order_by('-priorita', '-creato_il')
    
    def get_serializer_class(self):
        return DocumentExtractionTemplateSerializer
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_page(self, request, pk=None):
        """
        Aggiungi pagina a template.
        
        POST /api/v1/ai-classifier/templates/{id}/add_page/
        """
        template = self.get_object()
        serializer = CreateTemplatePageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            immagine_file = serializer.validated_data['immagine']
            
            # Verifica dimensioni immagine
            img = Image.open(immagine_file)
            larghezza_reale, altezza_reale = img.size
            
            page = ExtractionTemplatePage.objects.create(
                template=template,
                numero_pagina=serializer.validated_data['numero_pagina'],
                immagine_template=immagine_file,
                larghezza=larghezza_reale,
                altezza=altezza_reale,
            )
            
            logger.info(f"✅ Pagina template creata: {page}")
            
            response_serializer = ExtractionTemplatePageSerializer(page, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Errore creazione pagina: {e}", exc_info=True)
            return Response(
                {'error': f'Errore creazione pagina: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def add_zone(self, request):
        """
        Aggiungi zona estrazione a pagina template.
        
        POST /api/v1/templates/add_zone/
        """
        serializer = CreateTemplateZoneRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            zone = ExtractionTemplateZone.objects.create(**serializer.validated_data)
            
            logger.info(f"✅ Zona template creata: {zone}")
            
            response_serializer = ExtractionTemplateZoneSerializer(zone)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Errore creazione zona: {e}", exc_info=True)
            return Response(
                {'error': f'Errore creazione zona: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'], url_path='zones/(?P<zone_id>[^/.]+)')
    def delete_zone(self, request, zone_id=None):
        """
        Elimina zona estrazione.
        
        DELETE /api/v1/ai-classifier/templates/zones/{zone_id}/
        """
        try:
            zone = ExtractionTemplateZone.objects.get(id=zone_id)
            zone.delete()
            
            logger.info(f"✅ Zona template eliminata: ID={zone_id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ExtractionTemplateZone.DoesNotExist:
            return Response(
                {'error': 'Zona non trovata'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Errore eliminazione zona: {e}", exc_info=True)
            return Response(
                {'error': f'Errore eliminazione zona: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='field-mappings')
    def add_field_mapping(self, request):
        """
        Crea nuovo field mapping.
        
        POST /api/v1/ai-classifier/templates/field-mappings/
        
        Body:
            {
                "template_id": int,
                "nome_campo_template": str,
                "tipo_campo_destinazione": str,
                "nome_campo_destinazione": str,
                "funzione_trasformazione": str (optional)
            }
        """
        try:
            template_id = request.data.get('template_id')
            nome_campo_template = request.data.get('nome_campo_template')
            tipo_campo = request.data.get('tipo_campo_destinazione')
            nome_campo = request.data.get('nome_campo_destinazione')
            funzione_trasf = request.data.get('funzione_trasformazione')
            
            # Validazione
            if not all([template_id, nome_campo_template, nome_campo]):
                return Response(
                    {'error': 'Parametri mancanti: template_id, nome_campo_template, nome_campo_destinazione obbligatori'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verifica template esiste
            try:
                template = DocumentExtractionTemplate.objects.get(id=template_id)
            except DocumentExtractionTemplate.DoesNotExist:
                return Response(
                    {'error': 'Template non trovato'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Crea mapping
            mapping = ExtractionFieldMapping.objects.create(
                template=template,
                nome_campo_template=nome_campo_template,
                tipo_campo_destinazione=tipo_campo or 'field',
                nome_campo_destinazione=nome_campo,
                funzione_trasformazione=funzione_trasf or ''
            )
            
            logger.info(f"✅ Field mapping creato: {nome_campo_template} → {nome_campo}")
            
            serializer = ExtractionFieldMappingSerializer(mapping)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Errore creazione field mapping: {e}", exc_info=True)
            return Response(
                {'error': f'Errore creazione field mapping: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'], url_path='field-mappings/(?P<mapping_id>[^/.]+)')
    def delete_field_mapping(self, request, mapping_id=None):
        """
        Elimina field mapping.
        
        DELETE /api/v1/ai-classifier/templates/field-mappings/{mapping_id}/
        """
        try:
            mapping = ExtractionFieldMapping.objects.get(id=mapping_id)
            mapping.delete()
            
            logger.info(f"✅ Field mapping eliminato: ID={mapping_id}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ExtractionFieldMapping.DoesNotExist:
            return Response(
                {'error': 'Field mapping non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Errore eliminazione field mapping: {e}", exc_info=True)
            return Response(
                {'error': f'Errore eliminazione field mapping: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available-fields/(?P<tipo_documento_id>[^/.]+)')
    def available_fields(self, request, tipo_documento_id=None):
        """
        Restituisce lista campi disponibili per un tipo documento.
        Include campi fissi del modello + attributi dinamici.
        
        GET /api/v1/ai-classifier/templates/available-fields/{tipo_documento_id}/
        """
        try:
            logger.info(f"📥 Richiesta available_fields per tipo_documento_id={tipo_documento_id}")
            
            tipo_documento = DocumentiTipo.objects.get(id=tipo_documento_id)
            logger.info(f"✅ Tipo documento trovato: {tipo_documento.codice}")
            
            # Campi fissi del modello Documento
            campi_fissi = [
                {'value': 'numero_protocollo', 'label': 'Numero Protocollo', 'type': 'text'},
                {'value': 'data_documento', 'label': 'Data Documento', 'type': 'date'},
                {'value': 'data_protocollo', 'label': 'Data Protocollo', 'type': 'date'},
                {'value': 'oggetto', 'label': 'Oggetto', 'type': 'text'},
                {'value': 'note', 'label': 'Note (sovrascrive)', 'type': 'text'},
                {'value': '__note__', 'label': '📝 Aggiungi a Note', 'type': 'text'},
                {'value': 'cliente.anagrafica.codice_fiscale', 'label': 'Cliente - Codice Fiscale', 'type': 'codice_fiscale'},
                {'value': 'cliente.anagrafica.partita_iva', 'label': 'Cliente - Partita IVA', 'type': 'partita_iva'},
                {'value': 'cliente.anagrafica.nome', 'label': 'Cliente - Nome/Ragione Sociale', 'type': 'text'},
                {'value': 'cliente.anagrafica.email', 'label': 'Cliente - Email', 'type': 'email'},
                {'value': 'cliente.anagrafica.telefono', 'label': 'Cliente - Telefono', 'type': 'phone'},
            ]
            
            # Attributi dinamici per questo tipo documento
            attributi = AttributoDefinizione.objects.filter(
                tipo_documento=tipo_documento
            ).order_by('ordine', 'nome')
            
            campi_dinamici = []
            for attr in attributi:
                # Mappa tipo attributo a tipo dato zona
                tipo_mappa = {
                    'string': 'text',
                    'int': 'integer',
                    'decimal': 'decimal',
                    'date': 'date',
                    'bool': 'text',
                    'choice': 'text',
                }
                
                campi_dinamici.append({
                    'value': f'attributi.{attr.codice}',
                    'label': f'{attr.nome}',
                    'type': tipo_mappa.get(attr.tipo_dato, 'text'),
                })
            
            # Combina tutti i campi
            tutti_campi = campi_fissi + campi_dinamici
            
            logger.info(f"📊 Campi totali: {len(tutti_campi)} (fissi: {len(campi_fissi)}, dinamici: {len(campi_dinamici)})")
            
            return Response({
                'tipo_documento': {
                    'id': tipo_documento.id,
                    'codice': tipo_documento.codice,
                },
                'campi': tutti_campi,
            })
            
        except DocumentiTipo.DoesNotExist:
            return Response(
                {'error': 'Tipo documento non trovato'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Errore recupero campi disponibili: {e}", exc_info=True)
            return Response(
                {'error': f'Errore server: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available-transformations')
    def available_transformations(self, request):
        """
        Restituisce lista funzioni di trasformazione disponibili.
        
        GET /api/v1/ai-classifier/templates/available-transformations/
        
        Returns:
            List di dict con:
            - value: nome funzione
            - label: descrizione human-readable
            - category: categoria (UNILAV, Validazione, Testo, Estrazione)
        """
        try:
            transformations = get_available_transformations()
            
            logger.info(f"📊 Trasformazioni disponibili: {len(transformations)}")
            
            return Response({
                'transformations': transformations,
                'count': len(transformations),
            })
            
        except Exception as e:
            logger.error(f"❌ Errore recupero trasformazioni: {e}", exc_info=True)
            return Response(
                {'error': f'Errore: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# EXTRACTION SERVICE
# =============================================================================

class ExtractionService:
    """
    Servizio per estrazione dati da template.
    """
    
    def __init__(self):
        self.ocr_service = OCRService()
    
    def extract_from_template(
        self,
        file_path: str,
        template: DocumentExtractionTemplate
    ) -> Dict[str, Any]:
        """
        Estrae dati dal file usando le zone del template.
        
        Returns:
            {
                'campi_estratti': [...],
                'estrazione_completa': bool
            }
        """
        campi_estratti = []
        campi_obbligatori_ok = True
        
        # Per ogni pagina del template
        for pagina in template.pagine.all():
            # Per ogni zona della pagina
            for zona in pagina.zone.all():
                # Estrai valore dalla zona
                valore_estratto = self._extract_zone_value(
                    file_path=file_path,
                    pagina=pagina,
                    zona=zona
                )
                
                # Valida valore
                validazione = self._validate_field(
                    valore=valore_estratto['valore'],
                    zona=zona
                )
                
                # Trova mapping
                mapping = template.mapping_campi.filter(
                    nome_campo_template=zona.nome_campo
                ).first()
                
                mapping_info = {}
                if mapping:
                    mapping_info = {
                        'tipo_campo_destinazione': mapping.tipo_campo_destinazione,
                        'nome_campo_destinazione': mapping.nome_campo_destinazione,
                        'funzione_trasformazione': mapping.funzione_trasformazione or '',
                        'formato_input': mapping.formato_input or '',
                    }
                
                campo_estratto = {
                    'nome_campo': zona.nome_campo,
                    'etichetta': zona.etichetta,
                    'valore': valore_estratto['valore'],
                    'tipo_dato': zona.tipo_dato,
                    'confidence': valore_estratto.get('confidence'),
                    'mapping': mapping_info,
                    'validazione_ok': validazione['ok'],
                    'errore_validazione': validazione.get('errore'),
                }
                
                campi_estratti.append(campo_estratto)
                
                # Verifica campi obbligatori
                if zona.obbligatorio and not validazione['ok']:
                    campi_obbligatori_ok = False
        
        return {
            'campi_estratti': campi_estratti,
            'estrazione_completa': campi_obbligatori_ok,
        }
    
    def _extract_zone_value(
        self,
        file_path: str,
        pagina: ExtractionTemplatePage,
        zona: ExtractionTemplateZone
    ) -> Dict[str, Any]:
        """
        Estrae valore da una zona specifica del documento usando coordinate.
        
        Usa pdfplumber per estrarre testo solo dalla zona definita dalle coordinate percentuali.
        Se le coordinate non sono configurate, usa fallback pattern-based.
        """
        try:
            # Verifica se coordinate sono configurate
            has_coordinates = all([
                zona.x_percent is not None,
                zona.y_percent is not None,
                zona.width_percent is not None,
                zona.height_percent is not None,
            ])
            
            if not has_coordinates:
                logger.warning(
                    f"Zona '{zona.nome_campo}' senza coordinate, uso fallback pattern-based"
                )
                return self._extract_zone_value_by_pattern(file_path, zona)
            
            # Apri PDF con pdfplumber
            with pdfplumber.open(file_path) as pdf:
                # Verifica numero pagina valido
                if pagina.numero_pagina > len(pdf.pages):
                    logger.warning(
                        f"Pagina {pagina.numero_pagina} non trovata (PDF ha {len(pdf.pages)} pagine)"
                    )
                    return {'valore': '', 'confidence': None}
                
                # Ottieni pagina (0-indexed)
                page = pdf.pages[pagina.numero_pagina - 1]
                
                # Converti coordinate percentuali in assolute
                page_width = float(page.width)
                page_height = float(page.height)
                
                # Calcola bounding box da x, y, width, height percentuali
                x0 = page_width * (float(zona.x_percent) / 100)
                y0 = page_height * (float(zona.y_percent) / 100)
                x1 = page_width * ((float(zona.x_percent) + float(zona.width_percent)) / 100)
                y1 = page_height * ((float(zona.y_percent) + float(zona.height_percent)) / 100)
                
                # Definisci bounding box (x0, top, x1, bottom)
                bbox = (x0, y0, x1, y1)
                
                # Estrai testo dalla zona
                cropped_page = page.crop(bbox)
                zone_text = cropped_page.extract_text() or ''
                
                # Pulisci testo (rimuovi spazi multipli, newline extra)
                valore = ' '.join(zone_text.split())
                
                # Pulisci valore da etichette modulo e prefissi
                valore = self._clean_extracted_value(valore, zona)
                
                logger.debug(
                    f"Zona '{zona.nome_campo}': bbox={bbox}, "
                    f"estratto='{valore[:50]}...'"
                )
                
                # Applica pattern di ricerca se definito
                if zona.pattern_validazione and valore:
                    match = re.search(zona.pattern_validazione, valore)
                    if match:
                        valore = match.group(0)
                        logger.debug(f"Pattern match: '{valore}'")
                
                return {
                    'valore': valore.strip(),
                    'confidence': 1.0 if valore else 0.0,
                }
                
        except Exception as e:
            logger.error(
                f"Errore estrazione zona '{zona.nome_campo}': {e}",
                exc_info=True
            )
            return {'valore': '', 'confidence': None}
    
    def _extract_zone_value_by_pattern(
        self,
        file_path: str,
        zona: ExtractionTemplateZone
    ) -> Dict[str, Any]:
        """
        Fallback: estrae valore cercando pattern nel testo completo.
        Usato quando le coordinate della zona non sono configurate.
        """
        try:
            # Estrai tutto il testo
            ocr_result = self.ocr_service.extract_text_from_file(file_path)
            
            if not ocr_result.get('success'):
                return {'valore': '', 'confidence': None}
            
            full_text = ocr_result['text']
            
            # Cerca pattern specifici per tipo dato
            valore = self._search_pattern_in_text(
                text=full_text,
                zona=zona
            )
            
            # Pulisci valore
            valore = self._clean_extracted_value(valore, zona)
            
            return {
                'valore': valore,
                'confidence': 0.5 if valore else 0.0,  # Lower confidence
            }
        except Exception as e:
            logger.error(
                f"Errore estrazione pattern per zona '{zona.nome_campo}': {e}",
                exc_info=True
            )
            return {'valore': '', 'confidence': None}
    
    def _search_pattern_in_text(self, text: str, zona: ExtractionTemplateZone) -> str:
        """
        Cerca pattern specifici nel testo basandosi sul tipo dato.
        
        TODO: Questa è una implementazione semplificata.
        Versione completa userà coordinate + OCR di zona.
        """
        # Pattern regex per tipi dato comuni
        patterns = {
            'codice_fiscale': r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b',
            'partita_iva': r'\b\d{11}\b',
            'date': r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+39[\s\.]?)?(?:\d{2,3}[\s\.]?)?\d{6,8}\b',
        }
        
        pattern = patterns.get(zona.tipo_dato)
        
        if pattern:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # Se ha pattern custom
        if zona.pattern_validazione:
            match = re.search(zona.pattern_validazione, text)
            if match:
                return match.group(0)
        
        return ''
    
    def _validate_field(self, valore: str, zona: ExtractionTemplateZone) -> Dict[str, Any]:
        """
        Valida un campo estratto.
        
        Returns:
            {'ok': bool, 'errore': str}
        """
        # Campo obbligatorio vuoto
        if zona.obbligatorio and not valore:
            return {
                'ok': False,
                'errore': f'Campo obbligatorio "{zona.etichetta}" vuoto'
            }
        
        # Pattern validazione custom
        if zona.pattern_validazione and valore:
            if not re.match(zona.pattern_validazione, valore):
                return {
                    'ok': False,
                    'errore': f'Valore non corrisponde al pattern richiesto'
                }
        
        return {'ok': True}    
    def _clean_extracted_value(self, valore: str, zona: ExtractionTemplateZone) -> str:
        """
        Pulisce valore estratto rimuovendo etichette modulo e prefissi numerici.
        
        Args:
            valore: Valore grezzo estratto dalla zona
            zona: Zona template con tipo_dato
            
        Returns:
            Valore pulito
        """
        if not valore:
            return valore
        
        original = valore
        
        # 1. Rimuovi prefisso numerico seguito da spazio (es. "1 VALORE" → "VALORE")
        valore = re.sub(r'^\d+\s+', '', valore)
        
        # 2. Rimuovi prefisso numerico attaccato (es. "2VALORE" → "VALORE")
        valore = re.sub(r'^[0-9][A-Z]', lambda m: m.group(0)[1], valore)
        
        # 3. Pattern specifici per tipo dato
        if zona.tipo_dato == 'codice_fiscale':
            # Estrai codice fiscale (16 caratteri alfanumerici)
            match = re.search(r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b', valore)
            if match:
                return match.group(0)
            
            # P.IVA: rimuovi tutto tranne cifre
            solo_cifre = re.sub(r'\D', '', valore)
            
            # Se esattamente 11 cifre → OK
            if len(solo_cifre) == 11:
                logger.debug(f"P.IVA estratta (11 cifre esatte): '{solo_cifre}'")
                return solo_cifre
            
            # Se più di 11 cifre → prendi ultime 11
            # Questo gestisce il caso di bbox che cattura "1" extra
            # Es: "101689620530" (12 cifre) → "01689620530" (ultime 11)
            if len(solo_cifre) > 11:
                piva = solo_cifre[-11:]
                logger.debug(f"P.IVA estratta (ultime 11 di {len(solo_cifre)}): '{piva}' da '{valore}'")
                return piva
            
            # Se meno di 11 cifre → non è una P.IVA valida, lascia com'è
            logger.debug(f"Valore con {len(solo_cifre)} cifre (non P.IVA): '{valore}'")
        
        elif zona.tipo_dato == 'date':
            # Estrai data in formato gg mm aaaa o gg/mm/aaaa
            match = re.search(r'\b(\d{1,2}[\s/\-]\d{1,2}[\s/\-]\d{2,4})\b', valore)
            if match:
                return match.group(1).replace(' ', '/')
        
        elif zona.tipo_dato == 'integer':
            # Estrai numero intero (4 cifre per anno)
            match = re.search(r'\b(\d{4})\b', valore)
            if match:
                return match.group(1)
        
        # 4. Rimuovi etichette comuni nei moduli italiani
        etichette_da_rimuovere = [
            r'^C\d*ognome o Denominazione\s+',  # "C2ognome o Denominazione ROSSI" → "ROSSI"
            r'^Cognome o Denominazione\s+',
            r'^Cognome\s+',
            r'^Nome\s+',
            r'^N\d*ome\s+',  # "N3ome MARIO" → "MARIO"
            r'^Denominazione\s+',
            r'^Ragione Sociale\s+',
            r'^Prov\.\s*Cap\s*',  # Rimuove "Prov. Cap" finale
            r'\s+Prov\.\s*Cap.*$',  # Rimuove "Prov. Cap" finale con tutto dopo
        ]
        
        for pattern in etichette_da_rimuovere:
            valore = re.sub(pattern, '', valore, flags=re.IGNORECASE)
        
        # 5. Trim finale
        valore = valore.strip()
        
        if valore != original:
            logger.debug(f"Pulizia '{zona.nome_campo}': '{original[:50]}' → '{valore[:50]}'")
        
        return valore