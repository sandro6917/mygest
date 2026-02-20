# Riepilogo Fix: Attributi Dinamici nel Pattern Nome File

## Problema Identificato

Durante la **creazione di un documento** (sia tramite form Django che tramite API REST), quando il pattern del nome file (`DocumentiTipo.nome_file_pattern`) contiene token di attributi dinamici `{attr:codice}`, questi non venivano interpretati correttamente e rimanevano vuoti nel nome file generato.

**Esempio:**
- Pattern: `Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}`
- Attributi: `anno_riferimento=2024`, `mese_riferimento=12`
- **Risultato errato**: `Presenze__TESTCLI.pdf` (attributi vuoti)
- **Risultato corretto**: `Presenze_202412_TESTCLI.pdf`

### Causa Radice

Il problema era nel **timing del salvataggio**:

1. Il modello `Documento.save()` veniva chiamato
2. Durante il save, veniva chiamato `_rename_file_if_needed()` che usava `build_document_filename()`
3. La funzione `build_document_filename()` leggeva gli attributi dal database
4. **Gli attributi NON erano ancora stati salvati** nel database
5. Risultato: i token `{attr:}` rimanevano vuoti

## Soluzioni Implementate

### 1. Form Django (già implementato precedentemente)

**File**: `documenti/forms.py`

Il form `DocumentoDinamicoForm` era già stato corretto in precedenza:
- Imposta `doc._skip_auto_rename = True` prima del save
- Salva gli attributi nel database
- Chiama manualmente `_rename_file_if_needed()` passando la mappa degli attributi

### 2. API REST (FIX ATTUALE)

**File**: `api/v1/documenti/serializers.py`

Il serializer `DocumentoCreateUpdateSerializer` è stato corretto per implementare lo stesso meccanismo:

#### Modifiche al metodo `create()`:
```python
# Imposta il flag per saltare la rinominazione automatica
documento._skip_auto_rename = True
documento.save()

# Salva gli attributi e ottieni la mappa
attrs_map = {}
if attributi_data:
    attrs_map = self._save_attributi(documento, attributi_data)

# Rinomina esplicitamente DOPO aver salvato gli attributi
if documento.file:
    documento._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
    documento._move_file_into_archivio(attrs=attrs_map)
```

#### Modifiche al metodo `update()`:
Stesse modifiche applicate anche al metodo `update()` per gestire l'aggiornamento dei documenti.

#### Modifiche al metodo `_save_attributi()`:
Il metodo ora **ritorna la mappa degli attributi** salvati:
```python
def _save_attributi(self, documento, attributi_data):
    attrs_map = {}
    for codice, valore in attributi_data.items():
        # ... salva attributo ...
        attrs_map[codice] = valore
    return attrs_map
```

## File Modificati

1. ✅ `api/v1/documenti/serializers.py` - Serializer API
2. ✅ `api/v1/documenti/tests/test_api_attributi_nome_file.py` - Test per API (nuovo)
3. ✅ `FIX_ATTRIBUTI_DINAMICI_API.md` - Documentazione del fix (nuovo)

## File Correlati (precedenti)

- `documenti/models.py` - Contiene `_rename_file_if_needed()` con parametro `attrs`
- `documenti/utils.py` - Contiene `build_document_filename()` con parametro `attrs`
- `documenti/forms.py` - Form già corretto precedentemente
- `FIX_ATTRIBUTI_NOME_FILE.md` - Documentazione del fix precedente per il form
- `FIX_ATTRIBUTI_DINAMICI_NOME_FILE.md` - Documentazione generale

## Verifica della Soluzione

### Test esistenti
```bash
# Test per il form Django
python manage.py test documenti.tests.test_filename_attr_tokens

# Test per i pattern in generale
python manage.py test documenti.tests.test_filename_pattern
```

### Test nuovi (API)
```bash
# Test per l'API REST
python manage.py test api.v1.documenti.tests.test_api_attributi_nome_file
```

### Test manuale
```bash
# Test manuale con script
python test_attributi_nome_file_manuale.py
```

## Flusso Corretto Post-Fix

### Creazione tramite Form Django:
1. Form crea documento con `_skip_auto_rename = True`
2. Form salva il documento (NO rinominazione automatica)
3. Form salva gli attributi nel DB
4. Form chiama `_rename_file_if_needed()` con `attrs_map` ✅
5. File rinominato correttamente con attributi

### Creazione tramite API REST:
1. Serializer crea documento con `_skip_auto_rename = True`
2. Serializer salva il documento (NO rinominazione automatica)
3. Serializer salva gli attributi nel DB e ottiene `attrs_map`
4. Serializer chiama `_rename_file_if_needed()` con `attrs_map` ✅
5. File rinominato correttamente con attributi

### Modifica tramite Form o API:
1. Documento esistente viene caricato
2. Flag `_skip_auto_rename = True` viene impostato
3. Documento viene salvato (NO rinominazione automatica)
4. Attributi vengono aggiornati nel DB
5. Rinominazione esplicita con `attrs_map` aggiornata ✅
6. File rinominato con i nuovi valori degli attributi

## Vantaggi della Soluzione

1. ✅ **Completezza**: funziona sia per form Django che per API REST
2. ✅ **Coerenza**: stesso comportamento in tutti i punti di ingresso
3. ✅ **Retrocompatibilità**: non rompe il codice esistente
4. ✅ **Robustezza**: gestione degli errori non bloccante
5. ✅ **Testabilità**: test automatici per verificare il comportamento
6. ✅ **Debugging**: log dettagliati per troubleshooting

## Note Importanti

- Il parametro `attrs` in `build_document_filename()` e `_rename_file_if_needed()` è **opzionale**
- Se `attrs=None`, viene mantenuto il comportamento legacy (lettura dal DB)
- Se `attrs` è fornito, vengono usati quei valori (evita problemi di cache/timing)
- La gestione degli errori è **non bloccante**: se la rinominazione fallisce, il documento viene comunque salvato

## Stato Attuale

✅ **PROBLEMA RISOLTO**

Gli attributi dinamici `{attr:}` nel pattern del nome file ora funzionano correttamente:
- ✅ In fase di creazione (form Django)
- ✅ In fase di creazione (API REST)
- ✅ In fase di modifica (form Django)
- ✅ In fase di modifica (API REST)

## Autore & Data

- **Autore**: GitHub Copilot
- **Data**: 11 dicembre 2024
- **Versione**: 1.0

## Riferimenti

- Issue: "Attributi dinamici nel pattern nome file falliscono in fase di creazione"
- Documentazione correlata:
  - `FIX_ATTRIBUTI_NOME_FILE.md` (fix form Django)
  - `FIX_ATTRIBUTI_DINAMICI_NOME_FILE.md` (documentazione generale)
  - `FIX_ATTRIBUTI_DINAMICI_API.md` (fix API REST - questo documento)
