# Codici Tributo F24

Sistema per gestire l'elenco aggiornato dei codici tributo utilizzabili nel modello F24.

## Modello Database

Il modello `CodiceTributoF24` contiene i seguenti campi:

- **codice**: Codice identificativo del tributo (es: 1001, 1040, DM10)
- **sezione**: Sezione del modello F24 (Erario, INPS, Regioni, IMU, INAIL, Accise, Altri Enti)
- **descrizione**: Descrizione completa del tributo
- **causale**: Causale/sigla breve del tributo
- **periodicita**: Frequenza del versamento (mensile, trimestrale, annuale, ecc.)
- **note**: Informazioni aggiuntive e note operative
- **attivo**: Flag per indicare se il codice è ancora utilizzabile
- **data_inizio_validita**: Data da cui il codice è valido
- **data_fine_validita**: Data fino a cui il codice è valido (per codici obsoleti)

## Utilizzo tramite Django Admin

Accedi a `/admin/scadenze/codicetributof24/` per:

- **Visualizzare** l'elenco completo dei codici tributo
- **Filtrare** per sezione, periodicità e stato attivo
- **Cercare** per codice, descrizione o causale
- **Creare/Modificare** singoli codici tributo
- **Attivare/Disattivare** in blocco tramite actions

### Colonne nell'elenco

- Codice
- Sezione F24
- Descrizione (primi 50 caratteri)
- Causale
- Periodicità
- Attivo (✓/✗)
- Valido oggi (✓/✗) - controlla anche le date di validità

## Caricamento da File

### Comando Management

```bash
python manage.py carica_codici_tributo_f24 <file.csv|file.json>
```

### Opzioni

- `--update`: Aggiorna i codici esistenti invece di saltarli
- `--clear`: Elimina tutti i codici esistenti prima di caricare i nuovi

### Esempi

```bash
# Carica i codici di base (solo creazione)
python manage.py carica_codici_tributo_f24 scripts/codici_tributo_f24_base.json

# Aggiorna tutti i codici esistenti
python manage.py carica_codici_tributo_f24 scripts/codici_tributo_f24_base.json --update

# Ricarica completamente da zero
python manage.py carica_codici_tributo_f24 scripts/codici_tributo_f24_base.json --clear

# Usa un file CSV personalizzato
python manage.py carica_codici_tributo_f24 /path/to/nuovi_codici.csv --update
```

## Formato File JSON

```json
[
  {
    "codice": "1001",
    "sezione": "erario",
    "descrizione": "Ritenute su redditi da lavoro dipendente e assimilati",
    "causale": "Ritenute lavoro dipendente",
    "periodicita": "mensile",
    "note": "Da versare entro il 16 del mese successivo",
    "attivo": true,
    "data_inizio_validita": null,
    "data_fine_validita": null
  }
]
```

## Formato File CSV

```csv
codice,sezione,descrizione,causale,periodicita,note,attivo,data_inizio_validita,data_fine_validita
1001,erario,Ritenute su redditi da lavoro dipendente e assimilati,Ritenute lavoro dipendente,mensile,Da versare entro il 16 del mese successivo,true,,
```

**Note CSV:**
- La prima riga deve contenere le intestazioni
- Il campo `attivo` accetta: true/false, 1/0, si/no, yes/no
- Le date devono essere in formato YYYY-MM-DD
- I campi vuoti vengono interpretati come NULL

## Valori per Sezione

- `erario` - Erario (tributi statali)
- `inps` - INPS (contributi previdenziali)
- `regioni` - Regioni (addizionali regionali)
- `imu` - IMU e altri tributi locali
- `inail` - INAIL (premi assicurativi)
- `accise` - Accise
- `altri` - Altri enti previdenziali

## Codici Precaricati

Il sistema include 20 codici tributo di base:

### Erario
- 1001 - Ritenute lavoro dipendente
- 1040 - Ritenute lavoro autonomo
- 6001 - Ritenute provvigioni
- 4001 - IVA mensile
- 6099 - Acconto IVA
- 4034 - Saldo IVA
- 2003 - IRPEF prima rata acconto
- 2004 - IRPEF seconda rata acconto
- 4033 - IRPEF saldo

### INPS
- DM10 - Contributi dipendenti
- AP23 - Contributi artigiani/commercianti saldo
- AP53 - Contributi artigiani/commercianti acconto

### IMU e Tributi Locali
- 3800 - IMU
- 3850 - IMU interessi
- 3851 - IMU sanzioni
- 3918 - TASI (obsoleto dal 2020)
- 3944 - TARI

### Altri
- KK00 - Premi INAIL (INAIL)
- 3813 - Addizionale regionale saldo (Regioni)
- 3812 - Addizionale regionale acconto (Regioni)

## Mantenimento Aggiornato

### Aggiornamento Periodico

1. **Verifica fonti ufficiali**: Agenzia delle Entrate, INPS, enti locali
2. **Prepara file di aggiornamento**: JSON o CSV con i nuovi/modificati codici
3. **Esegui import con --update**: Aggiorna i codici esistenti
4. **Verifica in admin**: Controlla che i dati siano corretti

### Scraper Automatico

Sono disponibili due script per scaricare automaticamente i codici tributo:

#### 1. Scraper Base (senza JavaScript)
```bash
python scripts/scraper_codici_tributo.py --format both
```

**Caratteristiche:**
- Non richiede dipendenze aggiuntive (solo requests, beautifulsoup4)
- Include dataset manuale di backup con 23+ codici comuni
- Tenta scraping da fonti alternative
- Output in CSV e/o JSON

**Limitazioni:**
- Non può accedere a pagine con JavaScript dinamico (es: sito AdE)
- Dataset limitato alle fonti statiche disponibili

#### 2. Scraper Avanzato (con Selenium)
```bash
# Prima installa le dipendenze
pip install selenium webdriver-manager

# Poi esegui lo scraper
python scripts/scraper_codici_tributo_selenium.py
```

**Caratteristiche:**
- Gestisce pagine JavaScript dinamiche
- Può accedere al sito ufficiale dell'Agenzia delle Entrate
- Download automatico di ChromeDriver
- Modalità headless (senza interfaccia grafica)

**Requisiti:**
- Chrome o Chromium installato
- Connessione internet stabile

#### Uso Consigliato

```bash
# 1. Prova prima lo scraper avanzato (se disponibile)
python scripts/scraper_codici_tributo_selenium.py

# 2. Carica i dati nel database
python manage.py carica_codici_tributo_f24 scripts/codici_tributo_f24_selenium_*.json --update

# 3. Se Selenium non disponibile, usa i dati manuali
python scripts/scraper_codici_tributo.py --format json
python manage.py carica_codici_tributo_f24 scripts/codici_tributo_f24_*.json --update
```

### Gestione Codici Obsoleti

Per codici tributo non più validi:

1. **Non eliminare**: Mantieni lo storico
2. **Disattiva**: Imposta `attivo = False`
3. **Imposta date validità**: Specifica `data_fine_validita`

Esempio:
```json
{
  "codice": "3918",
  "attivo": false,
  "data_inizio_validita": "2014-01-01",
  "data_fine_validita": "2019-12-31"
}
```

## API (Futuro)

Sarà possibile esporre un'API REST per:
- Ricerca codici tributo
- Filtro per sezione e periodicità
- Verifica validità
- Autocomplete nei form

## Integrazione con Scadenze

Il modello è integrato nell'app `scadenze` perché i codici tributo F24 sono utilizzati principalmente per:

- Scadenze fiscali periodiche
- Promemoria versamenti
- Gestione adempimenti tributari

In futuro sarà possibile collegare direttamente le scadenze ai codici tributo per:
- Compilazione automatica F24
- Calcolo importi dovuti
- Tracciamento versamenti effettuati
