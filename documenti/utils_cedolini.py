"""
Utility per il parsing e l'importazione di cedolini paga da file ZIP.

Gestisce:
- Parsing del nome file per estrarre CF, nome, cognome, matricola
- Estrazione dati dal contenuto PDF (periodo, livello, azienda)
- Identificazione mensilità (ordinaria, tredicesima, quattordicesima)
"""
from __future__ import annotations
import re
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import date, datetime
import pdfplumber
from io import BytesIO

logger = logging.getLogger(__name__)

# Mappa mesi italiani
MESI_ITALIANI = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
    'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
    'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
    # Abbreviazioni
    'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
    'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12,
}


def parse_filename_cedolino(filename: str) -> Optional[Dict[str, str]]:
    """
    Estrae informazioni dal nome file del cedolino.
    
    Pattern atteso: 
    {CF} - {ANNO} - {COGNOME} {NOME} ({CF}-{MATRICOLA}).pdf
    Esempio: BNCLNR99C46G088Y - 2025 - BIANCHI ELEONORA (BNCLNR99C46G088Y-0000001).pdf
    
    Returns:
        Dict con chiavi: codice_fiscale, anno, cognome, nome, matricola
        None se il parsing fallisce
    """
    # Pattern regex per il nome file
    pattern = r'^([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\s*-\s*(\d{4})\s*-\s*([A-Z\s]+)\s+([A-Z]+)\s*\(([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])-(\d+)\)\.pdf$'
    
    match = re.match(pattern, filename, re.IGNORECASE)
    if not match:
        logger.warning(f"Nome file non valido: {filename}")
        return None
    
    cf1, anno, cognome, nome, cf2, matricola = match.groups()
    
    # Verifica coerenza codici fiscali
    if cf1.upper() != cf2.upper():
        logger.warning(f"Codici fiscali non coerenti nel nome file: {cf1} != {cf2}")
        return None
    
    return {
        'codice_fiscale': cf1.upper(),
        'anno': anno,
        'cognome': cognome.strip().title(),
        'nome': nome.strip().title(),
        'matricola': matricola,
    }


def extract_pdf_data(pdf_content: bytes) -> Dict[str, Any]:
    """
    Estrae dati dal contenuto del PDF del cedolino.
    
    Args:
        pdf_content: Contenuto binario del file PDF
        
    Returns:
        Dict con dati estratti (periodo, azienda, livello, etc.)
    """
    data = {
        'periodo': None,
        'mese': None,
        'anno': None,
        'azienda_cf': None,
        'azienda_ragione_sociale': None,
        'azienda_indirizzo': None,
        'livello': None,
        'data_nascita': None,
        'data_assunzione': None,
        'matricola_inps': None,
        'raw_text': '',
    }
    
    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            # Estrai testo dalla prima pagina (contiene i dati principali)
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
                data['raw_text'] = text
                
                # Dividi in linee per parsing più preciso
                lines = text.split('\n')
                
                # Estrai periodo retribuzione
                # Pattern: cerca dopo "SPECIAL." o "PERIODO" la stringa "Mese Anno"
                for line in lines:
                    periodo_match = re.search(r'(?:SPECIAL\.|PERIODO).*?([A-Z][a-z]+\s+\d{4})', line, re.IGNORECASE)
                    if periodo_match:
                        periodo_str = periodo_match.group(1).strip()
                        data['periodo'] = periodo_str
                        
                        # Estrai mese e anno
                        mese_anno = re.match(r'([A-Za-z]+)\s+(\d{4})', periodo_str, re.IGNORECASE)
                        if mese_anno:
                            mese_nome = mese_anno.group(1).lower()
                            data['anno'] = int(mese_anno.group(2))
                            data['mese'] = MESI_ITALIANI.get(mese_nome)
                        break
                
                # Estrai CF azienda
                # Cerca linea con numero 11 cifre seguito da spazi e numeri con slash
                # Supporta 2 formati:
                # - Formato 1: "00884530536 3603879309/00 021947673/73" (3 campi)
                # - Formato 2: "00884530536 021947673/73" (2 campi)
                for line in lines:
                    cf_line = re.match(r'^(\d{11})\s+\d+/\d+', line)
                    if cf_line:
                        data['azienda_cf'] = cf_line.group(1)
                        break
                
                # Estrai ragione sociale azienda
                # Cerca linea con codice (6 cifre) + nome azienda
                # Esempio: "000049 LA FORTEZZA SOCIETA' COOPERATIVA"
                for line in lines:
                    ragione_match = re.match(r'^\d{6}\s+(.+?)$', line)
                    if ragione_match:
                        nome_azienda = ragione_match.group(1).strip()
                        # Verifica che non sia un header o altro
                        if len(nome_azienda) > 5 and not re.match(r'^[A-Z\s]+$', nome_azienda[:20]):
                            data['azienda_ragione_sociale'] = nome_azienda
                            break
                
                # Estrai indirizzo (linea successiva alla ragione sociale, con CAP e città)
                if data['azienda_ragione_sociale']:
                    for i, line in enumerate(lines):
                        if data['azienda_ragione_sociale'] in line:
                            # Prendi le 2 linee successive
                            if i + 1 < len(lines):
                                indirizzo_line1 = lines[i + 1].strip()
                            if i + 2 < len(lines):
                                indirizzo_line2 = lines[i + 2].strip()
                                # Cerca CAP + città + provincia
                                cap_citta = re.match(r'(\d{5})\s+([A-Z\s]+)\s*\(([A-Z]{2})\)', indirizzo_line2)
                                if cap_citta:
                                    cap = cap_citta.group(1)
                                    citta = cap_citta.group(2).strip()
                                    prov = cap_citta.group(3)
                                    # Estrai via dalla linea precedente (rimuovi "Aut." e dopo)
                                    via = re.sub(r'\s*Aut\..*$', '', indirizzo_line1).strip()
                                    data['azienda_indirizzo'] = f"{via}, {cap} {citta} ({prov})"
                            break
                
                # Estrai livello
                livello_match = re.search(r"(\d+)'?\s*Livello", text, re.IGNORECASE)
                if livello_match:
                    data['livello'] = f"{livello_match.group(1)}° Livello"
                
                # Estrai date dipendente
                # Cerca linea con pattern: DD-MM-YYYY DD-MM-YYYY
                for line in lines:
                    date_match = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', line)
                    if date_match:
                        data['data_nascita'] = date_match.group(1)
                        data['data_assunzione'] = date_match.group(2)
                        break
                
                # Estrai matricola dipendente (dalla linea con nome dipendente)
                # Pattern: numero + COGNOME NOME + CF
                for line in lines:
                    matricola_match = re.match(r'^(\d+)\s+([A-Z]+\s+[A-Z]+)\s+([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', line)
                    if matricola_match:
                        data['matricola_inps'] = matricola_match.group(1)
                        break
                
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dati PDF: {e}", exc_info=True)
    
    return data


def identifica_mensilita(periodo: Optional[str], raw_text: str) -> int:
    """
    Identifica la mensilità del cedolino.
    
    Args:
        periodo: Stringa periodo (es. "Dicembre 2025")
        raw_text: Testo completo del PDF
        
    Returns:
        Numero mensilità (1-12 per ordinaria, 13 per tredicesima, 14 per quattordicesima)
    """
    if not raw_text:
        return 1
    
    # Cerca keywords per mensilità speciali
    text_lower = raw_text.lower()
    
    if 'tredicesima' in text_lower or '13esima' in text_lower or '13°' in text_lower:
        return 13
    
    if 'quattordicesima' in text_lower or '14esima' in text_lower or '14°' in text_lower:
        return 14
    
    # Altrimenti, estrai il mese dal periodo
    if periodo:
        for mese_nome, mese_num in MESI_ITALIANI.items():
            if mese_nome in periodo.lower():
                return mese_num
    
    # Default: mensilità 1 (gennaio)
    return 1


def calcola_ultimo_giorno_mese(anno: int, mese: int) -> date:
    """
    Calcola l'ultimo giorno del mese specificato.
    
    Args:
        anno: Anno (es. 2025)
        mese: Mese (1-12)
        
    Returns:
        Data dell'ultimo giorno del mese
    """
    from calendar import monthrange
    
    ultimo_giorno = monthrange(anno, mese)[1]
    return date(anno, mese, ultimo_giorno)


def genera_titolo_fascicolo(mese: int, anno: int) -> str:
    """
    Genera il titolo del fascicolo per le paghe.
    
    Args:
        mese: Numero mese (1-12)
        anno: Anno (es. 2025)
        
    Returns:
        Titolo fascicolo (es. "Paghe dic 2025")
    """
    # Mappa abbreviazioni mesi
    mesi_abbr = {
        1: 'gen', 2: 'feb', 3: 'mar', 4: 'apr',
        5: 'mag', 6: 'giu', 7: 'lug', 8: 'ago',
        9: 'set', 10: 'ott', 11: 'nov', 12: 'dic',
    }
    
    mese_abbr = mesi_abbr.get(mese, 'gen')
    return f"Paghe {mese_abbr} {anno}"


def genera_descrizione_documento(cognome: str, nome: str, periodo: str) -> str:
    """
    Genera la descrizione del documento cedolino.
    
    Args:
        cognome: Cognome dipendente
        nome: Nome dipendente
        periodo: Periodo (es. "Dicembre 2025")
        
    Returns:
        Descrizione documento (es. "Cedolino BIANCHI ELEONORA - Dicembre 2025")
    """
    return f"Cedolino {cognome.upper()} {nome.upper()} - {periodo}"


def parse_data_italiana(data_str: str) -> Optional[date]:
    """
    Converte una data in formato italiano (DD-MM-YYYY) in oggetto date.
    
    Args:
        data_str: Stringa data (es. "06-03-1999")
        
    Returns:
        Oggetto date o None se parsing fallisce
    """
    if not data_str:
        return None
    
    try:
        return datetime.strptime(data_str, "%d-%m-%Y").date()
    except ValueError:
        logger.warning(f"Formato data non valido: {data_str}")
        return None


def genera_note_documento(file_data: Dict[str, str], pdf_data: Dict[str, Any]) -> str:
    """
    Genera il testo delle note del documento con tutti i dati estratti.
    
    Args:
        file_data: Dati estratti dal nome file
        pdf_data: Dati estratti dal contenuto PDF
        
    Returns:
        Testo formattato per le note
    """
    note_lines = ["=== DATI CEDOLINO ===\n"]
    
    # Dati dipendente
    note_lines.append("DIPENDENTE:")
    if file_data:
        note_lines.append(f"  Nome: {file_data.get('nome', 'N/D')} {file_data.get('cognome', 'N/D')}")
        note_lines.append(f"  Codice Fiscale: {file_data.get('codice_fiscale', 'N/D')}")
        note_lines.append(f"  Matricola: {file_data.get('matricola', 'N/D')}")
    
    if pdf_data.get('data_nascita'):
        note_lines.append(f"  Data Nascita: {pdf_data['data_nascita']}")
    if pdf_data.get('data_assunzione'):
        note_lines.append(f"  Data Assunzione: {pdf_data['data_assunzione']}")
    if pdf_data.get('livello'):
        note_lines.append(f"  Livello: {pdf_data['livello']}")
    if pdf_data.get('matricola_inps'):
        note_lines.append(f"  Matricola INPS: {pdf_data['matricola_inps']}")
    
    # Dati azienda
    note_lines.append("\nAZIENDA:")
    if pdf_data.get('azienda_ragione_sociale'):
        note_lines.append(f"  Ragione Sociale: {pdf_data['azienda_ragione_sociale']}")
    if pdf_data.get('azienda_cf'):
        note_lines.append(f"  Codice Fiscale: {pdf_data['azienda_cf']}")
    if pdf_data.get('azienda_indirizzo'):
        note_lines.append(f"  Indirizzo: {pdf_data['azienda_indirizzo']}")
    
    # Periodo
    note_lines.append("\nPERIODO RETRIBUZIONE:")
    if pdf_data.get('periodo'):
        note_lines.append(f"  {pdf_data['periodo']}")
    
    return "\n".join(note_lines)
