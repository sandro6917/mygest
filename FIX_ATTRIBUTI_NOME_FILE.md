# Fix: Token {attr:} nei pattern dei nomi file

## Problema

Quando si salvava un documento con attributi dinamici, i token `{attr:}` nel pattern del nome file (`DocumentiTipo.nome_file_pattern`) non venivano renderizzati correttamente. 

Ad esempio, con il pattern:
```
Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}
```

Solo `cliente.anagrafica.codice` veniva correttamente renderizzato, mentre i token `{attr:anno_riferimento}` e `{attr:mese_riferimento}` rimanevano vuoti.

## Causa

Il problema era nell'ordine di esecuzione nel metodo `save()` del form `DocumentoDinamicoForm`:

1. Il documento veniva salvato
2. Gli attributi dinamici venivano salvati nel database tramite `update_or_create`
3. Veniva chiamato `_rename_file_if_needed()` per rinominare il file

Durante il punto 3, la funzione `build_document_filename()` leggeva gli attributi dal database tramite `_attrs_map()`, ma a causa di problemi di cache delle query o isolamento delle transazioni, poteva non vedere i valori appena salvati.

## Soluzione

La soluzione implementata prevede:

1. **Modifica di `build_document_filename()` in `documenti/utils.py`**:
   - Aggiunto parametro opzionale `attrs` che permette di passare esplicitamente la mappa degli attributi
   - Se `attrs=None`, la funzione legge gli attributi dal DB come prima (retrocompatibilità)
   - Se `attrs` è fornito, usa direttamente quella mappa

2. **Modifica di `_rename_file_if_needed()` in `documenti/models.py`**:
   - Aggiunto parametro opzionale `attrs` che viene passato a `build_document_filename()`

3. **Modifica del metodo `save()` in `documenti/forms.py`**:
   - Durante il salvataggio degli attributi, viene costruita una mappa `attrs_map` con i valori appena salvati
   - Questa mappa viene passata esplicitamente a `_rename_file_if_needed()` per garantire che i valori corretti siano usati nella generazione del nome file

## Codice modificato

### `documenti/utils.py`

```python
def build_document_filename(doc: Any, original_name: str, attrs: Optional[Dict[str, Any]] = None) -> str:
    """
    Costruisce il nome file finale in base a DocumentiTipo.nome_file_pattern.
    
    :param doc: istanza del documento
    :param original_name: nome file originale
    :param attrs: dizionario opzionale di attributi (codice -> valore). Se None, vengono letti dal DB.
    """
    # ...
    
    # Se attrs non è fornito, lo leggiamo dal DB
    if attrs is None:
        attrs = _attrs_map(doc)
    
    # ... resto del codice
```

### `documenti/models.py`

```python
def _rename_file_if_needed(self, original_name: str, only_new: bool, attrs=None):
    """
    Rinomina il file secondo il pattern del tipo documento.
    
    :param original_name: nome file originale
    :param only_new: se True, rinomina solo i nuovi documenti
    :param attrs: dizionario opzionale di attributi (codice -> valore). Se None, vengono letti dal DB.
    """
    if not self.file:
        return
    if only_new and not self._state.adding:
        return

    desired = build_document_filename(self, original_name, attrs=attrs)
    # ... resto del codice
```

### `documenti/forms.py`

```python
def save(self, commit=True):
    # ... salvataggio documento ...
    
    # Salva attributi dinamici
    tipo = self._tipo or getattr(doc, "tipo", None)
    defs = AttributoDefinizione.objects.filter(tipo_documento=tipo)
    
    # Costruisci una mappa degli attributi aggiornati
    attrs_map = {}
    
    for d in defs:
        key = f"attr_{d.codice}"
        if key in self.cleaned_data:
            raw = self.cleaned_data[key]
            val = self._to_json_safe(d.tipo_dato, raw, widget=getattr(d, "widget", ""))
            AttributoValore.objects.update_or_create(
                documento=doc, definizione=d, defaults={"valore": val}
            )
            # Aggiungi alla mappa per passarla alla rinominazione
            attrs_map[d.codice] = val

    # Dopo aver salvato gli attributi, forza la rinomina con il pattern aggiornato
    if getattr(doc, "file", None):
        try:
            doc.percorso_archivio = doc._build_path()
            doc.save(update_fields=["percorso_archivio"])
            current_basename = os.path.basename(doc.file.name)
            # Passa la mappa degli attributi appena salvati per evitare cache stale
            doc._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
            doc._move_file_into_archivio()
        except Exception:
            pass
    
    return doc
```

## Test

Sono stati creati test specifici in `documenti/tests/test_filename_attr_tokens.py` per verificare:

1. **Token `{attr:}` con attributi stringa**: verifica che attributi semplici come anno e mese vengano renderizzati correttamente
2. **Token `{attr:}` con formato data**: verifica che attributi di tipo data con formato (es. `{attr:data:%Y%m%d}`) funzionino
3. **Passaggio esplicito della mappa**: verifica che il parametro `attrs` funzioni correttamente
4. **Token misti**: verifica che si possano combinare `{attr:}`, `{cliente.*}` e altri token
5. **Attributi mancanti**: verifica il comportamento quando un attributo non ha valore

Tutti i test passano, inclusi quelli pre-esistenti per verificare la retrocompatibilità.

## Retrocompatibilità

La modifica è completamente retrocompatibile:

- Il parametro `attrs` è opzionale in entrambe le funzioni
- Se non viene fornito, il comportamento è identico a prima (lettura dal DB)
- Tutti i test esistenti passano senza modifiche

## Data

9 dicembre 2024
