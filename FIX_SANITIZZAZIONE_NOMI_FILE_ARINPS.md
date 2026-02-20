# Fix Sanitizzazione Nomi File - Tipo Documento ARINPS

**Data**: 23 Gennaio 2026  
**Tipo Documento**: ARINPS - Avviso di rettifica INPS  
**Issue**: Caratteri non validi nei nomi file (slash `/` in campo periodo)

## 🔍 Problema Rilevato

### Situazione Iniziale
- **Pattern nome file**: `RettificaINPS_{attr:modello}_{attr:periodo}_{attr:matricola}_{cliente.anagrafica.codice}`
- **Valore attributo periodo**: `06/2025` (contiene slash)
- **Nome file generato**: `RettificaINPS_DM-2013_06/2025_3601978802_PERIAD01.pdf`
- **Problema**: Il sistema interpretava `06/` come directory invece che come parte del nome file

### Impatto
- Creazione di sottodirectory indesiderate (`06/`)
- Struttura file non conforme
- Possibili errori di accesso ai file

## ✅ Soluzioni Implementate

### 1. Sanitizzazione Automatica Nomi File

**File modificato**: `documenti/utils.py`

Aggiunta funzione `_sanitize_filename_part()` che rimuove/sostituisce caratteri non validi:
- `/` → `-` (slash)
- `\` → `-` (backslash)
- `:` → `-` (due punti)
- `*` → `-` (asterisco)
- `?` → `-` (punto interrogativo)
- `"` → `-` (virgolette)
- `<` → `-` (minore)
- `>` → `-` (maggiore)
- `|` → `-` (pipe)

**Caratteristiche**:
- Rimuove trattini e spazi multipli
- Strip di caratteri speciali all'inizio/fine
- Gestisce valori `None` ed empty string

**Applicata a tutti i token**:
- `{attr:codice}` e `{attr:codice.path}`
- `{uattr:codice}` e `{uattr:codice.path}`
- `{cliente}` e `{cliente.path}`

### 2. Validazione Campo Periodo

**Modifiche al database**:
```python
AttributoDefinizione.objects.filter(
    tipo_documento__codice='ARINPS',
    codice='periodo'
).update(
    regex=r'^(0[1-9]|1[0-2])/?[0-9]{4}$',
    help_text='Formato: MMAAAA (es. 062025) oppure MM/AAAA (es. 06/2025). Gli slash verranno sostituiti con trattino nel nome file.',
    max_length=7
)
```

**Validazione regex**: `^(0[1-9]|1[0-2])/?[0-9]{4}$`
- Mese: `01-12` (con zero padding obbligatorio)
- Separatore opzionale: `/`
- Anno: 4 cifre

**Formati accettati**:
- ✅ `06/2025` → sanitizzato in `06-2025`
- ✅ `062025` → resta `062025`
- ❌ `6/2025` → invalido (mese senza zero)
- ❌ `13/2024` → invalido (mese > 12)
- ❌ `00/2024` → invalido (mese = 00)

### 3. Test di Verifica

**File creato**: `documenti/tests/test_filename_sanitization.py`

Test coverage:
- Sanitizzazione singoli caratteri
- Sanitizzazione caratteri multipli
- Documento ARINPS completo
- Attributi con caratteri speciali
- Campo cliente.anagrafica.codice con caratteri speciali

## 📊 Risultati

### Prima delle Modifiche
```
Input periodo: "06/2025"
Nome file: RettificaINPS_DM-2013_06/2025_3601978802_PERIAD01.pdf
                                  ↑ PROBLEMA: slash crea directory
```

### Dopo le Modifiche
```
Input periodo: "06/2025"
Nome file: RettificaINPS_DM-2013_06-2025_3601978802_PERIAD01.pdf
                                  ↑ OK: trattino
```

## 🔄 File Esistenti

**Nota**: I file già salvati mantengono il nome originale con la struttura errata.

Per correggere i file esistenti:
1. I nuovi documenti useranno automaticamente la sanitizzazione
2. I documenti esistenti possono essere ri-salvati per applicare il nuovo pattern
3. Eventualmente creare uno script di migrazione per rinominare i file esistenti

## 🧪 Testing

### Test Unitari Funzione Sanitizzazione
```python
from documenti.utils import _sanitize_filename_part

assert _sanitize_filename_part("06/2025") == "06-2025"
assert _sanitize_filename_part("test\\file") == "test-file"
assert _sanitize_filename_part("file*name?") == "file-name-"
```

### Test Documento Completo
```python
from documenti.models import Documento
from documenti.utils import build_document_filename

doc = Documento.objects.get(id=357)
nome = build_document_filename(doc, "test.pdf")
assert "/" not in nome
assert "\\" not in nome
# Output: RettificaINPS_DM-2013_06-2025_3601978802_PERIAD01.pdf
```

### Validazione Regex Periodo
```python
import re
regex = re.compile(r'^(0[1-9]|1[0-2])/?[0-9]{4}$')

assert regex.match("06/2025")  # ✅ Valido
assert regex.match("062025")   # ✅ Valido
assert regex.match("12/2024")  # ✅ Valido
assert not regex.match("13/2024")  # ❌ Invalido
assert not regex.match("6/2025")   # ❌ Invalido
```

## 🎯 Benefici

1. **Compatibilità Filesystem**: Nomi file validi su Windows, Linux, macOS
2. **Prevenzione Errori**: Nessuna creazione involontaria di directory
3. **Validazione Input**: Formato periodo standardizzato con feedback utente
4. **Robustezza**: Sanitizzazione applicata a tutti i token dinamici
5. **Estensibilità**: Facile aggiungere altri caratteri da sanitizzare

## 📝 Modifiche File

### Modificati
- `documenti/utils.py`: Aggiunta `_sanitize_filename_part()` e applicazione a tutti i token

### Creati
- `documenti/tests/test_filename_sanitization.py`: Suite completa di test

### Database
- `AttributoDefinizione` (periodo): Aggiunta regex, help_text, max_length

## 🔮 Prossimi Passi

1. ✅ **Implementato**: Sanitizzazione automatica
2. ✅ **Implementato**: Validazione campo periodo
3. ✅ **Implementato**: Test unitari
4. ⏳ **Opzionale**: Script migrazione per rinominare file esistenti
5. ⏳ **Opzionale**: Estendere validazione ad altri campi attributo

## 📌 Note Tecniche

- La sanitizzazione avviene durante `build_document_filename()` prima del salvataggio
- I caratteri vengono sostituiti con **trattino** (non rimossi) per mantenere leggibilità
- I trattini multipli vengono ridotti a singolo trattino
- La validazione regex è case-insensitive e applicata lato Django form/serializer

---

**Stato**: ✅ Implementato e Testato  
**Versione**: 1.0  
**Autore**: Sistema Automatico
