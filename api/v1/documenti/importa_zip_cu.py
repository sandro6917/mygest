"""
Utility per importazione ZIP come documento Archivio Certificazioni Uniche (CU-ZIP)
"""
import logging
import os
import tempfile
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Any

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, Subquery, OuterRef
from django.utils import timezone

from documenti.models import Documento, DocumentiTipo, AttributoValore, AttributoDefinizione
from api.v1.ai_classifier.views_ai_import import ExtractionService
from anagrafiche.models import Anagrafica, Cliente
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


def _salva_attributi_cu_zip(
    documento: Documento,
    anno_imposta: int,
    datore_cliente_id: Optional[int],
    datore_cf: str,
    datore_denominazione: str,
    num_certificazioni: int,
    dipendenti_lista: List[str]
) -> Dict[str, Any]:
    """
    Salva gli attributi dinamici per il documento CU-ZIP.
    
    Args:
        documento: Il documento CU-ZIP creato
        anno_imposta: Anno fiscale di riferimento
        datore_cliente_id: ID del cliente datore di lavoro (FK)
        datore_cf: Codice Fiscale o P.IVA datore
        datore_denominazione: Ragione sociale datore
        num_certificazioni: Numero di certificazioni contenute
        dipendenti_lista: Lista nomi dipendenti
    
    Returns:
        Dict con mapping codice_attributo -> valore (per passare a build_document_filename)
    """
    # Mappa attributi: codice -> valore
    attributi_map = {
        'anno_imposta': anno_imposta,
        'datore': datore_cliente_id,
        'datore_cf': datore_cf,
        'datore_denominazione': datore_denominazione,
        'num_certificazioni': num_certificazioni,
        'dipendenti_lista': '\n'.join(dipendenti_lista) if dipendenti_lista else '',
    }
    
    # Salva ogni attributo se definito per il tipo documento
    for codice, valore in attributi_map.items():
        try:
            # Salta valori None
            if valore is None and codice != 'dipendenti_lista':
                continue
                
            # Cerca la definizione dell'attributo per il tipo CU-ZIP
            definizione = AttributoDefinizione.objects.filter(
                tipo_documento=documento.tipo,
                codice=codice
            ).first()
            
            if definizione:
                # Crea o aggiorna l'attributo
                AttributoValore.objects.update_or_create(
                    documento=documento,
                    definizione=definizione,
                    defaults={'valore': valore}
                )
                logger.debug(f"Attributo {codice}={valore} salvato per documento {documento.id}")
            else:
                logger.warning(
                    f"Definizione attributo '{codice}' non trovata per tipo documento CU-ZIP"
                )
        except Exception as e:
            logger.error(f"Errore salvando attributo {codice}: {e}", exc_info=True)
    
    # Restituisci la mappa degli attributi per build_document_filename
    logger.debug(
        f"_salva_attributi_cu_zip: documento {documento.id}, "
        f"attrs_map keys: {list(attributi_map.keys())}, anno_imposta: {anno_imposta}"
    )
    return attributi_map


@transaction.atomic
def importa_zip_come_cu(
    zip_file,
    azione_duplicati: str = 'duplica',
    user=None
) -> Dict:
    """
    Importa un file ZIP contenente certificazioni uniche come singolo documento CU-ZIP.
    
    Args:
        zip_file: File ZIP uploadato
        azione_duplicati: 'sostituisci', 'duplica' o 'skip'
        user: Utente che esegue l'importazione
    
    Returns:
        Dict con risultato: {
            'success': bool,
            'documento_id': int (se creato),
            'duplicato': bool,
            'duplicato_id': int (se esisteva),
            'azione': str ('creato', 'sostituito', 'skipped'),
            'metadati': {...},
            'errori': [...]
        }
    """
    temp_dir = None
    risultato = {
        'success': False,
        'documento_id': None,
        'duplicato': False,
        'duplicato_id': None,
        'azione': None,
        'metadati': {},
        'errori': []
    }
    
    try:
        # Crea directory temporanea
        temp_dir = tempfile.mkdtemp(prefix='cu_zip_')
        
        # Estrai solo il nome del file (basename) dal path dello storage
        zip_filename = os.path.basename(zip_file.name)
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # Salva ZIP temporaneamente
        with open(zip_path, 'wb') as f:
            # Se è un FieldFile di Django, usa .read() invece di .chunks()
            if hasattr(zip_file, 'chunks'):
                for chunk in zip_file.chunks():
                    f.write(chunk)
            else:
                # Per file già aperti o ContentFile
                zip_file.seek(0)
                f.write(zip_file.read())
        
        # Verifica che il file sia un ZIP valido
        if not zipfile.is_zipfile(zip_path):
            risultato['errori'].append(
                f"Il file {zip_file.name} non è un archivio ZIP valido. "
                f"Dimensione: {os.path.getsize(zip_path)} bytes"
            )
            return risultato
        
        # Estrai PDF dallo ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        pdf_paths = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
            # Lista PDF estratti
            for root, dirs, files in os.walk(extract_dir):
                for filename in files:
                    if filename.lower().endswith('.pdf'):
                        pdf_paths.append(os.path.join(root, filename))
        
        if not pdf_paths:
            risultato['errori'].append("Lo ZIP non contiene file PDF")
            return risultato
        
        logger.info(f"Trovati {len(pdf_paths)} PDF nello ZIP {zip_file.name}")
        
        # Verifica esistenza template AI 'CU' prima dell'estrazione
        from ai_classifier.models import DocumentExtractionTemplate
        try:
            template_cu = DocumentExtractionTemplate.objects.get(
                tipo_documento__codice='CU',
                attivo=True
            )
            logger.info(f"Template AI 'CU' caricato: {template_cu.nome}")
        except DocumentExtractionTemplate.DoesNotExist:
            risultato['errori'].append(
                "Template AI 'CU' non configurato o non attivo. "
                "Configurare il template nell'admin (/admin/ai_classifier/documentextractiontemplate/) "
                "prima di importare archivi CU."
            )
            return risultato
        
        # Parsa il PRIMO PDF per estrarre metadati usando AI extraction
        primo_pdf = pdf_paths[0]
        try:
            # Usa il template AI esistente per CU
            extraction_service = ExtractionService()
            parsed_data = extraction_service.extract_from_template(
                file_path=primo_pdf,
                template=template_cu  # Passa oggetto template invece di nome
            )
            
            if not parsed_data or 'campi_estratti' not in parsed_data:
                raise ValueError("Nessun dato estratto dal template AI CU")

            fields = {c['nome_campo']: c['valore'] for c in parsed_data['campi_estratti']}
            logger.info(f"Parsed primo PDF CU: fields={list(fields.keys())}")
            
        except Exception as e:
            logger.error(f"Errore parsing primo PDF con AI: {e}")
            risultato['errori'].append(
                f"Impossibile estrarre dati dal primo PDF: {str(e)}. "
                f"Verificare che il PDF sia una Certificazione Unica valida."
            )
            return risultato
        
        # Estrai info datore di lavoro dal template AI
        # Campi attesi: sostituto_cf, sostituto_denominazione, anno_imposta, dipendente_cf, dipendente_cognome, dipendente_nome
        datore_cf = fields.get('codice_fiscale_datore', '').strip()
        datore_denominazione = fields.get('denominazione_datore', 'Sconosciuto').strip()
        anno_imposta_str = fields.get('anno_imposta', '')
        
        if not datore_cf:
            risultato['errori'].append("Impossibile identificare il datore di lavoro (CF mancante)")
            return risultato
        
        # Converti anno_imposta in int
        try:
            anno_imposta = int(anno_imposta_str) if anno_imposta_str else datetime.now().year - 1
        except (ValueError, TypeError):
            anno_imposta = datetime.now().year - 1
            logger.warning(f"Anno imposta non valido '{anno_imposta_str}', uso default {anno_imposta}")
        
        # Cerca anagrafica datore di lavoro
        datore_anagrafica = Anagrafica.objects.filter(
            Q(codice_fiscale=datore_cf) | Q(partita_iva=datore_cf)
        ).first()

        # Fallback: CF persona fisica (16 char) potrebbe essere estratto parzialmente
        # dal bbox del template (ottimizzato per P.IVA a 11 cifre).
        # Se il valore estratto è < 16 char e contiene lettere, prova startswith.
        if not datore_anagrafica and datore_cf and len(datore_cf) < 16 and not datore_cf.isdigit():
            datore_anagrafica = Anagrafica.objects.filter(
                Q(codice_fiscale__istartswith=datore_cf) | Q(partita_iva__istartswith=datore_cf)
            ).first()
            if datore_anagrafica:
                logger.info(
                    f"Anagrafica trovata per CF parziale '{datore_cf}' "
                    f"→ CF completo '{datore_anagrafica.codice_fiscale or datore_anagrafica.partita_iva}'"
                )
                datore_cf = datore_anagrafica.codice_fiscale or datore_anagrafica.partita_iva or datore_cf

        if not datore_anagrafica:
            risultato['errori'].append(
                f"Datore di lavoro con CF {datore_cf} non trovato in anagrafica. "
                f"Creare l'anagrafica prima di importare lo ZIP CU."
            )
            return risultato
        
        # Cerca/crea cliente
        cliente_datore, created = Cliente.objects.get_or_create(
            anagrafica=datore_anagrafica,
            defaults={'note': 'Creato automaticamente da importazione Archivio CU'}
        )
        
        if created:
            logger.info(f"Creato nuovo cliente per datore: {datore_denominazione}")
        
        # Data documento = 31 marzo dell'anno successivo (scadenza invio CU)
        data_documento = datetime(anno_imposta + 1, 3, 31).date()
        
        # Scansiona tutti i PDF per elenco dipendenti
        dipendenti_nomi = []
        for pdf_path in pdf_paths:
            try:
                parsed_dip = extraction_service.extract_from_template(
                    file_path=pdf_path,
                    template=template_cu  # Usa oggetto template già validato
                )
                
                if parsed_dip and 'campi_estratti' in parsed_dip:
                    fields_dip = {c['nome_campo']: c['valore'] for c in parsed_dip['campi_estratti']}
                    cognome = fields_dip.get('cognome_lavoratore', '').strip()
                    nome = fields_dip.get('nome_lavoratore', '').strip()
                    nome_completo = f"{cognome} {nome}".strip()
                    if nome_completo and nome_completo not in dipendenti_nomi:
                        dipendenti_nomi.append(nome_completo)
            except Exception as e:
                logger.warning(f"Errore parsing PDF {os.path.basename(pdf_path)}: {e}")
                continue
        
        dipendenti_nomi.sort()
        
        # Genera note
        note = f"Contiene {len(pdf_paths)} certificazioni uniche anno {anno_imposta}\n\nDipendenti:\n"
        note += "\n".join([f"- {nome}" for nome in dipendenti_nomi])
        
        # Genera titolo
        titolo = f"Archivio CU {anno_imposta} - {datore_denominazione}"
        
        # Cerca tipo documento CU-ZIP
        try:
            tipo_cu_zip = DocumentiTipo.objects.get(codice='CU-ZIP')
        except DocumentiTipo.DoesNotExist:
            risultato['errori'].append(
                "Tipo documento CU-ZIP non configurato. Eseguire: python manage.py setup_cu_zip"
            )
            return risultato
        
        # Cerca titolario HR-CU
        titolario_cu = TitolarioVoce.objects.filter(codice='HR-CU').first()
        
        if not titolario_cu:
            risultato['errori'].append("Titolario HR-CU non trovato. Eseguire: python manage.py setup_cu")
            return risultato
        
        # Controlla duplicati: stesso cliente + anno_imposta + tipo CU-ZIP
        # Usa Subquery per filtrare documenti con attributo anno_imposta corrispondente
        documenti_con_anno = AttributoValore.objects.filter(
            documento=OuterRef('pk'),
            definizione__codice='anno_imposta',
            definizione__tipo_documento=tipo_cu_zip,
            valore=anno_imposta
        )
        
        documento_esistente = Documento.objects.filter(
            cliente=cliente_datore,
            tipo=tipo_cu_zip
        ).annotate(
            has_anno=Subquery(documenti_con_anno.values('id')[:1])
        ).filter(
            has_anno__isnull=False
        ).first()
        
        if documento_esistente:
            risultato['duplicato'] = True
            risultato['duplicato_id'] = documento_esistente.id
            
            if azione_duplicati == 'skip':
                risultato['azione'] = 'skipped'
                logger.info(f"Skipped: documento CU-ZIP già esiste (ID {documento_esistente.id})")
                return risultato
            
            elif azione_duplicati == 'sostituisci':
                # Elimina il vecchio file se presente
                if documento_esistente.file:
                    try:
                        documento_esistente.file.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Impossibile eliminare vecchio file: {e}")
                
                # Aggiorna documento esistente
                documento_esistente.descrizione = titolo
                documento_esistente.data_documento = data_documento
                documento_esistente.titolario_voce = titolario_cu
                documento_esistente.fascicolo = None
                documento_esistente.note = note
                documento_esistente.digitale = True
                documento_esistente.tracciabile = True
                
                # Salva attributi dinamici PRIMA di allegare il file
                attrs_map = _salva_attributi_cu_zip(
                    documento=documento_esistente,
                    anno_imposta=anno_imposta,
                    datore_cliente_id=cliente_datore.id,
                    datore_cf=datore_cf,
                    datore_denominazione=datore_denominazione,
                    num_certificazioni=len(pdf_paths),
                    dipendenti_lista=dipendenti_nomi
                )
                
                # Imposta flag per saltare rename automatico durante file.save()
                documento_esistente._skip_auto_rename = True

                # Riallega ZIP
                with open(zip_path, 'rb') as f:
                    documento_esistente.file.save(
                        zip_file.name,
                        ContentFile(f.read()),
                        save=True
                    )
                
                # Applica rename con attributi dopo aver allegato il file
                logger.info(
                    f"applica_rename_con_attributi (sostituzione): documento {documento_esistente.id}, "
                    f"attrs_map: {attrs_map}"
                )
                documento_esistente.applica_rename_con_attributi(attrs=attrs_map)
                
                risultato['success'] = True
                risultato['documento_id'] = documento_esistente.id
                risultato['azione'] = 'sostituito'
                risultato['metadati'] = {
                    'titolo': titolo,
                    'anno_imposta': anno_imposta,
                    'datore': datore_denominazione,
                    'datore_cf': datore_cf,
                    'num_certificazioni': len(pdf_paths),
                    'dipendenti': dipendenti_nomi
                }
                
                logger.info(f"Sostituito documento CU-ZIP esistente ID {documento_esistente.id}")
                return risultato
        
        # Crea nuovo documento CU-ZIP (duplica o nuovo)
        nuovo_documento = Documento(
            tipo=tipo_cu_zip,
            cliente=cliente_datore,
            titolario_voce=titolario_cu,
            fascicolo=None,
            descrizione=titolo,
            data_documento=data_documento,
            note=note,
            digitale=True,
            tracciabile=True
        )
        
        # IMPORTANTE: Salva il documento PRIMA di allegare il file
        # per poter creare gli AttributoValore (richiedono documento.id)
        nuovo_documento.save()
        
        # Salva attributi dinamici PRIMA di allegare il file
        attrs_map = _salva_attributi_cu_zip(
            documento=nuovo_documento,
            anno_imposta=anno_imposta,
            datore_cliente_id=cliente_datore.id,
            datore_cf=datore_cf,
            datore_denominazione=datore_denominazione,
            num_certificazioni=len(pdf_paths),
            dipendenti_lista=dipendenti_nomi
        )
        
        # Imposta flag per saltare rename automatico durante file.save()
        nuovo_documento._skip_auto_rename = True

        # Allega ZIP
        with open(zip_path, 'rb') as f:
            nuovo_documento.file.save(
                zip_file.name,
                ContentFile(f.read()),
                save=True
            )
        
        # Ora applica il rename con gli attributi disponibili
        logger.info(
            f"applica_rename_con_attributi: documento {nuovo_documento.id}, "
            f"attrs_map: {attrs_map}"
        )
        nuovo_documento.applica_rename_con_attributi(attrs=attrs_map)
        
        risultato['success'] = True
        risultato['documento_id'] = nuovo_documento.id
        risultato['azione'] = 'duplicato' if documento_esistente else 'creato'
        risultato['metadati'] = {
            'titolo': titolo,
            'anno_imposta': anno_imposta,
            'datore': datore_denominazione,
            'datore_cf': datore_cf,
            'num_certificazioni': len(pdf_paths),
            'dipendenti': dipendenti_nomi
        }
        
        logger.info(f"Creato documento CU-ZIP ID {nuovo_documento.id}: {titolo}")
        
        return risultato
        
    except Exception as e:
        logger.error(f"Errore importazione ZIP CU: {e}", exc_info=True)
        risultato['errori'].append(f"Errore: {str(e)}")
        return risultato
    
    finally:
        # Cleanup directory temporanea
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Impossibile eliminare directory temporanea {temp_dir}: {e}")
