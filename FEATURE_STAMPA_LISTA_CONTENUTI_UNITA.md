# Feature: Stampa Lista Contenuti Unità Fisica

## 📋 Descrizione

Implementata la funzionalità di stampa PDF della lista degli oggetti contenuti in un'unità fisica dell'archivio. L'utente può scegliere tra tre tipi di liste:
1. **Sottounità** - Elenco delle unità fisiche figlie
2. **Fascicoli** - Elenco dei fascicoli archiviati nell'unità
3. **Documenti** - Elenco dei documenti cartacei archiviati nell'unità

Tutte le liste utilizzano il sistema di stampe configurabile tramite database (`StampaLista`).

## 🎯 Obiettivo

Permettere agli utenti di generare PDF con l'elenco completo degli oggetti contenuti in un'unità fisica specifica, con template configurabili nel database.

## ✅ Implementazione

### Backend

#### 1. API Endpoint (`/api/v1/archivio_fisico/views.py`)

**Action aggiunta a `UnitaFisicaViewSet`:**

```python
@action(detail=True, methods=['get'])
def stampa_lista_contenuti(self, request, pk=None):
    """
    Genera e ritorna un PDF con la lista degli oggetti contenuti nell'unità fisica.
    Supporta tre tipi di liste configurabili tramite parametro 'lista':
    - LST_OBJ: sottounità (default)
    - LST_FASCICOLI_UBICAZIONE: fascicoli
    - LST_DOCUMENTI_UBICAZIONE: documenti
    """
```

**URL Endpoint:**
```
GET /api/v1/archivio-fisico/unita/{id}/stampa_lista_contenuti/
```

**Query Parameters:**
- `lista` (opzionale): slug della `StampaLista` da utilizzare
  - `LST_OBJ` - Sottounità (default)
  - `LST_FASCICOLI_UBICAZIONE` - Fascicoli
  - `LST_DOCUMENTI_UBICAZIONE` - Documenti

### Frontend

#### 2. API Client (`/frontend/src/api/archivio.ts`)

**Funzione aggiunta:**
```typescript
async stampaListaContenuti(id: number, listaSlug?: string): Promise<Blob>
```

**Utility functions:**
- `previewListaContenutiPDF(id, listaSlug?)` - Apre PDF in nuova scheda
- `downloadListaContenutiPDF(id, nomeFile?, listaSlug?)` - Scarica PDF

#### 3. UI Component (`/frontend/src/pages/UnitaFisicaDetailPage.tsx`)

**Dropdown Menu** con tre opzioni:
- 📁 Sottounità
- 📂 Fascicoli  
- 📄 Documenti

**Features UI:**
- Menu dropdown che si apre al click
- Si chiude automaticamente cliccando fuori
- Hover effect sulle voci del menu
- Icone distintive per ogni tipo di lista

## 🗄️ Configurazione Database

### Script di Setup

Due script Python per inizializzare le configurazioni:

1. **`scripts/setup_colonne_lista_unita.py`** - Configura lista sottounità
2. **`scripts/setup_lista_contenuti_unita.py`** - Configura liste fascicoli e documenti

### Liste Configurate

#### 1. Lista Sottounità (`LST_OBJ`)
- **App/Model**: `archivio_fisico.unitafisica`
- **Filtro**: `parent_id = :unita_id`
- **Colonne**: Codice, Nome, Tipo, Percorso, Attivo, Archivio Fisso

#### 2. Lista Fascicoli (`LST_FASCICOLI_UBICAZIONE`)
- **App/Model**: `fascicoli.fascicolo`
- **Filtro**: `ubicazione_id = :unita_id`
- **Colonne**: Codice, Titolo, Anno, Cliente, Titolario, Stato

#### 3. Lista Documenti (`LST_DOCUMENTI_UBICAZIONE`)
- **App/Model**: `documenti.documento`
- **Filtro**: `ubicazione_id = :unita_id` AND `digitale = False`
- **Colonne**: Codice, Descrizione, Tipo, Data, Cliente, Fascicolo, Stato

## 📊 Flusso Utente

1. L'utente naviga alla detail page di un'unità fisica
2. Clicca sul pulsante "📋 Lista Contenuti ▼"
3. Si apre un menu dropdown con tre opzioni
4. L'utente seleziona il tipo di lista desiderato
5. Il PDF si apre in una nuova scheda del browser

## 🎨 UI/UX

### Dropdown Menu
- **Posizione**: Header della detail page
- **Stile**: Pulsante secondario con freccia down
- **Menu items**:
  - Sfondo bianco con bordo sottile
  - Hover effect grigio chiaro
  - Icone colorate per ogni tipo
  - Auto-close al click o fuori area

### Responsive
- Il menu si adatta alla larghezza del contenuto
- Posizionamento assoluto per overlay pulito

## 🔧 Script di Setup

### Setup Liste (da eseguire una volta)

```bash
cd /home/sandro/mygest
source venv/bin/activate

# Setup lista sottounità
python scripts/setup_colonne_lista_unita.py

# Setup liste fascicoli e documenti
python scripts/setup_lista_contenuti_unita.py
```

## 🧪 Testing

### Test Manuale

1. Assicurarsi che le configurazioni siano state create (script setup)
2. Navigare a un'unità fisica con contenuti
3. Testare ciascuna opzione del menu:
   - ✅ Sottounità
   - ✅ Fascicoli
   - ✅ Documenti
4. Verificare che i PDF si aprano correttamente
5. Verificare che il contenuto sia corretto per ogni tipo

### Test Edge Cases

- Unità senza contenuti → PDF vuoto o messaggio
- Configurazione `StampaLista` mancante → errore HTTP 404 con messaggio dettagliato
- Click fuori dal menu → menu si chiude

## 📝 Note Tecniche

- Sistema completamente configurabile da database
- Supporto placeholder nei filtri (`:unita_id`)
- PDF generato server-side con ReportLab
- Menu dropdown implementato con React state
- Auto-close del menu con event listener

## 🚀 Estensioni Future

- [ ] Aggiungi opzione "Stampa Tutto" (sottounità + fascicoli + documenti in un unico PDF)
- [ ] Permetti download oltre a preview
- [ ] Aggiungi anteprima numero elementi per ogni tipo nel tooltip
- [ ] Supporto export Excel/CSV
- [ ] Filtri personalizzabili dall'utente prima della stampa

## ✅ Checklist Implementazione

- [x] Backend API endpoint
- [x] Frontend API client
- [x] UI component con dropdown
- [x] Import statements
- [x] Error handling
- [x] Configurazione database liste
- [x] Script di setup automatico
- [x] Menu dropdown funzionante
- [x] Auto-close menu
- [x] Documentazione completa

## 📚 Riferimenti

- **Models**: `/home/sandro/mygest/stampe/models.py`
- **Services**: `/home/sandro/mygest/stampe/services.py`
- **API Views**: `/home/sandro/mygest/api/v1/archivio_fisico/views.py`
- **Frontend API**: `/home/sandro/mygest/frontend/src/api/archivio.ts`
- **Frontend Page**: `/home/sandro/mygest/frontend/src/pages/UnitaFisicaDetailPage.tsx`
- **Script Setup**: `/home/sandro/mygest/scripts/setup_lista_contenuti_unita.py`

---

**Data implementazione**: 15 Gennaio 2026  
**Versione**: 2.0 (con dropdown multi-lista)  
**Autore**: GitHub Copilot


## 🎯 Obiettivo

Permettere agli utenti di generare un PDF con l'elenco completo degli oggetti (sottounità, fascicoli, documenti) contenuti in un'unità fisica specifica, utilizzando template configurabili nel database.

## ✅ Implementazione

### Backend

#### 1. API Endpoint (`/api/v1/archivio_fisico/views.py`)

**Nuova action aggiunta a `UnitaFisicaViewSet`:**

```python
@action(detail=True, methods=['get'])
def stampa_lista_contenuti(self, request, pk=None):
    """
    Genera e ritorna un PDF con la lista degli oggetti contenuti nell'unità fisica.
    Utilizza StampaLista configurato come "archivio_fisico.archiviofisicolistastampa"
    """
    unita = self.get_object()
    
    # Ottieni il ContentType per UnitaFisica
    ct = ContentType.objects.get_for_model(UnitaFisica)
    
    # Cerca la StampaLista specifica per archivio_fisico
    lista_slug = request.GET.get("lista", "archiviofisicolistastampa")
    lista = get_lista_for(ct, lista_slug)
    
    # Parametri per il filtro: mostra contenuti di questa unità
    params = {
        "unita_id": str(pk),
    }
    params.update(request.GET.dict())
    
    # Genera il PDF
    pdf_bytes = render_lista_pdf(ct, lista, params, extra_context={"unita": unita})
    
    # Ritorna come FileResponse
    filename = f"contenuti_unita_{unita.codice}_{pk}.pdf"
    return FileResponse(
        BytesIO(pdf_bytes),
        filename=filename,
        content_type="application/pdf"
    )
```

**URL Endpoint:**
```
GET /api/v1/archivio-fisico/unita/{id}/stampa_lista_contenuti/
```

**Query Parameters:**
- `lista` (opzionale): slug della `StampaLista` da utilizzare (default: `"archiviofisicolistastampa"`)
- Qualsiasi altro parametro viene passato al sistema di filtri della lista

**Import aggiunti:**
```python
from stampe.services import render_lista_pdf, get_lista_for
from django.contrib.contenttypes.models import ContentType
from io import BytesIO
```

### Frontend

#### 2. API Client (`/frontend/src/api/archivio.ts`)

**Nuova funzione aggiunta a `archivioApi`:**

```typescript
/**
 * Stampa la lista degli oggetti contenuti nell'unità fisica
 * Utilizza StampaLista configurato come "archivio_fisico.archiviofisicolistastampa"
 * @param id - ID dell'unità fisica
 * @param listaSlug - Slug della lista di stampa (default: "archiviofisicolistastampa")
 */
async stampaListaContenuti(id: number, listaSlug?: string): Promise<Blob> {
  const params = new URLSearchParams();
  if (listaSlug) {
    params.append('lista', listaSlug);
  }
  
  const response = await apiClient.get(`${BASE_URL}/${id}/stampa_lista_contenuti/`, {
    responseType: 'blob',
    params,
  });
  
  return response.data;
}
```

**Utility functions esportate:**

```typescript
/**
 * Utility per aprire l'anteprima del PDF della lista contenuti in una nuova scheda
 */
export const previewListaContenutiPDF = async (id: number, listaSlug?: string) => {
  const blob = await archivioApi.stampaListaContenuti(id, listaSlug);
  const url = window.URL.createObjectURL(blob);
  
  const newWindow = window.open(url, '_blank');
  
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
  }, 100);
  
  return newWindow;
};

/**
 * Utility per scaricare il PDF della lista contenuti
 */
export const downloadListaContenutiPDF = async (id: number, nomeFile?: string, listaSlug?: string) => {
  const blob = await archivioApi.stampaListaContenuti(id, listaSlug);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `lista_contenuti_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
```

#### 3. UI Component (`/frontend/src/pages/UnitaFisicaDetailPage.tsx`)

**Import aggiunto:**
```typescript
import { previewEtichettaPDF, previewListaContenutiPDF } from '@/api/archivio';
```

**Handler aggiunto:**
```typescript
const handleStampaListaContenuti = async () => {
  if (!unita) return;
  
  try {
    // Stampa lista contenuti usando StampaLista "archiviofisicolistastampa"
    await previewListaContenutiPDF(unita.id);
  } catch (err) {
    console.error('Errore nella stampa della lista contenuti:', err);
    alert('Errore durante la generazione della lista contenuti');
  }
};
```

**Pulsante aggiunto nell'header:**
```tsx
<button
  className="btn btn-secondary"
  onClick={handleStampaListaContenuti}
  title="Stampa Lista Contenuti"
>
  📋 <span>Lista Contenuti</span>
</button>
```

## 🔧 Configurazione Database

Per utilizzare questa funzionalità, è necessario configurare nel database Django Admin:

### 1. Creare StampaFormato
- Nome: "A4 Landscape" (esempio)
- Larghezza: 297mm
- Altezza: 210mm
- Orientamento: Landscape
- Margini: configurabili

### 2. Creare StampaLista
- **app_label**: `archivio_fisico`
- **model_name**: `unitafisica`
- **slug**: `archiviofisicolistastampa`
- **nome**: "Lista Contenuti Unità Fisica"
- **formato**: riferimento a StampaFormato creato sopra
- **is_default**: True (opzionale)
- **layout**: `table` o `tree` (a seconda delle esigenze)

### 3. Configurare StampaColonna
Per ogni colonna della lista, creare record con:
- **lista**: riferimento a StampaLista creata sopra
- **ordine**: numero progressivo
- **tipo**: `text`, `template`, `barcode`, `qrcode`
- **label**: intestazione colonna
- **attr_path**: percorso attributo (es. `codice`, `nome`, `tipo_display`)
- **larghezza_mm**: larghezza colonna in millimetri
- **align**: `left`, `center`, `right`

### Esempio configurazione colonne:

| Ordine | Label | attr_path | larghezza_mm | align |
|--------|-------|-----------|--------------|-------|
| 1 | Codice | codice | 30 | left |
| 2 | Nome | nome | 60 | left |
| 3 | Tipo | tipo_display | 40 | left |
| 4 | Stato | attivo | 20 | center |

### 4. Configurare filtri (opzionale)

Nel campo `filter_def` di StampaLista (JSON):
```json
{
  "parent_id": ":unita_id",
  "attivo": true
}
```

Dove `:unita_id` è un placeholder che verrà sostituito con l'ID dell'unità corrente.

### 5. Configurare ordinamento (opzionale)

Nel campo `order_by` di StampaLista (JSON):
```json
["tipo", "codice", "nome"]
```

## 📊 Flusso Utente

1. L'utente naviga alla detail page di un'unità fisica
2. L'utente clicca sul pulsante "📋 Lista Contenuti"
3. Il frontend chiama l'API `stampa_lista_contenuti`
4. Il backend:
   - Recupera la configurazione `StampaLista` dal database
   - Applica i filtri per mostrare solo i contenuti dell'unità
   - Genera il PDF utilizzando il servizio `render_lista_pdf`
   - Ritorna il PDF come blob
5. Il frontend apre il PDF in una nuova scheda del browser

## 🎨 UI/UX

- **Posizione**: Header della detail page, accanto al pulsante "Etichetta"
- **Icona**: 📋 (clipboard/lista)
- **Stile**: `btn btn-secondary`
- **Tooltip**: "Stampa Lista Contenuti"

## 🔍 Query Database

Il sistema di stampe utilizza i filtri configurati in `StampaLista.filter_def` per determinare quali oggetti includere nella lista.

**Esempio query generata:**
```python
UnitaFisica.objects.filter(parent_id=<unita_id>, attivo=True).order_by('tipo', 'codice', 'nome')
```

## 🧪 Testing

### Test Manuale

1. Creare configurazione `StampaLista` in Django Admin
2. Navigare a un'unità fisica con contenuti
3. Cliccare su "📋 Lista Contenuti"
4. Verificare che il PDF si apra in una nuova scheda
5. Verificare che il contenuto mostri gli oggetti corretti

### Test Edge Cases

- Unità senza contenuti → lista vuota
- Configurazione `StampaLista` mancante → errore gestito
- Formato PDF non valido → errore gestito

## 📝 Note Tecniche

- Il sistema è completamente configurabile da database senza modifiche al codice
- Supporta placeholder nei filtri (es. `:unita_id`)
- Compatibile con layout tabella e albero
- Utilizza il servizio di stampe centralizzato (`stampe.services`)
- Il PDF viene generato server-side con ReportLab

## 🚀 Estensioni Future

- [ ] Aggiungere opzione download oltre a preview
- [ ] Permettere selezione di diverse liste dalla UI
- [ ] Aggiungere filtri interattivi prima della stampa
- [ ] Supporto per stampa di più unità in batch
- [ ] Export in formati alternativi (Excel, CSV)

## ✅ Checklist Implementazione

- [x] Backend API endpoint
- [x] Frontend API client
- [x] UI component e handler
- [x] Import statements
- [x] Error handling
- [x] Documentazione
- [ ] Configurazione database di esempio
- [ ] Test automatizzati

## 📚 Riferimenti

- **Models**: `/home/sandro/mygest/stampe/models.py`
- **Services**: `/home/sandro/mygest/stampe/services.py`
- **API Views**: `/home/sandro/mygest/api/v1/archivio_fisico/views.py`
- **Frontend API**: `/home/sandro/mygest/frontend/src/api/archivio.ts`
- **Frontend Page**: `/home/sandro/mygest/frontend/src/pages/UnitaFisicaDetailPage.tsx`

---

**Data implementazione**: 15 Gennaio 2026  
**Versione**: 1.0  
**Autore**: GitHub Copilot
