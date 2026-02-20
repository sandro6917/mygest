"""
Importatore per comunicazioni UNILAV.
Integrato con parser esistente documenti/parsers/unilav_parser.py
"""

import os
import logging
from typing import Dict, List, Any, TYPE_CHECKING
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from django.core.files import File

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from .base import BaseImporter, ParseResult, ImporterRegistry
from ..parsers.unilav_parser import parse_unilav_pdf
from ..models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore
from anagrafiche.models import Anagrafica, Cliente
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


@ImporterRegistry.register
class UNILAVImporter(BaseImporter):
    """
    Importatore per comunicazioni UNILAV.
    
    Supporta:
    - File PDF singolo
    - Estrazione campi da UNILAV
    - Match automatico anagrafiche da CF
    """
    
    tipo = 'unilav'
    display_name = 'Comunicazioni UNILAV'
    supported_extensions = ['.pdf']
    max_file_size_mb = 50
    batch_mode = False  # Tipicamente uno alla volta
    
    def extract_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        UNILAV è sempre singolo PDF.
        """
        return [{
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'ordine': 0,
        }]
    
    def parse_document(self, file_path: str, filename: str) -> ParseResult:
        """
        Parserizza UNILAV PDF usando parser esistente.
        """
        try:
            logger.info(f"Parsing UNILAV: {filename}")
            
            # Usa parser esistente
            parsed = parse_unilav_pdf(file_path)
            
            # Estrai dati
            datore_data = parsed['datore']
            lavoratore_data = parsed['lavoratore']
            unilav_data = parsed['unilav']
            
            # Determina tipo anagrafica datore (PF/PG in base a lunghezza CF)
            cf_datore = datore_data['codice_fiscale']
            tipo_datore = 'PF' if len(cf_datore) == 16 else 'PG'
            
            # Match anagrafiche
            anagrafiche = []
            
            # Match datore
            match_datore = self.match_anagrafica(cf_datore)
            if match_datore:
                match_datore['ruolo'] = 'datore'
                match_datore['tipo'] = tipo_datore
                match_datore['denominazione'] = datore_data['denominazione']
                anagrafiche.append(match_datore)
            else:
                # Anagrafica datore non trovata - aggiungi placeholder
                anagrafiche.append({
                    'codice_fiscale': cf_datore,
                    'nome': datore_data['denominazione'],
                    'match_type': 'not_found',
                    'ruolo': 'datore',
                    'tipo': tipo_datore,
                    'denominazione': datore_data['denominazione'],
                })
            
            # Match lavoratore
            cf_lavoratore = lavoratore_data['codice_fiscale']
            match_lavoratore = self.match_anagrafica(cf_lavoratore)
            if match_lavoratore:
                match_lavoratore['ruolo'] = 'lavoratore'
                match_lavoratore['tipo'] = 'PF'
                match_lavoratore['denominazione'] = f"{lavoratore_data['cognome']} {lavoratore_data['nome']}"
                anagrafiche.append(match_lavoratore)
            else:
                # Anagrafica lavoratore non trovata - aggiungi placeholder
                anagrafiche.append({
                    'codice_fiscale': cf_lavoratore,
                    'nome': f"{lavoratore_data['cognome']} {lavoratore_data['nome']}",
                    'match_type': 'not_found',
                    'ruolo': 'lavoratore',
                    'tipo': 'PF',
                    'denominazione': f"{lavoratore_data['cognome']} {lavoratore_data['nome']}",
                })
            
            # Mappa tipo comunicazione da modello
            tipo_mappato = self._mappa_tipo_comunicazione(
                modello=unilav_data.get('modello'),
                tipologia_contrattuale=unilav_data.get('tipologia_contrattuale'),
                tipo_comunicazione=unilav_data.get('tipo_comunicazione')
            )
            
            # Valori editabili (tutti i campi UNILAV)
            valori_editabili = {
                # Datore
                'datore_cf': cf_datore,
                'datore_denominazione': datore_data['denominazione'],
                'datore_email': datore_data.get('email'),
                'datore_telefono': datore_data.get('telefono'),
                'datore_comune': datore_data.get('comune_sede_legale'),
                'datore_cap': datore_data.get('cap_sede_legale'),
                'datore_indirizzo': datore_data.get('indirizzo_sede_legale'),
                # Lavoratore
                'lavoratore_cf': cf_lavoratore,
                'lavoratore_cognome': lavoratore_data['cognome'],
                'lavoratore_nome': lavoratore_data['nome'],
                'lavoratore_sesso': lavoratore_data.get('sesso'),
                'lavoratore_data_nascita': lavoratore_data.get('data_nascita'),
                'lavoratore_comune_nascita': lavoratore_data.get('comune_nascita'),
                'lavoratore_comune': lavoratore_data.get('comune_domicilio'),
                'lavoratore_cap': lavoratore_data.get('cap_domicilio'),
                'lavoratore_indirizzo': lavoratore_data.get('indirizzo_domicilio'),
                # Documento UNILAV
                'codice_comunicazione': unilav_data['codice_comunicazione'],
                'tipo_comunicazione': unilav_data.get('tipo_comunicazione'),
                'modello': unilav_data.get('modello'),
                'data_comunicazione': unilav_data['data_comunicazione'],
                'centro_impiego': unilav_data.get('centro_impiego'),
                'provincia_impiego': unilav_data.get('provincia_impiego'),
                'tipo': tipo_mappato,
                'data_da': unilav_data.get('data_inizio_rapporto'),
                'data_a': unilav_data.get('data_fine_rapporto'),
                'data_proroga': unilav_data.get('data_proroga'),
                'data_trasformazione': unilav_data.get('data_trasformazione'),
                'causa_trasformazione': unilav_data.get('causa_trasformazione'),
                'ente_previdenziale': unilav_data.get('ente_previdenziale'),
                'codice_ente_previdenziale': unilav_data.get('codice_ente_previdenziale'),
                'pat_inail': unilav_data.get('pat_inail'),
                'qualifica': unilav_data.get('qualifica_professionale'),
                'contratto_collettivo': unilav_data.get('contratto_collettivo'),
                'livello': unilav_data.get('livello_inquadramento'),
                'retribuzione': unilav_data.get('retribuzione'),
                'ore_settimanali': unilav_data.get('ore_settimanali'),
                'tipo_orario': unilav_data.get('tipo_orario'),
            }
            
            # Descrizione documento
            descrizione = f"UNILAV {tipo_mappato} {unilav_data['codice_comunicazione']} - {lavoratore_data['cognome']} {lavoratore_data['nome']}"
            
            # Costruisci preview note con dati aggiuntivi
            note_preview_parts = [
                f"Tipo Comunicazione: {tipo_mappato}",
                f"Codice Comunicazione: {unilav_data['codice_comunicazione']}",
                f"Data Comunicazione: {unilav_data['data_comunicazione']}",
                "",
                "=== DATORE DI LAVORO ===",
                f"Denominazione: {datore_data['denominazione']}",
                f"Codice Fiscale: {cf_datore}",
            ]
            
            if datore_data.get('email'):
                note_preview_parts.append(f"Email: {datore_data['email']}")
            if datore_data.get('telefono'):
                note_preview_parts.append(f"Telefono: {datore_data['telefono']}")
            if datore_data.get('comune_sede_legale'):
                note_preview_parts.append(f"Comune: {datore_data['comune_sede_legale']}")
                
            note_preview_parts.extend([
                "",
                "=== LAVORATORE ===",
                f"Nome: {lavoratore_data['nome']} {lavoratore_data['cognome']}",
                f"Codice Fiscale: {cf_lavoratore}",
            ])
            
            if lavoratore_data.get('data_nascita'):
                note_preview_parts.append(f"Data Nascita: {lavoratore_data['data_nascita']}")
            if lavoratore_data.get('comune_nascita'):
                note_preview_parts.append(f"Luogo Nascita: {lavoratore_data['comune_nascita']}")
                
            note_preview_parts.append("")
            note_preview_parts.append("=== DATI RAPPORTO ===")
            
            if unilav_data.get('data_inizio_rapporto'):
                note_preview_parts.append(f"Data Inizio: {unilav_data['data_inizio_rapporto']}")
            if unilav_data.get('data_fine_rapporto'):
                note_preview_parts.append(f"Data Fine: {unilav_data['data_fine_rapporto']}")
            if unilav_data.get('data_proroga'):
                note_preview_parts.append(f"Data Proroga: {unilav_data['data_proroga']}")
            if unilav_data.get('data_trasformazione'):
                note_preview_parts.append(f"Data Trasformazione: {unilav_data['data_trasformazione']}")
            if unilav_data.get('causa_trasformazione'):
                note_preview_parts.append(f"Causa Trasformazione: {unilav_data['causa_trasformazione']}")
            if unilav_data.get('qualifica_professionale'):
                note_preview_parts.append(f"Qualifica: {unilav_data['qualifica_professionale']}")
            if unilav_data.get('contratto_collettivo'):
                note_preview_parts.append(f"CCNL: {unilav_data['contratto_collettivo']}")
            if unilav_data.get('livello_inquadramento'):
                note_preview_parts.append(f"Livello: {unilav_data['livello_inquadramento']}")
            if unilav_data.get('retribuzione'):
                note_preview_parts.append(f"Retribuzione: {unilav_data['retribuzione']}")
            if unilav_data.get('ore_settimanali'):
                note_preview_parts.append(f"Ore Settimanali: {unilav_data['ore_settimanali']}")
            if unilav_data.get('tipo_orario'):
                note_preview_parts.append(f"Tipo Orario: {unilav_data['tipo_orario']}")
            
            note_preview = "\n".join(note_preview_parts)
            
            # Mappatura DB con tutti gli attributi per il frontend
            mappatura_db = {
                'tipo': 'UNILAV',
                'tipo_documento_codice': 'UNILAV',
                'descrizione': descrizione,
                'data_documento': unilav_data['data_comunicazione'],
                'digitale': True,
                'tracciabile': True,
                'attributi': [
                    {'codice': 'codice_comunicazione', 'nome': 'Codice Comunicazione', 'valore': unilav_data['codice_comunicazione']},
                    {'codice': 'tipo', 'nome': 'Tipo', 'valore': tipo_mappato},
                    {'codice': 'modello', 'nome': 'Modello', 'valore': unilav_data.get('modello')},
                    {'codice': 'data_comunicazione', 'nome': 'Data Comunicazione', 'valore': unilav_data['data_comunicazione']},
                    {'codice': 'datore_denominazione', 'nome': 'Datore - Denominazione', 'valore': datore_data['denominazione']},
                    {'codice': 'datore_cf', 'nome': 'Datore - CF/PIVA', 'valore': cf_datore},
                    {'codice': 'lavoratore_nome_completo', 'nome': 'Lavoratore', 'valore': f"{lavoratore_data['cognome']} {lavoratore_data['nome']}"},
                    {'codice': 'lavoratore_cf', 'nome': 'Lavoratore - CF', 'valore': cf_lavoratore},
                ],
                'note_preview': note_preview,
            }
            
            # Aggiungi attributi opzionali se presenti
            if unilav_data.get('data_inizio_rapporto'):
                mappatura_db['attributi'].append({
                    'codice': 'data_da', 'nome': 'Data Inizio Rapporto', 'valore': unilav_data['data_inizio_rapporto']
                })
            if unilav_data.get('data_fine_rapporto'):
                mappatura_db['attributi'].append({
                    'codice': 'data_a', 'nome': 'Data Fine Rapporto', 'valore': unilav_data['data_fine_rapporto']
                })
            if unilav_data.get('data_proroga'):
                mappatura_db['attributi'].append({
                    'codice': 'data_proroga', 'nome': 'Data Proroga', 'valore': unilav_data['data_proroga']
                })
            if unilav_data.get('data_trasformazione'):
                mappatura_db['attributi'].append({
                    'codice': 'data_trasformazione', 'nome': 'Data Trasformazione', 'valore': unilav_data['data_trasformazione']
                })
            if unilav_data.get('causa_trasformazione'):
                mappatura_db['attributi'].append({
                    'codice': 'causa_trasformazione', 'nome': 'Causa Trasformazione', 'valore': unilav_data['causa_trasformazione']
                })
            if unilav_data.get('qualifica_professionale'):
                mappatura_db['attributi'].append({
                    'codice': 'qualifica', 'nome': 'Qualifica', 'valore': unilav_data['qualifica_professionale']
                })
            if unilav_data.get('contratto_collettivo'):
                mappatura_db['attributi'].append({
                    'codice': 'contratto_collettivo', 'nome': 'CCNL', 'valore': unilav_data['contratto_collettivo']
                })
            if unilav_data.get('livello_inquadramento'):
                mappatura_db['attributi'].append({
                    'codice': 'livello', 'nome': 'Livello', 'valore': unilav_data['livello_inquadramento']
                })
            if unilav_data.get('retribuzione'):
                mappatura_db['attributi'].append({
                    'codice': 'retribuzione', 'nome': 'Retribuzione', 'valore': unilav_data['retribuzione']
                })
            if unilav_data.get('ore_settimanali'):
                mappatura_db['attributi'].append({
                    'codice': 'ore_settimanali', 'nome': 'Ore Settimanali', 'valore': unilav_data['ore_settimanali']
                })
            if unilav_data.get('tipo_orario'):
                mappatura_db['attributi'].append({
                    'codice': 'tipo_orario', 'nome': 'Tipo Orario', 'valore': unilav_data['tipo_orario']
                })
            
            return ParseResult(
                success=True,
                parsed_data=parsed,
                anagrafiche_reperite=anagrafiche,
                valori_editabili=valori_editabili,
                mappatura_db=mappatura_db,
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Errore parsing UNILAV {filename}: {e}")
            logger.error(traceback.format_exc())
            
            return ParseResult(
                success=False,
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={},
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )
    
    def check_duplicate(
        self,
        parsed_data: Dict[str, Any],
        valori_editabili: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica se l'UNILAV è un duplicato senza crearlo.
        
        Returns:
            {
              "is_duplicate": bool,
              "duplicate_info": {
                "id": int,
                "codice": str,
                "codice_comunicazione": str,
                "data_comunicazione": str,
                "confidence": float,
                "matched_fields": list
              } | None
            }
        """
        from documenti.services.duplicate_detection import DuplicateDetectionService
        
        # Tipo documento UNILAV
        tipo_unilav = DocumentiTipo.objects.filter(codice='UNILAV').first()
        if not tipo_unilav:
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
            'codice_comunicazione': valori.get('codice_comunicazione') or parsed_data['unilav'].get('codice_comunicazione'),
            'data_comunicazione': valori.get('data_comunicazione') or parsed_data['unilav'].get('data_comunicazione'),
        }
        
        # Usa service generico
        service = DuplicateDetectionService(tipo_unilav)
        
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
                    'codice_comunicazione': attributi_per_verifica.get('codice_comunicazione'),
                    'data_comunicazione': attributi_per_verifica.get('data_comunicazione'),
                    'confidence': result.confidence,
                    'matched_fields': result.matched_fields,
                }
            }
        else:
            return {'is_duplicate': False, 'duplicate_info': None}
    
    def _get_or_create_titolario_dipendente(self, anagrafica_dipendente: Anagrafica) -> TitolarioVoce:
        """
        Ottiene o crea la voce titolario CONTRATTI per il dipendente.
        
        Struttura: HR-PERS/{CODICE_ANAGRAFICA}/CONTRATTI
        Esempio: HR-PERS/ROSMAR01/CONTRATTI
        
        Args:
            anagrafica_dipendente: Anagrafica del lavoratore
            
        Returns:
            TitolarioVoce CONTRATTI per il dipendente
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
        
        # 4. Verifica/crea sottovoce CONTRATTI (HR-PERS/ROSMAR01/CONTRATTI)
        voce_contratti, created = TitolarioVoce.objects.get_or_create(
            codice='CONTRATTI',
            parent=voce_dipendente,
            defaults={
                'titolo': 'Contratti di lavoro',
                'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
            }
        )
        
        if created:
            logger.info(
                f"Creata voce titolario CONTRATTI per {codice_dipendente}: "
                f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_contratti.codice}"
            )
        
        logger.debug(
            f"Titolario UNILAV: {voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_contratti.codice}"
        )
        
        return voce_contratti
    
    def _mappa_tipo_comunicazione(
        self, 
        modello: str = None, 
        tipologia_contrattuale: str = None,
        tipo_comunicazione: str = None
    ) -> str:
        """
        Mappa tipo comunicazione UNILAV a uno dei valori standard.
        Priorità: modello > tipologia_contrattuale > tipo_comunicazione
        """
        # Mapping basato su campo "modello" (priorità massima)
        if modello:
            modello_upper = modello.upper()
            if 'ASSUNZIONE' in modello_upper or 'INSTAURAZIONE' in modello_upper:
                return 'Assunzione'
            elif 'PROROGA' in modello_upper:
                return 'Proroga'
            elif 'TRASFORMAZIONE' in modello_upper:
                return 'Trasformazione'
            elif 'CESSAZIONE' in modello_upper:
                return 'Cessazione'
        
        # Fallback su tipologia_contrattuale
        if tipologia_contrattuale:
            tipologia_upper = tipologia_contrattuale.upper()
            if 'INDETERMINATO' in tipologia_upper:
                return 'Assunzione'
            elif 'DETERMINATO' in tipologia_upper:
                return 'Assunzione'
        
        # Default
        return tipo_comunicazione or 'Assunzione'
    
    @transaction.atomic
    def create_documento(
        self,
        parsed_data: Dict[str, Any],
        valori_editati: Dict[str, Any],
        user: 'User',
        **kwargs
    ) -> 'Documento':
        """
        Crea documento UNILAV nel DB con logica completa.
        
        Gestisce:
        - Creazione/aggiornamento anagrafiche (datore + lavoratore)
        - Creazione cliente (datore)
        - Creazione fascicolo (se necessario)
        - Salvataggio attributi dinamici
        - Salvataggio note aggiuntive
        """
        logger.info(f"Creazione documento UNILAV per utente {user.username}")
        
        # 0. Converti data_comunicazione da stringa a date object
        from datetime import datetime
        data_comunicazione_str = valori_editati['data_comunicazione']
        if isinstance(data_comunicazione_str, str):
            data_comunicazione = datetime.strptime(data_comunicazione_str, '%Y-%m-%d').date()
        else:
            # Se già è un date object, usalo direttamente
            data_comunicazione = data_comunicazione_str
        
        # 1. Gestione Anagrafica e Cliente DATORE
        cf_datore = valori_editati['datore_cf']
        tipo_datore = 'PF' if len(cf_datore) == 16 else 'PG'
        
        # Prepara defaults per datore (solo campi validi di Anagrafica)
        datore_defaults = {
            'tipo': tipo_datore,
            'email': (valori_editati.get('datore_email') or ''),
            'telefono': (valori_editati.get('datore_telefono') or ''),
        }
        
        if tipo_datore == 'PG':
            datore_defaults['ragione_sociale'] = (valori_editati.get('datore_denominazione') or '')
        else:  # PF
            datore_defaults['cognome'] = (valori_editati.get('datore_cognome') or '')
            datore_defaults['nome'] = (valori_editati.get('datore_nome') or '')
        
        anagrafica_datore, created = Anagrafica.objects.get_or_create(
            codice_fiscale=cf_datore,
            defaults=datore_defaults
        )
        
        if created:
            logger.info(f"Creata nuova anagrafica datore: {anagrafica_datore}")
            
            # Crea indirizzo datore se disponibile
            indirizzo_datore = (valori_editati.get('datore_indirizzo') or '').strip()
            comune_datore = (valori_editati.get('datore_comune') or '').strip()
            
            if indirizzo_datore and comune_datore:
                from anagrafiche.models import Indirizzo
                
                Indirizzo.objects.create(
                    anagrafica=anagrafica_datore,
                    tipo_indirizzo='SLE' if tipo_datore == 'PG' else 'RES',
                    indirizzo=indirizzo_datore,
                    comune=comune_datore,
                    cap=(valori_editati.get('datore_cap') or ''),
                    provincia=(valori_editati.get('datore_provincia') or ''),
                    principale=True
                )
                logger.info(f"Creato indirizzo principale per datore: {comune_datore}")
        
        cliente_datore, _ = Cliente.objects.get_or_create(
            anagrafica=anagrafica_datore
        )
        
        # 2. Gestione Anagrafica LAVORATORE
        cf_lavoratore = valori_editati['lavoratore_cf']
        
        # Prepara defaults per lavoratore (solo campi validi di Anagrafica)
        lavoratore_defaults = {
            'tipo': 'PF',
            'cognome': (valori_editati.get('lavoratore_cognome') or ''),
            'nome': (valori_editati.get('lavoratore_nome') or ''),
        }
        
        anagrafica_lavoratore, created = Anagrafica.objects.get_or_create(
            codice_fiscale=cf_lavoratore,
            defaults=lavoratore_defaults
        )
        
        if created:
            logger.info(f"Creata nuova anagrafica lavoratore: {anagrafica_lavoratore}")
            
            # Crea indirizzo lavoratore se disponibile
            indirizzo_lavoratore = (valori_editati.get('lavoratore_indirizzo') or '').strip()
            comune_lavoratore = (valori_editati.get('lavoratore_comune') or '').strip()
            
            if indirizzo_lavoratore and comune_lavoratore:
                from anagrafiche.models import Indirizzo
                
                Indirizzo.objects.create(
                    anagrafica=anagrafica_lavoratore,
                    tipo_indirizzo='RES',
                    indirizzo=indirizzo_lavoratore,
                    comune=comune_lavoratore,
                    cap=(valori_editati.get('lavoratore_cap') or ''),
                    provincia=(valori_editati.get('lavoratore_provincia') or ''),
                    principale=True
                )
                logger.info(f"Creato indirizzo principale per lavoratore: {comune_lavoratore}")

        
        # 3. Recupera/Crea Tipo UNILAV
        tipo_unilav, _ = DocumentiTipo.objects.get_or_create(
            codice='UNILAV',
            defaults={'descrizione': 'Comunicazione UNILAV'}
        )
        
        # 4. Titolario: Gerarchia HR-PERS/{CODICE_DIPENDENTE}/CONTRATTI
        # Esempio: HR-PERS/ROSMAR01/CONTRATTI
        titolario = self._get_or_create_titolario_dipendente(anagrafica_lavoratore)
        
        # 5. Crea Fascicolo (se necessario)
        fascicolo = None
        tipo_comunicazione = valori_editati.get('tipo', 'Assunzione')
        
        # Recupera/Crea voce titolario per dossier personale lavoratore
        try:
            # Cerca voce titolario HR-PERS (Dossier personale)
            voce_dossier = TitolarioVoce.objects.filter(
                codice__icontains='HR-PERS'
            ).first()
            
            if voce_dossier:
                # Crea fascicolo per lavoratore se non esiste
                titolo_fascicolo = f"Dossier {anagrafica_lavoratore.display_name()}"
                fascicolo, _ = Fascicolo.objects.get_or_create(
                    titolario_voce=voce_dossier,
                    cliente=cliente_datore,
                    titolo__icontains=anagrafica_lavoratore.cognome,
                    defaults={
                        'titolo': titolo_fascicolo,
                        'anno': data_comunicazione.year,
                        'note': f"Dossier personale {anagrafica_lavoratore.display_name()}",
                    }
                )
        except Exception as e:
            logger.warning(f"Impossibile creare fascicolo: {e}")
        
        # 6. Crea Documento
        descrizione = f"UNILAV {tipo_comunicazione} {valori_editati['codice_comunicazione']} - {anagrafica_lavoratore.display_name()}"
        
        documento = Documento.objects.create(
            tipo=tipo_unilav,
            cliente=cliente_datore,
            fascicolo=fascicolo,
            titolario_voce=titolario,
            descrizione=descrizione,
            data_documento=data_comunicazione,
            digitale=True,
            tracciabile=True,
            stato=Documento.Stato.DEFINITIVO,
        )
        
        logger.info(f"Creato documento UNILAV #{documento.id}: {descrizione}")
        
        # 7. Salva file PDF
        file_path = kwargs.get('file_path')
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                documento.file.save(
                    os.path.basename(file_path),
                    File(f),
                    save=True
                )
        
        # 8. Salva Attributi Dinamici
        attributi_map = {
            'codice_comunicazione': valori_editati.get('codice_comunicazione'),
            'dipendente': anagrafica_lavoratore.id,
            'tipo': tipo_comunicazione,
            'data_comunicazione': valori_editati.get('data_comunicazione'),
            'data_da': valori_editati.get('data_da'),
            'data_a': valori_editati.get('data_a'),
            'data_proroga': valori_editati.get('data_proroga'),
        }
        
        for codice_attr, valore in attributi_map.items():
            if valore is not None:
                try:
                    definizione = AttributoDefinizione.objects.get(
                        tipo_documento=tipo_unilav,
                        codice=codice_attr
                    )
                    
                    AttributoValore.objects.update_or_create(
                        documento=documento,
                        definizione=definizione,
                        defaults={'valore': str(valore)}
                    )
                    
                    logger.debug(f"Salvato attributo '{codice_attr}': {valore}")
                    
                except AttributoDefinizione.DoesNotExist:
                    logger.warning(f"Attributo '{codice_attr}' non configurato, saltato")
        
        # 9. Salva dati aggiuntivi in NOTE
        note_extra = []
        
        # Dati trasformazione (solo per Trasformazione)
        if valori_editati.get('data_trasformazione'):
            note_extra.append(f"Data Trasformazione: {valori_editati['data_trasformazione']}")
        if valori_editati.get('causa_trasformazione'):
            note_extra.append(f"Causa Trasformazione: {valori_editati['causa_trasformazione']}")
        
        # Altri dati
        if valori_editati.get('qualifica'):
            note_extra.append(f"Qualifica: {valori_editati['qualifica']}")
        if valori_editati.get('contratto_collettivo'):
            note_extra.append(f"CCNL: {valori_editati['contratto_collettivo']}")
        if valori_editati.get('livello'):
            note_extra.append(f"Livello: {valori_editati['livello']}")
        if valori_editati.get('retribuzione'):
            note_extra.append(f"Retribuzione: {valori_editati['retribuzione']}")
        if valori_editati.get('ore_settimanali'):
            note_extra.append(f"Ore settimanali: {valori_editati['ore_settimanali']}")
        if valori_editati.get('tipo_orario'):
            note_extra.append(f"Tipo orario: {valori_editati['tipo_orario']}")
        
        if note_extra:
            documento.note = '\n'.join(note_extra)
            documento.save()
        
        logger.info(f"✓ Documento UNILAV #{documento.id} creato con successo")
        
        return documento
