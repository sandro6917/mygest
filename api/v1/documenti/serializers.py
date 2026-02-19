"""
Serializers per API Documenti
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from documenti.models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from anagrafiche.models import Cliente
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from archivio_fisico.models import UnitaFisica


class AttributoDefinizioneSerializer(serializers.ModelSerializer):
    obbligatorio = serializers.BooleanField(source='required', read_only=True)
    scelte = serializers.CharField(source='choices', read_only=True)
    
    class Meta:
        model = AttributoDefinizione
        fields = [
            'id', 'tipo_documento', 'codice', 'nome', 'tipo_dato',
            'widget', 'scelte', 'obbligatorio', 'ordine', 'help_text'
        ]


class DocumentiTipoSerializer(serializers.ModelSerializer):
    attributi = AttributoDefinizioneSerializer(many=True, read_only=True)
    help_status = serializers.SerializerMethodField()
    help_visibile_pubblico = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentiTipo
        fields = [
            'id', 'codice', 'nome', 'estensioni_permesse',
            'pattern_codice', 'nome_file_pattern', 'attivo', 'attributi',
            'help_data', 'help_ordine', 'help_status', 'help_visibile_pubblico'
        ]
    
    def get_help_status(self, obj) -> str:
        """Restituisce lo stato dell'help: completo, parziale, da_completare, vuoto"""
        from documenti.help_builder import get_help_status
        return get_help_status(obj.help_data or {})
    
    def get_help_visibile_pubblico(self, obj) -> bool:
        """Indica se l'help è visibile agli utenti non admin"""
        from documenti.help_builder import is_help_visible_to_public
        return is_help_visible_to_public(obj.help_data or {})
    
    def to_representation(self, instance):
        """
        Filtra help_data per utenti non-admin.
        Se help non visibile pubblicamente, restituisce solo metadati.
        """
        data = super().to_representation(instance)
        
        # Ottieni utente dal context
        request = self.context.get('request')
        if not request:
            return data
        
        user = request.user
        is_admin = user.is_staff or user.is_superuser
        
        # Admin vedono tutto
        if is_admin:
            return data
        
        # Non-admin: filtra help_data se non pubblico
        from documenti.help_builder import is_help_visible_to_public
        
        if not is_help_visible_to_public(instance.help_data or {}):
            # Nascondi help_data, mostra solo che non è disponibile
            data['help_data'] = {
                '_meta': {
                    'stato': 'non_disponibile',
                    'messaggio': 'Help in fase di completamento. Disponibile solo per amministratori.'
                }
            }
        
        return data


class AttributoValoreSerializer(serializers.ModelSerializer):
    definizione_detail = AttributoDefinizioneSerializer(source='definizione', read_only=True)
    
    class Meta:
        model = AttributoValore
        fields = ['id', 'documento', 'definizione', 'definizione_detail', 'valore']


class TitolarioVoceSimpleSerializer(serializers.ModelSerializer):
    path_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = TitolarioVoce
        fields = ['id', 'codice', 'titolo', 'parent', 'pattern_codice', 'path_display']


class ClienteSimpleSerializer(serializers.ModelSerializer):
    anagrafica_display = serializers.CharField(source='anagrafica.display_name', read_only=True)
    
    class Meta:
        model = Cliente
        fields = ['id', 'anagrafica', 'anagrafica_display', 'codice_fiscale', 'partita_iva']


class UnitaFisicaSimpleSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = UnitaFisica
        fields = ['id', 'codice', 'nome', 'tipo', 'tipo_display', 'full_path']


class FascicoloSimpleSerializer(serializers.ModelSerializer):
    cliente_display = serializers.CharField(source='cliente.anagrafica.display_name', read_only=True)
    titolario_voce_display = serializers.CharField(source='titolario_voce.path_display', read_only=True)
    
    class Meta:
        model = Fascicolo
        fields = ['id', 'codice', 'titolo', 'cliente', 'cliente_display', 'titolario_voce', 'titolario_voce_display']


class DocumentoListSerializer(serializers.ModelSerializer):
    tipo_detail = DocumentiTipoSerializer(source='tipo', read_only=True)
    cliente_detail = ClienteSimpleSerializer(source='cliente', read_only=True)
    fascicolo_detail = FascicoloSimpleSerializer(source='fascicolo', read_only=True)
    titolario_voce_detail = TitolarioVoceSimpleSerializer(source='titolario_voce', read_only=True)
    ubicazione_detail = UnitaFisicaSimpleSerializer(source='ubicazione', read_only=True)
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id', 'codice', 'tipo', 'tipo_detail', 'fascicolo', 'fascicolo_detail',
            'cliente', 'cliente_detail', 'titolario_voce', 'titolario_voce_detail',
            'descrizione', 'data_documento', 'stato', 'digitale', 'tracciabile',
            'file', 'file_name', 'percorso_archivio', 'tags', 'note',
            'creato_il', 'aggiornato_il', 'out_aperto', 'ubicazione', 'ubicazione_detail'
        ]
    
    def get_file_name(self, obj):
        if obj.file:
            import os
            return os.path.basename(obj.file.name)
        return None


class DocumentoDetailSerializer(serializers.ModelSerializer):
    tipo_detail = DocumentiTipoSerializer(source='tipo', read_only=True)
    cliente_detail = ClienteSimpleSerializer(source='cliente', read_only=True)
    fascicolo_detail = FascicoloSimpleSerializer(source='fascicolo', read_only=True)
    titolario_voce_detail = TitolarioVoceSimpleSerializer(source='titolario_voce', read_only=True)
    attributi = AttributoValoreSerializer(many=True, read_only=True, source='attributi_valori')
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    movimenti_protocollo = serializers.SerializerMethodField()
    protocollo_attivo = serializers.SerializerMethodField()
    ubicazione_detail = UnitaFisicaSimpleSerializer(source='ubicazione', read_only=True)
    
    class Meta:
        model = Documento
        fields = [
            'id', 'codice', 'tipo', 'tipo_detail', 'fascicolo', 'fascicolo_detail',
            'cliente', 'cliente_detail', 'titolario_voce', 'titolario_voce_detail',
            'descrizione', 'data_documento', 'stato', 'digitale', 'tracciabile',
            'file', 'file_name', 'file_url', 'percorso_archivio', 'tags', 'note',
            'creato_il', 'aggiornato_il', 'out_aperto', 'attributi',
            'movimenti_protocollo', 'protocollo_attivo', 'ubicazione', 'ubicazione_detail'
        ]
    
    def get_file_name(self, obj):
        if obj.file:
            import os
            return os.path.basename(obj.file.name)
        return None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_movimenti_protocollo(self, obj):
        """Restituisce i movimenti protocollo del documento"""
        movimenti = obj.movimenti.select_related('destinatario_anagrafica', 'ubicazione').order_by('-data')
        return [self._serialize_movimento_protocollo(mov) for mov in movimenti]
    
    def get_protocollo_attivo(self, obj):
        """Restituisce il protocollo attivo (ultimo movimento)"""
        movimento = obj.movimenti.select_related('destinatario_anagrafica', 'ubicazione').order_by('-data').first()
        if movimento:
            return self._serialize_movimento_protocollo(movimento)
        return None

    def _serialize_movimento_protocollo(self, movimento):
        suf = "E" if movimento.direzione == "IN" else "U"
        ubicazione_detail = None
        if movimento.ubicazione:
            ubicazione_detail = UnitaFisicaSimpleSerializer(movimento.ubicazione).data
        return {
            'id': movimento.id,
            'direzione': movimento.direzione,
            'direzione_display': movimento.get_direzione_display(),
            'protocollo_label': f"{movimento.anno}/{movimento.numero:06d}-{suf}",
            'anno': movimento.anno,
            'numero': movimento.numero,
            'data': movimento.data,
            'destinatario': movimento.destinatario,
            'destinatario_anagrafica': movimento.destinatario_anagrafica_id,
            'destinatario_anagrafica_detail': self._serialize_destinatario_anagrafica(movimento.destinatario_anagrafica),
            'ubicazione': movimento.ubicazione_id,
            'ubicazione_detail': ubicazione_detail,
            'chiuso': movimento.chiuso,
            'causale': movimento.causale,
            'note': movimento.note,
        }

    @staticmethod
    def _serialize_destinatario_anagrafica(anagrafica):
        if not anagrafica:
            return None
        return {
            'id': anagrafica.id,
            'display_name': anagrafica.display_name(),
            'tipo': anagrafica.tipo,
            'codice_fiscale': anagrafica.codice_fiscale,
            'partita_iva': anagrafica.partita_iva,
        }


class DocumentoCreateUpdateSerializer(serializers.ModelSerializer):
    file_operation = serializers.ChoiceField(
        choices=[('copy', 'Copy'), ('move', 'Move')],
        default='copy',
        write_only=True,
        required=False
    )
    attributi = serializers.JSONField(write_only=True, required=False)
    
    # Campo per richiedere eliminazione file originale
    delete_source_file = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text="Se True, crea una richiesta per eliminare il file originale tramite agent"
    )
    source_file_path = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Percorso completo del file originale sul filesystem locale"
    )
    
    class Meta:
        model = Documento
        fields = [
            'tipo', 'cliente', 'fascicolo', 'titolario_voce',
            'descrizione', 'data_documento', 'stato', 'digitale',
            'tracciabile', 'file', 'file_operation', 'tags', 'note', 'attributi', 'ubicazione',
            'delete_source_file', 'source_file_path'
        ]
        extra_kwargs = {
            'cliente': {'required': False},  # Può essere ricavato dal fascicolo
            'ubicazione': {'required': False, 'allow_null': True},
        }
    
    def validate(self, data):
        """Valida che cliente sia presente o ricavabile dal fascicolo"""
        # Se è un update, usa i valori esistenti come fallback
        is_update = self.instance is not None
        
        # Valida tipo documento (solo per creazione)
        if not is_update:
            if not data.get('tipo') or data.get('tipo') == 0:
                raise serializers.ValidationError({
                    'tipo': 'Il tipo documento è obbligatorio'
                })
        
        # Valida cliente (solo per creazione o se entrambi cliente e fascicolo sono None)
        if not is_update:
            if not data.get('cliente') and not data.get('fascicolo'):
                raise serializers.ValidationError({
                    'cliente': 'Il cliente è obbligatorio se non è specificato un fascicolo'
                })
        else:
            # In update, verifica che il cliente non diventi None se scolleghiamo il fascicolo
            # Usa il cliente esistente se non specificato nei dati
            cliente_finale = data.get('cliente', self.instance.cliente)
            fascicolo_finale = data.get('fascicolo', self.instance.fascicolo) if 'fascicolo' not in data else data.get('fascicolo')
            
            if not cliente_finale and not fascicolo_finale:
                raise serializers.ValidationError({
                    'cliente': 'Il cliente è obbligatorio se non è specificato un fascicolo'
                })
        
        # Se c'è un fascicolo ma non il cliente, lo ricava dal fascicolo
        if data.get('fascicolo') and not data.get('cliente'):
            data['cliente'] = data['fascicolo'].cliente
        
        return data
    
    def create(self, validated_data):
        file_operation = validated_data.pop('file_operation', 'copy')
        attributi_data = validated_data.pop('attributi', None)
        delete_source = validated_data.pop('delete_source_file', False)
        source_path = validated_data.pop('source_file_path', '')
        
        import logging
        import os
        logger = logging.getLogger(__name__)
        logger.info(
            "DocumentoCreateUpdateSerializer.create: file_operation=%s, delete_source=%s",
            file_operation,
            delete_source
        )
        
        documento = Documento(**validated_data)
        documento._file_operation = file_operation
        # Indica al modello di NON rinominare automaticamente il file
        # perché lo faremo noi DOPO aver salvato gli attributi dinamici
        documento._skip_auto_rename = True
        self._run_model_clean(documento)
        documento.save()
        
        # Salva attributi se presenti e costruisci la mappa per la rinominazione
        attrs_map = {}
        if attributi_data:
            attrs_map = self._save_attributi(documento, attributi_data)
        
        # Dopo aver salvato gli attributi, forza la rinomina con il pattern aggiornato
        if documento.file:
            try:
                # Aggiorna il percorso archivio (se dipende da campi del documento)
                documento.percorso_archivio = documento._build_path()
                documento.save(update_fields=["percorso_archivio"])
                current_basename = os.path.basename(documento.file.name)
                # Passa la mappa degli attributi appena salvati per evitare cache stale
                logger.info(
                    "API create: rinominazione file per documento id=%s con attrs=%s",
                    documento.pk,
                    attrs_map
                )
                documento._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
                documento._move_file_into_archivio(attrs=attrs_map)
            except Exception as e:
                # Logga l'errore ma evita di bloccare il salvataggio
                logger.exception(
                    "Errore durante rinominazione/spostamento file per documento id=%s: %s",
                    documento.pk,
                    str(e)
                )
        
        # Crea richiesta eliminazione se richiesto
        if delete_source and source_path:
            self._create_deletion_request(documento, source_path)
        
        return documento
    
    def update(self, instance, validated_data):
        file_operation = validated_data.pop('file_operation', 'copy')
        attributi_data = validated_data.pop('attributi', None)
        delete_source = validated_data.pop('delete_source_file', False)
        source_path = validated_data.pop('source_file_path', '')
        
        import logging
        import os
        logger = logging.getLogger(__name__)
        logger.info(
            "DocumentoCreateUpdateSerializer.update: documento id=%s, file_operation=%s",
            instance.pk,
            file_operation
        )
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance._file_operation = file_operation
        # Indica al modello di NON rinominare automaticamente il file
        # perché lo faremo noi DOPO aver salvato gli attributi dinamici
        instance._skip_auto_rename = True
        self._run_model_clean(instance)
        instance.save()
        
        # Aggiorna attributi se presenti e costruisci la mappa per la rinominazione
        attrs_map = {}
        if attributi_data:
            attrs_map = self._save_attributi(instance, attributi_data)
        
        # Dopo aver salvato gli attributi, forza la rinomina con il pattern aggiornato
        if instance.file:
            try:
                # Aggiorna il percorso archivio (se dipende da campi del documento)
                instance.percorso_archivio = instance._build_path()
                instance.save(update_fields=["percorso_archivio"])
                current_basename = os.path.basename(instance.file.name)
                # Passa la mappa degli attributi appena salvati per evitare cache stale
                logger.info(
                    "API update: rinominazione file per documento id=%s con attrs=%s",
                    instance.pk,
                    attrs_map
                )
                instance._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
                instance._move_file_into_archivio(attrs=attrs_map)
            except Exception as e:
                # Logga l'errore ma evita di bloccare il salvataggio
                logger.exception(
                    "Errore durante rinominazione/spostamento file per documento id=%s: %s",
                    instance.pk,
                    str(e)
                )
        
        # Crea richiesta eliminazione se richiesto (solo in update se necessario)
        if delete_source and source_path:
            self._create_deletion_request(instance, source_path)
        
        return instance
    
    def _save_attributi(self, documento, attributi_data):
        """Salva o aggiorna gli attributi del documento e ritorna la mappa degli attributi"""
        from documenti.models import AttributoValore, AttributoDefinizione
        
        attrs_map = {}
        
        for codice, valore in attributi_data.items():
            try:
                # Trova la definizione dell'attributo
                definizione = AttributoDefinizione.objects.get(
                    tipo_documento=documento.tipo,
                    codice=codice
                )
                
                # Aggiorna o crea il valore
                AttributoValore.objects.update_or_create(
                    documento=documento,
                    definizione=definizione,
                    defaults={'valore': valore}
                )
                
                # Aggiungi alla mappa per la rinominazione
                attrs_map[codice] = valore
                
            except AttributoDefinizione.DoesNotExist:
                # Ignora attributi non validi
                pass
            except Exception:
                # Ignora errori silenziosi
                pass
        
        return attrs_map
    
    def _create_deletion_request(self, documento, source_path):
        """Crea una richiesta di eliminazione del file originale"""
        from documenti.models_deletion import FileDeletionRequest
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Ottieni l'utente dalla request
            request = self.context.get('request')
            user = request.user if request and request.user.is_authenticated else None
            
            # Ottieni la dimensione del file se possibile
            file_size = None
            if documento.file:
                try:
                    file_size = documento.file.size
                except:
                    pass
            
            # Crea la richiesta
            deletion_request = FileDeletionRequest.objects.create(
                documento=documento,
                source_path=source_path,
                requested_by=user,
                file_size=file_size
            )
            
            logger.info(
                f"Richiesta eliminazione creata: id={deletion_request.id}, "
                f"documento={documento.codice}, path={source_path}"
            )
            
        except Exception as e:
            logger.error(f"Errore creando richiesta eliminazione: {e}", exc_info=True)

    def _run_model_clean(self, instance: Documento):
        try:
            instance.clean()
        except DjangoValidationError as exc:
            if getattr(exc, 'message_dict', None):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError(exc.messages)



class ImportaCedoliniSerializer(serializers.Serializer):
    """
    Serializer per l'importazione di cedolini paga da file ZIP.
    DEPRECATED: Usare CedoliniImportPreviewSerializer + CedoliniImportConfirmSerializer
    """
    file = serializers.FileField(
        required=True,
        help_text="File ZIP contenente i cedolini in formato PDF"
    )
    duplicate_policy = serializers.ChoiceField(
        choices=['skip', 'replace', 'add'],
        default='skip',
        required=False,
        help_text=(
            "Gestione documenti duplicati:\n"
            "- skip: Non importare se documento già esiste (default)\n"
            "- replace: Sostituire documento esistente\n"
            "- add: Aggiungere comunque il documento (crea duplicato)"
        )
    )
    
    def validate_file(self, value):
        """Valida che il file sia un ZIP e non superi 100MB"""
        # Verifica estensione
        if not value.name.endswith('.zip'):
            raise serializers.ValidationError("Il file deve essere in formato ZIP")
        
        # Verifica dimensione (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Il file è troppo grande ({value.size / 1024 / 1024:.1f}MB). "
                f"Dimensione massima: 100MB"
            )
        
        return value


class CedoliniImportPreviewSerializer(serializers.Serializer):
    """
    Serializer per preview importazione cedolini (Step 1).
    Accetta file ZIP o PDF singolo.
    """
    file = serializers.FileField(
        required=True,
        help_text="File ZIP contenente cedolini PDF oppure singolo PDF"
    )
    
    def validate_file(self, value):
        """Valida che il file sia ZIP o PDF e dimensione accettabile"""
        # Verifica estensione
        filename_lower = value.name.lower()
        if not (filename_lower.endswith('.zip') or filename_lower.endswith('.pdf')):
            raise serializers.ValidationError("Il file deve essere ZIP o PDF")
        
        # Verifica dimensione
        if filename_lower.endswith('.zip'):
            max_size = 500 * 1024 * 1024  # 500MB per ZIP
        else:
            max_size = 50 * 1024 * 1024  # 50MB per singolo PDF
        
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Il file è troppo grande ({value.size / 1024 / 1024:.1f}MB). "
                f"Dimensione massima: {max_size / 1024 / 1024:.0f}MB"
            )
        
        return value


class CedoliniImportConfirmSerializer(serializers.Serializer):
    """
    Serializer per conferma importazione cedolini (Step 2).
    """
    temp_dir = serializers.CharField(
        required=True,
        help_text="Path directory temporanea contenente i PDF estratti (da preview)"
    )
    cedolini = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="Lista cedolini da importare (da preview)"
    )
    fascicolo = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID fascicolo target (opzionale, altrimenti usa fascicolo auto per periodo)"
    )
    duplicate_policy = serializers.ChoiceField(
        choices=['skip', 'replace', 'add'],
        default='skip',
        required=False,
        help_text=(
            "Gestione documenti duplicati:\n"
            "- skip: Salta duplicati (default)\n"
            "- replace: Sostituisci duplicati\n"
            "- add: Crea comunque duplicati"
        )
    )


# ============================================================================
# IMPORTAZIONE UNILAV
# ============================================================================

class UnilavAnagraficaSerializer(serializers.Serializer):
    """Serializer per dati anagrafica (datore o lavoratore)"""
    codice_fiscale = serializers.CharField(max_length=16, required=True)
    tipo = serializers.ChoiceField(choices=['PF', 'PG'], required=True)
    
    # Persona Fisica
    cognome = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    nome = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    sesso = serializers.ChoiceField(choices=['M', 'F', ''], required=False, allow_blank=True, allow_null=True)
    data_nascita = serializers.DateField(required=False, allow_null=True)
    comune_nascita = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    
    # Persona Giuridica
    ragione_sociale = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    
    # Contatti e residenza
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    comune = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    cap = serializers.CharField(max_length=5, required=False, allow_blank=True, allow_null=True)
    indirizzo = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    
    # Flag
    crea_se_non_esiste = serializers.BooleanField(default=True)
    crea_cliente = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        tipo = attrs.get('tipo')
        
        if tipo == 'PF':
            # Persona fisica: richiede cognome e nome
            if not attrs.get('cognome') or not attrs.get('nome'):
                raise serializers.ValidationError({
                    'cognome': 'Cognome e nome sono obbligatori per persone fisiche',
                    'nome': 'Cognome e nome sono obbligatori per persone fisiche'
                })
        elif tipo == 'PG':
            # Persona giuridica: richiede ragione sociale
            if not attrs.get('ragione_sociale'):
                raise serializers.ValidationError({
                    'ragione_sociale': 'Ragione sociale obbligatoria per persone giuridiche'
                })
        
        return attrs


class UnilavDocumentoSerializer(serializers.Serializer):
    """Serializer per dati documento UNILAV"""
    codice_comunicazione = serializers.CharField(max_length=50, required=True)
    tipo_comunicazione = serializers.CharField(max_length=255, required=False, allow_blank=True)
    data_comunicazione = serializers.DateField(required=True)
    
    # Attributi dinamici
    dipendente = serializers.IntegerField(required=False, allow_null=True, 
                                         help_text="ID anagrafica lavoratore")
    tipo = serializers.CharField(max_length=255, required=False, allow_blank=True,
                                 help_text="Tipologia contrattuale")
    data_da = serializers.DateField(required=False, allow_null=True,
                                    help_text="Data inizio rapporto")
    data_a = serializers.DateField(required=False, allow_null=True,
                                   help_text="Data fine rapporto")
    data_proroga = serializers.DateField(required=False, allow_null=True,
                                        help_text="Data fine proroga (per comunicazioni di proroga)")
    data_trasformazione = serializers.DateField(required=False, allow_null=True,
                                               help_text="Data trasformazione (per comunicazioni di trasformazione)")
    causa_trasformazione = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True,
                                                help_text="Motivo/causa trasformazione")
    
    # Dati aggiuntivi (opzionali, salvati in note)
    qualifica = serializers.CharField(max_length=255, required=False, allow_blank=True)
    contratto_collettivo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    livello = serializers.CharField(max_length=100, required=False, allow_blank=True)
    retribuzione = serializers.CharField(max_length=50, required=False, allow_blank=True)
    ore_settimanali = serializers.CharField(max_length=10, required=False, allow_blank=True)
    tipo_orario = serializers.CharField(max_length=100, required=False, allow_blank=True)


class UnilavImportPreviewSerializer(serializers.Serializer):
    """Serializer per anteprima dati estratti da PDF UNILAV"""
    # File PDF caricato
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        """Valida che sia un PDF e non superi 10MB"""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Il file deve essere in formato PDF")
        
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Il file è troppo grande ({value.size / 1024 / 1024:.1f}MB). "
                f"Dimensione massima: 10MB"
            )
        
        return value


class UnilavImportConfirmSerializer(serializers.Serializer):
    """Serializer per conferma e importazione finale dei dati UNILAV"""
    # Dati estratti (modificabili dall'utente)
    datore = UnilavAnagraficaSerializer(required=True)
    lavoratore = UnilavAnagraficaSerializer(required=True)
    documento = UnilavDocumentoSerializer(required=True)
    
    # File PDF originale (da allegare al documento)
    file_path = serializers.CharField(max_length=500, required=False,
                                      help_text="Percorso temporaneo del file PDF caricato")
    file_temp_path = serializers.CharField(max_length=500, required=False,
                                           help_text="Percorso temporaneo del file PDF caricato (alternativo)")
    
    # Azione da compiere in caso di duplicato
    azione = serializers.ChoiceField(
        choices=['crea', 'sovrascrivi', 'duplica'],
        required=False,
        default='crea',
        help_text="Azione: crea (nuovo), sovrascrivi (aggiorna esistente), duplica (crea consapevolmente duplicato)"
    )
    documento_id_esistente = serializers.IntegerField(
        required=False, 
        allow_null=True,
        help_text="ID documento esistente da sovrascrivere (richiesto se azione=sovrascrivi)"
    )
    
    def validate(self, attrs):
        """Validazione incrociata"""
        import logging
        logger = logging.getLogger(__name__)
        
        print("\n" + "="*80)
        print("=== UNILAV SERIALIZER VALIDATION ===")
        print(f"Attrs keys: {list(attrs.keys())}")
        print(f"file_path: {attrs.get('file_path')}")
        print(f"file_temp_path: {attrs.get('file_temp_path')}")
        print("="*80 + "\n")
        
        datore = attrs.get('datore', {})
        lavoratore = attrs.get('lavoratore', {})
        
        # Verifica che datore e lavoratore abbiano CF diversi
        if datore.get('codice_fiscale') == lavoratore.get('codice_fiscale'):
            raise serializers.ValidationError(
                "Il codice fiscale del datore e del lavoratore non possono coincidere"
            )
        
        # Accetta sia file_path che file_temp_path (il frontend invia file_temp_path)
        if not attrs.get('file_path') and not attrs.get('file_temp_path'):
            print("ERRORE: Nessun file_path o file_temp_path presente!")
            logger.error("Nessun file_path o file_temp_path presente!")
            raise serializers.ValidationError({
                'file_path': 'Specificare file_path o file_temp_path'
            })
        
        # Normalizza: usa file_temp_path se presente, altrimenti file_path
        if attrs.get('file_temp_path'):
            print(f"Normalizzazione: file_temp_path -> file_path: {attrs['file_temp_path']}")
            logger.info(f"Normalizzazione: file_temp_path -> file_path: {attrs['file_temp_path']}")
            attrs['file_path'] = attrs['file_temp_path']
        
        # Validazione azione sovrascrittura
        azione = attrs.get('azione', 'crea')
        if azione == 'sovrascrivi':
            if not attrs.get('documento_id_esistente'):
                raise serializers.ValidationError({
                    'documento_id_esistente': 'ID documento esistente obbligatorio per sovrascrittura'
                })
        
        return attrs


# ============================================
# Serializers per Import Sessions
# ============================================

from documenti.models import ImportSession, ImportSessionDocument
from documenti.importers import ImporterRegistry


class ImportSessionListSerializer(serializers.ModelSerializer):
    """Serializer per lista sessioni (senza documenti)"""
    
    tipo_importazione_display = serializers.CharField(
        source='get_tipo_importazione_display',
        read_only=True
    )
    stato_display = serializers.CharField(
        source='get_stato_display',
        read_only=True
    )
    utente_nome = serializers.CharField(
        source='utente.get_full_name',
        read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ImportSession
        fields = [
            'uuid',
            'tipo_importazione',
            'tipo_importazione_display',
            'file_originale_nome',
            'num_documenti_totali',
            'num_documenti_importati',
            'num_documenti_saltati',
            'num_documenti_errore',
            'stato',
            'stato_display',
            'utente',
            'utente_nome',
            'created_at',
            'updated_at',
            'expires_at',
            'completed_at',
            'is_active',
            'progress_percentage',
        ]
        read_only_fields = [
            'uuid',
            'num_documenti_totali',
            'num_documenti_importati',
            'num_documenti_saltati',
            'num_documenti_errore',
            'stato',
            'utente',
            'created_at',
            'updated_at',
            'expires_at',
            'completed_at',
        ]


class ImportSessionDocumentSerializer(serializers.ModelSerializer):
    """Serializer per singolo documento di sessione"""
    
    stato_display = serializers.CharField(
        source='get_stato_display',
        read_only=True
    )
    documento_creato_detail = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportSessionDocument
        fields = [
            'uuid',
            'session',
            'filename',
            'file_path',
            'file_url',
            'file_size',
            'parsed_data',
            'anagrafiche_reperite',
            'valori_editabili',
            'mappatura_db',
            'stato',
            'stato_display',
            'ordine',
            'documento_creato',
            'documento_creato_detail',
            'error_message',
            'error_traceback',
            'parsed_at',
            'imported_at',
        ]
        read_only_fields = [
            'uuid',
            'session',
            'filename',
            'file_path',
            'file_url',
            'file_size',
            'parsed_at',
            'imported_at',
        ]
    
    def get_documento_creato_detail(self, obj):
        """Dettagli documento creato (se presente)"""
        if obj.documento_creato:
            return {
                'id': obj.documento_creato.id,
                'codice': obj.documento_creato.codice,
                'descrizione': obj.documento_creato.descrizione,
                'tipo': obj.documento_creato.tipo.codice if obj.documento_creato.tipo else None,
            }
        return None
    
    def get_file_url(self, obj):
        """URL per preview PDF del documento con signed token"""
        request = self.context.get('request')
        if request and obj.session and obj.uuid and request.user and request.user.is_authenticated:
            from django.core.signing import TimestampSigner
            
            # Genera signed token: "{session_uuid}:{doc_uuid}:{user_id}"
            signer = TimestampSigner()
            token_value = f"{obj.session.uuid}:{obj.uuid}:{request.user.id}"
            signed_token = signer.sign(token_value)
            
            # Costruisci URL con token
            base_url = request.build_absolute_uri(
                f'/api/v1/documenti/import-sessions/{obj.session.uuid}/documents/{obj.uuid}/preview/'
            )
            return f"{base_url}?token={signed_token}"
        return None


class ImportSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer dettagliato per sessione con lista documenti"""
    
    tipo_importazione_display = serializers.CharField(
        source='get_tipo_importazione_display',
        read_only=True
    )
    stato_display = serializers.CharField(
        source='get_stato_display',
        read_only=True
    )
    utente_nome = serializers.CharField(
        source='utente.get_full_name',
        read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    documents = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportSession
        fields = [
            'uuid',
            'tipo_importazione',
            'tipo_importazione_display',
            'file_originale',
            'file_originale_nome',
            'num_documenti_totali',
            'num_documenti_importati',
            'num_documenti_saltati',
            'num_documenti_errore',
            'stato',
            'stato_display',
            'utente',
            'utente_nome',
            'created_at',
            'updated_at',
            'expires_at',
            'completed_at',
            'temp_dir',
            'is_active',
            'progress_percentage',
            'documents',
        ]
        read_only_fields = [
            'uuid',
            'num_documenti_totali',
            'num_documenti_importati',
            'num_documenti_saltati',
            'num_documenti_errore',
            'stato',
            'utente',
            'created_at',
            'updated_at',
            'expires_at',
            'completed_at',
            'temp_dir',
        ]
    
    def get_documents(self, obj):
        """Serializza documenti passando il context per file_url"""
        request = self.context.get('request')
        return ImportSessionDocumentSerializer(
            obj.documents.all(),
            many=True,
            context={'request': request}
        ).data


class ImportSessionCreateSerializer(serializers.Serializer):
    """Serializer per creazione nuova sessione di importazione"""
    
    tipo_importazione = serializers.ChoiceField(
        choices=ImportSession.TIPO_CHOICES,
        required=True,
        help_text="Tipo di importazione (cedolini, unilav, f24, etc.)"
    )
    file = serializers.FileField(
        required=True,
        help_text="File da importare (PDF o ZIP)"
    )
    
    def validate(self, attrs):
        """Validazione tipo + file"""
        tipo = attrs['tipo_importazione']
        file = attrs['file']
        
        # Verifica che il tipo sia registrato
        if not ImporterRegistry.is_registered(tipo):
            raise serializers.ValidationError({
                'tipo_importazione': f"Tipo '{tipo}' non supportato"
            })
        
        # Recupera importer e valida estensione
        importer_class = ImporterRegistry.get_importer(tipo)
        file_ext = f".{file.name.split('.')[-1].lower()}" if '.' in file.name else ''
        
        if file_ext not in importer_class.supported_extensions:
            raise serializers.ValidationError({
                'file': f"Estensione {file_ext} non supportata per {tipo}. "
                        f"Estensioni valide: {', '.join(importer_class.supported_extensions)}"
            })
        
        # Verifica dimensione
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > importer_class.max_file_size_mb:
            raise serializers.ValidationError({
                'file': f"File troppo grande: {file_size_mb:.1f}MB "
                        f"(max {importer_class.max_file_size_mb}MB)"
            })
        
        return attrs


class ImportDocumentUpdateSerializer(serializers.Serializer):
    """Serializer per aggiornamento valori editabili di un documento"""
    
    valori_editabili = serializers.JSONField(
        required=True,
        help_text="Valori modificati dall'utente"
    )


class ImportDocumentCreateSerializer(serializers.Serializer):
    """Serializer per creazione documento da ImportSessionDocument"""
    
    valori_editabili = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Valori modificati dall'utente (merge con parsed_data)"
    )
    cliente_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID cliente a cui associare il documento (se None, dedotto da anagrafica)"
    )
    fascicolo_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID fascicolo a cui associare il documento (opzionale)"
    )
    
    def validate_cliente_id(self, value):
        """Valida che il cliente esista"""
        if value:
            if not Cliente.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Cliente con ID {value} non trovato")
        return value
    
    def validate_fascicolo_id(self, value):
        """Valida che il fascicolo esista"""
        if value:
            if not Fascicolo.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Fascicolo con ID {value} non trovato")
        return value


class ImporterTypeSerializer(serializers.Serializer):
    """Serializer per info su tipi importazione disponibili"""
    
    tipo = serializers.CharField()
    display_name = serializers.CharField()
    supported_extensions = serializers.ListField(child=serializers.CharField())
    batch_mode = serializers.BooleanField()
    max_file_size_mb = serializers.IntegerField()


class ImportaZipLibroUnicoSerializer(serializers.Serializer):
    """
    Serializer per importazione ZIP come documento Libro Unico.
    Endpoint: POST /api/v1/documenti/importa-zip-libro-unico/
    """
    file = serializers.FileField(
        required=True,
        help_text="File ZIP contenente i cedolini"
    )
    azione_duplicati = serializers.ChoiceField(
        choices=['sostituisci', 'duplica', 'skip'],
        required=False,
        default='duplica',
        help_text="Azione in caso di duplicati: sostituisci, duplica o skip"
    )
    
    def validate_file(self, value):
        """Valida che il file sia un ZIP"""
        if not value.name.lower().endswith('.zip'):
            raise serializers.ValidationError("Il file deve essere in formato ZIP")
        
        # Limite dimensione: 100MB
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Il file ZIP supera la dimensione massima di 100MB (dimensione: {value.size / 1024 / 1024:.1f}MB)"
            )
        
        return value

