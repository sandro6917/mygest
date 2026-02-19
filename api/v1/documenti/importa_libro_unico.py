"""
Utility per importazione ZIP come documento Libro Unico
"""
import logging
import os
import tempfile
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from documenti.models import Documento, DocumentiTipo, AttributoValore, AttributoDefinizione
from documenti.parsers.cedolino_parser import parse_cedolino_pdf
from anagrafiche.models import Anagrafica, Cliente
from titolario.models import TitolarioVoce

logger = logging.getLogger(__name__)


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
        
        # Salva ZIP temporaneamente
        zip_path = os.path.join(temp_dir, zip_file.name)
        with open(zip_path, 'wb') as f:
            for chunk in zip_file.chunks():
                f.write(chunk)
        
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
        
        # Cerca titolario HR-PAY/PAG
        titolario_hrpay = TitolarioVoce.objects.filter(
            Q(codice='HR-PAY') | Q(codice='HRPAY') | Q(codice__icontains='PAY')
        ).first()
        
        if not titolario_hrpay:
            # Fallback: cerca HR-PAY con parent
            titolario_hrpay = TitolarioVoce.objects.filter(
                codice__icontains='HR'
            ).filter(
                Q(titolo__icontains='PAY') | Q(titolo__icontains='PAGA')
            ).first()
        
        if not titolario_hrpay:
            risultato['errori'].append("Titolario HR-PAY non trovato")
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
                documento_esistente.titolario_voce = titolario_hrpay
                documento_esistente.fascicolo = None
                documento_esistente.note = note
                documento_esistente.digitale = True
                documento_esistente.tracciabile = True
                
                # Riallega ZIP
                with open(zip_path, 'rb') as f:
                    documento_esistente.file.save(
                        zip_file.name,
                        ContentFile(f.read()),
                        save=False
                    )
                
                documento_esistente.save()
                
                risultato['success'] = True
                risultato['documento_id'] = documento_esistente.id
                risultato['azione'] = 'sostituito'
                
                logger.info(f"Sostituito documento LIBUNI esistente ID {documento_esistente.id}")
                return risultato
        
        # Crea nuovo documento LIBUNI (duplica o nuovo)
        nuovo_documento = Documento(
            tipo=tipo_libuni,
            cliente=cliente_datore,
            titolario_voce=titolario_hrpay,
            fascicolo=None,
            descrizione=titolo,
            data_documento=data_documento,
            note=note,
            digitale=True,
            tracciabile=True
        )
        
        # Allega ZIP
        with open(zip_path, 'rb') as f:
            nuovo_documento.file.save(
                zip_file.name,
                ContentFile(f.read()),
                save=False
            )
        
        nuovo_documento.save()
        
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
