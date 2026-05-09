"""
Serializers per AI-Assisted Document Import
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from ai_classifier.models import (
    DocumentExtractionTemplate,
    ExtractionTemplatePage,
    ExtractionTemplateZone,
    ExtractionFieldMapping,
    AIPredictionFeedback,
    ExtractionCorrection,
)
from documenti.models import Documento, DocumentiTipo

User = get_user_model()


class ExtractionTemplateZoneSerializer(serializers.ModelSerializer):
    """
    Serializer per zone di estrazione.
    """
    absolute_coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtractionTemplateZone
        fields = [
            'id',
            'nome_campo',
            'etichetta',
            'x_percent',
            'y_percent',
            'width_percent',
            'height_percent',
            'absolute_coordinates',
            'tipo_dato',
            'obbligatorio',
            'pattern_validazione',
            'ordine',
        ]
    
    def get_absolute_coordinates(self, obj):
        """Ritorna coordinate assolute calcolate"""
        return obj.get_absolute_coordinates()


class ExtractionTemplatePageSerializer(serializers.ModelSerializer):
    """
    Serializer per pagine template.
    """
    zone = ExtractionTemplateZoneSerializer(many=True, read_only=True)
    immagine_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtractionTemplatePage
        fields = [
            'id',
            'numero_pagina',
            'immagine_template',
            'immagine_url',
            'larghezza',
            'altezza',
            'zone',
        ]
    
    def get_immagine_url(self, obj):
        """Ritorna URL completo dell'immagine"""
        if obj.immagine_template:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.immagine_template.url)
            return obj.immagine_template.url
        return None


class ExtractionFieldMappingSerializer(serializers.ModelSerializer):
    """
    Serializer per mapping campi.
    """
    class Meta:
        model = ExtractionFieldMapping
        fields = [
            'id',
            'nome_campo_template',
            'tipo_campo_destinazione',
            'nome_campo_destinazione',
            'funzione_trasformazione',
            'formato_input',
            'valore_default',
        ]
    
    def validate(self, attrs):
        """Auto-detect tipo campo destinazione se non specificato"""
        nome_campo = attrs.get('nome_campo_destinazione', '')
        
        # Auto-detect tipo campo
        if not attrs.get('tipo_campo_destinazione'):
            if nome_campo.startswith('attributi.'):
                attrs['tipo_campo_destinazione'] = 'attribute'
            elif nome_campo == '__note__':
                attrs['tipo_campo_destinazione'] = 'note'
            elif nome_campo in ['note', 'oggetto', 'numero_protocollo', 'data_documento', 'data_protocollo']:
                attrs['tipo_campo_destinazione'] = 'field'
            elif nome_campo.startswith('cliente.'):
                attrs['tipo_campo_destinazione'] = 'field'
            else:
                attrs['tipo_campo_destinazione'] = 'field'
        
        # Se è __note__, normalizza a 'note' per salvataggio
        if nome_campo == '__note__':
            attrs['tipo_campo_destinazione'] = 'note'
            # Mantieni nome originale per distinguere append vs overwrite
        
        return attrs


class DocumentExtractionTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer per template di estrazione documenti.
    """
    tipo_documento_id = serializers.IntegerField(
        source='tipo_documento.id',
        read_only=True
    )
    tipo_documento_codice = serializers.CharField(
        source='tipo_documento.codice',
        read_only=True
    )
    tipo_documento_descrizione = serializers.CharField(
        source='tipo_documento.descrizione',
        read_only=True
    )
    pagine = ExtractionTemplatePageSerializer(many=True, read_only=True)
    mapping_campi = ExtractionFieldMappingSerializer(many=True, read_only=True)
    creato_da_username = serializers.CharField(
        source='creato_da.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = DocumentExtractionTemplate
        fields = [
            'id',
            'tipo_documento',
            'tipo_documento_id',
            'tipo_documento_codice',
            'tipo_documento_descrizione',
            'nome',
            'descrizione',
            'numero_pagine',
            'attivo',
            'priorita',
            'creato_il',
            'aggiornato_il',
            'creato_da',
            'creato_da_username',
            'pagine',
            'mapping_campi',
        ]
        read_only_fields = ['creato_il', 'aggiornato_il']


class ExtractionCorrectionSerializer(serializers.ModelSerializer):
    """
    Serializer per correzioni campi estratti.
    """
    class Meta:
        model = ExtractionCorrection
        fields = [
            'id',
            'nome_campo',
            'valore_estratto',
            'valore_corretto',
            'confidence_estrazione',
            'data_correzione',
        ]
        read_only_fields = ['data_correzione']


class AIPredictionFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer per feedback predizioni AI.
    """
    documento_codice = serializers.CharField(
        source='documento.codice',
        read_only=True
    )
    tipo_predetto_codice = serializers.CharField(
        source='tipo_predetto.codice',
        read_only=True
    )
    tipo_confermato_codice = serializers.CharField(
        source='tipo_confermato.codice',
        read_only=True
    )
    utente_username = serializers.CharField(
        source='utente.username',
        read_only=True,
        allow_null=True
    )
    correzioni = ExtractionCorrectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIPredictionFeedback
        fields = [
            'id',
            'documento',
            'documento_codice',
            'tipo_predetto',
            'tipo_predetto_codice',
            'confidence_predizione',
            'top_3_predizioni',
            'tipo_confermato',
            'tipo_confermato_codice',
            'predizione_corretta',
            'dati_estratti_ai',
            'utente',
            'utente_username',
            'data_predizione',
            'usato_per_training',
            'training_job',
            'correzioni',
        ]
        read_only_fields = ['data_predizione', 'predizione_corretta', 'usato_per_training']


# =============================================================================
# SERIALIZERS PER REQUEST/RESPONSE
# =============================================================================

class UploadDocumentRequestSerializer(serializers.Serializer):
    """
    Serializer per richiesta upload documento.
    """
    file = serializers.FileField(
        help_text="File documento da analizzare"
    )
    filename = serializers.CharField(
        required=False,
        help_text="Nome file originale (opzionale)"
    )


class UploadDocumentResponseSerializer(serializers.Serializer):
    """
    Serializer per risposta upload documento.
    """
    temp_file_path = serializers.CharField(
        help_text="Path temporaneo del file caricato"
    )
    ocr_text = serializers.CharField(
        help_text="Testo estratto dal documento"
    )
    page_count = serializers.IntegerField(
        help_text="Numero di pagine del documento"
    )
    ocr_method = serializers.CharField(
        help_text="Metodo OCR utilizzato (native, hybrid, tesseract, etc.)"
    )


class PredictTypeRequestSerializer(serializers.Serializer):
    """
    Serializer per richiesta predizione tipo documento.
    """
    temp_file_path = serializers.CharField(
        required=False,
        help_text="Path file temporaneo (da upload)"
    )
    ocr_text = serializers.CharField(
        required=False,
        help_text="Testo OCR già estratto"
    )
    filename = serializers.CharField(
        required=False,
        help_text="Nome file originale"
    )
    
    def validate(self, attrs):
        """Almeno uno tra temp_file_path e ocr_text deve essere presente"""
        if not attrs.get('temp_file_path') and not attrs.get('ocr_text'):
            raise serializers.ValidationError(
                "Fornire almeno uno tra 'temp_file_path' o 'ocr_text'"
            )
        return attrs


class PredictionResultSerializer(serializers.Serializer):
    """
    Serializer per singolo risultato predizione.
    """
    tipo_documento_id = serializers.IntegerField()
    tipo_documento_codice = serializers.CharField()
    tipo_documento_descrizione = serializers.CharField()
    confidence = serializers.DecimalField(max_digits=5, decimal_places=4)
    has_template = serializers.BooleanField(
        help_text="True se esiste un template attivo per questo tipo"
    )


class PredictTypeResponseSerializer(serializers.Serializer):
    """
    Serializer per risposta predizione tipo documento.
    """
    predictions = PredictionResultSerializer(many=True)
    model_version = serializers.CharField()
    total_types = serializers.IntegerField()


class ExtractDataRequestSerializer(serializers.Serializer):
    """
    Serializer per richiesta estrazione dati.
    """
    temp_file_path = serializers.CharField(
        help_text="Path file temporaneo"
    )
    tipo_documento_id = serializers.IntegerField(
        help_text="ID tipo documento confermato"
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID template specifico (opzionale, usa quello con priorità maggiore)"
    )


class ExtractedFieldSerializer(serializers.Serializer):
    """
    Serializer per singolo campo estratto.
    """
    nome_campo = serializers.CharField()
    etichetta = serializers.CharField()
    valore = serializers.CharField(allow_blank=True, allow_null=True)
    tipo_dato = serializers.CharField()
    confidence = serializers.DecimalField(
        max_digits=5,
        decimal_places=4,
        required=False,
        allow_null=True
    )
    mapping = serializers.DictField(
        help_text="Info mapping: tipo_campo_destinazione, nome_campo_destinazione"
    )
    validazione_ok = serializers.BooleanField()
    errore_validazione = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )


class ExtractDataResponseSerializer(serializers.Serializer):
    """
    Serializer per risposta estrazione dati.
    """
    template_id = serializers.IntegerField()
    template_nome = serializers.CharField()
    campi_estratti = ExtractedFieldSerializer(many=True)
    note_generate = serializers.CharField(
        help_text="Note auto-generate con i dati estratti"
    )
    estrazione_completa = serializers.BooleanField(
        help_text="True se tutti i campi obbligatori sono stati estratti"
    )


class ConfirmPredictionRequestSerializer(serializers.Serializer):
    """
    Serializer per conferma predizione.
    """
    documento_id = serializers.IntegerField(
        help_text="ID documento appena creato"
    )
    tipo_predetto_id = serializers.IntegerField(
        help_text="ID tipo predetto dall'AI"
    )
    tipo_confermato_id = serializers.IntegerField(
        help_text="ID tipo confermato dall'utente"
    )
    confidence_predizione = serializers.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Confidence della predizione"
    )
    top_3_predizioni = serializers.JSONField(
        help_text="Lista top 3 predizioni"
    )
    dati_estratti_ai = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Dati estratti automaticamente"
    )


class SaveFeedbackRequestSerializer(serializers.Serializer):
    """
    Serializer per salvataggio feedback e correzioni.
    """
    feedback_id = serializers.IntegerField(
        help_text="ID feedback predizione"
    )
    correzioni = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Lista correzioni: [{nome_campo, valore_estratto, valore_corretto, confidence_estrazione}]"
    )


# =============================================================================
# SERIALIZERS PER TEMPLATE MANAGEMENT
# =============================================================================

class CreateTemplatePageRequestSerializer(serializers.Serializer):
    """
    Serializer per creazione pagina template.
    """
    template_id = serializers.IntegerField()
    numero_pagina = serializers.IntegerField()
    immagine = serializers.ImageField()
    larghezza = serializers.IntegerField()
    altezza = serializers.IntegerField()


class CreateTemplateZoneRequestSerializer(serializers.Serializer):
    """
    Serializer per creazione zona estrazione.
    """
    pagina_id = serializers.IntegerField()
    nome_campo = serializers.CharField(max_length=100)
    etichetta = serializers.CharField(max_length=200)
    x_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    y_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    width_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    height_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    tipo_dato = serializers.CharField(max_length=20)
    obbligatorio = serializers.BooleanField(default=False)
    pattern_validazione = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    ordine = serializers.IntegerField(default=0)
