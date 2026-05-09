# Fase 3: Admin Template Manager (Frontend) - COMPLETATA ✅

## 📋 Componenti Frontend Creati

### 🎨 Components

#### 1. **ZoneDrawingCanvas** (`/components/aiImport/ZoneDrawingCanvas.tsx`)
Componente Canvas per disegno interattivo zone di estrazione.

**Features:**
- ✅ Rendering immagine template su canvas HTML5
- ✅ Disegno zone tramite click & drag
- ✅ Visualizzazione zone esistenti con colori (verde=normale, rosso=obbligatorio, blu=selezionato)
- ✅ Selezione zona al click
- ✅ Zoom In/Out/Reset (0.5x - 3x)
- ✅ Conversione coordinate % → pixel assoluti
- ✅ Eliminazione zona selezionata
- ✅ Modalità read-only
- ✅ Prompt utente per definire proprietà zona (nome, etichetta, tipo, obbligatorio)

**Props:**
```typescript
interface ZoneDrawingCanvasProps {
  imageUrl: string;              // URL immagine template
  imageWidth: number;            // Larghezza originale immagine
  imageHeight: number;           // Altezza originale immagine
  zones: ExtractionTemplateZone[];  // Zone esistenti
  selectedZoneId?: number;       // Zona selezionata
  onZoneCreate?: (zone) => void; // Callback creazione zona
  onZoneSelect?: (id) => void;   // Callback selezione zona
  onZoneDelete?: (id) => void;   // Callback eliminazione zona
  readOnly?: boolean;            // Modalità solo lettura
}
```

**Interazioni:**
- **Click & Drag**: Crea nuova zona rettangolare
- **Click su zona**: Seleziona zona esistente
- **Pulsante Elimina**: Elimina zona selezionata
- **Zoom controls**: Toolbar in alto a destra

---

### 📄 Pages

#### 2. **TemplateListPage** (`/pages/aiImport/TemplateListPage.tsx`)
Pagina lista template di estrazione.

**Features:**
- ✅ Lista template in card layout (Grid responsive)
- ✅ Filtri: tipo documento, attivo/inattivo
- ✅ Info per card:
  - Nome template
  - Tipo documento (codice + descrizione)
  - Chip stato (Attivo/Inattivo)
  - Numero pagine e zone
  - Priorità
  - Data creazione + autore
- ✅ Azioni:
  - **Visualizza**: Naviga a editor (read-only)
  - **Modifica**: Naviga a editor (edit mode)
  - **Elimina**: Conferma + eliminazione
  - **Nuovo Template**: Dialog creazione
- ✅ Dialog creazione template con form:
  - Tipo Documento ID
  - Nome
  - Descrizione
  - Numero pagine
  - Priorità
  - Switch Attivo/Inattivo

**Routes:**
- `/admin/templates` - Lista template
- `/admin/templates/:id` - Visualizza template
- `/admin/templates/:id/edit` - Modifica template

---

#### 3. **TemplateEditorPage** (`/pages/aiImport/TemplateEditorPage.tsx`)
Pagina editor template con canvas per disegno zone.

**Features:**
- ✅ Upload immagini template (multi-pagina)
- ✅ Tabs per navigare tra pagine (se > 1 pagina)
- ✅ Canvas interattivo per disegno zone
- ✅ Sidebar con:
  - **Info Template**: Stato, priorità, contatori
  - **Lista Zone Pagina Corrente**: Tutte le zone della pagina attiva
  - **Dettagli Zona Selezionata**: Proprietà complete della zona
- ✅ Dialog upload pagina:
  - Numero pagina
  - Selezione file immagine
  - Preview info file
  - Auto-detect dimensioni immagine
- ✅ Integrazione React Query per data fetching e mutazioni

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Header: Nome Template | [Carica Pagina]                │
├──────────────────────────────┬──────────────────────────┤
│                              │ Sidebar:                 │
│ Canvas Area (8/12 cols)      │ - Info Template          │
│                              │ - Lista Zone             │
│ ┌──────────────────────────┐ │ - Dettagli Zona         │
│ │ [Tabs Pagine]            │ │   Selezionata           │
│ ├──────────────────────────┤ │                         │
│ │ ZoneDrawingCanvas        │ │ (4/12 cols)             │
│ │                          │ │                         │
│ │ [Zoom] [Reset] [Delete]  │ │                         │
│ └──────────────────────────┘ │                         │
└──────────────────────────────┴──────────────────────────┘
```

---

### 🔧 Services & Hooks

#### 4. **aiImport.ts** (`/api/aiImport.ts`)
API client per tutti gli endpoint AI Import.

**Metodi Implementati:**

**Workflow:**
- `upload(request)` - Upload documento + OCR
- `predict(request)` - Predizione tipo (top 3)
- `extract(request)` - Estrazione dati da template
- `confirmPrediction(request)` - Conferma predizione utente
- `saveFeedback(request)` - Salva correzioni

**Template Management:**
- `listTemplates(params)` - Lista template
- `getTemplate(id)` - Dettaglio template
- `createTemplate(request)` - Crea template
- `updateTemplate(id, request)` - Aggiorna template
- `deleteTemplate(id)` - Elimina template
- `addTemplatePage(templateId, request)` - Aggiungi pagina
- `addTemplateZone(request)` - Aggiungi zona
- `updateTemplateZone(zoneId, request)` - Aggiorna zona
- `deleteTemplateZone(zoneId)` - Elimina zona
- `addFieldMapping(request)` - Aggiungi mapping campo
- `deleteFieldMapping(mappingId)` - Elimina mapping

**Feedback:**
- `listFeedback(params)` - Lista feedback
- `getFeedback(id)` - Dettaglio feedback
- `getFeedbackStats()` - Statistiche (dashboard)

---

#### 5. **useAIImport.ts** (`/hooks/useAIImport.ts`)
Custom hooks React Query per AI Import.

**Query Hooks:**
- `useTemplates(params)` - Lista template
- `useTemplate(id)` - Dettaglio template
- `useFeedbackList(params)` - Lista feedback
- `useFeedback(id)` - Dettaglio feedback
- `useFeedbackStats()` - Statistiche

**Mutation Hooks:**
- `useCreateTemplate()` - Crea template
- `useUpdateTemplate()` - Aggiorna template
- `useDeleteTemplate()` - Elimina template
- `useAddTemplatePage()` - Aggiungi pagina
- `useAddTemplateZone()` - Aggiungi zona
- `useDeleteTemplateZone()` - Elimina zona
- `useUploadDocument()` - Upload documento
- `usePredictType()` - Predizione tipo
- `useExtractData()` - Estrazione dati
- `useConfirmPrediction()` - Conferma predizione
- `useSaveFeedback()` - Salva feedback

**Query Keys:**
```typescript
aiImportKeys = {
  all: ['ai-import'],
  templates: () => ['ai-import', 'templates'],
  template: (id) => ['ai-import', 'templates', id],
  feedback: () => ['ai-import', 'feedback'],
  feedbackItem: (id) => ['ai-import', 'feedback', id],
  feedbackStats: () => ['ai-import', 'feedback', 'stats'],
}
```

---

#### 6. **aiImport.ts** (`/types/aiImport.ts`)
TypeScript types per AI Import (250+ righe).

**Types Principali:**
- `DocumentExtractionTemplate` - Template completo
- `ExtractionTemplatePage` - Singola pagina
- `ExtractionTemplateZone` - Zona estrazione
- `ExtractionFieldMapping` - Mapping campo
- `AIPredictionFeedback` - Feedback predizione
- `ExtractionCorrection` - Correzione campo
- `UploadDocumentRequest/Response`
- `PredictTypeRequest/Response`
- `ExtractDataRequest/Response`
- `ConfirmPredictionRequest/Response`
- `SaveFeedbackRequest/Response`
- `CreateTemplateRequest`
- `CreateTemplatePageRequest`
- `CreateTemplateZoneRequest`
- `PaginatedResponse<T>`

---

## 📁 Struttura File Creati

```
frontend/src/
├── api/
│   └── aiImport.ts                 (270 righe) ✅
├── hooks/
│   └── useAIImport.ts              (200 righe) ✅
├── types/
│   └── aiImport.ts                 (260 righe) ✅
├── components/
│   └── aiImport/
│       ├── ZoneDrawingCanvas.tsx   (340 righe) ✅
│       └── index.ts                ✅
└── pages/
    └── aiImport/
        ├── TemplateListPage.tsx    (290 righe) ✅
        ├── TemplateEditorPage.tsx  (360 righe) ✅
        └── index.ts                ✅
```

**Totale:** ~1720 righe di codice TypeScript/React

---

## 🎯 Funzionalità Implementate

### ✅ Template Management
1. **Lista Template**
   - Grid responsive con card
   - Info complete (tipo doc, pagine, zone, priorità)
   - Filtri e ordinamento
   - Azioni: Visualizza, Modifica, Elimina

2. **Creazione Template**
   - Dialog con form completo
   - Validazione campi obbligatori
   - Auto-redirect a editor dopo creazione

3. **Editor Visuale**
   - Upload multi-pagina
   - Tabs navigazione pagine
   - Canvas disegno zone interattivo
   - Sidebar informazioni

### ✅ Zone Drawing Tool
1. **Disegno Zone**
   - Click & drag per creare zona
   - Prompt proprietà (nome, etichetta, tipo, obbligatorio)
   - Conversione coordinate % (scalabili)

2. **Gestione Zone**
   - Visualizzazione zone esistenti
   - Selezione zona al click
   - Evidenziazione zona selezionata
   - Colori semantici (verde/rosso/blu)
   - Eliminazione zona

3. **Zoom & Navigazione**
   - Zoom In/Out (0.5x - 3x)
   - Reset zoom
   - Scroll container

### ✅ Data Management
1. **React Query Integration**
   - Query con caching automatico
   - Mutations con invalidazione query
   - Loading/Error states
   - Optimistic updates

2. **Type Safety**
   - TypeScript types completi
   - Props validation
   - API response types

---

## 🧪 Come Testare

### 1. Aggiungi Route
Modifica `/frontend/src/routes/index.tsx`:

```typescript
import { TemplateListPage, TemplateEditorPage } from '@/pages/aiImport';

// Aggiungi alle routes protette:
{
  path: '/admin/templates',
  element: <TemplateListPage />,
},
{
  path: '/admin/templates/:id',
  element: <TemplateEditorPage />,
},
```

### 2. Test Workflow Completo

**Passo 1: Crea Template**
1. Naviga a `/admin/templates`
2. Click **Nuovo Template**
3. Compila form:
   - Tipo Documento: `15` (UNILAV)
   - Nome: `UNILAV Standard 2026`
   - Descrizione: `Template per comunicazioni UNILAV 2026`
   - Numero Pagine: `2`
   - Priorità: `10`
   - Attivo: `✓`
4. Click **Crea** → Redirect a editor

**Passo 2: Upload Pagina**
1. Click **Carica Pagina**
2. Numero Pagina: `1`
3. Seleziona immagine template (es. screenshot UNILAV PDF pagina 1)
4. Click **Carica**
5. Immagine appare su canvas

**Passo 3: Disegna Zone**
1. Click & drag su canvas per creare zona (es. area "Codice Fiscale Datore")
2. Prompt:
   - Nome campo: `codice_fiscale_datore`
   - Etichetta: `Codice Fiscale Datore di Lavoro`
   - Tipo dato: `codice_fiscale`
   - Obbligatorio: `Sì`
3. Zona appare con bordo rosso (obbligatoria)
4. Ripeti per altri campi (data assunzione, ragione sociale, etc.)

**Passo 4: Gestione Zone**
1. Click su zona esistente → Selezione (bordo blu)
2. Sidebar mostra dettagli zona
3. Click pulsante **Elimina** → Conferma
4. Zoom In/Out per precisione

**Passo 5: Multi-Pagina**
1. Click **Carica Pagina**
2. Numero Pagina: `2`
3. Upload pagina 2 template
4. Tabs navigazione appaiono
5. Disegna zone su pagina 2

---

## 🚀 Prossimi Passi - Fase 4

**Fase 4: AI Import Page (Frontend)**

Obiettivo: Pagina utente per import assistito AI.

Features da implementare:
1. **Upload/Scanner**
   - Button upload file
   - Integrazione scanner (se disponibile)
   - Preview documento

2. **Modal Conferma Tipo**
   - Mostra top 3 predizioni AI
   - Card per ogni predizione (codice, descrizione, confidence)
   - Dropdown manuale "Altro tipo"
   - Button "Conferma"

3. **Redirect Form**
   - Query params: `?ai_import=true&prediction_id=567&temp_file=/tmp/...`
   - Pre-fill campi estratti
   - Mostra note auto-generate
   - Tracking correzioni utente

4. **Feedback Flow**
   - Salva conferma predizione (corretta/errata)
   - Salva correzioni campi
   - Toast notifications

Vuoi procedere con la Fase 4? 🚀
