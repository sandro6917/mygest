# Fix Filtro Ubicazione - Archivio Fisico

## Problema Rilevato
Nella `UnitaFisicaDetailPage`, i documenti e fascicoli mostrati non erano filtrati per ubicazione. 
Venivano sempre mostrati gli stessi elementi indipendentemente dall'unità fisica selezionata.

## Causa
1. **Fascicoli**: Il filtro `ubicazione` non era presente in `filterset_fields` dell'API
2. **Frontend**: I parametri passati alle API usavano `ubicazione_id` invece di `ubicazione`
3. **Types**: Il filtro `ubicazione` non era definito nei types TypeScript

## Modifiche Applicate

### Backend
**File**: `/api/v1/fascicoli/views.py`
```python
# PRIMA
filterset_fields = ['anno', 'stato', 'cliente', 'titolario_voce', 'parent']

# DOPO
filterset_fields = ['anno', 'stato', 'cliente', 'titolario_voce', 'parent', 'ubicazione']
```

### Frontend Types

**File**: `/frontend/src/types/documento.ts`
```typescript
export interface DocumentoFilters {
  // ... altri campi
  ubicazione?: number;  // AGGIUNTO
  ordering?: string;
}
```

**File**: `/frontend/src/types/fascicolo.ts`
```typescript
export interface FascicoloFilters {
  // ... altri campi
  ubicazione?: number;  // AGGIUNTO
  parent?: number | string;
  ordering?: string;
  con_file?: string;
}
```

### Frontend Component

**File**: `/frontend/src/pages/UnitaFisicaDetailPage.tsx`
```typescript
// PRIMA (ERRATO)
const documentiResponse = await documentiApi.list({ ubicazione_id: Number(id) } as any, 1, 100);
const fascicoliResponse = await fascicoliApi.list({ ubicazione_id: Number(id) } as any);

// DOPO (CORRETTO)
const documentiResponse = await documentiApi.list({ ubicazione: Number(id) }, 1, 100);
const fascicoliResponse = await fascicoliApi.list({ ubicazione: Number(id) });
```

## Verifica Funzionamento

### API Backend
```bash
# Test filtro documenti per ubicazione
curl "http://localhost:8000/api/v1/documenti/?ubicazione=1"

# Test filtro fascicoli per ubicazione  
curl "http://localhost:8000/api/v1/fascicoli/?ubicazione=1"
```

### Frontend
1. Aprire `/archivio`
2. Cliccare su un'unità fisica
3. Verificare che i tab "Documenti" e "Fascicoli" mostrino solo elementi con quella ubicazione
4. Navigare ad un'altra unità fisica
5. Verificare che i contenuti cambino correttamente

## Query Database Corrette

Ora le API filtrano correttamente:

**Documenti**:
```sql
SELECT * FROM documenti_documento 
WHERE ubicazione_id = {unita_fisica_id}
```

**Fascicoli**:
```sql
SELECT * FROM fascicoli_fascicolo 
WHERE ubicazione_id = {unita_fisica_id}
```

## Test di Regressione

✅ Il filtro `ubicazione` ora funziona correttamente sia per documenti che fascicoli
✅ La UnitaFisicaDetailPage mostra solo gli elementi effettivamente archiviati in quella unità
✅ Navigando tra diverse unità fisiche, i contenuti si aggiornano correttamente
✅ I types TypeScript sono corretti e non richiedono più casting `as any`

## Note
- Il filtro per documenti era già presente, ma veniva chiamato con il parametro errato
- Il filtro per fascicoli è stato aggiunto ex-novo nell'API
- Entrambi i filtri sono ora documentati nei types TypeScript
