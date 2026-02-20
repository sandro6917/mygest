# Feature: Collegamento Documenti Non Fascicolati al Fascicolo

## 📋 Descrizione
Implementata la possibilità di collegare documenti esistenti non fascicolati a un fascicolo dalla detail page del fascicolo stesso. La funzionalità permette di selezionare più documenti contemporaneamente tra quelli dello stesso cliente che non sono ancora stati assegnati a un fascicolo.

## 🎯 Obiettivo
Facilitare l'organizzazione dei documenti permettendo agli utenti di collegare rapidamente documenti esistenti a un fascicolo senza doverli modificare singolarmente.

## ✨ Funzionalità Implementate

### Frontend

#### 1. Componente CollegaDocumentiDialog
**File**: `/frontend/src/components/fascicoli/CollegaDocumentiDialog.tsx`

- **Dialog modale** con tabella dei documenti disponibili
- **Selezione multipla** con checkbox (singola o seleziona tutto)
- **Filtro automatico** per cliente e stato di fascicolazione
- **Indicatore di caricamento** durante il fetch dei dati
- **Gestione errori** con messaggi user-friendly
- **Stato di salvataggio** con disabilitazione dei pulsanti durante l'operazione
- **Callback di successo** per notificare il parent component

#### 2. Integrazione in FascicoloDetailPage
**File**: `/frontend/src/pages/FascicoloDetailPage.tsx`

- **Nuovo pulsante** "Collega Documenti" nella tab Documenti
- **Posizionamento** accanto al pulsante "Crea Documento"
- **Stile distintivo** (colore azzurro `#17a2b8`) per differenziarlo
- **Condizionale rendering** del dialog (solo se fascicolo e cliente sono definiti)
- **Auto-refresh** della lista documenti dopo il collegamento

### Backend

#### 1. FilterSet Personalizzato
**File**: `/api/v1/documenti/filters.py` (nuovo)

Creato un `DocumentoFilter` con supporto per:
- **Lookup avanzati** (`fascicolo__isnull` per documenti non fascicolati)
- **Filtri standard** (tipo, cliente, fascicolo, stato, digitale, tracciabile, ubicazione, out_aperto)
- **Filtri per date** (data_da, data_a con lookup gte/lte)

```python
class DocumentoFilter(django_filters.FilterSet):
    fascicolo__isnull = django_filters.BooleanFilter(
        field_name='fascicolo', 
        lookup_expr='isnull'
    )
    # ... altri filtri
```

#### 2. Aggiornamento DocumentoViewSet
**File**: `/api/v1/documenti/views.py`

- Importato il nuovo `DocumentoFilter`
- Sostituito `filterset_fields` con `filterset_class = DocumentoFilter`
- Rimossi filtri custom data_da/data_a (ora gestiti dal FilterSet)

### Types e API Client

#### 1. Aggiornamento DocumentoFilters
**File**: `/frontend/src/types/documento.ts`

Aggiunto il campo `fascicolo__isnull?: boolean` all'interfaccia `DocumentoFilters`:

```typescript
export interface DocumentoFilters {
  // ... altri campi
  fascicolo__isnull?: boolean; // Filtro per documenti non fascicolati
}
```

#### 2. Aggiornamento documentiApi.list()
**File**: `/frontend/src/api/documenti.ts`

Aggiunto supporto per il parametro `fascicolo__isnull`:

```typescript
if (filters.fascicolo__isnull !== undefined) {
  params.append('fascicolo__isnull', filters.fascicolo__isnull.toString());
}
```

## 🔄 Flusso Utente

1. **Apertura detail page fascicolo** → Tab "Documenti"
2. **Click su "Collega Documenti"** → Apre dialog modale
3. **Caricamento automatico** dei documenti non fascicolati dello stesso cliente
4. **Selezione documenti** (checkbox singoli o "Seleziona tutto")
5. **Click su "Collega"** → Aggiornamento documenti in batch
6. **Chiusura dialog** → Ricaricamento automatico lista documenti
7. **Notifica successo** → Alert con messaggio di conferma

## 📊 Query API

### Esempio richiesta documenti non fascicolati
```http
GET /api/v1/documenti/?cliente=123&fascicolo__isnull=true
```

### Esempio aggiornamento documento
```http
PATCH /api/v1/documenti/456/
Content-Type: application/json

{
  "fascicolo": 789
}
```

## 🎨 UI/UX

### Pulsante "Collega Documenti"
- **Colore**: Info blue (`#17a2b8`)
- **Icona**: AddIcon
- **Tooltip**: "Collega documenti esistenti non fascicolati"
- **Posizione**: A sinistra del pulsante "Crea Documento"

### Dialog
- **Larghezza**: `lg` (large)
- **Full width**: Sì
- **Tabella**: Compatta (`size="small"`)
- **Checkbox**: Header per "Seleziona tutto" con stato indeterminate
- **Righe**: Clickabili (tutta la riga seleziona/deseleziona)
- **Counter**: Mostra numero documenti selezionati

### Stati UI
- **Loading**: CircularProgress centrato
- **Empty**: Messaggio "Nessun documento disponibile"
- **Error**: Alert rosso con messaggio d'errore
- **Saving**: Pulsante "Collega" con CircularProgress e disabilitato

## 🧪 Testing

### Test Manuali Consigliati

1. **Caso base**: Collegare 1 documento non fascicolato
2. **Selezione multipla**: Collegare 3-5 documenti contemporaneamente
3. **Seleziona tutto**: Collegare tutti i documenti disponibili
4. **Nessun documento**: Verificare messaggio empty state
5. **Cliente senza documenti**: Verificare comportamento
6. **Annullamento**: Chiudere dialog senza salvare
7. **Errore rete**: Simulare errore API (disconnect)
8. **Reload**: Verificare che i documenti collegati appaiano nella lista

### Backend Tests (da implementare)

```python
# api/v1/documenti/tests.py
def test_filter_documenti_non_fascicolati():
    """Testa filtro fascicolo__isnull=true"""
    response = client.get('/api/v1/documenti/?fascicolo__isnull=true')
    assert all(doc['fascicolo'] is None for doc in response.data['results'])

def test_collega_documento_a_fascicolo():
    """Testa aggiornamento campo fascicolo"""
    doc = baker.make('documenti.Documento', fascicolo=None)
    fasc = baker.make('fascicoli.Fascicolo')
    
    response = client.patch(f'/api/v1/documenti/{doc.id}/', {
        'fascicolo': fasc.id
    })
    
    assert response.status_code == 200
    doc.refresh_from_db()
    assert doc.fascicolo == fasc
```

## 📝 Note Tecniche

### Performance
- **Batch update**: I documenti vengono aggiornati in parallelo con `Promise.all()`
- **Lazy loading**: Il dialog carica i documenti solo quando aperto
- **Reset state**: La selezione viene resettata ad ogni apertura

### Validazione
- **Frontend**: Controllo che `selectedDocumenti.size > 0` prima di salvare
- **Backend**: Validazione del modello Documento (es. vincoli cartaceo/fascicolato)

### Error Handling
- **Network errors**: Catch generico con messaggio user-friendly
- **API errors**: Logging in console + alert utente
- **Empty state**: Messaggio informativo invece di errore

## 🔐 Sicurezza
- **Permission**: `IsAuthenticated` richiesta per API documenti
- **Filter by cliente**: Solo documenti dello stesso cliente del fascicolo
- **Validation**: Validazione lato server delle operazioni di update

## 🚀 Deployment

Nessuna migrazione database richiesta. Solo modifiche a:
- **Frontend**: Build e deploy nuova versione
- **Backend**: Restart server per caricare nuovo FilterSet

## 📚 File Modificati/Creati

### Creati
- ✅ `/frontend/src/components/fascicoli/CollegaDocumentiDialog.tsx`
- ✅ `/api/v1/documenti/filters.py`

### Modificati
- ✅ `/frontend/src/pages/FascicoloDetailPage.tsx`
- ✅ `/frontend/src/types/documento.ts`
- ✅ `/frontend/src/api/documenti.ts`
- ✅ `/api/v1/documenti/views.py`

## ✅ Checklist Completamento

- [x] Componente dialog creato
- [x] Integrazione in detail page
- [x] API filter implementato
- [x] Types aggiornati
- [x] Error handling
- [x] Loading states
- [x] Success callback
- [x] Auto-refresh lista
- [x] Documentazione

## 🎉 Risultato Finale

Gli utenti possono ora:
1. Visualizzare rapidamente i documenti non fascicolati dello stesso cliente
2. Selezionare multipli documenti con pochi click
3. Collegarli al fascicolo corrente in un'unica operazione
4. Vedere immediatamente i risultati nella lista documenti

Questa feature migliora significativamente l'efficienza nella gestione dei documenti e l'organizzazione dei fascicoli.
