"""
Parser per cedolini paga.

Estrae dati strutturati da PDF cedolini per l'importazione automatica nel sistema.
"""
from __future__ import annotations
import re
import logging
from typing import TypedDict, Optional, Dict, Any
from datetime import date, datetime
import pdfplumber

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


class DatoreData(TypedDict):
    """Dati estratti del datore di lavoro"""
    codice_fiscale: str
    ragione_sociale: Optional[str]
    indirizzo: Optional[str]


class LavoratoreData(TypedDict):
    """Dati estratti del lavoratore/dipendente"""
    codice_fiscale: str
    cognome: str
    nome: str
    matricola: Optional[str]
    data_nascita: Optional[str]
    data_assunzione: Optional[str]
    data_cessazione: Optional[str]  # Terza data - può essere NULL
    matricola_inps: Optional[str]


class CedolinoData(TypedDict):
    """Dati estratti dal cedolino"""
    anno: int
    mese: int
    mensilita: int  # 1-12 ordinaria, 13 tredicesima, 14 quattordicesima
    periodo: str  # es. "Dicembre 2025"
    livello: Optional[str]
    data_documento: date  # Ultimo giorno del mese
    netto: Optional[str]  # Netto da corrispondere (formato Decimal es. "56.51")
    numero_cedolino: Optional[str]  # Numero cedolino per chiave duplicazione
    data_ora_cedolino: Optional[str]  # Data e ora cedolino (formato "DD-MM-YYYY HH:MM")


class CedolinoParseResult(TypedDict):
    """Risultato completo del parsing"""
    datore: DatoreData
    lavoratore: LavoratoreData
    cedolino: CedolinoData


def parse_cedolino_pdf(pdf_path: str) -> CedolinoParseResult:
    """
    Estrae dati strutturati da un PDF cedolino.
    
    Args:
        pdf_path: Percorso del file PDF da analizzare
        
    Returns:
        Dizionario con dati di datore, lavoratore e cedolino
        
    Raises:
        ValueError: Se il PDF non è un valido cedolino o dati essenziali mancanti
        FileNotFoundError: Se il file non esiste
    """
    import os
    filename = os.path.basename(pdf_path)
    
    # 1. Prova a estrarre dati dal nome file (fallback se presente)
    file_data = parse_filename_cedolino(filename)
    
    # 2. Leggi PDF e estrai dati
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    pdf_data = extract_pdf_data(pdf_content)
    
    # 3. Validazione dati essenziali
    if not pdf_data.get('azienda_cf'):
        raise ValueError(f"Codice fiscale datore di lavoro non trovato nel PDF: {filename}")
    
    # 4. Costruzione dati lavoratore
    # Priorità: dati da nome file > dati da PDF
    if file_data:
        lavoratore_cf = file_data['codice_fiscale']
        lavoratore_cognome = file_data['cognome']
        lavoratore_nome = file_data['nome']
        lavoratore_matricola = file_data['matricola']
    else:
        # Se nome file non valido, prova a estrarre da PDF (best effort)
        # Cerca pattern: MATRICOLA COGNOME NOME CF nella prima pagina
        lavoratore_cf = None
        lavoratore_cognome = None
        lavoratore_nome = None
        lavoratore_matricola = None
        
        lines = pdf_data.get('raw_text', '').split('\n')
        for line in lines:
            # Pattern: numero + COGNOME NOME + CF
            match = re.match(r'^(\d+)\s+([A-Z]+)\s+([A-Z]+)\s+([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', line)
            if match:
                lavoratore_matricola = match.group(1)
                lavoratore_cognome = match.group(2).title()
                lavoratore_nome = match.group(3).title()
                lavoratore_cf = match.group(4).upper()
                break
        
        if not lavoratore_cf:
            raise ValueError(
                f"Impossibile identificare il dipendente dal PDF: {filename}. "
                "Verifica che il nome file segua il pattern: "
                "CF - ANNO - COGNOME NOME (CF-MATRICOLA).pdf"
            )
    
    # 5. Identificazione mensilità
    mensilita = identifica_mensilita(pdf_data.get('periodo'), pdf_data.get('raw_text', ''))
    
    # 6. Calcolo anno e mese
    anno = pdf_data.get('anno') or (int(file_data['anno']) if file_data else None)
    if not anno:
        raise ValueError(f"Anno non trovato nel cedolino: {filename}")
    
    mese = pdf_data.get('mese') or mensilita
    if mese > 12:  # Tredicesima/quattordicesima -> dicembre
        mese = 12
    
    # 7. Calcolo data documento (ultimo giorno mese)
    data_doc = calcola_ultimo_giorno_mese(anno, mese)
    
    # 8. Formattazione periodo
    periodo = pdf_data.get('periodo') or genera_periodo_display(mese, anno, mensilita)
    
    # 9. Costruzione risultato
    result: CedolinoParseResult = {
        'datore': {
            'codice_fiscale': pdf_data['azienda_cf'],
            'ragione_sociale': pdf_data.get('azienda_ragione_sociale'),
            'indirizzo': pdf_data.get('azienda_indirizzo'),
        },
        'lavoratore': {
            'codice_fiscale': lavoratore_cf,
            'cognome': lavoratore_cognome,
            'nome': lavoratore_nome,
            'matricola': lavoratore_matricola,
            'data_nascita': pdf_data.get('data_nascita'),
            'data_assunzione': pdf_data.get('data_assunzione'),
            'data_cessazione': pdf_data.get('data_cessazione'),
            'matricola_inps': pdf_data.get('matricola_inps'),
        },
        'cedolino': {
            'anno': anno,
            'mese': mese,
            'mensilita': mensilita,
            'periodo': periodo,
            'livello': pdf_data.get('livello'),
            'data_documento': data_doc,
            'netto': pdf_data.get('netto'),
            'numero_cedolino': pdf_data.get('numero_cedolino'),
            'data_ora_cedolino': pdf_data.get('data_ora_cedolino'),
        },
    }
    
    return result


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
        logger.debug(f"Nome file non segue il pattern standard: {filename}")
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
    from io import BytesIO
    
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
        'data_cessazione': None,
        'matricola_inps': None,
        'netto': None,
        'numero_cedolino': None,
        'data_ora_cedolino': None,
        'raw_text': '',
    }
    
    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("Il PDF è vuoto")
            
            # Estrai testo da tutte le pagine (supporto multi-pagina)
            all_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
            
            data['raw_text'] = all_text
            
            # Usa prima pagina per la maggior parte dei dati
            text = pdf.pages[0].extract_text()
            
            # Dividi in linee per parsing più preciso
            lines = text.split('\n')
            
            # Estrai periodo retribuzione
            # FIX: Gestisce vari formati di cedolini
            # Pattern 1: "SPECIAL. Gennaio 2025" (stessa riga)
            # Pattern 2: "SPECIAL." e "Gennaio 2025" su righe separate  
            # Pattern 3: "PERIODO RETRIBUZIONE" seguito da "Aprile 2025"
            # Pattern 4: Generico "Mese Anno" nelle prime 30 righe
            
            for idx, line in enumerate(lines):
                # Pattern 1: Periodo sulla stessa riga di SPECIAL./PERIODO
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
                        logger.debug(f"✅ Periodo estratto (pattern 1): {data['periodo']}")
                    break
                
                # Pattern 2: SPECIAL./PERIODO su una riga, periodo nelle successive 3 righe
                if re.search(r'^(?:SPECIAL\.|PERIODO)\s*$', line.strip(), re.IGNORECASE):
                    # Cerca mese+anno nelle successive 3 righe
                    for offset in range(1, 4):
                        if idx + offset < len(lines):
                            next_line = lines[idx + offset].strip()
                            mese_anno_match = re.match(r'^([A-Z][a-z]+)\s+(\d{4})$', next_line, re.IGNORECASE)
                            if mese_anno_match:
                                mese_nome = mese_anno_match.group(1).lower()
                                anno_str = mese_anno_match.group(2)
                                
                                data['periodo'] = f"{mese_anno_match.group(1).capitalize()} {anno_str}"
                                data['anno'] = int(anno_str)
                                data['mese'] = MESI_ITALIANI.get(mese_nome)
                                
                                logger.debug(f"✅ Periodo estratto (pattern 2): {data['periodo']}")
                                break
                    if data['periodo']:
                        break
                
                # Pattern 3: "PERIODO RETRIBUZIONE" seguito da mese anno
                if re.search(r'PERIODO.*RETRIBUZIONE', line, re.IGNORECASE):
                    # Cerca mese+anno nelle successive 25 righe (aumentato per Arklabs)
                    for offset in range(1, 26):
                        if idx + offset < len(lines):
                            next_line = lines[idx + offset].strip()
                            # Match flessibile: supporta "Aprile 2025" anche con spazi extra
                            mese_anno_match = re.search(r'\b([A-Z][a-z]+)\s+(\d{4})\b', next_line, re.IGNORECASE)
                            if mese_anno_match:
                                mese_nome = mese_anno_match.group(1).lower()
                                anno_str = mese_anno_match.group(2)
                                
                                # Verifica che il mese sia valido
                                if mese_nome in MESI_ITALIANI:
                                    data['periodo'] = f"{mese_anno_match.group(1).capitalize()} {anno_str}"
                                    data['anno'] = int(anno_str)
                                    data['mese'] = MESI_ITALIANI.get(mese_nome)
                                    
                                    logger.debug(f"✅ Periodo estratto (pattern 3 - PERIODO RETRIBUZIONE): {data['periodo']}")
                                    break
                    if data['periodo']:
                        break
            
            # Pattern 4 (fallback): Cerca qualsiasi "Mese Anno" nelle prime 30 righe
            if not data['periodo']:
                for idx, line in enumerate(lines[:30]):
                    # Cerca pattern mese+anno isolato
                    mese_anno_match = re.search(r'\b([A-Z][a-z]+)\s+(\d{4})\b', line, re.IGNORECASE)
                    if mese_anno_match:
                        mese_nome = mese_anno_match.group(1).lower()
                        anno_str = mese_anno_match.group(2)
                        
                        # Verifica che sia un mese valido (evita falsi positivi come "Via 2025")
                        if mese_nome in MESI_ITALIANI:
                            data['periodo'] = f"{mese_anno_match.group(1).capitalize()} {anno_str}"
                            data['anno'] = int(anno_str)
                            data['mese'] = MESI_ITALIANI.get(mese_nome)
                            
                            logger.debug(f"✅ Periodo estratto (pattern 4 - fallback): {data['periodo']}")
                            break
            
            # Estrai CF azienda/datore di lavoro
            # Può essere: 11 cifre (P.IVA persona giuridica) o 16 char alfanumerici (CF persona fisica)
            # Il CF datore si trova sempre alla riga 23 (indice 22) del formato:
            # - Persona giuridica: "01689620530 053 021 1" (11 cifre + INPS + INAIL)
            # - Persona fisica: "SLMRME40E22C080N 053 021 1" (16 char + INPS + INAIL)
            
            for idx, line in enumerate(lines):
                # Pattern 1: CF 16 caratteri alfanumerici seguito da codici INPS/INAIL
                # Questo pattern deve essere controllato PRIMA per evitare conflitti
                cf_16_match = re.match(r'^([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\s+\d+\s+\d+', line)
                if cf_16_match:
                    data['azienda_cf'] = cf_16_match.group(1)
                    break
                
                # Pattern 2: P.IVA 11 cifre seguito da codici INPS/INAIL (es. "01689620530 053 021 1")
                cf_11_match = re.match(r'^(\d{11})\s+\d+\s+\d+', line)
                if cf_11_match:
                    data['azienda_cf'] = cf_11_match.group(1)
                    break
                
                # Pattern 3: P.IVA 11 cifre con slash (formato alternativo "12345678901 123/456")
                cf_11_slash = re.match(r'^(\d{11})\s+\d+/\d+', line)
                if cf_11_slash:
                    data['azienda_cf'] = cf_11_slash.group(1)
                    break
            
            # Fallback: cerca CF 16 caratteri nelle prime 30 righe (escludi righe con matricola dipendente)
            if not data['azienda_cf']:
                for idx, line in enumerate(lines[:30]):
                    cf_16_fallback = re.search(r'\b([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\b', line)
                    if cf_16_fallback:
                        potential_cf = cf_16_fallback.group(1)
                        # Escludi CF dipendente (appare con matricola es. "0000040 COGNOME NOME CF")
                        if not re.match(r'^\d{7}\s+', line):
                            data['azienda_cf'] = potential_cf
                            break
            
            # Ultimo fallback: cerca qualsiasi 11 cifre nelle righe 15-30
            if not data['azienda_cf']:
                for idx, line in enumerate(lines[15:30], start=15):
                    cf_11_fallback = re.search(r'\b(\d{11})\b', line)
                    if cf_11_fallback:
                        data['azienda_cf'] = cf_11_fallback.group(1)
                        break
            
            # Estrai ragione sociale azienda
            for line in lines:
                ragione_match = re.match(r'^\d{6}\s+(.+?)$', line)
                if ragione_match:
                    nome_azienda = ragione_match.group(1).strip()
                    if len(nome_azienda) > 5:
                        data['azienda_ragione_sociale'] = nome_azienda
                        break
            
            # Estrai indirizzo
            if data['azienda_ragione_sociale']:
                for i, line in enumerate(lines):
                    if data['azienda_ragione_sociale'] in line:
                        if i + 1 < len(lines):
                            indirizzo_line1 = lines[i + 1].strip()
                        if i + 2 < len(lines):
                            indirizzo_line2 = lines[i + 2].strip()
                            cap_citta = re.match(r'(\d{5})\s+([A-Z\s]+)\s*\(([A-Z]{2})\)', indirizzo_line2)
                            if cap_citta:
                                cap = cap_citta.group(1)
                                citta = cap_citta.group(2).strip()
                                prov = cap_citta.group(3)
                                via = re.sub(r'\s*Aut\..*$', '', indirizzo_line1).strip()
                                data['azienda_indirizzo'] = f"{via}, {cap} {citta} ({prov})"
                        break
            
            # Estrai livello
            livello_match = re.search(r"(\d+)'?\s*Livello", text, re.IGNORECASE)
            if livello_match:
                data['livello'] = f"{livello_match.group(1)}° Livello"
            
            # Estrai date dipendente (nascita, assunzione, cessazione)
            for line in lines:
                # Cerca 3 date consecutive (nascita + assunzione + cessazione)
                date_match_3 = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', line)
                if date_match_3:
                    data['data_nascita'] = date_match_3.group(1)
                    data['data_assunzione'] = date_match_3.group(2)
                    data['data_cessazione'] = date_match_3.group(3)
                    break
                
                # Fallback: cerca solo 2 date (nascita + assunzione, senza cessazione)
                date_match_2 = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', line)
                if date_match_2:
                    data['data_nascita'] = date_match_2.group(1)
                    data['data_assunzione'] = date_match_2.group(2)
                    data['data_cessazione'] = None  # Dipendente ancora in servizio
                    break
            
            # Estrai matricola INPS
            for line in lines:
                matricola_match = re.match(r'^(\d+)\s+([A-Z]+\s+[A-Z]+)\s+([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])', line)
                if matricola_match:
                    data['matricola_inps'] = matricola_match.group(1)
                    break
            
            # Estrai NETTO da corrispondere (cerca in tutto il testo)
            # Pattern migliorato per gestire vari formati con separatori migliaia e decimali
            # Supporta: 1.234,56 | 1234,56 | 1234.56 | 123,45 | 12,34 | 1,23
            # FIX: Gestisce vari formati di cedolini:
            #   - "NETTO DA CORRISPONDERE 608,41"
            #   - "NETTO DEL MESE ... 608,41 €"
            
            netto_trovato = False
            
            # IMPORTANTE: Il netto è sempre nell'ULTIMA pagina del cedolino
            ultima_pagina_text = pdf.pages[-1].extract_text()
            ultima_pagina_lines = ultima_pagina_text.split('\n') if ultima_pagina_text else []
            
            # PRIORITY 1: Cerca "NETTO DEL MESE" (usato in cedolini Arklabs nuovi)
            # Cerca nella riga e prendi l'ultimo numero della riga successiva
            netto_trovato_in_riga = False
            for idx, line in enumerate(ultima_pagina_lines):
                if re.search(r'NETTO.*DEL.*MESE', line, re.IGNORECASE):
                    logger.debug(f"✅ Trovato 'NETTO DEL MESE' alla riga {idx}: {line.strip()}")
                    
                    # Cerca SOLO nelle successive righe (NON nella riga corrente)
                    # Per evitare di catturare numeri che precedono "NETTO DEL MESE"
                    for offset in range(1, 5):  # Aumentato a 5 righe
                        if idx + offset < len(ultima_pagina_lines):
                            next_line = ultima_pagina_lines[idx + offset].strip()
                            
                            # ESCLUDI righe che contengono parole chiave non desiderate
                            if any(keyword in next_line.upper() for keyword in ['R.O.L', 'ROL', 'FERIE', 'EX-FEST']):
                                logger.debug(f"⏭️  Riga {idx + offset} ignorata (contiene keyword): {next_line}")
                                continue
                            
                            # IMPORTANTE: Cerca solo righe che contengono il simbolo €
                            # oppure righe che hanno SOLO numeri (evita righe con testo misto)
                            if '€' in next_line or re.match(r'^\s*\d+[.,]\d+\s*$', next_line):
                                # Cerca tutti gli importi con 2 decimali nella riga
                                importi_in_riga = re.findall(
                                    r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})\s*€?',
                                    next_line
                                )
                                
                                if importi_in_riga:
                                    # Prendi l'ULTIMO importo della riga (quello più a destra)
                                    netto_raw = importi_in_riga[-1]
                                    logger.debug(f"✅ Riga {idx + offset}: {next_line}")
                                    logger.debug(f"✅ Importi trovati: {importi_in_riga}, ultimo: {netto_raw}")
                                    
                                    # Normalizza formato italiano -> formato standard
                                    if ',' in netto_raw and '.' in netto_raw:
                                        netto_str = netto_raw.replace('.', '').replace(',', '.')
                                    elif ',' in netto_raw:
                                        netto_str = netto_raw.replace(',', '.')
                                    else:
                                        netto_str = netto_raw
                                    
                                    data['netto'] = netto_str
                                    netto_trovato = True
                                    netto_trovato_in_riga = True
                                    logger.debug(f"✅ Netto normalizzato (NETTO DEL MESE - riga successiva): {netto_str}")
                                    break
                    
                    if netto_trovato_in_riga:
                        break
            
            # Se non trovato con metodo riga per riga, prova fallback con area circostante
            if not netto_trovato:
                netto_mese_section = re.search(
                    r'NETTO\s+DEL\s+MESE',
                    all_text,
                    re.IGNORECASE
                )
                
                if netto_mese_section:
                    # Estrai testo INTORNO a "NETTO DEL MESE" (300 char prima + 500 dopo)
                    start_pos = max(0, netto_mese_section.start() - 300)
                    end_pos = min(len(all_text), netto_mese_section.end() + 500)
                    text_around = all_text[start_pos:end_pos]
                    
                    logger.debug(f"⚠️  Fallback: cerco importo nell'area circostante a NETTO DEL MESE")
                    
                    # STRATEGIA 1: Cerca importo seguito da € (più affidabile)
                    importi_euro = re.findall(
                        r'(?<!COMPETENZE\s{0,50})(?<!TRATTENUTE\s{0,50})(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})\s*€',
                        text_around,
                        re.IGNORECASE
                    )
                    
                    if importi_euro:
                        # Se troviamo più importi con €, prendiamo l'ultimo (di solito il netto finale)
                        netto_raw = importi_euro[-1]
                        logger.debug(f"✅ Netto raw estratto (fallback con € - ultimo): {netto_raw}")
                        
                        # Normalizza formato italiano -> formato standard
                        if ',' in netto_raw and '.' in netto_raw:
                            netto_str = netto_raw.replace('.', '').replace(',', '.')
                        elif ',' in netto_raw:
                            netto_str = netto_raw.replace(',', '.')
                        else:
                            netto_str = netto_raw
                        
                        data['netto'] = netto_str
                        netto_trovato = True
                        logger.debug(f"✅ Netto normalizzato (fallback con €): {netto_str}")
                    else:
                        # STRATEGIA 2: Cerca importi >= 10 EUR e prendi il massimo
                        all_importi = re.findall(
                            r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})',
                            text_around
                        )
                        
                        if all_importi:
                            # Normalizza e filtra
                            importi_validi = []
                            for imp in all_importi:
                                if ',' in imp and '.' in imp:
                                    imp_norm = imp.replace('.', '').replace(',', '.')
                                elif ',' in imp:
                                    imp_norm = imp.replace(',', '.')
                                else:
                                    imp_norm = imp
                                
                                try:
                                    valore = float(imp_norm)
                                    # Filtra importi troppo piccoli (< 10 EUR, probabilmente ore/giorni)
                                    if valore >= 10:
                                        importi_validi.append((valore, imp))
                                except ValueError:
                                    continue
                            
                            if importi_validi:
                                # Prendi l'importo più grande (è il netto finale)
                                max_importo = max(importi_validi, key=lambda x: x[0])
                                netto_raw = max_importo[1]
                                
                                logger.debug(f"✅ Netto raw estratto (fallback - max filtrato): {netto_raw} = {max_importo[0]}")
                                
                                if ',' in netto_raw and '.' in netto_raw:
                                    netto_str = netto_raw.replace('.', '').replace(',', '.')
                                elif ',' in netto_raw:
                                    netto_str = netto_raw.replace(',', '.')
                                else:
                                    netto_str = netto_raw
                                
                                data['netto'] = netto_str
                                netto_trovato = True
                                logger.debug(f"✅ Netto normalizzato (fallback - max): {netto_str}")
            
            # PRIORITY 2: Cerca "NETTO DA CORRISPONDERE" (formato standard)
            if not netto_trovato:
                netto_section = re.search(
                    r'NETTO\s+DA\s+CORRISPONDERE',
                    all_text,
                    re.IGNORECASE | re.DOTALL
                )
                
                if netto_section:
                    # Estrai il testo dopo "NETTO DA CORRISPONDERE" (max 200 caratteri)
                    start_pos = netto_section.end()
                    text_after_netto = all_text[start_pos:start_pos + 200]
                    
                    # Pattern per importo con separatori
                    importo_match = re.search(
                        r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})',
                        text_after_netto
                    )
                    
                    if importo_match:
                        netto_raw = importo_match.group(1)
                        logger.debug(f"✅ Netto raw estratto (NETTO DA CORRISPONDERE): {netto_raw}")
                        
                        if ',' in netto_raw and '.' in netto_raw:
                            netto_str = netto_raw.replace('.', '').replace(',', '.')
                        elif ',' in netto_raw:
                            netto_str = netto_raw.replace(',', '.')
                        else:
                            netto_str = netto_raw
                        
                        data['netto'] = netto_str
                        netto_trovato = True
                        logger.debug(f"✅ Netto normalizzato (NETTO DA CORRISPONDERE): {netto_str}")
                    else:
                        logger.warning(f"⚠️  'NETTO DA CORRISPONDERE' trovato ma importo non estratto")
            
            # PRIORITY 3 (fallback): Cerca generico "Netto" seguito da importo
            if not netto_trovato:
                netto_fallback = re.search(
                    r'(?:Netto|NETTO)(?:\s+(?:da|DA)\s+)?',
                    all_text,
                    re.IGNORECASE
                )
                
                if netto_fallback:
                    start_pos = netto_fallback.end()
                    text_after = all_text[start_pos:start_pos + 200]
                    
                    importo_fallback = re.search(
                        r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})',
                        text_after
                    )
                    
                    if importo_fallback:
                        netto_raw = importo_fallback.group(1)
                        
                        if ',' in netto_raw and '.' in netto_raw:
                            netto_str = netto_raw.replace('.', '').replace(',', '.')
                        elif ',' in netto_raw:
                            netto_str = netto_raw.replace(',', '.')
                        else:
                            netto_str = netto_raw
                        
                        data['netto'] = netto_str
                        netto_trovato = True
                        logger.debug(f"✅ Netto estratto (fallback generico): {netto_str}")
                    else:
                        logger.warning(f"⚠️  Pattern netto fallback trovato ma importo non estratto")
            
            if not netto_trovato:
                logger.warning(f"⚠️  Netto NON trovato in nessuna sezione del PDF")
            
            # Estrai numero cedolino (es. "Nr. 00071" oppure pattern simile)
            # Supporta vari pattern: "Nr. 00071", "Numero: 123", "N. 456", etc.
            numero_match = re.search(
                r'(?:Nr\.|Numero|N\.|Num\.)\s*[:\s]*(\d+)',
                all_text,  # ✅ Cerca in tutto il testo, non solo prima pagina
                re.IGNORECASE
            )
            if numero_match:
                data['numero_cedolino'] = numero_match.group(1).zfill(5)  # ✅ Padding zeros (es. "71" → "00071")
                logger.info(f"✅ Numero cedolino estratto: {data['numero_cedolino']}")
            else:
                logger.warning(f"⚠️  Numero cedolino NON trovato nel PDF")
            
            # Estrai data e ora cedolino
            # Pattern 1: "DD-MM-YYYY HH:MM" (formato timestamp completo)
            datetime_match = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})', all_text)  # ✅ Cerca in tutto il testo
            if datetime_match:
                data['data_ora_cedolino'] = f"{datetime_match.group(1)} {datetime_match.group(2)}"
                logger.info(f"✅ Data/Ora cedolino estratta: {data['data_ora_cedolino']}")
            else:
                # Pattern 2: cerca solo data se ora non presente
                date_only_match = re.search(r'Prot\.\s*(\d{2}-\d{2}-\d{4})', all_text)
                if date_only_match:
                    data['data_ora_cedolino'] = date_only_match.group(1)
                    logger.info(f"✅ Data cedolino estratta (senza ora): {data['data_ora_cedolino']}")
                else:
                    logger.warning(f"⚠️  Data/Ora cedolino NON trovata nel PDF")
            
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dati PDF: {e}", exc_info=True)
    
    return data


def identifica_mensilita(periodo: Optional[str], raw_text: str) -> int:
    """
    Identifica la mensilità del cedolino.
    
    Args:
        periodo: Stringa periodo (es. "Dicembre 2025" o "Dicembre 2025 AGG.")
        raw_text: Testo completo del PDF
        
    Returns:
        Numero mensilità (1-12 per ordinaria, 13 per tredicesima, 14 per quattordicesima)
    """
    if not raw_text:
        return 1
    
    # Cerca keywords per mensilità speciali (case-insensitive)
    text_lower = raw_text.lower()
    periodo_lower = periodo.lower() if periodo else ""
    
    # PRIORITY 1: Verifica pattern "AGG." nel periodo
    # "Dicembre {anno} AGG." = Tredicesima
    # "Giugno {anno} AGG." = Quattordicesima
    if periodo and re.search(r'\bagg\.?\b', periodo_lower):
        # Se periodo contiene "dicembre" + "AGG." -> Tredicesima
        if 'dicembre' in periodo_lower:
            logger.debug(f"Tredicesima rilevata da periodo AGG.: {periodo}")
            return 13
        # Se periodo contiene "giugno" + "AGG." -> Quattordicesima
        elif 'giugno' in periodo_lower:
            logger.debug(f"Quattordicesima rilevata da periodo AGG.: {periodo}")
            return 14
        # Altro mese con AGG. - cerca nel testo per capire quale mensilità
        elif 'tredicesima' in text_lower or '13' in text_lower:
            logger.debug(f"Tredicesima rilevata da AGG. + keyword nel testo: {periodo}")
            return 13
        elif 'quattordicesima' in text_lower or '14' in text_lower:
            logger.debug(f"Quattordicesima rilevata da AGG. + keyword nel testo: {periodo}")
            return 14
    
    # PRIORITY 2: Pattern per tredicesima (più varianti possibili)
    tredicesima_patterns = [
        r'\btredicesima\b',
        r'\b13\s*esima\b',
        r'\b13\s*°\s*mensilit[aà]\b',
        r'\bxiii\s*mensilit[aà]\b',
        r'\b13\s*mensilit[aà]\b',
        r'\bmensilit[aà]\s*13\b',
        r'\bspecial\.\s*dicembre.*tredicesima',  # Pattern specifico alcuni cedolini
        r'\bdicembre.*13',  # Dicembre + 13 nelle vicinanze
        r'\bdicembre\s+\d{4}\s+agg\.?',  # Dicembre {anno} AGG.
    ]
    
    for pattern in tredicesima_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.debug(f"Tredicesima rilevata con pattern: {pattern}")
            return 13
    
    # PRIORITY 3: Pattern per quattordicesima
    quattordicesima_patterns = [
        r'\bquattordicesima\b',
        r'\b14\s*esima\b',
        r'\b14\s*°\s*mensilit[aà]\b',
        r'\bxiv\s*mensilit[aà]\b',
        r'\b14\s*mensilit[aà]\b',
        r'\bmensilit[aà]\s*14\b',
        r'\bspecial\.\s*giugno.*quattordicesima',  # Giugno + pattern
        r'\bgiugno.*14',  # Giugno + 14 nelle vicinanze
        r'\bgiugno\s+\d{4}\s+agg\.?',  # Giugno {anno} AGG.
    ]
    
    for pattern in quattordicesima_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.debug(f"Quattordicesima rilevata con pattern: {pattern}")
            return 14
    
    # PRIORITY 4: Altrimenti, estrai il mese dal periodo
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


def genera_periodo_display(mese: int, anno: int, mensilita: int) -> str:
    """
    Genera la stringa periodo display.
    
    Args:
        mese: Numero mese (1-12)
        anno: Anno (es. 2025)
        mensilita: Mensilità (12=ordinaria, 13=tredicesima, 14=quattordicesima)
        
    Returns:
        Periodo display (es. "Dicembre 2025" o "Tredicesima 2025")
    """
    mesi_nomi = {
        1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
        5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
        9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre',
    }
    
    if mensilita == 13:
        return f"Tredicesima {anno}"
    elif mensilita == 14:
        return f"Quattordicesima {anno}"
    else:
        return f"{mesi_nomi.get(mese, 'Gennaio')} {anno}"
