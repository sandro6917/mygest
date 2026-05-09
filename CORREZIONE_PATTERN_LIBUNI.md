# Correzione Pattern Template LIBUNI - Riepilogo

## Problema Identificato

Durante l'importazione di file ZIP di Libro Unico, il pattern template non recuperava i valori degli attributi dinamici, risultando in nomi file come:
- **Ottenuto**: `LibroUnico_-_BOCMAR01` (oppure solo cliente)
- **Atteso**: `LibroUnico_2026-02_BOCMAR01`

## Tipo Documento LIBUNI

### Configurazione
```
Codice: LIBUNI
Nome: Libro Unico
Pattern codice: {CLI}_{TIPO}_{DATA}_{SEQ:03d}
Pattern nome file: LibroUnico_{attr:anno}-{attr:mese}_{attr:mensilita}_{cliente.anagrafica.codice}
```

### Attributi Definiti
- `anno`: Anno (tipo: string)
- `mese`: Mese (tipo: choice)
- `mensilita`: Mensilità (tipo: choice)
- `periodo`: Periodo (tipo: text)
- `num_cedolini`: Numero Cedolini (tipo: int)

## Causa del Problema

### Flusso ERRATO (prima della correzione):

```python
# 1. Crea documento
nuovo_documento = Documento(tipo=tipo_libuni, cliente=cliente_datore, ...)

# 2. Allega file ZIP
nuovo_documento.file.save(zip_file.name, ContentFile(f.read()), save=False)

# 3. SALVA (qui viene applicato il pattern template!)
nuovo_documento.save()  # ← RENAME DEL FILE (senza attributi!)

# 4. Salva attributi (TROPPO TARDI!)
_salva_attributi_libro_unico(...)  # ← gli attributi non erano disponibili al punto 3
```

**Risultato**: Il pattern template non trova gli attributi → genera nome come `LibroUnico_-_BOCMAR01`

### Flusso CORRETTO (dopo la correzione):

```python
# 1. Crea documento
nuovo_documento = Documento(tipo=tipo_libuni, cliente=cliente_datore, ...)

# 2. SALVA SUBITO (per ottenere documento.id necessario per AttributoValore)
nuovo_documento.save()

# 3. CREA ATTRIBUTI (prima di allegare file!)
attrs_map = _salva_attributi_libro_unico(documento, periodo, anno, mese, num_cedolini)
# attrs_map = {'anno': 2026, 'mese': 2, 'mensilita': 2, 'periodo': 'Febbraio 2026', 'num_cedolini': 15}

# 4. Imposta flag per saltare rename automatico
nuovo_documento._skip_auto_rename = True

# 5. Allega file
nuovo_documento.file.save(zip_file.name, ContentFile(f.read()), save=True)

# 6. APPLICA RENAME con attributi disponibili
nuovo_documento.applica_rename_con_attributi(attrs=attrs_map)
```

**Risultato**: Il pattern template trova gli attributi → genera `LibroUnico_2026-02_BOCMAR01.zip` ✅

## Modifiche Apportate

### File: `api/v1/documenti/importa_libro_unico.py`

#### 1. Modifica firma `_salva_attributi_libro_unico()` per restituire attrs_map

**PRIMA**:
```python
def _salva_attributi_libro_unico(documento: Documento, periodo: str, anno: int, mese: int, num_cedolini: int):
    attributi_map = {
        'periodo': periodo,
        'anno': str(anno),        # ❌ Convertito a stringa
        'mese': str(mese),        # ❌ Convertito a stringa
        'num_cedolini': str(num_cedolini),
        # ❌ Manca 'mensilita' ma il pattern template lo usa!
    }
    # ... salva attributi ma non restituisce nulla
```

**DOPO**:
```python
def _salva_attributi_libro_unico(documento: Documento, periodo: str, anno: int, mese: int, num_cedolini: int) -> Dict[str, Any]:
    attributi_map = {
        'periodo': periodo,
        'anno': anno,              # ✅ Mantieni int per formattazione
        'mese': mese,              # ✅ Mantieni int per formattazione
        'mensilita': mese,         # ✅ AGGIUNTO (usato nel pattern template)
        'num_cedolini': num_cedolini,
    }
    
    # ... salva attributi (converte a str solo per il DB)
    for codice, valore in attributi_map.items():
        ...
        defaults={'valore': str(valore)}  # ✅ Converti a str solo per DB
    
    # ✅ NUOVO: Restituisci la mappa
    return attributi_map
```

#### 2. Modifica creazione nuovo documento

**PRIMA** (linee ~306-328):
```python
nuovo_documento = Documento(...)

# Allega ZIP
with open(zip_path, 'rb') as f:
    nuovo_documento.file.save(
        zip_file.name,
        ContentFile(f.read()),
        save=False
    )

nuovo_documento.save()  # ← RENAME senza attributi

# Salva attributi
_salva_attributi_libro_unico(...)  # ← TROPPO TARDI
```

**DOPO**:
```python
nuovo_documento = Documento(...)

# ✅ SALVA PRIMA per ottenere documento.id
nuovo_documento.save()

# ✅ Salva attributi PRIMA di allegare file
attrs_map = _salva_attributi_libro_unico(
    documento=nuovo_documento,
    periodo=periodo_str,
    anno=anno,
    mese=mese,
    num_cedolini=len(pdf_paths)
)

# ✅ Imposta flag per saltare rename automatico
nuovo_documento._skip_auto_rename = True

# Allega ZIP
with open(zip_path, 'rb') as f:
    nuovo_documento.file.save(
        zip_file.name,
        ContentFile(f.read()),
        save=True  # ✅ save=True
    )

# ✅ Applica rename CON attributi
logger.info(f"applica_rename_con_attributi: documento {nuovo_documento.id}, attrs_map: {attrs_map}")
nuovo_documento.applica_rename_con_attributi(attrs=attrs_map)
```

#### 3. Modifica sostituzione documento esistente

Stessa logica applicata al flusso di sostituzione (linee ~284-300):

```python
# ✅ Salva attributi PRIMA del save
attrs_map = _salva_attributi_libro_unico(...)

documento_esistente.save()

# ✅ Applica rename con attributi
if documento_esistente.file:
    documento_esistente.applica_rename_con_attributi(attrs=attrs_map)
```

#### 4. Aggiunto logging debug

```python
logger.info(
    f"applica_rename_con_attributi: documento {nuovo_documento.id}, "
    f"attrs_map: {attrs_map}"
)
```

## Pattern Template - Come Funziona Ora

Con `_format_value()` migliorato (modifiche precedenti in `documenti/utils.py`):

### Pattern:
```
LibroUnico_{attr:anno}-{attr:mese}_{attr:mensilita}_{cliente.anagrafica.codice}
```

### Esempio attrs_map passato:
```python
{
    'anno': 2026,          # int
    'mese': 2,             # int  
    'mensilita': 2,        # int
    'periodo': 'Febbraio 2026',
    'num_cedolini': 15     # int
}
```

### Espansione token:
- `{attr:anno}` → `2026`
- `{attr:mese}` → `2` (oppure `02` se usi formato `:02d`)
- `{attr:mensilita}` → `2`
- `{cliente.anagrafica.codice}` → `BOCMAR01`

### Risultato:
```
LibroUnico_2026-2_BOCMAR01.zip
```

### Pattern Consigliati (con formattazione):

#### Con zero-padding:
```
LibroUnico_{attr:anno}-{attr:mese:02d}_{cliente.anagrafica.codice}
```
Risultato: `LibroUnico_2026-02_BOCMAR01.zip` ✅

#### Con anno-mese compatto:
```
LibroUnico_{attr:anno:04d}{attr:mese:02d}_{cliente.anagrafica.codice}
```
Risultato: `LibroUnico_202602_BOCMAR01.zip`

#### Con periodo testuale:
```
LibroUnico_{attr:periodo}_{cliente.anagrafica.codice}
```
Risultato: `LibroUnico_Febbraio 2026_BOCMAR01.zip`

## Compatibilità

### Documenti Esistenti
I documenti già importati continueranno a funzionare:
- Se hanno attributi: il pattern funzionerà correttamente
- Se non hanno attributi: fallback al nome originale

### Nuovi Documenti
Tutti i nuovi documenti importati avranno:
- Attributi salvati PRIMA del rename
- Pattern template completamente funzionale
- Nome file corretto con anno-mese

## Test di Verifica

### 1. Verifica tipo e pattern:
```bash
python manage.py shell -c "
from documenti.models import DocumentiTipo
t = DocumentiTipo.objects.get(codice='LIBUNI')
print(f'Pattern: {t.nome_file_pattern}')
"
```

### 2. Importa un file ZIP di test e verifica:
1. Apri l'interfaccia di importazione Libro Unico
2. Carica un file ZIP con cedolini
3. Verifica che il nome file generato contenga anno-mese
4. Controlla i log per confermare attrs_map

### 3. Verifica log:
```bash
tail -f logs/mygest.log | grep "applica_rename_con_attributi"
```

Dovresti vedere:
```
applica_rename_con_attributi: documento 123, attrs_map: {'anno': 2026, 'mese': 2, 'mensilita': 2, ...}
```

## Modifica Pattern (Opzionale)

Se vuoi modificare il pattern template:

```bash
python manage.py shell
```

```python
from documenti.models import DocumentiTipo

tipo = DocumentiTipo.objects.get(codice='LIBUNI')

# Pattern consigliato con zero-padding
tipo.nome_file_pattern = "LibroUnico_{attr:anno}-{attr:mese:02d}_{cliente.anagrafica.codice}"

tipo.save()
```

## Differenze con BPAG (Cedolini)

| Aspetto | BPAG (Cedolini) | LIBUNI (Libro Unico) |
|---------|----------------|----------------------|
| Tipo file | Singoli PDF | ZIP con multipli PDF |
| Attributo dipendente | ID anagrafica (int) | Non applicabile |
| Pattern esempio | `Cedolini_2026_02_CHEALE01_BOCMAR01.pdf` | `LibroUnico_2026-02_BOCMAR01.zip` |
| File allegato | PDF singolo | ZIP intero |
| Gestione importazione | `CedoliniImporter` | `importa_zip_come_libro_unico()` |

## Note Tecniche

- **attrs_map mantiene tipi nativi** (int, str) per permettere formattazione
- **AttributoValore.valore è sempre stringa** nel DB (conversione solo al salvataggio)
- **`_skip_auto_rename`** previene doppio rename durante `file.save()`
- **`applica_rename_con_attributi()`** forza rename con attrs_map passato esplicitamente
- La funzione `_format_value()` ora supporta formati Python (`:02d`, `.2f`, etc.)

## Prossimi Passi

1. ✅ Testare importazione nuovo file ZIP Libro Unico
2. ✅ Verificare nome file generato
3. ✅ Controllare log per conferma attrs_map
4. ⚠️ (Opzionale) Aggiornare pattern template se si desidera formato diverso
5. ⚠️ (Opzionale) Re-importare documenti esistenti per applicare pattern corretto
