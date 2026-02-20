# Widget Anagrafica nei Template di Comunicazione

## 📋 Panoramica

Il sistema dei template di comunicazione ora supporta un **widget speciale per selezionare anagrafiche**, permettendo di riferirsi a soggetti specifici nel corpo della comunicazione anche se non sono tra i destinatari.

## 🎯 Caso d'Uso

**Esempio**: Inviare documenti a X riguardanti il cliente Y

- **Destinatari**: Studio legale (X)
- **Riferimento**: Cliente specifico (Y) - i cui dati devono apparire nel corpo della comunicazione

## ⚙️ Configurazione

### 1. Creare il Campo Variabile

Nel template di comunicazione, aggiungere un campo con queste impostazioni:

| Campo | Valore |
|-------|--------|
| **key** | `cliente` (o altro nome a scelta) |
| **label** | `Cliente di riferimento` |
| **field_type** | `integer` ⚠️ **IMPORTANTE** |
| **widget** | `anagrafica` |
| **required** | `False` (o `True` se obbligatorio) |
| **source_path** | Lasciare vuoto (o usare helper come `get_prima_anagrafica`) |

### 2. Usare nel Template

Una volta configurato, il campo sarà disponibile nel contesto del template come **oggetto Anagrafica completo**:

```django
Gentile {{ cliente.denominazione_anagrafica }},

in riferimento alla pratica del Sig./Sig.ra {{ cliente.ragione_sociale }},
con codice fiscale {{ cliente.codice_fiscale }},
residente in {{ cliente.indirizzo }}, {{ cliente.cap }} {{ cliente.comune.denominazione }}...

Distinti saluti.
```

### Attributi Disponibili

Tutti gli attributi del modello `Anagrafica` sono accessibili:

- `cliente.denominazione_anagrafica` - Nome completo o ragione sociale
- `cliente.ragione_sociale` - Ragione sociale (PG)
- `cliente.nome` - Nome (PF)
- `cliente.cognome` - Cognome (PF)
- `cliente.codice_fiscale` - Codice fiscale
- `cliente.partita_iva` - Partita IVA
- `cliente.email` - Email principale
- `cliente.telefono` - Telefono
- `cliente.indirizzo` - Indirizzo
- `cliente.cap` - CAP
- `cliente.comune.denominazione` - Nome del comune
- `cliente.comune.provincia` - Provincia

## 🔧 Funzionamento Tecnico

### Salvataggio

1. L'utente seleziona un'anagrafica dal dropdown
2. Il sistema salva l'**ID** dell'anagrafica in `dati_template`
3. Il valore viene memorizzato come intero (es. `{"cliente": 42}`)

### Rendering

1. Il sistema legge l'ID dal campo `dati_template`
2. Risolve l'ID recuperando l'oggetto `Anagrafica` dal database
3. L'oggetto completo viene reso disponibile nel contesto template
4. Django può accedere a tutti gli attributi e relazioni

## 📝 Esempi Pratici

### Esempio 1: Invio Documenti a Terzi

**Template**: "Invio documenti cliente"

**Configurazione Campo**:
- key: `cliente_riferimento`
- field_type: `integer`
- widget: `anagrafica`
- label: `Cliente di riferimento`

**Corpo Template**:
```
Gentile Dott. {{ destinatario.nome }},

in allegato inviamo la documentazione richiesta relativa al cliente
{{ cliente_riferimento.denominazione_anagrafica }} (CF: {{ cliente_riferimento.codice_fiscale }}).

Restiamo a disposizione per ulteriori chiarimenti.
```

### Esempio 2: Comunicazione con Fonte Dinamica

**Configurazione Campo**:
- key: `cliente`
- field_type: `integer`
- widget: `anagrafica`
- source_path: `get_prima_anagrafica` (opzionale - pre-compila con primo destinatario)

**Utilizzo**: Il campo si pre-compila automaticamente con l'anagrafica del primo contatto destinatario, ma può essere modificato manualmente.

## ⚠️ Note Importanti

1. **Tipo Campo**: DEVE essere `integer` per salvare l'ID
2. **Widget**: Usare `anagrafica`, `fk_anagrafica` o `anag`
3. **Validazione**: Se il campo è `required=True`, l'anagrafica deve essere selezionata
4. **Performance**: Il sistema usa `select_related` per ottimizzare le query

## 🔄 Integrazione con source_path

Puoi combinare `widget='anagrafica'` con `source_path` per valori di default:

```python
# Campo che si pre-compila con il primo contatto destinatario
key: "cliente"
widget: "anagrafica"
source_path: "get_prima_anagrafica"
```

L'utente può sempre sovrascrivere il valore pre-compilato.

## 🎨 UI/UX

- **Form di Creazione**: Dropdown con tutte le anagrafiche ordinate alfabeticamente
- **Visualizzazione**: Mostra la denominazione completa dell'anagrafica
- **Ricerca**: Filtrabile per nome/ragione sociale
- **Validazione**: Controllo automatico che l'ID esista

## 🧪 Testing

Per testare la funzionalità:

1. Creare un template con campo widget='anagrafica'
2. Creare una comunicazione usando quel template
3. Selezionare un'anagrafica dal dropdown
4. Verificare che nel rendering appaia il nome corretto
5. Controllare che `dati_template` contenga l'ID (non l'oggetto)

---

**Data implementazione**: Dicembre 2025
**Versione**: 1.0
