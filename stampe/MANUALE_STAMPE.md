# Manuale utente: moduli di stampa

Questo documento descrive come configurare formati, moduli e campi di stampa nel backoffice e fornisce esempi pratici sull uso dei campi "Python template format".

## 1. Flusso di configurazione
- **StampaFormato**: definisce dimensioni pagina, margini e font di default. Va creato una volta per ciascun formato carta/etichetta.
- **StampaModulo**: associa un formato a un modello Django (app_label + model_name) e contiene le opzioni generali della stampa singola.
- **StampaCampo**: elementi concreti posizionati sul modulo. Ogni campo decide cosa stampare (attr_path, template o static_value) e come mostrarlo.

## 2. Creare un nuovo modulo di stampa
1. Accedi a `Stampe > Formati` e crea il formato impostando nome, slug, dimensioni in mm e margini. Il font predefinito sara usato dai moduli che non specificano un font personalizzato.
2. In `Stampe > Moduli` crea un nuovo record compilando:
   - `app_label`: ad esempio `documenti`.
   - `model_name`: minuscolo, ad esempio `documento`.
   - `formato`: seleziona il formato creato al punto precedente.
   - `documento_tipo` (opzionale): limita il modulo a uno specifico tipo documento.
   - Spunta `is_default` se vuoi che sia il modulo di default per la coppia app+model (e tipo documento, se impostato).
3. Salva il modulo e, nella scheda del modulo, aggiungi i `Campi modulo` tramite l inline:
   - Imposta l ordine desiderato e la posizione (x_mm, y_mm) in millimetri calcolati dal bordo sinistro/superiore della pagina.
   - Scegli il `tipo` di campo. Per contenuti dinamici usa `Attr` o `Template`.
   - Compila `larghezza_mm` per abilitare il wrapping automatico del testo.
   - Se necessario personalizza font, dimensione, allineamento e numero massimo di righe.

## 3. Campi con Python template format
Quando un campo ha il tipo `Template` (o quando `attr_path` e vuoto ma il campo contiene un template) il motore usa `str.format` di Python con il seguente contesto:

| Place-holder | Descrizione |
| --- | --- |
| `{obj}` | Istanza del modello che si sta stampando. Puoi navigare attributi: `{obj.cliente.ragione_sociale}` |
| `{attr}` | Namespace che espone gli attributi dinamici (tabella `AttributoValore`). Ogni codice diventa un attributo, es: `{attr.protocollo}` |

> Nota: eventuali errori di formattazione vengono ignorati e il campo ritorna testo vuoto.

### 3.1 Esempi di base
- Ragione sociale cliente (partendo dalla relazione):
  ```text
  Cliente: {obj.cliente.ragione_sociale}
  ```
- Data documento formattata:
  ```text
  Data: {obj.data_documento:%d/%m/%Y}
  ```
  Il formato dopo i due punti usa la sintassi standard di `datetime.__format__`.
- Protocollo da attributo dinamico (codice `protocollo`):
  ```text
  Prot.: {attr.protocollo}
  ```

### 3.2 Combinare testo statico e placeholder
Puoi concatenare piu valori nello stesso template:
```text
{obj.tipo.nome} n. {obj.numero} del {obj.data_documento:%d/%m/%Y}
``` 
Se un attributo intermedio e `None`, il risultato sara una stringa vuota per quel placeholder.

### 3.3 Suggerimenti pratici
- Lascia vuoto `attr_path` quando usi il template, altrimenti ha precedenza e il template non verra valutato.
- Imposta `max_lines` e `larghezza_mm` per gestire correttamente testi lunghi con ellissi automatiche.
- Per valori opzionali puoi usare la sintassi di default di `str.format`, ad esempio `{attr.protocollo or 'N/D'}` non e supportato. In alternativa, crea un attributo calcolato sul modello (property) e referenzialo con `{obj.nome_property}`.

## 4. Template nelle liste di stampa
Le liste (`StampaLista` + `StampaColonna`) condividono la stessa logica dei template con una differenza nel contesto:
- `{obj}` e l oggetto di riga corrente.
- Non e disponibile `{attr}`; se ti servono attributi dinamici recuperali tramite `obj` stesso (aggiungi una property sul modello se necessario).

Esempio di colonna calcolata:
```text
Codice: {obj.codice} - {obj.get_stato_display()}
```
Ricorda di impostare il tipo colonna su `Template` e di lasciare vuoto `attr_path`.

## 5. Verifica e test
- Usa il pulsante "Anteprima" o stampa etichette di test per verificare allineamenti e testo.
- In caso di modifiche alla logica, crea test di integrazione nel modulo `stampe.tests` per assicurare che il rendering funzioni anche dopo aggiornamenti futuri.
- Conserva uno storico degli slug e non riutilizzare gli slug esistenti per evitare cache lato client.
