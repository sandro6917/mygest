from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _split_emails(value: str) -> list[str]:
    parts = [p.strip() for p in (value or "").replace(";", ",").split(",")]
    return [p for p in parts if p]

class Comunicazione(models.Model):
    class Direzione(models.TextChoices):
        IN = "IN", _("Entrata")
        OUT = "OUT", _("Uscita")

    class TipoComunicazione(models.TextChoices):
        AVVISO_SCADENZA = "AVVISO", _("Avviso scadenza")
        INVIO_DOCUMENTI = "DOCUMENTI", _("Invio documenti")
        INFORMATIVA = "INFORMATIVA", _("Comunicazione informativa")

    tipo = models.CharField(max_length=20, choices=TipoComunicazione.choices, db_index=True)
    direzione = models.CharField(
        max_length=3,
        choices=Direzione.choices,
        default=Direzione.OUT,
        db_index=True,
        help_text=_("Direzione della comunicazione ai fini del protocollo."),
    )
    oggetto = models.CharField(max_length=255)
    corpo = models.TextField(blank=True)
    corpo_html = models.TextField(blank=True, help_text=_("Versione HTML del messaggio, opzionale."))
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_invio = models.DateTimeField(null=True, blank=True, db_index=True)
    mittente = models.EmailField(blank=True, help_text=_("Email mittente (default: impostazioni sistema)"))
    destinatari = models.TextField(help_text=_("Lista destinatari separati da virgola (email/pec)"))
    contatti_destinatari = models.ManyToManyField(
        "anagrafiche.EmailContatto",
        blank=True,
        related_name="comunicazioni_destinatari",
    )
    liste_destinatari = models.ManyToManyField(
        "anagrafiche.MailingList",
        blank=True,
        related_name="comunicazioni_destinatari",
    )
    stato = models.CharField(
        max_length=20,
        choices=[
            ("bozza", "Bozza"),
            ("inviata", "Inviata"),
            ("errore", "Errore invio"),
            ("ricevuta", "Ricevuta"),
        ],
        default="bozza",
        db_index=True,
    )
    log_errore = models.TextField(blank=True)
    email_message_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_("Message-ID originale se importata da casella email."),
    )
    # Se true la comunicazione è bloccata per operazioni come la protocollazione
    bloccata = models.BooleanField(default=False)
    importato_il = models.DateTimeField(null=True, blank=True)
    import_source = models.CharField(max_length=120, blank=True)
    documento_protocollo = models.ForeignKey(
        "documenti.Documento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comunicazioni_protocollo",
        help_text=_("Documento da protocollare per questa comunicazione."),
    )
    template = models.ForeignKey(
        "comunicazioni.TemplateComunicazione",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazioni",
        help_text=_("Template utilizzato per generare il contenuto."),
    )
    dati_template = models.JSONField(default=dict, blank=True)
    firma = models.ForeignKey(
        "comunicazioni.FirmaComunicazione",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazioni",
        help_text=_("Firma applicata alla comunicazione."),
    )
    protocollo_movimento = models.OneToOneField(
        "protocollo.MovimentoProtocollo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicazione",
        help_text=_("Movimento di protocollo collegato."),
    )

    class Meta:
        verbose_name = _("Comunicazione")
        verbose_name_plural = _("Comunicazioni")
        ordering = ["-data_creazione"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.oggetto} ({self.data_creazione:%Y-%m-%d})"

    def get_absolute_url(self) -> str:
        return reverse("comunicazioni:detail", args=[self.pk])

    def get_update_url(self) -> str:
        return reverse("comunicazioni:edit", args=[self.pk])

    def get_send_url(self) -> str:
        return reverse("comunicazioni:send", args=[self.pk])

    @property
    def edit_url(self) -> str:
        return self.get_update_url()

    @property
    def invia_url(self) -> str:
        return self.get_send_url()

    @property
    def is_protocollata(self) -> bool:
        return self.protocollo_movimento_id is not None

    @property
    def can_protocolla(self) -> bool:
        return not self.is_protocollata and self.documento_protocollo_id is not None

    @property
    def protocollo_label(self) -> str:
        movimento = self.protocollo_movimento
        if movimento is None:
            return ""
        return f"{movimento.anno}/{movimento.numero:06d}"

    def get_prima_anagrafica(self):
        """
        Restituisce l'anagrafica del primo contatto destinatario.
        Utile per popolare automaticamente i campi template quando la comunicazione
        è associata a contatti di una specifica anagrafica.
        
        Returns:
            Anagrafica o None se non ci sono contatti destinatari
        """
        primo_contatto = self.contatti_destinatari.select_related('anagrafica').first()
        return primo_contatto.anagrafica if primo_contatto else None

    def get_destinatari_lista(self) -> list[str]:
        manuali = _split_emails(self.destinatari)
        contatti = [c.email for c in self.contatti_destinatari.filter(attivo=True)]
        liste = []
        for lista in self.liste_destinatari.filter(attiva=True).prefetch_related("contatti", "indirizzi_extra"):
            contatti_qs = lista.contatti.filter(attivo=True, membership__disiscritto_il__isnull=True)
            extra_qs = lista.indirizzi_extra.filter(disiscritto_il__isnull=True)
            if getattr(lista, "richiede_consenso_marketing", False):
                contatti_qs = contatti_qs.filter(marketing_consent=True)
                extra_qs = extra_qs.filter(marketing_consent=True)
            liste.extend([c.email for c in contatti_qs])
            liste.extend([extra.email for extra in extra_qs])
        dedup = []
        for email in manuali + contatti + liste:
            if email and email not in dedup:
                dedup.append(email)
        return dedup

    def sync_destinatari_testo(self) -> None:
        """
        Sincronizza il campo destinatari con i contatti e liste selezionati.
        Mantiene solo gli email manuali (non derivati da contatti/liste).
        """
        # Email attualmente nel campo destinatari
        current_emails = _split_emails(self.destinatari)
        
        # Tutti gli email derivati dai contatti e liste selezionati
        derived_emails = set()
        for contatto in self.contatti_destinatari.all():
            if contatto.email:
                derived_emails.add(contatto.email)
        
        for lista in self.liste_destinatari.all():
            for contatto in lista.contatti.all():
                if contatto.email:
                    derived_emails.add(contatto.email)
            for extra in lista.indirizzi_extra.all():
                if extra.email:
                    derived_emails.add(extra.email)
        
        # Identifica gli email veramente manuali (quelli che NON sono in contatti/liste)
        manual_emails = [email for email in current_emails if email not in derived_emails]
        
        # Combina: prima gli email manuali, poi quelli derivati (ordinati)
        all_emails = []
        for email in manual_emails:
            if email and email not in all_emails:
                all_emails.append(email)
        for email in sorted(derived_emails):
            if email and email not in all_emails:
                all_emails.append(email)
        
        self.destinatari = ", ".join(all_emails)
        self.save(update_fields=["destinatari"])

    def get_template_context(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        base: dict[str, Any] = {
            "comunicazione": self,
            "anagrafica": getattr(self, 'anagrafica', None),
            "documento_protocollo": self.documento_protocollo,
            "destinatari": self.get_destinatari_lista(),
            "oggi": timezone.now(),
        }
        if extra:
            base.update(extra)
        stored_values = self.dati_template or {}
        template = self.template
        if not template:
            for key, value in stored_values.items():
                if value is not None:
                    base[key] = value
            return base
        context_fields = template.context_fields.filter(active=True).order_by("ordering", "id")
        handled_keys: set[str] = set()
        for field in context_fields:
            if field.key in stored_values:
                stored_value = field.coerce_value(stored_values[field.key])
                # Se il campo usa widget='anagrafica', risolvi l'ID in oggetto Anagrafica
                if field.widget in ("anagrafica", "fk_anagrafica", "anag") and stored_value is not None:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Campo {field.key}: risoluzione anagrafica ID={stored_value}, widget={field.widget}")
                    anagrafica_obj = field.resolve_anagrafica_value(stored_value)
                    logger.info(f"Campo {field.key}: anagrafica_obj={anagrafica_obj}")
                    if anagrafica_obj:
                        base[field.key] = anagrafica_obj
                        handled_keys.add(field.key)
                        continue
                base[field.key] = stored_value if stored_value is not None else stored_values[field.key]
                handled_keys.add(field.key)
                continue
            source_value = field.get_source_value(self)
            if source_value is not None:
                base.setdefault(field.key, source_value)
                continue
            default_value = field.get_default_value()
            if field.key not in base and default_value is not None:
                base[field.key] = default_value
        for key, value in stored_values.items():
            if key in handled_keys or value is None:
                continue
            base[key] = value
        return base

    def _format_value(self, value: Any, format_string: str | None = None) -> str:
        """
        Formatta un valore secondo il format_string specificato.
        
        Args:
            value: Il valore da formattare
            format_string: La stringa di formato (es. '%.2f', '%d/%m/%Y', '{:,.2f}')
        
        Returns:
            Il valore formattato come stringa
        """
        if value is None:
            return ''
        
        if not format_string:
            return str(value)
        
        try:
            from datetime import date, datetime
            from decimal import Decimal
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🔧 Formattazione valore: {value!r} (tipo: {type(value).__name__}) con formato: {format_string!r}")
            print(f"🔧 DEBUG: Formattazione {type(value).__name__}: {value!r} -> formato: {format_string!r}")
            
            # Formattazione per date
            if isinstance(value, (date, datetime)):
                # Se usa formato Python strftime (es. '%d/%m/%Y')
                if '%' in format_string:
                    try:
                        result = value.strftime(format_string)
                        logger.info(f"✅ Data formattata: {result}")
                        print(f"✅ Data formattata: {result}")
                        return result
                    except ValueError as e:
                        logger.error(f"❌ Errore formato data '{format_string}': {e}. Usa formato tipo '%d/%m/%Y'")
                        print(f"❌ ERRORE: Formato data '{format_string}' non valido: {e}")
                        return str(value)
                # Altrimenti usa il formato standard
                result = value.strftime(format_string)
                logger.info(f"✅ Data formattata: {result}")
                return result
            
            # Formattazione per numeri decimali
            if isinstance(value, Decimal):
                # Se usa formato vecchio stile (es. '%.2f')
                if format_string.startswith('%'):
                    try:
                        result = format_string % float(value)
                        logger.info(f"✅ Decimal formattato (old style): {result}")
                        print(f"✅ Decimal formattato (old style): {result}")
                        return result
                    except (ValueError, TypeError) as e:
                        logger.error(f"❌ Errore formato decimal '{format_string}': {e}")
                        print(f"❌ ERRORE: Formato decimal '{format_string}' non valido: {e}")
                        return str(value)
                # Se usa formato nuovo stile (es. '{:,.2f}' o '{:,.2f}it' per formato italiano)
                # Controlla sia '}' che '}it'
                if format_string.startswith('{') and (format_string.endswith('}') or format_string.endswith('}it')):
                    # Controlla se vuole formato italiano
                    use_italian_format = format_string.endswith('it')
                    
                    if use_italian_format:
                        # Formato tipo '{:,.2f}it' -> estrai ':,.2f'
                        fmt = format_string[1:-3]  # Rimuovi { all'inizio e }it alla fine
                    else:
                        # Formato tipo '{:,.2f}' -> estrai ':,.2f'
                        fmt = format_string[1:-1]  # Rimuovi { e }
                    
                    print(f"🔧 Formato estratto: '{fmt}', italiano={use_italian_format}")
                    
                    try:
                        # Costruisci il formato completo e usa .format()
                        format_expr = "{" + fmt + "}"
                        result = format_expr.format(value)
                        print(f"🔧 Risultato format(): '{result}'")
                        
                        # Se richiesto formato italiano, scambia . e ,
                        if use_italian_format:
                            result = result.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
                            print(f"🔧 Dopo conversione IT: '{result}'")
                        
                        logger.info(f"✅ Decimal formattato (new style): {result}")
                        print(f"✅ Decimal formattato (new style): {result}")
                        return result
                    except (ValueError, TypeError) as e:
                        logger.error(f"❌ Errore formato decimal '{fmt}': {e}. Usa formato tipo '{{:,.2f}}' o '{{:,.2f}}it'")
                        print(f"❌ ERRORE: Formato decimal '{fmt}' non valido: {e}")
                        return str(value)
                
                # Fallback se non match nessuna condizione
                print(f"⚠️  FALLBACK: formato '{format_string}' non riconosciuto")
                result = str(value)
            
            # Formattazione per interi
            if isinstance(value, int):
                if format_string.startswith('%'):
                    result = format_string % value
                    logger.debug(f"Int formattato (old style): {result}")
                    return result
                if format_string.startswith('{') and format_string.endswith('}'):
                    fmt = format_string[1:-1]
                    result = format(value, fmt)
                    logger.debug(f"Int formattato (new style): {result}")
                    return result
                result = format_string.format(value)
                logger.debug(f"Int formattato: {result}")
                return result
            
            # Formattazione per stringhe
            if isinstance(value, str):
                if format_string.startswith('{') and format_string.endswith('}'):
                    fmt = format_string[1:-1]
                    result = format(value, fmt)
                    logger.debug(f"String formattata: {result}")
                    return result
                result = format_string.format(value)
                logger.debug(f"String formattata: {result}")
                return result
            
            # Default: usa format_string come template
            result = format_string.format(value)
            logger.debug(f"Valore formattato (default): {result}")
            return result
            
        except (ValueError, TypeError, KeyError) as e:
            # Se la formattazione fallisce, ritorna il valore come stringa
            logger.error(f"❌ Errore formattazione {value!r} con {format_string!r}: {e}")
            print(f"❌ ERRORE GENERALE: Formattazione fallita per {value!r} con formato {format_string!r}: {e}")
            return str(value)

    def render_content(self) -> None:
        """
        Renderizza il contenuto della comunicazione sostituendo i placeholder
        del template con i valori effettivi dal contesto.
        Gestisce anche l'inserimento della firma se presente.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        print(f"\n{'='*80}")
        print(f"🎨 RENDER_CONTENT chiamato per comunicazione ID={self.id}")
        print(f"{'='*80}")
        
        context = {}
        field_formats = {}
        if not self.template:
            logger.debug(f"render_content: Comunicazione {self.id} senza template")
            print(f"⚠️  Nessun template associato")
        else:
            logger.info(f"render_content: Inizio rendering comunicazione {self.id} con template {self.template.nome}")
            print(f"📋 Template: {self.template.nome}")
            
            context = self.get_template_context()
            logger.debug(f"Contesto: {list(context.keys())}")
            print(f"🔑 Chiavi contesto: {list(context.keys())}")
            
            # Crea una mappa key -> context_field per accedere alla formattazione
            if self.template:
                for field in self.template.context_fields.filter(active=True):
                    if field.format_string:
                        field_formats[field.key] = field.format_string
                        logger.debug(f"Formato per {field.key}: {field.format_string}")
                        print(f"📐 Formato per '{field.key}': {field.format_string}")
            
            logger.debug(f"Formati definiti: {field_formats}")
            print(f"📐 Totale formati definiti: {len(field_formats)}")
            
            # Usa il Django Template Engine per supportare espressioni come {{cliente.denominazione_anagrafica}}
            from django.template import Context, Template
            django_context = Context(context)
            
            # Renderizza oggetto, corpo e corpo_html usando Django Template Engine
            for field_name in ['oggetto', 'corpo', 'corpo_html']:
                content = getattr(self, field_name, '')
                print(f"\n📝 Campo '{field_name}':")
                print(f"   Lunghezza: {len(content)} caratteri")
                if content:
                    print(f"   Preview: {content[:200]}...")
                    # Conta quanti placeholder ci sono (pattern {{ ... }})
                    import re
                    placeholders = re.findall(r'\{\{[^}]+\}\}', content)
                    print(f"   Placeholder trovati: {len(placeholders)}")
                    if placeholders:
                        print(f"   Esempi: {placeholders[:5]}")
                else:
                    print(f"   ⚠️  Campo VUOTO!")
                
                if content:
                    try:
                        # Disabilita autoescape per evitare che ' diventi &#x27;
                        # Avvolge il contenuto con {% autoescape off %}...{% endautoescape %}
                        template_source = f'{{% autoescape off %}}{content}{{% endautoescape %}}'
                        template = Template(template_source)
                        rendered_content = template.render(django_context).strip()
                        print(f"   ✅ Rendering completato (autoescape off)")
                        print(f"   Preview risultato: {rendered_content[:200]}...")
                        setattr(self, field_name, rendered_content)
                    except Exception as e:
                        print(f"   ❌ Errore rendering: {e}")
                        logger.error(f"Errore rendering campo {field_name}: {e}")
                        # Mantieni il contenuto originale in caso di errore
        
        print(f"{'='*80}\n")
        # Aggiungi la firma al corpo se presente
        if self.firma:
            firma_html = self.firma.get_html()
            firma_text = self.firma.get_text()
            
            if firma_html:
                # Controlla se la firma è già presente nel corpo HTML
                firma_already_present = firma_html in (self.corpo_html or '')
                
                if not firma_already_present:
                    print(f"📝 Aggiunta firma HTML al corpo_html")
                    # Se abbiamo corpo testuale ma non HTML, convertiamo il corpo in HTML
                    if self.corpo and not self.corpo_html:
                        # Converti il testo in HTML: sostituisci newline con <br>
                        corpo_as_html = self.corpo.replace('\n', '<br>')
                        self.corpo_html = f'{corpo_as_html}<br><br>{firma_html}'
                    elif not self.corpo_html:
                        # Nessun corpo, solo firma
                        self.corpo_html = firma_html
                    elif '</body>' in self.corpo_html:
                        # Inserisci prima del tag di chiusura body
                        self.corpo_html = self.corpo_html.replace(
                            '</body>',
                            f'<br><br>{firma_html}</body>'
                        )
                    else:
                        # Aggiungi alla fine
                        self.corpo_html += f'\n\n<br><br>{firma_html}'
                else:
                    print(f"ℹ️  Firma HTML già presente, skip")
            
            if firma_text:
                # Controlla se la firma è già presente nel corpo testuale
                firma_already_present = firma_text in (self.corpo or '')
                
                if not firma_already_present:
                    print(f"📝 Aggiunta firma testuale al corpo")
                    # Aggiungi firma testuale (anche se corpo è vuoto)
                    if not self.corpo:
                        self.corpo = firma_text
                    else:
                        self.corpo += f'\n\n{firma_text}'
                else:
                    print(f"ℹ️  Firma testuale già presente, skip")


    # Import per registrare i modelli definiti in moduli separati.
    from .models_template import FirmaComunicazione, TemplateComunicazione  # noqa: E402,F401

class AllegatoComunicazione(models.Model):
    """
    Allegato a una comunicazione.
    Può essere:
    - Un documento esistente nel sistema
    - Un fascicolo (viene generato ZIP dei documenti)
    - Un file caricato direttamente dall'utente
    """
    comunicazione = models.ForeignKey(Comunicazione, on_delete=models.CASCADE, related_name="allegati")
    
    # Opzione 1: Documento esistente
    documento = models.ForeignKey(
        "documenti.Documento", 
        on_delete=models.CASCADE, 
        related_name="comunicazioni_allegato",
        null=True,
        blank=True,
        help_text=_("Documento esistente da allegare")
    )
    
    # Opzione 2: Fascicolo (verrà generato ZIP)
    fascicolo = models.ForeignKey(
        "fascicoli.Fascicolo",
        on_delete=models.CASCADE,
        related_name="comunicazioni_allegato",
        null=True,
        blank=True,
        help_text=_("Fascicolo da allegare come ZIP dei suoi documenti")
    )
    
    # Opzione 3: File caricato direttamente
    file = models.FileField(
        upload_to="comunicazioni/allegati/%Y/%m/",
        null=True,
        blank=True,
        help_text=_("File caricato direttamente senza creare un Documento")
    )
    nome_file = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Nome originale del file caricato")
    )
    
    # Metadati
    data_creazione = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Allegato comunicazione")
        verbose_name_plural = _("Allegati comunicazione")
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(documento__isnull=False) |
                    models.Q(fascicolo__isnull=False) |
                    models.Q(file__isnull=False)
                ),
                name="allegato_almeno_uno"
            )
        ]

    def __str__(self):
        if self.documento:
            return f"{self.comunicazione} -> Documento: {self.documento}"
        elif self.fascicolo:
            return f"{self.comunicazione} -> Fascicolo: {self.fascicolo}"
        elif self.file:
            return f"{self.comunicazione} -> File: {self.nome_file or self.file.name}"
        return f"{self.comunicazione} -> Allegato senza contenuto"
    
    def get_file_path(self):
        """Ritorna il path del file da allegare"""
        if self.documento and hasattr(self.documento, 'file') and self.documento.file:
            return self.documento.file.path
        elif self.file:
            return self.file.path
        elif self.fascicolo:
            # Genera ZIP al volo
            return self._generate_fascicolo_zip()
        return None
    
    def get_filename(self):
        """Ritorna il nome del file da usare nell'allegato email"""
        if self.documento:
            return self.documento.file.name.split('/')[-1] if self.documento.file else f"documento_{self.documento.id}.pdf"
        elif self.file:
            return self.nome_file or self.file.name.split('/')[-1]
        elif self.fascicolo:
            return f"{self.fascicolo.titolo}_{self.fascicolo.id}.zip"
        return "allegato"
    
    def _generate_fascicolo_zip(self):
        """Genera uno ZIP con tutti i documenti del fascicolo"""
        import os
        import zipfile
        from django.conf import settings
        from tempfile import NamedTemporaryFile
        
        # Crea file temporaneo
        temp_file = NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Aggiungi tutti i documenti del fascicolo
            for doc in self.fascicolo.documenti.all():
                if hasattr(doc, 'file') and doc.file:
                    try:
                        file_path = doc.file.path
                        arcname = f"{doc.file.name.split('/')[-1]}"
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        # Log errore ma continua
                        print(f"Errore aggiunta documento {doc.id} allo ZIP: {e}")
                        continue
        
        temp_file.close()
        return temp_file.name

    def clean(self):
        """Validazione: deve avere almeno un tipo di allegato"""
        from django.core.exceptions import ValidationError
        
        count = sum([
            self.documento_id is not None,
            self.fascicolo_id is not None,
            bool(self.file)
        ])
        
        if count == 0:
            raise ValidationError(_("Deve essere specificato almeno un documento, fascicolo o file"))
        elif count > 1:
            raise ValidationError(_("Può essere specificato solo un tipo di allegato"))


class Mailbox(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    host = models.CharField(max_length=255)
    porta = models.PositiveIntegerField(default=993)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    cartella = models.CharField(max_length=120, default="INBOX")
    usa_ssl = models.BooleanField(default=True)
    usa_starttls = models.BooleanField(default=False)
    attiva = models.BooleanField(default=True)
    filtra_da = models.TextField(
        blank=True,
        help_text=_("Elenco di indirizzi mittente consentiti (uno per riga). Lascia vuoto per accettare tutti."),
    )
    escludi_da = models.TextField(
        blank=True,
        help_text=_("Indirizzi mittente da escludere (uno per riga)."),
    )
    soggetto_contiene = models.TextField(
        blank=True,
        help_text=_("Importa solo se il soggetto contiene almeno una delle parole chiave (una per riga)."),
    )
    ultimi_uid = models.CharField(max_length=120, blank=True)
    ultima_lettura = models.DateTimeField(null=True, blank=True)
    timeout = models.PositiveIntegerField(default=30)
    salva_headers = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Casella IMAP")
        verbose_name_plural = _("Caselle IMAP")
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def allowed_from(self) -> set[str]:
        values = {r.strip().lower() for r in (self.filtra_da or "").splitlines() if r.strip()}
        return values

    def blocked_from(self) -> set[str]:
        values = {r.strip().lower() for r in (self.escludi_da or "").splitlines() if r.strip()}
        return values

    def subject_tokens(self) -> list[str]:
        return [r.strip().lower() for r in (self.soggetto_contiene or "").splitlines() if r.strip()]


class EmailImportBlacklist(models.Model):
    email = models.EmailField(unique=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_blacklist_entries",
    )

    class Meta:
        verbose_name = _("Email bloccata")
        verbose_name_plural = _("Email bloccate")
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)


class EmailImport(models.Model):
    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE, related_name="email_imports")
    uid = models.CharField(max_length=120, blank=True)
    message_id = models.CharField(max_length=255)
    mittente = models.CharField(max_length=255, blank=True)
    destinatari = models.TextField(blank=True)
    oggetto = models.CharField(max_length=500, blank=True)
    data_messaggio = models.DateTimeField(null=True, blank=True)
    raw_headers = models.TextField(blank=True)
    corpo_testo = models.TextField(blank=True)
    corpo_html = models.TextField(blank=True)
    # raw_message conserva il byte-stream originale RFC822 (utile per ricreare allegati/eml)
    raw_message = models.BinaryField(null=True, blank=True, editable=False)
    comunicazione = models.OneToOneField(
        Comunicazione,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_import",
    )
    importato_il = models.DateTimeField(auto_now_add=True)
    errore = models.TextField(blank=True)
    # stato_import: 'nuovo' quando importata, 'processato' dopo la creazione manuale della comunicazione
    stato_import = models.CharField(max_length=30, default="nuovo")
    processato_il = models.DateTimeField(null=True, blank=True)
    processato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_import_processati",
    )

    class Meta:
        verbose_name = _("Email importata")
        verbose_name_plural = _("Email importate")
        ordering = ["-importato_il"]
        constraints = [
            models.UniqueConstraint(fields=["mailbox", "message_id"], name="uniq_mailbox_message_id"),
        ]

    def __str__(self) -> str:
        return f"{self.mailbox}: {self.oggetto or self.message_id}"

    @property
    def data_messaggio_or_import(self):
        return self.data_messaggio or self.importato_il
