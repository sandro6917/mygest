# 📦 Bulk Creation - Voci Titolario Intestate

## Panoramica

La funzionalità di **Bulk Creation** consente di creare voci titolario intestate ad anagrafiche in modalità batch, con opzione di generare automaticamente anche sotto-voci standard (Buste Paga, Contratti, CU, Documenti Vari).

Sono disponibili **3 modalità** di creazione bulk:
1. **Admin Action** - Interfaccia Django Admin
2. **Management Command** - Terminale/script
3. **API Endpoint** - REST API

---

## 🎯 Casi d'Uso

### Scenario 1: Nuovo Cliente con molti dipendenti
Un nuovo cliente con 50 dipendenti richiede l'apertura di dossier personali per tutti.

**Soluzione**: Management command con flag `--crea-sottovoci`
```bash
python manage.py crea_voci_intestate HR-PERS --crea-sottovoci
```
Risultato: 50 dossier + 200 sotto-voci (4 per dossier) in pochi secondi.

### Scenario 2: Selezione dipendenti specifici
Il cliente richiede dossier solo per 5 dipendenti specifici.

**Soluzione**: Admin action con selezione manuale
1. Andare in Django Admin → Titolario → Voci Titolario
2. Selezionare voce `HR-PERS`
3. Action: "Crea voci intestate per anagrafiche selezionate"
4. **Selezionare** i 5 dipendenti specifici con checkbox
5. (Opzionale) Spuntare "Crea sotto-voci standard"
6. Click "Crea voci selezionate"
7. Risultato: 5 dossier creati (+ eventualmente 20 sotto-voci)

### Scenario 3: Integrazione con sistema esterno
Sistema esterno deve creare dossier via API per nuovi assunti.

**Soluzione**: API endpoint bulk
```bash
POST /api/v1/fascicoli/titolario-voci/{id}/crea_voci_bulk/
{
  "anagrafica_ids": [123, 456, 789],
  "crea_sottovoci": true
}
```

---

## 1️⃣ Admin Action

### Accesso
1. Django Admin → **Titolario** → **Voci Titolario**
2. Selezionare **UNA SOLA** voce con `consente_intestazione=True` (es. HR-PERS)
3. Action dropdown → **"Crea voci intestate per anagrafiche selezionate"**
4. Click "Go"

### Form di Selezione
Dopo aver cliccato "Go", si apre una **pagina intermedia** con:

- **Voce Parent**: Mostra codice e titolo della voce selezionata
- **Anagrafiche disponibili**: Conta totale anagrafiche non ancora intestate
- **Checkbox anagrafiche**: Lista con checkbox per ogni anagrafica disponibile
- **Selezione rapida**: Bottoni "Seleziona tutte" / "Deseleziona tutte"
- **Contatore**: Mostra numero anagrafiche selezionate in tempo reale
- **Crea sotto-voci**: Checkbox per creare automaticamente sotto-voci standard (BP, CONTR, CU, DOC)

### Comportamento
- ✅ **Selezione manuale**: L'utente sceglie quali anagrafiche intestare
- ✅ **Selezione multipla**: Checkbox per selezionare più anagrafiche
- ✅ **Sotto-voci opzionali**: Flag per creare sotto-voci standard
- ✅ Salta anagrafiche già esistenti (messaggi informativi)
- ✅ Pattern automatico: `{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}`
- ✅ Transazioni atomiche individuali (un errore non blocca le altre)
- ✅ Messaggi di feedback dettagliati:
  - Successo: "✓ Create X voci intestate con successo! (+ Y sotto-voci)"
  - Info: "ℹ️ X voci già esistenti (saltate)"
  - Errori: "✗ X errori durante la creazione"

### Codice chiave
File: `titolario/admin.py`

```python
class AnagraficheBulkSelectionForm(forms.Form):
    """Form per selezione anagrafiche nella bulk creation"""
    anagrafiche = forms.ModelMultipleChoiceField(
        queryset=Anagrafica.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    crea_sottovoci = forms.BooleanField(required=False, initial=False)

@admin.register(TitolarioVoce)
class TitolarioVoceAdmin(admin.ModelAdmin):
    actions = ["crea_voci_intestate_bulk"]
    
    def crea_voci_intestate_bulk(self, request, queryset):
        """Mostra form per selezionare anagrafiche"""
        # Filtra voci valide
        voci_valide = queryset.filter(consente_intestazione=True)
        
        # Solo 1 voce parent alla volta
        voce_parent = voci_valide.first()
        
        # GET: mostra form selezione
        if 'apply' not in request.POST:
            form = AnagraficheBulkSelectionForm(...)
            return render(request, 'admin/titolario/bulk_creation_form.html', {...})
        
        # POST: esegui creazione per anagrafiche selezionate
        form = AnagraficheBulkSelectionForm(request.POST, ...)
        if form.is_valid():
            for anagrafica in form.cleaned_data['anagrafiche']:
                # Crea voce + eventualmente sotto-voci
                # ...
```

Template: `templates/admin/titolario/bulk_creation_form.html`

### Limitazioni
- ⚠️ **Una sola voce parent alla volta** (se selezioni più voci, viene mostrato warning)
- ✅ Selezione manuale anagrafiche tramite checkbox
- ✅ Opzione sotto-voci configurabile

---

## 2️⃣ Management Command

### Sintassi
```bash
python manage.py crea_voci_intestate <VOCE_PARENT_CODICE> [opzioni]
```

### Parametri

#### Posizionale (obbligatorio)
- `voce_parent_codice`: Codice della voce parent (es. `HR-PERS`)

#### Opzioni
- `--anagrafiche <CODICE1> <CODICE2> ...`: Codici anagrafiche specifiche (default: tutte disponibili)
- `--dry-run`: Modalità simulazione senza salvare nel database
- `--crea-sottovoci`: Crea anche sotto-voci standard (BP, CONTR, CU, DOC)

### Esempi

#### 1. Dry-run per tutte le disponibili
```bash
python manage.py crea_voci_intestate HR-PERS --dry-run
```
Output:
```
📋 Voce parent: HR-PERS - Dossier personale
👥 Anagrafiche da processare: 96
🔍 MODALITÀ DRY-RUN (nessuna modifica sarà salvata)

  ✓ ROSMAR01 - Dossier Rossi Mario
  ✓ BIAGIO01 - Dossier Bianchi Giovanni
  ...
────────────────────────────────────────────────────────────
✓ Voci create: 96
```

#### 2. Creazione reale per anagrafiche specifiche
```bash
python manage.py crea_voci_intestate HR-PERS \
  --anagrafiche ROSMAR01 BIAGIO01 VERDLU01
```

#### 3. Creazione con sotto-voci per tutte le disponibili
```bash
python manage.py crea_voci_intestate HR-PERS --crea-sottovoci
```
Output:
```
  ✓ ROSMAR01 - Dossier Rossi Mario
      ↳ BP - Buste Paga
      ↳ CONTR - Contratti
      ↳ CU - Certificazione Unica
      ↳ DOC - Documenti Vari
  ✓ BIAGIO01 - Dossier Bianchi Giovanni
      ↳ BP - Buste Paga
      ↳ CONTR - Contratti
      ↳ CU - Certificazione Unica
      ↳ DOC - Documenti Vari
────────────────────────────────────────────────────────────
✓ Voci create: 2
✓ Sotto-voci create: 8
```

#### 4. Test completo con dry-run
```bash
python manage.py crea_voci_intestate HR-PERS \
  --anagrafiche ROSMAR01 BIAGIO01 \
  --crea-sottovoci \
  --dry-run
```

### Template Sotto-Voci Standard

Quando si usa `--crea-sottovoci`, vengono create automaticamente:

| Codice | Titolo                | Pattern                           |
|--------|-----------------------|-----------------------------------|
| BP     | Buste Paga            | {CLI}-{ANA}-BP-{ANNO}-{SEQ:03d}   |
| CONTR  | Contratti             | {CLI}-{ANA}-CONTR-{ANNO}-{SEQ:03d}|
| CU     | Certificazione Unica  | {CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}   |
| DOC    | Documenti Vari        | {CLI}-{ANA}-DOC-{ANNO}-{SEQ:03d}  |

### Output e Feedback

Il comando fornisce feedback dettagliato con emoji e colori:

- ✅ **Verde**: Successo
- ⚠️ **Giallo**: Warning (già esistente, anagrafiche non trovate)
- ❌ **Rosso**: Errori
- ℹ️ **Blu**: Informazioni

### Codice chiave
File: `titolario/management/commands/crea_voci_intestate.py`

```python
class Command(BaseCommand):
    help = 'Crea voci titolario intestate ad anagrafiche in modalità bulk'
    
    def add_arguments(self, parser):
        parser.add_argument('voce_parent_codice', type=str)
        parser.add_argument('--anagrafiche', nargs='+', type=str)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--crea-sottovoci', action='store_true')
```

---

## 3️⃣ API Endpoint

### Endpoint
```
POST /api/v1/fascicoli/titolario-voci/{id}/crea_voci_bulk/
```

### Autenticazione
Richiesta autenticazione JWT:
```
Authorization: Bearer <access_token>
```

### Request Body

```json
{
  "anagrafica_ids": [123, 456, 789],      // Opzionale: IDs specifici
  "tutte_disponibili": true,              // Opzionale: tutte disponibili
  "crea_sottovoci": true,                 // Opzionale: crea sotto-voci
  "pattern_codice": "{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}",  // Opzionale
  "dry_run": false                        // Opzionale: simulazione
}
```

#### Parametri

| Campo              | Tipo         | Default | Descrizione                                      |
|--------------------|--------------|---------|--------------------------------------------------|
| anagrafica_ids     | number[]     | -       | Lista IDs anagrafiche specifiche                 |
| tutte_disponibili  | boolean      | false   | Crea per tutte le anagrafiche disponibili        |
| crea_sottovoci     | boolean      | false   | Crea anche sotto-voci standard (BP, CONTR, etc.) |
| pattern_codice     | string       | {CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d} | Pattern codice documenti |
| dry_run            | boolean      | false   | Modalità simulazione (non salva)                 |

**Nota**: Specificare **uno** tra `anagrafica_ids` o `tutte_disponibili=true`.

### Response (Success)

**Status**: 200 OK / 201 Created

```json
{
  "voci_create": 3,
  "sottovoci_create": 12,
  "gia_esistenti": 1,
  "errori": [],
  "voci": [
    {
      "id": 134,
      "codice": "ROSMAR01",
      "titolo": "Dossier Rossi Mario",
      "anagrafica_id": 45,
      "anagrafica_nome": "Rossi Mario"
    },
    {
      "id": 135,
      "codice": "BIAGIO01",
      "titolo": "Dossier Bianchi Giovanni",
      "anagrafica_id": 67,
      "anagrafica_nome": "Bianchi Giovanni"
    }
  ],
  "dry_run": false
}
```

### Response (Dry-run)

```json
{
  "voci_create": 3,
  "sottovoci_create": 12,
  "gia_esistenti": 1,
  "errori": [],
  "voci": [],  // Vuoto in dry-run
  "dry_run": true,
  "message": "Dry-run completato: nessuna modifica salvata"
}
```

### Response (Errore)

**Status**: 400 Bad Request

```json
{
  "error": "Questa voce non consente intestazione ad anagrafiche"
}
```

```json
{
  "error": "Specificare anagrafica_ids o tutte_disponibili=true"
}
```

### Esempi cURL

#### 1. Dry-run con 3 anagrafiche + sotto-voci
```bash
curl -X POST http://localhost:8000/api/v1/fascicoli/titolario-voci/20/crea_voci_bulk/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "anagrafica_ids": [123, 456, 789],
    "crea_sottovoci": true,
    "dry_run": true
  }'
```

#### 2. Creazione reale per tutte le disponibili
```bash
curl -X POST http://localhost:8000/api/v1/fascicoli/titolario-voci/20/crea_voci_bulk/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tutte_disponibili": true,
    "crea_sottovoci": false,
    "dry_run": false
  }'
```

### Esempi Python (requests)

```python
import requests

# Login e ottieni token
response = requests.post('http://localhost:8000/api/v1/auth/login/', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access']

# Bulk creation
response = requests.post(
    'http://localhost:8000/api/v1/fascicoli/titolario-voci/20/crea_voci_bulk/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'anagrafica_ids': [123, 456, 789],
        'crea_sottovoci': True,
        'dry_run': False
    }
)

result = response.json()
print(f"Voci create: {result['voci_create']}")
print(f"Sotto-voci create: {result['sottovoci_create']}")
```

### Esempi JavaScript (fetch)

```javascript
// Login
const loginResponse = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});
const { access } = await loginResponse.json();

// Bulk creation
const response = await fetch('/api/v1/fascicoli/titolario-voci/20/crea_voci_bulk/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    anagrafica_ids: [123, 456, 789],
    crea_sottovoci: true,
    dry_run: false
  })
});

const result = await response.json();
console.log(`Voci create: ${result.voci_create}`);
console.log(`Sotto-voci create: ${result.sottovoci_create}`);
```

### Codice chiave
File: `api/v1/fascicoli/views.py`

```python
class TitolarioVoceViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def crea_voci_bulk(self, request, pk=None):
        """Crea voci intestate in modalità bulk"""
        parent_voce = self.get_object()
        
        # Validazioni...
        
        # Determina anagrafiche da processare
        if tutte_disponibili:
            anagrafiche = parent_voce.get_anagrafiche_disponibili()
        elif anagrafica_ids:
            anagrafiche = Anagrafica.objects.filter(id__in=anagrafica_ids)
        
        # Creazione bulk con transazione atomica
        with transaction.atomic():
            for anagrafica in anagrafiche:
                # Crea voce + sotto-voci
                # ...
            
            if dry_run:
                transaction.set_rollback(True)
        
        return Response({...})
```

---

## 📊 Confronto Modalità

| Feature                    | Admin Action | Management Command | API Endpoint |
|----------------------------|--------------|-------------------|--------------|
| Selezione anagrafiche      | ✅ Manuale   | ✅ Specifiche     | ✅ Specifiche |
| Dry-run                    | ❌           | ✅                | ✅           |
| Sotto-voci standard        | ✅ Opzionale | ✅                | ✅           |
| Pattern personalizzato     | ❌           | ❌                | ✅           |
| Feedback visivo            | ✅ Form+Msg  | ✅ Colorato       | ✅ JSON      |
| Automazione/Script         | ❌           | ✅                | ✅           |
| Integrazione esterna       | ❌           | ⚠️ Limitata      | ✅           |
| Richiede autenticazione    | ✅ Django    | ✅ Sistema        | ✅ JWT       |
| Selezione multipla voci    | ❌ Solo 1    | ✅                | ✅           |

**Legenda**:
- ✅ = Supportato completamente
- ⚠️ = Supporto parziale
- ❌ = Non supportato

---

## 🧪 Test

### Test Completo
File: `test_bulk_shell.py`

```bash
python manage.py shell < test_bulk_shell.py
```

Output atteso:
```
======================================================================
TEST BULK CREATION - Voci Titolario Intestate
======================================================================

📊 STATO INIZIALE
----------------------------------------------------------------------
✓ Voce parent: HR-PERS - Dossier personale
  Consente intestazione: True
  Voci intestate esistenti: 3
  Anagrafiche disponibili: 96

🌐 TEST API ENDPOINT BULK
----------------------------------------------------------------------

1️⃣ DRY-RUN con 5 anagrafiche + sotto-voci
   Status: 201
   ✓ Voci da creare: 5
   ✓ Sotto-voci da creare: 20
   ✓ Già esistenti: 0
   ✓ Errori: 0

2️⃣ CREAZIONE REALE di 1 voce + sotto-voci
   Anagrafica test: Beibak Iryna
   Status: 201
   ✓ Voci create: 1
   ✓ Sotto-voci create: 4

   📄 Dettagli voce creata:
      ID: 137
      Codice: BEIIRY01
      Titolo: Dossier Beibak Iryna

   📁 Sotto-voci (4):
      - BP: Buste Paga [{CLI}-{ANA}-BP-{ANNO}-{SEQ:03d}]
      - CONTR: Contratti [{CLI}-{ANA}-CONTR-{ANNO}-{SEQ:03d}]
      - CU: Certificazione Unica [{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}]
      - DOC: Documenti Vari [{CLI}-{ANA}-DOC-{ANNO}-{SEQ:03d}]

3️⃣ BULK TUTTE LE DISPONIBILI (dry-run)
   Status: 201
   ✓ Voci da creare: 95
   ✓ Già esistenti: 1

📊 STATISTICHE FINALI
----------------------------------------------------------------------
✓ Totale voci intestate: 4
✓ Totale sotto-voci: 5
✓ Anagrafiche ancora disponibili: 95

======================================================================
✅ TEST COMPLETATO
======================================================================
```

### Test Unitari
```bash
pytest titolario/tests_voci_intestate.py -v
```

---

## 🔐 Validazioni e Business Rules

### Pre-validazioni (tutte le modalità)

1. **Voce parent deve esistere**
   - Admin: Selezione da lista esistente
   - Command: `CommandError` se codice non trovato
   - API: `404 Not Found`

2. **Voce parent deve consentire intestazione**
   - `consente_intestazione=True` obbligatorio
   - Admin: Filtra automaticamente voci non valide
   - Command: `CommandError`
   - API: `400 Bad Request`

3. **Anagrafiche devono avere codice valido**
   - Filtro automatico: `exclude(codice__isnull=True).exclude(codice='')`
   - Anagrafiche senza codice vengono saltate silenziosamente

### Durante creazione

4. **Unicità (parent, anagrafica)**
   - Constraint DB: `uniq_titolario_parent_anagrafica`
   - Comportamento:
     - Admin: Conta come "già esistente", continua
     - Command: Conta come "già esistente", continua
     - API: Conta come "già esistente", continua

5. **Unicità (parent, codice)**
   - Constraint DB: `uniq_titolario_codice_per_parent`
   - Se anagrafica.codice già usato sotto parent → errore
   - Comportamento: errore registrato, continua con prossima anagrafica

6. **Creazione sotto-voci**
   - Solo se voce parent creata con successo
   - Errori sotto-voci non bloccano creazione voce parent
   - Errori registrati in array `errori`

---

## 🎯 Best Practices

### 1. Usa sempre dry-run prima di operazioni massive
```bash
# Prima simula
python manage.py crea_voci_intestate HR-PERS --crea-sottovoci --dry-run

# Poi esegui
python manage.py crea_voci_intestate HR-PERS --crea-sottovoci
```

### 2. Management command per operazioni pianificate
```bash
#!/bin/bash
# Script cron per nuovi assunti settimanali
python manage.py crea_voci_intestate HR-PERS \
  --anagrafiche $(cat new_hires_this_week.txt) \
  --crea-sottovoci
```

### 3. API endpoint per integrazioni real-time
```javascript
// Dopo inserimento nuovo dipendente
async function onNewEmployee(employeeId) {
  const response = await fetch(`/api/v1/fascicoli/titolario-voci/20/crea_voci_bulk/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      anagrafica_ids: [employeeId],
      crea_sottovoci: true
    })
  });
  
  if (response.ok) {
    const result = await response.json();
    console.log(`Dossier creato per dipendente ${employeeId}`);
  }
}
```

### 4. Admin action per operazioni estemporanee
- Utile per utenti non tecnici
- Ideale per creazioni spot (es. "crea dossier per nuovi 5 dipendenti")

---

## 🐛 Troubleshooting

### Problema: "Voce non consente intestazione"
**Causa**: La voce parent ha `consente_intestazione=False`

**Soluzione**:
```python
from titolario.models import TitolarioVoce
voce = TitolarioVoce.objects.get(codice='HR-PERS')
voce.consente_intestazione = True
voce.save()
```

### Problema: "Nessuna anagrafica disponibile"
**Causa**: Tutte le anagrafiche hanno già voci intestate o non hanno codice

**Verifica**:
```python
from titolario.models import TitolarioVoce
voce = TitolarioVoce.objects.get(codice='HR-PERS')
disponibili = voce.get_anagrafiche_disponibili()
print(f"Disponibili: {disponibili.count()}")
```

### Problema: "duplicate key violates unique constraint"
**Causa**: Anagrafica già ha voce intestata sotto quella parent

**Soluzione**: Normale, viene gestito automaticamente come "già esistente"

### Problema: API restituisce 404
**Causa**: URL errato

**Verifica URL corretto**:
```
/api/v1/fascicoli/titolario-voci/{id}/crea_voci_bulk/
```
Non: `/api/v1/titolario/{id}/crea_voci_bulk/`

---

## 📈 Performance

### Benchmark (PostgreSQL, server locale)

| Operazione                        | N. Voci | Tempo     | Voci/sec |
|-----------------------------------|---------|-----------|----------|
| Admin action (solo voci)          | 100     | ~3s       | 33       |
| Management command (solo voci)    | 100     | ~2.5s     | 40       |
| Management command (+sottovoci)   | 100     | ~8s       | 12.5*    |
| API endpoint (solo voci)          | 100     | ~3s       | 33       |
| API endpoint (+sottovoci)         | 100     | ~9s       | 11*      |

\* Include 400 sotto-voci totali (4 per voce)

### Ottimizzazioni

1. **Bulk create per sotto-voci** (TODO future enhancement):
```python
# Invece di:
for sv in sotto_voci:
    TitolarioVoce.objects.create(...)

# Usare:
TitolarioVoce.objects.bulk_create([
    TitolarioVoce(...) for sv in sotto_voci
])
```
Migliora performance del 60-70% per creazioni massive.

2. **Prefetch anagrafiche disponibili**:
Già implementato in `get_anagrafiche_disponibili()` con query ottimizzate.

---

## 🔄 Roadmap Future

### Possibili miglioramenti

1. **Template personalizzati sotto-voci**
   - Consentire template JSON personalizzati invece di hardcoded
   - Es: `--template-sottovoci custom_hr_template.json`

2. **Bulk update**
   - Modificare in batch pattern_codice o altri campi

3. **Importazione CSV**
   - Import da CSV per creazione massive da sistemi esterni

4. **Frontend React**
   - Interfaccia grafica per bulk creation con preview

5. **Task asincrono (Celery)**
   - Per operazioni massive (1000+ voci) eseguire in background

6. **Notifiche email**
   - Inviare report al completamento operazioni bulk

---

## 📚 Riferimenti

### File modificati

- `titolario/admin.py` - Admin action
- `titolario/management/commands/crea_voci_intestate.py` - Management command
- `api/v1/fascicoli/views.py` - API endpoint `crea_voci_bulk()`
- `test_bulk_shell.py` - Test completo

### Documentazione correlata

- [FEATURE_TITOLARIO_VOCI_INTESTATE.md](./FEATURE_TITOLARIO_VOCI_INTESTATE.md) - Feature principale voci intestate
- [DOCUMENTAZIONE_COMPLETA_TITOLARIO.md](./DOCUMENTAZIONE_COMPLETA_TITOLARIO.md) - Documentazione completa Titolario

---

**Versione**: 1.0  
**Data**: 21 Gennaio 2025  
**Autore**: Sandro Chimenti
