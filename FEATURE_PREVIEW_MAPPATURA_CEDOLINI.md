# Feature: Preview Mappatura Dati Cedolini

## 📋 Descrizione

Aggiunta visualizzazione dettagliata nella preview dell'importazione cedolini che mostra esplicitamente:
- **Attributi DB**: Dati che verranno salvati come `AttributoValore` (ricercabili e filtrabili)
- **Dati Note**: Informazioni estratte dal PDF disponibili per riferimento

## 🎯 Obiettivo

Fornire all'utente una chiara visibilità di quali dati verranno salvati come attributi strutturati del documento e quali dati sono stati estratti dal PDF come informazioni aggiuntive.

## 🔧 Modifiche Implementate

### 1. Backend API (`api/v1/documenti/views.py`)

**Endpoint**: `POST /api/v1/documenti/importa_cedolini_preview/`

Aggiunto alla response di ogni cedolino:

```python
'attributi_db': {
    'tipo': 'Libro Unico',
    'anno_riferimento': parsed['cedolino']['anno'],
    'mese_riferimento': parsed['cedolino']['mese'],
    'mensilita': parsed['cedolino']['mensilita'],
    'dipendente': f"{parsed['lavoratore']['cognome']} {parsed['lavoratore']['nome']}",
},
'dati_note': {
    'matricola': parsed['lavoratore'].get('matricola'),
    'matricola_inps': parsed['lavoratore'].get('matricola_inps'),
    'data_nascita': parsed['lavoratore'].get('data_nascita'),
    'data_assunzione': parsed['lavoratore'].get('data_assunzione'),
    'livello': parsed['cedolino'].get('livello'),
},
```

### 2. Frontend TypeScript Types (`frontend/src/api/documenti.ts`)

Aggiornati i tipi TypeScript della response `importaCedoliniPreview()`:

```typescript
attributi_db: {
  tipo: string;
  anno_riferimento: number;
  mese_riferimento: number;
  mensilita: number;
  dipendente: string;
};
dati_note: {
  matricola?: string | null;
  matricola_inps?: string | null;
  data_nascita?: string | null;
  data_assunzione?: string | null;
  livello?: string | null;
};
```

### 3. Frontend UI (`frontend/src/pages/ImportaCedoliniPage.tsx`)

**Modifiche alla tabella cedolini validi:**

- Aggiunta colonna "Attributi DB" con Chip colorati:
  - `Tipo: Libro Unico`
  - `Anno: 2025`
  - `Mese: 12`
  - `Mensilità: 12`

- Aggiunta colonna "Dati Note" con icone:
  - 🆔 Matricola
  - 📋 Matricola INPS
  - 🎂 Data Nascita
  - 📅 Data Assunzione
  - (Livello già mostrato nella colonna Periodo)

**Alert informativo:**
Aggiunto alert sopra la tabella espandibile che spiega:
```
💡 Legenda mappatura dati:
📊 Attributi DB = Dati salvati come attributi del documento (ricercabili e filtrabili)
📝 Dati Note = Informazioni estratte dal PDF disponibili per riferimento
```

**Istruzioni aggiornate:**
Aggiunte nelle istruzioni iniziali le informazioni su cosa viene salvato:
- 💾 Dati salvati come attributi documento
- 📝 Dati estratti per riferimento

## 📊 Mappatura Dati

### Attributi Salvati nel DB

Questi dati vengono salvati come `AttributoValore` e sono:
- **Ricercabili** tramite filtri API
- **Utilizzabili** nei pattern di codifica documenti (`{ATTR:...}`)
- **Strutturati** secondo le `AttributoDefinizione` del tipo BPAG

| Attributo | Valore | Fonte |
|-----------|--------|-------|
| `tipo` | "Libro Unico" | Fisso |
| `anno_riferimento` | es. 2025 | Parser PDF |
| `mese_riferimento` | es. 12 | Parser PDF |
| `mensilita` | 1-12, 13, 14 | Parser PDF + logica tredicesima |
| `dipendente` | ID anagrafica | Match/Create anagrafica |

### Dati Estratti (Note)

Questi dati vengono estratti dal PDF ma NON salvati come attributi:
- Sono disponibili nella preview per verifica
- Potrebbero essere aggiunti manualmente alle note del documento
- Utili per debug e verifica correttezza parsing

| Campo | Descrizione | Fonte |
|-------|-------------|-------|
| `matricola` | Matricola dipendente | Nome file o PDF |
| `matricola_inps` | Matricola INPS | Parsing PDF |
| `data_nascita` | Data nascita (formato DD-MM-YYYY) | Parsing PDF |
| `data_assunzione` | Data assunzione (formato DD-MM-YYYY) | Parsing PDF |
| `livello` | Livello contrattuale | Parsing PDF |

## 🎨 Visualizzazione UI

### Prima (senza mappatura dettagliata)
```
File | Dipendente | Datore | Periodo
```

### Dopo (con mappatura dettagliata)
```
File | Dipendente | Periodo | Attributi DB | Dati Note
                              [Chip Tipo]    [🆔 Matricola: 12345]
                              [Chip Anno]    [📋 INPS: 67890]
                              [Chip Mese]    [🎂 Nato: 01-01-1980]
                              [Chip Mensilità] [📅 Assunto: 15-06-2020]
```

## ✅ Benefici

1. **Trasparenza**: L'utente vede esattamente cosa verrà salvato nel DB
2. **Verifica**: Possibilità di controllare i dati estratti prima dell'import
3. **Educativo**: L'utente capisce la differenza tra attributi e dati estratti
4. **Debug**: Facilita identificazione errori di parsing

## 🧪 Testing

### Test Case 1: Cedolino Ordinario
- **Input**: PDF cedolino dicembre 2025
- **Verifica**:
  - ✅ Attributi DB: tipo="Libro Unico", anno=2025, mese=12, mensilita=12
  - ✅ Dati Note: matricola, data_nascita, data_assunzione visibili

### Test Case 2: Tredicesima
- **Input**: PDF tredicesima 2025
- **Verifica**:
  - ✅ Attributi DB: mensilita=13 (non 12)
  - ✅ Periodo: "Tredicesima 2025"

### Test Case 3: ZIP Multiplo
- **Input**: ZIP con 20 cedolini
- **Verifica**:
  - ✅ Tabella mostra max 20 righe
  - ✅ Ogni riga ha colonne Attributi DB e Dati Note compilate
  - ✅ Alert informativo visibile

## 📝 Note Tecniche

### Parser Cedolino (`documenti/parsers/cedolino_parser.py`)

Il parser estrae tutti i dati disponibili:
```python
{
    'datore': {...},
    'lavoratore': {
        'codice_fiscale': str,
        'cognome': str,
        'nome': str,
        'matricola': Optional[str],
        'data_nascita': Optional[str],
        'data_assunzione': Optional[str],
        'matricola_inps': Optional[str],
    },
    'cedolino': {
        'anno': int,
        'mese': int,
        'mensilita': int,
        'periodo': str,
        'livello': Optional[str],
        'data_documento': date,
    }
}
```

### Confirm Endpoint

L'endpoint `importa_cedolini_confirm` utilizza solo i dati `attributi_db` per creare gli `AttributoValore`.

I `dati_note` sono puramente informativi nella preview e non vengono passati al confirm.

Se si volesse salvare anche i dati_note, si potrebbero:
1. Aggiungere come attributi dinamici (richiede creazione nuove `AttributoDefinizione`)
2. Inserire nel campo `note` del documento (testo libero)
3. Salvare in una tabella separata

## 🔮 Future Improvements

1. **Export Preview**: Esportare preview come Excel per archivio
2. **Dati Note → Attributi**: Checkbox per salvare dati_note come attributi opzionali
3. **Evidenziazione Duplicati**: Highlight colonne con dati diversi rispetto al duplicato esistente
4. **Validazione Dati**: Warning se dati_note incompleti o malformati

## 📅 Changelog

**Data**: 4 Febbraio 2026  
**Autore**: Sistema Copilot  
**Versione**: 1.0  

### Modifiche
- ✅ Backend: Aggiunto `attributi_db` e `dati_note` alla preview response
- ✅ Frontend Types: Aggiornati tipi TypeScript
- ✅ Frontend UI: Nuove colonne tabella + alert informativo
- ✅ Documentazione: Aggiornate istruzioni nella pagina import

---

**Stato**: ✅ Completato  
**Testing**: ⏳ In attesa di test end-to-end
