# Feature: Stampa Copertina A3 per Unità Fisica

## 📋 Riepilogo

Aggiunta la funzionalità di stampa della copertina A3 orizzontale per le unità fisiche dell'archivio.

## ✅ Modifiche Implementate

### 1. Backend - API Endpoint

**File**: `/api/v1/archivio_fisico/views.py`

Aggiunta nuova action `stampa_copertina_a3` al ViewSet `UnitaFisicaViewSet`:

```python
@action(detail=True, methods=['get'])
def stampa_copertina_a3(self, request, pk=None):
    """
    Genera e ritorna un PDF copertina A3 ORIZZONTALE per l'unità fisica.
    La copertina è configurata completamente da database (StampaModulo/StampaCampo).
    """
```

**Endpoint**: `GET /api/v1/archivio-fisico/unita/{id}/stampa_copertina_a3/`

### 2. Backend - Modulo di Stampa

**File**: `/scripts/setup_copertina_unita_a3.py`

Creato script per generare il modulo di stampa `COPERTINA_UNITA_A3`:
- **Formato**: A3 Orizzontale (420x297 mm)
- **Slug**: `COPERTINA_UNITA_A3`
- **Campi**: 24 (identici a COPERTINA_UNITA)
- **Traslazione**: Campi con x >= 170mm spostati di +210mm
- **Coordinate Y**: Mantenute identiche al modulo A4

**Esecuzione**:
```bash
source venv/bin/activate
python scripts/setup_copertina_unita_a3.py
```

### 3. Frontend - API Client

**File**: `/frontend/src/api/archivio.ts`

Aggiunte funzioni per la gestione della copertina A3:

```typescript
// API call
async stampaCopertinaA3(id: number): Promise<Blob>

// Utility per preview
export const previewCopertinaA3PDF = async (id: number)

// Utility per download
export const downloadCopertinaA3PDF = async (id: number, nomeFile?: string)
```

### 4. Frontend - UI

**File**: `/frontend/src/pages/UnitaFisicaDetailPage.tsx`

Aggiunto:
1. **Import** della funzione `previewCopertinaA3PDF`
2. **Handler** `handleStampaCopertinaA3()` 
3. **Pulsante** "Copertina A3" nell'header della pagina di dettaglio

```tsx
<button
  className="btn btn-secondary"
  onClick={handleStampaCopertinaA3}
  title="Stampa Copertina A3 Orizzontale"
>
  📋 <span>Copertina A3</span>
</button>
```

## 🎯 Funzionalità

### Differenze tra A4 e A3

| Caratteristica | COPERTINA_UNITA (A4) | COPERTINA_UNITA_A3 (A3) |
|---------------|---------------------|------------------------|
| Formato | 210x297 mm (Portrait) | 420x297 mm (Landscape) |
| Orientamento | Verticale | Orizzontale |
| Campi traslati | N/A | 2 campi (x >= 170mm) |
| Spazio aggiuntivo | N/A | +210mm larghezza |

### Campi Traslati

I seguenti campi sono stati spostati di +210mm sull'asse X:

1. **Data Stampa** (campo #2)
   - A4: x=195mm → A3: x=405mm
   
2. **ID Database** (campo #23)
   - A4: x=200mm → A3: x=410mm

### Elementi Adattati

- **Bordo principale**: esteso a 410mm di larghezza
- **Linee separatrici**: estese fino a 400mm
- **Campi descrizione/note**: larghezza aumentata a 380mm

## 🔗 Utilizzo

### Da Interfaccia Web

1. Aprire la pagina di dettaglio di un'unità fisica
2. Cliccare sul pulsante **"📋 Copertina A3"** nell'header
3. Il PDF si aprirà in una nuova scheda del browser

### Da API

```bash
# Con autenticazione JWT
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/archivio-fisico/unita/2/stampa_copertina_a3/ \
  --output copertina_a3.pdf
```

### Da Codice

```typescript
import { previewCopertinaA3PDF, downloadCopertinaA3PDF } from '@/api/archivio';

// Preview in nuova scheda
await previewCopertinaA3PDF(unitaId);

// Download diretto
await downloadCopertinaA3PDF(unitaId, 'mia_copertina_a3.pdf');
```

## 📊 Database

### Modulo di Stampa Creato

```sql
SELECT 
  nome, 
  slug, 
  formato.nome as formato,
  formato.larghezza_mm || 'x' || formato.altezza_mm as dimensioni
FROM stampe_stampamodulo
WHERE slug = 'COPERTINA_UNITA_A3';
```

Risultato:
- **Nome**: Copertina Unità Fisica A3 Orizzontale
- **Slug**: COPERTINA_UNITA_A3
- **Formato**: Copertina formato A3
- **Dimensioni**: 420x297 mm
- **Campi**: 24

## 🧪 Test

Per testare la generazione del PDF:

```bash
source venv/bin/activate
python test_copertina_a3.py
```

Il PDF di test sarà salvato in `/tmp/test_copertina_a3_{id}.pdf`

## 📝 Note Tecniche

- Il modulo usa il sistema di rendering configurabile via database (StampaModulo/StampaCampo)
- Il formato A3 "Copertina formato A3" deve esistere nel database (slug: "Copertina")
- La traslazione dei campi è configurata nello script di setup (TRASLAZIONE_X = 210.0)
- Le coordinate Y sono mantenute identiche per preservare il layout verticale

## 🔄 Manutenzione

### Rigenerare il Modulo

Se si desidera modificare il layout o rigenerare il modulo:

```bash
source venv/bin/activate
python scripts/setup_copertina_unita_a3.py
```

Lo script sovrascrive il modulo esistente mantenendo lo stesso slug.

### Modificare la Traslazione

Per modificare la traslazione dei campi, editare la variabile `TRASLAZIONE_X` in:
`/scripts/setup_copertina_unita_a3.py`

```python
TRASLAZIONE_X = 210.0  # Millimetri da aggiungere ai campi >= 170mm
```

## ✅ Checklist Completata

- [x] Endpoint API backend creato
- [x] Script di setup modulo A3 creato
- [x] Modulo COPERTINA_UNITA_A3 generato nel database
- [x] Funzioni API client frontend aggiunte
- [x] Handler UI frontend implementato
- [x] Pulsante UI aggiunto alla pagina di dettaglio
- [x] Test di generazione PDF completato
- [x] Documentazione creata

## 🚀 Deploy

Le modifiche sono pronte per il deploy. Non sono necessarie migrazioni database in quanto il modulo viene creato tramite script.

**Passi per il deploy**:

1. Push del codice su repository
2. Deploy backend standard
3. Eseguire lo script di setup sul server:
   ```bash
   python scripts/setup_copertina_unita_a3.py
   ```
4. Build e deploy frontend

---

**Data**: 22 Gennaio 2026
**Versione**: 1.0
**Feature**: Stampa Copertina A3 Unità Fisica
