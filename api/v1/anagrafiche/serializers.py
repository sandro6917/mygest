"""
Serializers per API Anagrafiche
"""
from rest_framework import serializers
from anagrafiche.models import Anagrafica, Cliente, Indirizzo, ClientiTipo, EmailContatto
from anagrafiche.models_comuni import ComuneItaliano


class ComuneItalianoSerializer(serializers.ModelSerializer):
    """Serializer per comuni italiani (per autocomplete)"""
    denominazione_completa = serializers.ReadOnlyField()
    denominazione_estesa = serializers.ReadOnlyField()
    
    class Meta:
        model = ComuneItaliano
        fields = [
            'id', 'codice_istat', 'codice_belfiore', 'nome', 'nome_alternativo',
            'provincia', 'nome_provincia', 'cap', 'regione',
            'flag_capoluogo', 'denominazione_completa', 'denominazione_estesa'
        ]


class IndirizzoSerializer(serializers.ModelSerializer):
    """Serializer per indirizzi"""
    tipo_indirizzo_display = serializers.CharField(source='get_tipo_indirizzo_display', read_only=True)
    comune_italiano_display = serializers.SerializerMethodField()
    # Campi sincronizzati automaticamente quando c'è comune_italiano
    cap = serializers.CharField(required=False, allow_blank=True)
    comune = serializers.CharField(required=False, allow_blank=True)
    provincia = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Indirizzo
        fields = [
            'id', 'tipo_indirizzo', 'tipo_indirizzo_display', 
            'comune_italiano', 'comune_italiano_display',
            'toponimo', 'indirizzo', 'numero_civico', 
            'frazione', 'cap', 'comune', 'provincia', 'nazione', 
            'principale', 'note',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_comune_italiano_display(self, obj):
        """Restituisce la rappresentazione completa del comune italiano"""
        if obj.comune_italiano:
            return {
                'id': obj.comune_italiano.id,
                'nome': obj.comune_italiano.nome,
                'provincia': obj.comune_italiano.provincia,
                'cap': obj.comune_italiano.cap,
                'denominazione_completa': obj.comune_italiano.denominazione_completa
            }
        return None


class EmailContattoSerializer(serializers.ModelSerializer):
    """Serializer per contatti email"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = EmailContatto
        fields = [
            'id', 'nominativo', 'email', 'tipo', 'tipo_display', 
            'note', 'is_preferito', 'attivo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ClienteNestedSerializer(serializers.ModelSerializer):
    """Serializer compatto per Cliente (nested)"""
    tipo_cliente_display = serializers.CharField(source='tipo_cliente.descrizione', read_only=True)
    
    class Meta:
        model = Cliente
        fields = ['id', 'cliente_dal', 'cliente_al', 'codice_destinatario', 'tipo_cliente', 'tipo_cliente_display']


class AnagraficaListSerializer(serializers.ModelSerializer):
    """Serializer per lista anagrafiche (più compatto)"""
    display_name = serializers.SerializerMethodField()
    is_cliente = serializers.SerializerMethodField()
    
    class Meta:
        model = Anagrafica
        fields = [
            'id', 'tipo', 'display_name', 'codice_fiscale', 'partita_iva',
            'denominazione_abbreviata', 'email', 'pec', 'telefono', 'codice', 
            'is_cliente', 'created_at', 'updated_at'
        ]
    
    def get_display_name(self, obj):
        """Nome visualizzato (ragione sociale o cognome nome)"""
        if obj.tipo == 'PG':
            return obj.ragione_sociale
        return f"{obj.cognome} {obj.nome}".strip()
    
    def get_is_cliente(self, obj):
        """Verifica se è un cliente"""
        return hasattr(obj, 'cliente')


class AnagraficaDetailSerializer(serializers.ModelSerializer):
    """Serializer per dettaglio anagrafica (completo)"""
    display_name = serializers.SerializerMethodField()
    cliente = ClienteNestedSerializer(read_only=True)
    indirizzi = IndirizzoSerializer(many=True, read_only=True)
    contatti_email = EmailContattoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Anagrafica
        fields = [
            'id', 'tipo', 'display_name',
            'ragione_sociale', 'nome', 'cognome',
            'codice_fiscale', 'partita_iva', 'codice',
            'denominazione_abbreviata',
            'pec', 'email', 'telefono', 'indirizzo',
            'note', 'created_at', 'updated_at',
            'cliente', 'indirizzi', 'contatti_email'
        ]
    
    def get_display_name(self, obj):
        """Nome visualizzato"""
        if obj.tipo == 'PG':
            return obj.ragione_sociale
        return f"{obj.cognome} {obj.nome}".strip()


class AnagraficaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creazione/modifica anagrafica"""
    
    # Codice generato automaticamente, non richiesto dall'utente
    codice = serializers.CharField(required=False, allow_blank=True, allow_null=True, read_only=True)
    
    # Campi sincronizzati automaticamente da indirizzi/contatti - READ ONLY
    indirizzo = serializers.CharField(read_only=True, help_text="Sincronizzato da indirizzo principale")
    email = serializers.EmailField(read_only=True, help_text="Sincronizzato da contatto email Generico preferito")
    pec = serializers.EmailField(read_only=True, help_text="Sincronizzato da contatto email PEC preferito")
    
    # Campi per gestione Cliente (opzionali)
    is_cliente = serializers.BooleanField(required=False, default=False, write_only=True)
    cliente_dal = serializers.DateField(required=False, allow_null=True)
    cliente_al = serializers.DateField(required=False, allow_null=True)
    codice_destinatario = serializers.CharField(required=False, allow_blank=True, max_length=7)
    tipo_cliente = serializers.PrimaryKeyRelatedField(
        queryset=ClientiTipo.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Anagrafica
        fields = [
            'id',  # Necessario per il redirect dopo creazione
            'tipo', 'ragione_sociale', 'nome', 'cognome',
            'codice_fiscale', 'partita_iva', 'codice',
            'denominazione_abbreviata',
            'pec', 'email', 'telefono', 'indirizzo', 'note',
            # Campi Cliente
            'is_cliente', 'cliente_dal', 'cliente_al', 'codice_destinatario', 'tipo_cliente'
        ]
        read_only_fields = ['codice', 'indirizzo', 'email', 'pec']
    
    def validate(self, data):
        """Validazione custom"""
        tipo = data.get('tipo')
        
        # PG deve avere ragione_sociale
        if tipo == 'PG' and not data.get('ragione_sociale'):
            raise serializers.ValidationError({
                'ragione_sociale': 'Obbligatorio per persona giuridica'
            })
        
        # PF deve avere nome e cognome
        if tipo == 'PF':
            if not data.get('nome'):
                raise serializers.ValidationError({
                    'nome': 'Obbligatorio per persona fisica'
                })
            if not data.get('cognome'):
                raise serializers.ValidationError({
                    'cognome': 'Obbligatorio per persona fisica'
                })
        
        # Se is_cliente=True e cliente_dal non fornito, usa data odierna
        if data.get('is_cliente') and not data.get('cliente_dal'):
            from datetime import date
            data['cliente_dal'] = date.today()
        
        # Normalizza codice_destinatario
        if data.get('codice_destinatario'):
            data['codice_destinatario'] = data['codice_destinatario'].upper().strip()
        
        return data
    
    def create(self, validated_data):
        """Override create per gestire Cliente"""
        from anagrafiche.utils import get_or_generate_cli
        
        # Rimuovi il codice se presente (sarà generato automaticamente)
        validated_data.pop('codice', None)
        
        # Estrai campi Cliente
        is_cliente = validated_data.pop('is_cliente', False)
        cliente_dal = validated_data.pop('cliente_dal', None)
        cliente_al = validated_data.pop('cliente_al', None)
        codice_destinatario = validated_data.pop('codice_destinatario', '')
        tipo_cliente = validated_data.pop('tipo_cliente', None)
        
        # Crea Anagrafica
        anagrafica = super().create(validated_data)
        
        # Genera codice anagrafica
        get_or_generate_cli(anagrafica)
        
        # Se richiesto, crea anche Cliente
        if is_cliente:
            Cliente.objects.create(
                anagrafica=anagrafica,
                cliente_dal=cliente_dal,
                cliente_al=cliente_al,
                codice_destinatario=codice_destinatario,
                tipo_cliente=tipo_cliente
            )
        
        return anagrafica
    
    def update(self, instance, validated_data):
        """Override update per gestire Cliente"""
        # Estrai campi Cliente
        is_cliente = validated_data.pop('is_cliente', None)
        cliente_dal = validated_data.pop('cliente_dal', None)
        cliente_al = validated_data.pop('cliente_al', None)
        codice_destinatario = validated_data.pop('codice_destinatario', '')
        tipo_cliente = validated_data.pop('tipo_cliente', None)
        
        # Aggiorna Anagrafica
        anagrafica = super().update(instance, validated_data)
        
        # Gestione Cliente
        if is_cliente is not None:
            if is_cliente:
                # Crea o aggiorna Cliente
                cliente, created = Cliente.objects.get_or_create(anagrafica=anagrafica)
                if cliente_dal is not None:
                    cliente.cliente_dal = cliente_dal
                if cliente_al is not None:
                    cliente.cliente_al = cliente_al
                cliente.codice_destinatario = codice_destinatario
                if tipo_cliente is not None:
                    cliente.tipo_cliente = tipo_cliente
                cliente.save()
            else:
                # Rimuovi Cliente se exists
                Cliente.objects.filter(anagrafica=anagrafica).delete()
        
        return anagrafica


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer per Cliente"""
    anagrafica = AnagraficaDetailSerializer(read_only=True)
    tipo_cliente_display = serializers.CharField(source='tipo_cliente.descrizione', read_only=True)
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'anagrafica', 'cliente_dal', 'cliente_al',
            'codice_destinatario', 'tipo_cliente', 'tipo_cliente_display'
        ]


class ClientiTipoSerializer(serializers.ModelSerializer):
    """Serializer per tipi cliente"""
    class Meta:
        model = ClientiTipo
        fields = ['id', 'codice', 'descrizione', 'slug']

