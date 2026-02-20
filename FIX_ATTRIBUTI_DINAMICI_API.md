# Fix: Attributi dinamici nel nome file pattern - API

## Problema

Durante la creazione di un documento tramite **API REST**, i token `{attr:}` nel pattern del nome file (`DocumentiTipo.nome_file_pattern`) non venivano interpretati correttamente. Gli attributi dinamici rimanevano vuoti nel nome file.

### Esempio del Problema

Per un tipo documento con pattern:
```
Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}
```

Con attributi:
- `anno_riferimento`: "2024"
- `mese_riferimento`: "12"

**Risultato errato**: `Presenze__TESTCLI.pdf` (attributi vuoti)
**Risultato atteso**: `Presenze_202412_TESTCLI.pdf`

### Causa del Problema

Il problema era nel flusso di salvataggio dell'**API serializer** `DocumentoCreateUpdateSerializer`:

1. Il serializer creava l'istanza del documento
2. Impostava `documento._file_operation` per la gestione del file
3. **NON impostava** `documento._skip_auto_rename` 
4. Chiamava `documento.save()` che eseguiva automaticamente `_rename_file_if_needed()`
5. **A questo punto gli attributi dinamici NON erano ancora stati salvati nel database**
6. Solo dopo il save, il serializer salvava gli attributi tramite `_save_attributi()`
7. **NON c'era una seconda chiamata** a `_rename_file_if_needed()` con gli attributi aggiornati

Risultato: il file veniva rinominato PRIMA che gli attributi fossero disponibili, quindi i token `{attr:}` rimanevano vuoti.

## Soluzione Implementata

### File modificato: `api/v1/documenti/serializers.py`

#### 1. Metodo `create()`

**Modifiche apportate:**

1. **Aggiunto flag `_skip_auto_rename`** prima del save per disabilitare la rinominazione automatica nel `save()` del modello:
   ```python
   documento._skip_auto_rename = True
   ```

2. **Modificato `_save_attributi()`** per ritornare la mappa degli attributi salvati (`attrs_map`)

3. **Aggiunta rinominazione esplicita DOPO il salvataggio degli attributi**:
   ```python
   if documento.file:
       try:
           documento.percorso_archivio = documento._build_path()
           documento.save(update_fields=["percorso_archivio"])
           current_basename = os.path.basename(documento.file.name)
           # Passa la mappa degli attributi appena salvati
           documento._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
           documento._move_file_into_archivio(attrs=attrs_map)
       except Exception as e:
           logger.exception("Errore durante rinominazione/spostamento file...")
   ```

**Codice completo:**

```python
def create(self, validated_data):
    file_operation = validated_data.pop('file_operation', 'copy')
    attributi_data = validated_data.pop('attributi', None)
    delete_source = validated_data.pop('delete_source_file', False)
    source_path = validated_data.pop('source_file_path', '')
    
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    documento = Documento(**validated_data)
    documento._file_operation = file_operation
    # Indica al modello di NON rinominare automaticamente il file
    # perché lo faremo noi DOPO aver salvato gli attributi dinamici
    documento._skip_auto_rename = True
    self._run_model_clean(documento)
    documento.save()
    
    # Salva attributi se presenti e costruisci la mappa per la rinominazione
    attrs_map = {}
    if attributi_data:
        attrs_map = self._save_attributi(documento, attributi_data)
    
    # Dopo aver salvato gli attributi, forza la rinomina con il pattern aggiornato
    if documento.file:
        try:
            documento.percorso_archivio = documento._build_path()
            documento.save(update_fields=["percorso_archivio"])
            current_basename = os.path.basename(documento.file.name)
            # Passa la mappa degli attributi appena salvati per evitare cache stale
            logger.info(
                "API create: rinominazione file per documento id=%s con attrs=%s",
                documento.pk,
                attrs_map
            )
            documento._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
            documento._move_file_into_archivio(attrs=attrs_map)
        except Exception as e:
            logger.exception(
                "Errore durante rinominazione/spostamento file per documento id=%s: %s",
                documento.pk,
                str(e)
            )
    
    # Crea richiesta eliminazione se richiesto
    if delete_source and source_path:
        self._create_deletion_request(documento, source_path)
    
    return documento
```

#### 2. Metodo `update()`

Le stesse modifiche sono state applicate al metodo `update()` per garantire che anche durante l'aggiornamento di un documento gli attributi dinamici vengano correttamente interpretati nel pattern del nome file.

#### 3. Metodo `_save_attributi()`

Modificato per **ritornare la mappa degli attributi** salvati:

```python
def _save_attributi(self, documento, attributi_data):
    """Salva o aggiorna gli attributi del documento e ritorna la mappa degli attributi"""
    from documenti.models import AttributoValore, AttributoDefinizione
    
    attrs_map = {}
    
    for codice, valore in attributi_data.items():
        try:
            definizione = AttributoDefinizione.objects.get(
                tipo_documento=documento.tipo,
                codice=codice
            )
            
            AttributoValore.objects.update_or_create(
                documento=documento,
                definizione=definizione,
                defaults={'valore': valore}
            )
            
            # Aggiungi alla mappa per la rinominazione
            attrs_map[codice] = valore
            
        except AttributoDefinizione.DoesNotExist:
            pass
        except Exception:
            pass
    
    return attrs_map
```

## Test Implementati

È stato creato un nuovo file di test `api/v1/documenti/tests/test_api_attributi_nome_file.py` che verifica:

1. **Creazione documento via API** con attributi dinamici nel pattern
2. **Aggiornamento documento via API** con modifica attributi dinamici
3. **Verifica del nome file generato** che deve contenere i valori degli attributi

### Esecuzione dei test

```bash
python manage.py test api.v1.documenti.tests.test_api_attributi_nome_file
```

## Flusso Corretto Dopo il Fix

1. **Serializer crea il documento** con `_skip_auto_rename = True`
2. **Serializer chiama `documento.save()`** che NON rinomina il file
3. **Serializer salva gli attributi** nel database e costruisce `attrs_map`
4. **Serializer chiama esplicitamente** `_rename_file_if_needed()` passando `attrs_map`
5. **Il file viene rinominato** con il pattern completo includendo i valori degli attributi

## Coerenza con il Form

Questa soluzione rende il comportamento dell'API **coerente** con quello del form `DocumentoDinamicoForm` che già implementava lo stesso meccanismo (file `documenti/forms.py`).

## Vantaggi della Soluzione

1. ✅ **Gli attributi dinamici vengono interpretati correttamente** nel pattern del nome file
2. ✅ **Funziona sia in creazione che in aggiornamento** tramite API
3. ✅ **Coerente con il comportamento del form Django**
4. ✅ **Preserva la retrocompatibilità** (se non ci sono attributi, funziona come prima)
5. ✅ **Gestione degli errori robusta** (non blocca il salvataggio in caso di problemi con la rinominazione)

## Note

- Il fix è **retrocompatibile**: se un documento viene creato senza attributi o senza pattern, il comportamento rimane invariato
- La gestione degli errori durante la rinominazione è **non bloccante**: se c'è un problema, il documento viene comunque salvato
- I log dettagliati aiutano il **debugging** in caso di problemi

## Data Fix

11 dicembre 2024

## Riferimenti

- Issue originale: "Gli attributi dinamici nel pattern nome file non funzionano in fase di creazione"
- File modificato: `api/v1/documenti/serializers.py`
- Test aggiunto: `api/v1/documenti/tests/test_api_attributi_nome_file.py`
- Documentazione correlata: `FIX_ATTRIBUTI_NOME_FILE.md`, `FIX_ATTRIBUTI_DINAMICI_NOME_FILE.md`
