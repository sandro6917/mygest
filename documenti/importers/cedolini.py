"""
Importatore per cedolini paga.
Estende BaseImporter riutilizzando il parser esistente in documenti/parsers/cedolino_parser.py
"""

import os
import zipfile
import tempfile
import logging
from typing import Dict, List, Any, TYPE_CHECKING
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from .base import BaseImporter, ParseResult, ImporterRegistry
from ..parsers.cedolino_parser import parse_cedolino_pdf
from ..models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from anagrafiche.models import Anagrafica, Cliente
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


class DocumentoDuplicatoError(Exception):
    """Eccezione sollevata quando viene rilevato un documento duplicato"""
    def __init__(self, message: str, documento_esistente=None, dettagli: Dict = None):
        super().__init__(message)
        self.documento_esistente = documento_esistente
        self.dettagli = dettagli or {}


@ImporterRegistry.register
class CedoliniImporter(BaseImporter):
    """
    Importatore per cedolini paga.
    
    Supporta:
    - File PDF singolo
    - File ZIP con multipli PDF
    - Estrazione campi: datore, lavoratore, periodo, netto, etc.
    - Match automatico anagrafiche da CF
    - Creazione fascicolo automatica "Paghe {mese} {anno}"
    """
    
    tipo = 'cedolini'
    display_name = 'Cedolini Paga'
    supported_extensions = ['.pdf', '.zip']
    max_file_size_mb = 500
    batch_mode = True
    
    def extract_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Estrae PDF da ZIP o ritorna singolo PDF.
        
        Per ZIP: estrae tutti i .pdf in una directory temporanea
        Per PDF: ritorna il file stesso
        """
        documents = []
        
        if file_path.lower().endswith('.zip'):
            # Estrai ZIP in temp_dir
            temp_dir = tempfile.mkdtemp(prefix='cedolini_import_')
            self.session.temp_dir = temp_dir
            self.session.save()
            
            logger.info(f"Estrazione ZIP in {temp_dir}")
            
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Validazione ZIP
                    if zip_ref.testzip():
                        raise ValueError("File ZIP corrotto")
                    
                    # Estrai solo PDF
                    pdf_count = 0
                    for idx, file_info in enumerate(zip_ref.filelist):
                        if file_info.filename.lower().endswith('.pdf') and not file_info.is_dir():
                            try:
                                extracted_path = zip_ref.extract(file_info, temp_dir)
                                file_size = os.path.getsize(extracted_path)
                                
                                documents.append({
                                    'filename': os.path.basename(file_info.filename),
                                    'file_path': extracted_path,
                                    'file_size': file_size,
                                    'ordine': pdf_count,
                                })
                                pdf_count += 1
                                
                            except Exception as e:
                                logger.warning(f"Errore estrazione {file_info.filename}: {e}")
                                continue
                    
                    if pdf_count == 0:
                        raise ValueError("Nessun file PDF trovato nello ZIP")
                    
                    logger.info(f"Estratti {pdf_count} PDF da ZIP")
                    
            except zipfile.BadZipFile:
                raise ValueError("File ZIP non valido o corrotto")
        
        else:
            # Singolo PDF
            documents.append({
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'ordine': 0,
            })
            logger.info(f"Singolo PDF: {os.path.basename(file_path)}")
        
        return documents
    
    def parse_document(self, file_path: str, filename: str) -> ParseResult:
        """
        Parserizza cedolino PDF usando il parser esistente.
        """
        try:
            logger.info(f"Parsing cedolino: {filename}")
            
            # Usa parser esistente
            parsed = parse_cedolino_pdf(file_path)
            
            # Match anagrafiche
            anagrafiche = []
            
            # Anagrafica datore
            if parsed['datore']['codice_fiscale']:
                match_datore = self.match_anagrafica(parsed['datore']['codice_fiscale'])
                if match_datore:
                    match_datore['ruolo'] = 'datore'
                    match_datore['dati'] = {
                        'ragione_sociale': parsed['datore']['ragione_sociale'],
                        'indirizzo': parsed['datore']['indirizzo'],
                    }
                    anagrafiche.append(match_datore)
                else:
                    # Datore non trovato - crea entry per creazione futura
                    anagrafiche.append({
                        'id': None,
                        'codice_fiscale': parsed['datore']['codice_fiscale'],
                        'nome': parsed['datore']['ragione_sociale'],
                        'match_type': 'not_found',
                        'ruolo': 'datore',
                        'cliente_id': None,
                        'dati': {
                            'ragione_sociale': parsed['datore']['ragione_sociale'],
                            'indirizzo': parsed['datore']['indirizzo'],
                        }
                    })
            
            # Anagrafica dipendente
            if parsed['lavoratore']['codice_fiscale']:
                match_dipendente = self.match_anagrafica(parsed['lavoratore']['codice_fiscale'])
                if match_dipendente:
                    match_dipendente['ruolo'] = 'dipendente'
                    match_dipendente['dati'] = {
                        'cognome': parsed['lavoratore']['cognome'],
                        'nome': parsed['lavoratore']['nome'],
                        'data_nascita': parsed['lavoratore']['data_nascita'],
                    }
                    anagrafiche.append(match_dipendente)
                else:
                    # Dipendente non trovato
                    anagrafiche.append({
                        'id': None,
                        'codice_fiscale': parsed['lavoratore']['codice_fiscale'],
                        'nome': f"{parsed['lavoratore']['cognome']} {parsed['lavoratore']['nome']}",
                        'match_type': 'not_found',
                        'ruolo': 'dipendente',
                        'cliente_id': None,
                        'dati': {
                            'cognome': parsed['lavoratore']['cognome'],
                            'nome': parsed['lavoratore']['nome'],
                            'data_nascita': parsed['lavoratore']['data_nascita'],
                        }
                    })
            
            # Valori editabili (per correzioni OCR future)
            valori_editabili = {
                'periodo': parsed['cedolino']['periodo'],
                'anno': parsed['cedolino']['anno'],
                'mese': parsed['cedolino']['mese'],
                'mensilita': parsed['cedolino']['mensilita'],
                'netto': str(parsed['cedolino']['netto']) if parsed['cedolino']['netto'] else None,
                # ✅ AGGIUNTO: Campi per rilevamento duplicati
                'numero_cedolino': parsed['cedolino'].get('numero_cedolino'),
                'data_ora_cedolino': parsed['cedolino'].get('data_ora_cedolino'),
            }
            
            # Mappatura DB (cosa finirà nei campi del documento)
            mappatura_db = {
                'tipo': 'BPAG',
                'attributi': [
                    {
                        'codice': 'anno_riferimento',
                        'nome': 'Anno riferimento',
                        'valore': str(parsed['cedolino']['anno'])
                    },
                    {
                        'codice': 'mese_riferimento',
                        'nome': 'Mese riferimento',
                        'valore': str(parsed['cedolino']['mese'])
                    },
                    {
                        'codice': 'mensilita',
                        'nome': 'Mensilità',
                        'valore': parsed['cedolino']['mensilita']
                    },
                    {
                        'codice': 'dipendente',
                        'nome': 'Dipendente',
                        'valore': f"{parsed['lavoratore']['cognome']} {parsed['lavoratore']['nome']}"
                    },
                    # ✅ AGGIUNTO: Attributi per rilevamento duplicati
                    {
                        'codice': 'numero_cedolino',
                        'nome': 'Numero cedolino',
                        'valore': parsed['cedolino'].get('numero_cedolino')
                    },
                    {
                        'codice': 'data_ora_cedolino',
                        'nome': 'Data/Ora cedolino',
                        'valore': parsed['cedolino'].get('data_ora_cedolino')
                    },
                ],
                'note_preview': self._build_note_preview(parsed),
            }
            
            logger.info(f"Parsing OK: {filename}")
            
            return ParseResult(
                success=True,
                parsed_data=parsed,
                anagrafiche_reperite=anagrafiche,
                valori_editabili=valori_editabili,
                mappatura_db=mappatura_db,
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Errore parsing {filename}: {e}")
            
            return ParseResult(
                success=False,
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={},
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )
    
    def _build_note_preview(self, parsed: Dict) -> str:
        """Costruisce preview campo note del documento"""
        lines = [
            "=== DATORE DI LAVORO ===",
            f"Ragione Sociale: {parsed['datore']['ragione_sociale']}",
            f"Codice Fiscale: {parsed['datore']['codice_fiscale']}",
            f"Indirizzo: {parsed['datore']['indirizzo']}",
            "",
            "=== LAVORATORE ===",
            f"Cognome e Nome: {parsed['lavoratore']['cognome']} {parsed['lavoratore']['nome']}",
            f"Codice Fiscale: {parsed['lavoratore']['codice_fiscale']}",
            f"Matricola: {parsed['lavoratore']['matricola']}",
            f"Matricola INPS: {parsed['lavoratore']['matricola_inps']}",
            f"Data Nascita: {parsed['lavoratore']['data_nascita']}",
            f"Data Assunzione: {parsed['lavoratore']['data_assunzione']}",
        ]
        
        if parsed['lavoratore'].get('data_cessazione'):
            lines.append(f"Data Cessazione: {parsed['lavoratore']['data_cessazione']}")
        
        lines.append("")
        lines.append("=== CEDOLINO ===")
        lines.append(f"Periodo: {parsed['cedolino']['periodo']}")
        
        if parsed['cedolino'].get('livello'):
            lines.append(f"Livello: {parsed['cedolino']['livello']}")
        
        if parsed['cedolino'].get('netto'):
            lines.append(f"Netto: {parsed['cedolino']['netto']}")
        
        if parsed['cedolino'].get('numero_cedolino'):
            lines.append(f"Numero: {parsed['cedolino']['numero_cedolino']}")
        
        if parsed['cedolino'].get('data_ora_cedolino'):
            lines.append(f"Data/Ora: {parsed['cedolino']['data_ora_cedolino']}")
        
        return "\n".join(lines)
    
    def check_duplicate(
        self,
        parsed_data: Dict[str, Any],
        valori_editabili: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica se il cedolino è un duplicato senza crearlo.
        
        Returns:
            {
              "is_duplicate": bool,
              "duplicate_info": {
                "id": int,
                "codice": str,
                "numero_cedolino": str,
                "data_ora_cedolino": str,
                "confidence": float,
                "matched_fields": list
              } | None
            }
        """
        from documenti.services.duplicate_detection import DuplicateDetectionService
        
        # Tipo documento BPAG
        tipo_bpag = DocumentiTipo.objects.filter(codice='BPAG').first()
        if not tipo_bpag:
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # Cliente: cerca da anagrafica datore
        cliente = None
        cf_datore = parsed_data['datore']['codice_fiscale']
        if cf_datore:
            try:
                anagrafica_datore = Anagrafica.objects.get(codice_fiscale__iexact=cf_datore)
                if hasattr(anagrafica_datore, 'cliente'):
                    cliente = anagrafica_datore.cliente
            except (Anagrafica.DoesNotExist, Anagrafica.MultipleObjectsReturned):
                pass
        
        if not cliente:
            # Non possiamo verificare duplicati senza cliente
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # Prepara attributi per verifica (usa valori editabili se presenti)
        valori = valori_editabili or {}
        attributi_per_verifica = {
            'numero_cedolino': valori.get('numero_cedolino') or parsed_data['cedolino'].get('numero_cedolino'),
            'data_ora_cedolino': valori.get('data_ora_cedolino') or parsed_data['cedolino'].get('data_ora_cedolino'),
        }
        
        # Usa service generico
        service = DuplicateDetectionService(tipo_bpag)
        
        if not service.is_enabled():
            return {'is_duplicate': False, 'duplicate_info': None}
        
        result = service.find_duplicate(
            cliente=cliente,
            attributi=attributi_per_verifica,
            documento_fields={'data_documento': timezone.now().date()}
        )
        
        if result.is_duplicate:
            return {
                'is_duplicate': True,
                'duplicate_info': {
                    'id': result.documento.id,
                    'codice': result.documento.codice,
                    'numero_cedolino': attributi_per_verifica.get('numero_cedolino'),
                    'data_ora_cedolino': attributi_per_verifica.get('data_ora_cedolino'),
                    'confidence': result.confidence,
                    'matched_fields': result.matched_fields,
                }
            }
        else:
            return {'is_duplicate': False, 'duplicate_info': None}
    
    @transaction.atomic
    def create_documento(
        self,
        parsed_data: Dict[str, Any],
        valori_editati: Dict[str, Any],
        user: 'User',
        **kwargs
    ) -> Documento:
        """
        Crea documento cedolino nel DB.
        
        Kwargs opzionali:
            fascicolo_id: ID fascicolo target (opzionale, assegnabile dopo)
            cliente_id: ID cliente (richiesto)
            file_path: str - Path del file PDF originale da allegare
        """
        logger.info(f"Creazione documento cedolino per {parsed_data['lavoratore']['cognome']}")
        
        # Merge valori editati con parsed_data
        periodo = valori_editati.get('periodo', parsed_data['cedolino']['periodo'])
        anno = valori_editati.get('anno', parsed_data['cedolino']['anno'])
        mese = valori_editati.get('mese', parsed_data['cedolino']['mese'])
        mensilita = valori_editati.get('mensilita', parsed_data['cedolino']['mensilita'])
        netto_str = valori_editati.get('netto', str(parsed_data['cedolino']['netto']) if parsed_data['cedolino']['netto'] else None)
        
        # Tipo documento BPAG
        tipo_bpag, _ = DocumentiTipo.objects.get_or_create(
            codice='BPAG',
            defaults={'descrizione': 'Busta Paga'}
        )
        
        # Cliente: usa kwargs o cerca da anagrafica datore
        cliente = None
        if 'cliente_id' in kwargs and kwargs['cliente_id']:
            cliente = Cliente.objects.get(id=kwargs['cliente_id'])
        else:
            # Cerca cliente da anagrafica datore
            cf_datore = parsed_data['datore']['codice_fiscale']
            if cf_datore:
                try:
                    anagrafica_datore = Anagrafica.objects.get(codice_fiscale__iexact=cf_datore)
                    if hasattr(anagrafica_datore, 'cliente'):
                        cliente = anagrafica_datore.cliente
                except (Anagrafica.DoesNotExist, Anagrafica.MultipleObjectsReturned):
                    pass
        
        # Se ancora non abbiamo cliente, errore
        if not cliente:
            raise ValueError(
                f"Cliente non trovato per datore {parsed_data['datore']['ragione_sociale']} "
                f"(CF: {parsed_data['datore']['codice_fiscale']}). "
                "Specificare cliente_id o creare anagrafica/cliente prima dell'importazione."
            )
        
        # **NUOVO: Crea automaticamente anagrafica dipendente se non esiste**
        anagrafica_dipendente = self._create_or_get_dipendente_anagrafica(parsed_data['lavoratore'])
        
        # Titolario: Gerarchia HR-PERS/{CODICE_DIPENDENTE}/PAG
        # Esempio: HR-PERS/ROSMAR01/PAG
        titolario = self._get_or_create_titolario_dipendente(anagrafica_dipendente)
        
        # Fascicolo opzionale (può essere assegnato dopo nella pagina di modifica)
        fascicolo = None
        if 'fascicolo_id' in kwargs and kwargs['fascicolo_id']:
            fascicolo = Fascicolo.objects.get(id=kwargs['fascicolo_id'])
        
        # ✅ VERIFICA DUPLICAZIONE usando service generico
        duplicate_policy = kwargs.get('duplicate_policy', 'skip')
        
        if duplicate_policy != 'add':
            from documenti.services.duplicate_detection import DuplicateDetectionService
            
            # Prepara attributi per verifica duplicazione
            attributi_per_verifica = {
                'numero_cedolino': parsed_data['cedolino'].get('numero_cedolino'),
                'data_ora_cedolino': parsed_data['cedolino'].get('data_ora_cedolino'),
            }
            
            # Usa service generico
            service = DuplicateDetectionService(tipo_bpag)
            
            if service.is_enabled():
                result = service.find_duplicate(
                    cliente=cliente,
                    attributi=attributi_per_verifica,
                    documento_fields={'data_documento': timezone.now().date()}
                )
                
                if result.is_duplicate:
                    if duplicate_policy == 'skip':
                        numero = attributi_per_verifica.get('numero_cedolino') or 'N/A'
                        data_ora = attributi_per_verifica.get('data_ora_cedolino') or 'N/A'
                        logger.warning(
                            f"Cedolino duplicato rilevato: Doc {result.documento.codice} "
                            f"(Nr. {numero}, Data/Ora {data_ora}, "
                            f"confidence {result.confidence:.0%}, "
                            f"matched_fields: {', '.join(result.matched_fields)}). "
                            f"Importazione saltata."
                        )
                        raise DocumentoDuplicatoError(
                            f"Cedolino già presente nel sistema",
                            documento_esistente=result.documento,
                            dettagli={
                                'codice': result.documento.codice,
                                'numero_cedolino': numero,
                                'data_ora_cedolino': data_ora,
                                'confidence': result.confidence,
                                'matched_fields': result.matched_fields,
                            }
                        )
                    
                    elif duplicate_policy == 'replace':
                        logger.info(
                            f"Sostituzione documento duplicato {result.documento.id} "
                            f"({result.documento.codice})"
                        )
                        result.documento.delete()
        
        # Crea documento
        documento = Documento.objects.create(
            tipo=tipo_bpag,
            cliente=cliente,
            fascicolo=fascicolo,  # Opzionale, None se non specificato
            titolario_voce=titolario,
            descrizione=f"Cedolino {parsed_data['lavoratore']['cognome']} {parsed_data['lavoratore']['nome']} - {periodo}",
            data_documento=timezone.now().date(),
            note=self._build_note_preview(parsed_data),
            stato=Documento.Stato.DEFINITIVO,  # Cedolini sono sempre definitivi
            digitale=True,  # Cedolini sono sempre digitali
            tracciabile=True,  # Cedolini sono sempre tracciabili
        )
        
        # Allega file PDF se fornito
        file_path = kwargs.get('file_path')
        if file_path and os.path.exists(file_path):
            from django.core.files import File as DjangoFile
            filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                django_file = DjangoFile(f, name=filename)
                documento.file.save(filename, django_file, save=True)
            
            logger.info(f"File PDF allegato: {filename}")
        
        logger.info(f"Creato documento {documento.id}: {documento.descrizione} (fascicolo: {fascicolo or 'da assegnare'})")
        
        # Crea attributi dinamici
        self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)
        
        return documento
    
    def _create_attributi(
        self,
        documento: Documento,
        tipo_bpag: DocumentiTipo,
        anno: int,
        mese: int,
        mensilita: str,
        parsed_data: Dict
    ):
        """Crea AttributoValore per il documento"""
        
        # Estrai numero e data/ora dal parsed_data
        numero_cedolino = parsed_data['cedolino'].get('numero_cedolino')
        data_ora_cedolino = parsed_data['cedolino'].get('data_ora_cedolino')
        
        # Definizioni attributi
        attributi_config = [
            ('anno_riferimento', 'Anno riferimento', 'int', anno),
            ('mese_riferimento', 'Mese riferimento', 'int', mese),
            ('mensilita', 'Mensilità', 'string', mensilita),  # ✅ CORRETTO: 'string' invece di 'str'
            (
                'dipendente',
                'Dipendente',
                'string',  # ✅ CORRETTO: 'string' invece di 'str'
                f"{parsed_data['lavoratore']['cognome']} {parsed_data['lavoratore']['nome']}"
            ),
            # ✅ NUOVI ATTRIBUTI per rilevamento duplicati
            ('numero_cedolino', 'Numero cedolino', 'string', numero_cedolino),  # ✅ CORRETTO: 'string' invece di 'str'
            ('data_ora_cedolino', 'Data/Ora cedolino', 'string', data_ora_cedolino),  # ✅ CORRETTO: 'string' invece di 'str'
        ]
        
        for codice, nome, tipo_campo, valore in attributi_config:
            # Salta se valore è None (attributi opzionali)
            if valore is None:
                continue
            
            # Get or create definizione
            definizione, _ = AttributoDefinizione.objects.get_or_create(
                tipo_documento=tipo_bpag,
                codice=codice,
                defaults={
                    'nome': nome,
                    'tipo_dato': tipo_campo,  # ✅ CORRETTO: era 'tipo'
                    'required': False,  # ✅ CORRETTO: era 'obbligatorio'
                }
            )
            
            # Create valore
            AttributoValore.objects.create(
                documento=documento,
                definizione=definizione,
                valore=str(valore)
            )
        
        logger.debug(f"Creati attributi per documento {documento.id}")
    
    def _create_or_get_dipendente_anagrafica(self, lavoratore_data: Dict) -> Anagrafica:
        """
        Crea o recupera anagrafica dipendente.
        
        Se l'anagrafica esiste già (match per CF), la restituisce.
        Altrimenti crea una nuova anagrafica Persona Fisica.
        
        Args:
            lavoratore_data: Dict con dati lavoratore (cf, cognome, nome, data_nascita)
            
        Returns:
            Anagrafica creata o esistente
        """
        cf = lavoratore_data['codice_fiscale']
        
        # Verifica se esiste già
        try:
            anagrafica = Anagrafica.objects.get(codice_fiscale__iexact=cf)
            logger.info(f"Anagrafica dipendente già esistente: {anagrafica.display_name} (ID: {anagrafica.id})")
            return anagrafica
        except Anagrafica.DoesNotExist:
            pass
        except Anagrafica.MultipleObjectsReturned:
            # Se ci sono duplicati, usa il primo
            anagrafica = Anagrafica.objects.filter(codice_fiscale__iexact=cf).first()
            logger.warning(f"Trovate anagrafiche duplicate per CF {cf}, uso ID {anagrafica.id}")
            return anagrafica
        
        # Crea nuova anagrafica Persona Fisica
        cognome = lavoratore_data.get('cognome', '').strip().upper()
        nome = lavoratore_data.get('nome', '').strip().upper()
        data_nascita = lavoratore_data.get('data_nascita')  # Formato DD-MM-YYYY
        
        # Converti data nascita se presente
        data_nascita_obj = None
        if data_nascita:
            try:
                from datetime import datetime
                # Parse formato DD-MM-YYYY
                data_nascita_obj = datetime.strptime(data_nascita, '%d-%m-%Y').date()
            except (ValueError, TypeError):
                logger.warning(f"Formato data nascita non valido: {data_nascita}")
        
        anagrafica = Anagrafica.objects.create(
            tipo='PF',  # Persona Fisica
            codice_fiscale=cf.upper(),
            cognome=cognome,
            nome=nome,
            ragione_sociale='',  # Vuoto per PF
            # Opzionali
            # Non impostiamo is_cliente=True: i dipendenti non sono clienti
        )
        
        logger.info(
            f"Creata nuova anagrafica dipendente: {anagrafica.display_name} "
            f"(CF: {cf}, ID: {anagrafica.id})"
        )
        
        return anagrafica
    
    def _get_or_create_titolario_dipendente(self, anagrafica_dipendente: Anagrafica) -> TitolarioVoce:
        """
        Ottiene o crea la voce titolario PAG per il dipendente.
        
        Struttura: HR-PERS/{CODICE_ANAGRAFICA}/PAG
        Esempio: HR-PERS/ROSMAR01/PAG
        
        Args:
            anagrafica_dipendente: Anagrafica del dipendente
            
        Returns:
            TitolarioVoce PAG per il dipendente
        """
        from anagrafiche.utils import get_or_generate_cli
        
        # 1. Verifica/crea voce radice HR-PERS
        try:
            voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
        except TitolarioVoce.DoesNotExist:
            logger.error("Voce titolario HR-PERS non trovata! Crearla manualmente.")
            # Fallback: usa voce di default
            from documenti.models import get_or_create_default_titolario
            return get_or_create_default_titolario()
        
        # 2. Ottieni codice anagrafica dipendente (es. ROSMAR01)
        codice_dipendente = get_or_generate_cli(anagrafica_dipendente)
        
        # 3. Verifica/crea sottovoce per il dipendente (HR-PERS/ROSMAR01)
        voce_dipendente, created = TitolarioVoce.objects.get_or_create(
            codice=codice_dipendente,
            parent=voce_hr_pers,
            defaults={
                'titolo': f"{anagrafica_dipendente.cognome} {anagrafica_dipendente.nome}",
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
        
        if created:
            logger.info(f"Creata voce titolario dipendente: {voce_dipendente.codice} - {voce_dipendente.titolo}")
        
        # 4. Verifica/crea sottovoce PAG (HR-PERS/ROSMAR01/PAG)
        voce_pag, created = TitolarioVoce.objects.get_or_create(
            codice='PAG',
            parent=voce_dipendente,
            defaults={
                'titolo': 'Paghe',
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
        
        if created:
            logger.info(
                f"Creata voce titolario PAG per {codice_dipendente}: "
                f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_pag.codice}"
            )
        
        logger.debug(
            f"Titolario cedolino: {voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_pag.codice}"
        )
        
        return voce_pag
