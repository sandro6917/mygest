"""
String Utilities - Funzioni per la manipolazione di stringhe
"""
import re
import unicodedata


def normalize_string(text):
    """
    Normalizza una stringa rimuovendo spazi extra e caratteri speciali.
    
    Args:
        text: Stringa da normalizzare
    
    Returns:
        str: Stringa normalizzata
    """
    if not text:
        return ""
    
    # Rimuove spazi multipli e fa strip
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def slugify_italian(text):
    """
    Crea uno slug URL-friendly da una stringa italiana.
    Gestisce caratteri accentati italiani.
    
    Args:
        text: Stringa da convertire in slug
    
    Returns:
        str: Slug (es: "Casa di Proprietà" -> "casa-di-proprieta")
    """
    if not text:
        return ""
    
    # Converti in minuscolo
    text = text.lower()
    
    # Sostituisci caratteri accentati italiani
    replacements = {
        'à': 'a', 'è': 'e', 'é': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'À': 'a', 'È': 'e', 'É': 'e', 'Ì': 'i', 'Ò': 'o', 'Ù': 'u'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Rimuovi caratteri non alfanumerici (tranne spazi e trattini)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    
    # Sostituisci spazi con trattini
    text = re.sub(r'\s+', '-', text)
    
    # Rimuovi trattini multipli
    text = re.sub(r'-+', '-', text)
    
    # Rimuovi trattini all'inizio e alla fine
    text = text.strip('-')
    
    return text


def remove_accents(text):
    """
    Rimuove tutti gli accenti da una stringa usando Unicode normalization.
    
    Args:
        text: Stringa con possibili accenti
    
    Returns:
        str: Stringa senza accenti
    """
    if not text:
        return ""
    
    # Normalizza in forma NFD (decomposed)
    nfd = unicodedata.normalize('NFD', text)
    # Rimuovi i caratteri di combining (accenti)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def truncate_string(text, max_length, suffix='...'):
    """
    Tronca una stringa alla lunghezza massima specificata.
    
    Args:
        text: Stringa da troncare
        max_length: Lunghezza massima (incluso suffisso)
        suffix: Suffisso da aggiungere se troncata (default: '...')
    
    Returns:
        str: Stringa troncata
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    return text[:max_length - len(suffix)] + suffix


def capitalize_words(text):
    """
    Capitalizza la prima lettera di ogni parola (title case).
    Gestisce correttamente articoli e preposizioni italiane.
    
    Args:
        text: Stringa da capitalizzare
    
    Returns:
        str: Stringa con ogni parola capitalizzata
    """
    if not text:
        return ""
    
    # Parole da non capitalizzare (articoli, preposizioni)
    lowercase_words = {'di', 'da', 'del', 'della', 'dei', 'degli', 'delle', 
                       'al', 'alla', 'ai', 'agli', 'alle', 'con', 'per', 
                       'su', 'in', 'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'una'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Prima parola sempre maiuscola
        if i == 0 or word.lower() not in lowercase_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    
    return ' '.join(result)


def extract_numbers(text):
    """
    Estrae tutti i numeri da una stringa.
    
    Args:
        text: Stringa contenente numeri
    
    Returns:
        list: Lista di stringhe numeriche trovate
    """
    if not text:
        return []
    
    return re.findall(r'\d+', text)


def clean_whitespace(text):
    """
    Rimuove spazi all'inizio/fine e normalizza spazi interni.
    
    Args:
        text: Stringa da pulire
    
    Returns:
        str: Stringa pulita
    """
    if not text:
        return ""
    
    # Rimuove spazi all'inizio/fine
    text = text.strip()
    
    # Sostituisce tabs e newline con spazi
    text = re.sub(r'[\t\n\r]+', ' ', text)
    
    # Rimuove spazi multipli
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text
