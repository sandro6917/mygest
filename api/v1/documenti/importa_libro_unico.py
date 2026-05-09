"""
Utility per importazione ZIP come documento Libro Unico
"""
import logging
import os
import tempfile
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from documenti.models import Documento, DocumentiTipo, AttributoValore, AttributoDefinizione
from documenti.parsers.cedolino_parser import parse_cedolino_pdf
from anagrafiche.models import Anagrafica, Cliente
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


def _salva_attributi_libro_unico(documento: Documento, periodo: str, anno: int, mese: int, num_cedolini: int) -> Dict[str, Any]:
    """
    Salva gli attributi dinamici per il documento Libro Unico.
    
    Args:
        documento: Il documento LIBUNI creato
        periodo: Periodo in formato testo (es: "Aprile 2025")
        anno: Anno di riferimento
        mese: Mese di riferimento (1-12)
        num_cedolini: Numero di cedolini contenuti
    
    Returns:
        Dict con mapping codice_attributo -> valore (per passare a build_document_filename)
    """
    # Mappa attributi: codice -> valore
    # NOTA: 'anno' e 'mese' sono int perché usati nel pattern template con formati numerici
    attributi_map = {
        'periodo': periodo,
        'anno': anno,  # ✅ Mantieni come int per formattazione
        'mese': mese,  # ✅ Mantieni come int per formattazione
        'mensilita': mese,  # ✅ AGGIUNTO: stesso valore di mese (usato nel pattern template)
        'num_cedolini': num_cedolini,  # ✅ Mantieni come int
    }
    
    # Salva ogni attributo se definito per il tipo documento
    for codice, valore in attributi_map.items():
        try:
            # Cerca la definizione dell'attributo per il tipo LIBUNI
            definizione = AttributoDefinizione.objects.filter(
                tipo_documento=documento.tipo,
                codice=codice
            ).first()
            
            if definizione:
                # Crea o aggiorna l'attributo
                # NOTA: valore rimane nel tipo originale (int/str) perché JSONField preserva i tipi
                AttributoValore.objects.update_or_create(
                    documento=documento,
                    definizione=definizione,
                    defaults={'valore': valore}  # ✅ Preserva tipo nativo per pattern template
                )
                logger.debug(f"Attributo {codice}={valore} salvato per documento {documento.id}")
            else:
                logger.warning(
                    f"Definizione attributo '{codice}' non trovata per tipo documento LIBUNI"
                )
        except Exception as e:
            logger.error(f"Errore salvando attributo {codice}: {e}", exc_info=True)
    
    # ✅ Restituisci la mappa degli attributi per build_document_filename
    logger.debug(
        f"_salva_attributi_libro_unico: documento {documento.id}, "
        f"attrs_map keys: {list(attributi_map.keys())}, values: {attributi_map}"
    )
    return attributi_map


def importa_zip_come_libro_unico(
    zip_file,
    azione_duplicati: str = 'duplica',
    user=None
) -> Dict:
    """
    Importa un file ZIP contenente cedolini come singolo documento LIBUNI.
    
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
        temp_dir = tempfile.mkdtemp(prefix='libro_unico_')
        
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
        
        # Parsa il PRIMO PDF per estrarre metadati
        primo_pdf = pdf_paths[0]
        try:
            parsed = parse_cedolino_pdf(primo_pdf)
            logger.info(f"Parsed primo PDF: periodo={parsed['cedolino'].get('periodo')}, azienda={parsed['datore'].get('ragione_sociale')}")
        except Exception as e:
            logger.error(f"Errore parsing primo PDF: {e}")
            risultato['errori'].append(f"Impossibile estrarre dati dal primo PDF: {str(e)}")
            return risultato
        
        # Estrai info azienda (datore di lavoro)
        datore_cf = parsed['datore'].get('codice_fiscale')
        datore_ragione_sociale = parsed['datore'].get('ragione_sociale', 'Sconosciuto')
        
        if not datore_cf:
            risultato['errori'].append("Impossibile identificare il datore di lavoro (CF mancante)")
            return risultato
        
        # Cerca/crea anagrafica datore di lavoro
        datore_anagrafica = Anagrafica.objects.filter(
            Q(codice_fiscale=datore_cf) | Q(partita_iva=datore_cf)
        ).first()
        
        if not datore_anagrafica:
            risultato['errori'].append(f"Datore di lavoro con CF {datore_cf} non trovato in anagrafica")
            return risultato
        
        # Cerca/crea cliente
        cliente_datore, created = Cliente.objects.get_or_create(
            anagrafica=datore_anagrafica,
            defaults={'note': 'Creato automaticamente da importazione Libro Unico'}
        )
        
        if created:
            logger.info(f"Creato nuovo cliente per datore: {datore_ragione_sociale}")
        
        # Estrai periodo
        periodo_str = parsed['cedolino'].get('periodo')  # es: "Aprile 2025"
        anno = parsed['cedolino'].get('anno')
        mese = parsed['cedolino'].get('mese')
        
        if not periodo_str or not anno or not mese:
            risultato['errori'].append("Impossibile determinare il periodo di riferimento")
            return risultato
        
        # Data documento = primo giorno del mese di riferimento
        data_documento = datetime(anno, mese, 1).date()
        
        # Scansiona tutti i PDF per elenco dipendenti
        dipendenti_nomi = []
        for pdf_path in pdf_paths:
            try:
                parsed_dip = parse_cedolino_pdf(pdf_path)
                nome_dip = parsed_dip['lavoratore'].get('nome', 'Sconosciuto')
                cognome_dip = parsed_dip['lavoratore'].get('cognome', '')
                nome_completo = f"{cognome_dip} {nome_dip}".strip()
                if nome_completo and nome_completo not in dipendenti_nomi:
                    dipendenti_nomi.append(nome_completo)
            except Exception as e:
                logger.warning(f"Errore parsing PDF {os.path.basename(pdf_path)}: {e}")
                continue
        
        dipendenti_nomi.sort()
        
        # Genera note
        note = f"Contiene {len(pdf_paths)} cedolini\n\nDipendenti:\n"
        note += "\n".join([f"- {nome}" for nome in dipendenti_nomi])
        
        # Genera titolo
        titolo = f"Libro Unico {periodo_str} - {datore_ragione_sociale}"
        
        # Cerca tipo documento LIBUNI
        try:
            tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
        except DocumentiTipo.DoesNotExist:
            risultato['errori'].append("Tipo documento LIBUNI non configurato nel sistema")
            return risultato
        
        # Cerca titolario LIBUNI
        titolario_libuni = TitolarioVoce.objects.filter(
            codice='LIBUNI'
        ).first()
        
        if not titolario_libuni:
            risultato['errori'].append("Titolario LIBUNI non trovato")
            return risultato
        
        # Controlla duplicati: stesso cliente + periodo + tipo LIBUNI
        documento_esistente = Documento.objects.filter(
            cliente=cliente_datore,
            tipo=tipo_libuni,
            data_documento__year=anno,
            data_documento__month=mese
        ).first()
        
        if documento_esistente:
            risultato['duplicato'] = True
            risultato['duplicato_id'] = documento_esistente.id
            
            if azione_duplicati == 'skip':
                risultato['azione'] = 'skipped'
                logger.info(f"Skipped: documento LIBUNI già esiste (ID {documento_esistente.id})")
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
                documento_esistente.titolario_voce = titolario_libuni
                documento_esistente.fascicolo = None
                documento_esistente.note = note
                documento_esistente.digitale = True
                documento_esistente.tracciabile = True
                
                # ✅ Salva attributi dinamici PRIMA di allegare il file
                attrs_map = _salva_attributi_libro_unico(
                    documento=documento_esistente,
                    periodo=periodo_str,
                    anno=anno,
                    mese=mese,
                    num_cedolini=len(pdf_paths)
                )
                
                # ✅ Imposta flag per saltare rename automatico durante file.save()
                documento_esistente._skip_auto_rename = True
                
                # Riallega ZIP
                with open(zip_path, 'rb') as f:
                    documento_esistente.file.save(
                        zip_file.name,
                        ContentFile(f.read()),
                        save=True  # ✅ save=True per salvare il file
                    )
                
                # ✅ Applica rename con attributi dopo aver allegato il file
                logger.info(
                    f"applica_rename_con_attributi (sostituzione): documento {documento_esistente.id}, "
                    f"attrs_map: {attrs_map}"
                )
                documento_esistente.applica_rename_con_attributi(attrs=attrs_map)
                
                risultato['success'] = True
                risultato['documento_id'] = documento_esistente.id
                risultato['azione'] = 'sostituito'
                
                logger.info(f"Sostituito documento LIBUNI esistente ID {documento_esistente.id}")
                return risultato
        
        # Crea nuovo documento LIBUNI (duplica o nuovo)
        nuovo_documento = Documento(
            tipo=tipo_libuni,
            cliente=cliente_datore,
            titolario_voce=titolario_libuni,
            fascicolo=None,
            descrizione=titolo,
            data_documento=data_documento,
            note=note,
            digitale=True,
            tracciabile=True
        )
        
        # ✅ IMPORTANTE: Salva il documento PRIMA di allegare il file
        # per poter creare gli AttributoValore (richiedono documento.id)
        nuovo_documento.save()
        
        # ✅ Salva attributi dinamici PRIMA di allegare il file
        # Così il sistema di naming dei file potrà usare gli attributi
        attrs_map = _salva_attributi_libro_unico(
            documento=nuovo_documento,
            periodo=periodo_str,
            anno=anno,
            mese=mese,
            num_cedolini=len(pdf_paths)
        )
        
        # ✅ Imposta flag per saltare rename automatico durante file.save()
        nuovo_documento._skip_auto_rename = True
        
        # Allega ZIP
        with open(zip_path, 'rb') as f:
            nuovo_documento.file.save(
                zip_file.name,
                ContentFile(f.read()),
                save=True  # ✅ save=True per salvare il file
            )
        
        # ✅ Ora applica il rename con gli attributi disponibili
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
            'periodo': periodo_str,
            'anno': anno,
            'mese': mese,
            'cliente': datore_ragione_sociale,
            'num_cedolini': len(pdf_paths),
            'dipendenti': dipendenti_nomi
        }
        
        logger.info(f"Creato documento LIBUNI ID {nuovo_documento.id}: {titolo}")
        
        return risultato
        
    except Exception as e:
        logger.error(f"Errore importazione ZIP libro unico: {e}", exc_info=True)
        risultato['errori'].append(f"Errore: {str(e)}")
        return risultato
    
    finally:
        # Cleanup directory temporanea
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Impossibile eliminare directory temporanea {temp_dir}: {e}")
