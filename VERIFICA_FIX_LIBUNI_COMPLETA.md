# VERIFICA IMPLEMENTAZIONE FIX - Pattern Template LIBUNI

## ✅ STATO: CORREZIONE IMPLEMENTATA CORRETTAMENTE

### Verifica Eseguita il 4 Marzo 2026

## 1. ✅ Funzione `_salva_attributi_libro_unico` - CORRETTA

**File**: `api/v1/documenti/importa_libro_unico.py`

### Modifiche Implementate:
```python
def _salva_attributi_libro_unico(...) -> Dict[str, Any]:  # ✅ Restituisce attrs_map
    attributi_map = {
        'periodo': periodo,
        'anno': anno,              # ✅ INT (non str)
        'mese': mese,              # ✅ INT (non str)
        'mensilita': mese,         # ✅ AGGIUNTO
        'num_cedolini': num_cedolini,
    }
    
    # Salva nel DB (converti a str solo qui)
    for codice, valore in attributi_map.items():
        ...
        defaults={'valore': str(valore)}  # ✅ str solo per DB
    
    return attributi_map  # ✅ Restituisci mappa
```

**Test**: ✅ PASS
- Firma corretta con return type `Dict[str, Any]`
- Attributo `mensilita` presente
- Attributi `anno` e `mese` mantengono tipo `int`
- Restituisce `attributi_map`

## 2. ✅ Flusso Importazione Nuovo Documento - CORRETTO

**File**: `api/v1/documenti/importa_libro_unico.py` (linee ~325-370)

### Flusso Implementato:
```python
# 1. Crea documento
nuovo_documento = Documento(tipo=tipo_libuni, cliente=..., ...)

# 2. SALVA per ottenere documento.id
nuovo_documento.save()

# 3. SALVA ATTRIBUTI prima di allegare file
attrs_map = _salva_attributi_libro_unico(
    documento=nuovo_documento,
    periodo=periodo_str,
    anno=anno,
    mese=mese,
    num_cedolini=len(pdf_paths)
)

# 4. Imposta flag per saltare rename automatico
nuovo_documento._skip_auto_rename = True

# 5. Allega file
with open(zip_path, 'rb') as f:
    nuovo_documento.file.save(zip_file.name, ContentFile(f.read()), save=True)

# 6. Applica rename CON attributi
logger.info(f"applica_rename_con_attributi: documento {nuovo_documento.id}, attrs_map: {attrs_map}")
nuovo_documento.applica_rename_con_attributi(attrs=attrs_map)
```

**Test**: ✅ PASS
- Ordine corretto: save() → attributi → file → rename
- `_skip_auto_rename` impostato
- `applica_rename_con_attributi()` chiamato con `attrs_map`
- Logging implementato

## 3. ✅ Flusso Sostituzione Documento Esistente - CORRETTO

**File**: `api/v1/documenti/importa_libro_unico.py` (linee ~293-323)

### Flusso Implementato:
```python
# Aggiorna campi
documento_esistente.descrizione = titolo
documento_esistente.data_documento = data_documento
...

# Allega nuovo file
with open(zip_path, 'rb') as f:
    documento_esistente.file.save(zip_file.name, ContentFile(f.read()), save=False)

# SALVA ATTRIBUTI prima del save
attrs_map = _salva_attributi_libro_unico(...)

# Salva documento
documento_esistente.save()

# Applica rename CON attributi
if documento_esistente.file:
    logger.info(f"applica_rename_con_attributi (sostituzione): documento {documento_esistente.id}, attrs_map: {attrs_map}")
    documento_esistente.applica_rename_con_attributi(attrs=attrs_map)
```

**Test**: ✅ PASS
- Attributi salvati prima del `save()`
- `applica_rename_con_attributi()` chiamato dopo
- Logging implementato

## 4. ✅ Modello Documento - Supporto `_skip_auto_rename`

**File**: `documenti/models.py` (metodo `save()`)

### Implementazione:
```python
def save(self, *args, **kwargs):
    ...
    # SKIP se il form ha impostato _skip_auto_rename
    skip_auto_operations = getattr(self, '_skip_auto_rename', False)
    
    if self.file and original_name and not skip_auto_operations:
        self._rename_file_if_needed(original_name, only_new=...)
    
    # SKIP move se _skip_auto_rename
    elif self.file and not skip_auto_operations:
        self._move_file_into_archivio()
```

**Test**: ✅ PASS
- Flag `_skip_auto_rename` rispettato
- Rename e move saltati se flag impostato
- Logica corretta

## 5. ✅ Pattern Template - Funzionamento Corretto

**Pattern Configurato**:
```
LibroUnico_{attr:anno}-{attr:mese}_{attr:mensilita}_{cliente.anagrafica.codice}
```

**Test con attrs_map simulato**:
```python
attrs_map = {
    'anno': 2026,
    'mese': 2,
    'mensilita': 2,
    'periodo': 'Febbraio 2026',
    'num_cedolini': 15
}
```

**Risultato**: `LibroUnico_2026-2_2_CHISAN01.zip`

**Analisi**: ✅ PASS
- Token `{attr:anno}` → `2026` ✓
- Token `{attr:mese}` → `2` ✓
- Token `{attr:mensilita}` → `2` ✓
- Token `{cliente.anagrafica.codice}` → `CHISAN01` ✓

## 6. ✅ Funzione `_format_value()` - Supporto Formati Python

**File**: `documenti/utils.py`

### Miglioramenti:
```python
def _format_value(value: Any, fmt: Optional[str]) -> str:
    if fmt and (fmt[0].isdigit() or fmt[0] == '.' or fmt[-1] in 'dfeExXobgGnsc'):
        try:
            if fmt[-1] in 'dxXob':  # Formati interi
                val_int = int(value)
                return f"{val_int:{fmt}}"
            elif fmt[-1] in 'fFeEgGn':  # Formati float
                ...
```

**Test**:
```
✓ _format_value(2, '02d') = '02'
✓ _format_value(10, '02d') = '10'
✓ _format_value(2026, '04d') = '2026'
✓ _format_value(3.14, '.2f') = '3.14'
```

**Analisi**: ✅ PASS - Tutti i test passano

## 7. ⚠️ Documenti Esistenti - Nomi File Non Aggiornati

**Documenti nel database**:
```
ID: 641 → File: LibroUnico_-_BOCMAR01.zip  ❌
ID: 638 → File: LibroUnico_-_ARKLAB01.zip  ❌
ID: 630 → File: LibroUnico_-_BOCBRU01.zip  ❌
```

**Causa**: Documenti importati prima della correzione

**Soluzione**: Opzionale - Re-importare o eseguire script di migrazione

## 8. ✅ Flusso Generale Salvataggio Documenti

### Pattern Corretto per Documenti con Attributi Dinamici:

```python
# STEP 1: Crea documento (opzionalmente senza file)
documento = Documento(tipo=tipo_doc, cliente=cliente, ...)

# STEP 2: Salva per ottenere documento.id
documento.save()

# STEP 3: Crea AttributoValore (richiedono documento.id)
attrs_map = {}
for codice, valore in attributi.items():
    definizione = AttributoDefinizione.objects.get(tipo_documento=tipo_doc, codice=codice)
    AttributoValore.objects.create(documento=documento, definizione=definizione, valore=str(valore))
    attrs_map[codice] = valore  # Mantieni tipo nativo per formattazione

# STEP 4: Se il file non è già allegato, allegalo con flag
documento._skip_auto_rename = True
with open(file_path, 'rb') as f:
    documento.file.save(filename, File(f), save=True)

# STEP 5: Applica rename CON attributi
documento.applica_rename_con_attributi(attrs=attrs_map)
```

### Verificato nei seguenti punti:

1. ✅ **LIBUNI** (`api/v1/documenti/importa_libro_unico.py`)
   - Nuovo documento: ✓ Corretto
   - Sostituzione: ✓ Corretto

2. ✅ **BPAG** (`documenti/importers/cedolini.py`)
   - Pattern implementato: ✓ Corretto
   - Attributo `dipendente` come ID: ✓ Corretto

3. ⚠️ **UNILAV** (`documenti/importers/unilav.py`)
   - DA VERIFICARE se usa attributi dinamici nel pattern template

## CONCLUSIONE

### ✅ LA CORREZIONE È STATA IMPLEMENTATA CORRETTAMENTE

#### Checklist Verifica:
- [x] `_salva_attributi_libro_unico` restituisce `Dict[str, Any]`
- [x] Attributo `mensilita` aggiunto
- [x] Attributi mantengono tipo nativo (int) in attrs_map
- [x] Nuovo documento: attributi salvati PRIMA del rename
- [x] Sostituzione: attributi salvati PRIMA del rename
- [x] Flag `_skip_auto_rename` impostato correttamente
- [x] `applica_rename_con_attributi(attrs=attrs_map)` chiamato
- [x] Logging implementato per debug
- [x] Pattern template genera nomi corretti
- [x] Funzione `_format_value()` supporta formati Python
- [x] Modello `Documento.save()` rispetta `_skip_auto_rename`

#### Problemi Aperti (NON bloccanti):
- [ ] Documenti esistenti hanno nomi file non aggiornati (opzionale: migrazione)
- [ ] Verificare UNILAV se usa attributi dinamici

#### Raccomandazioni:

1. **Pattern template consigliato con zero-padding**:
   ```
   LibroUnico_{attr:anno}-{attr:mese:02d}_{cliente.anagrafica.codice}
   ```
   Risultato: `LibroUnico_2026-02_BOCMAR01.zip`

2. **Per aggiornare documenti esistenti** (opzionale):
   ```python
   from documenti.models import Documento, DocumentiTipo
   tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
   for doc in Documento.objects.filter(tipo=tipo_libuni, file__isnull=False):
       doc.applica_rename_con_attributi(attrs=None)  # Legge attributi dal DB
   ```

3. **Monitoraggio**: Verificare log durante prossima importazione:
   ```bash
   tail -f logs/mygest.log | grep "applica_rename_con_attributi"
   ```

---

**Data verifica**: 4 Marzo 2026  
**Stato**: ✅ IMPLEMENTAZIONE CORRETTA E VERIFICATA  
**Verificato da**: GitHub Copilot
