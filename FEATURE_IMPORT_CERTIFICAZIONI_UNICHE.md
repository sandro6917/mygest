# Feature: Import Semplificato Certificazioni Uniche (CU)

## 📋 Panoramica

Sistema di importazione batch per **Certificazioni Uniche (CU)** - documenti fiscali rilasciati annualmente dal sostituto d'imposta (datore di lavoro) ai dipendenti.

## 🎯 Obiettivo

Importare in **MyGest** file ZIP contenenti CU di tutti i dipendenti dello stesso datore di lavoro, con parsing automatico dei dati fiscali e creazione documenti strutturati.

## 📁 Struttura File ZIP

### Formato Previsto

```
CU_2024_ACME_SRL.zip
├── CU_2024_RSSMRA80A01H501U.pdf  (CU di Mario Rossi)
├── CU_2024_BNCLGU75B15F205X.pdf  (CU di Luigi Bianchi)
├── CU_2024_VRDNNA85C50A794Y.pdf  (CU di Anna Verdi)
└── ...
```

### Naming Convention File PDF (opzionale)

Pattern supportati (per fallback parsing):
- `CU_2024_RSSMRA80A01H501U.pdf` → Anno + CF dipendente
- `2024_CU_RSSMRA80A01H501U.pdf` → Anno + CF dipendente
- `CU_ROSSI_MARIO_2024.pdf` → Anno generico

**NOTA**: Il parser estrae sempre i dati dal **contenuto PDF**, il nome file è solo fallback.

## 🛠️ Setup Iniziale

### 1. Eseguire Management Command

```bash
python manage.py setup_cu
```

**Cosa fa:**
- ✅ Crea tipo documento `CU` (Certificazione Unica)
- ✅ Crea 9 attributi dinamici (anno, dipendente, dati fiscali)
- ✅ Crea voce titolario `HR-CU` (Human Resources → Certificazioni Uniche)
- ✅ Configura pattern codice: `{CLI}-CU-{ANNO}-{SEQ:03d}`
- ✅ Configura pattern nome file: `{attr:dipendente.codice}_CU_{attr:anno_riferimento}.pdf`

### 2. Verifica Prerequisiti

**Voce Titolario HR** (Parent):
- Deve esistere voce `HR` (Human Resources)
- Se non esiste, crearla manualmente o eseguire setup titolario

**Voce Titolario HR-PERS** (per intestazioni dipendenti):
- Voce `HR-PERS` (Dossier personale)
- Permette intestazioni individuali: `HR-PERS/{CODICE_DIPENDENTE}`

## 📊 Modello Dati

### Documento CU

| Campo                    | Tipo       | Descrizione                              |
|--------------------------|------------|------------------------------------------|
| `tipo`                   | FK         | Tipo documento `CU`                      |
| `cliente`                | FK         | Datore di lavoro (sostituto d'imposta)   |
| `titolario_voce`         | FK         | Voce intestata dipendente (HR-PERS/XXX)  |
| `descrizione`            | STR        | Es. "CU 2024 - ROSSI MARIO"              |
| `data_documento`         | DATE       | 31/12/{anno_riferimento}                 |
| `stato`                  | CHOICE     | `definitivo` (auto)                      |
| `digitale`               | BOOL       | `True`                                   |
| `tracciabile`            | BOOL       | `True`                                   |
| `file`                   | FILE       | PDF Certificazione Unica                 |

### Attributi Dinamici CU

| Codice                        | Tipo   | Required | Descrizione                              |
|-------------------------------|--------|----------|------------------------------------------|
| `anno_riferimento`            | INT    | ✅        | Anno fiscale (es. 2024)                  |
| `dipendente`                  | INT    | ✅        | ID Anagrafica percipiente                |
| `tipo_certificazione`         | STR    | ❌        | Es. "Ordinaria", "Soggetto estero"       |
| `redditi_lavoro_dipendente`   | STR    | ❌        | Punto 1 - Formato: "12.345,67"           |
| `ritenute_irpef`              | STR    | ❌        | Punto 4 - Formato: "3.456,78"            |
| `addizionale_regionale`       | STR    | ❌        | Punto 5 - Formato: "234,56"              |
| `addizionale_comunale`        | STR    | ❌        | Punto 6 - Formato: "123,45"              |
| `contributi_previdenziali`    | STR    | ❌        | Contributi dipendente                    |
| `bonus_renzi`                 | STR    | ❌        | Trattamento integrativo                  |

## 🔄 Workflow Import

### 1. Accedi alla Pagina Import

**Frontend**:
```
Documenti → Importa Documenti → Certificazioni Uniche
```

**Endpoint**:
```
GET /import
→ Selezione tipo: "certificazioni_uniche"
```

### 2. Upload File ZIP

- **Estensioni supportate**: `.zip`, `.pdf` (singolo)
- **Dimensione max**: 50MB (configurabile)
- **Modalità**: Batch (multipli documenti in ZIP)

### 3. Sistema Elabora

**Backend Processing** (`documenti/import_cu.py`):

```python
from documenti.import_cu import CUImporter

importer = CUImporter(
    zip_file=uploaded_file,
    user=request.user,
    duplicate_policy='skip'  # 'skip' | 'replace' | 'add'
)

risultati = importer.importa()
```

**Step Elaborazione**:
1. ✅ Estrazione ZIP
2. ✅ Loop per ogni PDF:
   - **Parse** CU con `cu_parser.py`
   - **Estrae** dati sostituto (datore)
   - **Estrae** dati percipiente (dipendente)
   - **Estrae** dati fiscali (redditi, ritenute, etc.)
3. ✅ **Validazione** dati essenziali (CF sostituto, CF percipiente, anno)
4. ✅ **Ricerca/Creazione** anagrafica datore
5. ✅ **Ricerca/Creazione** cliente datore
6. ✅ **Ricerca/Creazione** anagrafica dipendente
7. ✅ **Ricerca/Creazione** voce titolario intestata `HR-PERS/{CODICE_DIP}`
8. ✅ **Controllo duplicati** (stesso dipendente + anno)
9. ✅ **Creazione/Sovrascrittura** documento CU
10. ✅ **Salvataggio** attributi dinamici
11. ✅ **Rigenera** codice documento (con attributi)

### 4. Risultati Import

**Response**:
```json
{
  "created": 15,
  "replaced": 0,
  "skipped": 2,
  "errors": [],
  "warnings": [],
  "documenti": [
    {
      "id": 123,
      "codice": "ROSMAR-CU-2024-001",
      "descrizione": "CU 2024 - ROSSI MARIO",
      "filename": "CU_2024_RSSMRA80A01H501U.pdf",
      "action": "creato"
    },
    ...
  ],
  "total": 17
}
```

## 🔍 Parser CU (`cu_parser.py`)

### Funzione Principale

```python
from documenti.parsers.cu_parser import parse_cu_pdf

result = parse_cu_pdf('/path/to/cu.pdf')
# Returns: CUParseResult
```

### Dati Estratti

#### Sostituto d'Imposta (Datore)
```python
result['sostituto'] = {
    'codice_fiscale': '12345678901',  # CF o P.IVA (11 cifre PG, 16 PF)
    'denominazione': 'ACME SRL',
    'partita_iva': '12345678901',
    'comune': 'Milano',
    'provincia': 'MI',
    'indirizzo': 'Via Roma 123',
    'cap': '20100',
}
```

#### Percipiente (Dipendente)
```python
result['percipiente'] = {
    'codice_fiscale': 'RSSMRA80A01H501U',
    'cognome': 'Rossi',
    'nome': 'Mario',
    'data_nascita': '01/01/1980',
    'comune_nascita': 'Roma',
    'provincia_nascita': 'RM',
    'comune_residenza': 'Milano',
    'provincia_residenza': 'MI',
    'indirizzo_residenza': 'Via Dante 45',
    'cap_residenza': '20121',
}
```

#### Dati Fiscali CU
```python
result['cu'] = {
    'anno_riferimento': 2024,
    'tipo_certificazione': 'Ordinaria',
    'redditi_lavoro_dipendente': '28.500,00',
    'ritenute_irpef': '6.840,00',
    'addizionale_regionale': '570,00',
    'addizionale_comunale': '285,00',
    'contributi_previdenziali': '2.565,00',
    'bonus_renzi': '1.200,00',
}
```

### Strategie Parsing

**Pattern Matching**:
- **Sezioni**: "SOSTITUTO D'IMPOSTA", "PERCIPIENTE", "CERTIFICAZIONE"
- **Codici Fiscali**: Regex `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` (16 caratteri) o `\d{11}` (P.IVA)
- **Importi**: Regex `\d{1,3}(?:\.\d{3})*(?:,\d{2})?` (formato italiano)
- **Date**: Regex `\d{2}[/-]\d{2}[/-]\d{4}`
- **Punti CU**: "PUNTO 1", "PUNTO 4", "PUNTO 5", etc.

## ⚙️ Configurazione

### Gestione Duplicati

**Policy disponibili** (`duplicate_policy`):

| Policy     | Comportamento                                          |
|------------|--------------------------------------------------------|
| `skip`     | ⏭️  Salta documento se già esiste (default)            |
| `replace`  | 🔄 Sostituisci documento esistente + attributi         |
| `add`      | ➕ Crea comunque nuovo documento (duplicato consapevole) |

**Logica Duplicati**:
```python
# Duplicato = stesso dipendente + stesso anno
documento = Documento.objects.filter(
    tipo=tipo_cu,
    attributi_valori__definizione__codice='dipendente',
    attributi_valori__valore=str(dipendente.id),
    data_documento__year=anno_riferimento
).first()
```

### Titolario Intestato

**Gerarchia automatica**:
```
HR (Human Resources)
└── HR-PERS (Dossier personale)
    ├── ROSMAR (Dossier Mario Rossi)
    │   ├── CU 2024
    │   ├── CU 2023
    │   └── ...
    ├── BIALUI (Dossier Luigi Bianchi)
    └── ...
```

**Pattern generazione voce**:
- **Codice**: Codice anagrafica dipendente (es. `ROSMAR`)
- **Titolo**: `"Dossier {Cognome} {Nome}"`
- **Parent**: `HR-PERS`
- **Anagrafica collegata**: FK → dipendente
- **Pattern codice doc**: `{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}`

## 🧪 Testing

### Test Manuale

```bash
# 1. Setup
python manage.py setup_cu

# 2. Prepara file ZIP test
# CU_2024_TEST.zip con 3-5 PDF CU

# 3. Import via UI o API
# POST /api/v1/import-sessions/
# Body: tipo_importazione=certificazioni_uniche, file=CU_2024_TEST.zip

# 4. Verifica risultati
# GET /api/v1/import-sessions/{uuid}/
```

### Test Unitario

```python
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from documenti.import_cu import CUImporter

@pytest.mark.django_db
def test_import_cu():
    # Prepara ZIP test
    zip_content = b'...'  # ZIP con CU test
    zip_file = SimpleUploadedFile('cu_test.zip', zip_content, content_type='application/zip')
    
    # Import
    importer = CUImporter(zip_file, user=None, duplicate_policy='skip')
    risultati = importer.importa()
    
    # Assert
    assert risultati['created'] > 0
    assert len(risultati['errors']) == 0
    assert risultati['documenti'][0]['codice'].startswith('CLI')
```

## 📝 Note Implementative

### File Creati

1. **Backend**:
   - ✅ `documenti/models.py` → Aggiunto `certificazioni_uniche` a `ImportSession.TIPO_CHOICES`
   - ✅ `documenti/parsers/cu_parser.py` → Parser PDF CU (nuovo)
   - ✅ `documenti/import_cu.py` → Importer batch CU (nuovo)
   - ✅ `documenti/management/commands/setup_cu.py` → Setup command (nuovo)

2. **Frontend**:
   - ✅ `frontend/src/api/import.ts` → Aggiunto `certificazioni_uniche` a `TipoImportazione`
   - ✅ `frontend/src/pages/ImportSelectionPage.tsx` → Icona + descrizione CU

### Dipendenze

**Python packages** (già presenti):
- `pdfplumber` → Estrazione testo PDF
- `zipfile` → Gestione ZIP
- `django.db.transaction` → Atomicità import

### Limitazioni

- ⚠️ Parser basato su **pattern testuali** → Layout PDF non standard può fallire
- ⚠️ Importi estratti come **stringhe** (formato italiano) → Conversione in Decimal va fatta esternamente se necessaria
- ⚠️ **Nessun OCR** → Se PDF è immagine scansionata, il parser fallisce

## 🚀 Quick Start

### Esempio Completo

```bash
# 1. Setup iniziale (una tantum)
python manage.py setup_cu

# 2. Prepara ZIP con CU dipendenti
# Struttura:
# CU_2024_ACME.zip
#   ├── CU_2024_RSSMRA80A01H501U.pdf
#   ├── CU_2024_BNCLGU75B15F205X.pdf
#   └── CU_2024_VRDNNA85C50A794Y.pdf

# 3. Import via UI
# → Vai su: http://localhost:5173/import
# → Seleziona: "Certificazioni Uniche"
# → Upload: CU_2024_ACME.zip
# → Conferma

# 4. Verifica risultati
# → Lista documenti: Filtro tipo = "CU"
# → Cliente: ACME SRL
# → Fascicoli individuali sotto HR-PERS/{CODICE_DIP}
```

## 🎯 Use Case

**Scenario**: Studio di consulenza del lavoro che gestisce contabilità per 20 aziende clienti.

**Ogni anno (circa aprile)**:
- Riceve ZIP con CU di tutti i dipendenti per ogni azienda
- File ZIP: 5-200 PDF per azienda (dipende dal numero dipendenti)

**Con MyGest**:
1. Upload ZIP → Import automatico
2. Sistema:
   - Crea/aggiorna anagrafiche datori e dipendenti
   - Crea documenti CU con dati fiscali
   - Organizza in titolario per dipendente
3. Risultato: 
   - Archivio digitale strutturato
   - Ricerca rapida CU per dipendente/anno
   - Storico completo redditi per pratica fiscale

## 📞 Support

**Errori comuni**:

| Errore                                  | Soluzione                                     |
|-----------------------------------------|-----------------------------------------------|
| "Tipo documento CU mancante"            | Eseguire `python manage.py setup_cu`         |
| "Voce titolario HR-CU non trovata"      | Eseguire `python manage.py setup_cu`         |
| "CF sostituto non trovato"              | Verificare layout PDF CU (possibile non standard) |
| "Anno di riferimento non trovato"       | Verificare nome file o contenuto PDF          |

**Contatti**:
- **Issue Tracker**: GitHub Issues
- **Email**: supporto@mygest.it

---

**Versione**: 1.0.0  
**Data**: 15 Marzo 2026  
**Autore**: Sandro Chimenti
