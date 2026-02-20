# Feature: Estensione Campi Parser Cedolini

## 📋 Descrizione

Estensione del parser cedolini per estrarre tutti i dati richiesti dal PDF, inclusi campi precedentemente non gestiti.

**Data**: 4 Febbraio 2026  
**Riferimento**: Immagine cedolino INAIL allegata dall'utente

---

## 🎯 Nuovi Campi Estratti

### 1️⃣ **Data Cessazione Lavoratore**
- **Tipo**: `Optional[str]` (formato `DD-MM-YYYY`)
- **Posizione**: Terza data nella sequenza (dopo nascita e assunzione)
- **Pattern**: `(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})`
- **Gestione NULL**: Se mancante, il dipendente è ancora in servizio
- **Esempio**: `"01-12-2025"`

### 2️⃣ **Netto da Corrispondere**
- **Tipo**: `Optional[str]` (formato Decimal, es. `"56.51"`)
- **Posizione**: Box "NETTO DA CORRISPONDERE" in basso a destra
- **Pattern**: `NETTO\s+DA\s+CORRISPONDERE.*?(\d+[.,]\d{2})`
- **Normalizzazione**: Virgola sostituita con punto per compatibilità Decimal
- **Esempio**: `"56.51"` (estratto da "56,51 €")

### 3️⃣ **Numero Cedolino**
- **Tipo**: `Optional[str]`
- **Posizione**: Header documento (es. "Nr. 00071")
- **Pattern**: `(?:Nr\.|Numero)\s*[:\s]*(\d+)`
- **Uso**: Chiave primaria per rilevamento duplicati
- **Esempio**: `"00071"`

### 4️⃣ **Data e Ora Cedolino**
- **Tipo**: `Optional[str]` (formato `"DD-MM-YYYY HH:MM"` o solo data)
- **Posizione**: Header documento (timestamp generazione)
- **Pattern**: `(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})` o `Prot\.\s*(\d{2}-\d{2}-\d{4})`
- **Uso**: Chiave primaria per rilevamento duplicati (insieme a numero)
- **Esempio**: `"07-01-2026 17:13"` o `"29-01-2009"`

---

## 🔧 Modifiche Implementate

### 1. Parser (`documenti/parsers/cedolino_parser.py`)

#### TypedDict Aggiornati

```python
class LavoratoreData(TypedDict):
    # ... campi esistenti ...
    data_cessazione: Optional[str]  # NUOVO

class CedolinoData(TypedDict):
    # ... campi esistenti ...
    netto: Optional[str]  # NUOVO
    numero_cedolino: Optional[str]  # NUOVO
    data_ora_cedolino: Optional[str]  # NUOVO
```

#### Funzione `extract_pdf_data()` Aggiornata

**Supporto Multi-Pagina:**
```python
# Estrai testo da TUTTE le pagine (non solo la prima)
all_text = ""
for page in pdf.pages:
    page_text = page.extract_text()
    if page_text:
        all_text += page_text + "\n"
```

**Estrazione 3 Date (nascita + assunzione + cessazione):**
```python
# Cerca 3 date consecutive
date_match_3 = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', line)
if date_match_3:
    data['data_nascita'] = date_match_3.group(1)
    data['data_assunzione'] = date_match_3.group(2)
    data['data_cessazione'] = date_match_3.group(3)
    break

# Fallback: 2 date (senza cessazione)
date_match_2 = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})', line)
if date_match_2:
    data['data_nascita'] = date_match_2.group(1)
    data['data_assunzione'] = date_match_2.group(2)
    data['data_cessazione'] = None  # Ancora in servizio
```

**Estrazione Netto:**
```python
# Cerca in tutto il testo (supporto multi-pagina)
netto_match = re.search(r'NETTO\s+DA\s+CORRISPONDERE.*?(\d+[.,]\d{2})', all_text, re.IGNORECASE | re.DOTALL)
if netto_match:
    netto_str = netto_match.group(1).replace(',', '.')  # Normalizza
    data['netto'] = netto_str
```

**Estrazione Numero Cedolino:**
```python
numero_match = re.search(r'(?:Nr\.|Numero)\s*[:\s]*(\d+)', text, re.IGNORECASE)
if numero_match:
    data['numero_cedolino'] = numero_match.group(1)
```

**Estrazione Data/Ora Cedolino:**
```python
# Pattern 1: Data + Ora
datetime_match = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})', text)
if datetime_match:
    data['data_ora_cedolino'] = f"{datetime_match.group(1)} {datetime_match.group(2)}"
else:
    # Pattern 2: Solo data (fallback)
    date_only_match = re.search(r'Prot\.\s*(\d{2}-\d{2}-\d{4})', text)
    if date_only_match:
        data['data_ora_cedolino'] = date_only_match.group(1)
```

---

### 2. Backend API (`api/v1/documenti/views.py`)

#### Logica Duplicazione Aggiornata

**Priorità chiave univoca: `numero_cedolino + data_ora_cedolino`**

```python
# Strategia 1: Chiave primaria (numero + data/ora)
if numero_cedolino and data_ora_cedolino:
    # Cerca attributi con stesso numero + data/ora
    for doc in documenti_candidati:
        attributi = {av.definizione.codice: av.valore for av in doc.attributi_valori.all()}
        
        if (attributi.get('numero_cedolino') == numero_cedolino and
            attributi.get('data_ora_cedolino') == data_ora_cedolino):
            is_duplicato = True
            documento_duplicato_id = doc.id
            break

# Fallback: Logica precedente (dipendente + anno + mese + mensilità)
if not is_duplicato and dipendente_esistente:
    # ... logica esistente ...
```

#### Preview Response Estesa

**Nuovi campi in `dati_note`:**
```python
'dati_note': {
    'matricola': parsed['lavoratore'].get('matricola'),
    'matricola_inps': parsed['lavoratore'].get('matricola_inps'),
    'data_nascita': parsed['lavoratore'].get('data_nascita'),
    'data_assunzione': parsed['lavoratore'].get('data_assunzione'),
    'data_cessazione': parsed['lavoratore'].get('data_cessazione'),  # NUOVO
    'livello': parsed['cedolino'].get('livello'),
    'netto': parsed['cedolino'].get('netto'),  # NUOVO
    'numero_cedolino': parsed['cedolino'].get('numero_cedolino'),  # NUOVO
    'data_ora_cedolino': parsed['cedolino'].get('data_ora_cedolino'),  # NUOVO
}
```

---

### 3. Frontend TypeScript (`frontend/src/api/documenti.ts`)

**Tipi aggiornati:**
```typescript
dati_note: {
  matricola?: string | null;
  matricola_inps?: string | null;
  data_nascita?: string | null;
  data_assunzione?: string | null;
  data_cessazione?: string | null;  // NUOVO
  livello?: string | null;
  netto?: string | null;  // NUOVO
  numero_cedolino?: string | null;  // NUOVO
  data_ora_cedolino?: string | null;  // NUOVO
};
```

---

### 4. Frontend UI (`frontend/src/pages/ImportaCedoliniPage.tsx`)

**Visualizzazione nuovi campi nella tabella preview:**

```tsx
{c.dati_note.data_cessazione && (
  <Typography variant="caption" color="error.main">
    🚪 Cessato: {c.dati_note.data_cessazione}
  </Typography>
)}
{c.dati_note.netto && (
  <Typography variant="caption" color="success.main" sx={{ fontWeight: 'bold' }}>
    💰 Netto: € {c.dati_note.netto}
  </Typography>
)}
{c.dati_note.numero_cedolino && (
  <Typography variant="caption" color="primary.main">
    🔢 Nr: {c.dati_note.numero_cedolino}
  </Typography>
)}
{c.dati_note.data_ora_cedolino && (
  <Typography variant="caption" color="text.secondary">
    🕒 {c.dati_note.data_ora_cedolino}
  </Typography>
)}
```

**Istruzioni aggiornate:**
```
📝 Dati estratti per riferimento: 
Matricola, Matricola INPS, Date (Nascita/Assunzione/Cessazione), 
Livello, Netto, Nr. Cedolino, Data/Ora
```

---

## 📊 Riepilogo Completo Campi Estratti

### ✅ Campi Richiesti (11/11)

| # | Campo | Estratto | Tipo | Note |
|---|-------|----------|------|------|
| 1 | Ragione sociale datore | ✅ | `str` &#124; `None` | Pattern `^\d{6}\s+(.+?)$` |
| 2 | CF datore | ✅ | `str` | Pattern `^\d{11}` (chiave match DB) |
| 3 | Indirizzo datore | ✅ | `str` &#124; `None` | Via + CAP + Città |
| 4 | CF lavoratore | ✅ | `str` | Pattern CF 16 char (chiave match DB) |
| 5 | Cognome Nome lavoratore | ✅ | `str` | Da nome file o PDF |
| 6 | Data nascita | ✅ | `str` &#124; `None` | `DD-MM-YYYY` |
| 7 | Data assunzione | ✅ | `str` &#124; `None` | `DD-MM-YYYY` |
| 8 | **Data cessazione** | ✅ **NUOVO** | `str` &#124; `None` | `DD-MM-YYYY` (terza data) |
| 9 | **Netto** | ✅ **NUOVO** | `str` &#124; `None` | Formato Decimal `"56.51"` |
| 10 | **Nr + Data/Ora cedolino** | ✅ **NUOVO** | `str` &#124; `None` | **Chiave duplicazione** |
| 11 | Periodo retribuzione | ✅ | `str` | Es. "Dicembre 2025" |

---

## 🎯 Logica Rilevamento Duplicati

### Strategia a 2 Livelli

**1️⃣ Chiave Primaria (PREFERITA):**
```
numero_cedolino + data_ora_cedolino
```
- ✅ Più precisa
- ✅ Evita falsi positivi (stesso dipendente, stesso mese, ma cedolino diverso)
- ⚠️ Richiede AttributoDefinizione `numero_cedolino` e `data_ora_cedolino`

**2️⃣ Chiave Fallback (LEGACY):**
```
dipendente + anno_riferimento + mese_riferimento + mensilita
```
- ✅ Funziona anche senza nuovi attributi configurati
- ⚠️ Può avere falsi positivi in caso di cedolini sostitutivi

---

## 🧪 Testing

### Test Case 1: Cedolino Standard (dipendente in servizio)
**Input**: PDF con 2 date (nascita + assunzione), netto, numero
**Verifica**:
- ✅ `data_cessazione` = `None`
- ✅ `netto` = `"56.51"`
- ✅ `numero_cedolino` = `"00071"`
- ✅ `data_ora_cedolino` = `"07-01-2026 17:13"`

### Test Case 2: Cedolino con Cessazione
**Input**: PDF con 3 date (nascita + assunzione + cessazione)
**Verifica**:
- ✅ `data_cessazione` = `"01-12-2025"`
- ✅ Visualizzazione UI con icona 🚪 rossa

### Test Case 3: Duplicato Esatto
**Input**: 2 cedolini con stesso numero + data/ora
**Verifica**:
- ✅ Secondo rilevato come duplicato
- ✅ `documento_duplicato_id` popolato
- ✅ Appare in sezione "⚠️ Duplicati"

### Test Case 4: Cedolino Multi-Pagina
**Input**: PDF su 2+ pagine
**Verifica**:
- ✅ Netto estratto anche se su pagina 2
- ✅ `raw_text` contiene testo completo di tutte le pagine

### Test Case 5: Campi Mancanti (Ignora Errori)
**Input**: PDF senza numero cedolino o netto
**Verifica**:
- ✅ Importazione procede comunque
- ✅ Campi = `None`
- ✅ Fallback a chiave duplicazione legacy

---

## 📝 Note Implementative

### Gestione Errori
- **Approccio**: Ignora campi mancanti (come da requisito 5)
- **Pattern**: Campi opzionali con valore `None` se non trovati
- **Logging**: Errori loggati ma non bloccano importazione

### Supporto Multi-Pagina
- ✅ Estrazione testo da **tutte le pagine**
- ✅ `raw_text` contiene testo completo
- ✅ Ricerca `NETTO DA CORRISPONDERE` in tutto il documento

### Normalizzazione Formati
- **Netto**: Virgola → Punto (es. `"56,51"` → `"56.51"`)
- **Date**: Mantiene formato originale `DD-MM-YYYY`
- **Data/Ora**: Formattato come `"DD-MM-YYYY HH:MM"`

---

## 🔮 Future Improvements

1. **AttributoDefinizione Auto-Setup**: Script per creare automaticamente attributi `numero_cedolino` e `data_ora_cedolino`
2. **Validazione Netto**: Controllo range valori (warning se negativo o anomalo)
3. **Pattern Cedolini Alternativi**: Supporto formati diversi da INAIL
4. **Export Dati Estratti**: Funzionalità export Excel con tutti i campi estratti
5. **Preview Confronto Duplicati**: Mostrare differenze tra cedolino nuovo e duplicato esistente

---

## ✅ Checklist Completamento

- [x] Parser estrae data cessazione (3° data opzionale)
- [x] Parser estrae netto (formato Decimal normalizzato)
- [x] Parser estrae numero cedolino
- [x] Parser estrae data/ora cedolino
- [x] Supporto multi-pagina implementato
- [x] Logica duplicazione aggiornata (chiave primaria numero+dataora)
- [x] Backend API estende response preview
- [x] Frontend TypeScript types aggiornati
- [x] Frontend UI mostra nuovi campi
- [x] Nessun errore compilazione Python
- [x] Nessun errore compilazione TypeScript
- [x] Documentazione aggiornata

---

**Stato**: ✅ Completato  
**Testing**: ⏳ In attesa di test end-to-end con PDF reali  
**Deploy**: ⏳ Pending (richiede riavvio backend)
