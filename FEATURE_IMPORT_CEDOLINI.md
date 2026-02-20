# Feature: Importazione Cedolini da ZIP

## 📋 Panoramica

Sistema completo per l'importazione massiva di cedolini paga da file ZIP contenenti PDF.

## ✨ Funzionalità Implementate

### 1. Parsing Automatico
- **Filename**: Estrazione CF, Nome, Cognome, Anno, Matricola
- **PDF Content**: 
  - CF Azienda (11 cifre)
  - Ragione Sociale
  - Indirizzo completo
  - Periodo (Mese Anno)
  - **Mensilità Aggiuntive**: Riconoscimento automatico "AGG." 
    - "Dicembre {anno} AGG." → Tredicesima (mensilità 13)
    - "Giugno {anno} AGG." → Quattordicesima (mensilità 14)
  - Livello dipendente
  - Date (nascita, assunzione)
  - Netto (importo finale con regex avanzate)

### 2. Creazione Automatica Entità

#### Anagrafica Azienda
- Tipo: PG (Persona Giuridica) se CF 11 cifre
- Codice Fiscale validato
- Ragione Sociale da PDF
- Indirizzo completo

#### Anagrafica Dipendente
- Tipo: PF (Persona Fisica) se CF 16 caratteri
- Codice Fiscale da filename
- Nome e Cognome
- Matricola

#### Cliente
- Creato per Azienda e Dipendente
- Collegamento con Anagrafica

#### Fascicolo
- Titolo: "Paghe {Mese} {Anno}"
- Titolario: PAG (Paghe)
- Digitale (ubicazione = None)
- Raggruppamento per Cliente+Periodo

#### Documento BPAG
- Tipo: BPAG (Buste Paga)
- Stato: DEFINITIVO
- Digitale + Tracciabile
- File PDF allegato

#### Attributi Dinamici
- `tipo`: Livello contrattuale
- `anno_riferimento`: Anno competenza
- `mese_riferimento`: Mese (1-12)
- `mensilita`: 12=Normale, 13=Tredicesima, 14=Quattordicesima
- `dipendente`: Link ad Anagrafica dipendente

### 3. Transazioni Atomiche

**Strategia**: Atomicità per singolo cedolino (Best Effort)

```
Per ogni cedolino:
  BEGIN TRANSACTION
    - Crea/Trova Anagrafica Dipendente
    - Crea/Trova Cliente Azienda
    - Crea/Trova Fascicolo Paghe
    - Crea Documento BPAG
    - Salva File PDF
    - Salva Attributi
  COMMIT o ROLLBACK se errore
```

**Vantaggi**:
- ✅ Importa il massimo possibile
- ✅ Errori isolati non bloccano tutto
- ✅ Rollback solo per cedolini problematici
- ✅ Report dettagliato successi/fallimenti

### 4. Frontend React

#### UI Components
- **Upload Area**: Drag & drop + selezione file
- **Progress Bar**: Indicatore caricamento
- **Results Card**: Riepilogo dettagliato

#### Alert Riepilogativo
- 🟢 **Successo totale**: Tutti i cedolini importati
- �� **Parziale**: X su Y importati, Z errori
- 🔴 **Fallimento**: Nessun cedolino importato

#### Statistiche
- Totale cedolini nel ZIP
- Importati con successo
- Errori (con filename e dettaglio)
- Barra progresso visuale

#### Documenti Creati
- Lista con link "Visualizza"
- Codice documento
- Descrizione
- Filename originale

## 🎯 Pattern PDF Supportati

### Formato Filename
```
{CF} - {ANNO} - {COGNOME} {NOME} ({CF}-{MATRICOLA}).pdf

Esempio:
BNCLNR99C46G088Y - 2025 - BIANCHI ELEONORA (BNCLNR99C46G088Y-0000001).pdf
```

### Formato PDF - CF Azienda
**Pattern 1** (con campo centrale):
```
00884530536 3603879309/00 021947673/73
```

**Pattern 2** (senza campo centrale):
```
00884530536 021947673/73
```

Entrambi i pattern sono supportati.

### Formato PDF - Ragione Sociale
```
000049 LA FORTEZZA SOCIETA' COOPERATIVA
```
Pattern: 6 cifre + spazio + nome azienda

## 🛠️ Setup Iniziale

```bash
# 1. Installa dipendenze
pip install pdfplumber==0.11.4

# 2. Esegui setup (crea tipo BPAG + attributi + titolario PAG)
python manage.py setup_cedolini
```

## 🎯 Riconoscimento Mensilità Aggiuntive

### Pattern "AGG." (Mensilità Aggiuntive)

Il parser riconosce automaticamente le mensilità aggiuntive dal suffisso **"AGG."** nel campo periodo:

#### Logica di Riconoscimento (Priority Order)

1. **PRIORITY 1**: Pattern "AGG." nel periodo
   - `"Dicembre {anno} AGG."` → **Tredicesima** (mensilità 13)
   - `"Giugno {anno} AGG."` → **Quattordicesima** (mensilità 14)
   - Regex: `\bagg\.?\b` (case-insensitive)

2. **PRIORITY 2**: Keywords nel testo
   - "tredicesima", "13 esima", "XIII mensilità", etc.
   - Pattern aggiuntivo: `\bdicembre\s+\d{4}\s+agg\.?`

3. **PRIORITY 3**: Quattordicesima keywords
   - "quattordicesima", "14 esima", "XIV mensilità", etc.
   - Pattern aggiuntivo: `\bgiugno\s+\d{4}\s+agg\.?`

4. **PRIORITY 4**: Estrazione mese standard
   - Da periodo senza "AGG." (es. "Gennaio 2024" → mensilità 1)

#### Esempi

```python
from documenti.parsers.cedolino_parser import identifica_mensilita

# Tredicesima
identifica_mensilita("Dicembre 2023 AGG.", "...") # → 13

# Quattordicesima  
identifica_mensilita("Giugno 2023 AGG.", "...") # → 14

# Mensilità ordinaria
identifica_mensilita("Dicembre 2023", "...") # → 12 (Dicembre normale)
identifica_mensilita("Gennaio 2024", "...") # → 1
```

#### Implementazione

**File**: `documenti/parsers/cedolino_parser.py`

```python
def identifica_mensilita(periodo: Optional[str], raw_text: str) -> int:
    """Identifica mensilità con supporto AGG."""
    periodo_lower = periodo.lower() if periodo else ""
    
    # Priority 1: Verifica pattern "AGG."
    if periodo and re.search(r'\bagg\.?\b', periodo_lower):
        if 'dicembre' in periodo_lower:
            return 13  # Tredicesima
        elif 'giugno' in periodo_lower:
            return 14  # Quattordicesima
    
    # ... resto della logica
```

---

## 🧪 Testing

### Test Parsing
```bash
cd /home/sandro/mygest
python3 << 'EOF'
from documenti.utils_cedolini import parse_filename_cedolino, extract_pdf_data
import zipfile

with zipfile.ZipFile('Cedolini_Fortezza_202512.zip', 'r') as zf:
    for filename in zf.namelist():
        if filename.endswith('.pdf'):
            # Parse filename
            file_data = parse_filename_cedolino(filename)
            print(f"File: {file_data}")
            
            # Parse PDF
            pdf_bytes = zf.read(filename)
            pdf_data = extract_pdf_data(pdf_bytes)
            print(f"PDF: CF={pdf_data.get('azienda_cf')}, Periodo={pdf_data.get('periodo')}")
