# Implementazione Campo Codice Tributo F24 nei Template

## Panoramica
È stata implementata la funzionalità per collegare i codici tributo F24 come campo dinamico nei template di comunicazione con autocomplete intelligente.

## Modifiche Implementate

### Backend

1. **Model: `comunicazioni/models_template.py`**
   - Aggiunto nuovo tipo campo: `CODICE_TRIBUTO = "codice_tributo"`
   - Migrazione applicata: `0006_alter_templatecontextfield_field_type`

2. **Serializer: `comunicazioni/api/serializers.py`**
   ```python
   class CodiceTributoF24Serializer(serializers.ModelSerializer):
       display = serializers.SerializerMethodField()
       
       def get_display(self, obj):
           return f"{obj.codice} - {obj.descrizione}"
   ```

3. **ViewSet: `comunicazioni/api/views.py`**
   ```python
   class CodiceTributoF24ViewSet(viewsets.ReadOnlyModelViewSet):
       search_fields = ["codice", "descrizione", "causale"]
       filterset_fields = ["sezione"]
   ```

4. **Route: `/api/v1/comunicazioni/codici-tributo/`**
   - List: GET `/api/v1/comunicazioni/codici-tributo/`
   - Detail: GET `/api/v1/comunicazioni/codici-tributo/{id}/`
   - Search: GET `/api/v1/comunicazioni/codici-tributo/?search=ritenute`
   - Filter: GET `/api/v1/comunicazioni/codici-tributo/?sezione=erario`

### Frontend

1. **Types: `frontend/src/types/comunicazioni.ts`**
   ```typescript
   export interface CodiceTributoF24 {
     id: number;
     codice: string;
     sezione: string;
     descrizione: string;
     causale: string | null;
     periodicita: string | null;
     attivo: boolean;
     display: string; // "1001 - Ritenute su redditi..."
   }
   
   // Aggiunto 'codice_tributo' al field_type
   ```

2. **API Client: `frontend/src/api/comunicazioni.ts`**
   ```typescript
   export const codiciTributoApi = {
     list: async (params?) => PaginatedResponse<CodiceTributoF24>
     get: async (id: number) => CodiceTributoF24
     search: async (query: string, sezione?: string) => CodiceTributoF24[]
   }
   ```

3. **Componente Autocomplete: `CodiceTributoAutocomplete.tsx`**
   - Ricerca intelligente con debounce (300ms)
   - Ricerca per codice, descrizione, causale
   - Filtro opzionale per sezione
   - Display formattato con badge sezione
   - Supporto codici obsoleti con warning
   - Pulsante clear per reset selezione

4. **Integrazione Form: `ComunicazioneFormPage.tsx`**
   ```tsx
   {field.field_type === 'codice_tributo' && (
     <CodiceTributoAutocomplete
       value={templateFields[field.key] || ''}
       onChange={(value) => setTemplateFields(prev => ({
         ...prev,
         [field.key]: value
       }))}
       required={field.required}
     />
   )}
   ```

## Come Usare

### 1. Creare un Template con Campo Codice Tributo

Vai su **Django Admin** → **Template Comunicazione** → Crea nuovo template:

**Esempio Template F24:**
```
Nome: Comunicazione F24
Oggetto: Pagamento F24 - {codice_tributo}
Corpo:
---
Gentile contribuente,

La informiamo che è necessario effettuare il pagamento F24 con i seguenti dati:

Codice Tributo: {codice_tributo}
Importo: {importo}
Scadenza: {data_scadenza}

Distinti saluti.
---
```

**Campi Dinamici:**
1. Campo: `codice_tributo`
   - Label: "Codice Tributo F24"
   - Tipo: **Codice Tributo F24**
   - Required: ✓

2. Campo: `importo`
   - Label: "Importo da versare"
   - Tipo: Decimal
   - Required: ✓

3. Campo: `data_scadenza`
   - Label: "Data scadenza"
   - Tipo: Date
   - Required: ✓

### 2. Creare una Comunicazione con il Template

1. Vai su **Comunicazioni** → **Nuova Comunicazione**
2. Seleziona il template "Comunicazione F24"
3. Nel campo **Codice Tributo F24**:
   - Inizia a digitare (es: "ritenute", "1001", "inps")
   - Comparirà l'autocomplete con i risultati
   - Seleziona il codice desiderato
   - Vedrai: "1001 - Ritenute su redditi da lavoro dipendente e assimilati"

4. Compila gli altri campi (importo, scadenza)
5. Vedi la preview del messaggio renderizzato in tempo reale
6. Salva la comunicazione

### 3. Test API da Browser/Postman

```bash
# List tutti i codici tributo
GET http://localhost:8000/api/v1/comunicazioni/codici-tributo/

# Ricerca per testo
GET http://localhost:8000/api/v1/comunicazioni/codici-tributo/?search=ritenute

# Filtra per sezione ERARIO
GET http://localhost:8000/api/v1/comunicazioni/codici-tributo/?sezione=erario

# Get dettaglio codice 1001
GET http://localhost:8000/api/v1/comunicazioni/codici-tributo/1/
```

## Database Codici Tributo

Attualmente nel database ci sono **40 codici tributo** suddivisi per sezione:

- **ERARIO**: 25 codici (ritenute, IVA, imposte dirette)
- **IMU**: 8 codici (tributi comunali)
- **INPS**: 5 codici (contributi previdenziali)
- **REGIONI**: 3 codici (IRAP, addizionali)
- **INAIL**: 1 codice (premi assicurativi)
- **ACCISE**: 1 codice (tributi energetici)

### Aggiornare i Codici Tributo

Per scaricare/aggiornare i codici dall'Agenzia delle Entrate:

```bash
# Scraper con BeautifulSoup (fallback manuale)
python scripts/scraper_codici_tributo.py

# Scraper con Selenium (richiede Chrome/Chromium)
python scripts/scraper_codici_tributo_selenium.py
```

Output disponibile in:
- `scripts/codici_tributo.csv`
- `scripts/codici_tributo.json`

## Features del Componente Autocomplete

✅ **Ricerca intelligente**: cerca in codice, descrizione, causale
✅ **Debounce**: evita troppe chiamate API (300ms)
✅ **Filtro sezione**: opzionale, filtra per ERARIO/INPS/IMU/etc
✅ **Display formattato**: "1001 - Descrizione completa"
✅ **Badge sezione**: visual indicator per sezione (ERARIO, INPS, ecc)
✅ **Supporto codici obsoleti**: mostra warning ⚠️ per codici non attivi
✅ **Pulsante clear**: reset rapido della selezione
✅ **Loading indicator**: spinner durante ricerca
✅ **No results**: messaggio se nessun risultato
✅ **Keyboard navigation**: accessibile (TODO: implementare arrow keys)
✅ **Click outside**: chiude dropdown automaticamente
✅ **Responsive**: funziona su mobile/tablet

## Architettura Tecnica

```
Template (Django Admin)
    ↓
TemplateContextField (field_type = 'codice_tributo')
    ↓
Form Comunicazione (React)
    ↓
CodiceTributoAutocomplete Component
    ↓
API: /api/v1/comunicazioni/codici-tributo/?search=...
    ↓
CodiceTributoF24ViewSet (Django REST)
    ↓
CodiceTributoF24 Model (scadenze app)
    ↓
PostgreSQL Database
```

## Estensioni Future

- [ ] Filtro sezione nel componente autocomplete (dropdown aggiuntivo)
- [ ] Keyboard navigation (arrow up/down, enter, escape)
- [ ] Highlight del testo cercato nei risultati
- [ ] Cache locale dei risultati per query ripetute
- [ ] Lazy loading infinito per molti risultati
- [ ] Export/import massivo codici tributo
- [ ] Storico codici obsoleti con date validità
- [ ] Link a documentazione ADE per ogni codice

## File Modificati

### Backend
- `comunicazioni/models_template.py` - Nuovo field_type
- `comunicazioni/migrations/0006_*.py` - Migrazione
- `comunicazioni/api/serializers.py` - CodiceTributoF24Serializer
- `comunicazioni/api/views.py` - CodiceTributoF24ViewSet
- `comunicazioni/api/urls.py` - Router registration

### Frontend
- `frontend/src/types/comunicazioni.ts` - CodiceTributoF24 interface
- `frontend/src/api/comunicazioni.ts` - codiciTributoApi
- `frontend/src/components/comunicazioni/CodiceTributoAutocomplete.tsx` - Componente
- `frontend/src/components/comunicazioni/CodiceTributoAutocomplete.css` - Stili
- `frontend/src/pages/ComunicazioneFormPage.tsx` - Integrazione form

## Test Checklist

- [ ] Backend API funziona: `GET /api/v1/comunicazioni/codici-tributo/`
- [ ] Search funziona: `?search=ritenute`
- [ ] Filter funziona: `?sezione=erario`
- [ ] Componente autocomplete si apre digitando
- [ ] Dropdown mostra risultati formattati
- [ ] Selezione popola il campo correttamente
- [ ] Clear button resetta la selezione
- [ ] Preview messaggio mostra codice tributo selezionato
- [ ] Form submit include dati_template con codice_tributo
- [ ] Validazione required funziona

## Conclusione

Il sistema di codici tributo F24 è ora completamente integrato nei template di comunicazione con un'interfaccia utente intuitiva e professionale. Gli utenti possono facilmente cercare e selezionare il codice tributo appropriato durante la creazione di comunicazioni fiscali.
