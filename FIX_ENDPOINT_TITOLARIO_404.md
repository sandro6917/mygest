# Fix: Errore 404 su endpoint titolario voci

## Problema
Il frontend stava chiamando un endpoint non esistente:
```
GET /api/v1/fascicoli/titolario/voci/
```

Questo causava un errore 404:
```
Failed to load resource: the server responded with a status of 404 (Not Found)
FascicoloFormPage.tsx:113 Errore caricamento dati: AxiosError
```

## Causa
Nel file `frontend/src/api/fascicoli.ts`, la funzione `listTitolarioVoci()` stava costruendo l'URL con uno slash:
```typescript
const url = `${BASE_URL}/titolario/voci/?${queryString}`
```

Ma il backend ha registrato il router con un trattino:
```python
# api/v1/fascicoli/urls.py
router.register(r'titolario-voci', TitolarioVoceViewSet, basename='titolario-voce')
```

## Soluzione
✅ Modificato `frontend/src/api/fascicoli.ts`:

```typescript
// PRIMA (❌ errato)
const url = queryString 
  ? `${BASE_URL}/titolario/voci/?${queryString}` 
  : `${BASE_URL}/titolario/voci/`;

// DOPO (✅ corretto)
const url = queryString 
  ? `${BASE_URL}/titolario-voci/?${queryString}` 
  : `${BASE_URL}/titolario-voci/`;
```

✅ Migliorato anche il tipo di ritorno per gestire correttamente la paginazione:
```typescript
// PRIMA
const response = await apiClient.get<{ results: TitolarioVoce[] }>(url);
return response.data.results;

// DOPO (con fallback per sicurezza)
const response = await apiClient.get<{ count: number; results: TitolarioVoce[] }>(url);
return response.data.results || [];
```

## Endpoint Corretto
L'endpoint corretto è:
```
GET /api/v1/fascicoli/titolario-voci/
```

Che corrisponde al ViewSet registrato:
```python
router.register(r'titolario-voci', TitolarioVoceViewSet, basename='titolario-voce')
```

## Verifica
```bash
# L'endpoint ora risponde correttamente (401 = serve autenticazione, non 404)
curl -I http://localhost:8000/api/v1/fascicoli/titolario-voci/
# HTTP/1.1 401 Unauthorized (✅ corretto)
```

## File Modificati
- ✅ `frontend/src/api/fascicoli.ts`

## Test
- ✅ Nessun errore TypeScript introdotto
- ✅ Build frontend completata (errori pre-esistenti non correlati)
- ✅ Endpoint backend esistente e funzionante

## Convenzioni REST Django
Questa fix segue le convenzioni standard di Django REST Framework:
- Router usa trattini `-` per separare parole negli URL
- Es: `titolario-voci`, `archivio-fisico`, etc.
- NON slash `/` che indicherebbe percorsi nidificati

## Note
Il form di creazione/modifica fascicolo ora dovrebbe caricare correttamente la lista delle voci del titolario dal backend.

---
**Data**: 21 Gennaio 2026  
**Issue**: 404 su `/api/v1/fascicoli/titolario/voci/`  
**Risolto**: ✅ Endpoint corretto a `titolario-voci`
