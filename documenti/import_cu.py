"""
Logica business per l'importazione di Certificazioni Uniche (CU).

Gestisce:
- Estrazione file ZIP contenente CU
- Parsing CU (estrazione dati fiscali)
- Creazione/ricerca anagrafica dipendente e datore di lavoro
- Creazione documento CU con attributi dinamici
"""
from __future__ import annotations
import logging
import zipfile
from io import BytesIO
from typing import Dict, List, Any
from datetime import date
from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from anagrafiche.models import Anagrafica, Cliente
from anagrafiche.utils import get_or_generate_cli
from fascicoli.models import Fascicolo
from titolario.models import TitolarioVoce
from documenti.models import Documento, DocumentiTipo, AttributoValore, AttributoDefinizione
from documenti.parsers.cu_parser import parse_cu_pdf

logger = logging.getLogger(__name__)
User = get_user_model()


class CUImporter:
    """Classe per gestire l'importazione di Certificazioni Uniche"""
    
    def __init__(self, zip_file, user=None, duplicate_policy='skip'):
        """
        Inizializza l'importer.
        
        Args:
            zip_file: File ZIP contenente le CU
            user: Utente che richiede l'import (opzionale)
            duplicate_policy: Gestione duplicati ('skip', 'replace', 'add')
        """
        self.zip_file = zip_file
        self.user = user
        self.duplicate_policy = duplicate_policy
        self.tipo_cu = None
        self.voce_hr_cu = None
        self.risultati = {
            'created': 0,
            'replaced': 0,
            'skipped': 0,
            'errors': [],
            'documenti': [],
            'warnings': [],
        }
    
    def importa(self) -> Dict[str, Any]:
        """
        Esegue l'importazione completa.
        
        Returns:
            Dict con risultati: created, errors, documenti, warnings
        """
        logger.info(f"Inizio importazione CU da {self.zip_file.name}")
        
        try:
            # Carica tipo documento CU
            self.tipo_cu = DocumentiTipo.objects.get(codice='CU')
            
            # Carica voce titolario HR-CU (Certificazioni Uniche)
            self.voce_hr_cu = TitolarioVoce.objects.get(codice='HR-CU')
            
        except DocumentiTipo.DoesNotExist:
            error_msg = "Tipo documento CU mancante. Eseguire: python manage.py setup_cu"
            logger.error(error_msg)
            self.risultati['errors'].append(error_msg)
            return self.risultati
        except TitolarioVoce.DoesNotExist:
            error_msg = "Voce titolario HR-CU non trovata. Eseguire: python manage.py setup_cu"
            logger.error(error_msg)
            self.risultati['errors'].append(error_msg)
            return self.risultati
        
        # Estrai e processa file dal ZIP
        try:
            with zipfile.ZipFile(BytesIO(self.zip_file.read()), 'r') as zip_ref:
                pdf_files = [f for f in zip_ref.namelist() if f.endswith('.pdf')]
                total_files = len(pdf_files)
                
                logger.info(f"Trovati {total_files} file PDF nel ZIP")
                self.risultati['total'] = total_files
                
                for pdf_filename in pdf_files:
                    try:
                        pdf_content = zip_ref.read(pdf_filename)
                        self._processa_cu(pdf_filename, pdf_content)
                    except Exception as e:
                        error_msg = f"Errore processando {pdf_filename}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        self.risultati['errors'].append({
                            'filename': pdf_filename,
                            'error': str(e)
                        })
        
        except zipfile.BadZipFile:
            error_msg = "File ZIP non valido o corrotto"
            logger.error(error_msg)
            self.risultati['errors'].append({
                'filename': self.zip_file.name,
                'error': error_msg
            })
        except Exception as e:
            error_msg = f"Errore durante l'estrazione del ZIP: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.risultati['errors'].append({
                'filename': self.zip_file.name,
                'error': error_msg
            })
        
        logger.info(
            f"Importazione completata: {self.risultati['created']}/{self.risultati.get('total', 0)} "
            f"documenti creati, {len(self.risultati['errors'])} errori"
        )
        
        return self.risultati
    
    def _processa_cu(self, filename: str, pdf_content: bytes):
        """
        Processa una singola CU.
        
        Args:
            filename: Nome file PDF
            pdf_content: Contenuto binario PDF
        """
        logger.info(f"Processando CU: {filename}")
        
        # Salva temporaneamente il PDF per il parser
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            with open(temp_path, 'wb') as f:
                f.write(pdf_content)
            
            # 1. Parse PDF CU
            parsed_data = parse_cu_pdf(temp_path)
            
            # Estrai dati
            sostituto_data = parsed_data['sostituto']
            percipiente_data = parsed_data['percipiente']
            cu_data = parsed_data['cu']
            
            # Validazione dati essenziali
            if not sostituto_data.get('codice_fiscale'):
                error_msg = f"CF datore non trovato in: {filename}"
                logger.warning(error_msg)
                self.risultati['errors'].append({
                    'filename': filename,
                    'error': error_msg
                })
                return
            
            if not percipiente_data.get('codice_fiscale'):
                error_msg = f"CF dipendente non trovato in: {filename}"
                logger.warning(error_msg)
                self.risultati['errors'].append({
                    'filename': filename,
                    'error': error_msg
                })
                return
            
            with transaction.atomic():
                # 2. Crea/trova anagrafica datore (sostituto d'imposta)
                datore = self._crea_o_trova_datore(sostituto_data)
                
                # 3. Crea/trova cliente datore
                cliente_datore, _ = Cliente.objects.get_or_create(anagrafica=datore)
                
                # 4. Crea/trova anagrafica dipendente (percipiente)
                dipendente = self._crea_o_trova_dipendente(percipiente_data)
                
                # 5. Crea/trova voce titolario intestata al dipendente
                voce_dipendente = self._crea_o_trova_voce_dipendente(dipendente)
                
                # 6. Verifica duplicato
                anno_riferimento = cu_data['anno_riferimento']
                
                documento_esistente = self._find_duplicate(dipendente, anno_riferimento)
                
                if documento_esistente:
                    if self.duplicate_policy == 'skip':
                        self.risultati['skipped'] += 1
                        logger.info(f"CU saltata (duplicato): {filename}")
                        return
                    elif self.duplicate_policy == 'replace':
                        # Aggiorna documento esistente
                        documento = documento_esistente
                        if documento.file:
                            documento.file.delete(save=False)
                        
                        documento.descrizione = self._genera_descrizione(percipiente_data, anno_riferimento)
                        documento.data_documento = date(anno_riferimento, 12, 31)
                        documento.cliente = cliente_datore
                        documento.titolario_voce = voce_dipendente
                        
                        # Salva file
                        documento.file.save(filename, ContentFile(pdf_content), save=True)
                        
                        # Elimina vecchi attributi
                        AttributoValore.objects.filter(documento=documento).delete()
                        
                        self.risultati['replaced'] += 1
                        action = 'sostituito'
                    else:  # 'add'
                        documento = None  # Crea nuovo documento
                
                # 7. Crea nuovo documento (se non replace)
                if not documento_esistente or self.duplicate_policy == 'add':
                    descrizione = self._genera_descrizione(percipiente_data, anno_riferimento)
                    
                    documento = Documento.objects.create(
                        tipo=self.tipo_cu,
                        cliente=cliente_datore,
                        titolario_voce=voce_dipendente,
                        descrizione=descrizione,
                        data_documento=date(anno_riferimento, 12, 31),  # 31/12 dell'anno di riferimento
                        stato=Documento.Stato.DEFINITIVO,
                        digitale=True,
                        tracciabile=True,
                    )
                    
                    # Salva file
                    documento.file.save(filename, ContentFile(pdf_content), save=True)
                    
                    self.risultati['created'] += 1
                    action = 'creato'
                
                # 8. Salva attributi dinamici
                self._salva_attributi(documento, cu_data, dipendente)
                
                # 9. Rigenera codice se usa attributi
                if '{ATTR:' in (voce_dipendente.pattern_codice or ''):
                    documento.rigenera_codice_con_attributi()
                
                # Aggiungi a risultati
                self.risultati['documenti'].append({
                    'id': documento.id,
                    'codice': documento.codice,
                    'descrizione': documento.descrizione,
                    'filename': filename,
                    'action': action,
                })
                
                logger.info(f"CU {action}: {documento.codice}")
        
        finally:
            # Cleanup file temporaneo
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
    
    def _crea_o_trova_datore(self, sostituto_data: Dict[str, Any]) -> Anagrafica:
        """Crea o trova anagrafica del datore di lavoro (sostituto d'imposta)"""
        cf = sostituto_data['codice_fiscale']
        
        # Cerca per CF o P.IVA
        from django.db.models import Q
        anagrafica = Anagrafica.objects.filter(
            Q(codice_fiscale=cf) | Q(partita_iva=cf)
        ).first()
        
        if anagrafica:
            return anagrafica
        
        # Determina tipo (PG se 11 cifre, PF se 16)
        tipo = 'PG' if len(cf) == 11 else 'PF'
        
        # Crea nuova anagrafica
        anagrafica = Anagrafica.objects.create(
            tipo=tipo,
            codice_fiscale=cf,
            partita_iva=sostituto_data.get('partita_iva') if tipo == 'PG' else None,
            denominazione=sostituto_data.get('denominazione') if tipo == 'PG' else None,
        )
        
        # Genera codice anagrafica
        get_or_generate_cli(anagrafica)
        anagrafica.refresh_from_db()
        
        logger.info(f"Creata anagrafica datore: {anagrafica.display_name()}")
        
        return anagrafica
    
    def _crea_o_trova_dipendente(self, percipiente_data: Dict[str, Any]) -> Anagrafica:
        """Crea o trova anagrafica del dipendente (percipiente)"""
        cf = percipiente_data['codice_fiscale']
        
        # Cerca per CF
        anagrafica = Anagrafica.objects.filter(codice_fiscale=cf).first()
        
        if anagrafica:
            return anagrafica
        
        # Crea nuova anagrafica
        anagrafica = Anagrafica.objects.create(
            tipo='PF',
            codice_fiscale=cf,
            cognome=percipiente_data.get('cognome', ''),
            nome=percipiente_data.get('nome', ''),
        )
        
        # Genera codice anagrafica
        get_or_generate_cli(anagrafica)
        anagrafica.refresh_from_db()
        
        logger.info(f"Creata anagrafica dipendente: {anagrafica.display_name()}")
        
        return anagrafica
    
    def _crea_o_trova_voce_dipendente(self, dipendente: Anagrafica) -> TitolarioVoce:
        """Crea o trova voce titolario intestata al dipendente sotto HR-PERS"""
        # Cerca voce HR-PERS
        try:
            voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
        except TitolarioVoce.DoesNotExist:
            logger.warning("Voce HR-PERS non trovata, uso HR-CU come parent")
            voce_hr_pers = self.voce_hr_cu
        
        # Verifica che il dipendente abbia codice
        if not dipendente.codice:
            get_or_generate_cli(dipendente)
            dipendente.refresh_from_db()
        
        # Cerca voce esistente per codice dipendente
        voce_dipendente = TitolarioVoce.objects.filter(
            parent=voce_hr_pers,
            codice=dipendente.codice
        ).first()
        
        if voce_dipendente:
            # Assicura collegamento anagrafica
            if voce_dipendente.anagrafica_id != dipendente.id:
                voce_dipendente.anagrafica = dipendente
                voce_dipendente.save(update_fields=['anagrafica'])
            return voce_dipendente
        
        # Crea nuova voce intestata
        voce_dipendente = TitolarioVoce.objects.create(
            codice=dipendente.codice,
            titolo=f"Dossier {dipendente.display_name()}",
            parent=voce_hr_pers,
            anagrafica=dipendente,
            pattern_codice='{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}',
            consente_intestazione=False,
        )
        
        logger.info(f"Creata voce titolario: {voce_dipendente.codice}")
        
        return voce_dipendente
    
    def _find_duplicate(self, dipendente: Anagrafica, anno_riferimento: int):
        """
        Cerca documento CU duplicato per stesso dipendente + anno.
        """
        try:
            attr_def_dipendente = AttributoDefinizione.objects.get(
                tipo_documento=self.tipo_cu,
                codice='dipendente'
            )
            attr_def_anno = AttributoDefinizione.objects.get(
                tipo_documento=self.tipo_cu,
                codice='anno_riferimento'
            )
            
            # Cerca documenti CU dello stesso anno
            documenti_anno = Documento.objects.filter(
                tipo=self.tipo_cu,
                data_documento__year=anno_riferimento
            ).prefetch_related('attributi_valori')
            
            for doc in documenti_anno:
                attributi = {av.definizione_id: av.valore for av in doc.attributi_valori.all()}
                
                # Match dipendente + anno
                if (attributi.get(attr_def_dipendente.id) == str(dipendente.id) and
                    attributi.get(attr_def_anno.id) == str(anno_riferimento)):
                    return doc
            
        except AttributoDefinizione.DoesNotExist:
            pass
        
        return None
    
    def _genera_descrizione(self, percipiente_data: Dict[str, Any], anno: int) -> str:
        """Genera descrizione documento CU"""
        cognome = percipiente_data.get('cognome', '').upper()
        nome = percipiente_data.get('nome', '').upper()
        return f"CU {anno} - {cognome} {nome}"
    
    def _salva_attributi(self, documento: Documento, cu_data: Dict[str, Any], dipendente: Anagrafica):
        """Salva attributi dinamici del documento CU"""
        attributi_def = {
            attr.codice: attr
            for attr in AttributoDefinizione.objects.filter(tipo_documento=self.tipo_cu)
        }
        
        valori_attributi = {
            'anno_riferimento': cu_data['anno_riferimento'],
            'dipendente': dipendente.id,
            'tipo_certificazione': cu_data.get('tipo_certificazione', ''),
            'redditi_lavoro_dipendente': cu_data.get('redditi_lavoro_dipendente', ''),
            'ritenute_irpef': cu_data.get('ritenute_irpef', ''),
            'addizionale_regionale': cu_data.get('addizionale_regionale', ''),
            'addizionale_comunale': cu_data.get('addizionale_comunale', ''),
            'contributi_previdenziali': cu_data.get('contributi_previdenziali', ''),
            'bonus_renzi': cu_data.get('bonus_renzi', ''),
        }
        
        for codice, valore in valori_attributi.items():
            if codice in attributi_def and valore:
                AttributoValore.objects.create(
                    documento=documento,
                    definizione=attributi_def[codice],
                    valore=str(valore)
                )
