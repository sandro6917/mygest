# Feature: Stampa Etichetta Unità Fisica

## 📋 Panoramica

Aggiunta funzionalità per stampare l'etichetta di un'unità fisica dell'archivio in formato PDF, **ottimizzata per stampante Dymo LabelWriter 450 con etichette formato 30321 Large Address (89mm x 36mm, orientamento orizzontale)**.

## 🖨️ Specifiche Stampante

- **Modello**: Dymo LabelWriter 450
- **Formato etichetta**: DYMO S0722400 (30321 Large Address)
- **Dimensioni**: 89mm x 36mm (3.5" x 1.4")
- **Orientamento**: Orizzontale (landscape)
- **Layout**: Solo testo, NESSUN QR code
- **Configurazione**: Formato e margini letti dal database (`StampaModulo` + `StampaFormato`)

## 🎯 Implementazione

### Backend (Django)

#### 1. API Endpoint
**File modificato**: `/api/v1/archivio_fisico/views.py`

Aggiunta action `stampa_etichetta` al `UnitaFisicaViewSet` con supporto per formato Dymo:

```python
@action(detail=True, methods=['get'])
def stampa_etichetta(self, request, pk=None):
    """
    Genera e ritorna un PDF con l'etichetta dell'unità fisica
    Ottimizzato per Dymo LabelWriter 450 - Formato 30321 Large Address (89x36mm)
    """
    unita = self.get_object()
    
    include_qr = request.query_params.get('qr', 'true').lower() == 'true'
    mostra_path = request.query_params.get('path', 'true').lower() == 'true'
    formato = request.query_params.get('formato', 'dymo').lower()
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    if formato == 'dymo':
        return render_etichetta_dymo(
            unita, include_qr=include_qr, 
            mostra_path=mostra_path, base_url=base_url
        )
    else:
        return render_etichette_unita([unita], ...)
```

**Import aggiunto**:
```python
from archivio_fisico.pdf import render_etichette_unita, render_etichetta_dymo
```

#### 2. URL Endpoint
```
GET /api/v1/archivio-fisico/unita/{id}/stampa_etichetta/
```

**Query Parameters**:
- `qr` (boolean, default: **false**): Include QR code nell'etichetta (di solito non usato)
- `path` (boolean, default: true): Mostra il percorso completo
- `formato` (string, default: 'dymo'): Formato etichetta ('dymo' o 'standard')

**Response**:
- Content-Type: `application/pdf`
- Content-Disposition: `inline; filename="etichetta_dymo.pdf"`

#### 3. Funzione PDF Dymo
**File modificato**: `/archivio_fisico/pdf.py`

Funzione `render_etichetta_dymo()` ottimizzata per Dymo LabelWriter 450:

```python
def render_etichetta_dymo(unita, *, include_qr: bool = False, 
                          mostra_path: bool = True,
                          base_url: Optional[str] = None) -> HttpResponse:
    """
    Genera etichetta PDF ottimizzata per Dymo LabelWriter 450
    Legge dimensioni e margini dal database (StampaModulo + StampaFormato)
    """
    from stampe.models import StampaModulo
    
    # Recupera configurazione dal database
    modulo = StampaModulo.objects.select_related('formato').get(
        app_label='archivio_fisico',
        model_name='unitafisica',
        slug='Etichetta_archivio'
    )
    
    # Dimensioni da StampaFormato
    label_width = modulo.formato.larghezza_mm * mm  # 89mm
    label_height = modulo.formato.altezza_mm * mm   # 36mm
    
    # Margini da StampaFormato
    # Font da StampaModulo/StampaFormato
```

**Vantaggi configurazione database**:
- ✅ Dimensioni dinamiche da `StampaFormato`
- ✅ Margini personalizzabili
- ✅ Font configurabile
- ✅ Cambio formato senza modificare codice
- ✅ Tracciabilità configurazione

**Layout etichetta** (SENZA QR code):
```
┌────────────────────────────────────────────────────┐
│  TIPO • CODICE                                     │
│  Nome Unità Fisica                                 │
│  Path/Completo/Gerarchia                           │
└────────────────────────────────────────────────────┘
   Tutto lo spazio disponibile per il testo
```

### Frontend (React + TypeScript)

#### 1. API Service
**File creato**: `/frontend/src/api/archivio.ts`

Nuovo servizio API dedicato per le unità fisiche con funzioni:

```typescript
export const archivioApi = {
  list(): Promise<UnitaFisica[]>
  get(id: number): Promise<UnitaFisica>
  getTree(): Promise<UnitaFisicaTreeNode[]>
  getChildren(id: number): Promise<UnitaFisica[]>
  getAncestors(id: number): Promise<UnitaFisica[]>
  getRoots(): Promise<UnitaFisica[]>
  stampaEtichetta(id: number, options?: { qr?: boolean; path?: boolean }): Promise<Blob>
}

export const downloadEtichettaPDF(
  id: number, 
  nomeFile?: string,
  options?: { qr?: boolean; path?: boolean }
): Promise<void>
```

**Utility per anteprima PDF**:
```typescript
previewEtichettaPDF(unitaId, { qr: true, path: true })
```

**Utility per download PDF**:
```typescript
downloadEtichettaPDF(unitaId, 'etichetta_CON1.pdf', { qr: true, path: true })
```

#### 2. UI Component
**File modificato**: `/frontend/src/pages/UnitaFisicaDetailPage.tsx`

**Import aggiunto**:
```typescript
import { previewEtichettaPDF } from '@/api/archivio';
```

**Handler aggiunto**:
```typescript
const handleStampaEtichetta = async () => {
  if (!unita) return;
  
  try {
    await previewEtichettaPDF(
      unita.id,
      { qr: false, path: true, formato: 'dymo' }  // NESSUN QR code
    );
  } catch (err) {
    console.error('Errore nella stampa dell\'etichetta:', err);
    alert('Errore durante la generazione dell\'etichetta');
  }
};
```

**Pulsante aggiunto nell'header**:
```tsx
<button
  className="btn btn-secondary"
  onClick={handleStampaEtichetta}
  title="Visualizza Etichetta"
>
  🏷️ <span>Etichetta</span>
</button>
```

## 🧪 Test

### Test Backend
```python
# Django shell test
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_staff=True).first()

client = Client()
client.force_login(user)

response = client.get('/api/v1/archivio-fisico/unita/2/stampa_etichetta/')
print(f"Status: {response.status_code}")
print(f"PDF Size: {len(response.content)} bytes")

# Expected: 
# Status: 200
# Content-Type: application/pdf
# ✅ Etichetta PDF generata!
```

### Test Frontend
1. Navigare a: `/archivio/unita/{id}`
2. Cliccare sul pulsante "🏷️ Etichetta"
3. Verificare che si apra una nuova scheda con l'anteprima del PDF
4. (Opzionale) Dalla finestra di anteprima, stampare o salvare il PDF

## 📝 Formato Etichetta Dymo

L'etichetta PDF generata per Dymo LabelWriter 450 (formato DYMO S0722400 - 89x36mm) contiene:

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│    Tipo Unità • CODICE123                                │
│    Nome completo dell'Unità Fisica                       │
│    Path/Gerarchico/Completo/UFF1/ST1/SCF1               │
│                                                          │
└──────────────────────────────────────────────────────────┘
               Layout orizzontale 89x36mm (SENZA QR)
```

**Caratteristiche**:
- **NESSUN QR Code**: Tutto lo spazio per il testo
- **Testo**: 
  - Riga 1: Tipo + Codice (font bold, dimensione da DB)
  - Riga 2: Nome unità (font normale)
  - Riga 3: Path completo (font ridotto)
- **Margini**: Configurabili in `StampaFormato` (default: 3mm laterali, 2mm verticali)
- **Font**: Configurabile in `StampaModulo`/`StampaFormato`
- **Orientamento**: Landscape (orizzontale)

**Esempio**:
```
┌──────────────────────────────────────────────────────────┐
│    Contenitore • CON1                                    │
│    Scatola Verde Fascicoli 2024                          │
│    UFF1/ST1/SCF1/CON1                                    │
└──────────────────────────────────────────────────────────┘
```

## 🔧 Configurazione

### Personalizzazione Etichetta

**Parametri disponibili**:
- `qr`: true/false - Include QR code
- `path`: true/false - Mostra percorso completo

**Esempi**:

```typescript
// Anteprima formato Dymo SENZA QR code (default)
previewEtichettaPDF(id, { qr: false, path: true, formato: 'dymo' })

// Anteprima formato Dymo CON QR code (opzionale)
previewEtichettaPDF(id, { qr: true, path: true, formato: 'dymo' })

// Anteprima formato standard (A4 grid)
previewEtichettaPDF(id, { qr: false, path: true, formato: 'standard' })

// Download del PDF invece di anteprima
downloadEtichettaPDF(id, 'etichetta.pdf', { qr: false, path: true, formato: 'dymo' })
```

## 📦 Files Modificati/Creati

### Backend
- ✅ `/api/v1/archivio_fisico/views.py` - Action `stampa_etichetta` con formato da DB
- ✅ `/archivio_fisico/pdf.py` - Funzione `render_etichetta_dymo()` legge da `StampaModulo`
- ✅ `/stampe/models.py` - Modello `StampaModulo` + `StampaFormato` per configurazione
- ℹ️  Database: Record esistente `app=archivio_fisico, model=unitafisica, slug=Etichetta_archivio`
- ℹ️  `/archivio_fisico/pdf.py` - Funzione `render_etichette_unita()` (formato standard)

### Frontend
- ✅ `/frontend/src/api/archivio.ts` - Nuovo servizio API (creato)
- ✅ `/frontend/src/pages/UnitaFisicaDetailPage.tsx` - Aggiunto pulsante stampa
- ✅ `/frontend/src/api/documenti.ts` - Fix filtro ubicazione
- ✅ `/frontend/src/api/fascicoli.ts` - Fix filtro ubicazione

## 🎨 UI/UX

### Posizionamento
Il pulsante "Etichetta" è posizionato nell'header della detail page, accanto a:
- "Modifica" (btn-secondary)
- "Aggiungi Sottounità" (btn-primary)

### Icona
Emoji 🏷️ utilizzata per rappresentare visivamente l'azione di visualizzazione etichetta.

### Comportamento
1. Click su pulsante → Chiamata API asincrona
2. Apertura automatica nuova scheda browser con anteprima PDF
3. L'utente può stampare o salvare dalla finestra di anteprima
4. Alert su errore se la generazione fallisce

## 🚀 Utilizzo

### Scenario d'uso tipico

1. **Navigazione**: Utente va alla pagina archivio `/archivio`
2. **Selezione**: Clicca su un'unità fisica nel TreeView
3. **Visualizzazione**: Viene mostrata la detail page `/archivio/unita/{id}`
4. **Anteprima**: Clicca su "🏷️ Etichetta"
5. **Preview**: Si apre nuova scheda con anteprima PDF
6. **Stampa fisica**: L'utente stampa il PDF su stampante per etichette
7. **Applicazione**: Applica l'etichetta adesiva sull'unità fisica

### Business Value

- ✅ **Configurazione database**: Dimensioni e margini in `StampaModulo`/`StampaFormato`
- ✅ **Etichette ottimizzate**: Layout perfetto per Dymo LabelWriter 450
- ✅ **Massimo spazio testo**: Nessun QR code, tutto per informazioni leggibili
- ✅ **Identificazione univoca**: Ogni unità fisica ha etichetta dedicata
- ✅ **Riduzione errori**: Posizionamento documenti sempre corretto
- ✅ **Miglioramento efficienza**: Ricerca fisica ultra-rapida
- ✅ **Conformità normative**: Tracciabilità completa archivio
- ✅ **Formato professionale**: Etichette stampabili di qualità
- ✅ **Flessibilità**: Cambio formato senza modificare codice

## 🗄️ Configurazione Database

### StampaFormato (già esistente)

```sql
SELECT * FROM stampe_stampaformato WHERE nome = 'DYMO S0722400';

-- Risultato:
nome: DYMO S0722400
slug: dymo-s0722400
larghezza_mm: 89.0
altezza_mm: 36.0
orientamento: L (Landscape)
margine_top_mm: 2.0
margine_right_mm: 3.0
margine_bottom_mm: 2.0
margine_left_mm: 3.0
font_nome_default: Helvetica
font_size_default: 10.0
```

### StampaModulo (già esistente)

```sql
SELECT * FROM stampe_stampamodulo 
WHERE app_label = 'archivio_fisico' 
  AND model_name = 'unitafisica';

-- Risultato:
nome: Etichetta archivio
slug: Etichetta_archivio
formato_id: [FK a DYMO S0722400]
app_label: archivio_fisico
model_name: unitafisica
```

**Come modificare le dimensioni**:
1. Accedi a Django Admin: `/admin/stampe/stampaformato/`
2. Modifica il formato "DYMO S0722400"
3. Cambia `larghezza_mm`, `altezza_mm`, margini
4. Salva → Le etichette useranno subito le nuove dimensioni!

## 🖨️ Istruzioni Stampa Dymo

### Configurazione Stampante

1. **Driver**: Installare Dymo Label Software v8 o superiore
2. **Formato carta**: Selezionare "30321 Large Address Label"
3. **Orientamento**: Orizzontale (Landscape)
4. **Margini**: Nessun margine (usa tutto lo spazio disponibile)
5. **Scala**: 100% (nessuna riduzione)

### Procedura Stampa

1. Clicca su "🏷️ Etichetta" nella detail page
2. Si apre anteprima PDF in nuova scheda
3. Ctrl+P (o Cmd+P su Mac) per stampare
4. **Seleziona stampante**: Dymo LabelWriter 450
5. **Dimensioni pagina**: Personalizzata 89x36mm
6. **Orientamento**: Orizzontale
7. **Margini**: Nessuno
8. Stampa!

### Verifica Qualità

- ✅ Testo nitido e leggibile
- ✅ Nessun troncamento informazioni
- ✅ Layout centrato sull'etichetta
- ✅ Nessun margine bianco eccessivo
- ✅ Tutte le 3 righe visibili (Tipo•Codice, Nome, Path)

## 📚 Riferimenti

- **Business Logic**: `/home/sandro/mygest/.github/copilot-instructions.md` - Sezione "Archivio Fisico"
- **PDF Generation**: `/home/sandro/mygest/archivio_fisico/pdf.py`
- **API Docs**: Endpoint documentato in DRF browsable API
- **Frontend Routes**: `/frontend/src/routes/index.tsx`

---

**Data implementazione**: 14 Gennaio 2025  
**Versione**: 1.0.0  
**Status**: ✅ Completato e testato
