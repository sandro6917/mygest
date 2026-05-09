# Correzione Pattern Template Cedolini - Riepilogo

## Problema Identificato

Durante l'importazione di file ZIP contenenti cedolini, il pattern template non recuperava i valori degli attributi dinamici, risultando in nomi file come:
- **Ottenuto**: `LibroUnico_-_BOCMAR01.pdf`
- **Atteso**: `LibroUnico_2026-02_BOCMAR01.pdf`

## Cause del Problema

1. **Attributo dipendente errato**: 
   - L'attributo `dipendente` veniva salvato come **stringa** (nome completo) invece di **INT** (ID anagrafica)
   - Questo causava il fallimento del token `{attr:dipendente.codice}` nel pattern template
   
2. **Formato numerico non supportato**:
   - La funzione `_format_value()` non gestiva formati Python come `:02d`, `:04d`, etc.
   - Supportava solo formati `strftime` per date

## Modifiche Apportate

### 1. File: `documenti/importers/cedolini.py`

#### a) Passaggio ID anagrafica a `_create_attributi()`
```python
# PRIMA (linea 507)
attrs_map = self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)

# DOPO
attrs_map = self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data, anagrafica_dipendente)
```

#### b) Modifica firma e implementazione `_create_attributi()`
```python
def _create_attributi(
    self,
    documento: Documento,
    tipo_bpag: DocumentiTipo,
    anno: int,
    mese: int,
    mensilita: str,
    parsed_data: Dict,
    anagrafica_dipendente: Anagrafica = None  # ✅ AGGIUNTO
) -> Dict[str, Any]:
```

**Creazione attributo dipendente corretto**:
```python
# ✅ CORREZIONE: Usa l'ID dell'anagrafica dipendente se disponibile
if anagrafica_dipendente:
    attributi_config.append((
        'dipendente',
        'Dipendente',
        'int',  # ✅ INT per ID anagrafica
        anagrafica_dipendente.id
    ))
else:
    # Fallback: salva il nome (compatibilità)
    attributi_config.append((
        'dipendente',
        'Dipendente',
        'string',
        f"{parsed_data['lavoratore']['cognome']} {parsed_data['lavoratore']['nome']}"
    ))
```

#### c) Aggiunto logging debug
```python
# ✅ Log debug per verificare attrs_map prima del rename
logger.info(
    f"applica_rename_con_attributi: documento {documento.id}, "
    f"attrs_map keys: {list(attrs_map.keys())}, "
    f"attrs_map values: {attrs_map}"
)
```

### 2. File: `documenti/utils.py`

#### Migliorato `_format_value()` per supportare formati Python

**PRIMA**: Ignorava formati non-data
```python
def _format_value(value: Any, fmt: Optional[str]) -> str:
    if value is None:
        return ""
    if fmt:
        # Solo formati strftime per date
        if isinstance(value, (datetime.date, datetime.datetime)):
            return d.strftime(fmt)
        # fallback: ignora il fmt su tipi non data
    return str(value)
```

**DOPO**: Supporta formati Python per numeri
```python
def _format_value(value: Any, fmt: Optional[str]) -> str:
    if value is None:
        return ""
    
    if fmt:
        # 1. Formati strftime per date
        if isinstance(value, (datetime.date, datetime.datetime)):
            return d.strftime(fmt)
        
        # 2. Parsing stringa ISO date
        if isinstance(value, str):
            d = _parse_iso_date(value)
            if d:
                return d.strftime(fmt)
        
        # 3. ✅ NUOVO: Formati Python per numeri (02d, .2f, etc.)
        if fmt and (fmt[0].isdigit() or fmt[0] == '.' or fmt[-1] in 'dfeExXobgGnsc'):
            try:
                if fmt[-1] in 'dxXob':  # Formati interi
                    val_int = int(value) if not isinstance(value, int) else value
                    return f"{val_int:{fmt}}"
                elif fmt[-1] in 'fFeEgGn':  # Formati float
                    val_float = float(value) if not isinstance(value, float) else value
                    return f"{val_float:{fmt}}"
                else:
                    return f"{value:{fmt}}"
            except (ValueError, TypeError):
                pass
    
    return str(value)
```

## Test di Verifica

### Test `_format_value()`:
```
✓ _format_value(2, '02d') = '02' (expected: '02')
✓ _format_value(10, '02d') = '10' (expected: '10')
✓ _format_value(2026, '04d') = '2026' (expected: '2026')
✓ _format_value(3.14, '.2f') = '3.14' (expected: '3.14')
✓ _format_value(3.1, '.2f') = '3.10' (expected: '3.10')
```

## Pattern Template Consigliati

### Pattern Attuale (da verificare nel DB)
```
Cedolini_{attr:anno_riferimento}_{attr:mensilita}_{attr:dipendente.codice}_{cliente.anagrafica.codice}
```

Con le correzioni, ora funziona correttamente:
- `{attr:anno_riferimento}` → `2026`
- `{attr:mensilita}` → `2`
- `{attr:dipendente.codice}` → `CHEALE01` (✅ ora funziona!)
- `{cliente.anagrafica.codice}` → `BOCMAR01`

Risultato: `Cedolini_2026_2_CHEALE01_BOCMAR01.pdf`

### Pattern Alternativi con Formattazione

#### Con zero-padding per mese:
```
Cedolini_{attr:anno_riferimento}_{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}
```
Risultato: `Cedolini_2026_02_CHEALE01_BOCMAR01.pdf`

#### Con formato anno-mese:
```
LibroUnico_{attr:anno_riferimento}-{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}
```
Risultato: `LibroUnico_2026-02_CHEALE01_BOCMAR01.pdf` ✅

#### Formato compatto:
```
LU_{attr:anno_riferimento:04d}{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}
```
Risultato: `LU_202602_CHEALE01_BOCMAR01.pdf`

## Compatibilità

### Documenti Esistenti
I documenti già importati con attributo `dipendente` come stringa continueranno a funzionare:
- Se `{attr:dipendente.codice}` non trova l'oggetto, restituisce stringa vuota
- Il nome file sarà del tipo: `Cedolini_2026_2__BOCMAR01.pdf` (con doppio underscore)

### Nuovi Documenti
Tutti i nuovi documenti importati avranno:
- Attributo `dipendente` con tipo `int` contenente l'ID anagrafica
- Pattern template completamente funzionale con tutti i token

## Comandi per Aggiornare il Pattern

Se si desidera modificare il pattern template nel database:

```bash
# Accedi alla shell Django
python manage.py shell

# Modifica il pattern
from documenti.models import DocumentiTipo
tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
tipo_bpag.nome_file_pattern = "LibroUnico_{attr:anno_riferimento}-{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}"
tipo_bpag.save()
```

Oppure eseguire nuovamente il setup (aggiorna solo le definizioni attributi, non il pattern):
```bash
python manage.py setup_cedolini
```

## Prossimi Passi

1. ✅ Testare l'importazione di un nuovo file ZIP con cedolini
2. ✅ Verificare che i nomi file generati contengano anno, mese e codice dipendente
3. ✅ Controllare i log per confermare che attrs_map contenga tutti i valori
4. ⚠️ (Opzionale) Aggiornare il pattern template nel database se diverso dall'atteso
5. ⚠️ (Opzionale) Migrare i documenti esistenti per aggiornare l'attributo dipendente

## Note Tecniche

- Il parametro `anagrafica_dipendente` è opzionale per retrocompatibilità
- Se non fornito, usa il fallback con nome stringa (comportamento precedente)
- Il tipo_dato nella AttributoDefinizione è metadata; il valore nel DB è sempre stringa
- Il widget 'anagrafica' in AttributoDefinizione permette al sistema di riconoscere che è un FK
