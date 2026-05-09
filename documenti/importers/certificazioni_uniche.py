"""
Importatore per Certificazioni Uniche (CU).
Estrae dati usando template AI con zone coordinate invece di regex.
"""

import os
import zipfile
import tempfile
import logging
import traceback
import re
from typing import Dict, List, Any, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files import File as DjangoFile

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from .base import BaseImporter, ParseResult, ImporterRegistry
from ..models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from anagrafiche.models import Anagrafica, Cliente
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from ai_classifier.models import DocumentExtractionTemplate

logger = logging.getLogger(__name__)


@ImporterRegistry.register
class CertificazioniUnicheImporter(BaseImporter):
    """
    Importatore per Certificazioni Uniche (CU).
    
    Supporta:
    - File ZIP con multipli PDF CU
    - Estrazione campi: sostituto, percipiente, dati fiscali
    - Match automatico anagrafiche dipendenti da CF
    - Rilevamento duplicati per dipendente+anno
    - Classificazione sotto titolario HR-CU
    """
    
    tipo = 'certificazioni_uniche'
    display_name = 'Certificazioni Uniche'
    supported_extensions = ['.zip']
    max_file_size_mb = 200
    batch_mode = True
    
    def extract_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Estrae PDF CU da ZIP.
        
        Args:
            file_path: Path al file ZIP caricato
            
        Returns:
            Lista di dict con info sui file estratti
        """
        documents = []
        
        if not file_path.lower().endswith('.zip'):
            raise ValueError("Le Certificazioni Uniche richiedono un file ZIP")
        
        # Estrai ZIP in temp_dir
        temp_dir = tempfile.mkdtemp(prefix='cu_import_')
        self.session.temp_dir = temp_dir
        self.session.save()
        
        logger.info(f"Estrazione ZIP CU in {temp_dir}")
        
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
                
                logger.info(f"Estratti {pdf_count} PDF CU da ZIP")
                
        except zipfile.BadZipFile:
            raise ValueError("File ZIP non valido o corrotto")
        
        return documents
    
    def parse_document(self, file_path: str, filename: str) -> ParseResult:
        """
        Parsa singolo PDF CU usando template AI con zone coordinate.
        
        Args:
            file_path: Path al PDF estratto
            filename: Nome file originale
            
        Returns:
            ParseResult con dati estratti tramite template AI
        """
        print(f"\n{'='*80}")
        print(f"🔍 PARSING CU: {filename}")
        print(f"{'='*80}")
        logger.info(f"Parsing CU con template AI: {filename}")
        
        try:
            # 1. Carica template AI
            template = DocumentExtractionTemplate.objects.get(
                tipo_documento__codice='CU',
                attivo=True
            )
            print(f"✅ Template AI caricato: {template.nome}")
            logger.debug(f"Template AI caricato: {template.nome}")
            
            # 2. Estrai dati con servizio AI
            from api.v1.ai_classifier.views_ai_import import ExtractionService
            service = ExtractionService()
            
            extraction_result = service.extract_from_template(
                file_path=file_path,
                template=template
            )
            
            print(f"📊 Estrazione completata: {extraction_result['estrazione_completa']}")
            
            # 3. Converti campi estratti in dizionario
            dati = {}
            campi_non_validati = []
            
            for campo in extraction_result['campi_estratti']:
                dati[campo['nome_campo']] = campo['valore']
                
                print(f"  • {campo['nome_campo']:30} = '{campo.get('valore', '')[:60]}'  [{campo.get('confidence', 0.0):.1f}]")
                
                # Debug: log validazione campo
                if not campo['validazione_ok']:
                    campi_non_validati.append(
                        f"{campo['nome_campo']}='{campo.get('valore', '')[:50]}'"
                    )
                    logger.debug(
                        f"Campo non validato: {campo['nome_campo']} = "
                        f"'{campo.get('valore', '')}' - Errore: {campo.get('errore_validazione')}"
                    )
            
            logger.info(
                f"Estrazione completata: {len(dati)} campi estratti, "
                f"{len(campi_non_validati)} non validati"
            )
            
            print(f"\n🔑 Campi critici:")
            print(f"  CF Datore:     '{dati.get('codice_fiscale_datore', 'MANCANTE')}'")
            print(f"  CF Lavoratore: '{dati.get('codice_fiscale_lavoratore', 'MANCANTE')}'")
            
            # Verifica campi critici (CF datore e lavoratore)
            if not dati.get('codice_fiscale_datore'):
                print(f"❌ ERRORE: Codice fiscale datore non trovato")
                return ParseResult(
                    success=False,
                    error_message="Codice fiscale datore di lavoro non trovato nel documento",
                    error_traceback="",
                    parsed_data=dati,
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            if not dati.get('codice_fiscale_lavoratore'):
                return ParseResult(
                    success=False,
                    error_message="Codice fiscale lavoratore non trovato nel documento",
                    error_traceback="",
                    parsed_data=dati,
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            logger.debug(f"Dati estratti: {list(dati.keys())}")
            
            # 4. Gestisci DATORE DI LAVORO (Cliente)
            # Il cliente viene creato/trovato automaticamente in create_documento
            # qui prepariamo solo i dati
            cf_datore = dati.get('codice_fiscale_datore', '').strip().upper()
            # Rimuovi spazi interni
            cf_datore = re.sub(r'\s+', '', cf_datore)
            
            print(f"🔧 CF Datore pulito: '{cf_datore}' (len={len(cf_datore)})")
            
            if not cf_datore:
                print(f"❌ ERRORE: CF datore vuoto dopo pulizia")
                return ParseResult(
                    success=False,
                    error_message="Codice fiscale datore di lavoro mancante",
                    error_traceback="",
                    parsed_data={},
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            # Validazione formato CF/P.IVA datore
            if len(cf_datore) not in [11, 16]:
                print(f"❌ ERRORE: CF datore lunghezza invalida: {len(cf_datore)} (deve essere 11 o 16)")
                return ParseResult(
                    success=False,
                    error_message=f"Codice fiscale datore formato invalido (lunghezza {len(cf_datore)})",
                    error_traceback="",
                    parsed_data=dati,
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            # 5. Gestisci LAVORATORE
            cf_lavoratore = dati.get('codice_fiscale_lavoratore', '').strip().upper()
            # Rimuovi spazi interni
            cf_lavoratore = re.sub(r'\s+', '', cf_lavoratore)
            
            print(f"🔧 CF Lavoratore pulito: '{cf_lavoratore}' (len={len(cf_lavoratore)})")
            
            if not cf_lavoratore:
                print(f"❌ ERRORE: CF lavoratore vuoto dopo pulizia")
                return ParseResult(
                    success=False,
                    error_message="Codice fiscale lavoratore mancante",
                    error_traceback="",
                    parsed_data={},
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            # Validazione formato CF lavoratore (deve essere 16 caratteri per PF)
            if len(cf_lavoratore) != 16:
                print(f"❌ ERRORE: CF lavoratore lunghezza invalida: {len(cf_lavoratore)} (deve essere 16)")
                return ParseResult(
                    success=False,
                    error_message=f"Codice fiscale lavoratore formato invalido (lunghezza {len(cf_lavoratore)}): {cf_lavoratore}",
                    error_traceback="",
                    parsed_data=dati,
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={},
                )
            
            # Aggiorna dati con CF puliti
            dati['codice_fiscale_datore'] = cf_datore
            dati['codice_fiscale_lavoratore'] = cf_lavoratore
            
            # 6. CERCA CLIENTE DATORE (già in fase di parsing)
            denominazione_datore = dati.get('denominazione_datore', '').strip()
            nome_datore = dati.get('nome_datore', '').strip()
            
            cliente_datore = Cliente.objects.filter(
                anagrafica__codice_fiscale__iexact=cf_datore
            ).select_related('anagrafica').first()
            
            if cliente_datore:
                # Cliente trovato
                anagrafica_datore = cliente_datore.anagrafica
                nome_completo_datore = (
                    anagrafica_datore.ragione_sociale or 
                    f"{anagrafica_datore.cognome} {anagrafica_datore.nome}".strip() or
                    denominazione_datore or nome_datore
                )
                datore_info = {
                    'id': cliente_datore.id,
                    'codice_fiscale': anagrafica_datore.codice_fiscale,
                    'nome': nome_completo_datore,
                    'match_type': 'exact',
                    'ruolo': 'cliente',
                    'cliente_id': cliente_datore.id,
                    'dati': {
                        'codice_cliente': cliente_datore.anagrafica.codice,
                        'tipo': anagrafica_datore.tipo,
                    }
                }
                print(f"✅ Cliente datore trovato: {cliente_datore.anagrafica.codice} - {nome_completo_datore}")
            else:
                # Cliente NON trovato - verrà creato in create_documento()
                nome_completo_datore = denominazione_datore or nome_datore or f"CF {cf_datore}"
                datore_info = {
                    'id': None,
                    'codice_fiscale': cf_datore,
                    'nome': nome_completo_datore,
                    'match_type': 'not_found',
                    'ruolo': 'cliente',
                    'cliente_id': None,
                    'dati': {
                        'denominazione': denominazione_datore,
                        'nome': nome_datore,
                    }
                }
                print(f"⚠️  Cliente datore NON trovato: {nome_completo_datore} (CF: {cf_datore}) - verrà creato")
            
            # 7. CERCA ANAGRAFICA LAVORATORE
            cognome_lavoratore = dati.get('cognome_lavoratore', '').strip()
            nome_lavoratore = dati.get('nome_lavoratore', '').strip()
            
            anagrafica_lavoratore = Anagrafica.objects.filter(
                codice_fiscale__iexact=cf_lavoratore
            ).first()
            
            if anagrafica_lavoratore:
                lavoratore_info = {
                    'id': anagrafica_lavoratore.id,
                    'codice_fiscale': anagrafica_lavoratore.codice_fiscale,
                    'nome': f"{anagrafica_lavoratore.cognome} {anagrafica_lavoratore.nome}",
                    'match_type': 'exact',
                    'ruolo': 'dipendente',
                }
            else:
                lavoratore_info = {
                    'id': None,
                    'codice_fiscale': cf_lavoratore,
                    'nome': f"{cognome_lavoratore} {nome_lavoratore}".strip(),
                    'match_type': 'not_found',
                    'ruolo': 'dipendente',
                }
            
            # 8. Prepara lista anagrafiche reperite (DATORE + LAVORATORE)
            anagrafiche_reperite = [
                datore_info,      # Prima il datore (cliente)
                lavoratore_info,  # Poi il lavoratore (dipendente)
            ]
            
            # 9. Prepara dati parsed
            anno_imposta = dati.get('anno_imposta')
            if anno_imposta:
                try:
                    anno_imposta = int(anno_imposta)
                except (ValueError, TypeError):
                    anno_imposta = None
            
            # Deriva anno_presentazione se vuoto (testo grigio non estraibile)
            anno_presentazione = dati.get('anno_presentazione')
            if not anno_presentazione and anno_imposta:
                try:
                    anno_presentazione = int(anno_imposta) + 1
                    logger.info(f"Anno presentazione derivato da anno imposta: {anno_presentazione}")
                except (ValueError, TypeError):
                    anno_presentazione = None
            elif anno_presentazione:
                try:
                    anno_presentazione = int(anno_presentazione)
                except (ValueError, TypeError):
                    anno_presentazione = None
            
            parsed_data = {
                # Dati lavoratore
                'codice_fiscale_lavoratore': cf_lavoratore,
                'cognome_lavoratore': cognome_lavoratore,
                'nome_lavoratore': nome_lavoratore,
                'dipendente_id': lavoratore_info.get('id'),
                
                # Dati datore (con ID cliente se trovato)
                'codice_fiscale_datore': cf_datore,
                'denominazione_datore': dati.get('denominazione_datore', '').strip(),
                'nome_datore': dati.get('nome_datore', '').strip(),
                'cliente_datore_id': datore_info.get('cliente_id'),  # ID o None
                
                # Dati CU
                'anno_riferimento': anno_imposta,
                'anno_presentazione': anno_presentazione,
                'data_comunicazione': dati.get('data_comunicazione'),
                
                # Metadata
                'filename': filename,
            }
            
            # 7. Check duplicati
            # TODO: Fix query AttributoValore - temporaneamente disabilitato
            duplicate_check = None
            # if lavoratore_info.get('id') and anno_imposta:
            #     duplicate_check = self._check_duplicati(
            #         lavoratore_info['id'],
            #         anno_imposta
            #     )
            
            # 8. Prepara valori editabili
            titolo = f"CU {anno_imposta} - {cognome_lavoratore} {nome_lavoratore}".strip()
            valori_editabili = {
                'titolo': titolo,
                'note': f"Importato da {filename}",
            }
            
            # 9. Prepara mappatura DB
            mappatura_db = {
                'tipo': 'CU',
                'attributi': [
                    # Anno
                    {'codice': 'anno_riferimento', 'nome': 'Anno Imposta', 'valore': str(anno_imposta or '')},
                    {'codice': 'anno_presentazione', 'nome': 'Anno Presentazione', 'valore': str(anno_presentazione or '')},
                    # Datore di lavoro
                    {'codice': 'datore_cf', 'nome': 'CF/P.IVA Datore', 'valore': cf_datore},
                    {'codice': 'datore_denominazione', 'nome': 'Denominazione Datore', 'valore': dati.get('denominazione_datore', '')},
                    {'codice': 'datore_nome', 'nome': 'Nome Datore', 'valore': dati.get('nome_datore', '')},
                    # Dipendente
                    {'codice': 'dipendente_cf', 'nome': 'CF Dipendente', 'valore': cf_lavoratore},
                    {'codice': 'dipendente_cognome', 'nome': 'Cognome', 'valore': cognome_lavoratore},
                    {'codice': 'dipendente_nome', 'nome': 'Nome', 'valore': nome_lavoratore},
                ],
                'note_preview': f"CU {anno_imposta} - {cognome_lavoratore} {nome_lavoratore}",
            }
            
            return ParseResult(
                success=True,
                error_message="",
                error_traceback="",
                parsed_data=parsed_data,
                anagrafiche_reperite=anagrafiche_reperite,
                valori_editabili=valori_editabili,
                mappatura_db=mappatura_db,
            )
            
        except DocumentExtractionTemplate.DoesNotExist:
            logger.error("Template AI per CU non trovato. Eseguire configurazione.")
            return ParseResult(
                success=False,
                error_message="Template AI per CU non configurato. Contattare amministratore.",
                error_traceback="",
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={},
            )
        except Exception as e:
            logger.error(f"Errore parsing CU {filename}: {e}", exc_info=True)
            return ParseResult(
                success=False,
                error_message=str(e),
                error_traceback=traceback.format_exc(),
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={},
            )
    
    def _check_duplicati(self, dipendente_id: int, anno_riferimento: int) -> Dict[str, Any]:
        """
        Verifica se esiste già una CU per dipendente+anno.
        
        Args:
            dipendente_id: ID anagrafica dipendente
            anno_riferimento: Anno CU
            
        Returns:
            Dict con info duplicato se trovato, None altrimenti
        """
        try:
            # Cerca tipo documento CU
            tipo_cu = DocumentiTipo.objects.filter(codice='CU').first()
            if not tipo_cu:
                return None
            
            # Cerca attributo dipendente
            attr_dipendente = AttributoDefinizione.objects.filter(
                tipo_documento=tipo_cu,
                codice='dipendente'
            ).first()
            
            attr_anno = AttributoDefinizione.objects.filter(
                tipo_documento=tipo_cu,
                codice='anno_riferimento'
            ).first()
            
            if not attr_dipendente or not attr_anno:
                return None
            
            # Cerca documento esistente
            from django.db.models import Q
            
            # Query documenti CU con stesso dipendente e anno
            documenti_esistenti = Documento.objects.filter(
                tipo=tipo_cu,
                attributi_valori__attributo=attr_dipendente,
                attributi_valori__valore_str=str(dipendente_id),
            ).filter(
                attributi_valori__attributo=attr_anno,
                attributi_valori__valore_int=anno_riferimento,
            ).distinct()
            
            if documenti_esistenti.exists():
                doc = documenti_esistenti.first()
                return {
                    'id': doc.id,
                    'codice': doc.codice,
                    'data_creazione': doc.data_creazione.isoformat(),
                    'note': f"CU anno {anno_riferimento} già presente",
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Errore check duplicati: {e}")
            return None
    
    def check_duplicate(
        self,
        parsed_data: Dict[str, Any],
        valori_editabili: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica se la CU è un duplicato senza crearla.
        
        Criteri duplicazione:
        - Stesso cliente (datore di lavoro)
        - Stesso dipendente (anagrafica lavoratore)
        - Stesso anno_imposta
        
        Returns:
            {
              "is_duplicate": bool,
              "duplicate_info": {
                "id": int,
                "codice": str,
                "anno_imposta": str,
                "dipendente_nome": str,
                "confidence": float,
                "matched_fields": list
              } | None
            }
        """
        from documenti.services.duplicate_detection import DuplicateDetectionService
        
        # Tipo documento CU
        tipo_cu = DocumentiTipo.objects.filter(codice='CU').first()
        if not tipo_cu:
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # 1. Cliente: cerca da anagrafica datore (o usa quello già trovato in parsing)
        cliente_datore_id = parsed_data.get('cliente_datore_id')
        if cliente_datore_id:
            try:
                cliente = Cliente.objects.get(id=cliente_datore_id)
            except Cliente.DoesNotExist:
                cliente = None
        else:
            # Fallback: cerca per CF
            cliente = None
            cf_datore = parsed_data.get('codice_fiscale_datore')
            if cf_datore:
                try:
                    anagrafica_datore = Anagrafica.objects.get(codice_fiscale__iexact=cf_datore)
                    if hasattr(anagrafica_datore, 'cliente'):
                        cliente = anagrafica_datore.cliente
                except (Anagrafica.DoesNotExist, Anagrafica.MultipleObjectsReturned):
                    pass
        
        if not cliente:
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # 2. Anagrafica lavoratore: cerca per CF per ottenere ID
        cf_lavoratore = parsed_data.get('codice_fiscale_lavoratore')
        if not cf_lavoratore:
            return {'is_duplicate': False, 'duplicate_info': None}
        
        try:
            anagrafica_lavoratore = Anagrafica.objects.get(codice_fiscale__iexact=cf_lavoratore)
            dipendente_id = anagrafica_lavoratore.id
        except Anagrafica.DoesNotExist:
            # Dipendente non esiste ancora → non può essere duplicato
            return {'is_duplicate': False, 'duplicate_info': None}
        except Anagrafica.MultipleObjectsReturned:
            logger.warning(f"Multipli dipendenti con CF {cf_lavoratore}")
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # 3. Anno imposta (usa valori editabili se presenti)
        valori = valori_editabili or {}
        anno_riferimento = (
            valori.get('anno_riferimento') or 
            parsed_data.get('anno_riferimento') or 
            parsed_data.get('anno_imposta')
        )
        
        if not anno_riferimento:
            return {'is_duplicate': False, 'duplicate_info': None}
        
        # 4. Prepara attributi per verifica (IMPORTANTE: usa 'anno_riferimento' non 'anno_imposta')
        attributi_per_verifica = {
            'dipendente': dipendente_id,        # ID anagrafica (int)
            'anno_riferimento': str(anno_riferimento)  # Anno riferimento (string) - CHIAVE CORRETTA
        }
        
        # 5. Usa service generico
        service = DuplicateDetectionService(tipo_cu)
        
        if not service.is_enabled():
            return {'is_duplicate': False, 'duplicate_info': None}
        
        result = service.find_duplicate(
            cliente=cliente,
            attributi=attributi_per_verifica
        )
        
        # 6. Formatta risultato per frontend
        if result.is_duplicate and result.documento:
            doc = result.documento
            return {
                'is_duplicate': True,
                'duplicate_info': {
                    'id': doc.id,
                    'codice': doc.codice,
                    'anno_imposta': anno_riferimento,  # Anno di riferimento (usato per display)
                    'dipendente_nome': f"{anagrafica_lavoratore.cognome} {anagrafica_lavoratore.nome}",
                    'data_documento': doc.data_documento.isoformat() if doc.data_documento else None,
                    'confidence': result.confidence,
                    'matched_fields': result.matched_fields,
                }
            }
        
        return {'is_duplicate': False, 'duplicate_info': None}
    
    def create_documento(
        self,
        parsed_data: Dict[str, Any],
        valori_editati: Dict[str, Any],
        user: 'User',
        **kwargs
    ) -> Documento:
        """
        Crea documento CU salvando attributi dinamici.
        Gestisce creazione automatica anagrafiche datore e lavoratore.
        
        Args:
            parsed_data: Dati estratti dal parser (template AI)
            valori_editati: Valori modificati dall'utente (merge con parsed_data)
            user: Utente che sta eseguendo l'import
            **kwargs: Parametri aggiuntivi
            
        Returns:
            Documento creato e salvato
        """
        # Merge dati
        data = {**parsed_data, **valori_editati}
        
        # Recupera tipo documento CU
        tipo_cu = DocumentiTipo.objects.filter(codice='CU').first()
        if not tipo_cu:
            raise ValidationError("Tipo documento 'CU' non trovato. Esegui: python manage.py setup_cu")
        
        # 1. Gestisci DATORE DI LAVORO → Cliente
        # Se già trovato in fase di parsing, riutilizzalo. Altrimenti crea/trova ora.
        cliente_datore_id = data.get('cliente_datore_id')
        if cliente_datore_id:
            # Cliente già trovato in parse_document() → riutilizza
            try:
                cliente_datore = Cliente.objects.get(id=cliente_datore_id)
                logger.debug(f"📌 Riutilizzo cliente datore già trovato: {cliente_datore.anagrafica.codice}")
            except Cliente.DoesNotExist:
                # Fallback: ricerca standard (caso edge raro)
                logger.warning(f"Cliente datore ID {cliente_datore_id} non trovato, ricerco per CF")
                cliente_datore = self._crea_o_trova_cliente_datore(data)
        else:
            # Cliente NON trovato in parsing → crea/cerca ora
            logger.debug("🆕 Cliente datore non trovato in parsing, creazione/ricerca in corso...")
            cliente_datore = self._crea_o_trova_cliente_datore(data)
        
        # 2. Gestisci LAVORATORE → Anagrafica
        anagrafica_lavoratore = self._crea_o_trova_anagrafica_lavoratore(data)
        
        # 3. Ottieni anno imposta (per titolario)
        anno_imposta = data.get('anno_riferimento')
        if not anno_imposta:
            # Fallback: usa anno corrente
            anno_imposta = timezone.now().year
        else:
            try:
                anno_imposta = int(anno_imposta)
            except (ValueError, TypeError):
                anno_imposta = timezone.now().year
        
        # 4. Crea/ottieni titolario gerarchico HR-PERS/{dipendente}/CU/{anno}
        titolario_cu = self._get_titolario_cu(anagrafica_lavoratore, anno_imposta)
        
        # Prepara titolo e note
        cognome = data.get('cognome_lavoratore', '')
        nome = data.get('nome_lavoratore', '')
        anno = data.get('anno_riferimento', '')
        
        titolo = data.get('titolo', f"CU {anno} - {cognome} {nome}").strip()
        note = data.get('note', f"Importato da {data.get('filename', 'ZIP')}")
        
        # Data documento: converti da stringa a date object se necessario
        data_doc = data.get('data_comunicazione')
        if data_doc and isinstance(data_doc, str):
            try:
                data_doc = datetime.strptime(data_doc, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                logger.warning(f"Data comunicazione non valida: {data_doc}, uso data corrente")
                data_doc = timezone.now().date()
        elif not data_doc:
            data_doc = timezone.now().date()
        
        # Crea documento
        with transaction.atomic():
            documento = Documento.objects.create(
                tipo=tipo_cu,
                cliente=cliente_datore,  # Cliente = datore di lavoro
                titolario_voce=titolario_cu,
                descrizione=titolo,
                digitale=True,  # CU sono sempre digitali
                tracciabile=True,
                stato='definitivo',
                data_documento=data_doc,
                note=note,
            )
            
            # Salva attributi dinamici (inclusi dati lavoratore e datore)
            # Riceve attrs_map completo (15+ attributi) per pattern naming
            attrs_map = self._salva_attributi_cu(documento, data, cliente_datore.id, anagrafica_lavoratore.id)
            
            # ✅ FIX: Allega file PDF se fornito
            file_path = kwargs.get('file_path')
            if file_path and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                
                # Imposta flag per saltare rename automatico durante save()
                # (evita rename prematuro prima che attributi siano disponibili)
                documento._skip_auto_rename = True
                
                with open(file_path, 'rb') as f:
                    django_file = DjangoFile(f, name=filename)
                    documento.file.save(filename, django_file, save=True)
                
                logger.info(f"✅ File PDF CU allegato: {filename} → documento {documento.codice}")
                
                # Applica rename con attributi disponibili (attrs_map già popolato da _salva_attributi_cu)
                # Pattern naming basato su titolario + attributi dinamici (15+ attributi)
                logger.debug(
                    f"applica_rename_con_attributi: documento {documento.id}, "
                    f"attrs: {list(attrs_map.keys())}"
                )
                
                try:
                    documento.applica_rename_con_attributi(attrs=attrs_map)
                    logger.info(f"File rinominato: {documento.file.name}")
                except Exception as e:
                    # ✅ Logging migliorato con traceback
                    logger.warning(
                        f"Errore rename file CU: {e}. File salvato con nome originale.",
                        exc_info=True
                    )
            else:
                logger.warning(
                    f"⚠️  File PDF non disponibile per documento CU {documento.id}: "
                    f"file_path={file_path}, "
                    f"exists={os.path.exists(file_path) if file_path else False}"
                )
            
            logger.info(
                f"Creato documento CU {documento.codice} - "
                f"Cliente: {cliente_datore.anagrafica.codice} - "
                f"Dipendente: {cognome} {nome} - "
                f"File: {'✅' if documento.file else '❌'}"
            )
            
        return documento
    
    def _crea_o_trova_cliente_datore(self, data: Dict[str, Any]) -> Cliente:
        """
        Trova o crea Cliente per datore di lavoro.
        
        Determina automaticamente se PF (16 char CF) o PG (11 digit CF/PIVA)
        e crea Anagrafica + Cliente se non esistono.
        
        Args:
            data: Dati con codice_fiscale_datore, denominazione_datore, nome_datore
            
        Returns:
            Cliente datore di lavoro
        """
        cf_datore = data.get('codice_fiscale_datore', '').strip().upper()
        
        if not cf_datore:
            raise ValidationError("Codice fiscale datore di lavoro mancante")
        
        # 1. Cerca Cliente esistente
        cliente = Cliente.objects.filter(
            anagrafica__codice_fiscale__iexact=cf_datore
        ).select_related('anagrafica').first()
        
        if cliente:
            logger.debug(f"Cliente datore esistente: {cliente.anagrafica.codice}")
            return cliente
        
        # 2. Determina tipo (PF o PG)
        if len(cf_datore) == 16:
            tipo = 'PF'
            nome = data.get('nome_datore', '(Da verificare)').strip()
            cognome = ''  # Potrebbe essere nel campo nome
            ragione_sociale = None
        elif len(cf_datore) == 11 and cf_datore.isdigit():
            tipo = 'PG'
            nome = None
            cognome = None
            ragione_sociale = data.get('denominazione_datore', '(Da verificare)').strip()
        else:
            raise ValidationError(f"Codice fiscale datore non valido: {cf_datore}")
        
        # 3. Crea Anagrafica CON codice
        from anagrafiche.utils import genera_codice_cliente
        
        # Prima creiamo senza codice per ottenere l'ID
        anagrafica = Anagrafica.objects.create(
            tipo=tipo,
            codice_fiscale=cf_datore,
            nome=nome,
            cognome=cognome,
            ragione_sociale=ragione_sociale,
        )
        
        # Poi generiamo e assegniamo il codice
        anagrafica.codice = genera_codice_cliente(anagrafica)
        anagrafica.save()
        
        logger.info(f"Anagrafica datore creata: {ragione_sociale or nome} ({tipo}, codice: {anagrafica.codice})")
        
        # 4. Crea Cliente (senza campi codice_cliente/attivo che non esistono)
        cliente = Cliente.objects.create(
            anagrafica=anagrafica,
        )
        
        logger.info(f"Cliente datore creato: {cliente.anagrafica.codice}")
        
        return cliente
    
    def _crea_o_trova_anagrafica_lavoratore(self, data: Dict[str, Any]) -> Anagrafica:
        """
        Trova o crea Anagrafica PF per lavoratore dipendente.
        
        Args:
            data: Dati con codice_fiscale_lavoratore, cognome_lavoratore, nome_lavoratore
            
        Returns:
            Anagrafica lavoratore
        """
        cf_lavoratore = data.get('codice_fiscale_lavoratore', '').strip().upper()
        
        if not cf_lavoratore:
            raise ValidationError("Codice fiscale lavoratore mancante")
        
        # 1. Cerca esistente
        anagrafica = Anagrafica.objects.filter(
            codice_fiscale__iexact=cf_lavoratore
        ).first()
        
        if anagrafica:
            logger.debug(f"Anagrafica lavoratore esistente: {anagrafica.codice_fiscale}")
            return anagrafica
        
        # 2. Crea nuova Anagrafica PF
        cognome = data.get('cognome_lavoratore', '(Da verificare)').strip()
        nome = data.get('nome_lavoratore', '(Da verificare)').strip()
        
        anagrafica = Anagrafica.objects.create(
            tipo='PF',
            codice_fiscale=cf_lavoratore,
            cognome=cognome,
            nome=nome,
        )
        
        logger.info(f"Anagrafica lavoratore creata: {cognome} {nome} (CF: {cf_lavoratore})")
        
        return anagrafica
    
    def _get_titolario_cu(
        self,
        anagrafica_dipendente: Anagrafica,
        anno_imposta: int
    ) -> TitolarioVoce:
        """
        Ottiene o crea la voce titolario gerarchica per CU:
        HR-PERS/{codice_dipendente}/CU/{anno_imposta}
        
        Args:
            anagrafica_dipendente: Anagrafica del dipendente
            anno_imposta: Anno di imposta della CU
            
        Returns:
            TitolarioVoce per l'anno CU del dipendente
        """
        from anagrafiche.utils import get_or_generate_cli
        
        # 1. Verifica/crea voce radice HR-PERS
        try:
            voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
        except TitolarioVoce.DoesNotExist:
            logger.error("Voce titolario HR-PERS non trovata! Crearla manualmente.")
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
        
        # 4. Verifica/crea sottovoce CU (HR-PERS/ROSMAR01/CU)
        voce_cu, created = TitolarioVoce.objects.get_or_create(
            codice='CU',
            parent=voce_dipendente,
            defaults={
                'titolo': 'Certificazioni Uniche',
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
        
        if created:
            logger.info(
                f"Creata voce titolario CU per {codice_dipendente}: "
                f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_cu.codice}"
            )
        
        # 5. Verifica/crea sottovoce per anno imposta (HR-PERS/ROSMAR01/CU/2025)
        anno_str = str(anno_imposta)
        voce_anno, created = TitolarioVoce.objects.get_or_create(
            codice=anno_str,
            parent=voce_cu,
            defaults={
                'titolo': f"Anno {anno_imposta}",
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
        
        if created:
            logger.info(
                f"Creata voce titolario anno CU per {codice_dipendente}: "
                f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_cu.codice}/{voce_anno.codice}"
            )
        
        logger.debug(
            f"Titolario CU: {voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_cu.codice}/{voce_anno.codice}"
        )
        
        return voce_anno
    
    def _salva_attributi_cu(
        self, 
        documento: Documento, 
        data: Dict[str, Any], 
        cliente_datore_id: int,
        anagrafica_lavoratore_id: int
    ) -> Dict[str, Any]:
        """
        Salva attributi dinamici CU estratti da template AI.
        
        Args:
            documento: Documento CU creato
            data: Dati con valori attributi
            cliente_datore_id: ID cliente (datore di lavoro)
            anagrafica_lavoratore_id: ID anagrafica (dipendente)
        
        Returns:
            Dict mapping codice_attributo -> valore per pattern naming
        """
        # Inizializza mappa output per return
        attrs_map_output = {}
        
        # Recupera definizioni attributi
        attributi_def = AttributoDefinizione.objects.filter(tipo_documento=documento.tipo)
        
        # Estrai anno_imposta dai dati (estratto dal template)
        anno_imposta_estratto = data.get('anno_imposta') or data.get('anno_riferimento')
        
        # Mapping valori (dati template AI → attributi DB)
        attr_map = {
            # Anno
            'anno_riferimento': data.get('anno_riferimento') or anno_imposta_estratto,
            'anno_imposta': anno_imposta_estratto,  # Stesso valore di anno_riferimento
            'anno_documento': documento.data_documento.year,  # Anno della data documento
            'anno_presentazione': data.get('anno_presentazione'),
            
            # Relazioni ID
            'committente': cliente_datore_id,  # ID cliente (datore di lavoro)
            'dipendente': anagrafica_lavoratore_id,  # ID anagrafica (dipendente)
            
            # Datore di lavoro (dati testuali)
            'datore_cf': data.get('codice_fiscale_datore', ''),
            'datore_denominazione': data.get('denominazione_datore', ''),
            'datore_nome': data.get('nome_datore', ''),
            
            # Dipendente (dati testuali)
            'dipendente_cf': data.get('codice_fiscale_lavoratore', ''),
            'dipendente_cognome': data.get('cognome_lavoratore', ''),
            'dipendente_nome': data.get('nome_lavoratore', ''),
            
            # Altri attributi economici (opzionali, estratti se presenti nel template)
            'tipo_certificazione': data.get('tipo_certificazione', ''),
            'redditi_lavoro_dipendente': data.get('redditi_lavoro_dipendente', ''),
            'ritenute_irpef': data.get('ritenute_irpef', ''),
            'addizionale_regionale': data.get('addizionale_regionale', ''),
            'addizionale_comunale': data.get('addizionale_comunale', ''),
            'contributi_previdenziali': data.get('contributi_previdenziali', ''),
            'bonus_renzi': data.get('bonus_renzi', ''),
        }
        
        for attr_def in attributi_def:
            valore = attr_map.get(attr_def.codice)
            
            # Salta se vuoto (ma permetti 0 e False)
            if valore is None or valore == '':
                continue
            
            # Converti valore in base al tipo dato
            valore_finale = None
            
            if attr_def.tipo_dato == AttributoDefinizione.TipoDato.INT:
                try:
                    valore_finale = int(valore) if valore else None
                except (ValueError, TypeError):
                    logger.warning(f"Valore non convertibile a int: {attr_def.codice} = {valore}")
                    continue
            elif attr_def.tipo_dato == AttributoDefinizione.TipoDato.DECIMAL:
                try:
                    from decimal import Decimal
                    valore_finale = float(Decimal(str(valore))) if valore else None
                except (ValueError, TypeError):
                    logger.warning(f"Valore non convertibile a decimal: {attr_def.codice} = {valore}")
                    continue
            else:  # STRING, DATE, BOOL, etc.
                valore_finale = str(valore) if valore else None
            
            # Crea AttributoValore con nuovo modello (campo "valore" JSONField)
            AttributoValore.objects.create(
                documento=documento,
                definizione=attr_def,  # FK "definizione" (non "attributo")
                valore=valore_finale,  # JSONField unico
            )
            
            # Popola mappa output per pattern naming
            attrs_map_output[attr_def.codice] = valore_finale
        
        conteggio = len([v for v in attr_map.values() if v])
        logger.debug(f"Salvati {conteggio} attributi per documento {documento.codice}")
        
        # Ritorna mappa completa per pattern naming
        return attrs_map_output
