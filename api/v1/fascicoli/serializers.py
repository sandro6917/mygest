"""
Serializers per API Fascicoli
"""
from rest_framework import serializers
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from archivio_fisico.models import UnitaFisica
from anagrafiche.models import Anagrafica
from pratiche.models import Pratica


class TitolarioVoceSerializer(serializers.ModelSerializer):
    """Serializer per voce di titolario"""
    anagrafica_nome = serializers.CharField(source='anagrafica.nome', read_only=True)
    is_voce_intestata = serializers.BooleanField(read_only=True)
    codice_gerarchico = serializers.CharField(read_only=True)
    
    class Meta:
        model = TitolarioVoce
        fields = [
            'id', 'codice', 'titolo', 'pattern_codice', 'parent',
            'consente_intestazione', 'anagrafica', 'anagrafica_nome',
            'is_voce_intestata', 'codice_gerarchico'
        ]
        read_only_fields = ['is_voce_intestata', 'codice_gerarchico']


class UnitaFisicaSerializer(serializers.ModelSerializer):
    """Serializer per unità fisica"""
    
    class Meta:
        model = UnitaFisica
        fields = ['id', 'tipo', 'codice', 'nome', 'full_path']


class FascicoloListSerializer(serializers.ModelSerializer):
    """Serializer per lista fascicoli"""
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    cliente_display = serializers.SerializerMethodField()
    titolario_voce_detail = TitolarioVoceSerializer(source='titolario_voce', read_only=True)
    parent_display = serializers.SerializerMethodField()
    ubicazione_full_path = serializers.SerializerMethodField()
    num_pratiche = serializers.SerializerMethodField()
    num_sottofascicoli = serializers.SerializerMethodField()
    num_fascicoli_collegati = serializers.SerializerMethodField()
    
    class Meta:
        model = Fascicolo
        fields = [
            'id', 'codice', 'titolo', 'anno', 'stato', 'stato_display',
            'cliente', 'cliente_display', 'titolario_voce', 'titolario_voce_detail',
            'parent', 'parent_display', 'progressivo', 'sub_progressivo',
            'ubicazione', 'ubicazione_full_path', 'retention_anni',
            'created_at', 'updated_at', 'num_pratiche', 'num_sottofascicoli', 'num_fascicoli_collegati'
        ]
    
    def get_cliente_display(self, obj):
        """Restituisce il nome del cliente"""
        if obj.cliente and hasattr(obj.cliente, 'anagrafica'):
            return obj.cliente.anagrafica.display_name()
        return None
    
    def get_parent_display(self, obj):
        """Restituisce il codice del fascicolo padre"""
        if obj.parent:
            return f"{obj.parent.codice} - {obj.parent.titolo}"
        return None
    
    def get_ubicazione_full_path(self, obj):
        """Restituisce il path completo dell'ubicazione"""
        return obj.ubicazione_full_path
    
    def get_num_pratiche(self, obj):
        """Restituisce il numero di pratiche associate"""
        return obj.pratiche.count()
    
    def get_num_sottofascicoli(self, obj):
        """Restituisce il numero di sottofascicoli"""
        return obj.sottofascicoli.count()
    
    def get_num_fascicoli_collegati(self, obj):
        """Restituisce il numero di fascicoli collegati"""
        return obj.fascicoli_collegati.count()


class PraticaSimpleSerializer(serializers.ModelSerializer):
    """Serializer semplificato per pratiche"""
    
    class Meta:
        model = Pratica
        fields = ['id', 'codice', 'oggetto']


class FascicoloDetailSerializer(serializers.ModelSerializer):
    """Serializer per dettaglio fascicolo"""
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    cliente_display = serializers.SerializerMethodField()
    titolario_voce_detail = TitolarioVoceSerializer(source='titolario_voce', read_only=True)
    parent_display = serializers.SerializerMethodField()
    ubicazione_detail = UnitaFisicaSerializer(source='ubicazione', read_only=True)
    ubicazione_full_path = serializers.SerializerMethodField()
    pratica_id = serializers.SerializerMethodField()
    pratica_display = serializers.SerializerMethodField()
    pratiche_details = serializers.SerializerMethodField()
    sottofascicoli = serializers.SerializerMethodField()
    fascicoli_collegati_details = serializers.SerializerMethodField()
    movimenti_protocollo = serializers.SerializerMethodField()
    protocollo_attivo = serializers.SerializerMethodField()
    
    class Meta:
        model = Fascicolo
        fields = [
            'id', 'codice', 'titolo', 'anno', 'stato', 'stato_display',
            'cliente', 'cliente_display', 'titolario_voce', 'titolario_voce_detail',
            'parent', 'parent_display', 'progressivo', 'sub_progressivo',
            'ubicazione', 'ubicazione_detail', 'ubicazione_full_path',
            'retention_anni', 'note', 'path_archivio',
            'pratica_id', 'pratica_display', 'pratiche_details',
            'sottofascicoli', 'fascicoli_collegati_details', 'movimenti_protocollo', 'protocollo_attivo',
            'created_at', 'updated_at'
        ]
    
    def get_cliente_display(self, obj):
        """Restituisce il nome del cliente"""
        if obj.cliente and hasattr(obj.cliente, 'anagrafica'):
            return obj.cliente.anagrafica.display_name()
        return None
    
    def get_parent_display(self, obj):
        """Restituisce il codice del fascicolo padre"""
        if obj.parent:
            return f"{obj.parent.codice} - {obj.parent.titolo}"
        return None
    
    def get_ubicazione_full_path(self, obj):
        """Restituisce il path completo dell'ubicazione"""
        return obj.ubicazione_full_path
    
    def get_movimenti_protocollo(self, obj):
        """Restituisce i movimenti protocollo del fascicolo"""
        movimenti = obj.movimenti_protocollo.all().order_by('-data')
        result = []
        for mov in movimenti:
            suf = "E" if mov.direzione == "IN" else "U"
            result.append({
                'id': mov.id,
                'direzione': mov.direzione,
                'direzione_display': mov.get_direzione_display(),
                'protocollo_label': f"{mov.anno}/{mov.numero:06d}-{suf}",
                'anno': mov.anno,
                'numero': mov.numero,
                'data': mov.data,
                'destinatario': mov.destinatario,
                'chiuso': mov.chiuso,
                'causale': mov.causale,
                'note': mov.note
            })
        return result
    
    def get_protocollo_attivo(self, obj):
        """Restituisce il protocollo attivo (ultimo movimento)"""
        movimento = obj.movimenti_protocollo.order_by('-data').first()
        if movimento:
            suf = "E" if movimento.direzione == "IN" else "U"
            return {
                'id': movimento.id,
                'protocollo_label': f"{movimento.anno}/{movimento.numero:06d}-{suf}",
                'direzione': movimento.direzione,
                'data': movimento.data,
                'chiuso': movimento.chiuso
            }
        return None
    
    def get_pratica_id(self, obj):
        """Restituisce l'ID della prima pratica associata (property pratica)"""
        return obj.pratica_id
    
    def get_pratica_display(self, obj):
        """Restituisce la descrizione della prima pratica associata"""
        pratica = obj.pratica
        if pratica:
            return f"{pratica.codice} - {pratica.oggetto}"
        return None
    
    def get_pratiche_details(self, obj):
        """Restituisce i dettagli di tutte le pratiche associate"""
        return PraticaSimpleSerializer(obj.pratiche.all(), many=True).data
    
    def get_sottofascicoli(self, obj):
        """Restituisce i sottofascicoli"""
        sottofascicoli = obj.sottofascicoli.all()
        return FascicoloListSerializer(sottofascicoli, many=True).data
    
    def get_fascicoli_collegati_details(self, obj):
        """Restituisce i fascicoli collegati"""
        fascicoli_collegati = obj.fascicoli_collegati.all()
        return FascicoloListSerializer(fascicoli_collegati, many=True).data


class FascicoloWriteSerializer(serializers.ModelSerializer):
    """Serializer per creazione/modifica fascicolo"""
    
    class Meta:
        model = Fascicolo
        fields = [
            'titolo', 'anno', 'cliente', 'titolario_voce', 'parent',
            'stato', 'note', 'ubicazione', 'retention_anni', 'pratiche', 'fascicoli_collegati'
        ]
        # Anno può essere impostato solo alla creazione
        extra_kwargs = {
            'anno': {'required': False}
        }
    
    def validate(self, data):
        """Validazione dati"""
        # Se è un update e l'anno è presente nei dati, rimuovilo
        if self.instance and 'anno' in data:
            data.pop('anno')
        
        # Verifica che titolario_voce sia presente (solo per creazione)
        if not self.instance and ('titolario_voce' not in data or not data['titolario_voce']):
            raise serializers.ValidationError({
                'titolario_voce': 'La voce di titolario è obbligatoria'
            })
        
        # Verifica anno valido (solo per creazione)
        if not self.instance:
            anno = data.get('anno')
            if anno and (anno < 1900 or anno > 2100):
                raise serializers.ValidationError({
                    'anno': 'Anno non valido'
                })
        
        # Se c'è un parent, verifica che cliente e titolario coincidano
        parent = data.get('parent')
        if parent:
            if data.get('cliente') and data['cliente'] != parent.cliente:
                raise serializers.ValidationError({
                    'cliente': 'Il cliente deve coincidere con quello del fascicolo padre'
                })
            if 'titolario_voce' in data and data['titolario_voce'] != parent.titolario_voce:
                raise serializers.ValidationError({
                    'titolario_voce': 'La voce di titolario deve coincidere con quella del fascicolo padre'
                })
            if not self.instance and data.get('anno') != parent.anno:
                raise serializers.ValidationError({
                    'anno': 'L\'anno deve coincidere con quello del fascicolo padre'
                })
        
        return data
