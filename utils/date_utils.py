"""
Date Utilities - Funzioni per la gestione di date
"""
from datetime import datetime, date, timedelta
from dateutil.parser import parse as dateutil_parse
from dateutil.relativedelta import relativedelta


def parse_date_flexible(date_str):
    """
    Parsing flessibile di stringhe data in vari formati.
    
    Args:
        date_str: Stringa rappresentante una data
    
    Returns:
        date: Oggetto date, o None se parsing fallisce
    
    Supporta formati:
        - DD/MM/YYYY
        - DD-MM-YYYY
        - YYYY-MM-DD (ISO)
        - DD/MM/YY
        - E molti altri tramite dateutil
    """
    if not date_str:
        return None
    
    if isinstance(date_str, (date, datetime)):
        return date_str if isinstance(date_str, date) else date_str.date()
    
    try:
        # Prova con dateutil (molto flessibile)
        parsed = dateutil_parse(date_str, dayfirst=True)
        return parsed.date()
    except Exception:
        return None


def format_date_italian(date_obj, include_weekday=False):
    """
    Formatta una data in formato italiano leggibile.
    
    Args:
        date_obj: Oggetto date o datetime
        include_weekday: Se True, include il giorno della settimana
    
    Returns:
        str: Data formattata (es: "20 novembre 2025" o "venerdì 20 novembre 2025")
    """
    if not date_obj:
        return ""
    
    if isinstance(date_obj, str):
        date_obj = parse_date_flexible(date_obj)
        if not date_obj:
            return ""
    
    months = {
        1: 'gennaio', 2: 'febbraio', 3: 'marzo', 4: 'aprile',
        5: 'maggio', 6: 'giugno', 7: 'luglio', 8: 'agosto',
        9: 'settembre', 10: 'ottobre', 11: 'novembre', 12: 'dicembre'
    }
    
    weekdays = {
        0: 'lunedì', 1: 'martedì', 2: 'mercoledì', 3: 'giovedì',
        4: 'venerdì', 5: 'sabato', 6: 'domenica'
    }
    
    day = date_obj.day
    month = months[date_obj.month]
    year = date_obj.year
    
    result = f"{day} {month} {year}"
    
    if include_weekday:
        weekday = weekdays[date_obj.weekday()]
        result = f"{weekday} {result}"
    
    return result


def get_fiscal_year(date_obj=None):
    """
    Restituisce l'anno fiscale per una data.
    Anno fiscale italiano: inizia il 1° gennaio, termina il 31 dicembre.
    
    Args:
        date_obj: Data di riferimento (default: oggi)
    
    Returns:
        int: Anno fiscale
    """
    if date_obj is None:
        date_obj = date.today()
    
    if isinstance(date_obj, str):
        date_obj = parse_date_flexible(date_obj)
    
    return date_obj.year


def get_quarter(date_obj=None):
    """
    Restituisce il trimestre per una data (1-4).
    
    Args:
        date_obj: Data di riferimento (default: oggi)
    
    Returns:
        int: Numero del trimestre (1, 2, 3, 4)
    """
    if date_obj is None:
        date_obj = date.today()
    
    if isinstance(date_obj, str):
        date_obj = parse_date_flexible(date_obj)
    
    return (date_obj.month - 1) // 3 + 1


def add_business_days(start_date, days):
    """
    Aggiunge giorni lavorativi a una data (esclude sabato e domenica).
    
    Args:
        start_date: Data di partenza
        days: Numero di giorni lavorativi da aggiungere
    
    Returns:
        date: Data risultante
    """
    if isinstance(start_date, str):
        start_date = parse_date_flexible(start_date)
    
    current_date = start_date
    days_added = 0
    
    while days_added < days:
        current_date += timedelta(days=1)
        # 0-4 = lunedì-venerdì, 5-6 = sabato-domenica
        if current_date.weekday() < 5:
            days_added += 1
    
    return current_date


def get_date_range(start_date, end_date):
    """
    Genera una lista di date tra due date (incluse).
    
    Args:
        start_date: Data iniziale
        end_date: Data finale
    
    Returns:
        list: Lista di oggetti date
    """
    if isinstance(start_date, str):
        start_date = parse_date_flexible(start_date)
    if isinstance(end_date, str):
        end_date = parse_date_flexible(end_date)
    
    if not start_date or not end_date:
        return []
    
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def is_business_day(date_obj):
    """
    Verifica se una data è un giorno lavorativo (non sabato/domenica).
    Non considera festività.
    
    Args:
        date_obj: Data da verificare
    
    Returns:
        bool: True se giorno lavorativo
    """
    if isinstance(date_obj, str):
        date_obj = parse_date_flexible(date_obj)
    
    if not date_obj:
        return False
    
    return date_obj.weekday() < 5


def get_month_boundaries(date_obj=None):
    """
    Restituisce primo e ultimo giorno del mese.
    
    Args:
        date_obj: Data di riferimento (default: oggi)
    
    Returns:
        tuple: (primo_giorno, ultimo_giorno) come oggetti date
    """
    if date_obj is None:
        date_obj = date.today()
    
    if isinstance(date_obj, str):
        date_obj = parse_date_flexible(date_obj)
    
    first_day = date_obj.replace(day=1)
    
    # Ultimo giorno = primo giorno del mese successivo - 1 giorno
    if date_obj.month == 12:
        last_day = date_obj.replace(day=31)
    else:
        next_month = date_obj.replace(month=date_obj.month + 1, day=1)
        last_day = next_month - timedelta(days=1)
    
    return first_day, last_day


def get_year_boundaries(year=None):
    """
    Restituisce primo e ultimo giorno dell'anno.
    
    Args:
        year: Anno (default: anno corrente)
    
    Returns:
        tuple: (primo_gennaio, trentuno_dicembre) come oggetti date
    """
    if year is None:
        year = date.today().year
    
    first_day = date(year, 1, 1)
    last_day = date(year, 12, 31)
    
    return first_day, last_day


def age_in_years(birth_date, reference_date=None):
    """
    Calcola l'età in anni tra due date.
    
    Args:
        birth_date: Data di nascita
        reference_date: Data di riferimento (default: oggi)
    
    Returns:
        int: Età in anni
    """
    if isinstance(birth_date, str):
        birth_date = parse_date_flexible(birth_date)
    
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, str):
        reference_date = parse_date_flexible(reference_date)
    
    if not birth_date or not reference_date:
        return 0
    
    age = reference_date.year - birth_date.year
    
    # Aggiusta se il compleanno non è ancora avvenuto quest'anno
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age
