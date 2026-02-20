# Utils - Funzioni di Utilità Comuni

Raccolta di funzioni di utilità comuni utilizzabili in tutto il progetto MyGest.

## Struttura

```
utils/
├── __init__.py          # Esportazioni pubbliche
├── file_utils.py        # Gestione file e storage
├── string_utils.py      # Manipolazione stringhe
├── date_utils.py        # Gestione date
└── README.md           # Questa documentazione
```

## File Utilities (`file_utils.py`)

### `get_unique_filename(storage, destination_path)`
Genera un nome file unico aggiungendo suffissi numerici progressivi.
```python
from utils.file_utils import get_unique_filename

# Se esiste già documento.pdf, restituisce documento_1.pdf
unique_path = get_unique_filename(storage, "archivio/documento.pdf")
```

### `move_to_orphaned(storage, source_path, orphaned_dir="FileNonAssociati")`
Sposta un file nella cartella dei file orfani senza sovrascrivere.
```python
from utils.file_utils import move_to_orphaned

destination = move_to_orphaned(storage, "path/to/file.pdf")
# File spostato in FileNonAssociati/file.pdf (o file_1.pdf se esiste già)
```

### `ensure_directory(path)`
Crea una directory se non esiste.
```python
from utils.file_utils import ensure_directory

ensure_directory("/mnt/archivio/nuova_cartella")
```

### `get_file_extension(filename)`
Estrae l'estensione da un nome file.
```python
from utils.file_utils import get_file_extension

ext = get_file_extension("documento.pdf")  # "pdf"
```

### `format_file_size(size_bytes)`
Formatta dimensioni file in formato leggibile.
```python
from utils.file_utils import format_file_size

size = format_file_size(1536000)  # "1.5 MB"
```

## String Utilities (`string_utils.py`)

### `normalize_string(text)`
Normalizza stringhe rimuovendo spazi extra.
```python
from utils.string_utils import normalize_string

text = normalize_string("  Troppi   spazi  ")  # "Troppi spazi"
```

### `slugify_italian(text)`
Crea slug URL-friendly gestendo caratteri italiani.
```python
from utils.string_utils import slugify_italian

slug = slugify_italian("Casa di Proprietà")  # "casa-di-proprieta"
```

### `remove_accents(text)`
Rimuove accenti da una stringa.
```python
from utils.string_utils import remove_accents

text = remove_accents("àèéìòù")  # "aeeiou"
```

### `truncate_string(text, max_length, suffix='...')`
Tronca stringa alla lunghezza massima.
```python
from utils.string_utils import truncate_string

short = truncate_string("Testo molto lungo", 10)  # "Testo m..."
```

### `capitalize_words(text)`
Capitalizza parole gestendo articoli italiani.
```python
from utils.string_utils import capitalize_words

title = capitalize_words("la casa di mario")  # "La Casa di Mario"
```

### `extract_numbers(text)`
Estrae numeri da una stringa.
```python
from utils.string_utils import extract_numbers

nums = extract_numbers("Doc123 del 2024")  # ['123', '2024']
```

### `clean_whitespace(text)`
Pulisce e normalizza spazi bianchi.
```python
from utils.string_utils import clean_whitespace

clean = clean_whitespace("  Testo\ncon\t\ttabs  ")  # "Testo con tabs"
```

## Date Utilities (`date_utils.py`)

### `parse_date_flexible(date_str)`
Parsing flessibile di stringhe data in vari formati.
```python
from utils.date_utils import parse_date_flexible

date1 = parse_date_flexible("20/11/2025")
date2 = parse_date_flexible("2025-11-20")
date3 = parse_date_flexible("20-11-25")
```

### `format_date_italian(date_obj, include_weekday=False)`
Formatta date in italiano leggibile.
```python
from utils.date_utils import format_date_italian
from datetime import date

text = format_date_italian(date(2025, 11, 20))
# "20 novembre 2025"

text = format_date_italian(date(2025, 11, 20), include_weekday=True)
# "giovedì 20 novembre 2025"
```

### `get_fiscal_year(date_obj=None)`
Restituisce anno fiscale per una data.
```python
from utils.date_utils import get_fiscal_year

year = get_fiscal_year()  # Anno corrente
```

### `get_quarter(date_obj=None)`
Restituisce trimestre (1-4) per una data.
```python
from utils.date_utils import get_quarter
from datetime import date

quarter = get_quarter(date(2025, 5, 15))  # 2
```

### `add_business_days(start_date, days)`
Aggiunge giorni lavorativi escludendo weekend.
```python
from utils.date_utils import add_business_days
from datetime import date

# Aggiunge 5 giorni lavorativi
new_date = add_business_days(date(2025, 11, 17), 5)
```

### `get_date_range(start_date, end_date)`
Genera lista di date tra due estremi.
```python
from utils.date_utils import get_date_range
from datetime import date

dates = get_date_range(date(2025, 11, 1), date(2025, 11, 5))
# [date(2025,11,1), date(2025,11,2), ..., date(2025,11,5)]
```

### `is_business_day(date_obj)`
Verifica se una data è un giorno lavorativo.
```python
from utils.date_utils import is_business_day
from datetime import date

is_working = is_business_day(date(2025, 11, 20))  # True (giovedì)
is_working = is_business_day(date(2025, 11, 23))  # False (sabato)
```

### `get_month_boundaries(date_obj=None)`
Restituisce primo e ultimo giorno del mese.
```python
from utils.date_utils import get_month_boundaries

first, last = get_month_boundaries()
# (date(2025, 11, 1), date(2025, 11, 30))
```

### `get_year_boundaries(year=None)`
Restituisce primo e ultimo giorno dell'anno.
```python
from utils.date_utils import get_year_boundaries

first, last = get_year_boundaries(2025)
# (date(2025, 1, 1), date(2025, 12, 31))
```

### `age_in_years(birth_date, reference_date=None)`
Calcola età in anni.
```python
from utils.date_utils import age_in_years
from datetime import date

age = age_in_years(date(1990, 5, 15), date(2025, 11, 20))  # 35
```

## Come Aggiungere Nuove Utilities

1. Aggiungi la funzione nel file tematico appropriato
2. Aggiungi docstring completa con esempi
3. Esporta la funzione in `__init__.py`
4. Aggiorna questo README con la documentazione
5. Aggiungi test unitari se necessario

## Best Practices

- **Funzioni pure**: Preferire funzioni senza effetti collaterali
- **Type hints**: Usare type hints per parametri e return
- **Docstring**: Documentare sempre con esempi
- **Error handling**: Gestire eccezioni e casi edge
- **Logging**: Loggare errori ma non info in utilities
- **Testing**: Testare casi normali e edge cases

## Dipendenze

- `python-dateutil`: Per parsing flessibile date (già in requirements.txt)
- Django storage API per file utilities

## Esempi di Uso Combinato

```python
from utils import slugify_italian, format_date_italian, get_unique_filename
from datetime import date

# Crea slug per documento
title = "Fattura di Marzo 2025"
slug = slugify_italian(title)  # "fattura-di-marzo-2025"

# Formatta data per visualizzazione
doc_date = date(2025, 3, 15)
formatted = format_date_italian(doc_date)  # "15 marzo 2025"

# Genera nome file unico
filename = get_unique_filename(storage, f"{slug}.pdf")
```

## Note

- Le utility sono **stateless** e non dipendono dal database
- Sono **thread-safe** e possono essere usate in task asincroni
- Gestiscono **None** e valori vuoti in modo sicuro
- Usano logging standard di Python per errori
