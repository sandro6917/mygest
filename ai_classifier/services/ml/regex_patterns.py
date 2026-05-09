"""
Regex Patterns per riconoscimento documenti italiani

Contiene pattern per:
- Codici Fiscali (PF e PG)
- Partite IVA
- Date (formati italiani)
- Importi (€, EUR, virgola decimale)
- Numeri documento (fattura, protocollo, etc.)
"""
import re

# ============================================================================
# CODICE FISCALE
# ============================================================================

# Codice Fiscale Persona Fisica (16 caratteri alfanumerici)
# Formato: RSSMRA85M01H501U
CODICE_FISCALE_PATTERN = r'\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b'

# ============================================================================
# PARTITA IVA
# ============================================================================

# Partita IVA italiana (11 cifre)
PARTITA_IVA_PATTERN = r'\b[0-9]{11}\b'

# ============================================================================
# DATE (formati italiani comuni)
# ============================================================================

DATE_PATTERNS = [
    # DD/MM/YYYY o DD-MM-YYYY
    r'\b([0-3]?[0-9])[\/\-]([0-1]?[0-9])[\/\-]([12][0-9]{3})\b',
    
    # DD/MM/YY o DD-MM-YY
    r'\b([0-3]?[0-9])[\/\-]([0-1]?[0-9])[\/\-]([0-9]{2})\b',
    
    # YYYY-MM-DD (ISO)
    r'\b([12][0-9]{3})[\/\-]([0-1]?[0-9])[\/\-]([0-3]?[0-9])\b',
    
    # Testuale: 15 gennaio 2024, 15 gen 2024
    r'\b([0-3]?[0-9])\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)\s+([12][0-9]{3})\b',
]

# ============================================================================
# IMPORTI
# ============================================================================

IMPORTO_PATTERNS = [
    # €1.234,56 o € 1.234,56
    r'€\s?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)',
    
    # 1.234,56€ o 1.234,56 €
    r'([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s?€',
    
    # EUR 1.234,56 o 1.234,56 EUR
    r'(?:EUR\s)?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)(?:\sEUR)?',
    
    # 1234.56 (formato inglese, usato in alcuni documenti)
    r'\b([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})\b',
]

# ============================================================================
# NUMERI DOCUMENTO
# ============================================================================

NUMERO_DOCUMENTO_PATTERNS = [
    # Numero fattura: FAT-2024-001, FATT/2024/001, etc.
    r'\b(?:FAT|FATT|FT|FATTURA)\s?[-\/]?\s?([0-9]{1,4})\s?[-\/]?\s?([0-9]{1,6})\b',
    
    # Protocollo: PROT-12345, Prot.12345
    r'\b(?:PROT|Prot\.?)\s?[-\/]?\s?([0-9]{4,8})\b',
    
    # Numero pratica: PRA-2024-123
    r'\b(?:PRA|PRATICA)\s?[-\/]?\s?([0-9]{1,4})\s?[-\/]?\s?([0-9]{1,6})\b',
    
    # Numero generico: N. 12345, Nr. 12345, n°12345
    r'\b(?:N\.|Nr\.|n°|num\.)\s?([0-9]{4,8})\b',
    
    # Codice documento: DOC-12345
    r'\b(?:DOC|COD)\s?[-\/]?\s?([0-9]{4,8})\b',
]

# ============================================================================
# ALTRI PATTERN UTILI
# ============================================================================

# IBAN italiano
IBAN_PATTERN = r'\bIT[0-9]{2}[A-Z][0-9]{10}[0-9A-Z]{12}\b'

# Numero di telefono italiano
TELEFONO_PATTERN = r'\b(?:\+39\s?)?(?:[0-9]{2,4}[-\s]?)?[0-9]{6,8}\b'

# Email
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# PEC (Posta Elettronica Certificata)
PEC_PATTERN = r'\b[A-Za-z0-9._%+-]+@pec\.[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Codice ATECO
ATECO_PATTERN = r'\b[0-9]{2}\.[0-9]{2}\.[0-9]{2}\b'

# ============================================================================
# KEYWORDS PER TIPO DOCUMENTO (usate in FeatureExtractor)
# ============================================================================

DOCUMENT_TYPE_KEYWORDS = {
    'CED': [  # Cedolino
        'cedolino', 'busta paga', 'retribuzione', 'stipendio',
        'competenze', 'detrazioni', 'contributi inps', 'inail',
        'trattenute', 'netto', 'lordo', 'tfr', 'rateo',
    ],
    'F24': [  # F24
        'f24', 'modello f24', 'codice tributo', 'ravvedimento',
        'saldo', 'acconto', 'imposta', 'sanzione', 'interessi',
    ],
    'FAT': [  # Fattura
        'fattura', 'iva', 'imponibile', 'totale fattura',
        'scadenza pagamento', 'aliquota', 'bollo', 'ritenuta',
    ],
    'UNI': [  # Unilav
        'unilav', 'comunicazione obbligatoria', 'rapporto di lavoro',
        'assunzione', 'cessazione', 'trasformazione', 'proroga',
        'co_', 'unificata lav',
    ],
    'DIC': [  # Dichiarazione Fiscale
        'dichiarazione', 'redditi', 'agenzia entrate', '730',
        'unico', 'irpef', 'ires', 'addizionale', 'detrazioni',
    ],
    'CON': [  # Contratto
        'contratto', 'parti contraenti', 'clausola', 'oggetto contratto',
        'stipula', 'accordo', 'risoluzione', 'recesso',
    ],
    'BIL': [  # Bilancio
        'bilancio', 'stato patrimoniale', 'conto economico',
        'attivo', 'passivo', 'utile', 'perdita', 'esercizio',
    ],
    'EST': [  # Estratto Conto
        'estratto conto', 'saldo iniziale', 'saldo finale',
        'movimenti', 'dare', 'avere', 'bonifico', 'addebito',
    ],
    'BPAG': [  # Busta Paga (alias di CED)
        'busta paga', 'retribuzione mensile', 'stipendio',
        'salario', 'mensilità',
    ],
    '770': [  # 770
        '770', 'dichiarazione sostituti imposta', 'ritenute',
        'certificazione unica', 'cu',
    ],
    'RED': [  # Redditi
        'redditi', 'modello redditi', 'quadro', 'addizionale',
        'irpef', 'ires',
    ],
    'LIBUNI': [  # Libro Unico
        'libro unico', 'lul', 'presenze', 'timbrature',
        'ore lavorate', 'straordinario',
    ],
    'PRES': [  # Presenze
        'presenze', 'timbrature', 'cartellini', 'badge',
        'ore lavorate', 'permessi', 'ferie', 'malattia',
    ],
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_codice_fiscale(cf: str) -> bool:
    """
    Valida formalmente un codice fiscale (solo formato, non checksum).
    
    Args:
        cf: Codice fiscale da validare
        
    Returns:
        True se formato valido
    """
    if not cf or len(cf) != 16:
        return False
    
    # Match pattern
    if not re.match(CODICE_FISCALE_PATTERN, cf.upper()):
        return False
    
    # TODO: Implementare validazione checksum (carattere 16)
    return True


def validate_partita_iva(piva: str) -> bool:
    """
    Valida formalmente una partita IVA italiana.
    
    Args:
        piva: Partita IVA da validare
        
    Returns:
        True se formato valido
    """
    if not piva or len(piva) != 11:
        return False
    
    if not piva.isdigit():
        return False
    
    # TODO: Implementare validazione checksum (algoritmo Luhn)
    return True


def extract_all_matches(text: str, pattern: str, flags=re.IGNORECASE) -> list:
    """
    Estrae tutti i match di un pattern dal testo.
    
    Args:
        text: Testo da analizzare
        pattern: Regex pattern
        flags: Regex flags
        
    Returns:
        Lista di match
    """
    return re.findall(pattern, text, flags)
