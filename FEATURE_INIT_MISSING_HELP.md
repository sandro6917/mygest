# Feature: Inizializzazione Automatica Help Mancanti

## 📋 Panoramica

Implementata funzionalità per rilevare automaticamente i tipi documento senza help configurato e inizializzarli con:
- **Sezioni tecniche** auto-generate
- **Placeholder** per sezioni discorsive
- **Stato "da_completare"** per distinguerli
- **Visibilità solo admin** fino a completamento

---

## 🎯 Obiettivo

**Problema**: Tipi documento esistenti senza help → utenti non hanno documentazione

**Soluzione**: 
1. Comando automatico che rileva tipi senza help
2. Inizializza help con sezioni tecniche + placeholder
3. Marca come "da_completare" → visibile solo admin
4. Admin completa le sezioni discorsive
5. Rimuove flag "da_completare" → diventa pubblico

---

## 🔧 Componenti Implementati

### 1. Management Command `init_missing_help`

**File**: `documenti/management/commands/init_missing_help.py`

**Funzionalità**:
- Rileva tutti i tipi documento senza `help_data`
- Inizializza help con sezioni tecniche auto-generate
- Aggiunge placeholder per sezioni discorsive
- Imposta stato `da_completare` e flag `visibile_pubblico: false`

**Utilizzo**:
```bash
# Inizializza tutti i tipi senza help
python manage.py init_missing_help

# Dry-run (mostra cosa farebbe senza salvare)
python manage.py init_missing_help --dry-run

# Inizializza solo un tipo specifico
python manage.py init_missing_help --tipo FAT
```

**Output**:
```
======================================================================
  INIZIALIZZAZIONE HELP MANCANTI
======================================================================

Trovati 3 tipi senza help:
  - FAT: Fatture
  - CNT: Contratti
  - RIC: Ricevute

✓ FAT - Help inizializzato
✓ CNT - Help inizializzato
✓ RIC - Help inizializzato

======================================================================
  RIEPILOGO
======================================================================
✓ Inizializzati: 3
✗ Errori: 0

✓ Modifiche salvate nel database
```

### 2. Funzioni Helper Help Status

**File**: `documenti/help_builder.py`

#### `get_help_status(help_data) -> str`
Determina lo stato di completamento:
- `'vuoto'` - Nessun help_data
- `'da_completare'` - Help inizializzato automaticamente (flag _meta.stato)
- `'parziale'` - 40-80% sezioni completate
- `'completo'` - >= 80% sezioni completate

#### `is_help_complete(tipo_documento) -> bool`
Verifica se help è completo.

#### `is_help_visible_to_public(help_data) -> bool`
Determina visibilità pubblica:
- `False` se `_meta.visibile_pubblico = false`
- `False` se stato `da_completare`
- `True` se stato `completo` o `parziale`

**Esempio**:
```python
from documenti.models import DocumentiTipo
from documenti.help_builder import get_help_status, is_help_visible_to_public

tipo = DocumentiTipo.objects.get(codice='FAT')

status = get_help_status(tipo.help_data)
print(status)  # 'da_completare'

is_public = is_help_visible_to_public(tipo.help_data)
print(is_public)  # False
```

### 3. API Endpoints Estesi

**File**: `api/v1/documenti/views.py` - `DocumentiTipoViewSet`

#### Nuovi Endpoint:

**GET `/api/v1/documenti-tipo/with_help/`**
Lista tipi con help configurato, filtrata per permessi:
- **Admin**: Vedono tutti i tipi con help (anche `da_completare`)
- **Non-admin**: Vedono solo help pubblici (`completo` o `parziale`)

**Response**:
```json
{
  "count": 5,
  "is_admin": true,
  "results": [
    {
      "id": 1,
      "codice": "CED",
      "nome": "Cedolini",
      "help_status": "completo",
      "help_visibile_pubblico": true,
      "help_data": { ... }
    },
    {
      "id": 2,
      "codice": "FAT",
      "nome": "Fatture",
      "help_status": "da_completare",
      "help_visibile_pubblico": false,
      "help_data": { ... }  // Solo per admin
    }
  ]
}
```

**GET `/api/v1/documenti-tipo/missing_help/`** (Solo Admin)
Lista tipi senza help configurato.

**Response**:
```json
{
  "count": 2,
  "results": [
    {
      "id": 10,
      "codice": "ALT",
      "nome": "Altri",
      "help_status": "vuoto",
      "help_data": null
    }
  ]
}
```

### 4. Serializer Filtrato

**File**: `api/v1/documenti/serializers.py`

**Modifiche a `DocumentiTipoSerializer`**:

**Nuovi campi**:
- `help_status` (read-only)
- `help_visibile_pubblico` (read-only)

**Logica filtro**:
```python
def to_representation(self, instance):
    # Admin: help_data completo
    if is_admin:
        return data
    
    # Non-admin + help non pubblico:
    #   help_data sostituito con messaggio placeholder
    if not is_help_visible_to_public(instance.help_data):
        data['help_data'] = {
            '_meta': {
                'stato': 'non_disponibile',
                'messaggio': 'Help in fase di completamento. Disponibile solo per amministratori.'
            }
        }
    
    return data
```

### 5. Frontend Hook React

**File**: `frontend/src/hooks/useHelpVisibility.tsx`

**Hook `useHelpVisibility(tipo, isAdmin)`**:
```typescript
const { isVisible, status, message } = useHelpVisibility(tipo, isAdmin);

if (!isVisible) {
  return <Alert severity="info">{message}</Alert>;
}
```

**Hook `useFilteredTipiByHelpVisibility(tipi, isAdmin)`**:
```typescript
const tipiVisibili = useFilteredTipiByHelpVisibility(tipi, isAdmin);
// Admin: tutti i tipi
// Non-admin: solo tipi con help pubblico
```

**Component `<HelpStatusBadge />`**:
```tsx
<HelpStatusBadge status={tipo.help_status} isAdmin={isAdmin} />
// Mostra: ✓ Completo | ⚠ Parziale | ⏳ Da Completare | 🔒 Non Disponibile
```

### 6. TypeScript Types Aggiornati

**File**: `frontend/src/types/documento.ts`

```typescript
export interface DocumentiTipo {
  // ... campi esistenti
  help_status?: 'completo' | 'parziale' | 'da_completare' | 'vuoto' | 'non_disponibile';
  help_visibile_pubblico?: boolean;
}
```

---

## 📊 Struttura Help Inizializzato

Quando `init_missing_help` viene eseguito, crea questo help_data:

```json
{
  "_meta": {
    "stato": "da_completare",
    "data_creazione": "2026-02-11T15:30:00Z",
    "completato": false,
    "visibile_pubblico": false
  },
  
  "descrizione_breve": "Tipo documento Fatture - Help da completare",
  
  "quando_usare": {
    "casi_uso": ["Da definire"],
    "non_usare_per": ["Da definire"]
  },
  
  "attributi_dinamici": {
    "disponibili": [
      // Auto-generato da AttributoDefinizione
      {
        "codice": "numero_fattura",
        "nome": "Numero Fattura",
        "tipo": "CharField",
        "descrizione": "Numero progressivo della fattura",
        "obbligatorio": true,
        "esempio": "2026/001"
      }
    ],
    "pattern_code_examples": [ ... ]
  },
  
  "pattern_codice": {
    // Auto-generato da DocumentiTipo.pattern_codice
    "default": "{CLI}-FAT-{ANNO}-{SEQ:03d}",
    "spiegazione": "...",
    "esempi": [ ... ],
    "placeholder_disponibili": { ... }
  },
  
  "archiviazione": {
    // Auto-generato da nome_file_pattern + logica NAS
    "percorso_tipo": "/NAS/{CLI}/{TIT}/",
    "esempio": "/NAS/123456AB/FAT/",
    "nome_file_pattern": "{tipo.codice}_{attr:numero_fattura}.pdf",
    "esempio_completo": "/NAS/123456AB/FAT/FAT_2026_001.pdf",
    "note": [ ... ]
  },
  
  "campi_obbligatori": {
    // Auto-generato da AttributoDefinizione.required
    "sempre": [
      "Cliente",
      "Data documento",
      "Titolario",
      "Numero Fattura"
    ],
    "condizionali": { ... }
  },
  
  "workflow": {
    "stati_possibili": ["Bozza", "Protocollato", "Archiviato"],
    "stato_iniziale": "Bozza",
    "azioni_disponibili": [
      {
        "azione": "Protocolla",
        "quando": "Da bozza a protocollato",
        "effetto": "Assegna numero protocollo"
      }
    ]
  },
  
  "note_speciali": {
    "attenzioni": ["Help in fase di completamento"],
    "suggerimenti": ["Contatta l'amministratore per maggiori informazioni"],
    "vincoli_business": []
  },
  
  "faq": [
    {
      "domanda": "Quando sarà disponibile la guida completa?",
      "risposta": "La guida è in fase di completamento da parte degli amministratori."
    }
  ],
  
  "risorse_correlate": {
    "guide_correlate": [],
    "tipi_documento_correlati": [],
    "link_esterni": []
  }
}
```

**Nota**: Le sezioni `attributi_dinamici`, `pattern_codice`, `archiviazione`, `campi_obbligatori` sono **auto-generate** e corrette.

---

## 🔄 Workflow Completamento Help

### Fase 1: Inizializzazione (Automatica)
```bash
# Admin esegue comando
python manage.py init_missing_help

# Risultato:
# - help_data creato con sezioni tecniche corrette
# - Placeholder per sezioni discorsive
# - _meta.stato = "da_completare"
# - _meta.visibile_pubblico = false
```

### Fase 2: Completamento (Manuale Admin)
```
1. Admin accede a /admin/documenti/documentitipo/<ID>/change/

2. Compila sezioni discorsive:
   - Descrizione breve
   - Quando usare (casi + non usare)
   - Relazione fascicoli
   - Workflow (dettagli azioni)
   - Note speciali
   - FAQ

3. Salva → Sezioni tecniche rigenerate automaticamente

4. Help ora ha contenuto completo ma ancora _meta.stato = "da_completare"
```

### Fase 3: Pubblicazione (Manuale Admin)

**Opzione A: Via Admin UI** (futuro)
```
1. Admin clicca "Pubblica Help"
2. Sistema rimuove _meta.stato e imposta _meta.visibile_pubblico = true
3. Help diventa visibile a tutti gli utenti
```

**Opzione B: Via Django Shell** (attuale)
```python
from documenti.models import DocumentiTipo

tipo = DocumentiTipo.objects.get(codice='FAT')

# Rimuovi stato da_completare
meta = tipo.help_data.get('_meta', {})
meta['stato'] = 'completo'
meta['completato'] = True
meta['visibile_pubblico'] = True

tipo.help_data['_meta'] = meta
tipo.save()
```

**Opzione C: Via Wizard CLI**
```bash
python manage.py configure_help_wizard --tipo FAT --publish
# (da implementare)
```

### Fase 4: Verifica

**Frontend**:
```
1. Utente non-admin accede a /help/documenti
2. Vede tipo FAT nella lista
3. Click → Help completo visualizzato
```

**API**:
```bash
# Non-admin
curl -H "Authorization: Bearer <token>" \
  /api/v1/documenti-tipo/with_help/

# Response: tipo FAT incluso con help_visibile_pubblico = true
```

---

## 🧪 Testing

### Test Comando Init Missing Help

```bash
# 1. Test dry-run
python manage.py init_missing_help --dry-run

# Verifica output mostra tipi senza help
# Verifica messaggio "DRY-RUN: Nessuna modifica salvata"

# 2. Test inizializzazione reale
python manage.py init_missing_help

# Verifica output conferma inizializzazioni
# Verifica database:
python manage.py shell
```

```python
from documenti.models import DocumentiTipo
from documenti.help_builder import get_help_status

tipo = DocumentiTipo.objects.get(codice='FAT')

# Verifica help_data presente
assert tipo.help_data is not None
print(f"Sezioni: {list(tipo.help_data.keys())}")

# Verifica stato
status = get_help_status(tipo.help_data)
assert status == 'da_completare'
print(f"Status: {status}")

# Verifica meta
meta = tipo.help_data.get('_meta', {})
assert meta.get('stato') == 'da_completare'
assert meta.get('visibile_pubblico') == False
print(f"Meta: {meta}")

# Verifica sezioni tecniche auto-generate
assert 'attributi_dinamici' in tipo.help_data
assert 'pattern_codice' in tipo.help_data
assert 'archiviazione' in tipo.help_data
assert 'campi_obbligatori' in tipo.help_data
print("✓ Sezioni tecniche presenti")
```

### Test API Visibilità

**Test Admin**:
```bash
# Login admin
curl -X POST /api/v1/auth/login/ \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access'

export TOKEN="<access_token>"

# Lista tipi con help
curl -H "Authorization: Bearer $TOKEN" \
  /api/v1/documenti-tipo/with_help/ | jq

# Verifica:
# - count include tipi da_completare
# - is_admin = true
# - help_data completo anche per tipi da_completare
```

**Test Non-Admin**:
```bash
# Login utente normale
curl -X POST /api/v1/auth/login/ \
  -d '{"username":"user","password":"password"}' \
  | jq -r '.access'

export USER_TOKEN="<access_token>"

# Lista tipi con help
curl -H "Authorization: Bearer $USER_TOKEN" \
  /api/v1/documenti-tipo/with_help/ | jq

# Verifica:
# - count NON include tipi da_completare
# - is_admin = false
# - help_data filtrato per tipi da_completare

# Dettaglio tipo da_completare
curl -H "Authorization: Bearer $USER_TOKEN" \
  /api/v1/documenti-tipo/<ID>/ | jq

# Verifica help_data sostituito con:
# {
#   "_meta": {
#     "stato": "non_disponibile",
#     "messaggio": "Help in fase di completamento..."
#   }
# }
```

### Test Frontend React

```typescript
// Test hook useHelpVisibility
import { renderHook } from '@testing-library/react-hooks';
import { useHelpVisibility } from '@/hooks/useHelpVisibility';

const tipoCompleto = {
  id: 1,
  codice: 'CED',
  help_status: 'completo',
  help_visibile_pubblico: true,
  help_data: { ... }
};

const tipoDaCompletare = {
  id: 2,
  codice: 'FAT',
  help_status: 'da_completare',
  help_visibile_pubblico: false,
  help_data: { ... }
};

// Admin vede tutto
const { result: adminResult } = renderHook(() =>
  useHelpVisibility(tipoDaCompletare, true)
);
expect(adminResult.current.isVisible).toBe(true);
expect(adminResult.current.message).toContain('admin');

// Non-admin non vede help da_completare
const { result: userResult } = renderHook(() =>
  useHelpVisibility(tipoDaCompletare, false)
);
expect(userResult.current.isVisible).toBe(false);
expect(userResult.current.status).toBe('non_disponibile');
```

---

## 📝 Documentazione Utente

### Per Amministratori

**Comando: Inizializzare Help Mancanti**

1. Accedi al server via SSH
2. Attiva virtualenv: `source venv/bin/activate`
3. Esegui comando:
   ```bash
   python manage.py init_missing_help
   ```
4. Verifica output per conferma inizializzazioni
5. Accedi ad Admin Django per completare help

**Completamento Help**:

1. `/admin/documenti/documentitipo/`
2. Seleziona tipo con help da completare
3. Compila sezioni Help collassabili
4. Salva
5. Per pubblicare: via shell Django (temporaneo) o attendi feature "Pubblica"

### Per Utenti Finali

**Visualizzazione Help**:

- Accedi a `/help/documenti`
- Vedi solo tipi con help completo/parziale
- Tipi "da completare" visibili solo ad admin
- Se help non disponibile: messaggio informativo

---

## 🚀 Deploy

### Checklist Pre-Deploy

- [x] Comando `init_missing_help` creato
- [x] Funzioni helper status/visibilità
- [x] API endpoint filtrati
- [x] Serializer con filtro permessi
- [x] Frontend hook React
- [x] TypeScript types aggiornati
- [x] Documentazione completa

### Deploy Steps

```bash
# 1. Pull codice
git pull origin main

# 2. Collect static (se modifiche frontend)
python manage.py collectstatic --noinput

# 3. Restart services
sudo systemctl restart gunicorn

# 4. Esegui init_missing_help
source venv/bin/activate
python manage.py init_missing_help

# 5. Verifica log
tail -f /var/log/gunicorn/error.log
```

### Post-Deploy

1. **Verifica API**:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     https://tuodominio.com/api/v1/documenti-tipo/with_help/
   ```

2. **Verifica Frontend**:
   - Login admin → Verifica lista help include tipi "da_completare"
   - Login user → Verifica lista help NON include tipi "da_completare"

3. **Completa Help**:
   - Admin completa sezioni discorsive per tipi inizializzati
   - Pubblica help rimuovendo flag `da_completare`

---

## 🔮 Miglioramenti Futuri

### Prossime Implementazioni

1. **Pulsante "Pubblica Help" in Admin**
   - Action Django Admin
   - Rimuove `_meta.stato = da_completare`
   - Imposta `_meta.visibile_pubblico = true`

2. **Wizard Step Pubblicazione**
   ```bash
   python manage.py configure_help_wizard --tipo FAT --publish
   ```

3. **Notifiche Admin**
   - Email quando help inizializzato
   - Reminder help da completare
   - Conferma pubblicazione

4. **Dashboard Admin**
   - Statistiche help completati/da completare
   - Progress bar completamento
   - Lista priorità

5. **Feedback Utenti**
   - Pulsante "Richiedi Help" per tipo senza
   - Notifica admin della richiesta
   - Tracking richieste

---

**Versione**: 1.0  
**Data**: 11 Febbraio 2026  
**Status**: ✅ IMPLEMENTATO E TESTATO
