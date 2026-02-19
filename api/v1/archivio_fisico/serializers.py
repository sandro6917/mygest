"""
Serializers per API Archivio Fisico
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from archivio_fisico.models import (
    OperazioneArchivio,
    RigaOperazioneArchivio,
    UnitaFisica,
    CollocazioneFisica,
    VerbaleConsegnaTemplate,
)
from anagrafiche.models import Anagrafica
from documenti.models import Documento
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'display_name']

    def get_display_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username


class AnagraficaSimpleSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Anagrafica
        fields = ['id', 'codice', 'cognome', 'nome', 'ragione_sociale', 'display_name']

    def get_display_name(self, obj):
        return obj.display_name()


class UnitaFisicaSimpleSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    parent_nome = serializers.CharField(source='parent.nome', read_only=True, allow_null=True)
    cliente_nome = serializers.SerializerMethodField()

    class Meta:
        model = UnitaFisica
        fields = [
            'id', 'codice', 'nome', 'tipo', 'tipo_display', 'parent', 'parent_nome',
            'full_path', 'attivo', 'archivio_fisso', 'cliente', 'cliente_nome'
        ]
    
    def get_cliente_nome(self, obj):
        if obj.cliente and obj.cliente.anagrafica:
            return obj.cliente.anagrafica.display_name()
        return None


class UnitaFisicaDetailSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    parent_detail = UnitaFisicaSimpleSerializer(source='parent', read_only=True)
    ancestors = serializers.SerializerMethodField()
    figli_count = serializers.SerializerMethodField()
    cliente_nome = serializers.SerializerMethodField()

    class Meta:
        model = UnitaFisica
        fields = [
            'id', 'prefisso_codice', 'progressivo_codice', 'codice', 'nome', 'tipo',
            'tipo_display', 'parent', 'parent_detail', 'ordine', 'attivo', 'archivio_fisso',
            'cliente', 'cliente_nome', 'note', 'full_path', 'progressivo', 'created_at', 'updated_at',
            'ancestors', 'figli_count'
        ]

    def get_ancestors(self, obj):
        return [{'id': u.id, 'codice': u.codice, 'nome': u.nome, 'tipo': u.tipo} for u in obj.ancestors()]

    def get_figli_count(self, obj):
        return obj.figli.count()
    
    def get_cliente_nome(self, obj):
        if obj.cliente and obj.cliente.anagrafica:
            return obj.cliente.anagrafica.display_name()
        return None


class DocumentoSimpleSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    ubicazione_nome = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            'id', 'codice', 'tipo', 'tipo_nome', 'descrizione', 'data_documento',
            'stato', 'stato_display', 'digitale', 'tracciabile',
            'ubicazione', 'ubicazione_nome'
        ]

    def get_ubicazione_nome(self, obj):
        if obj.ubicazione:
            return obj.ubicazione.full_path
        return None


class FascicoloSimpleSerializer(serializers.ModelSerializer):
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    cliente_nome = serializers.SerializerMethodField()
    ubicazione_nome = serializers.SerializerMethodField()

    class Meta:
        model = Fascicolo
        fields = [
            'id', 'codice', 'titolo', 'anno', 'numero', 'stato', 'stato_display',
            'cliente', 'cliente_nome', 'ubicazione', 'ubicazione_nome'
        ]

    def get_cliente_nome(self, obj):
        if obj.cliente and hasattr(obj.cliente, 'anagrafica'):
            return obj.cliente.anagrafica.display_name()
        return None

    def get_ubicazione_nome(self, obj):
        if obj.ubicazione:
            return obj.ubicazione.full_path
        return None


class MovimentoProtocolloSimpleSerializer(serializers.ModelSerializer):
    direzione_display = serializers.CharField(source='get_direzione_display', read_only=True)

    class Meta:
        model = MovimentoProtocollo
        fields = [
            'id', 'numero', 'anno', 'direzione', 'direzione_display', 'data',
            'documento', 'fascicolo'
        ]


class RigaOperazioneArchivioSerializer(serializers.ModelSerializer):
    documento_detail = DocumentoSimpleSerializer(source='documento', read_only=True)
    fascicolo_detail = FascicoloSimpleSerializer(source='fascicolo', read_only=True)
    movimento_protocollo_detail = MovimentoProtocolloSimpleSerializer(source='movimento_protocollo', read_only=True)
    unita_fisica_sorgente_detail = UnitaFisicaSimpleSerializer(source='unita_fisica_sorgente', read_only=True)
    unita_fisica_destinazione_detail = UnitaFisicaSimpleSerializer(source='unita_fisica_destinazione', read_only=True)
    oggetto_display = serializers.SerializerMethodField()

    class Meta:
        model = RigaOperazioneArchivio
        fields = [
            'id', 'operazione', 'fascicolo', 'fascicolo_detail', 'documento', 'documento_detail',
            'movimento_protocollo', 'movimento_protocollo_detail',
            'unita_fisica_sorgente', 'unita_fisica_sorgente_detail',
            'unita_fisica_destinazione', 'unita_fisica_destinazione_detail',
            'stato_precedente', 'stato_successivo', 'note', 'oggetto_display'
        ]

    def get_oggetto_display(self, obj):
        if obj.documento:
            return f"DOC: {obj.documento.codice} - {obj.documento.descrizione}"
        elif obj.fascicolo:
            return f"FASC: {obj.fascicolo.codice} - {obj.fascicolo.titolo}"
        return "N/A"


class RigaOperazioneArchivioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RigaOperazioneArchivio
        fields = [
            'fascicolo', 'documento', 'movimento_protocollo',
            'unita_fisica_sorgente', 'unita_fisica_destinazione',
            'stato_precedente', 'stato_successivo', 'note'
        ]

    def to_internal_value(self, data):
        print(f"  [RIGA] to_internal_value ricevuto: {data}")
        try:
            result = super().to_internal_value(data)
            print(f"  [RIGA] to_internal_value risultato: {result}")
            return result
        except Exception as e:
            print(f"  [RIGA] ERRORE in to_internal_value: {e}")
            raise

    def validate(self, data):
        """Valida che sia specificato almeno un documento o un fascicolo"""
        print(f"  [RIGA] validate ricevuto: {data}")
        if not data.get('documento') and not data.get('fascicolo'):
            raise serializers.ValidationError(
                "Specificare almeno un documento o un fascicolo"
            )
        if data.get('documento') and data.get('fascicolo'):
            raise serializers.ValidationError(
                "Specificare solo un documento o un fascicolo, non entrambi"
            )
        return data


class OperazioneArchivioListSerializer(serializers.ModelSerializer):
    tipo_operazione_display = serializers.CharField(source='get_tipo_operazione_display', read_only=True)
    referente_interno_detail = UserSimpleSerializer(source='referente_interno', read_only=True)
    referente_esterno_detail = AnagraficaSimpleSerializer(source='referente_esterno', read_only=True)
    righe_count = serializers.SerializerMethodField()
    verbale_scan_url = serializers.SerializerMethodField()

    class Meta:
        model = OperazioneArchivio
        fields = [
            'id', 'tipo_operazione', 'tipo_operazione_display', 'data_ora',
            'referente_interno', 'referente_interno_detail',
            'referente_esterno', 'referente_esterno_detail',
            'note', 'verbale_scan', 'verbale_scan_url', 'righe_count'
        ]

    def get_righe_count(self, obj):
        return obj.righe.count()
    
    def get_verbale_scan_url(self, obj):
        if obj.verbale_scan:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.verbale_scan.url)
        return None


class OperazioneArchivioDetailSerializer(serializers.ModelSerializer):
    tipo_operazione_display = serializers.CharField(source='get_tipo_operazione_display', read_only=True)
    referente_interno_detail = UserSimpleSerializer(source='referente_interno', read_only=True)
    referente_esterno_detail = AnagraficaSimpleSerializer(source='referente_esterno', read_only=True)
    righe = RigaOperazioneArchivioSerializer(many=True, read_only=True)
    verbale_scan_url = serializers.SerializerMethodField()

    class Meta:
        model = OperazioneArchivio
        fields = [
            'id', 'tipo_operazione', 'tipo_operazione_display', 'data_ora',
            'referente_interno', 'referente_interno_detail',
            'referente_esterno', 'referente_esterno_detail',
            'note', 'verbale_scan', 'verbale_scan_url', 'righe'
        ]
    
    def get_verbale_scan_url(self, obj):
        if obj.verbale_scan:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.verbale_scan.url)
        return None


class OperazioneArchivioCreateSerializer(serializers.ModelSerializer):
    righe = RigaOperazioneArchivioCreateSerializer(many=True, required=False)

    class Meta:
        model = OperazioneArchivio
        fields = [
            'id', 'tipo_operazione', 'referente_interno', 'referente_esterno',
            'note', 'verbale_scan', 'righe'
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        print(f"\n{'*'*50}")
        print(f"TO_INTERNAL_VALUE - Dati RAW ricevuti:")
        print(f"  Keys: {data.keys() if hasattr(data, 'keys') else 'N/A'}")
        print(f"  tipo_operazione: {data.get('tipo_operazione') if hasattr(data, 'get') else 'N/A'}")
        print(f"  righe in data: {'righe' in data if hasattr(data, '__contains__') else 'N/A'}")
        if 'righe' in data:
            print(f"  righe type: {type(data['righe'])}")
            print(f"  righe length: {len(data['righe']) if hasattr(data['righe'], '__len__') else 'N/A'}")
            print(f"  righe content: {data['righe']}")
        print(f"{'*'*50}\n")
        return super().to_internal_value(data)

    def validate(self, data):
        print(f"\n{'='*50}")
        print(f"VALIDATE - Dati ricevuti:")
        print(f"  tipo_operazione: {data.get('tipo_operazione')}")
        print(f"  referente_interno: {data.get('referente_interno')}")
        print(f"  referente_esterno: {data.get('referente_esterno')}")
        print(f"  Righe: {len(data.get('righe', []))} righe")
        for i, riga in enumerate(data.get('righe', [])):
            print(f"    Riga {i+1}: doc={riga.get('documento')}, fasc={riga.get('fascicolo')}, dest={riga.get('unita_fisica_destinazione')}")
        print(f"{'='*50}\n")
        return data

    def create(self, validated_data):
        print(f"\n{'='*50}")
        print(f"CREATE - Inizio creazione operazione")
        print(f"  Validated data keys: {validated_data.keys()}")
        
        righe_data = validated_data.pop('righe', [])
        print(f"  Righe estratte: {len(righe_data)}")
        
        operazione = OperazioneArchivio.objects.create(**validated_data)
        print(f"  Operazione creata con ID: {operazione.id}")
        
        for i, riga_data in enumerate(righe_data):
            print(f"  Creazione riga {i+1}/{len(righe_data)}: {riga_data}")
            try:
                riga = RigaOperazioneArchivio.objects.create(operazione=operazione, **riga_data)
                print(f"    ✓ Riga creata con ID: {riga.id}")
                
                # Aggiorna ubicazione documento o fascicolo con il valore di "A Unità"
                if riga.unita_fisica_destinazione:
                    if riga.documento:
                        riga.documento.ubicazione = riga.unita_fisica_destinazione
                        riga.documento.save(update_fields=['ubicazione'])
                        print(f"    ✓ Aggiornata ubicazione documento {riga.documento.id} → {riga.unita_fisica_destinazione.id}")
                    elif riga.fascicolo:
                        riga.fascicolo.ubicazione = riga.unita_fisica_destinazione
                        riga.fascicolo.save(update_fields=['ubicazione'])
                        print(f"    ✓ Aggiornata ubicazione fascicolo {riga.fascicolo.id} → {riga.unita_fisica_destinazione.id}")
            except Exception as e:
                print(f"    ✗ ERRORE creazione riga {i+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
        
        print(f"CREATE - Fine. Totale righe create: {operazione.righe.count()}")
        print(f"{'='*50}\n")
        return operazione

    def update(self, instance, validated_data):
        righe_data = validated_data.pop('righe', None)
        
        # Aggiorna i campi dell'operazione
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Se sono fornite nuove righe, sostituisci le esistenti
        if righe_data is not None:
            instance.righe.all().delete()
            for riga_data in righe_data:
                riga = RigaOperazioneArchivio.objects.create(operazione=instance, **riga_data)
                
                # Aggiorna ubicazione documento o fascicolo con il valore di "A Unità"
                if riga.unita_fisica_destinazione:
                    if riga.documento:
                        riga.documento.ubicazione = riga.unita_fisica_destinazione
                        riga.documento.save(update_fields=['ubicazione'])
                    elif riga.fascicolo:
                        riga.fascicolo.ubicazione = riga.unita_fisica_destinazione
                        riga.fascicolo.save(update_fields=['ubicazione'])
        
        return instance


class VerbaleConsegnaTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerbaleConsegnaTemplate
        fields = [
            'id', 'nome', 'slug', 'descrizione', 'file_template',
            'filename_pattern', 'attivo', 'is_default',
            'created_at', 'updated_at'
        ]


class CollocazioneFisicaSerializer(serializers.ModelSerializer):
    unita_detail = UnitaFisicaSimpleSerializer(source='unita', read_only=True)
    documento_detail = DocumentoSimpleSerializer(source='documento', read_only=True)

    class Meta:
        model = CollocazioneFisica
        fields = [
            'id', 'content_type', 'object_id', 'documento', 'documento_detail',
            'unita', 'unita_detail', 'attiva', 'dal', 'al', 'note',
            'created_at', 'updated_at'
        ]
