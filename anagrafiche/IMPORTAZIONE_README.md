# Importazione Anagrafiche - README Tecnico

## Architettura

### Componenti

1. **Form** (`forms.py`):
   - `ImportAnagraficaForm`: gestisce l'upload del file CSV

2. **View** (`views.py`):
   - `import_anagrafiche()`: elabora il CSV e genera il report
   - `facsimile_csv()`: genera un file CSV di esempio scaricabile

3. **Template** (`templates/anagrafiche/import_anagrafiche.html`):
   - Interfaccia utente per caricamento e visualizzazione report

4. **URL** (`urls.py`):
   - `/anagrafiche/import/` - Pagina di importazione
   - `/anagrafiche/facsimile-csv/` - Download esempio

### Flusso di Elaborazione

```
┌─────────────────┐
│  Upload CSV     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Decodifica File        │
│  (UTF-8 / Latin-1)      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Parse CSV              │
│  (DictReader, sep=';')  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Per ogni riga:         │
│  ┌──────────────────┐   │
│  │ Validazione Base │   │
│  └────────┬─────────┘   │
│           ▼             │
│  ┌──────────────────┐   │
│  │ Check Duplicati  │   │
│  └────────┬─────────┘   │
│           ▼             │
│  ┌──────────────────┐   │
│  │ Model.clean()    │   │
│  └────────┬─────────┘   │
│           ▼             │
│  ┌──────────────────┐   │
│  │ Model.save()     │   │
│  └──────────────────┘   │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Genera Report          │
│  - Importate            │
│  - Scartate con motivi  │
└─────────────────────────┘
```

## Validazioni Implementate

### Livello 1: Validazione Base (Pre-Model)

```python
# Campi obbligatori
- tipo in ['PF', 'PG']
- codice_fiscale presente

# Campi specifici per tipo
PF: nome, cognome
PG: ragione_sociale
```

### Livello 2: Check Duplicati

```python
# Univocità nel database
- codice_fiscale (sempre)
- partita_iva (se presente)
- pec (se presente)
```

### Livello 3: Validazione Model (Django)

```python
# Validatori custom
- validate_codice_fiscale()
- validate_piva()

# Model.clean()
- Coerenza campi per tipo
- Requisiti minimi

# Model.save()
- Normalizzazione dati
- Azzeramento campi non pertinenti
```

## Struttura Dati Report

### Formato Report Dictionary

```python
report = {
    "totale": int,           # Numero totale righe (escluso header)
    "num_importate": int,    # Conteggio importazioni riuscite
    "num_scartate": int,     # Conteggio scarti
    "importate": [
        {
            "riga": int,              # Numero riga nel CSV
            "nome": str,              # display_name()
            "codice_fiscale": str,    # CF dell'anagrafica
            "id": int                 # PK per link dettaglio
        },
        ...
    ],
    "scartate": [
        {
            "riga": int,              # Numero riga nel CSV
            "dati": str,              # Identificativo (nome/CF)
            "motivi": [str, ...]      # Lista errori
        },
        ...
    ]
}
```

## Gestione Errori

### Tipi di Errore e Gestione

| Errore | Livello | Gestione |
|--------|---------|----------|
| Campo obbligatorio mancante | Pre-validazione | Aggiunto a errori_riga, continua |
| Tipo non valido | Pre-validazione | Aggiunto a errori_riga, continua |
| Duplicato (CF/PIVA/PEC) | Database query | Aggiunto a scartate, continua |
| ValidationError (clean) | Model | Catturato, dettagli in scartate |
| Exception generica | Runtime | Catturato, messaggio in scartate |

### Esempio Gestione ValidationError

```python
try:
    anagrafica.full_clean()
    anagrafica.save()
    # Successo -> lista importate
except ValidationError as ve:
    # Estrazione errori multipli
    if hasattr(ve, 'message_dict'):
        for field, errors in ve.message_dict.items():
            errori_validazione.extend([f"{field}: {e}" for e in errors])
    else:
        errori_validazione.append(str(ve))
    # Aggiunto a scartate con motivi
```

## Personalizzazioni e Estensioni

### Aggiungere un Nuovo Campo

1. **Aggiornare il CSV header** in `facsimile_csv()`:
```python
header = [..., "nuovo_campo"]
```

2. **Leggere dal CSV** in `import_anagrafiche()`:
```python
nuovo_campo = row.get("nuovo_campo", "").strip()
```

3. **Validare (opzionale)**:
```python
if tipo == "PF" and not nuovo_campo:
    errori_riga.append("Campo 'nuovo_campo' obbligatorio per PF")
```

4. **Aggiungere al model**:
```python
anagrafica = Anagrafica(
    ...,
    nuovo_campo=nuovo_campo
)
```

### Aggiungere Validazione Custom

```python
# Esempio: validazione età minima per PF
if tipo == "PF":
    # Estrai data nascita da codice fiscale
    try:
        anno = int(codice_fiscale[6:8])
        if anno > 50:  # Logica specifica
            errori_riga.append("Età non valida")
    except:
        pass
```

### Importazione con Relazioni (Indirizzi)

Per estendere l'importazione agli indirizzi correlati:

```python
# Nel CSV aggiungere campi indirizzo
indirizzo_tipo = row.get("indirizzo_tipo", "").strip()
indirizzo_via = row.get("indirizzo_via", "").strip()
# ...

# Dopo save anagrafica
if indirizzo_via:
    from .models import Indirizzo
    Indirizzo.objects.create(
        anagrafica=anagrafica,
        tipo_indirizzo=indirizzo_tipo or "RESIDENZA",
        indirizzo=indirizzo_via,
        # ...altri campi
        principale=True
    )
```

## Testing

### Test Unitari Raccomandati

```python
# tests/test_import_anagrafiche.py

def test_import_valido_pf():
    """Test importazione persona fisica valida"""
    
def test_import_valido_pg():
    """Test importazione persona giuridica valida"""
    
def test_import_cf_duplicato():
    """Test scarto per codice fiscale duplicato"""
    
def test_import_campi_obbligatori_mancanti():
    """Test scarto per campi obbligatori vuoti"""
    
def test_import_tipo_non_valido():
    """Test scarto per tipo errato"""
    
def test_import_encoding_latin1():
    """Test gestione encoding Latin-1"""
    
def test_import_bom_utf8():
    """Test gestione BOM UTF-8"""
    
def test_report_structure():
    """Test struttura report"""
```

### Test di Integrazione

```python
def test_import_workflow_completo():
    """Test workflow completo: upload -> elaborazione -> report"""
    csv_content = "tipo;...\\nPF;Mario;Rossi;..."
    file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'))
    response = client.post('/anagrafiche/import/', {'file': file})
    assert response.status_code == 200
    assert 'report' in response.context
    assert response.context['report']['num_importate'] == 1
```

## Performance

### Ottimizzazioni Implementate

1. **Query di Check Duplicati**: Una query per campo (CF, PIVA, PEC)
2. **Transazioni**: Non usate (permette partial import)
3. **Bulk Operations**: Non implementate (privilegia tracciabilità)

### Raccomandazioni per Grandi Volumi

Per importazioni > 1000 record:

```python
# Opzione 1: Bulk create con validazione preventiva
anagrafiche_valide = []
for row in reader:
    # validazione...
    if valida:
        anagrafiche_valide.append(Anagrafica(**dati))

# Bulk create (disabilita validazione model)
Anagrafica.objects.bulk_create(anagrafiche_valide, ignore_conflicts=True)

# Opzione 2: Batch processing
from django.db import transaction
batch_size = 100
for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    with transaction.atomic():
        # processa batch
```

**Nota**: L'implementazione attuale privilegia:
- Tracciabilità dettagliata degli errori
- Report preciso riga per riga
- Validazione completa per ogni record

## Logging

### Log Levels Consigliati

```python
import logging
logger = logging.getLogger(__name__)

# INFO: importazione avviata/completata
logger.info(f"Importazione avviata: {file.name}")
logger.info(f"Importazione completata: {num_importate} ok, {num_scartate} scarti")

# WARNING: righe scartate
logger.warning(f"Riga {riga_numero} scartata: {motivi}")

# ERROR: errori critici
logger.error(f"Errore critico durante importazione: {e}")
```

## Sicurezza

### Validazioni di Sicurezza Implementate

1. **Upload File**:
   - Accept solo `.csv`
   - Validazione formato in form

2. **Parsing**:
   - Gestione encoding sicura (try/except)
   - Limite implicito dimensione file (Django settings)

3. **Database**:
   - Validazioni model Django
   - Constraint univocità
   - No SQL injection (uso ORM)

### Considerazioni Ulteriori

```python
# Limite dimensione file (settings.py)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

# Limite numero righe (view)
MAX_ROWS = 10000
if riga_numero > MAX_ROWS:
    messages.error(request, "Troppi record, massimo 10000 righe")
    break
```

## Maintenance

### Checklist Manutenzione

- [ ] Verificare compatibilità encoding con nuove versioni Python/Django
- [ ] Monitorare performance con dataset crescenti
- [ ] Aggiornare esempi CSV con nuovi campi model
- [ ] Verificare validatori CF/PIVA con aggiornamenti normativi
- [ ] Testare con diverse versioni Excel/LibreOffice
- [ ] Documentare nuovi motivi di scarto che emergono dall'uso

### Troubleshooting Comune

**Problema**: "UnicodeDecodeError"
- Verifica encoding file
- Aggiungi supporto per altri encoding se necessario

**Problema**: "Lentezza con file grandi"
- Implementa batching
- Considera task asincrono (Celery)

**Problema**: "Report incompleto"
- Verifica dimensione response
- Considera paginazione o esportazione report

## Riferimenti

- Django CSV Processing: https://docs.djangoproject.com/en/stable/howto/outputting-csv/
- Python CSV Module: https://docs.python.org/3/library/csv.html
- Codice Fiscale Italiano: https://it.wikipedia.org/wiki/Codice_fiscale
- Partita IVA: https://www.agenziaentrate.gov.it/

## Autore e Versione

- **Versione**: 1.0
- **Data**: Dicembre 2025
- **Compatibilità**: Django 4.x+, Python 3.8+
