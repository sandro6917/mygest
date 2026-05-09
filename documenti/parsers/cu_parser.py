"""
Parser per Certificazioni Uniche (CU).

Estrae dati strutturati da PDF CU per l'importazione automatica nel sistema.
"""
from __future__ import annotations
import re
import logging
from typing import TypedDict, Optional, Dict, Any
from datetime import date
import pdfplumber

logger = logging.getLogger(__name__)


class SostitutoData(TypedDict):
    """Dati estratti del sostituto d'imposta (datore di lavoro)"""
    codice_fiscale: str
    denominazione: Optional[str]
    partita_iva: Optional[str]
    comune: Optional[str]
    provincia: Optional[str]
    indirizzo: Optional[str]
    cap: Optional[str]


class PercepieteData(TypedDict):
    """Dati estratti del percipiente (lavoratore dipendente)"""
    codice_fiscale: str
    cognome: str
    nome: str
    data_nascita: Optional[str]
    comune_nascita: Optional[str]
    provincia_nascita: Optional[str]
    comune_residenza: Optional[str]
    provincia_residenza: Optional[str]
    indirizzo_residenza: Optional[str]
    cap_residenza: Optional[str]


class CUData(TypedDict):
    """Dati fiscali estratti dalla CU"""
    anno_riferimento: int  # Anno fiscale (es. 2024)
    tipo_certificazione: Optional[str]  # Es. "Ordinaria", "Soggetto estero", etc.
    redditi_lavoro_dipendente: Optional[str]  # Punto 1 - Redditi lavoro dipendente
    ritenute_irpef: Optional[str]  # Punto 4 - Ritenute IRPEF
    addizionale_regionale: Optional[str]  # Punto 5 - Addizionale regionale
    addizionale_comunale: Optional[str]  # Punto 6 - Addizionale comunale
    contributi_previdenziali: Optional[str]  # Contributi a carico dipendente
    bonus_renzi: Optional[str]  # Eventuale bonus Renzi/IRPEF


class CUParseResult(TypedDict):
    """Risultato completo del parsing CU"""
    sostituto: SostitutoData
    percipiente: PercepieteData
    cu: CUData


def parse_cu_pdf(pdf_path: str) -> CUParseResult:
    """
    Estrae dati strutturati da un PDF Certificazione Unica.
    
    Args:
        pdf_path: Percorso del file PDF da analizzare
        
    Returns:
        Dizionario con dati di sostituto, percipiente e CU
        
    Raises:
        ValueError: Se il PDF non è una CU valida o dati essenziali mancanti
        FileNotFoundError: Se il file non esiste
    """
    import os
    filename = os.path.basename(pdf_path)
    
    logger.info(f"Parsing CU: {filename}")
    
    # Estrai testo da PDF
    raw_text = extract_text_from_pdf(pdf_path)
    
    # Estrai dati strutturati
    sostituto_data = extract_sostituto_data(raw_text)
    percipiente_data = extract_percipiente_data(raw_text)
    cu_data = extract_cu_data(raw_text, filename)
    
    # Validazione dati essenziali
    if not sostituto_data.get('codice_fiscale'):
        raise ValueError(f"Codice fiscale sostituto d'imposta non trovato in: {filename}")
    
    if not percipiente_data.get('codice_fiscale'):
        raise ValueError(f"Codice fiscale percipiente non trovato in: {filename}")
    
    if not cu_data.get('anno_riferimento'):
        raise ValueError(f"Anno di riferimento non trovato in: {filename}")
    
    result: CUParseResult = {
        'sostituto': sostituto_data,
        'percipiente': percipiente_data,
        'cu': cu_data,
    }
    
    logger.info(
        f"CU parsata con successo: {percipiente_data['cognome']} {percipiente_data['nome']} - "
        f"Anno {cu_data['anno_riferimento']}"
    )
    
    return result


def extract_text_from_pdf(pdf_path: str) -> str:
    """Estrae tutto il testo dal PDF"""
    text_parts = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or '')
    except Exception as e:
        logger.error(f"Errore estrazione testo PDF: {e}")
        raise ValueError(f"Impossibile leggere il PDF: {e}")
    
    return '\n'.join(text_parts)


def extract_sostituto_data(text: str) -> SostitutoData:
    """
    Estrae dati del sostituto d'imposta (datore di lavoro) dal testo della CU.
    
    Pattern comuni:
    - "Codice fiscale" seguito da CF
    - "Denominazione" o "Ragione sociale"
    - "Partita IVA"
    - Sezione "DATI RELATIVI AL SOSTITUTO D'IMPOSTA"
    """
    sostituto: SostitutoData = {
        'codice_fiscale': '',
        'denominazione': None,
        'partita_iva': None,
        'comune': None,
        'provincia': None,
        'indirizzo': None,
        'cap': None,
    }
    
    lines = text.split('\n')
    
    # Cerca sezione sostituto
    in_sostituto_section = False
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        line_upper = line_clean.upper()
        
        # Individua sezione sostituto
        if 'SOSTITUTO' in line_upper and "IMPOSTA" in line_upper:
            in_sostituto_section = True
            continue
        
        # Fine sezione sostituto (inizia sezione percipiente)
        if 'PERCIPIENTE' in line_upper or 'DATI ANAGRAFICI' in line_upper:
            in_sostituto_section = False
        
        if in_sostituto_section or not sostituto['codice_fiscale']:
            # Codice fiscale (11 o 16 caratteri alfanumerici)
            cf_match = re.search(
                r'\b([A-Z0-9]{11}|[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\b',
                line_upper
            )
            if cf_match and not sostituto['codice_fiscale']:
                candidate_cf = cf_match.group(1)
                # Valida: P.IVA (11 cifre) o CF (16 alfanumerici)
                if len(candidate_cf) == 11 and candidate_cf.isdigit():
                    sostituto['codice_fiscale'] = candidate_cf
                    sostituto['partita_iva'] = candidate_cf
                elif len(candidate_cf) == 16:
                    sostituto['codice_fiscale'] = candidate_cf
            
            # Denominazione/Ragione sociale
            if any(keyword in line_upper for keyword in ['DENOMINAZIONE', 'RAGIONE SOCIALE']) and i + 1 < len(lines):
                # Prendi riga successiva come denominazione
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) > 3:
                    sostituto['denominazione'] = next_line
            
            # Partita IVA (se separata da CF)
            if 'PARTITA IVA' in line_upper or 'P.IVA' in line_upper:
                piva_match = re.search(r'\b(\d{11})\b', line)
                if piva_match:
                    sostituto['partita_iva'] = piva_match.group(1)
            
            # Indirizzo
            if 'VIA' in line_upper or 'PIAZZA' in line_upper or 'VIALE' in line_upper:
                if not sostituto['indirizzo'] and len(line_clean) > 5:
                    sostituto['indirizzo'] = line_clean
            
            # CAP
            cap_match = re.search(r'\b(\d{5})\b', line)
            if cap_match and not sostituto['cap']:
                sostituto['cap'] = cap_match.group(1)
            
            # Comune e Provincia
            provincia_match = re.search(r'\(([A-Z]{2})\)', line)
            if provincia_match and not sostituto['provincia']:
                sostituto['provincia'] = provincia_match.group(1)
                # Comune è probabilmente prima della sigla provincia
                comune_match = re.search(r'\b([A-Z][A-Z\s]+)\s*\([A-Z]{2}\)', line_upper)
                if comune_match:
                    sostituto['comune'] = comune_match.group(1).strip().title()
    
    return sostituto


def extract_percipiente_data(text: str) -> PercepieteData:
    """
    Estrae dati del percipiente (dipendente) dal testo della CU.
    
    Pattern comuni:
    - "Codice fiscale" del dipendente
    - "Cognome" e "Nome"
    - "Data di nascita"
    - "Comune" e "Provincia" di nascita
    - Residenza
    """
    percipiente: PercepieteData = {
        'codice_fiscale': '',
        'cognome': '',
        'nome': '',
        'data_nascita': None,
        'comune_nascita': None,
        'provincia_nascita': None,
        'comune_residenza': None,
        'provincia_residenza': None,
        'indirizzo_residenza': None,
        'cap_residenza': None,
    }
    
    lines = text.split('\n')
    
    # Cerca sezione percipiente
    in_percipiente_section = False
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        line_upper = line_clean.upper()
        
        # Individua sezione percipiente
        if 'PERCIPIENTE' in line_upper or ('DATI ANAGRAFICI' in line_upper and 'SOSTITUTO' not in line_upper):
            in_percipiente_section = True
            continue
        
        # Fine sezione (inizia dati certificazione)
        if 'CERTIFICAZIONE' in line_upper and 'UNICA' in line_upper:
            in_percipiente_section = False
        
        if in_percipiente_section or not percipiente['codice_fiscale']:
            # Codice fiscale dipendente (16 caratteri)
            cf_match = re.search(r'\b([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\b', line_upper)
            if cf_match and not percipiente['codice_fiscale']:
                percipiente['codice_fiscale'] = cf_match.group(1)
            
            # Cognome
            if 'COGNOME' in line_upper and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) > 1:
                    percipiente['cognome'] = next_line.title()
            
            # Nome
            if 'NOME' in line_upper and 'COGNOME' not in line_upper and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) > 1:
                    percipiente['nome'] = next_line.title()
            
            # Data di nascita (pattern DD/MM/YYYY o DD-MM-YYYY)
            data_nascita_match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', line)
            if data_nascita_match and not percipiente['data_nascita']:
                percipiente['data_nascita'] = data_nascita_match.group(1)
            
            # Comune di nascita
            if 'NATO' in line_upper or 'NASCITA' in line_upper:
                comune_match = re.search(r'\b([A-Z][A-Z\s]+)\s*\(([A-Z]{2})\)', line_upper)
                if comune_match:
                    percipiente['comune_nascita'] = comune_match.group(1).strip().title()
                    percipiente['provincia_nascita'] = comune_match.group(2)
            
            # Residenza
            if 'RESIDENZA' in line_upper:
                # Comune e provincia residenza
                comune_res_match = re.search(r'\b([A-Z][A-Z\s]+)\s*\(([A-Z]{2})\)', line_upper)
                if comune_res_match:
                    percipiente['comune_residenza'] = comune_res_match.group(1).strip().title()
                    percipiente['provincia_residenza'] = comune_res_match.group(2)
                
                # Indirizzo residenza (riga successiva)
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if 'VIA' in next_line.upper() or 'PIAZZA' in next_line.upper():
                        percipiente['indirizzo_residenza'] = next_line
                
                # CAP residenza
                cap_res_match = re.search(r'\b(\d{5})\b', line)
                if cap_res_match:
                    percipiente['cap_residenza'] = cap_res_match.group(1)
    
    return percipiente


def extract_cu_data(text: str, filename: str) -> CUData:
    """
    Estrae dati fiscali dalla CU.
    
    Pattern comuni:
    - Anno di riferimento (da filename o testo)
    - Tipo certificazione
    - Punto 1: Redditi da lavoro dipendente
    - Punto 4: Ritenute IRPEF
    - Punto 5/6: Addizionali regionali/comunali
    """
    cu: CUData = {
        'anno_riferimento': 0,
        'tipo_certificazione': None,
        'redditi_lavoro_dipendente': None,
        'ritenute_irpef': None,
        'addizionale_regionale': None,
        'addizionale_comunale': None,
        'contributi_previdenziali': None,
        'bonus_renzi': None,
    }
    
    # Anno di riferimento (priorità: filename > testo)
    anno_match_filename = re.search(r'20\d{2}', filename)
    if anno_match_filename:
        cu['anno_riferimento'] = int(anno_match_filename.group(0))
    else:
        # Cerca nel testo: pattern "Anno YYYY" o "20XX"
        anno_match_text = re.search(r'\b(20\d{2})\b', text)
        if anno_match_text:
            cu['anno_riferimento'] = int(anno_match_text.group(1))
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        line_upper = line_clean.upper()
        
        # Tipo certificazione
        if 'TIPO CERTI' in line_upper or 'TIPO RAPPORTO' in line_upper:
            if i + 1 < len(lines):
                tipo = lines[i + 1].strip()
                if tipo and len(tipo) > 2:
                    cu['tipo_certificazione'] = tipo
        
        # Redditi lavoro dipendente (Punto 1)
        if 'PUNTO 1' in line_upper or 'REDDITI' in line_upper and 'LAVORO' in line_upper:
            # Cerca importo numerico nella stessa riga o successiva
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['redditi_lavoro_dipendente'] = importo_match.group(1)
            elif i + 1 < len(lines):
                importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', lines[i + 1])
                if importo_match:
                    cu['redditi_lavoro_dipendente'] = importo_match.group(1)
        
        # Ritenute IRPEF (Punto 4)
        if 'PUNTO 4' in line_upper or ('RITENUTE' in line_upper and 'IRPEF' in line_upper):
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['ritenute_irpef'] = importo_match.group(1)
            elif i + 1 < len(lines):
                importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', lines[i + 1])
                if importo_match:
                    cu['ritenute_irpef'] = importo_match.group(1)
        
        # Addizionale regionale (Punto 5)
        if 'PUNTO 5' in line_upper or 'ADDIZIONALE REGIONALE' in line_upper:
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['addizionale_regionale'] = importo_match.group(1)
        
        # Addizionale comunale (Punto 6)
        if 'PUNTO 6' in line_upper or 'ADDIZIONALE COMUNALE' in line_upper:
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['addizionale_comunale'] = importo_match.group(1)
        
        # Contributi previdenziali
        if 'CONTRIBUTI' in line_upper and 'PREVIDENZIALI' in line_upper:
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['contributi_previdenziali'] = importo_match.group(1)
        
        # Bonus Renzi/IRPEF
        if 'BONUS' in line_upper or 'TRATTAMENTO INTEGRATIVO' in line_upper:
            importo_match = re.search(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\b', line)
            if importo_match:
                cu['bonus_renzi'] = importo_match.group(1)
    
    return cu


def parse_filename_cu(filename: str) -> Optional[Dict[str, str]]:
    """
    Prova a estrarre dati dal nome file CU.
    
    Pattern comuni:
    - CU_2024_RSSMRA80A01H501U.pdf
    - CU_ROSSI_MARIO_2024.pdf
    - 2024_CU_RSSMRA80A01H501U.pdf
    
    Returns:
        Dict con 'anno' e 'codice_fiscale' se parsato, altrimenti None
    """
    # Pattern 1: CU_ANNO_CF.pdf
    match = re.match(r'CU[_-]?(20\d{2})[_-]?([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', filename, re.IGNORECASE)
    if match:
        return {
            'anno': match.group(1),
            'codice_fiscale': match.group(2).upper(),
        }
    
    # Pattern 2: ANNO_CU_CF.pdf
    match = re.match(r'(20\d{2})[_-]?CU[_-]?([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', filename, re.IGNORECASE)
    if match:
        return {
            'anno': match.group(1),
            'codice_fiscale': match.group(2).upper(),
        }
    
    # Pattern 3: Solo anno nel nome
    match = re.search(r'(20\d{2})', filename)
    if match:
        return {
            'anno': match.group(1),
            'codice_fiscale': None,
        }
    
    return None
