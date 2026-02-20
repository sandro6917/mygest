# Feature: Uniformazione Ricerca per ID e Tempi di Risposta

**Data**: 2026-02-17
**Tipo**: Enhancement
**Moduli**: Pratiche, Fascicoli, Documenti

## 📝 Descrizione

Uniformazione del campo ricerca e della procedura di filtraggio nelle list page di pratiche, fascicoli e documenti, con l'aggiunta dell'ID tra gli attributi ricercabili e uniformazione dei tempi di risposta del debounce.

## 🎯 Obiettivi

1. **Aggiungere ID come campo ricercabile** in tutti e tre i moduli
2. **Uniformare tempi di debounce** a 300ms per tutte le list page
3. **Migliorare esperienza utente** con ricerca più veloce e uniforme

## 🔧 Modifiche Implementate

### Backend - API ViewSets

#### 1. Pratiche (`api/v1/pratiche/views.py`)

```python
# BEFORE
search_fields = ['codice', 'oggetto', 'note', 'tag']

# AFTER
search_fields = ['id', 'codice', 'oggetto', 'note', 'tag']
```

**Impatto**: Gli utenti possono ora cercare pratiche direttamente per ID numerico.

#### 2. Fascicoli (`api/v1/fascicoli/views.py`)

**FascicoloViewSet**:
```python
# BEFORE
search_fields = ['codice', 'titolo', 'note']

# AFTER
search_fields = ['id', 'codice', 'titolo', 'note']
```

**TitolarioVoceViewSet**:
```python
# BEFORE
search_fields = ['codice', 'titolo', 'anagrafica__nome', 'anagrafica__cognome']

# AFTER
search_fields = ['id', 'codice', 'titolo', 'anagrafica__nome', 'anagrafica__cognome']
```

**Impatto**: Ricerca fascicoli e voci titolario per ID numerico abilitata.

#### 3. Documenti (`api/v1/documenti/views.py`)

```python
# BEFORE
search_fields = ['codice', 'descrizione', 'tags', 'note', 'ubicazione__codice', 'ubicazione__nome', 'ubicazione__full_path']

# AFTER
search_fields = ['id', 'codice', 'descrizione', 'tags', 'note', 'ubicazione__codice', 'ubicazione__nome', 'ubicazione__full_path']
```

**Impatto**: Ricerca documenti per ID numerico abilitata.

### Frontend - List Pages

#### 1. Pratiche (`frontend/src/pages/PraticheListPage.tsx`)

```typescript
// BEFORE: 500ms debounce
searchTimeoutRef.current = window.setTimeout(() => {
  setFilters((prev) => ({
    ...prev,
    page: 1,
    search: value || undefined,
  }));
}, 500);

// AFTER: 300ms debounce
searchTimeoutRef.current = window.setTimeout(() => {
  setFilters((prev) => ({
    ...prev,
    page: 1,
    search: value || undefined,
  }));
}, 300);
```

#### 2. Fascicoli (`frontend/src/pages/FascicoliListPage.tsx`)

```typescript
// BEFORE: 500ms debounce
searchTimeoutRef.current = window.setTimeout(() => {
  if (searchQuery.length === 0 || searchQuery.length >= 3) {
    setDebouncedSearchQuery(searchQuery);
  }
}, 500);

// AFTER: 300ms debounce
searchTimeoutRef.current = window.setTimeout(() => {
  if (searchQuery.length === 0 || searchQuery.length >= 3) {
    setDebouncedSearchQuery(searchQuery);
  }
}, 300);
```

#### 3. Documenti (`frontend/src/pages/DocumentiListPage.tsx`)

**Nessuna modifica necessaria** - già implementato con 300ms debounce.

## ✅ Vantaggi

### 1. Ricerca per ID
- **Precisione**: Possibilità di cercare oggetti specifici tramite ID numerico
- **Debug**: Facilita troubleshooting e supporto utenti
- **Integrazione**: Migliore integrazione con sistemi esterni che usano ID

### 2. Uniformità Tempi di Risposta
- **300ms per tutte le list page** (prima: 300ms documenti, 500ms pratiche/fascicoli)
- **Esperienza utente coerente** tra tutte le sezioni
- **Bilanciamento ottimale**:
  - Veloce abbastanza per digitazione manuale
  - Sufficiente per lettori barcode/QR code

### 3. Benefici UX
- **Ricerca più reattiva**: 200ms di risposta in meno per pratiche e fascicoli
- **Comportamento prevedibile**: stessa logica in tutte le sezioni
- **Supporto lettori**: tempo adeguato per acquisizione codici

## 📊 Casi d'Uso

### Ricerca per ID

```
# Pratiche
Cerca: "1234" → Trova pratica con ID=1234

# Fascicoli  
Cerca: "567" → Trova fascicolo con ID=567

# Documenti
Cerca: "890" → Trova documento con ID=890
```

### Ricerca Combinata

```
# Ricerca multipla (OR tra campi)
Cerca: "2024" → Trova:
  - ID contenente "2024"
  - Codici contenenti "2024"
  - Titoli/Descrizioni contenenti "2024"
  - Note contenenti "2024"
```

## 🧪 Test Consigliati

### Test Funzionali

1. **Test Ricerca ID**:
   ```
   - Cerca pratiche, fascicoli, documenti per ID esatto
   - Verifica risultati corretti
   - Verifica ricerca parziale ID (es. "123" trova "1234", "1235")
   ```

2. **Test Tempi di Risposta**:
   ```
   - Digita velocemente nella search box
   - Verifica che la ricerca parta dopo 300ms
   - Verifica annullamento ricerche precedenti (debounce)
   ```

3. **Test Lettore Barcode**:
   ```
   - Scansiona codice a barre/QR code
   - Verifica acquisizione completa prima della ricerca
   - Testa su tutti e tre i moduli
   ```

### Test Regressione

1. **Ricerca campi esistenti** (codice, titolo, note) continua a funzionare
2. **Filtri combinati** (ricerca + filtri dropdown) funzionano correttamente
3. **Paginazione** si resetta correttamente a pagina 1 su nuova ricerca

## 📝 Note Implementative

### Django REST Framework Search

Il campo `id` nei `search_fields` viene trattato come ricerca case-insensitive con `icontains`:

```python
# Django genera query tipo:
WHERE (
    id::text ILIKE '%<search_term>%' OR
    codice ILIKE '%<search_term>%' OR
    ...
)
```

**Nota**: PostgreSQL converte `id` a text per la ricerca parziale.

### Performance

- **Impatto minimo**: L'aggiunta di `id` ai search_fields ha overhead trascurabile
- **Index esistente**: `id` è sempre indicizzato (primary key)
- **Cast to text**: Operazione veloce in PostgreSQL

### Compatibilità

- **Backward compatible**: Nessuna breaking change
- **API**: Parametro `search` continua a funzionare come prima
- **Frontend**: Nessuna modifica UI necessaria

## 🚀 Deploy

### Checklist

- [x] Backend: Aggiornati search_fields in tutti i ViewSet
- [x] Frontend: Uniformati tempi debounce a 300ms
- [ ] Test: Verificare ricerca per ID su dev
- [ ] Test: Verificare tempi di risposta su dev
- [ ] Deploy: Push to production
- [ ] Monitoring: Verificare performance query search

### Comandi Deploy

```bash
# Backend - No migrations needed (solo codice Python)
git add api/v1/pratiche/views.py
git add api/v1/fascicoli/views.py
git add api/v1/documenti/views.py

# Frontend
git add frontend/src/pages/PraticheListPage.tsx
git add frontend/src/pages/FascicoliListPage.tsx

# Commit
git commit -m "feat: uniforma ricerca per ID e tempi debounce (300ms)

- Aggiungi 'id' ai search_fields di Pratiche, Fascicoli, Documenti
- Uniforma debounce a 300ms per tutte le list page
- Migliora UX con ricerca più veloce e uniforme"

# Deploy
./scripts/deploy.sh
```

## 📚 Documentazione Utente

### Come Cercare per ID

Gli utenti possono ora cercare oggetti direttamente inserendo l'ID numerico nella barra di ricerca:

1. **Pratiche**: Digita l'ID pratica (es. "1234")
2. **Fascicoli**: Digita l'ID fascicolo (es. "567")
3. **Documenti**: Digita l'ID documento (es. "890")

La ricerca funziona anche con ID parziali (es. "12" trova tutti gli ID che contengono "12").

### Miglioramento Velocità

La ricerca ora risponde più velocemente:
- **Prima**: 500ms di attesa prima della ricerca
- **Ora**: 300ms di attesa per tutte le sezioni
- **Risultato**: Ricerca 40% più reattiva

---

**Autore**: Sistema AI  
**Review**: Sandro Chimenti  
**Status**: ✅ Implementato  
**Version**: 1.0
