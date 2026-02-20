# Rifattorizzazione PraticaDetailPage con Sistema a Tab

**Data**: 2 Febbraio 2026  
**Tipo**: Refactoring UI  
**Status**: ✅ Completato

## 📋 Panoramica

Rifattorizzata la `PraticaDetailPage` da una pagina disabilitata/placeholder a una pagina completamente funzionale con sistema a tab, seguendo lo schema usato in `FascicoloDetailPage`.

## 🎯 Obiettivo

Organizzare le informazioni della pratica in tab distinte per migliorare l'usabilità e la leggibilità:

```
┌─ TABS ──────────────────────────────────┐
│ Generale │ Fascicoli │ Documenti │ Note │ Scadenze │
└──────────────────────────────────────────┘
```

## 🔧 Modifiche Implementate

### File Modificato
- `/frontend/src/pages/PraticaDetailPage.tsx`

### Struttura Tabs

#### **Tab 0: Generale** 📝
Informazioni principali della pratica:
- **Card Informazioni Principali**
  - Tipo Pratica
  - Cliente (con link)
  - Responsabile
  - Stato
  
- **Card Date**
  - Data Apertura
  - Data Riferimento
  - Periodo Riferimento
  - Data Chiusura

- **Card Note Generali** (se presenti)
  - Visualizzazione note testuali della pratica

- **Card Tags** (se presenti)
  - Tags associati alla pratica

- **Card Informazioni Sistema**
  - Progressivo
  - Periodo Key

#### **Tab 1: Fascicoli** 📁
Gestione fascicoli collegati:
- Lista fascicoli con:
  - Codice (link)
  - Titolo
  - Stato (badge colorato)
  - Azioni: Visualizza, Scollega

- **Pulsanti Header**:
  - 🔗 **Collega Fascicolo**: Apre modal per collegare fascicolo esistente
  - ➕ **Crea Fascicolo**: Naviga al form creazione con `pratica_id` pre-compilato

- **Modal Collega Fascicolo**:
  - `FascicoloAutocomplete` con esclusione fascicoli già collegati
  - Validazione required
  - Gestione collegamento via API

#### **Tab 2: Documenti** 📄
Visualizzazione documenti dai fascicoli collegati:
- **Barra Filtri** (sticky):
  - 🔍 Ricerca fulltext (codice, descrizione, fascicolo)
  - 📋 Tipo documento (dropdown)
  - 👤 Cliente (dropdown)
  - 📅 Data da/a
  - 🔄 Pulsante Reset filtri

- **Tabella Documenti**:
  - Codice (link al documento)
  - Descrizione
  - Tipo
  - Fascicolo (link)
  - Data documento
  - Stato (badge)
  - Azioni: Visualizza, Apri file

- **Filtri Real-time**: Applicati via `useEffect` su `documentiFiltered`

#### **Tab 3: Note** 📝
Sistema gestione note:
- **Form Aggiungi/Modifica Nota**:
  - Tipo (memo, comunicazione, chiusura, altro)
  - Data
  - Stato (aperta, chiusa)
  - Testo (textarea)
  - Pulsanti: Annulla, Salva/Aggiorna

- **Lista Note**:
  - Badge tipo e stato
  - Data
  - Testo (pre-wrap)
  - Azioni: Modifica, Elimina

- **Toggle Form**: `showNotaForm` state per mostrare/nascondere

#### **Tab 4: Scadenze** ⏰
Lista scadenze collegate:
- **Card Scadenze** (clickable):
  - Titolo
  - Descrizione (truncate a 150 caratteri)
  - Badge Stato (colori semantici)
  - Badge Priorità
  - Categoria
  - Data scadenza

- **Navigazione**: Click su card → `/scadenze/{id}`

- **Pulsante Header**:
  - ➕ **Crea Scadenza**: Naviga al form con `pratica_id` e `return` URL

## 🎨 Features UI/UX

### Badge Colorati
```typescript
// Stati Pratica
aperta: 'badge-info'       // Blu
lavorazione: 'badge-warning' // Giallo
attesa: 'badge-secondary'  // Grigio
chiusa: 'badge-success'    // Verde

// Stati Fascicolo
corrente: 'badge-success'
storico: 'badge-info'
chiuso: 'badge-secondary'

// Stati Documento
definitivo: 'badge-success'
bozza: 'badge-warning'
archiviato: 'badge-info'

// Note Tipo
memo: 'badge-info'
comunicazione: 'badge-warning'
chiusura: 'badge-success'

// Scadenze Stato
attiva: 'badge-success'
completata: 'badge-info'
in_scadenza: 'badge-warning'
scaduta: 'badge-danger'

// Scadenze Priorità
critical: 'badge-danger'
high: 'badge-warning'
medium: 'badge-info'
low: 'badge-secondary'
```

### Badge con Contatori
Ogni tab mostra il numero di elementi:
- Fascicoli (X)
- Documenti (Y)
- Note (Z)
- Scadenze (W)

### Responsive
- Grid 2 colonne su desktop per info principali
- Tabelle scrollabili orizzontalmente
- Form responsive con grid

### Hover States
- Tabelle: row hover
- Scadenze card: hover con cambio colore
- Pulsanti icon: hover states

## 🔄 Flussi Principali

### Collegamento Fascicolo
1. Click "Collega Fascicolo" → Apre modal
2. Selezione da autocomplete (esclusi già collegati)
3. Confirm → API update fascicolo con nuova pratica
4. Reload pratica → Chiude modal
5. Alert successo

### Gestione Note
1. Click "Aggiungi Nota" → Toggle form
2. Compilazione campi
3. Save → API create/update
4. Reload pratica → Chiude form
5. Lista aggiornata

### Filtri Documenti
- Real-time filtering via `useEffect`
- Combinazione filtri (AND logic)
- Reset rapido con pulsante dedicato

## 📦 Componenti Utilizzati

### MUI Components
- `Tabs`, `Tab`, `Box`, `Badge` - Sistema tab
- `TabPanel` - Custom component per gestione contenuto tab
- `a11yProps` - Accessibilità

### Custom Components
- `FascicoloAutocomplete` - Autocomplete fascicoli con esclusioni

### Icons
- `ArrowBackIcon`, `EditIcon`, `DeleteIcon`
- `AddIcon`, `VisibilityIcon`, `DownloadIcon`

## 🔗 Integrazioni API

### Endpoints Utilizzati
```typescript
// Pratiche
praticheApi.get(id)
praticheApi.delete(id)
praticheApi.createNota(data)
praticheApi.updateNota(id, data)
praticheApi.deleteNota(id)

// Fascicoli
fascicoliApi.get(id)
fascicoliApi.update(id, { pratiche })

// Documenti
documentiApi.list({ fascicolo })
documentiApi.listTipi()
```

## 📊 Stati Gestiti

### State Principale
```typescript
const [pratica, setPratica] = useState<Pratica | null>(null);
const [documenti, setDocumenti] = useState<Documento[]>([]);
const [documentiFiltered, setDocumentiFiltered] = useState<Documento[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [activeTab, setActiveTab] = useState(0);
```

### State Note
```typescript
const [showNotaForm, setShowNotaForm] = useState(false);
const [editingNotaId, setEditingNotaId] = useState<number | null>(null);
const [notaForm, setNotaForm] = useState<NotaFormState>({...});
```

### State Fascicoli
```typescript
const [showCollegaFascicoloModal, setShowCollegaFascicoloModal] = useState(false);
const [selectedFascicoloId, setSelectedFascicoloId] = useState<number | null>(null);
```

### State Filtri Documenti
```typescript
const [filterDocSearch, setFilterDocSearch] = useState('');
const [filterDocTipo, setFilterDocTipo] = useState('');
const [filterDocCliente, setFilterDocCliente] = useState('');
const [filterDocDataDa, setFilterDocDataDa] = useState('');
const [filterDocDataA, setFilterDocDataA] = useState('');
const [tipiDocumento, setTipiDocumento] = useState<...>([]);
const [clientiDocumento, setClientiDocumento] = useState<...>([]);
```

## ✅ Vantaggi

1. **Organizzazione**: Informazioni raggruppate logicamente
2. **Performance**: Rendering condizionale solo tab attiva
3. **Navigazione**: Badge contatori per overview rapida
4. **Filtri**: Sistema filtri avanzato per documenti
5. **UX**: Azioni contestuali in ogni tab
6. **Consistenza**: Stesso pattern di FascicoloDetailPage
7. **Accessibilità**: Props a11y per screen readers

## 🎯 Pattern Seguiti

### Coerenza con FascicoloDetailPage
- Stesso sistema di tab con MUI
- Stessa struttura card per informazioni
- Stesso pattern header con badge
- Stessi pulsanti azione

### Best Practices
- Type safety completo con TypeScript
- Error handling con try/catch
- Loading states
- Confirm dialog per azioni critiche
- Real-time filtering
- Responsive design

## 📝 Note Tecniche

### Caricamento Documenti
```typescript
// Carica documenti da TUTTI i fascicoli collegati
const loadDocumenti = useCallback(async (fascicoli) => {
  const responses = await Promise.all(
    fascicoli.map(f => documentiApi.list({ fascicolo: f.id }))
  );
  const allDocumenti = responses.flatMap(r => r.results);
  setDocumenti(allDocumenti);
}, []);
```

### Filtri Documenti Real-time
```typescript
useEffect(() => {
  let filtered = [...documenti];
  // Applica filtri search, tipo, cliente, date
  setDocumentiFiltered(filtered);
}, [documenti, filterDocSearch, filterDocTipo, ...]);
```

### Modal Gestione
- Click fuori → Chiude modal
- StopPropagation su contenuto interno
- Cleanup state on close

## 🚀 Testing Consigliato

### Scenari da Testare
1. ✅ Navigazione tra tab
2. ✅ Caricamento dati pratica
3. ✅ Collegamento/scollegamento fascicoli
4. ✅ Creazione/modifica/eliminazione note
5. ✅ Filtri documenti (tutti i tipi)
6. ✅ Navigazione a pagine correlate
7. ✅ Modal collega fascicolo
8. ✅ Preview file documenti

### Edge Cases
- Pratica senza fascicoli
- Pratica senza documenti
- Pratica senza note
- Pratica senza scadenze
- Filtri documenti senza risultati

## 📌 Riferimenti

- **File Originale**: `PraticaDetailPage.tsx.broken` (backup)
- **File Corrente**: `PraticaDetailPage.tsx`
- **Modello**: `FascicoloDetailPage.tsx`
- **Types**: `@/types/pratica.ts`
- **API**: `@/api/pratiche.ts`, `@/api/fascicoli.ts`, `@/api/documenti.ts`

---

**Rifattorizzazione completata con successo!** ✨

La PraticaDetailPage è ora completamente funzionale con un'interfaccia moderna e organizzata in tab.
