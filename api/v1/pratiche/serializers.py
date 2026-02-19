"""
Serializers per API Pratiche
"""
from rest_framework import serializers
from pratiche.models import Pratica, PraticheTipo, PraticaNota
from anagrafiche.models import Cliente


class PraticheTipoSerializer(serializers.ModelSerializer):
    """Serializer per tipi pratica"""
    
    class Meta:
        model = PraticheTipo
        fields = ['id', 'codice', 'nome', 'prefisso_codice', 'pattern_codice']


class ClienteSimpleSerializer(serializers.ModelSerializer):
    """Serializer semplificato per Cliente"""
    anagrafica_display = serializers.CharField(source='anagrafica.display_name', read_only=True)
    anagrafica = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Cliente
        fields = ['id', 'anagrafica', 'anagrafica_display', 'codice_fiscale', 'partita_iva']


class PraticaListSerializer(serializers.ModelSerializer):
    """Serializer per lista pratiche"""
    tipo_detail = PraticheTipoSerializer(source='tipo', read_only=True)
    cliente_detail = ClienteSimpleSerializer(source='cliente', read_only=True)
    responsabile_nome = serializers.CharField(source='responsabile.get_full_name', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    num_note = serializers.SerializerMethodField()
    ultima_nota = serializers.SerializerMethodField()
    
    class Meta:
        model = Pratica
        fields = [
            'id', 'codice', 'tipo', 'tipo_detail', 'cliente', 'cliente_detail',
            'oggetto', 'stato', 'stato_display', 'responsabile', 'responsabile_nome',
            'data_apertura', 'data_chiusura', 'periodo_riferimento', 'data_riferimento',
            'num_note', 'ultima_nota'
        ]
    
    def get_num_note(self, obj):
        """Restituisce il numero di note collegate"""
        return obj.note_collegate.count()
    
    def get_ultima_nota(self, obj):
        """Restituisce il testo dell'ultima nota"""
        ultima = obj.note_collegate.first()  # Già ordinato per -data, -id nel model
        if ultima:
            # Limita il testo a 100 caratteri
            testo = ultima.testo
            return testo[:100] + '...' if len(testo) > 100 else testo
        return None


class FascicoloSimpleSerializer(serializers.Serializer):
    """Serializer semplificato per fascicoli in pratica detail"""
    id = serializers.IntegerField()
    codice = serializers.CharField()
    titolo = serializers.CharField()
    stato = serializers.CharField()
    stato_display = serializers.CharField(source='get_stato_display')


class PraticaNotaListSerializer(serializers.ModelSerializer):
    """Serializer semplificato per lista note in pratica detail"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    
    class Meta:
        model = PraticaNota
        fields = ['id', 'tipo', 'tipo_display', 'testo', 'data', 'stato', 'stato_display']


class ScadenzaSimpleSerializer(serializers.Serializer):
    """Serializer semplificato per scadenze in pratica detail"""
    id = serializers.IntegerField()
    titolo = serializers.CharField()
    descrizione = serializers.CharField()
    stato = serializers.CharField()
    stato_display = serializers.CharField(source='get_stato_display')
    priorita = serializers.CharField()
    priorita_display = serializers.CharField(source='get_priorita_display')
    data_scadenza = serializers.DateField()
    categoria = serializers.CharField()


class PraticaDetailSerializer(serializers.ModelSerializer):
    """Serializer dettagliato per pratica singola"""
    tipo_detail = PraticheTipoSerializer(source='tipo', read_only=True)
    cliente_detail = ClienteSimpleSerializer(source='cliente', read_only=True)
    responsabile_nome = serializers.CharField(source='responsabile.get_full_name', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    periodo_riferimento_display = serializers.CharField(source='get_periodo_riferimento_display', read_only=True)
    note_collegate = PraticaNotaListSerializer(many=True, read_only=True)
    fascicoli = serializers.SerializerMethodField()
    scadenze = serializers.SerializerMethodField()
    
    class Meta:
        model = Pratica
        fields = [
            'id', 'codice', 'tipo', 'tipo_detail', 'cliente', 'cliente_detail',
            'oggetto', 'stato', 'stato_display', 'responsabile', 'responsabile_nome',
            'data_apertura', 'data_chiusura', 'periodo_riferimento', 'periodo_riferimento_display',
            'data_riferimento', 'periodo_key', 'progressivo', 'note', 'tag', 'note_collegate',
            'fascicoli', 'scadenze'
        ]
    
    def get_fascicoli(self, obj):
        """Restituisce la lista dei fascicoli associati"""
        fascicoli = obj.fascicoli.all()
        return FascicoloSimpleSerializer(fascicoli, many=True).data
    
    def get_scadenze(self, obj):
        """Restituisce la lista delle scadenze collegate"""
        scadenze = obj.scadenze.all()
        return ScadenzaSimpleSerializer(scadenze, many=True).data


class PraticaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creazione e aggiornamento pratica"""
    
    class Meta:
        model = Pratica
        fields = [
            'tipo', 'cliente', 'oggetto', 'stato', 'responsabile',
            'periodo_riferimento', 'data_riferimento', 'data_chiusura', 'note', 'tag'
        ]
    
    def create(self, validated_data):
        pratica = Pratica(**validated_data)
        pratica.save()
        return pratica
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PraticaNotaSerializer(serializers.ModelSerializer):
    """Serializer per note pratiche"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    
    class Meta:
        model = PraticaNota
        fields = [
            'id', 'pratica', 'tipo', 'tipo_display', 'testo', 'data', 
            'stato', 'stato_display'
        ]
    
    def create(self, validated_data):
        return PraticaNota.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        # Non aggiornare la pratica se non è specificata
        validated_data.pop('pratica', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
