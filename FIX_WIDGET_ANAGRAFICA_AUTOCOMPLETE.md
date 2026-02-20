# Fix Widget Autocomplete per Attributi Dinamici Anagrafica

## Problema
Nella pagina di creazione/modifica di un documento, quando un attributo dinamico è configurato come widget anagrafica (`widget='anagrafica'`), il form non mostrava una select con autocomplete, ma solo una select HTML standard senza funzionalità di ricerca.

## Soluzione Implementata

### 1. Modifiche al Form (`documenti/forms.py`)

Nel metodo `_build_attr_field` della classe `DocumentoDinamicoForm`, quando viene creato un `ModelChoiceField` per un attributo di tipo anagrafica, ora viene aggiunto un widget Select con gli attributi necessari per Select2:

```python
# Crea il widget Select con la classe select2 per l'autocomplete
select_widget = forms.Select(attrs={
    "class": "form-select select2",
    "data-placeholder": "Seleziona un'anagrafica",
    "data-allow-clear": "true",
    "style": "width: 100%;",
})
return forms.ModelChoiceField(queryset=qs, widget=select_widget, **common)
```

### 2. Modifiche ai Template

Aggiunti script JavaScript per inizializzare Select2 sui campi con classe `select2`:

#### `documenti/templates/documenti/nuovo_dinamico.html`
#### `documenti/templates/documenti/modifica_dinamico.html`

Aggiunto blocco `extra_js` che inizializza Select2:

```javascript
document.addEventListener("DOMContentLoaded", function() {
  // Inizializza Select2 su tutti i campi con classe select2
  $('.select2').each(function() {
    var $element = $(this);
    var placeholder = $element.data('placeholder') || 'Seleziona...';
    var allowClear = $element.data('allow-clear') !== undefined ? $element.data('allow-clear') : true;
    
    $element.select2({
      width: $element.data('width') || $element.css('width') || '100%',
      placeholder: placeholder,
      allowClear: allowClear,
      language: {
        noResults: function() {
          return "Nessun risultato trovato";
        },
        searching: function() {
          return "Ricerca in corso...";
        }
      }
    });
  });
});
```

### 3. Test

Creato file di test completo: `documenti/tests/test_widget_anagrafica_dinamico.py`

I test verificano:
- ✅ Il form contiene il widget select2 con gli attributi corretti
- ✅ Il rendering HTML include gli elementi Select2
- ✅ La view mostra correttamente il form con l'attributo anagrafica
- ✅ Il salvataggio funziona correttamente
- ✅ La modifica carica i valori esistenti correttamente

Tutti i test passano con successo.

## Funzionalità

Ora quando si crea o modifica un documento con attributi dinamici di tipo anagrafica:

1. Il campo viene renderizzato come una select con autocomplete
2. L'utente può cercare digitando il nome dell'anagrafica
3. Il campo mostra un placeholder personalizzato
4. È possibile cancellare la selezione con il pulsante X
5. L'interfaccia è coerente con altri campi select2 dell'applicazione

## File Modificati

- `documenti/forms.py`: Aggiunto widget Select2 per campi anagrafica
- `documenti/templates/documenti/nuovo_dinamico.html`: Aggiunto script inizializzazione Select2
- `documenti/templates/documenti/modifica_dinamico.html`: Aggiunto script inizializzazione Select2
- `documenti/tests/test_widget_anagrafica_dinamico.py`: Nuovo file di test (creato)

## Note Tecniche

- Select2 è già caricato globalmente in `templates/base.html`
- La classe CSS `select2` viene utilizzata come selettore per l'inizializzazione
- Il widget supporta tutte le opzioni standard di Select2 tramite attributi `data-*`
