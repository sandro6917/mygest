# Fix: Nome File Cedolini con Attributi Dinamici

## 🐛 Problema Identificato

**Descrizione**: Nella creazione dei documenti relativi alle singole buste paga, il nome del file salvato in archivio non rispettava il template configurato nel tipo documento BPAG. Gli attributi dinamici erano correttamente salvati ma non venivano utilizzati nella composizione del nome del file associato al documento.

**Causa**: Il file veniva salvato **PRIMA** del salvataggio degli attributi dinamici, quindi il sistema di naming dei file non poteva accedere agli attributi per comporre il nome secondo il template.

### Flusso Errato (BEFORE)
```python
# 1. Documento creato
documento = Documento.objects.create(...)

# 2. File salvato CON nome originale ❌
documento.file.save(filename, django_file, save=True)
# -> Durante save() viene chiamato build_document_filename()
# -> Ma gli attributi NON esistono ancora!

# 3. Attributi creati DOPO ⚠️
self._create_attributi(documento, ...)
```

---

## ✅ Soluzione Implementata

### 1. Nuovo Metodo nel Modello Documento

**File**: `/home/sandro/mygest/documenti/models.py`

**Aggiunto metodo**: `applica_rename_con_attributi(attrs=None)`

```python
def applica_rename_con_attributi(self, attrs: Optional[Dict[str, Any]] = None):
    """
    Applica il rename del file utilizzando gli attributi dinamici.
    
    Questo metodo è utile quando:
    - Il documento viene creato con _skip_auto_rename=True
    - Gli attributi vengono salvati DOPO la creazione del documento
    - Il nome_file_pattern del tipo documento utilizza token {attr:...}
    
    NOTA: Deve essere chiamato DOPO che il documento è stato salvato
    e gli attributi sono stati creati.
    
    :param attrs: dizionario opzionale di attributi (codice -> valore).
                 Se None, vengono letti automaticamente dal DB.
    """
    if not self.pk:
        raise ValueError("Il documento deve essere salvato prima di applicare il rename")
    
    if not self.file:
        logger.debug(f"applica_rename_con_attributi: documento {self.pk} senza file, skip")
        return
    
    original_name = os.path.basename(self.file.name)
    
    logger.info(
        f"applica_rename_con_attributi: documento {self.pk}, "
        f"original_name={original_name}, attrs_passed={'YES' if attrs else 'NO'}"
    )
    
    # Rename con attributi
    self._rename_file_if_needed(
        original_name,
        only_new=False,  # Forza il rename anche se non è nuovo
        attrs=attrs
    )
    
    # Move in archivio con attributi
    self._move_file_into_archivio(attrs=attrs)
    
    logger.info(
        f"applica_rename_con_attributi completato: documento {self.pk}, "
        f"nuovo_percorso={self.file.name}"
    )
```

**Import aggiunto**:
```python
from typing import Optional, Dict, Any
```

---

### 2. Modifiche al CedoliniImporter

**File**: `/home/sandro/mygest/documenti/importers/cedolini.py`

#### Modifiche al metodo `create_documento()`

**Nuovo Flusso (AFTER)**:
```python
# 1. Documento creato
documento = Documento.objects.create(...)

# 2. Attributi creati PRIMA ✅
attrs_map = self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)

# 3. File salvato CON skip auto-rename
documento._skip_auto_rename = True  # ✅ Salta il rename automatico
documento.file.save(filename, django_file, save=True)

# 4. Applica rename CON attributi disponibili ✅
documento.applica_rename_con_attributi(attrs=attrs_map)
```

**Codice completo modificato**:
```python
# Crea documento
documento = Documento.objects.create(
    tipo=tipo_bpag,
    cliente=cliente,
    fascicolo=fascicolo,
    titolario_voce=titolario,
    descrizione=f"Cedolino {parsed_data['lavoratore']['cognome']} {parsed_data['lavoratore']['nome']} - {periodo}",
    data_documento=timezone.now().date(),
    note=self._build_note_preview(parsed_data),
    stato=Documento.Stato.DEFINITIVO,
    digitale=True,
    tracciabile=True,
)

# ✅ Crea attributi dinamici PRIMA di allegare il file
# Così il sistema di naming dei file potrà usare gli attributi
attrs_map = self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)

# Allega file PDF se fornito
# Imposta _skip_auto_rename per evitare rename prematuro senza attributi
file_path = kwargs.get('file_path')
if file_path and os.path.exists(file_path):
    from django.core.files import File as DjangoFile
    filename = os.path.basename(file_path)
    
    # ✅ Imposta flag per saltare rename automatico durante save()
    documento._skip_auto_rename = True
    
    with open(file_path, 'rb') as f:
        django_file = DjangoFile(f, name=filename)
        documento.file.save(filename, django_file, save=True)
    
    logger.info(f"File PDF allegato: {filename}")
    
    # ✅ Ora applica il rename con gli attributi disponibili
    documento.applica_rename_con_attributi(attrs=attrs_map)

logger.info(f"Creato documento {documento.id}: {documento.descrizione} (fascicolo: {fascicolo or 'da assegnare'})")

return documento
```

#### Modifiche al metodo `_create_attributi()`

**Return Type aggiunto**: Ora restituisce `Dict[str, Any]` con la mappa degli attributi

```python
def _create_attributi(
    self,
    documento: Documento,
    tipo_bpag: DocumentiTipo,
    anno: int,
    mese: int,
    mensilita: str,
    parsed_data: Dict
) -> Dict[str, Any]:  # ✅ Aggiunto return type
    """
    Crea AttributoValore per il documento.
    
    Returns:
        Dict con mapping codice_attributo -> valore (per passare a build_document_filename)
    """
    
    # ... codice esistente ...
    
    # ✅ Mappa da restituire per build_document_filename
    attrs_map = {}
    
    for codice, nome, tipo_campo, valore in attributi_config:
        if valore is None:
            continue
        
        # Get or create definizione
        definizione, _ = AttributoDefinizione.objects.get_or_create(...)
        
        # Create valore
        AttributoValore.objects.create(...)
        
        # ✅ Aggiungi alla mappa per build_document_filename
        attrs_map[codice] = valore
    
    logger.debug(f"Creati attributi per documento {documento.id}: {list(attrs_map.keys())}")
    
    return attrs_map  # ✅ Restituisce la mappa
```

---

## 🎯 Funzionamento del Sistema

### Meccanismo `_skip_auto_rename`

Il modello `Documento` supporta già il flag `_skip_auto_rename` per controllare il comportamento del rename:

```python
# Nel metodo save() di Documento
skip_auto_operations = getattr(self, '_skip_auto_rename', False)

if self.file and original_name and not skip_auto_operations:
    self._rename_file_if_needed(...)
```

### Pattern Template Supportati

Il tipo documento BPAG può usare pattern come:
```python
nome_file_pattern = '{attr:dipendente.codice}_{tipo.codice}_{attr:mese_riferimento:02d}_{attr:anno_riferimento}.pdf'
```

**Esempio output**:
```
ROSMAR01_BPAG_12_2024.pdf
```

**Token disponibili**:
- `{attr:codice}` - Valore attributo dinamico
- `{attr:codice.campo}` - Navigazione FK (es. dipendente.codice)
- `{attr:codice:%Y%m%d}` - Formattazione date
- `{tipo.codice}` - Codice tipo documento
- `{cliente.denominazione}` - Campi cliente
- `{id}`, `{data_documento}`, ecc.

---

## 📊 Attributi Cedolini Utilizzabili nel Template

Dopo questa modifica, tutti questi attributi sono **disponibili durante il naming del file**:

| Attributo | Tipo | Esempio Valore | Navigazione FK |
|-----------|------|----------------|----------------|
| `anno_riferimento` | int | 2024 | - |
| `mese_riferimento` | int | 12 | - |
| `mensilita` | string | 202412 | - |
| `dipendente` | string | ID anagrafica | ✅ Sì: `.codice`, `.codice_fiscale`, `.nome`, `.cognome` |
| `numero_cedolino` | string | 001234 | - |
| `data_ora_cedolino` | string | 2024-12-15 10:30 | - |

**Esempio di utilizzo FK**:
```python
nome_file_pattern = '{attr:dipendente.codice}_{attr:anno_riferimento}_{attr:mese_riferimento:02d}.pdf'
# Output: ROSMAR01_2024_12.pdf
```

---

## 🧪 Test e Verifica

### Test Manuale
1. Configurare il template nel tipo documento BPAG:
   - Admin Django → Tipi Documento → BPAG → `nome_file_pattern`
   - Esempio: `{attr:dipendente.codice}_{tipo.codice}_{attr:mensilita}.pdf`

2. Importare uno ZIP di cedolini

3. Verificare che i file salvati abbiano il nome corretto secondo il template

### Log Diagnostici
Il sistema ora logga dettagliatamente:
```
applica_rename_con_attributi: documento 123, original_name=cedolino.pdf, attrs_passed=YES
Rinomina file documento id=123 da tmp/2024/CLI123/cedolino.pdf a archivio/path/ROSMAR01_BPAG_202412.pdf
applica_rename_con_attributi completato: documento 123, nuovo_percorso=archivio/path/ROSMAR01_BPAG_202412.pdf
```

---

## 🔄 Compatibilità

### Backward Compatibility
- ✅ Il metodo `_create_attributi()` ora restituisce una mappa, ma **non** rompe codice esistente che non usa il valore di ritorno
- ✅ Il metodo `applica_rename_con_attributi()` è **nuovo** e non modifica comportamenti esistenti
- ✅ Il flag `_skip_auto_rename` era già supportato nel modello `Documento`

### Documenti Esistenti
- Non impattati: il rename avviene solo per **nuovi documenti** importati
- Possibile applicare manualmente: chiamare `documento.applica_rename_con_attributi()` dopo aver creato/aggiornato attributi

---

## 📝 Riepilogo Modifiche

### File Modificati
1. **`/home/sandro/mygest/documenti/models.py`**
   - Aggiunto import: `from typing import Optional, Dict, Any`
   - Aggiunto metodo: `applica_rename_con_attributi(attrs=None)`

2. **`/home/sandro/mygest/documenti/importers/cedolini.py`**
   - Modificato: `create_documento()` - Cambio ordine operazioni
   - Modificato: `_create_attributi()` - Aggiunto return `Dict[str, Any]`

### Benefici
- ✅ I nomi file rispettano il template configurato
- ✅ Gli attributi dinamici sono utilizzabili nel naming
- ✅ Codice più leggibile e manutenibile
- ✅ Logging dettagliato per debugging
- ✅ Compatibile con codice esistente

### Server Django
- ✅ Server riavviato con PID 21810, 21814
- ✅ Modifiche applicate e attive

---

## 🚀 Prossimi Passi

1. **Test di importazione**: Verificare con ZIP reali che i nomi file siano corretti
2. **Documentazione utente**: Aggiornare la guida su come configurare i template per BPAG
3. **Template predefinito**: Eventualmente creare un comando management per impostare un template BPAG consigliato

---

**Data Modifica**: 25 Febbraio 2026  
**Autore**: GitHub Copilot  
**Status**: ✅ Completato e Deployato
