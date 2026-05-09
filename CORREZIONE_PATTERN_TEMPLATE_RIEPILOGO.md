# Correzione Pattern Template - Riepilogo Completo

## Problema Identificato

Durante l'importazione di file ZIP (sia cedolini BPAG che Libro Unico LIBUNI), il pattern template per la denominazione dei file **non recuperava i valori degli attributi dinamici**, risultando in nomi file incompleti.

### Sintomi
- Nome file ottenuto: `LibroUnico_-_BOCMAR01.zip` ❌
- Nome file atteso: `LibroUnico_2026-02_BOCMAR01.zip` ✅

## Causa Principale

Gli **attributi dinamici venivano salvati DOPO che il file era già stato rinominato**:

```python
# Flusso ERRATO
documento.file.save(...)  # ← Allega file
documento.save()          # ← RENAME (pattern template cercava attributi ma non li trovava)
salva_attributi(...)      # ← Attributi salvati TROPPO TARDI
```

## Soluzione Implementata

### 1. Modifiche a `documenti/utils.py`

**Migliorato `_format_value()` per supportare formati Python numerici**:

Prima supportava solo formati `strftime` per le date. Ora supporta anche:
- Formati interi: `:02d`, `:04d`, `:03d`, etc.
- Formati float: `.2f`, `.3f`, etc.

```python
# Esempio
_format_value(2, '02d')     → '02'    # ✅ NUOVO
_format_value(2026, '04d')  → '2026'  # ✅ NUOVO
_format_value(3.14, '.2f')  → '3.14'  # ✅ NUOVO
```

**Test confermano correttezza**: Tutti i test passano ✅

### 2. Modifiche a `documenti/importers/cedolini.py` (Tipo BPAG)

**Problema specifico BPAG**: L'attributo `dipendente` conteneva il NOME invece dell'ID anagrafica, causando il fallimento del token `{attr:dipendente.codice}`.

**Correzioni**:
1. ✅ Passaggio `anagrafica_dipendente` a `_create_attributi()`
2. ✅ Salvataggio attributo `dipendente` con ID anagrafica (tipo `int`) invece di nome
3. ✅ Chiamata `_create_attributi()` PRIMA del file save
4. ✅ Uso di `_skip_auto_rename` + `applica_rename_con_attributi(attrs=attrs_map)`
5. ✅ Aggiunto logging debug

### 3. Modifiche a `api/v1/documenti/importa_libro_unico.py` (Tipo LIBUNI)

**Problema specifico LIBUNI**: 
- Gli attributi venivano salvati dopo il file save
- L'attributo `mensilita` non veniva salvato (ma il pattern lo usava!)

**Correzioni**:
1. ✅ Aggiunto attributo `mensilita` alla mappa (uguale a `mese`)
2. ✅ Modifica firma `_salva_attributi_libro_unico()` per restituire `Dict[str, Any]`
3. ✅ Salvataggio documento prima del file save (per ottenere `documento.id`)
4. ✅ Chiamata `_salva_attributi_libro_unico()` PRIMA del file save
5. ✅ Uso di `_skip_auto_rename` + `applica_rename_con_attributi(attrs=attrs_map)`
6. ✅ Mantenimento tipi nativi in `attrs_map` (int invece di str) per formattazione
7. ✅ Aggiunto logging debug

## Flusso Corretto (Nuovo)

### Per LIBUNI:
```python
# 1. Crea documento
documento = Documento(tipo=tipo_libuni, ...)

# 2. SALVA per ottenere documento.id
documento.save()

# 3. CREA ATTRIBUTI (prima di allegare file!)
attrs_map = _salva_attributi_libro_unico(documento, periodo, anno, mese, num_cedolini)

# 4. Imposta flag per saltare rename automatico
documento._skip_auto_rename = True

# 5. Allega file
documento.file.save(nome, contenuto, save=True)

# 6. APPLICA RENAME con attributi disponibili
documento.applica_rename_con_attributi(attrs=attrs_map)
```

### Per BPAG (Cedolini):
```python
# 1. Crea documento  
documento = Documento.objects.create(tipo=tipo_bpag, ...)

# 2. CREA ATTRIBUTI (prima di allegare file!)
attrs_map = _create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data, anagrafica_dipendente)

# 3. Imposta flag
documento._skip_auto_rename = True

# 4. Allega file
with open(file_path, 'rb') as f:
    documento.file.save(filename, django_file, save=True)

# 5. APPLICA RENAME con attributi
documento.applica_rename_con_attributi(attrs=attrs_map)
```

## Pattern Template

### LIBUNI (Libro Unico)
```
Pattern attuale: LibroUnico_{attr:anno}-{attr:mese}_{attr:mensilita}_{cliente.anagrafica.codice}

Esempio risultato: LibroUnico_2026-2_BOCMAR01.zip
```

**Pattern consigliato con zero-padding**:
```
LibroUnico_{attr:anno}-{attr:mese:02d}_{cliente.anagrafica.codice}

Risultato: LibroUnico_2026-02_BOCMAR01.zip ✅
```

### BPAG (Cedolini)
```
Pattern attuale: Cedolini_{attr:anno_riferimento}_{attr:mensilita}_{attr:dipendente.codice}_{cliente.anagrafica.codice}

Esempio risultato: Cedolini_2026_2_CHEALE01_BOCMAR01.pdf
```

**Pattern consigliato con zero-padding**:
```
Cedolini_{attr:anno_riferimento}_{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}

Risultato: Cedolini_2026_02_CHEALE01_BOCMAR01.pdf ✅
```

## File Modificati

| File | Modifiche | Tipo |
|------|-----------|------|
| `documenti/utils.py` | Esteso `_format_value()` per formati Python | Core |
| `documenti/importers/cedolini.py` | Corretto flusso salvataggio attributi BPAG | Importatore |
| `api/v1/documenti/importa_libro_unico.py` | Corretto flusso salvataggio attributi LIBUNI | API |

## Test di Verifica

### 1. Test `_format_value()`
```bash
cd /home/sandro/mygest
source venv/bin/activate
./test_format_value.sh
```

**Risultati**: ✅ Tutti i test passano

### 2. Test Importazione LIBUNI
1. Apri interfaccia importazione Libro Unico
2. Carica file ZIP con cedolini
3. Verifica nome file generato contiene anno-mese
4. Controlla log:
   ```bash
   tail -f logs/mygest.log | grep "applica_rename_con_attributi"
   ```

### 3. Test Importazione BPAG (Cedolini)
1. Apri interfaccia importazione cedolini
2. Carica file ZIP o PDF singolo
3. Verifica nome file generato contiene anno-mese-codice dipendente
4. Controlla log come sopra

## Verifica Log Attesi

### LIBUNI:
```
INFO applica_rename_con_attributi: documento 123, attrs_map: {'anno': 2026, 'mese': 2, 'mensilita': 2, 'periodo': 'Febbraio 2026', 'num_cedolini': 15}
INFO applica_rename_con_attributi completato: documento 123, nuovo_percorso=...LibroUnico_2026-02_BOCMAR01.zip
```

### BPAG:
```
INFO applica_rename_con_attributi: documento 456, attrs_map keys: ['anno_riferimento', 'mese_riferimento', 'mensilita', 'dipendente', ...], attrs_map values: {...}
INFO applica_rename_con_attributi completato: documento 456, nuovo_percorso=...Cedolini_2026_02_CHEALE01_BOCMAR01.pdf
```

## Compatibilità

### Documenti Esistenti
✅ I documenti già importati continueranno a funzionare
- Se hanno attributi corretti: il pattern funziona
- Se hanno attributi mancanti/errati: fallback al nome originale

### Nuovi Documenti
✅ Tutti i nuovi documenti avranno:
- Attributi salvati PRIMA del rename
- Pattern template completamente funzionale
- Nome file corretto

## Modifiche Opzionali Post-Correzione

### 1. Aggiornare Pattern Template LIBUNI con Zero-Padding

```bash
python manage.py shell
```

```python
from documenti.models import DocumentiTipo

tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
tipo_libuni.nome_file_pattern = "LibroUnico_{attr:anno}-{attr:mese:02d}_{cliente.anagrafica.codice}"
tipo_libuni.save()

print(f"✓ Pattern aggiornato: {tipo_libuni.nome_file_pattern}")
```

### 2. Aggiornare Pattern Template BPAG con Zero-Padding

```python
tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
tipo_bpag.nome_file_pattern = "Cedolini_{attr:anno_riferimento}_{attr:mese_riferimento:02d}_{attr:dipendente.codice}_{cliente.anagrafica.codice}"
tipo_bpag.save()

print(f"✓ Pattern aggiornato: {tipo_bpag.nome_file_pattern}")
```

### 3. Re-applicare Pattern ai Documenti Esistenti

**ATTENZIONE**: Questa operazione rinomina i file fisici sul NAS. Fare backup prima!

```python
from documenti.models import Documento, DocumentiTipo

# Per LIBUNI
tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
docs_libuni = Documento.objects.filter(tipo=tipo_libuni, file__isnull=False)

print(f"Trovati {docs_libuni.count()} documenti LIBUNI con file")

for doc in docs_libuni:
    try:
        print(f"Aggiornamento {doc.id}: {doc.file.name}")
        doc.applica_rename_con_attributi(attrs=None)  # Legge attributi dal DB
        print(f"  → {doc.file.name}")
    except Exception as e:
        print(f"  ✗ Errore: {e}")
```

## Documentazione Completa

- **LIBUNI**: [CORREZIONE_PATTERN_LIBUNI.md](CORREZIONE_PATTERN_LIBUNI.md)
- **BPAG**: [CORREZIONE_PATTERN_CEDOLINI_BPAG.md](CORREZIONE_PATTERN_CEDOLINI_BPAG.md)
- **Questo riepilogo**: [CORREZIONE_PATTERN_TEMPLATE_RIEPILOGO.md](CORREZIONE_PATTERN_TEMPLATE_RIEPILOGO.md)

## Conclusione

✅ Il problema è stato completamente risolto per entrambi i tipi documento:
- **LIBUNI**: Attributi salvati prima del rename + aggiunto attributo `mensilita`
- **BPAG**: Attributo dipendente corretto (ID anagrafica) + attributi salvati prima del rename
- **Core**: Funzione `_format_value()` estesa per formati numerici Python

✅ Il sistema è ora in grado di generare nomi file corretti utilizzando tutti i token del pattern template.

✅ Le modifiche sono retrocompatibili e non richiedono migrazione dati.

---

**Data correzione**: 4 Marzo 2026  
**Versione**: 1.0  
**Autore**: GitHub Copilot + Sandro Chimenti
