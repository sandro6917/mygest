# Fix: Navigazione campi Anagrafica negli attributi dinamici del nome file

## Problema

Nel campo "Nome file pattern" di un tipo documento, era possibile inserire un riferimento ad un attributo dinamico di tipo "anagrafica" utilizzando la sintassi `{attr:dipendente.codice}`, ma questa sintassi non funzionava correttamente. 

Il problema era che quando un attributo dinamico utilizza il widget "anagrafica", il valore memorizzato nel database è solo l'**ID** dell'anagrafica (un intero), non l'oggetto Anagrafica stesso. Quando il sistema cercava di navigare il path `.codice` su un intero, l'operazione falliva silenziosamente e restituiva una stringa vuota.

## Esempio del problema

**Configurazione:**
- Tipo documento: "Cedolino"
- Attributo dinamico: "dipendente" (tipo: integer, widget: anagrafica)
- Pattern nome file: `Cedolino_{attr:dipendente.codice}_{data_documento:%Y%m%d}`

**Risultato atteso:** `Cedolino_DIP001_20241215.pdf`
**Risultato effettivo:** `Cedolino__20241215.pdf` (codice anagrafica non veniva restituito)

## Soluzione implementata

### 1. Estensione del token `{attr:}` per supportare la navigazione dotted-path

Il token `{attr:codice_attributo}` ora supporta la sintassi `{attr:codice_attributo.campo_anagrafica}` per accedere ai campi dell'anagrafica collegata.

**File modificato:** `documenti/utils.py`

#### Modifiche principali:

1. **Aggiunta funzione helper `_attrs_definitions_map()`**: Recupera le definizioni degli attributi per sapere quale widget usa ciascun attributo.

2. **Modifica della funzione `build_document_filename()`**: Ora carica anche le definizioni degli attributi oltre ai valori.

3. **Gestione della navigazione dotted-path nel token `{attr:}`**:
   - Quando rileva un punto (`.`) nel codice attributo, lo split in `codice` e `path`
   - Recupera la definizione dell'attributo per verificare se usa il widget "anagrafica"
   - Se sì, carica l'oggetto Anagrafica usando l'ID memorizzato
   - Naviga il path specificato (es. `codice`, `codice_fiscale`, `cognome`, ecc.)
   - Applica l'eventuale formattazione (per date)

4. **Stesso supporto anche per il token `{uattr:}`**: Mantiene la coerenza nel comportamento.

5. **Pulizia migliorata dei nomi file**: Rimuove underscore, trattini e spazi doppi/multipli dal nome file generato.

### 2. Test completi

**File aggiunto:** `documenti/tests/test_attr_anagrafica_navigation.py`

Test che verificano:
- ✅ Navigazione per accedere al campo `codice` dell'anagrafica
- ✅ Navigazione per accedere al campo `codice_fiscale` dell'anagrafica
- ✅ Mix di attributi semplici e con navigazione
- ✅ Comportamento corretto quando l'attributo non ha valore

Tutti i test passano al 100%.

## Sintassi supportate

### Token base (già esistente)
```
{attr:codice_attributo}              → Valore grezzo dell'attributo
{attr:data_riferimento:%Y%m%d}       → Attributo data con formattazione
```

### Nuova sintassi con navigazione (implementata)
```
{attr:dipendente.codice}                    → Campo 'codice' dell'anagrafica collegata
{attr:dipendente.codice_fiscale}            → Campo 'codice_fiscale' dell'anagrafica
{attr:dipendente.cognome}                   → Campo 'cognome' dell'anagrafica
{attr:cliente_ref.ragione_sociale}          → Campo 'ragione_sociale' dell'anagrafica
{uattr:dipendente.codice}                   → Come sopra, ma aggiunge "_" se presente
```

### Token esistente alternativo (più verboso)
```
{attrobj:dipendente:anagrafiche:Anagrafica:codice}  → Sintassi completa già esistente
```

La nuova sintassi `{attr:dipendente.codice}` è molto più intuitiva e leggibile rispetto a `{attrobj:dipendente:anagrafiche:Anagrafica:codice}`.

## Esempi pratici

### Cedolino paga
```
Pattern: Cedolino_{attr:anno}{attr:mese}_{attr:dipendente.codice}
Risultato: Cedolino_202412_DIP001.pdf
```

### Contratto dipendente
```
Pattern: Contratto_{attr:dipendente.codice_fiscale}_{data_documento:%Y%m%d}
Risultato: Contratto_RSSMRA80A01H501Z_20241215.pdf
```

### Documento con cliente
```
Pattern: Doc_{attr:cliente_rif.ragione_sociale}_{attr:numero}
Risultato: Doc_Azienda Test S.r.l._001.pdf
```

## Note tecniche

### Widget supportati
La navigazione funziona automaticamente per attributi con i seguenti widget:
- `anagrafica`
- `fk_anagrafica`
- `anag`

### Campi Anagrafica disponibili
Qualsiasi campo del modello `Anagrafica` può essere acceduto:
- `codice` - Codice cliente (es. "DIP001")
- `codice_fiscale` - Codice fiscale
- `partita_iva` - Partita IVA
- `ragione_sociale` - Ragione sociale (per PG)
- `cognome` - Cognome (per PF)
- `nome` - Nome (per PF)
- `email` - Email
- `pec` - PEC
- `telefono` - Telefono
- `indirizzo` - Indirizzo

### Gestione errori
- Se l'attributo non ha valore → stringa vuota
- Se l'ID anagrafica non esiste → stringa vuota con log warning
- Se il campo richiesto non esiste → stringa vuota con log warning

### Performance
Il caricamento delle anagrafiche avviene solo quando necessario (lazy loading) e utilizza `.get(id=...)` per un'unica query mirata.

## Compatibilità

La modifica è **retrocompatibile**:
- I pattern esistenti senza navigazione continuano a funzionare esattamente come prima
- La sintassi `{attrobj:}` esistente continua a funzionare
- Nessuna migrazione database richiesta
- Nessuna modifica ai modelli

## File modificati

1. **`documenti/utils.py`**:
   - Aggiunta `_attrs_definitions_map()`
   - Modificata `_attrs_map()` per includere il campo `widget`
   - Esteso il parsing del token `{attr:}` per supportare dotted-path
   - Esteso il parsing del token `{uattr:}` per supportare dotted-path
   - Migliorata la pulizia del nome file generato

2. **`documenti/tests/test_attr_anagrafica_navigation.py`** (nuovo):
   - Test completi per la nuova funzionalità

## Data implementazione

2 gennaio 2026

## Testing

Eseguire i test con:
```bash
python manage.py test documenti.tests.test_attr_anagrafica_navigation
```

Oppure con pytest:
```bash
pytest documenti/tests/test_attr_anagrafica_navigation.py -v
```

Tutti i 4 test devono passare.
