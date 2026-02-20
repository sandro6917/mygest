from __future__ import annotations

from rest_framework import serializers

from comunicazioni.models import Comunicazione, EmailImport, AllegatoComunicazione
from comunicazioni.models_template import (
    FirmaComunicazione,
    TemplateComunicazione,
    TemplateContextField,
)
from anagrafiche.models import EmailContatto, MailingList
from scadenze.models import CodiceTributoF24


class EmailContattoSerializer(serializers.ModelSerializer):
    anagrafica_display = serializers.CharField(source="anagrafica.__str__", read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailContatto
        fields = [
            "id",
            "email",
            "nominativo",
            "tipo",
            "is_preferito",
            "attivo",
            "anagrafica",
            "anagrafica_display",
            "display_name",
        ]
        read_only_fields = ["is_preferito", "attivo"]
    
    def get_display_name(self, obj):
        """Restituisce una stringa formattata per la visualizzazione nell'autocomplete"""
        parts = []
        if obj.nominativo:
            parts.append(obj.nominativo)
        parts.append(f"<{obj.email}>")
        if obj.anagrafica:
            parts.append(f"- {obj.anagrafica.display_name()}")
        return " ".join(parts)


class MailingListSerializer(serializers.ModelSerializer):
    proprietario_display = serializers.CharField(source="proprietario.__str__", read_only=True)
    contatti_count = serializers.IntegerField(source="contatti.count", read_only=True)

    class Meta:
        model = MailingList
        fields = [
            "id",
            "nome",
            "slug",
            "descrizione",
            "attiva",
            "proprietario",
            "proprietario_display",
            "contatti_count",
        ]
        read_only_fields = ["slug", "attiva", "contatti_count"]


class TemplateContextFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateContextField
        fields = [
            "id",
            "template",
            "key",
            "label",
            "field_type",
            "widget",
            "required",
            "help_text",
            "default_value",
            "format_string",
            "choices",
            "source_path",
            "ordering",
            "active",
        ]
        read_only_fields = fields


class TemplateComunicazioneSerializer(serializers.ModelSerializer):
    context_fields = TemplateContextFieldSerializer(many=True, read_only=True)

    class Meta:
        model = TemplateComunicazione
        fields = [
            "id",
            "nome",
            "oggetto",
            "corpo_testo",
            "corpo_html",
            "attivo",
            "data_creazione",
            "data_modifica",
            "context_fields",
        ]
        read_only_fields = ["data_creazione", "data_modifica", "context_fields"]


class FirmaComunicazioneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmaComunicazione
        fields = [
            "id",
            "nome",
            "corpo_testo",
            "corpo_html",
            "attivo",
            "data_creazione",
            "data_modifica",
        ]
        read_only_fields = ["data_creazione", "data_modifica"]


class ComunicazioneSerializer(serializers.ModelSerializer):
    destinatari = serializers.CharField(required=False, allow_blank=True)
    contatti_destinatari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmailContatto.objects.filter(attivo=True),
        required=False,
    )
    liste_destinatari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MailingList.objects.filter(attiva=True),
        required=False,
    )
    template = serializers.PrimaryKeyRelatedField(
        queryset=TemplateComunicazione.objects.all(),
        required=False,
        allow_null=True,
    )
    firma = serializers.PrimaryKeyRelatedField(
        queryset=FirmaComunicazione.objects.all(),
        required=False,
        allow_null=True,
    )
    template_nome = serializers.CharField(source="template.nome", read_only=True)
    firma_nome = serializers.CharField(source="firma.nome", read_only=True)
    protocollo_label = serializers.CharField(read_only=True)
    destinatari_calcolati = serializers.SerializerMethodField()
    destinatari_con_anagrafica = serializers.SerializerMethodField()

    class Meta:
        model = Comunicazione
        fields = [
            "id",
            "tipo",
            "direzione",
            "oggetto",
            "corpo",
            "corpo_html",
            "mittente",
            "destinatari",
            "destinatari_calcolati",
            "destinatari_con_anagrafica",
            "contatti_destinatari",
            "liste_destinatari",
            "template",
            "template_nome",
            "firma",
            "firma_nome",
            "dati_template",
            "stato",
            "log_errore",
            "data_creazione",
            "data_invio",
            "documento_protocollo",
            "protocollo_movimento",
            "protocollo_label",
            "email_message_id",
            "importato_il",
            "import_source",
        ]
        read_only_fields = [
            "stato",
            "log_errore",
            "data_creazione",
            "data_invio",
            "protocollo_movimento",
            "protocollo_label",
            "template_nome",
            "firma_nome",
            "email_message_id",
            "importato_il",
            "import_source",
        ]

    def get_destinatari_calcolati(self, obj: Comunicazione) -> list[str]:
        return obj.get_destinatari_lista()
    
    def get_destinatari_con_anagrafica(self, obj: Comunicazione) -> list[dict]:
        """
        Ritorna lista destinatari con informazioni anagrafica se disponibile.
        Formato: [{"email": "...", "codice_anagrafica": "...", "ragione_sociale": "..."}, ...]
        """
        destinatari_info = []
        
        # Analizza i contatti destinatari diretti
        for contatto in obj.contatti_destinatari.select_related('anagrafica').all():
            if contatto.anagrafica:
                destinatari_info.append({
                    "email": contatto.email,
                    "codice_anagrafica": contatto.anagrafica.codice,
                    "ragione_sociale": contatto.anagrafica.ragione_sociale,
                })
            else:
                destinatari_info.append({
                    "email": contatto.email,
                    "codice_anagrafica": None,
                    "ragione_sociale": None,
                })
        
        # Analizza le mailing list
        for lista in obj.liste_destinatari.prefetch_related('contatti__anagrafica').all():
            for contatto in lista.contatti.filter(attivo=True):
                if contatto.anagrafica:
                    # Evita duplicati
                    if not any(d['email'] == contatto.email for d in destinatari_info):
                        destinatari_info.append({
                            "email": contatto.email,
                            "codice_anagrafica": contatto.anagrafica.codice,
                            "ragione_sociale": contatto.anagrafica.ragione_sociale,
                        })
                else:
                    if not any(d['email'] == contatto.email for d in destinatari_info):
                        destinatari_info.append({
                            "email": contatto.email,
                            "codice_anagrafica": None,
                            "ragione_sociale": None,
                        })
        
        return destinatari_info

    def _process_template_values(self, validated_data):
        """
        Processa corpo, corpo_html e oggetto per sostituire gli ID dei codici tributo
        con i valori formattati quando ci sono dati_template.
        """
        dati_template = validated_data.get("dati_template", {})
        template = validated_data.get("template")
        
        if not dati_template or not template:
            return validated_data
        
        # Mappa degli ID dei codici tributo ai loro valori formattati
        replacements = {}
        
        # Ottieni i context_fields del template
        from comunicazioni.models_template import TemplateContextField
        context_fields = TemplateContextField.objects.filter(
            template=template,
            field_type='codice_tributo',
            active=True
        )
        
        # Per ogni campo di tipo codice_tributo, se c'è un ID in dati_template,
        # recupera il valore formattato
        for field in context_fields:
            if field.key in dati_template:
                raw_value = dati_template[field.key]
                formatted_value = field.parse_raw_input(raw_value)
                if formatted_value and raw_value:
                    # Mappa l'ID al valore formattato
                    replacements[str(raw_value)] = formatted_value
        
        # Sostituisci gli ID con i valori formattati in corpo, corpo_html e oggetto
        if replacements:
            for field_name in ['corpo', 'corpo_html', 'oggetto']:
                if field_name in validated_data and validated_data[field_name]:
                    text = validated_data[field_name]
                    for id_value, formatted_value in replacements.items():
                        text = text.replace(id_value, formatted_value)
                    validated_data[field_name] = text
        
        return validated_data

    def create(self, validated_data):
        contatti = validated_data.pop("contatti_destinatari", [])
        liste = validated_data.pop("liste_destinatari", [])
        dati_template = validated_data.pop("dati_template", {})
        
        # Se destinatari non è fornito, usa stringa vuota come default
        if 'destinatari' not in validated_data or not validated_data['destinatari']:
            validated_data['destinatari'] = ''
        
        # Processa i valori del template prima di creare
        # NOTA: Commentato perché il rendering ora avviene con render_content()
        # validated_data = self._process_template_values({**validated_data, 'dati_template': dati_template})
        
        comunicazione = Comunicazione.objects.create(**validated_data)
        if dati_template:
            comunicazione.dati_template = dati_template
            comunicazione.save(update_fields=["dati_template"])
        if contatti:
            comunicazione.contatti_destinatari.set(contatti)
        if liste:
            comunicazione.liste_destinatari.set(liste)
        comunicazione.sync_destinatari_testo()
        
        # Renderizza il contenuto sostituendo i placeholder con i valori effettivi
        comunicazione.render_content()
        comunicazione.save(update_fields=['oggetto', 'corpo', 'corpo_html'])
        
        return comunicazione

    def update(self, instance, validated_data):
        contatti = validated_data.pop("contatti_destinatari", None)
        liste = validated_data.pop("liste_destinatari", None)
        dati_template = validated_data.pop("dati_template", None)
        
        if instance.is_protocollata:
            if "direzione" in validated_data and validated_data["direzione"] != instance.direzione:
                raise serializers.ValidationError("Impossibile modificare la direzione dopo la protocollazione.")
            if "documento_protocollo" in validated_data and validated_data["documento_protocollo"] != instance.documento_protocollo:
                raise serializers.ValidationError("Impossibile modificare il documento dopo la protocollazione.")
        
        # Se vengono modificati contatti/liste, identifica gli email manuali dal NUOVO valore di destinatari
        manual_emails_from_frontend = None
        if contatti is not None or liste is not None:
            from comunicazioni.models import _split_emails
            
            # Email che il frontend sta inviando nel campo destinatari
            new_destinatari_value = validated_data.get('destinatari', instance.destinatari)
            frontend_emails = _split_emails(new_destinatari_value)
            
            # Tutti gli email derivati dai contatti e liste ATTUALI (prima della modifica)
            old_derived_emails = set()
            for contatto in instance.contatti_destinatari.all():
                if contatto.email:
                    old_derived_emails.add(contatto.email)
            for lista in instance.liste_destinatari.all():
                for contatto in lista.contatti.all():
                    if contatto.email:
                        old_derived_emails.add(contatto.email)
                for extra in lista.indirizzi_extra.all():
                    if extra.email:
                        old_derived_emails.add(extra.email)
            
            # Gli email manuali sono quelli nel frontend che NON erano derivati dai vecchi contatti
            manual_emails_from_frontend = [email for email in frontend_emails if email not in old_derived_emails]
        
        # Processa i valori del template prima di aggiornare
        # NOTA: Commentato perché il rendering ora avviene con render_content()
        # template = validated_data.get("template", instance.template)
        # dati = dati_template if dati_template is not None else instance.dati_template
        # if template and dati:
        #     validated_data = self._process_template_values({
        #         **validated_data,
        #         'template': template,
        #         'dati_template': dati
        #     })
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if dati_template is not None:
            instance.dati_template = dati_template
            instance.save(update_fields=["dati_template"])
        if contatti is not None:
            instance.contatti_destinatari.set(contatti)
        if liste is not None:
            instance.liste_destinatari.set(liste)
        
        # Se abbiamo modificato contatti/liste, ripristina solo gli email manuali dal frontend
        if manual_emails_from_frontend is not None:
            instance.destinatari = ", ".join(manual_emails_from_frontend)
            instance.save(update_fields=["destinatari"])
        
        instance.sync_destinatari_testo()
        
        # Se il corpo testuale è stato modificato, rigenera corpo_html
        # convertendo il testo plain in HTML
        if 'corpo' in validated_data:
            corpo_text = instance.corpo or ''
            # Converti newline in <br> e mantieni la formattazione
            corpo_html_from_text = corpo_text.replace('\n', '<br>')
            
            # Se c'è una firma, aggiungila al corpo_html
            if instance.firma:
                firma_html = instance.firma.get_html()
                if firma_html:
                    # Controlla se la firma è già presente
                    if firma_html not in corpo_html_from_text:
                        corpo_html_from_text += f'<br><br>{firma_html}'
            
            instance.corpo_html = corpo_html_from_text
            instance.save(update_fields=['corpo_html'])
            print(f"✅ Corpo HTML rigenerato dal corpo testuale")
        
        return instance


class EmailImportSerializer(serializers.ModelSerializer):
    comunicazione = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmailImport
        fields = [
            "id",
            "mailbox",
            "uid",
            "message_id",
            "mittente",
            "destinatari",
            "oggetto",
            "data_messaggio",
            "importato_il",
            "comunicazione",
        ]
        read_only_fields = fields


class CodiceTributoF24Serializer(serializers.ModelSerializer):
    """Serializer per i codici tributo F24."""
    
    display = serializers.SerializerMethodField()
    
    class Meta:
        model = CodiceTributoF24
        fields = [
            "id",
            "codice",
            "sezione",
            "descrizione",
            "causale",
            "periodicita",
            "attivo",
            "display",
        ]
        read_only_fields = fields
    
    def get_display(self, obj):
        """Testo per l'autocomplete."""
        return f"{obj.codice} - {obj.descrizione}"


class AllegatoComunicazioneSerializer(serializers.ModelSerializer):
    """
    Serializer per gli allegati delle comunicazioni.
    Gestisce tre tipi: documento, fascicolo, file caricato.
    """
    documento_display = serializers.SerializerMethodField()
    fascicolo_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    tipo = serializers.SerializerMethodField()
    
    class Meta:
        model = AllegatoComunicazione
        fields = [
            "id",
            "comunicazione",
            "documento",
            "documento_display",
            "fascicolo",
            "fascicolo_display",
            "file",
            "file_url",
            "nome_file",
            "filename",
            "tipo",
            "note",
            "data_creazione",
        ]
        read_only_fields = ["id", "comunicazione", "data_creazione", "documento_display", "fascicolo_display", "file_url", "filename", "tipo"]
    
    def to_internal_value(self, data):
        """
        Preprocessa i dati prima della validazione.
        Sanitizza e tronca il nome del file se necessario.
        """
        # Se c'è un file, sanitizza il nome PRIMA della validazione Django
        if 'file' in data and data['file']:
            import os
            from datetime import datetime
            from django.core.files.uploadedfile import UploadedFile
            
            uploaded_file = data['file']
            if isinstance(uploaded_file, UploadedFile):
                original_name = uploaded_file.name
                print(f"🔍 File originale: {original_name} (len={len(original_name)})")
                
                # Sanitizza il nome
                sanitized_name = self._sanitize_filename(original_name)
                print(f"🧹 Nome sanitizzato: {sanitized_name} (len={len(sanitized_name)})")
                
                # Calcola lunghezza massima considerando il path
                now = datetime.now()
                upload_path = f"comunicazioni/allegati/{now.year}/{now.month:02d}/"
                max_total_length = 100
                max_filename_length = max_total_length - len(upload_path)
                
                print(f"📁 Upload path: {upload_path} (len={len(upload_path)})")
                print(f"📏 Max lunghezza nome file: {max_filename_length}")
                
                # Tronca se necessario
                if len(sanitized_name) > max_filename_length:
                    base, ext = os.path.splitext(sanitized_name)
                    max_base_len = max_filename_length - len(ext)
                    if max_base_len < 1:
                        from rest_framework.exceptions import ValidationError
                        raise ValidationError({
                            'file': f'L\'estensione del file è troppo lunga. Max {max_filename_length} caratteri totali.'
                        })
                    truncated_name = base[:max_base_len] + ext
                    print(f"✂️ Nome troncato: {truncated_name} (len={len(truncated_name)})")
                    sanitized_name = truncated_name
                
                # Modifica il nome del file nell'oggetto UploadedFile
                uploaded_file.name = sanitized_name
                data['file'] = uploaded_file
                
                # Imposta anche nome_file se non presente
                if 'nome_file' not in data or not data['nome_file']:
                    data['nome_file'] = sanitized_name
                
                print(f"✅ Nome file finale: {sanitized_name}")
                print(f"✅ Path completo: {upload_path}{sanitized_name} (len={len(upload_path + sanitized_name)})")
        
        return super().to_internal_value(data)
    
    def get_documento_display(self, obj):
        """Descrizione del documento allegato"""
        if obj.documento:
            return str(obj.documento)
        return None
    
    def get_fascicolo_display(self, obj):
        """Descrizione del fascicolo allegato"""
        if obj.fascicolo:
            return f"{obj.fascicolo.titolo} ({obj.fascicolo.documenti.count()} documenti)"
        return None
    
    def get_file_url(self, obj):
        """URL del file (se caricato direttamente)"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_filename(self, obj):
        """Nome del file da visualizzare"""
        return obj.get_filename()
    
    def get_tipo(self, obj):
        """Tipo di allegato: 'documento', 'fascicolo' o 'file'"""
        if obj.documento_id:
            return 'documento'
        elif obj.fascicolo_id:
            return 'fascicolo'
        elif obj.file:
            return 'file'
        return 'unknown'
    
    def validate(self, attrs):
        """Valida che ci sia esattamente un tipo di allegato"""
        print(f"🔍 AllegatoComunicazione validate - attrs ricevuti: {attrs}")
        
        documento = attrs.get('documento')
        fascicolo = attrs.get('fascicolo')
        file = attrs.get('file')
        
        count = sum([
            documento is not None,
            fascicolo is not None,
            bool(file)
        ])
        
        print(f"🔍 documento={documento}, fascicolo={fascicolo}, file={bool(file)}, count={count}")
        
        if count == 0:
            raise serializers.ValidationError(
                "Deve essere specificato almeno un documento, fascicolo o file"
            )
        elif count > 1:
            raise serializers.ValidationError(
                "Può essere specificato solo un tipo di allegato"
            )
        
        return attrs
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizza il nome file rimuovendo caratteri non permessi.
        Mantiene: lettere, numeri, spazi, punti, trattini, underscore
        """
        import re
        import unicodedata
        
        # Normalizza unicode (converte caratteri accentati)
        filename = unicodedata.normalize('NFKD', filename)
        
        # Rimuove caratteri non ASCII
        filename = filename.encode('ASCII', 'ignore').decode('ASCII')
        
        # Sostituisce caratteri non permessi con underscore
        # Permette: lettere, numeri, spazi, punto, trattino, underscore
        filename = re.sub(r'[^a-zA-Z0-9\s._-]', '_', filename)
        
        # Rimuove spazi multipli e underscore multipli
        filename = re.sub(r'\s+', ' ', filename)
        filename = re.sub(r'_+', '_', filename)
        
        # Rimuove spazi all'inizio e alla fine
        filename = filename.strip()
        
        return filename
