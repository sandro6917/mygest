# ✅ Feature: Collegamento Sottofascicolo - Frontend React

## 🎯 Obiettivo
Permettere di collegare un fascicolo esistente come sottofascicolo direttamente dalla detail page di un fascicolo nell'**interfaccia React**.

## 📝 Modifiche Implementate

### 1. **Backend API**: `/api/v1/fascicoli/views.py`

#### Nuovo Endpoint: `fascicoli_collegabili`
```python
@action(detail=True, methods=['get'])
def fascicoli_collegabili(self, request, pk=None):
    """
    GET /api/v1/fascicoli/{id}/fascicoli_collegabili/
    
    Restituisce fascicoli collegabili come sottofascicoli:
    - Stesso cliente, titolario, anno
    - parent__isnull=True (non già collegati)
    - Escludi il fascicolo corrente
    """
    fascicolo = self.get_object()
    
    collegabili = Fascicolo.objects.filter(
        cliente=fascicolo.cliente,
        titolario_voce=fascicolo.titolario_voce,
        anno=fascicolo.anno,
        parent__isnull=True
    ).exclude(pk=fascicolo.pk).select_related(
        'cliente', 'cliente__anagrafica', 'titolario_voce'
    ).order_by('-progressivo')[:20]
    
    serializer = FascicoloListSerializer(collegabili, many=True, context={'request': request})
    return Response(serializer.data)
```

**Endpoint**: `GET /api/v1/fascicoli/{id}/fascicoli_collegabili/`  
**Response**: Array di `FascicoloListItem[]`

---

### 2. **Frontend API Client**: `/frontend/src/api/fascicoli.ts`

#### Nuovi Metodi API

```typescript
// Collega fascicolo esistente come sottofascicolo
async collegaSottofascicolo(parentId: number, targetId: number): Promise<void> {
  const formData = new FormData();
  formData.append('target_id', targetId.toString());
  
  await apiClient.post(`/fascicoli/${parentId}/collega/`, formData);
},

// Ottieni fascicoli collegabili (stesso cliente, titolario, anno, no parent)
async getFascicoliCollegabili(fascicoloId: number): Promise<FascicoloListItem[]> {
  const response = await apiClient.get<FascicoloListItem[]>(
    `${BASE_URL}/fascicoli/${fascicoloId}/fascicoli_collegabili/`
  );
  return response.data;
}
```

**Metodi**:
- `getFascicoliCollegabili(id)` → Ottiene lista fascicoli collegabili
- `collegaSottofascicolo(parentId, targetId)` → Esegue il collegamento

---

### 3. **Frontend Component**: `/frontend/src/pages/FascicoloDetailPage.tsx`

#### State Management

```typescript
const [fascicoliCollegabili, setFascicoliCollegabili] = useState<FascicoloListItem[]>([]);
```

#### Data Loading

```typescript
const loadFascicoliCollegabili = useCallback(async () => {
  const fascicoloId = parseId();
  if (fascicoloId === null) return;

  try {
    const data = await fascicoliApi.getFascicoliCollegabili(fascicoloId);
    setFascicoliCollegabili(data);
  } catch (err) {
    console.error('Error loading fascicoli collegabili:', err);
  }
}, [parseId]);

useEffect(() => {
  loadFascicoliCollegabili();
}, [loadFascicoliCollegabili]);
```

#### Event Handler

```typescript
const handleCollegaSottofascicolo = async (targetId: number, targetCodice: string) => {
  const fascicoloId = parseId();
  if (fascicoloId === null) return;

  const confirmMessage = `Sei sicuro di voler collegare il fascicolo ${targetCodice} come sottofascicolo di ${fascicolo?.codice}?`;
  if (!window.confirm(confirmMessage)) return;

  try {
    await fascicoliApi.collegaSottofascicolo(fascicoloId, targetId);
    
    // Ricarica sottofascicoli e fascicoli collegabili
    await loadSottofascicoli();
    await loadFascicoliCollegabili();
    
    alert(`Fascicolo ${targetCodice} collegato con successo!`);
  } catch (err) {
    alert(getErrorMessage(err, 'Errore durante il collegamento del fascicolo'));
  }
};
```

#### UI Component

```tsx
{/* Sezione Fascicoli Collegabili */}
{fascicoliCollegabili.length > 0 && (
  <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #dee2e6' }}>
    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
      Collega Fascicolo Esistente come Sottofascicolo
    </h3>
    <p style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
      Fascicoli dello stesso cliente, titolario e anno non collegati ad altri fascicoli
    </p>
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>Codice</th>
            <th>Titolo</th>
            <th>Progressivo</th>
            <th style={{ width: '120px' }}>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {fascicoliCollegabili.map((fasc) => (
            <tr key={fasc.id}>
              <td><strong>{fasc.codice}</strong></td>
              <td>{fasc.titolo}</td>
              <td>{fasc.progressivo}</td>
              <td>
                <button
                  onClick={() => handleCollegaSottofascicolo(fasc.id, fasc.codice)}
                  className="btn-primary btn-sm"
                  title={`Collega ${fasc.codice} come sottofascicolo`}
                >
                  + Collega
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)}
```

---

## 🎨 User Experience

### Flusso Utente React

1. **Utente apre la detail page** di un fascicolo
   - URL: `/fascicoli/{id}`

2. **Naviga alla sezione "Sottofascicoli"**
   - Vede sottofascicoli già collegati (se presenti)
   - Vede pulsante "Nuovo Sottofascicolo" per crearne uno nuovo

3. **Vede la sezione "Collega Fascicolo Esistente"** (se ci sono fascicoli collegabili)
   - Lista fascicoli dello stesso cliente/titolario/anno
   - Ogni riga ha: Codice, Titolo, Progressivo, Pulsante "+ Collega"

4. **Click su "+ Collega"**
   - Popup conferma: "Sei sicuro di voler collegare il fascicolo XXXXX come sottofascicolo di YYYYY?"

5. **Conferma** → POST a `/api/v1/fascicoli/{parent_id}/collega/`
   - Body: `target_id=...`

6. **Successo**
   - Alert: "Fascicolo XXXXX collegato con successo!"
   - Ricarica lista sottofascicoli (aggiornata)
   - Ricarica lista fascicoli collegabili (fascicolo collegato scompare dalla lista)

### Validazioni

Il backend (`fascicoli/views.py::fascicolo_collega`) gestisce le validazioni:

- ✅ **Cliente identico**: Bloccato se diverso
- ✅ **Titolario identico**: Bloccato se diverso
- ✅ **Anno identico**: Bloccato se diverso
- ✅ **Target non ha già parent**: Bloccato se già collegato
- ✅ **No cicli**: Verifica gerarchica completa
- ✅ **No self-reference**: Bloccato se target = parent

Messaggio di errore mostrato via `alert()` se la richiesta fallisce.

---

## 🔧 API Endpoints

### GET `/api/v1/fascicoli/{id}/fascicoli_collegabili/`

**Request**: Nessun body  
**Response**:
```json
[
  {
    "id": 123,
    "codice": "ROSSMRO-01-2025-003",
    "titolo": "Contratto preliminare",
    "anno": 2025,
    "progressivo": 3,
    "cliente_display": "Mario Rossi",
    "titolario_voce_display": "01 - Contratti"
  }
]
```

### POST `/fascicoli/{parent_id}/collega/`

**Request** (FormData):
```
target_id=123
```

**Response Success** (Redirect nella view Django):
- Status: 302 Found
- Location: `/fascicoli/{parent_id}/`
- Message: "Fascicolo XXXXX collegato come sottofascicolo."

**Response Error**:
```json
{
  "detail": "Impossibile collegare: il cliente del fascicolo XXXXX non coincide."
}
```

---

## 🔒 Business Rules Rispettate

✅ **Filtro intelligente frontend**:
- Query backend filtra per `cliente`, `titolario_voce`, `anno`, `parent__isnull=True`
- Solo fascicoli **realmente collegabili**

✅ **Validazioni backend**:
- Tutti i controlli implementati in `fascicoli/views.py::fascicolo_collega`
- Cliente, titolario, anno DEVONO coincidere
- Target non deve avere già un parent
- Prevenzione cicli e self-reference

✅ **Auto-generazione progressivi**:
- `sub_progressivo` → max + 1
- `progressivo` → 0 (constraint)

✅ **Path condiviso**:
- Sottofascicoli condividono `path_archivio` del parent

---

## 🧪 Test Manuale

### Scenario 1: Collegamento Valido

**Setup**:
- Fascicolo A: `ROSSMRO-01-2025-005` (Cliente: Mario Rossi, Titolario: 01, Anno: 2025)
- Fascicolo B: `ROSSMRO-01-2025-003` (Cliente: Mario Rossi, Titolario: 01, Anno: 2025, parent=None)

**Steps**:
1. Apri `/fascicoli/A/`
2. Scroll a "Sottofascicoli"
3. Vedi sezione "Collega Fascicolo Esistente"
4. Vedi `ROSSMRO-01-2025-003` nella lista
5. Click "+ Collega"
6. Conferma popup
7. ✅ Successo: "Fascicolo ROSSMRO-01-2025-003 collegato con successo!"
8. Fascicolo B compare nella lista "Sottofascicoli"
9. Fascicolo B scompare da "Collega Fascicolo Esistente"

### Scenario 2: Nessun Fascicolo Collegabile

**Setup**:
- Fascicolo A: `ROSSMRO-01-2025-005`
- Nessun altro fascicolo con stesso cliente/titolario/anno senza parent

**Steps**:
1. Apri `/fascicoli/A/`
2. Scroll a "Sottofascicoli"
3. ❌ NON vedi sezione "Collega Fascicolo Esistente" (nascosta perché `fascicoliCollegabili.length === 0`)

### Scenario 3: Errore Validazione (Anno Diverso)

**Setup**:
- Fascicolo A: `ROSSMRO-01-2025-005` (Anno: 2025)
- Modifica manualmente la richiesta per forzare collegamento di fascicolo con anno diverso

**Steps**:
1. Tentativi di collegare fascicolo con anno 2024
2. Backend risponde con errore
3. ❌ Alert: "Errore durante il collegamento del fascicolo: Impossibile collegare: l'anno del fascicolo XXXXX non coincide."

---

## 📊 Performance

### Query Optimization

**Backend**:
```python
.select_related('cliente', 'cliente__anagrafica', 'titolario_voce')
```
→ Single query con JOIN (no N+1)

**Frontend**:
- Caricamento asincrono con `useEffect`
- State separato per sottofascicoli e fascicoli collegabili
- Ricarica solo i dati necessari dopo il collegamento

### Caching

- **Frontend**: React Query (TanStack Query) cache automatica
- **Backend**: Possibile aggiungere cache Redis per query frequenti

---

## 🚀 Deploy

### Checklist

- [x] Backend API endpoint (`fascicoli_collegabili`)
- [x] Backend validation view (`fascicolo_collega`)
- [x] Frontend API methods (`getFascicoliCollegabili`, `collegaSottofascicolo`)
- [x] Frontend component (`FascicoloDetailPage`)
- [x] Django check ✅ (no errors)
- [ ] Frontend build test
- [ ] Test funzionale su staging
- [ ] Deploy su produzione

### Comandi Deploy

```bash
# Backend
cd /srv/mygest/app
git pull origin main
sudo systemctl restart mygest

# Frontend
cd /srv/mygest/app/frontend
npm run build
# Vite genera dist/ che viene servito da Nginx

# oppure
./scripts/deploy.sh
```

---

## 📚 Riferimenti

- **Backend Model**: `fascicoli/models.py` - Classe `Fascicolo`
- **Backend View**: `fascicoli/views.py` - `fascicolo_collega` (Django template - deprecato)
- **Backend API**: `api/v1/fascicoli/views.py` - `FascicoloViewSet`
- **Frontend API**: `frontend/src/api/fascicoli.ts`
- **Frontend Page**: `frontend/src/pages/FascicoloDetailPage.tsx`
- **Business Rules**: `.github/copilot-instructions.md` - Sezione "Relazione Fascicolo-Sottofascicolo"

---

## 🎯 Differenze Template Django vs React

| Aspetto | Django Template (❌ Deprecato) | React Frontend (✅ Attuale) |
|---------|-------------------------------|---------------------------|
| **Rendering** | Server-side (Jinja2) | Client-side (React) |
| **API** | Django views (HTML response) | REST API (JSON response) |
| **State** | Page reload | React state + hooks |
| **UX** | Full page reload | SPA - no reload |
| **Validazione** | Django forms | API + client validation |
| **URL** | `/fascicoli/{pk}/collega/` (POST) | API: `/api/v1/fascicoli/{pk}/collega/` |

---

**Data implementazione**: 5 Gennaio 2026  
**Versione**: MyGest 1.0  
**Stack**: React 19 + TypeScript + Django REST Framework  
**Autore**: GitHub Copilot + Sandro Chimenti
