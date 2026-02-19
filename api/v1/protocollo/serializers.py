"""
Serializers per API Protocollo
"""
from rest_framework import serializers
from protocollo.models import MovimentoProtocollo, ProtocolloCounter
from archivio_fisico.models import UnitaFisica
from anagrafiche.models import Anagrafica
from django.contrib.auth import get_user_model

User = get_user_model()


class AnagraficaSimpleSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Anagrafica
        fields = [
            'id', 'display_name', 'tipo', 'codice_fiscale', 'partita_iva',
        ]

    def get_display_name(self, obj):
        return obj.display_name()


class UnitaFisicaSimpleSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = UnitaFisica
        fields = ['id', 'codice', 'nome', 'tipo', 'tipo_display', 'full_path']


class ProtocolloCounterSerializer(serializers.ModelSerializer):
    """Serializer per contatori protocollo"""
    cliente_display = serializers.SerializerMethodField()
    direzione_display = serializers.CharField(source='get_direzione_display', read_only=True)
    
    class Meta:
        model = ProtocolloCounter
        fields = ['id', 'cliente', 'cliente_display', 'anno', 'direzione', 'direzione_display', 'last_number']
        read_only_fields = ['last_number']
    
    def get_cliente_display(self, obj):
        if obj.cliente:
            return obj.cliente.display_name()
        return None


class MovimentoProtocolloListSerializer(serializers.ModelSerializer):
    """Serializer per lista movimenti protocollo"""
    direzione_display = serializers.CharField(source='get_direzione_display', read_only=True)
    cliente_display = serializers.SerializerMethodField()
    operatore_display = serializers.SerializerMethodField()
    documento_display = serializers.SerializerMethodField()
    fascicolo_display = serializers.SerializerMethodField()
    protocollo_label = serializers.SerializerMethodField()
    ubicazione_full_path = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    destinatario_anagrafica_display = serializers.SerializerMethodField()
    destinatario_anagrafica_detail = AnagraficaSimpleSerializer(source='destinatario_anagrafica', read_only=True)
    ubicazione_detail = UnitaFisicaSimpleSerializer(source='ubicazione', read_only=True)
    
    class Meta:
        model = MovimentoProtocollo
        fields = [
            'id', 'documento', 'documento_display', 'fascicolo', 'fascicolo_display',
            'cliente', 'cliente_display', 'direzione', 'direzione_display',
            'data', 'anno', 'numero', 'protocollo_label',
            'target_tipo', 'target_type', 'target_label', 'target_object_id',
            'operatore', 'operatore_display', 'destinatario',
            'destinatario_anagrafica', 'destinatario_anagrafica_display',
            'destinatario_anagrafica_detail',
            'ubicazione', 'ubicazione_full_path', 'ubicazione_detail', 'chiuso',
            'rientro_di', 'data_rientro_prevista', 'causale', 'note'
        ]
    
    def get_cliente_display(self, obj):
        if obj.cliente:
            return obj.cliente.display_name()
        return None
    
    def get_operatore_display(self, obj):
        if obj.operatore:
            return f"{obj.operatore.first_name} {obj.operatore.last_name}".strip() or obj.operatore.username
        return None
    
    def get_documento_display(self, obj):
        if obj.documento:
            return f"{obj.documento.codice} - {obj.documento.descrizione}"
        return None
    
    def get_fascicolo_display(self, obj):
        if obj.fascicolo:
            return f"{obj.fascicolo.codice} - {obj.fascicolo.titolo}"
        return None
    
    def get_protocollo_label(self, obj):
        suf = "E" if obj.direzione == "IN" else "U"
        return f"{obj.anno}/{obj.numero:06d}-{suf}"
    
    def get_ubicazione_full_path(self, obj):
        if obj.ubicazione:
            return obj.ubicazione.full_path
        return None

    def get_target_type(self, obj):
        if obj.target_content_type:
            ct = obj.target_content_type
            return f"{ct.app_label}.{ct.model}"
        return None

    def get_destinatario_anagrafica_display(self, obj):
        if obj.destinatario_anagrafica:
            return obj.destinatario_anagrafica.display_name()
        return None


class MovimentoProtocolloDetailSerializer(MovimentoProtocolloListSerializer):
    """Serializer per dettaglio movimento protocollo"""
    
    class Meta(MovimentoProtocolloListSerializer.Meta):
        model = MovimentoProtocollo
        fields = MovimentoProtocolloListSerializer.Meta.fields


class ProtocollazioneInputSerializer(serializers.Serializer):
    """Serializer per input protocollazione"""
    direzione = serializers.ChoiceField(choices=[('IN', 'Entrata'), ('OUT', 'Uscita')], required=True)
    quando = serializers.DateTimeField(required=False, allow_null=True)
    
    # Campi per ENTRATA
    da_chi = serializers.CharField(required=False, allow_blank=True)
    da_chi_anagrafica = serializers.PrimaryKeyRelatedField(
        queryset=Anagrafica.objects.all(), required=False, allow_null=True
    )
    
    # Campi per USCITA
    a_chi = serializers.CharField(required=False, allow_blank=True)
    a_chi_anagrafica = serializers.PrimaryKeyRelatedField(
        queryset=Anagrafica.objects.all(), required=False, allow_null=True
    )
    data_rientro_prevista = serializers.DateField(required=False, allow_null=True)
    
    # Campi comuni
    ubicazione_id = serializers.IntegerField(required=False, allow_null=True)
    causale = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    target_type = serializers.CharField(required=False, allow_blank=True)
    target_id = serializers.CharField(required=False, allow_blank=True)
    
    def validate_ubicazione_id(self, value):
        if value:
            try:
                UnitaFisica.objects.get(pk=value)
            except UnitaFisica.DoesNotExist:
                raise serializers.ValidationError("Ubicazione non trovata")
        return value
    
    def validate(self, data):
        direzione = data.get('direzione')

        if direzione == 'OUT':
            if not (data.get('a_chi') or data.get('a_chi_anagrafica')):
                raise serializers.ValidationError({"a_chi": "Specificare il destinatario o selezionare un'anagrafica."})
        elif direzione == 'IN':
            if not (data.get('da_chi') or data.get('da_chi_anagrafica')):
                raise serializers.ValidationError({"da_chi": "Specificare il mittente o selezionare un'anagrafica."})

        return data
