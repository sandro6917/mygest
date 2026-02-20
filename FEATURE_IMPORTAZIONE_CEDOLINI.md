# Importazione Cedolini Paga - Documentazione

## 📋 Panoramica

È stata implementata una funzionalità completa per l'importazione automatica di cedolini paga da file ZIP.

### ✨ Caratteristiche Implementate

1. **Parsing Automatico**:
   - Estrazione dati da nome file (CF, Nome, Cognome, Matricola, Anno)
   - Parsing contenuto PDF (Periodo, Azienda, Livello, Date)
   - Identificazione mensilità (ordinaria, tredicesima, quattordicesima)

2. **Creazione Automatica**:
   - Anagrafica dipendente (se non esiste)
   - Cliente azienda datore di lavoro (se non esiste)
   - Fascicolo "Paghe {mese} {anno}" (se non esiste)
   - Documento BPAG con tutti gli attributi dinamici

3. **Validazione**:
   - Controllo formato file (ZIP, max 100MB)
   - Validazione pattern nome file
   - Gestione errori con report dettagliato

4. **UI Completa**:
   - Pagina dedicata per import
   - Progress indicator
   - Report risultati dettagliato
   - Bottone "Importa Cedolini" nella lista documenti

---

## 🗂️ File Creati/Modificati

### Backend

#### Nuovi File
- **`documenti/utils_cedolini.py`** (337 righe)
  - Utility per parsing cedolini
  - Funzioni: `parse_filename_cedolino()`, `extract_pdf_data()`, `identifica_mensilita()`, etc.

- **`documenti/import_cedolini.py`** (359 righe)
  - Classe `CedolinoImporter` per gestione import
  - Logica business completa
  - Creazione automatica anagrafica/cliente/fascicolo/documento

- **`documenti/management/commands/setup_cedolini.py`** (117 righe)
  - Setup attributi tipo BPAG
  - Setup voce titolario PAG
  - Usage: `python manage.py setup_cedolini`

#### File Modificati
- **`requirements.txt`**
  - Aggiunto: `pdfplumber==0.11.4`

- **`api/v1/documenti/serializers.py`**
  - Aggiunto: `ImportaCedoliniSerializer`

- **`api/v1/documenti/views.py`**
  - Aggiunto: Action `@action(detail=False, methods=['post']) importa_cedolini()`
  - Endpoint: `POST /api/v1/documenti/importa_cedolini/`

### Frontend

#### Nuovi File
- **`frontend/src/pages/ImportaCedoliniPage.tsx`** (359 righe)
  - Pagina completa per import cedolini
  - Form upload ZIP
  - Progress indicator
  - Report risultati dettagliato

#### File Modificati
- **`frontend/src/api/documenti.ts`**
  - Aggiunto: Metodo `importaCedolini(zipFile: File)`

- **`frontend/src/routes/index.tsx`**
  - Aggiunta route: `/documenti/importa-cedolini`
  - Import: `ImportaCedoliniPage`

- **`frontend/src/pages/DocumentiListPage.tsx`**
  - Aggiunto bottone "Importa Cedolini"

---

## ⚙️ Configurazione

### Setup Iniziale

Eseguire il comando di setup per creare gli attributi BPAG e la voce titolario PAG:

```bash
python manage.py setup_cedolini
```

Output atteso:
```
=== Setup Cedolini ===

✓ Tipo documento già esistente: BPAG - Buste paga
  ✓ Creato/Aggiornato attributo: tipo (Tipo)
  ✓ Creato/Aggiornato attributo: anno_riferimento (Anno Riferimento)
  ✓ Creato/Aggiornato attributo: mese_riferimento (Mese Riferimento)
  ✓ Creato/Aggiornato attributo: mensilita (Mensilità)
  ✓ Creato/Aggiornato attributo: dipendente (Dipendente)

✓ Creata voce titolario: PAG - Paghe

=== Setup completato con successo! ===
```

### Attributi Dinamici BPAG

Il tipo documento BPAG ha i seguenti attributi dinamici:

| Codice | Nome | Tipo | Obbligatorio | Descrizione |
|--------|------|------|--------------|-------------|
| `tipo` | Tipo | CHOICE | Sì | Tipo di libro (default: "Libro Unico") |
| `anno_riferimento` | Anno Riferimento | INT | Sì | Anno di riferimento (es. 2025) |
| `mese_riferimento` | Mese Riferimento | INT | Sì | Mese di riferimento (1-12) |
| `mensilita` | Mensilità | INT | Sì | Mensilità (1-12 ordinaria, 13 tredicesima, 14 quattordicesima) |
| `dipendente` | Dipendente | ANAGRAFICA | Sì | Anagrafica del dipendente (widget anagrafica) |

### Voce Titolario

- **Codice**: `PAG`
- **Titolo**: `Paghe`
- **Tipo**: Voce di primo livello (parent=None)
- **Pattern Codice**: `{CLI}-PAG-{ANNO}-{SEQ:03d}`

---

## 📖 Utilizzo

### 1. Via Interfaccia Web

1. Accedi a MyGest
2. Vai su **Documenti** → **Importa Cedolini**
3. Seleziona file ZIP contenente i cedolini PDF
4. Clicca **Importa Cedolini**
5. Visualizza il report dei risultati

### 2. Formato Nome File Cedolini

Pattern richiesto:
```
{CF} - {ANNO} - {COGNOME} {NOME} ({CF}-{MATRICOLA}).pdf
```

Esempi validi:
```
RSSMRA85M01H501X - 2025 - ROSSI MARIO (RSSMRA85M01H501X-0000123).pdf
BNCLNR99C46G088Y - 2025 - BIANCHI ELEONORA (BNCLNR99C46G088Y-0000001).pdf
```

### 3. Contenuto PDF

Il sistema estrae automaticamente dal PDF:
- Periodo retribuzione (es. "Dicembre 2025")
- Dati azienda (CF, Ragione Sociale, Indirizzo)
- Livello contrattuale
- Date (nascita, assunzione)
- Matricola INPS

### 4. Logica di Creazione

Per ogni cedolino:

1. **Dipendente**:
   - Cerca anagrafica esistente tramite CF
   - Se non esiste, crea nuova anagrafica PF con Nome, Cognome, CF

2. **Azienda**:
   - Cerca cliente esistente tramite CF azienda (estratto dal PDF)
   - Se non esiste, crea anagrafica PG + cliente con Denominazione, CF

3. **Fascicolo**:
   - Cerca fascicolo esistente con titolo "Paghe {mese abbr} {anno}" (es. "Paghe dic 2025")
   - Se non esiste, crea nuovo fascicolo digitale con voce titolario PAG

4. **Documento**:
   - Crea documento tipo BPAG
   - Descrizione: "Cedolino {COGNOME} {NOME} - {Periodo}"
   - Data: Ultimo giorno del mese
   - Stato: DEFINITIVO
   - Salva PDF come allegato
   - Crea attributi dinamici (tipo, anno, mese, mensilità, dipendente)
   - Note: Tutti i dati estratti

---

## 🔌 API Endpoint

### POST `/api/v1/documenti/importa_cedolini/`

Importa cedolini paga da file ZIP.

**Request** (multipart/form-data):
```json
{
  "file": <ZIP_FILE>
}
```

**Response** (201 Created / 207 Multi-Status / 400 Bad Request):
```json
{
  "created": 6,
  "errors": [],
  "warnings": [],
  "documenti": [
    {
      "id": 123,
      "codice": "CLI001-BPAG-2025-001",
      "descrizione": "Cedolino ROSSI MARIO - Dicembre 2025",
      "filename": "RSSMRA85M01H501X - 2025 - ROSSI MARIO (RSSMRA85M01H501X-0000123).pdf"
    },
    ...
  ]
}
```

**Status Codes**:
- `201`: Importazione completata con successo
- `207`: Importazione parziale (alcuni errori)
- `400`: Errore nella richiesta o importazione fallita

**Validazione**:
- File deve essere ZIP
- Dimensione massima: 100MB

---

## 🧪 Test

### Test Parsing Nome File

```python
from documenti.utils_cedolini import parse_filename_cedolino

filename = "RSSMRA85M01H501X - 2025 - ROSSI MARIO (RSSMRA85M01H501X-0000123).pdf"
result = parse_filename_cedolino(filename)

# Output:
# {
#   'codice_fiscale': 'RSSMRA85M01H501X',
#   'anno': '2025',
#   'cognome': 'Rossi',
#   'nome': 'Mario',
#   'matricola': '0000123'
# }
```

### Test Import Completo

File di test incluso: `test_import_cedolini.py`

```bash
python test_import_cedolini.py
```

---

## 📊 Esempi

### Esempio 1: Cedolino Ordinario

**Nome File**: `RSSMRA85M01H501X - 2025 - ROSSI MARIO (RSSMRA85M01H501X-0000123).pdf`

**Dati PDF**:
- Periodo: "Dicembre 2025"
- Azienda: "ACME S.R.L." (CF: 12345678901)

**Risultato**:
- Documento: `CLI001-BPAG-2025-012`
- Descrizione: "Cedolino ROSSI MARIO - Dicembre 2025"
- Data: 31/12/2025
- Fascicolo: "Paghe dic 2025"
- Attributi:
  - tipo: "Libro Unico"
  - anno_riferimento: 2025
  - mese_riferimento: 12
  - mensilita: 12
  - dipendente: ID anagrafica ROSSI MARIO

### Esempio 2: Tredicesima

**PDF contiene**: "Tredicesima" nel testo

**Risultato**:
- Attributi:
  - mensilita: 13 (invece di 12)

---

## 🔧 Troubleshooting

### Errore: "Configurazione mancante"

**Causa**: Tipo BPAG o voce titolario PAG non esistono.

**Soluzione**:
```bash
python manage.py setup_cedolini
```

### Errore: "Nome file non valido"

**Causa**: Il nome del PDF non rispetta il pattern richiesto.

**Soluzione**: Rinomina il file seguendo il pattern:
```
{CF} - {ANNO} - {COGNOME} {NOME} ({CF}-{MATRICOLA}).pdf
```

### Errore: "Impossibile identificare l'azienda"

**Causa**: Il PDF non contiene il codice fiscale dell'azienda.

**Soluzione**: Verifica che il PDF contenga la sezione "Codice Fiscale" dell'azienda.

### Errore: "File troppo grande"

**Causa**: Il file ZIP supera i 100MB.

**Soluzione**: Dividi i cedolini in più file ZIP più piccoli.

---

## 🚀 Miglioramenti Futuri

Possibili estensioni della funzionalità:

1. **Import Incrementale**:
   - Skip cedolini già importati (check duplicati per CF+periodo)

2. **Validazione Avanzata**:
   - Controllo congruenza dati (data nascita da CF vs PDF)
   - Alert per anomalie retributive

3. **Report Excel**:
   - Export risultati importazione in Excel

4. **Scheduling**:
   - Import automatico da cartella monitorata

5. **Integrazione Email**:
   - Import da allegati email

6. **OCR Avanzato**:
   - Estrazione dati retributivi (stipendio, ritenute, netto)
   - Salvataggio in attributi dinamici aggiuntivi

---

## 📝 Note Tecniche

### Dipendenze Python

```
pdfplumber==0.11.4
  └── pdfminer.six==20231228
  └── pypdfium2>=4.18.0
  └── Pillow>=9.1
```

### Performance

- Tempo medio per cedolino: ~1-2 secondi
- File ZIP con 50 cedolini: ~1-2 minuti
- Limite raccomandato: 100 cedolini per batch

### Storage

- PDF salvati in NAS: `{CLI}/PAG/{ANNO}/`
- Pattern nome file: configurabile in `DocumentiTipo.nome_file_pattern`

---

## ✅ Checklist Deployment

- [x] Installare `pdfplumber`: `pip install pdfplumber==0.11.4`
- [x] Eseguire setup: `python manage.py setup_cedolini`
- [x] Verificare tipo BPAG esiste nel DB
- [x] Verificare voce titolario PAG esiste
- [x] Build frontend: `cd frontend && npm run build`
- [x] Restart backend: `systemctl restart gunicorn`
- [ ] Test con file ZIP reale
- [ ] Verificare permessi utenti
- [ ] Monitorare log durante primo import

---

**Versione**: 1.0  
**Data**: 28 Gennaio 2026  
**Autore**: Sandro Chimenti
