# Feature: Logica Gestione Anagrafiche Esistenti - Importazione UNILAV

## 📋 Overview

La funzionalità di importazione UNILAV implementa una **logica intelligente di gestione anagrafiche esistenti** che:

1. ✅ **Controlla se le anagrafiche esistono già** (per codice fiscale)
2. ✅ **Riutilizza le anagrafiche esistenti SENZA modificarle**
3. ✅ **Mostra all'utente quali anagrafiche verranno create/riutilizzate**
4. ✅ **Permette di visualizzare le anagrafiche esistenti prima della conferma**

## 🔍 Logica Backend

### Step 1: Preview (Controllo Esistenza)

Endpoint: `POST /api/v1/documenti/importa_unilav_preview/`

```python
# Per il DATORE DI LAVORO
try:
    anagrafica_datore = Anagrafica.objects.get(
        codice_fiscale=cf_datore
    )
    datore_response['esiste'] = True
    datore_response['anagrafica_id'] = anagrafica_datore.id
    
    # Verifica se è già cliente
    try:
        cliente = Cliente.objects.get(anagrafica=anagrafica_datore)
        datore_response['cliente_id'] = cliente.id
    except Cliente.DoesNotExist:
        datore_response['cliente_id'] = None
        
except Anagrafica.DoesNotExist:
    datore_response['esiste'] = False
    datore_response['anagrafica_id'] = None
    datore_response['cliente_id'] = None

# Per il LAVORATORE (stessa logica)
try:
    anagrafica_lavoratore = Anagrafica.objects.get(
        codice_fiscale=cf_lavoratore
    )
    lavoratore_response['esiste'] = True
    lavoratore_response['anagrafica_id'] = anagrafica_lavoratore.id
except Anagrafica.DoesNotExist:
    lavoratore_response['esiste'] = False
    lavoratore_response['anagrafica_id'] = None
```

**Response Structure:**
```json
{
  "datore": {
    "codice_fiscale": "SLMRME65H01H501A",
    "tipo": "PF",
    "cognome": "SALIMBENI",
    "nome": "REMO",
    "esiste": true,              // ← Indica se anagrafica esiste
    "anagrafica_id": 123,        // ← ID anagrafica esistente
    "cliente_id": 456,           // ← ID cliente (se esiste)
    "crea_se_non_esiste": true,
    "crea_cliente": true
  },
  "lavoratore": {
    "codice_fiscale": "CNSLSI95E50H501X",
    "tipo": "PF",
    "cognome": "CONSORTI",
    "nome": "LISA",
    "esiste": false,             // ← Anagrafica non esiste
    "anagrafica_id": null,
    "crea_se_non_esiste": true
  },
  "documento": { ... },
  "file_temp_path": "/tmp/unilav_xxx.pdf"
}
```

### Step 2: Confirm (Creazione/Riutilizzo)

Endpoint: `POST /api/v1/documenti/importa_unilav_confirm/`

```python
with transaction.atomic():
    # 1. DATORE DI LAVORO
    # REGOLA: Se esiste → RIUTILIZZA senza modifiche
    #         Se non esiste → CREA nuova
    
    try:
        # Cerca anagrafica esistente
        anagrafica_datore = Anagrafica.objects.get(
            codice_fiscale=datore_data['codice_fiscale']
        )
        # ✅ TROVATA: viene riutilizzata così com'è
        # ❌ NON vengono sovrascritti i dati esistenti
        
    except Anagrafica.DoesNotExist:
        # Anagrafica non esiste
        if datore_data.get('crea_se_non_esiste', True):
            # ✅ CREA nuova anagrafica
            anagrafica_datore = Anagrafica.objects.create(
                codice_fiscale=datore_data['codice_fiscale'],
                tipo=datore_data['tipo'],
                ragione_sociale=datore_data.get('ragione_sociale', ''),
                cognome=datore_data.get('cognome', ''),
                nome=datore_data.get('nome', ''),
            )
        else:
            # ❌ Creazione disabilitata → errore
            raise ValueError("Anagrafica datore non trovata e creazione disabilitata")
    
    # 2. LAVORATORE (stessa logica)
    try:
        anagrafica_lavoratore = Anagrafica.objects.get(
            codice_fiscale=lavoratore_data['codice_fiscale']
        )
        # ✅ TROVATA: riutilizzata
        
    except Anagrafica.DoesNotExist:
        if lavoratore_data.get('crea_se_non_esiste', True):
            # ✅ CREA nuova
            anagrafica_lavoratore = Anagrafica.objects.create(...)
        else:
            raise ValueError("Anagrafica lavoratore non trovata e creazione disabilitata")
    
    # 3. CLIENTE (solo per datore)
    if datore_data.get('crea_cliente', True):
        # get_or_create: se esiste usa quello, altrimenti crea
        cliente_datore, created = Cliente.objects.get_or_create(
            anagrafica=anagrafica_datore
        )
    
    # 4. DOCUMENTO UNILAV
    documento = Documento.objects.create(
        tipo=tipo_unilav,
        cliente=cliente_datore,  # Usa cliente esistente o appena creato
        descrizione=f"UNILAV {codice_comunicazione} - {anagrafica_lavoratore.denominazione}",
        data_documento=documento_data['data_comunicazione'],
        digitale=True,
        tracciabile=True,
        stato='definitivo',
    )
```

## 🎨 UI/UX Frontend

### Alert Informativi

#### Anagrafica Esistente
```tsx
{editedData.datore.esiste && editedData.datore.anagrafica_id && (
  <Alert 
    severity="info" 
    sx={{ mb: 2 }}
    action={
      <Button
        color="inherit"
        size="small"
        onClick={() => window.open(`/anagrafiche/${editedData.datore.anagrafica_id}`, '_blank')}
      >
        Visualizza
      </Button>
    }
  >
    <strong>Anagrafica esistente trovata</strong> (ID: {editedData.datore.anagrafica_id})
    <br />
    L'anagrafica con questo codice fiscale esiste già. Verrà utilizzata quella esistente senza modifiche.
    {editedData.datore.cliente_id && (
      <> È già un cliente (ID: {editedData.datore.cliente_id}).</>
    )}
  </Alert>
)}
```

**Screenshot concettuale:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ℹ️ Anagrafica esistente trovata (ID: 123)                       │
│                                                                  │
│ L'anagrafica con questo codice fiscale esiste già. Verrà        │
│ utilizzata quella esistente senza modifiche.                    │
│ È già un cliente (ID: 456).                      [Visualizza]   │
└─────────────────────────────────────────────────────────────────┘
```

#### Nuova Anagrafica
```tsx
{!editedData.datore.esiste && (
  <Alert severity="warning" sx={{ mb: 2 }}>
    <strong>Nuova anagrafica</strong>
    <br />
    Questa anagrafica non esiste. Verrà creata una nuova anagrafica e un nuovo cliente.
  </Alert>
)}
```

**Screenshot concettuale:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ Nuova anagrafica                                             │
│                                                                  │
│ Questa anagrafica non esiste. Verrà creata una nuova anagrafica │
│ e un nuovo cliente.                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Scenari d'Uso

### Scenario 1: Entrambe le anagrafiche esistono

**Situazione:**
- Datore: SALIMBENI REMO (CF: SLMRME65H01H501A) → **Esiste**
- Lavoratore: CONSORTI LISA (CF: CNSLSI95E50H501X) → **Esiste**

**Comportamento:**
1. Preview mostra entrambi come "esistenti"
2. UI mostra alert blu per entrambi con pulsanti "Visualizza"
3. Conferma: riutilizza entrambe le anagrafiche senza modifiche
4. Crea solo il documento UNILAV collegato

**Database:**
- ✅ 0 nuove anagrafiche
- ✅ 0 nuovi clienti (se datore è già cliente)
- ✅ 1 nuovo documento UNILAV

### Scenario 2: Datore esiste, lavoratore no

**Situazione:**
- Datore: SALIMBENI REMO → **Esiste**
- Lavoratore: ROSSI MARIO (nuovo) → **Non esiste**

**Comportamento:**
1. Preview mostra datore "esistente", lavoratore "nuovo"
2. UI: alert blu per datore, alert arancione per lavoratore
3. Conferma:
   - Riutilizza anagrafica datore
   - Crea nuova anagrafica lavoratore

**Database:**
- ✅ 1 nuova anagrafica (lavoratore)
- ✅ 0 nuovi clienti datore (se già cliente)
- ✅ 1 nuovo documento UNILAV

### Scenario 3: Nessuna anagrafica esiste

**Situazione:**
- Datore: Nuova azienda → **Non esiste**
- Lavoratore: Nuovo dipendente → **Non esiste**

**Comportamento:**
1. Preview mostra entrambi come "nuovi"
2. UI: alert arancione per entrambi
3. Conferma:
   - Crea nuova anagrafica datore
   - Crea nuovo cliente datore
   - Crea nuova anagrafica lavoratore

**Database:**
- ✅ 2 nuove anagrafiche
- ✅ 1 nuovo cliente (datore)
- ✅ 1 nuovo documento UNILAV

### Scenario 4: Datore esiste ma non è cliente

**Situazione:**
- Datore: SALIMBENI REMO → **Esiste** (anagrafica_id=123)
- Cliente SALIMBENI REMO → **Non esiste**

**Comportamento:**
1. Preview:
   ```json
   {
     "esiste": true,
     "anagrafica_id": 123,
     "cliente_id": null,  // ← Non è cliente
     "crea_cliente": true
   }
   ```
2. UI mostra: "Anagrafica esistente (ID: 123)" ma senza "È già un cliente"
3. Conferma:
   - Riutilizza anagrafica esistente
   - **Crea nuovo cliente** collegato all'anagrafica

**Database:**
- ✅ 0 nuove anagrafiche
- ✅ 1 nuovo cliente (collegato ad anagrafica esistente)
- ✅ 1 nuovo documento UNILAV

## 🔐 Protezioni Implementate

### 1. Non Modifica Dati Esistenti
```python
# ❌ SBAGLIATO (sovrascrive dati)
anagrafica.ragione_sociale = datore_data['ragione_sociale']
anagrafica.save()

# ✅ CORRETTO (riutilizza senza modifiche)
try:
    anagrafica = Anagrafica.objects.get(codice_fiscale=cf)
    # Usata così com'è, nessun .save()
except Anagrafica.DoesNotExist:
    anagrafica = Anagrafica.objects.create(...)
```

### 2. Transazione Atomica
```python
with transaction.atomic():
    # Tutto-o-niente
    # Se qualcosa fallisce, rollback completo
    anagrafica_datore = ...
    cliente_datore = ...
    anagrafica_lavoratore = ...
    documento = ...
```

### 3. Validazione Codice Fiscale
- **PF**: 16 caratteri alfanumerici + checksum
- **PG**: 11 cifre numeriche (P.IVA) + checksum
- Validazione in `Anagrafica.clean()` prima di salvare

### 4. Flag Controllo Creazione
```python
# Permette di disabilitare la creazione se necessario
if datore_data.get('crea_se_non_esiste', True):
    # Crea solo se esplicitamente richiesto
```

## 🧪 Test Cases

### Test 1: Anagrafica esistente non viene modificata
```python
@pytest.mark.django_db
def test_anagrafica_esistente_non_modificata():
    # Crea anagrafica esistente
    anagrafica = baker.make(
        'anagrafiche.Anagrafica',
        codice_fiscale='SLMRME65H01H501A',
        cognome='SALIMBENI_ORIGINALE',
        nome='REMO_ORIGINALE'
    )
    
    # Importa UNILAV con dati diversi
    response = client.post('/api/v1/documenti/importa_unilav_confirm/', {
        'datore': {
            'codice_fiscale': 'SLMRME65H01H501A',
            'cognome': 'MODIFICATO',  # ← Deve essere ignorato
            'nome': 'MODIFICATO',
        },
        ...
    })
    
    # Verifica che anagrafica NON sia stata modificata
    anagrafica.refresh_from_db()
    assert anagrafica.cognome == 'SALIMBENI_ORIGINALE'
    assert anagrafica.nome == 'REMO_ORIGINALE'
```

### Test 2: Nuova anagrafica viene creata correttamente
```python
@pytest.mark.django_db
def test_nuova_anagrafica_creata():
    assert not Anagrafica.objects.filter(
        codice_fiscale='RSSMRA90A01H501X'
    ).exists()
    
    response = client.post('/api/v1/documenti/importa_unilav_confirm/', {
        'datore': {
            'codice_fiscale': 'RSSMRA90A01H501X',
            'tipo': 'PF',
            'cognome': 'ROSSI',
            'nome': 'MARIO',
        },
        ...
    })
    
    assert response.status_code == 200
    assert Anagrafica.objects.filter(
        codice_fiscale='RSSMRA90A01H501X',
        cognome='ROSSI',
        nome='MARIO'
    ).exists()
```

## 📝 Logs e Debugging

### Esempio Log Preview
```
INFO: UNILAV Preview Request
  File: UNILAV_1700026200007595.pdf
  Datore CF: SLMRME65H01H501A
  Datore Check: ESISTE (ID: 123, Cliente ID: 456)
  Lavoratore CF: CNSLSI95E50H501X
  Lavoratore Check: NON ESISTE
  Response: {esiste: true/false, anagrafica_id: ...}
```

### Esempio Log Confirm
```
INFO: UNILAV Confirm Request
  Datore CF: SLMRME65H01H501A
  Datore Azione: RIUTILIZZO anagrafica ID 123 (senza modifiche)
  Cliente Azione: RIUTILIZZO cliente ID 456
  Lavoratore CF: CNSLSI95E50H501X
  Lavoratore Azione: CREAZIONE nuova anagrafica
  Documento: CREATO documento ID 789
  Success: true
```

## ✅ Vantaggi Implementazione

1. **Integrità dati**: Non modifica anagrafiche esistenti
2. **Trasparenza**: Utente vede cosa verrà fatto prima di confermare
3. **Flessibilità**: Supporta tutti gli scenari (esistente/nuovo)
4. **Sicurezza**: Transazione atomica garantisce consistenza
5. **UX**: Alert chiari con link per visualizzare anagrafiche
6. **Debugging**: Log dettagliati per ogni operazione

## 🚀 Prossimi Sviluppi

### Opzionale: Modalità "Aggiorna se esiste"
```python
# Configurazione opzionale per aggiornare dati esistenti
datore_data = {
    'codice_fiscale': '...',
    'crea_se_non_esiste': True,
    'aggiorna_se_esiste': False,  # ← Flag futuro
    'campi_da_aggiornare': ['telefono', 'email'],  # ← Whitelist
}
```

### Opzionale: Merge Intelligente
```python
# Propone merge per anagrafiche simili (stesso cognome+nome ma CF diverso)
# "ATTENZIONE: Esiste già ROSSI MARIO (CF: XXX). Potrebbe essere duplicato?"
```

## 📚 Riferimenti

- **Modello**: `anagrafiche/models.py` → `Anagrafica`, `Cliente`
- **API Preview**: `api/v1/documenti/views.py` → `importa_unilav_preview()`
- **API Confirm**: `api/v1/documenti/views.py` → `importa_unilav_confirm()`
- **UI Component**: `frontend/src/pages/ImportaUnilavPage.tsx`
- **Parser**: `documenti/parsers/unilav_parser.py`

---

**Versione**: 1.0  
**Data**: 3 Febbraio 2026  
**Autore**: Sistema MyGest
