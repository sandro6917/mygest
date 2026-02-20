# Feature: Gestione Duplicati e Pattern Codice con Attributi Dinamici

## Data
29 Gennaio 2026

## Modifiche Implementate

### 1. Gestione Duplicati nell'Importazione Cedolini

#### Backend

**File modificati:**
- `documenti/import_cedolini.py`
- `api/v1/documenti/views.py`
- `api/v1/documenti/serializers.py`

**Funzionalità:**
- Aggiunto parametro `duplicate_policy` al `CedolinoImporter`
- Tre opzioni disponibili:
  - `skip`: Non importare se documento già esiste (default)
  - `replace`: Sostituire documento esistente
  - `add`: Aggiungere comunque il documento (crea duplicato)

**Logica di rilevamento duplicati:**
- Ricerca documenti esistenti per:
  - Stesso tipo (BPAG)
  - Stesso cliente
  - Stesso anno
  - Attributo `dipendente` uguale
  - Attributo `mese_riferimento` uguale
  - Attributo `mensilita` uguale

**Nuovi metodi:**
- `CedolinoImporter._trova_documento_esistente()`: Cerca documenti duplicati
- Aggiornato `_processa_cedolino()` con logica di gestione duplicati

**Risultati aggiornati:**
```python
{
    'created': int,      # Nuovi documenti creati
    'replaced': int,     # Documenti sostituiti
    'skipped': int,      # Documenti saltati
    'errors': [],        # Errori
    'warnings': [],      # Avvisi (es. documento saltato)
    'documenti': []      # Lista documenti processati
}
```

#### Frontend

**File modificati:**
- `frontend/src/pages/ImportaCedoliniPage.tsx`
- `frontend/src/api/documenti.ts`

**UI Aggiornata:**
- Aggiunto `RadioGroup` per selezionare la politica duplicati
- Tre opzioni visibili all'utente:
  - "Non importare se già esiste (consigliato)"
  - "Sostituisci documento esistente"
  - "Aggiungi comunque (crea duplicato)"

**Visualizzazione risultati:**
- Riepilogo con contatori separati: Nuovi, Sostituiti, Saltati, Errori
- Alert con informazioni dettagliate
- Warnings con informazioni su documenti saltati (filename, messaggio, azione)

### 2. Pattern Codice con Attributi Dinamici

#### Backend

**File modificati:**
- `documenti/models.py`

**Funzionalità:**
- Esteso il metodo `Documento._generate_codice()` per supportare attributi dinamici
- Nuovi placeholder disponibili:
  - `{ATTR:<codice>}`: Valore di un attributo dinamico
  - `{ATTR:<codice>.<campo>}`: Campo di un'anagrafica referenziata

**Esempi pattern:**
```python
# Pattern base (esistente)
"{CLI}-{TIT}-{ANNO}-{SEQ:03d}"  # LAFORT01-PAG-2025-001

# Pattern con attributo semplice
"{CLI}-{ATTR:tipo}-{ANNO}-{SEQ:02d}"  # LAFORT01-MENSILE-2025-01

# Pattern con attributo anagrafica
"{CLI}-{ATTR:dipendente.codice}-{ANNO}-{SEQ:02d}"  # LAFORT01-ROSMAR01-2025-01

# Pattern complesso
"{ATTR:tipo}-{ATTR:dipendente.codice}-{ANNO}{SEQ:04d}"  # MENSILE-ROSMAR01-20250001
```

**Nuovo metodo:**
- `Documento.rigenera_codice_con_attributi()`: Rigenera il codice dopo il salvataggio degli attributi
  - Utile quando il pattern usa attributi non disponibili alla creazione
  - Mantiene il numero sequenziale originale
  - Auto-chiamato dall'importer se il pattern contiene `{ATTR:`

**Logica di generazione:**
1. Documento salvato con codice temporaneo (solo placeholder base)
2. Attributi salvati nel database
3. Se pattern contiene `{ATTR:`, rigenerazione automatica del codice
4. Codice finale con tutti gli attributi risolti

#### Importazione Cedolini

**Aggiornamento flusso:**
```python
# 1. Salva documento con codice base
documento.save()

# 2. Salva attributi dinamici
self._salva_attributi(documento, ...)

# 3. Rigenera codice se pattern usa attributi
if '{ATTR:' in pattern:
    documento.rigenera_codice_con_attributi()
```

## Esempi d'Uso

### Importazione con gestione duplicati

**API Request:**
```bash
curl -X POST http://localhost:8000/api/v1/documenti/importa_cedolini/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@cedolini.zip" \
  -F "duplicate_policy=skip"  # o 'replace' o 'add'
```

**Response:**
```json
{
  "created": 5,
  "replaced": 1,
  "skipped": 2,
  "total": 8,
  "errors": [],
  "warnings": [
    {
      "filename": "cedolino_001.pdf",
      "message": "Documento già esistente: LAFORT01-PAG-2025-001",
      "action": "skipped"
    }
  ],
  "documenti": [
    {
      "id": 123,
      "codice": "LAFORT01-PAG-2025-001",
      "descrizione": "...",
      "filename": "...",
      "action": "replaced"
    }
  ]
}
```

### Pattern codice con attributi

**Configurazione Titolario:**
```python
# Admin Django → TitolarioVoce
pattern_codice = "{CLI}-{ATTR:dipendente.codice}-{ANNO}-{SEQ:02d}"
```

**Risultato:**
```
Cliente: LA FORTEZZA SRL (LAFORT01)
Dipendente: Mario Rossi (ROSMAR01)
Anno: 2025
Sequenza: 1

Codice generato: LAFORT01-ROSMAR01-2025-01
```

## Note Tecniche

### Transaction Handling
- Ogni cedolino è processato in una transazione atomica separata
- In caso di errore, il cedolino fallito non impedisce l'importazione degli altri
- Reporting dettagliato con totale/successi/errori

### Performance
- La ricerca duplicati usa `prefetch_related('attributi')` per ottimizzare le query
- Attributi caricati una sola volta per documento
- Regex compilata una sola volta per pattern matching

### Validazione
- `duplicate_policy` validato nel serializer (`skip | replace | add`)
- Pattern codice validato con fallback a pattern default in caso di errore
- Gestione graceful degli errori con logging dettagliato

## Testing

### Test manuale
```bash
# 1. Importa cedolini (prima volta)
# Policy: skip (default)
# Risultato: 6 creati

# 2. Reimporta stesso ZIP
# Policy: skip
# Risultato: 0 creati, 6 saltati, warnings con dettagli

# 3. Reimporta stesso ZIP
# Policy: replace
# Risultato: 0 creati, 6 sostituiti

# 4. Reimporta stesso ZIP
# Policy: add
# Risultato: 6 creati (duplicati)
```

### Verifica pattern attributi
```python
# Console Django
from documenti.models import Documento
from titolario.models import TitolarioVoce

# Modifica pattern
voce = TitolarioVoce.objects.get(id=107)
voce.pattern_codice = "{CLI}-{ATTR:dipendente.codice}-{ANNO}-{SEQ:02d}"
voce.save()

# Importa cedolini
# Codice generato: LAFORT01-ROSMAR01-2025-01
```

## Compatibilità
- ✅ Retrocompatibile: pattern esistenti continuano a funzionare
- ✅ Default policy 'skip': comportamento sicuro per evitare duplicati
- ✅ Attributi dinamici opzionali: pattern base sempre supportato

## Documentazione Aggiornata
- Help text nel serializer API
- Docstring nei metodi Python
- Commenti inline nel codice critico
- UI con label esplicativi
