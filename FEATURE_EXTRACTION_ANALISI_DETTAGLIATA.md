# 🔍 Feature Extraction - Analisi Dettagliata

## 📋 Panoramica

Durante la fase di **Feature Extraction**, il sistema analizza ogni documento ed estrae **519 caratteristiche numeriche** (features) che vengono poi utilizzate dal modello ML per la classificazione.

---

## 📊 Composizione Features (519 dimensioni totali)

```
┌─────────────────────────────────────────────────────────┐
│  FEATURE TYPE          │  DIMENSIONI  │  PERCENTUALE   │
├─────────────────────────────────────────────────────────┤
│  TF-IDF Text Vector    │     500      │    96.3%       │
│  NER (Named Entities)  │       5      │     1.0%       │
│  Pattern Matching      │       5      │     1.0%       │
│  Filename Features     │       3      │     0.6%       │
│  Statistical Features  │       6      │     1.1%       │
├─────────────────────────────────────────────────────────┤
│  TOTALE                │     519      │   100.0%       │
└─────────────────────────────────────────────────────────┘
```

---

## 1️⃣ TF-IDF Text Features (500 dimensioni)

### Cos'è TF-IDF?

**TF-IDF** (Term Frequency - Inverse Document Frequency) trasforma il testo in un vettore numerico che cattura l'importanza delle parole.

### Algoritmo

```
TF (Term Frequency) = n° occorrenze parola nel documento / totale parole

IDF (Inverse Document Frequency) = log(n° documenti totali / n° documenti con la parola)

TF-IDF = TF × IDF

Normalizzazione: vettore / lunghezza_vettore (norma L2)
```

### Configurazione

```python
TfidfVectorizer(
    max_features=500,        # Top 500 parole più significative
    ngram_range=(1, 2),      # Unigram (1 parola) + Bigram (2 parole)
    min_df=2,                # Parola deve apparire in almeno 2 documenti
    max_df=0.8,              # Parola non deve apparire in > 80% documenti
    stop_words='italian'     # Rimuove "il", "di", "la", "che", ecc.
)
```

### Esempi Parole Estratte

#### Per documenti UNILAV:
```python
Top features:
  'unilav': 0.45            # Peso alto (parola distintiva)
  'comunicazione': 0.38
  'codice_comunicazione': 0.42  # Bigram
  'rapporto_lavoro': 0.35
  'assunzione': 0.40
  'lavoratore': 0.33
  'codice_fiscale': 0.37
  'data_inizio': 0.29
  'centro_impiego': 0.31
  'ente_previdenziale': 0.28
```

#### Per documenti F24:
```python
Top features:
  'f24': 0.52
  'codice_tributo': 0.48
  'agenzia_entrate': 0.41
  'ravvedimento': 0.39
  'saldo': 0.35
  'acconto': 0.33
  'importo_versare': 0.36
  'compensazione': 0.30
```

#### Per Cedolini:
```python
Top features:
  'cedolino': 0.50
  'busta_paga': 0.46
  'retribuzione': 0.43
  'competenze': 0.40
  'contributi': 0.38
  'inps': 0.36
  'netto_pagare': 0.41
  'stipendio': 0.37
  'tfr': 0.32
```

### Output TF-IDF

Per ogni documento, viene creato un **vettore di 500 numeri**:

```python
[0.0, 0.23, 0.0, 0.45, 0.12, 0.0, 0.0, 0.34, ..., 0.0, 0.18]
 ↑     ↑     ↑     ↑     ↑     ↑     ↑     ↑          ↑     ↑
 P1    P2    P3    P4    P5    P6    P7    P8   ...  P499  P500

Dove:
- P1, P3, P6, P7, ... = 0.0 (parola non presente)
- P2 = 0.23 (parola presente con peso 0.23)
- P4 = 0.45 (parola molto importante)
```

**Esempio reale documento UNILAV**:
```python
{
    'unilav': 0.45,
    'comunicazione': 0.38,
    'obbligatoria': 0.22,
    'rapporto': 0.31,
    'lavoro': 0.29,
    'codice': 0.25,
    'fiscale': 0.27,
    'assunzione': 0.40,
    'lavoratore': 0.33,
    # ... altre 491 parole (molte a 0.0)
}
```

---

## 2️⃣ NER Features - Named Entity Recognition (5 dimensioni)

### Tecnologia

Usa **spaCy** (modello `it_core_news_sm`) per riconoscere entità nel testo italiano.

### Entità Riconosciute

```python
entities = {
    'persons':        # PER - Nomi di persone
    'organizations':  # ORG - Aziende, enti
    'locations':      # LOC/GPE - Luoghi, città
    'dates':          # Espressioni temporali
    'money':          # Valori monetari
}
```

### Estrazione

```python
# Esempio testo UNILAV
text = """
SALIMBENI REMO nato a Perugia il 22/05/1965
Codice Fiscale: SLMRME65H22C080N
Lavoratore: CONSORTI LISA
Comune: Perugia
Ente Previdenziale: INPS
Retribuzione: 1500.00 EUR
"""

# spaCy processa il testo
doc = nlp(text)

# Entità trovate:
entities['persons'] = ['SALIMBENI REMO', 'CONSORTI LISA']
entities['organizations'] = ['INPS']
entities['locations'] = ['Perugia']
entities['dates'] = ['22/05/1965']
entities['money'] = ['1500.00 EUR']
```

### Output NER Features (normalizzate 0-1)

```python
{
    'persons_count': 2,           → Vector: 2/10 = 0.20
    'organizations_count': 1,     → Vector: 1/10 = 0.10
    'locations_count': 1,         → Vector: 1/5  = 0.20
    'dates_count': 1,             → Vector: 1/20 = 0.05
    'money_count': 1,             → Vector: 1/20 = 0.05
}

Feature vector NER = [0.20, 0.10, 0.20, 0.05, 0.05]
```

### Normalizzazione

I conteggi vengono normalizzati per evitare che numeri troppo grandi distorcano il modello:

```python
# Persone: max 10 (saturazione)
persons_normalized = min(persons_count / 10.0, 1.0)

# Se ho 15 persone → 15/10 = 1.5 → min(1.5, 1.0) = 1.0
# Se ho 3 persone  → 3/10  = 0.3 → min(0.3, 1.0) = 0.3
```

---

## 3️⃣ Pattern Matching Features (5 dimensioni)

### Regex Patterns

Ricerca pattern specifici con espressioni regolari ottimizzate per documenti italiani.

### Pattern 1: Codici Fiscali

```python
CODICE_FISCALE_PATTERN = r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b'

# Esempi matchati:
'SLMRME65H22C080N'  ✅
'CNSLSI95E50H501X'  ✅
'ABC123'            ❌ (troppo corto)
```

**Estrazione**:
```python
text = "Datore: SLMRME65H22C080N, Lavoratore: CNSLSI95E50H501X"

codici_fiscali = ['SLMRME65H22C080N', 'CNSLSI95E50H501X']
codici_fiscali_count = 2

Vector: min(2/5, 1.0) = 0.40
```

### Pattern 2: Partite IVA

```python
PARTITA_IVA_PATTERN = r'\b\d{11}\b'

# Esempi:
'12345678901'  ✅
'98765432109'  ✅
'123456'       ❌ (troppo corta)
```

**Estrazione**:
```python
text = "P.IVA: 12345678901"

partite_iva = ['12345678901']
partite_iva_count = 1

Vector: min(1/5, 1.0) = 0.20
```

### Pattern 3: Date (formati multipli)

```python
DATE_PATTERNS = [
    r'\b\d{2}/\d{2}/\d{4}\b',           # 15/01/2024
    r'\b\d{2}-\d{2}-\d{4}\b',           # 15-01-2024
    r'\b\d{4}-\d{2}-\d{2}\b',           # 2024-01-15
    r'\b\d{1,2}\s+(?:gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*\s+\d{4}\b',  # 15 gennaio 2024
]

# Esempi matchati:
'15/01/2024'      ✅
'2024-01-15'      ✅
'15 gennaio 2024' ✅
```

**Estrazione**:
```python
text = "Data: 15/01/2024, Scadenza: 31/12/2024"

date_found = ['15/01/2024', '31/12/2024']
date_count = 2

Vector: min(2/20, 1.0) = 0.10
```

### Pattern 4: Importi

```python
IMPORTO_PATTERNS = [
    r'€\s*[\d.,]+',                     # €1.500,00
    r'EUR\s*[\d.,]+',                   # EUR 1500.00
    r'[\d.,]+\s*€',                     # 1500,00 €
    r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b',  # 1.500,00
]

# Esempi:
'€ 1.500,00'   ✅
'EUR 1500.00'  ✅
'1.500,00 €'   ✅
'2.500'        ✅
```

**Estrazione**:
```python
text = "Totale: € 1.500,00, IVA: € 300,00, Netto: € 1.200,00"

importi_found = ['€ 1.500,00', '€ 300,00', '€ 1.200,00']
importi_count = 3

Vector: min(3/20, 1.0) = 0.15
```

### Pattern 5: Numeri Documento

```python
NUMERO_DOCUMENTO_PATTERNS = [
    r'(?:fatt(?:ura)?|invoice)[\s\-:]*n?\.?\s*(\d+)',  # Fattura n. 123
    r'(?:prot(?:ocollo)?)[\s\-:]*n?\.?\s*(\d+)',       # Protocollo 456
    r'(?:cod(?:ice)?)[\s\-:]*(\w+)',                   # Codice ABC123
]

# Esempi:
'Fattura n. 123/2024'      ✅ → '123'
'Protocollo: 456'          ✅ → '456'
'Codice comunicazione: 789' ✅ → '789'
```

**Estrazione**:
```python
text = "Fattura n. 123/2024, Protocollo: 456"

numeri_documento = ['123', '456']
numeri_documento_count = 2

Vector: min(2/5, 1.0) = 0.40
```

### Output Pattern Features

```python
Feature vector Pattern = [
    0.40,  # codici_fiscali_count (2/5)
    0.20,  # partite_iva_count (1/5)
    0.10,  # date_count (2/20)
    0.15,  # importi_count (3/20)
    0.40,  # numeri_documento_count (2/5)
]
```

---

## 4️⃣ Filename Features (3 dimensioni)

### Analisi Nome File

Estrae informazioni dal nome del file originale.

### Estrazione Parole

```python
filename = "UNILAV_Assunzione_Consorti_Lisa_15012024.pdf"

# Parsing
words = ['unilav', 'assunzione', 'consorti', 'lisa', '15012024', 'pdf']
words_count = 6

Vector: min(6/20, 1.0) = 0.30
```

### Keyword Matching

```python
document_keywords = {
    'cedolino': ['cedolino', 'payslip', 'busta', 'paga'],
    'fattura': ['fattura', 'invoice', 'fatt'],
    'f24': ['f24', 'modello f24'],
    'unilav': ['unilav', 'co_'],
    # ... altri tipi
}

# Match
filename_lower = 'unilav_assunzione_consorti_lisa.pdf'

keyword_matches = ['unilav']  # Trovato!

Vector: 1.0 (match trovato)
```

### Date nel Filename

```python
filename = "documento_15012024.pdf"

# Cerca pattern data
date_in_filename = ['15012024']

Vector: 1.0 (data trovata)
```

### Output Filename Features

```python
Feature vector Filename = [
    0.30,  # words_count (6/20)
    1.0,   # keyword_match (trovato)
    1.0,   # date_in_filename (trovata)
]
```

---

## 5️⃣ Statistical Features (6 dimensioni)

### Statistiche Testuali

Calcola metriche statistiche sul contenuto del documento.

### Conteggio Parole

```python
text = "Il lavoratore CONSORTI LISA è stato assunto..."

words = text.split()
word_count = 250  # Esempio

Vector: min(250/5000, 1.0) = 0.05
```

### Parole Unique

```python
unique_words = len(set(['il', 'lavoratore', 'consorti', 'lisa', ...]))
unique_words = 120  # Esempio

Vector: min(120/2000, 1.0) = 0.06
```

### Lunghezza Media Parola

```python
avg_word_length = total_chars / word_count
                = 1500 / 250
                = 6.0

Vector: 6.0 / 20.0 = 0.30
```

### Densità Caratteri Speciali

```python
text = "Codice: ABC-123, Data: 15/01/2024, €1.500,00"
special_chars = [',', ':', '-', '/', '.', '€']
special_count = 8

special_char_density = 8 / len(text) = 0.15

Vector: 0.15
```

### Densità Numeri

```python
digit_count = 15  # Conteggio cifre '0'-'9'
digit_density = 15 / len(text) = 0.08

Vector: 0.08
```

### Densità Maiuscole

```python
upper_count = 25  # Conteggio caratteri maiuscoli
upper_density = 25 / len(text) = 0.12

Vector: 0.12
```

### Output Statistical Features

```python
Feature vector Statistical = [
    0.05,  # word_count
    0.06,  # unique_words
    0.30,  # avg_word_length
    0.15,  # special_char_density
    0.08,  # digit_density
    0.12,  # upper_density
]
```

---

## 🎯 Esempio Completo: Documento UNILAV

### Input

```
File: UNILAV_1700026200007595.pdf
Testo estratto (OCR):

COMUNICAZIONE OBBLIGATORIA UNILAV
Codice Comunicazione: 1700026200007595
Tipo: ASSUNZIONE
Data: 03/01/2026

DATORE DI LAVORO
Denominazione: SALIMBENI REMO
Codice Fiscale: SLMRME40E22C080N
Email: salimbeni@example.com
Comune: Perugia

LAVORATORE
Nome: LISA
Cognome: CONSORTI
Codice Fiscale: CNSLSI95E50H501X
Data Nascita: 10/05/1995
Comune Nascita: Perugia

RAPPORTO DI LAVORO
Data Inizio: 15/01/2026
Tipologia: DETERMINATO
Qualifica: IMPIEGATO
Retribuzione: € 1.500,00
Ore settimanali: 40
```

### Output Features (519 dimensioni)

#### 1. TF-IDF (500 dimensioni)

```python
[
    0.00, 0.45, 0.00, 0.38, 0.42, 0.00, 0.35, 0.40, 0.33, 0.37,
    0.29, 0.31, 0.28, 0.00, 0.00, 0.27, 0.00, 0.23, 0.00, 0.25,
    # ... altre 480 dimensioni (molte a 0.0)
]

Top 10 parole importanti:
  'unilav': 0.45
  'comunicazione': 0.38
  'codice_comunicazione': 0.42
  'assunzione': 0.40
  'lavoratore': 0.33
  'codice_fiscale': 0.37
  'rapporto': 0.29
  'centro': 0.31
  'ente': 0.28
  'qualifica': 0.25
```

#### 2. NER (5 dimensioni)

```python
Entities found:
  Persons: ['SALIMBENI REMO', 'LISA', 'CONSORTI']
  Organizations: []
  Locations: ['Perugia']
  Dates: ['03/01/2026', '10/05/1995', '15/01/2026']
  Money: ['€ 1.500,00']

Vector: [0.30, 0.00, 0.20, 0.15, 0.05]
        ↑     ↑     ↑     ↑     ↑
        3/10  0/10  1/5   3/20  1/20
```

#### 3. Pattern (5 dimensioni)

```python
Patterns matched:
  Codici Fiscali: ['SLMRME40E22C080N', 'CNSLSI95E50H501X']
  Partite IVA: []
  Date: ['03/01/2026', '10/05/1995', '15/01/2026']
  Importi: ['€ 1.500,00']
  Numeri Documento: ['1700026200007595']

Vector: [0.40, 0.00, 0.15, 0.05, 0.20]
        ↑     ↑     ↑     ↑     ↑
        2/5   0/5   3/20  1/20  1/5
```

#### 4. Filename (3 dimensioni)

```python
Filename analysis:
  Words: ['unilav', '1700026200007595', 'pdf']
  Keywords matched: ['unilav']
  Date in filename: ['1700026200007595']

Vector: [0.15, 1.00, 1.00]
        ↑     ↑     ↑
        3/20  match date
```

#### 5. Statistical (6 dimensioni)

```python
Text statistics:
  Words: 120
  Unique words: 85
  Avg word length: 6.2
  Special chars density: 0.12
  Digit density: 0.08
  Upper density: 0.15

Vector: [0.02, 0.04, 0.31, 0.12, 0.08, 0.15]
        ↑     ↑     ↑     ↑     ↑     ↑
        120/  85/   6.2/  0.12  0.08  0.15
        5000  2000  20
```

### Vettore Finale (519 numeri)

```python
feature_vector = [
    # TF-IDF (500)
    0.00, 0.45, 0.00, 0.38, 0.42, ..., 0.00,
    
    # NER (5)
    0.30, 0.00, 0.20, 0.15, 0.05,
    
    # Pattern (5)
    0.40, 0.00, 0.15, 0.05, 0.20,
    
    # Filename (3)
    0.15, 1.00, 1.00,
    
    # Statistical (6)
    0.02, 0.04, 0.31, 0.12, 0.08, 0.15
]

Shape: (519,)
Type: numpy.ndarray float32
```

Questo vettore viene poi passato al modello RandomForest per la predizione! 🎯

---

## 🔄 Processo Completo

```
FILE PDF
   ↓
OCR (pytesseract/pdfplumber)
   ↓
TESTO ESTRATTO
   ↓
┌──────────────────────────────────────┐
│  FEATURE EXTRACTOR                   │
├──────────────────────────────────────┤
│  1. TF-IDF Vectorization (500)       │
│  2. NER spaCy (5)                    │
│  3. Regex Patterns (5)               │
│  4. Filename Analysis (3)            │
│  5. Text Statistics (6)              │
└──────────────────────────────────────┘
   ↓
FEATURE VECTOR (519 dimensioni)
   ↓
RANDOM FOREST MODEL
   ↓
PREDICTION: "UNILAV" (99.6% confidence)
```

---

## 📈 Importanza Features

Durante il training, RandomForest calcola l'importanza di ogni feature:

```python
Top 20 features più importanti (esempio):

1. 'unilav' (TF-IDF)                    → 0.085
2. 'comunicazione' (TF-IDF)             → 0.072
3. 'codici_fiscali_count' (Pattern)     → 0.068
4. 'keyword_match' (Filename)           → 0.065
5. 'assunzione' (TF-IDF)                → 0.061
6. 'codice_comunicazione' (TF-IDF)      → 0.058
7. 'persons_count' (NER)                → 0.055
8. 'cedolino' (TF-IDF)                  → 0.052
9. 'date_count' (Pattern)               → 0.049
10. 'f24' (TF-IDF)                      → 0.047
... altre 509 features
```

Le features TF-IDF dominano perché sono le più numerose e specifiche! 🎯

---

**Documento creato**: 26 Febbraio 2026  
**Versione**: 1.0.0  
**Autore**: Sistema AI MyGest
