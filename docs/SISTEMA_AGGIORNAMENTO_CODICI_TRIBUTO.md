# 🔄 Sistema Automatico Aggiornamento Codici Tributo F24

## Panoramica

Sistema completo per scaricare e aggiornare automaticamente i codici tributo F24 dal **sito ufficiale dell'Agenzia delle Entrate**.

### Fonti Ufficiali

- 📋 **Codici Erariali e Regionali**: Aggiornata 11/11/2025
- 🏘️ **Tributi Locali** (IMU, TASI, TARI): Aggiornata 28/10/2025  
- 💼 **INPS ed Enti Previdenziali**: Aggiornata 20/10/2025

**Link:** https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24

## Componenti del Sistema

### 1. Scraper Python (`scripts/scraper_ade_ufficiale.py`)

Script autonomo che scarica i codici tributo dalle pagine HTML dell'ADE.

**Caratteristiche:**
- ✅ Parsing intelligente delle tabelle HTML
- ✅ Pulizia e normalizzazione dei dati
- ✅ Identificazione automatica sezione (erario, inps, imu, etc.)
- ✅ Rilevamento codici obsoleti
- ✅ Export CSV/JSON
- ✅ Aggiornamento database Django

**Uso:**

```bash
# Scarica e esporta in CSV/JSON (default)
python scripts/scraper_ade_ufficiale.py

# Aggiorna il database Django
python scripts/scraper_ade_ufficiale.py --update-db

# Tutte le opzioni
python scripts/scraper_ade_ufficiale.py --update-db --export-csv --export-json --verbose

# Solo export CSV
python scripts/scraper_ade_ufficiale.py --export-csv

# Output dettagliato
python scripts/scraper_ade_ufficiale.py --verbose
```

### 2. Django Management Command

Command Django per integrare lo scraper nel sistema.

**Uso:**

```bash
# Aggiornamento standard
python manage.py aggiorna_codici_tributo

# Dry run (simula senza modificare il DB)
python manage.py aggiorna_codici_tributo --dry-run

# Forza aggiornamento anche se recente
python manage.py aggiorna_codici_tributo --force

# Con export CSV/JSON
python manage.py aggiorna_codici_tributo --export

# Output dettagliato
python manage.py aggiorna_codici_tributo --verbose
```

### 3. Task Celery (Opzionale)

Automazione completa con scheduling.

**Configurazione** in `mygest/settings.py`:

```python
# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    # Aggiornamento automatico ogni lunedì alle 3:00
    'aggiorna-codici-tributo': {
        'task': 'scadenze.tasks.aggiorna_codici_tributo_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
    },
    
    # Verifica codici obsoleti ogni giorno alle 8:00
    'verifica-codici-obsoleti': {
        'task': 'scadenze.tasks.verifica_codici_obsoleti_task',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

**Uso manuale:**

```python
# Django shell
from scadenze.tasks import aggiorna_codici_tributo_task

# Esegui subito
aggiorna_codici_tributo_task.delay()

# Con opzioni
aggiorna_codici_tributo_task.delay(force=True, export=True)
```

### 4. Cron Job

Per sistemi senza Celery, usa cron:

```bash
# Edita crontab
crontab -e

# Aggiungi (ogni lunedì alle 3:00 AM)
0 3 * * 1 cd /home/sandro/mygest && source venv/bin/activate && python manage.py aggiorna_codici_tributo --force > /tmp/codici_tributo_update.log 2>&1
```

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  AGENZIA DELLE ENTRATE                       │
│  https://www.agenziaentrate.gov.it/portale/...              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP GET + BeautifulSoup
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            ScraperADEUfficiale (Python)                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 1. fetch_page() - Scarica HTML                   │       │
│  │ 2. estrai_codici_da_tabella() - Parse HTML       │       │
│  │ 3. pulisci_testo() - Normalizza dati             │       │
│  │ 4. Identifica sezione automaticamente            │       │
│  └──────────────────────────────────────────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐   ┌──────────┐
    │   CSV   │    │  JSON   │   │ Database │
    │  Export │    │ Export  │   │  Django  │
    └─────────┘    └─────────┘   └──────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  CodiceTributoF24Model   │
                         │  - codice                │
                         │  - sezione               │
                         │  - descrizione           │
                         │  - causale               │
                         │  - attivo                │
                         └──────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │    REST API              │
                         │ /api/v1/comunicazioni/   │
                         │   codici-tributo/        │
                         └──────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  React Autocomplete UI   │
                         └──────────────────────────┘
```

## Flusso di Aggiornamento

### Step by Step

1. **Trigger** (Manuale, Cron, o Celery Beat)
   ```bash
   python manage.py aggiorna_codici_tributo
   ```

2. **Scraping**
   - Connessione a www.agenziaentrate.gov.it
   - Download pagine HTML delle tabelle
   - Parsing con BeautifulSoup

3. **Estrazione Dati**
   - Identifica tabelle nelle pagine
   - Estrae headers per capire struttura
   - Parse righe e celle
   - Pulisce testo (spazi, caratteri speciali)

4. **Normalizzazione**
   - Validazione codice (lunghezza, formato)
   - Validazione descrizione (lunghezza minima)
   - Identificazione sezione automatica
   - Rilevamento codici obsoleti (keywords)

5. **Aggiornamento Database**
   - `update_or_create()` per ogni codice
   - Se esiste: aggiorna descrizione/causale/attivo
   - Se nuovo: crea record

6. **Export** (opzionale)
   - CSV: `scripts/codici_tributo_ade.csv`
   - JSON: `scripts/codici_tributo_ade.json`

7. **Notifiche**
   - Email agli admin (se errori)
   - Log dettagliati
   - Statistiche finali

## Gestione Codici Obsoleti

### Identificazione Automatica

Il sistema rileva codici obsoleti cercando parole chiave:

```python
parole_obsoleto = [
    'soppresso', 
    'abolito', 
    'non più', 
    'cessato', 
    'dismesso', 
    'abrogato'
]
```

### Esempi

- ✅ Attivo: "1001 - Ritenute su redditi da lavoro dipendente"
- ❌ Obsoleto: "TASI - Tassa servizi indivisibili (abolita dal 2020)"

### Comportamento

- Codici obsoleti → `attivo=False` nel DB
- API filtra solo `attivo=True` per default
- UI mostra warning ⚠️ se selezionato codice obsoleto

## Sezioni Gestite

### ERARIO (Tributi Erariali)

Codici per:
- Ritenute (1001, 1002, 1012, 1040, etc.)
- IVA (6099, 6001, etc.)
- Imposte dirette (4001, 4033, etc.)
- Addizionali comunali/regionali

**Esempi:**
```
1001 - Ritenute su redditi da lavoro dipendente
6099 - IVA - Versamento trimestrale
4001 - IRPEF - Acconto prima rata
```

### REGIONI (Tributi Regionali)

Codici per:
- IRAP
- Addizionali regionali
- Tributi specifici regionali

**Esempi:**
```
3801 - IRAP - Saldo
3843 - Addizionale regionale IRPEF
```

### IMU (Tributi Comunali)

Codici per:
- IMU (Imposta Municipale Unica)
- TASI (abolita)
- TARI
- Altri tributi locali

**Esempi:**
```
3800 - IMU - Abitazione principale
3847 - IMU - Altri fabbricati
3944 - TARI - Tassa rifiuti
```

### INPS (Contributi Previdenziali)

Codici per:
- Contributi gestione separata
- Artigiani e commercianti
- Contributi previdenziali dipendenti

**Esempi:**
```
PXX - Gestione separata INPS
AP23 - Artigiani e commercianti - Saldo
DM10 - Contributi previdenziali dipendenti
```

### INAIL (Premi Assicurativi)

Codici per premi assicurativi INAIL.

### ACCISE (Prodotti Energetici)

Codici per accise su prodotti energetici.

## Formato Dati

### Struttura Record

```json
{
  "codice": "1001",
  "sezione": "erario",
  "descrizione": "Ritenute su redditi da lavoro dipendente e assimilati",
  "causale": "Ritenute lavoro dipendente",
  "periodicita": "Mensile",
  "attivo": true,
  "fonte": "ADE",
  "data_aggiornamento": "2025-11-25"
}
```

### CSV Export

```csv
codice,sezione,descrizione,causale,periodicita,attivo,fonte,data_aggiornamento
1001,erario,Ritenute su redditi da lavoro dipendente...,Ritenute lavoro dipendente,Mensile,true,ADE,2025-11-25
6099,erario,IVA - Versamento trimestrale,IVA trimestrale,Trimestrale,true,ADE,2025-11-25
```

### JSON Export

```json
{
  "metadata": {
    "fonte": "Agenzia delle Entrate",
    "url": "https://www.agenziaentrate.gov.it",
    "data_scaricamento": "2025-11-25T10:30:00",
    "totale_codici": 250
  },
  "codici": [
    {
      "codice": "1001",
      "sezione": "erario",
      "descrizione": "Ritenute su redditi da lavoro dipendente e assimilati",
      "causale": "Ritenute lavoro dipendente",
      "periodicita": "Mensile",
      "attivo": true,
      "fonte": "ADE",
      "data_aggiornamento": "2025-11-25"
    }
  ]
}
```

## Monitoraggio e Log

### Django Logs

```python
# settings.py
LOGGING = {
    'loggers': {
        'scadenze.tasks': {
            'level': 'INFO',
            'handlers': ['file'],
        },
    },
}
```

### File Log

```bash
# Vedi log aggiornamenti
tail -f logs/codici_tributo.log
```

### Statistiche

Dopo ogni aggiornamento:

```
📊 TOTALE CODICI SCARICATI: 250

📈 Statistiche per sezione:
  - ERARIO: 120 codici
  - IMU: 45 codici
  - INPS: 35 codici
  - REGIONI: 30 codici
  - INAIL: 15 codici
  - ACCISE: 5 codici

💾 Database aggiornato:
  - Creati: 15 nuovi codici
  - Aggiornati: 235 codici esistenti
  - Totale nel DB: 250
```

## Troubleshooting

### Problema: Nessun codice scaricato

**Causa:** Struttura HTML del sito cambiata

**Soluzione:**
1. Verifica manualmente il sito
2. Aggiorna selettori CSS in `estrai_codici_da_tabella()`
3. Esegui con `--verbose` per debug

### Problema: Timeout connessione

**Causa:** Sito ADE lento o non disponibile

**Soluzione:**
1. Aumenta timeout in `fetch_page()` (default 30s)
2. Riprova più tardi
3. Usa Celery con retry automatico

### Problema: Codici duplicati

**Causa:** Stesso codice in sezioni diverse

**Soluzione:**
- Il sistema usa `update_or_create()` con chiave `(codice, sezione)`
- Codici duplicati in sezioni diverse sono normali

### Problema: Codici mancanti

**Causa:** Parsing incompleto

**Soluzione:**
1. Esegui con `--verbose`
2. Controlla log per errori parsing
3. Verifica manualmente tabelle HTML
4. Ajusta logica `estrai_codici_da_tabella()`

## Manutenzione

### Aggiornamento Manuale

```bash
# 1. Backup database
pg_dump mygest > backup_before_update.sql

# 2. Esegui dry-run
python manage.py aggiorna_codici_tributo --dry-run

# 3. Se OK, aggiorna
python manage.py aggiorna_codici_tributo --force --export

# 4. Verifica risultati
python manage.py shell -c "
from scadenze.models import CodiceTributoF24
print(f'Totale: {CodiceTributoF24.objects.count()}')
print(f'Attivi: {CodiceTributoF24.objects.filter(attivo=True).count()}')
"
```

### Verifica Integrità

```bash
# Query di controllo
python manage.py shell -c "
from scadenze.models import CodiceTributoF24
from django.db.models import Count

# Codici per sezione
print('Codici per sezione:')
for item in CodiceTributoF24.objects.values('sezione').annotate(count=Count('id')):
    print(f\"  {item['sezione']}: {item['count']}\")

# Codici obsoleti
obsoleti = CodiceTributoF24.objects.filter(attivo=False)
print(f'\nCodici obsoleti: {obsoleti.count()}')
for c in obsoleti:
    print(f\"  {c.codice} - {c.descrizione[:50]}...\")
"
```

### Ripristino da Backup

```bash
# Se qualcosa va storto
psql mygest < backup_before_update.sql
```

## Best Practices

### Frequenza Aggiornamento

- ✅ **Raccomandato:** Settimanale (ogni lunedì)
- ⚠️ **Minimo:** Mensile
- 🔥 **Critico:** Dopo comunicazioni ufficiali ADE

### Notifiche

Configura email per:
- ✉️ Errori di scraping
- ✉️ Nuovi codici trovati
- ✉️ Codici marcati obsoleti

### Backup

Fai backup prima di ogni aggiornamento:
```bash
# Script di backup automatico
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump mygest > backups/codici_tributo_$DATE.sql
```

## File del Sistema

```
mygest/
├── scripts/
│   ├── scraper_ade_ufficiale.py          # Scraper principale
│   ├── codici_tributo_ade.csv            # Export CSV
│   └── codici_tributo_ade.json           # Export JSON
│
├── scadenze/
│   ├── models.py                         # Model CodiceTributoF24
│   ├── tasks.py                          # Task Celery
│   └── management/commands/
│       └── aggiorna_codici_tributo.py    # Command Django
│
├── comunicazioni/api/
│   ├── views.py                          # CodiceTributoF24ViewSet
│   └── serializers.py                    # CodiceTributoF24Serializer
│
└── docs/
    └── SISTEMA_AGGIORNAMENTO_CODICI_TRIBUTO.md  # Questo file
```

## Conclusione

Il sistema automatico di aggiornamento garantisce che i codici tributo F24 siano sempre aggiornati con le ultime modifiche dell'Agenzia delle Entrate, riducendo errori manuali e garantendo conformità normativa.

🎯 **Obiettivo:** Automazione completa e affidabilità 100%
