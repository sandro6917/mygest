"""
Funzioni di trasformazione per field mapping AI.

Ogni funzione accetta un valore estratto dall'AI e lo trasforma
nel formato corretto per il campo destinazione.
"""
from typing import Optional, Callable
import re
from datetime import datetime


def normalize_choice_from_db(value: str, campo_codice: str = None, tipo_documento_id: int = None) -> str:
    """
    Normalizza valore per campo choice usando configurazione da database.
    
    FUNZIONE GENERICA per tutti i campi choice di AttributoDefinizione.
    Legge le scelte configurate in Django Admin e cerca match automatico.
    
    Args:
        value: Valore estratto dall'AI (es. "Assunzione", "ASS", "assunzione")
        campo_codice: Codice dell'attributo (es. "tipo", "mese")
        tipo_documento_id: ID del tipo documento (es. 34 per UNILAV)
    
    Returns:
        Valore normalizzato (es. "ASS") o valore originale se nessun match
    
    Esempio:
        AttributoDefinizione.choices = "ASS|Assunzione,PRO|Proroga,TRA|Trasformazione"
        normalize_choice_from_db("assunzione", "tipo", 34) → "ASS"
        normalize_choice_from_db("PROROGA CONTRATTO", "tipo", 34) → "PRO"
    """
    if not value:
        return ""
    
    # Se non abbiamo metadata, ritorna valore originale
    # (questo caso si verifica se chiamata manualmente senza contesto)
    if not campo_codice or not tipo_documento_id:
        return value
    
    try:
        from documenti.models import AttributoDefinizione
        
        # Cerca definizione attributo
        attr_def = AttributoDefinizione.objects.get(
            tipo_documento_id=tipo_documento_id,
            codice=campo_codice
        )
        
        # Ottieni scelte configurate
        choices = attr_def.scelte()  # [(value, label), ...]
        
        if not choices:
            return value
        
        value_lower = value.lower().strip()
        
        # 1. Match esatto sul valore (case-insensitive)
        for val, label in choices:
            if value_lower == val.lower():
                return val
        
        # 2. Match esatto sulla label (case-insensitive)
        for val, label in choices:
            if value_lower == label.lower():
                return val
        
        # 3. Match parziale: valore contiene label o viceversa
        for val, label in choices:
            if value_lower in label.lower() or label.lower() in value_lower:
                return val
        
        # 4. Match sulla prima parola significativa
        # Esempio: "ASSUNZIONE A TEMPO INDETERMINATO" → cerca "assunzione"
        first_word = value_lower.split()[0] if value_lower else ""
        if first_word:
            for val, label in choices:
                if first_word in label.lower() or label.lower().startswith(first_word):
                    return val
        
        # Nessun match: ritorna valore originale
        return value
        
    except Exception:
        # In caso di errore (AttributoDefinizione non trovata, etc.)
        # ritorna valore originale
        return value


def normalize_tipo_comunicazione_unilav(value: str) -> str:
    """
    Normalizza tipo comunicazione UNILAV.
    
    Input possibili: "Assunzione", "ASS", "assunzione", "ASSUNZIONE A TEMPO INDETERMINATO"
    Output: "ASS", "PRO", "TRA", "CES"
    """
    if not value:
        return ""
    
    value_lower = value.lower().strip()
    
    # Mapping completo
    mapping = {
        # Assunzione
        'ass': 'ASS',
        'assunzione': 'ASS',
        'nuova assunzione': 'ASS',
        'assunzione a tempo indeterminato': 'ASS',
        'assunzione a tempo determinato': 'ASS',
        
        # Proroga
        'pro': 'PRO',
        'proroga': 'PRO',
        'proroga contratto': 'PRO',
        'proroga rapporto': 'PRO',
        
        # Trasformazione
        'tra': 'TRA',
        'trasformazione': 'TRA',
        'trasformazione contratto': 'TRA',
        'trasformazione rapporto': 'TRA',
        
        # Cessazione
        'ces': 'CES',
        'cessazione': 'CES',
        'cessazione rapporto': 'CES',
        'licenziamento': 'CES',
        'dimissioni': 'CES',
        'risoluzione': 'CES',
    }
    
    # Cerca match esatto
    if value_lower in mapping:
        return mapping[value_lower]
    
    # Cerca match parziale (contiene)
    for key, code in mapping.items():
        if key in value_lower:
            return code
    
    # Fallback: se è già un codice valido, restituiscilo
    if value.upper() in ['ASS', 'PRO', 'TRA', 'CES']:
        return value.upper()
    
    # Default: ritorna valore originale
    return value


def normalize_sesso(value: str) -> str:
    """
    Normalizza campo sesso.
    
    Input: "Maschio", "M", "Femmina", "F", "MALE", "FEMALE"
    Output: "M" o "F"
    """
    if not value:
        return ""
    
    value_lower = value.lower().strip()
    
    if value_lower in ['m', 'maschio', 'male', 'uomo']:
        return 'M'
    elif value_lower in ['f', 'femmina', 'female', 'donna']:
        return 'F'
    
    # Fallback
    return value.upper()[:1]


def normalize_codice_fiscale(value: str) -> str:
    """
    Normalizza codice fiscale.
    
    - Rimuove spazi
    - Uppercase
    - Mantiene solo alfanumerici
    """
    if not value:
        return ""
    
    # Rimuovi spazi e caratteri non alfanumerici
    cf = re.sub(r'[^A-Za-z0-9]', '', value)
    
    # Uppercase
    cf = cf.upper()
    
    return cf


def normalize_partita_iva(value: str) -> str:
    """
    Normalizza partita IVA.
    
    - Rimuove spazi, punti, trattini
    - Mantiene solo numeri
    """
    if not value:
        return ""
    
    # Mantieni solo cifre
    piva = re.sub(r'\D', '', value)
    
    return piva


def normalize_cap(value: str) -> str:
    """
    Normalizza CAP.
    
    - Rimuove spazi
    - Pad a 5 cifre con zeri iniziali
    """
    if not value:
        return ""
    
    # Mantieni solo cifre
    cap = re.sub(r'\D', '', value)
    
    # Pad a 5 cifre
    cap = cap.zfill(5)
    
    return cap


def normalize_phone(value: str) -> str:
    """
    Normalizza numero di telefono.
    
    - Rimuove spazi, trattini, slash
    - Mantiene solo cifre e +
    """
    if not value:
        return ""
    
    # Rimuovi caratteri non numerici eccetto +
    phone = re.sub(r'[^\d+]', '', value)
    
    return phone


def normalize_email(value: str) -> str:
    """
    Normalizza email.
    
    - Lowercase
    - Trim spazi
    """
    if not value:
        return ""
    
    email = value.strip().lower()
    
    return email


def normalize_date_italian(value: str) -> Optional[str]:
    """
    Normalizza data da formato italiano (gg/mm/aaaa) a ISO (aaaa-mm-gg).
    
    Input: "15/03/2024", "15-03-2024", "15.03.2024"
    Output: "2024-03-15"
    """
    if not value:
        return None
    
    # Prova vari formati italiani
    formats = [
        r'(\d{1,2})[/-.](\d{1,2})[/-.](\d{4})',  # gg/mm/aaaa
        r'(\d{1,2})[/-.](\d{1,2})[/-.](\d{2})',   # gg/mm/aa
    ]
    
    for fmt in formats:
        match = re.match(fmt, value.strip())
        if match:
            day, month, year = match.groups()
            
            # Se anno è a 2 cifre, aggiungi 2000
            if len(year) == 2:
                year = '20' + year
            
            # Padding
            day = day.zfill(2)
            month = month.zfill(2)
            
            # Validazione base
            try:
                datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                return f"{year}-{month}-{day}"
            except ValueError:
                continue
    
    # Prova formato ISO già corretto
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        pass
    
    # Fallback: ritorna valore originale
    return value


def uppercase(value: str) -> str:
    """Converte in maiuscolo."""
    return value.upper() if value else ""


def lowercase(value: str) -> str:
    """Converte in minuscolo."""
    return value.lower() if value else ""


def title_case(value: str) -> str:
    """Converte in Title Case (prima lettera maiuscola di ogni parola)."""
    return value.title() if value else ""


def strip_whitespace(value: str) -> str:
    """Rimuove spazi all'inizio e alla fine."""
    return value.strip() if value else ""


def remove_extra_spaces(value: str) -> str:
    """Riduce spazi multipli a singolo spazio."""
    if not value:
        return ""
    return ' '.join(value.split())


def extract_numbers(value: str) -> str:
    """Estrae solo numeri dalla stringa."""
    if not value:
        return ""
    return re.sub(r'\D', '', value)


def extract_letters(value: str) -> str:
    """Estrae solo lettere dalla stringa."""
    if not value:
        return ""
    return re.sub(r'[^A-Za-z]', '', value)


# ============================================================
# REGISTRY - Mappa nome funzione → callable
# ============================================================

TRANSFORMATION_REGISTRY: dict[str, Callable[[str], str]] = {
    # Choice fields (generica)
    'normalize_choice_from_db': normalize_choice_from_db,
    
    # UNILAV specifiche
    'normalize_tipo_comunicazione_unilav': normalize_tipo_comunicazione_unilav,
    'normalize_sesso': normalize_sesso,
    
    # Validazione dati
    'normalize_codice_fiscale': normalize_codice_fiscale,
    'normalize_partita_iva': normalize_partita_iva,
    'normalize_cap': normalize_cap,
    'normalize_phone': normalize_phone,
    'normalize_email': normalize_email,
    'normalize_date_italian': normalize_date_italian,
    
    # Utilità generiche
    'uppercase': uppercase,
    'lowercase': lowercase,
    'title_case': title_case,
    'strip_whitespace': strip_whitespace,
    'remove_extra_spaces': remove_extra_spaces,
    'extract_numbers': extract_numbers,
    'extract_letters': extract_letters,
}


def get_transformation(name: str) -> Optional[Callable[[str], str]]:
    """
    Ottieni funzione di trasformazione dal registry.
    
    Args:
        name: Nome della funzione
        
    Returns:
        Callable o None se non trovata
    """
    return TRANSFORMATION_REGISTRY.get(name)


def apply_transformation(
    value: str, 
    transformation_name: str,
    campo_codice: str = None,
    tipo_documento_id: int = None
) -> str:
    """
    Applica trasformazione a un valore.
    
    Args:
        value: Valore da trasformare
        transformation_name: Nome della funzione di trasformazione
        campo_codice: Codice campo (per normalize_choice_from_db)
        tipo_documento_id: ID tipo documento (per normalize_choice_from_db)
        
    Returns:
        Valore trasformato, o valore originale se trasformazione non trovata
        
    Note:
        Per normalize_choice_from_db è necessario passare campo_codice e tipo_documento_id
    """
    if not transformation_name:
        return value
    
    transform_fn = get_transformation(transformation_name)
    if transform_fn:
        try:
            # Se la funzione è normalize_choice_from_db, passa metadata
            if transformation_name == 'normalize_choice_from_db':
                return transform_fn(value, campo_codice, tipo_documento_id)
            else:
                return transform_fn(value)
        except Exception as e:
            # In caso di errore, ritorna valore originale
            # TODO: loggare errore
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore trasformazione {transformation_name}: {e}")
            return value
    
    return value


def get_available_transformations() -> list[dict[str, str]]:
    """
    Ottieni lista trasformazioni disponibili per UI.
    
    Returns:
        Lista di dict con 'value' (nome funzione) e 'label' (descrizione)
    """
    return [
        # Choice Fields
        {'value': 'normalize_choice_from_db', 'label': '🔄 Normalizza da Scelte DB (Auto)', 'category': 'Choice Fields'},
        
        # UNILAV
        {'value': 'normalize_tipo_comunicazione_unilav', 'label': 'UNILAV - Tipo Comunicazione', 'category': 'UNILAV'},
        {'value': 'normalize_sesso', 'label': 'Normalizza Sesso (M/F)', 'category': 'Validazione'},
        
        # Validazione
        {'value': 'normalize_codice_fiscale', 'label': 'Normalizza Codice Fiscale', 'category': 'Validazione'},
        {'value': 'normalize_partita_iva', 'label': 'Normalizza Partita IVA', 'category': 'Validazione'},
        {'value': 'normalize_cap', 'label': 'Normalizza CAP', 'category': 'Validazione'},
        {'value': 'normalize_phone', 'label': 'Normalizza Telefono', 'category': 'Validazione'},
        {'value': 'normalize_email', 'label': 'Normalizza Email', 'category': 'Validazione'},
        {'value': 'normalize_date_italian', 'label': 'Data Italiana → ISO', 'category': 'Validazione'},
        
        # Utilità
        {'value': 'uppercase', 'label': 'MAIUSCOLO', 'category': 'Testo'},
        {'value': 'lowercase', 'label': 'minuscolo', 'category': 'Testo'},
        {'value': 'title_case', 'label': 'Title Case', 'category': 'Testo'},
        {'value': 'strip_whitespace', 'label': 'Rimuovi spazi', 'category': 'Testo'},
        {'value': 'remove_extra_spaces', 'label': 'Riduci spazi multipli', 'category': 'Testo'},
        {'value': 'extract_numbers', 'label': 'Estrai solo numeri', 'category': 'Estrazione'},
        {'value': 'extract_letters', 'label': 'Estrai solo lettere', 'category': 'Estrazione'},
    ]
