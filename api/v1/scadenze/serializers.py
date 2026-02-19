"""
Serializers per API Scadenze
"""
from rest_framework import serializers
from scadenze.models import Scadenza, ScadenzaAlert, ScadenzaOccorrenza
from django.contrib.auth import get_user_model

User = get_user_model()


class ScadenzaAlertSerializer(serializers.ModelSerializer):
    """Serializer per alert individuali"""
    offset_alert_periodo_display = serializers.CharField(source='get_offset_alert_periodo_display', read_only=True)
    metodo_alert_display = serializers.CharField(source='get_metodo_alert_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    
    class Meta:
        model = ScadenzaAlert
        fields = [
            'id',
            'occorrenza',  # Foreign key all'occorrenza (required per create)
            'offset_alert',
            'offset_alert_periodo',
            'offset_alert_periodo_display',
            'metodo_alert',
            'metodo_alert_display',
            'alert_config',
            'alert_programmata_il',
            'alert_inviata_il',
            'stato',
            'stato_display',
            'creato_il',
            'aggiornato_il',
        ]
        read_only_fields = ['id', 'alert_programmata_il', 'creato_il', 'aggiornato_il']


class UserSimpleSerializer(serializers.ModelSerializer):
    """Serializer semplificato per User"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PraticaSimpleSerializer(serializers.Serializer):
    """Serializer semplificato per Pratica"""
    id = serializers.IntegerField()
    numero = serializers.CharField()
    oggetto = serializers.CharField()
    
    
class FascicoloSimpleSerializer(serializers.Serializer):
    """Serializer semplificato per Fascicolo"""
    id = serializers.IntegerField()
    numero = serializers.CharField()
    oggetto = serializers.CharField()
    

class DocumentoSimpleSerializer(serializers.Serializer):
    """Serializer semplificato per Documento"""
    id = serializers.IntegerField()
    numero_protocollo = serializers.CharField()
    oggetto = serializers.CharField()


class ScadenzaListSerializer(serializers.ModelSerializer):
    """Serializer per lista scadenze"""
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    priorita_display = serializers.CharField(source='get_priorita_display', read_only=True)
    periodicita_display = serializers.CharField(source='get_periodicita_display', read_only=True)
    creato_da_nome = serializers.CharField(source='creato_da.get_full_name', read_only=True)
    num_assegnatari = serializers.IntegerField(source='num_assegnatari_count', read_only=True)
    num_occorrenze = serializers.IntegerField(source='num_occorrenze_count', read_only=True)
    prossima_occorrenza = serializers.DateTimeField(source='prossima_occorrenza_data', read_only=True)
    
    class Meta:
        model = Scadenza
        fields = [
            'id', 'titolo', 'descrizione', 'stato', 'stato_display',
            'priorita', 'priorita_display', 'categoria', 'data_scadenza',
            'periodicita', 'periodicita_display', 'periodicita_intervallo',
            'creato_da', 'creato_da_nome', 'num_assegnatari',
            'num_occorrenze', 'prossima_occorrenza',
            'creato_il', 'aggiornato_il'
        ]


class ScadenzaDetailSerializer(serializers.ModelSerializer):
    """Serializer dettagliato per scadenza singola"""
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    priorita_display = serializers.CharField(source='get_priorita_display', read_only=True)
    periodicita_display = serializers.CharField(source='get_periodicita_display', read_only=True)
    creato_da_detail = UserSimpleSerializer(source='creato_da', read_only=True)
    assegnatari_detail = UserSimpleSerializer(many=True, source='assegnatari', read_only=True)
    pratiche_detail = serializers.SerializerMethodField()
    fascicoli_detail = serializers.SerializerMethodField()
    documenti_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Scadenza
        fields = [
            'id', 'titolo', 'descrizione', 'stato', 'stato_display',
            'priorita', 'priorita_display', 'categoria', 'note_interne',
            'data_scadenza',
            'creato_da', 'creato_da_detail',
            'assegnatari', 'assegnatari_detail',
            'pratiche', 'pratiche_detail',
            'fascicoli', 'fascicoli_detail',
            'documenti', 'documenti_detail',
            'comunicazione_destinatari', 'comunicazione_modello',
            'periodicita', 'periodicita_display', 'periodicita_intervallo',
            'periodicita_config',
            'google_calendar_calendar_id', 'google_calendar_synced_at',
            'creato_il', 'aggiornato_il'
        ]
    
    def get_pratiche_detail(self, obj):
        """Restituisce dettagli delle pratiche"""
        pratiche = obj.pratiche.all()
        return [
            {
                'id': p.id,
                'numero': p.codice,
                'oggetto': p.oggetto
            }
            for p in pratiche
        ]
    
    def get_fascicoli_detail(self, obj):
        """Restituisce dettagli dei fascicoli"""
        fascicoli = obj.fascicoli.all()
        return [
            {
                'id': f.id,
                'numero': f.codice,
                'oggetto': f.titolo
            }
            for f in fascicoli
        ]
    
    def get_documenti_detail(self, obj):
        """Restituisce dettagli dei documenti"""
        documenti = obj.documenti.all()
        return [
            {
                'id': d.id,
                'numero_protocollo': d.codice or '',
                'oggetto': d.descrizione
            }
            for d in documenti
        ]


class ScadenzaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creazione e aggiornamento scadenza"""
    
    class Meta:
        model = Scadenza
        fields = [
            'titolo', 'descrizione', 'stato', 'priorita', 'categoria',
            'note_interne', 'assegnatari',
            'pratiche', 'fascicoli', 'documenti',
            'comunicazione_destinatari', 'comunicazione_modello',
            'periodicita', 'periodicita_intervallo', 'periodicita_config',
            'num_occorrenze', 'data_scadenza',
            'google_calendar_calendar_id'
        ]


class ScadenzaOccorrenzaSerializer(serializers.ModelSerializer):
    """Serializer per occorrenze"""
    metodo_alert_display = serializers.CharField(source='get_metodo_alert_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    scadenza_titolo = serializers.CharField(source='scadenza.titolo', read_only=True)
    alerts = ScadenzaAlertSerializer(many=True, read_only=True)
    num_alerts = serializers.SerializerMethodField()
    
    # Nested scadenza dettagli (read-only)
    scadenza_dettaglio = serializers.SerializerMethodField()
    
    class Meta:
        model = ScadenzaOccorrenza
        fields = [
            'id', 'scadenza', 'scadenza_dettaglio', 'scadenza_titolo', 'titolo', 'descrizione',
            'inizio', 'fine', 'giornaliera', 'metodo_alert', 'metodo_alert_display',
            'offset_alert_minuti', 'alert_config', 'alert_programmata_il',
            'alert_inviata_il', 'stato', 'stato_display',
            'alerts', 'num_alerts',
            'google_calendar_event_id', 'google_calendar_synced_at',
            'creato_il', 'aggiornato_il'
        ]
        read_only_fields = [
            'scadenza_dettaglio',
            'alert_programmata_il', 'alert_inviata_il',
            'google_calendar_event_id', 'google_calendar_synced_at',
            'creato_il', 'aggiornato_il'
        ]
    
    def get_scadenza_dettaglio(self, obj):
        """Restituisce i dati completi della scadenza"""
        return {
            'id': obj.scadenza.id,
            'titolo': obj.scadenza.titolo,
            'descrizione': obj.scadenza.descrizione,
            'priorita': obj.scadenza.priorita,
            'categoria': obj.scadenza.categoria,
            'periodicita': obj.scadenza.periodicita,
            'stato': obj.scadenza.stato,
        }
    
    def get_num_alerts(self, obj):
        """Restituisce il numero di alert configurati"""
        return obj.alerts.count()
