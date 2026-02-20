# 🔧 Troubleshooting - Autocomplete Codici Tributo F24

## Problema: L'autocomplete non appare nel form

### Checklist di Verifica

#### 1. ✅ Verifica che il Backend sia in esecuzione

```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py runserver
```

Dovresti vedere:
```
Starting development server at http://127.0.0.1:8000/
```

#### 2. ✅ Verifica che il Frontend sia in esecuzione

```bash
cd /home/sandro/mygest/frontend
npm run dev
```

Dovresti vedere:
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

#### 3. ✅ Verifica Template con campo codice_tributo

Esegui nel terminale:

```bash
python manage.py shell -c "
from comunicazioni.models_template import TemplateContextField

fields = TemplateContextField.objects.filter(field_type='codice_tributo')
print(f'Trovati {fields.count()} campi con tipo codice_tributo')

for field in fields:
    print(f'  Template: {field.template.nome}')
    print(f'    Campo: {field.key} - {field.label}')
"
```

**Output atteso:**
```
Trovati 3 campi con tipo codice_tributo
  Template: Scadenza F24
    Campo: primo_tributo_descrizione - primo tributo
  ...
```

Se non trovi campi, devi creare un template con campo `codice_tributo`.

#### 4. ✅ Verifica API Endpoint

```bash
python manage.py shell -c "
from comunicazioni.api.views import CodiceTributoF24ViewSet
from scadenze.models import CodiceTributoF24

count = CodiceTributoF24.objects.filter(attivo=True).count()
print(f'Codici tributo attivi: {count}')
"
```

**Output atteso:**
```
Codici tributo attivi: 39
```

#### 5. ✅ Verifica Autenticazione

L'API richiede autenticazione. Assicurati di essere loggato nel frontend.

**Test login:**
1. Vai su `http://localhost:5173/login`
2. Accedi con le tue credenziali
3. Vai su `/comunicazioni/new`
4. Seleziona un template con campo codice_tributo

#### 6. ✅ Console del Browser

Apri gli strumenti per sviluppatori (F12) e guarda la console.

**Log attesi:**
```
Field: primo_tributo_descrizione Type: codice_tributo Label: primo tributo
```

**Errori da cercare:**
- Errori 401 (autenticazione)
- Errori 404 (endpoint non trovato)
- Errori di import del componente
- Errori di rendering React

#### 7. ✅ Verifica Import del Componente

Nel file `ComunicazioneFormPage.tsx` dovrebbe esserci:

```typescript
import CodiceTributoAutocomplete from '@/components/comunicazioni/CodiceTributoAutocomplete';
```

#### 8. ✅ Verifica Rendering Condizionale

Nel form, cerca il codice:

```typescript
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

## Soluzioni ai Problemi Comuni

### Problema: "Module not found: CodiceTributoAutocomplete"

**Soluzione:**
```bash
cd /home/sandro/mygest/frontend
npm install
npm run dev
```

### Problema: "401 Unauthorized" in console

**Soluzione:**
1. Fai logout e rilogin
2. Verifica che il token JWT sia valido
3. Controlla che CORS sia configurato

### Problema: Il campo non appare per nessun template

**Causa:** Nessun template ha campi di tipo `codice_tributo`.

**Soluzione:** Crea un nuovo template via Django Admin:

1. Vai su **Django Admin** → **Comunicazioni** → **Template Comunicazione**
2. Clicca **Aggiungi Template**
3. Compila i dati base
4. Nella sezione **Context Fields**, aggiungi un campo:
   - Key: `codice_tributo`
   - Label: `Codice Tributo F24`
   - Field Type: **Codice Tributo F24**
   - Required: ✓
5. Salva

### Problema: Il dropdown non si apre quando digito

**Debug:**

1. Apri console browser (F12)
2. Digita nel campo
3. Guarda se ci sono chiamate API a `/api/v1/comunicazioni/codici-tributo/?search=...`
4. Verifica la risposta

**Causa comune:** Debounce di 300ms - devi digitare almeno 2 caratteri e aspettare 300ms.

### Problema: "No results" anche se digito correttamente

**Verifica database:**
```bash
python manage.py shell -c "
from scadenze.models import CodiceTributoF24

# Test search
query = 'ritenute'
results = CodiceTributoF24.objects.filter(
    descrizione__icontains=query,
    attivo=True
)
print(f'Risultati per \"{query}\": {results.count()}')
"
```

Se conta = 0, devi caricare i codici tributo:
```bash
python scripts/scraper_codici_tributo.py
python manage.py loaddata scripts/codici_tributo.json
```

## Test Manuale Completo

### 1. Avvia i server

**Terminale 1:**
```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py runserver
```

**Terminale 2:**
```bash
cd /home/sandro/mygest/frontend
npm run dev
```

### 2. Login

Vai su `http://localhost:5173/login` e accedi.

### 3. Crea Comunicazione

1. Vai su `http://localhost:5173/comunicazioni/new`
2. Seleziona Template: **Scadenza F24**
3. Dovresti vedere i campi:
   - `scadenza` (date)
   - `primo tributo` (autocomplete) ← **QUESTO**
   - `primo importo` (decimal)
   - `secondo tributo` (autocomplete) ← **QUESTO**
   - ...

### 4. Test Autocomplete

1. Clicca nel campo "primo tributo"
2. Digita "rite" (almeno 2 caratteri)
3. Aspetta 300ms
4. Dovrebbe apparire dropdown con risultati:
   ```
   1001 [ERARIO]
   Ritenute su redditi da lavoro dipendente e assimilati
   Causale: Ritenute lavoro dipendente
   ```

### 5. Seleziona un codice

1. Clicca su un risultato
2. Il campo si popola con: "1001 - Ritenute su redditi..."
3. Il dropdown si chiude
4. Il valore è salvato in `templateFields`

## Video Debug Step-by-Step

### Console Browser

1. Apri DevTools (F12)
2. Vai su tab **Console**
3. Dovresti vedere:
   ```
   Field: primo_tributo_descrizione Type: codice_tributo Label: primo tributo
   ```

4. Quando digiti nel campo, dovresti vedere:
   ```
   GET /api/v1/comunicazioni/codici-tributo/?search=rite&page_size=20
   ```

5. La risposta dovrebbe essere:
   ```json
   {
     "count": 8,
     "results": [
       {
         "id": 1,
         "codice": "1001",
         "display": "1001 - Ritenute su redditi da lavoro dipendente e assimilati",
         ...
       }
     ]
   }
   ```

### Network Tab

1. Vai su tab **Network**
2. Filtra per `codici-tributo`
3. Quando digiti, dovresti vedere richieste GET
4. Status code dovrebbe essere **200 OK**
5. Se vedi **401**, problema autenticazione
6. Se vedi **404**, problema routing

## File da Verificare

```bash
# Backend
ls -la comunicazioni/api/views.py
ls -la comunicazioni/api/serializers.py
ls -la comunicazioni/api/urls.py

# Frontend
ls -la frontend/src/components/comunicazioni/CodiceTributoAutocomplete.tsx
ls -la frontend/src/components/comunicazioni/CodiceTributoAutocomplete.css
ls -la frontend/src/api/comunicazioni.ts
ls -la frontend/src/types/comunicazioni.ts
```

Tutti i file devono esistere.

## Log Aggiunti per Debug

Nel file `ComunicazioneFormPage.tsx` è stato aggiunto un log:

```typescript
console.log('Field:', field.key, 'Type:', field.field_type, 'Label:', field.label);
```

Questo ti permette di vedere in console browser:
- Quali campi vengono renderizzati
- Quale è il `field_type` di ogni campo
- Se il tipo `codice_tributo` viene riconosciuto

## Prossimi Passi

Se dopo tutte queste verifiche il problema persiste:

1. **Condividi screenshot** della console browser
2. **Condividi screenshot** del form senza l'autocomplete
3. **Esegui** i comandi di verifica e condividi output
4. **Verifica** versioni:
   ```bash
   python --version  # Python 3.10+
   node --version    # Node 18+
   npm --version     # npm 9+
   ```

## Contatti

Per ulteriore supporto, condividi:
- Screenshot console browser con errori
- Output dei comandi di verifica
- Template che stai usando
- Versioni di Python/Node/npm
