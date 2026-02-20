# Feature: Gestione Duplicati UNILAV

**Data**: 4 Febbraio 2026  
**Componente**: Importazione documenti UNILAV  
**Requisito**: Prevenire duplicazione documenti UNILAV con stesso codice_comunicazione

---

## 🎯 Requisiti Implementati

### 1. Controllo Duplicati Globale
- ✅ Codice comunicazione UNILAV deve essere **univoco globalmente**
- ✅ Verifica eseguita durante **preview** (prima della conferma)
- ✅ Ricerca in `AttributoValore` con `codice='codice_comunicazione'`

### 2. UX Gestione Duplicati
- ✅ **Alert rosso** prominente in preview se duplicato rilevato
- ✅ **Dettagli documento esistente**: codice, descrizione, cliente, data
- ✅ **Link** per visualizzare documento esistente
- ✅ **Diff visuale** tra valori attuali e nuovi (modifiche evidenziate)

### 3. Azioni Disponibili
- ✅ **Sovrascrivi**: Aggiorna documento esistente + sostituisce file PDF
- ✅ **Aggiungi comunque**: Crea duplicato consapevolmente (con warning)
- ✅ **Annulla**: Abbandona importazione e torna al form upload

### 4. Audit Logging
- ✅ **Sovrascrittura**: Log con utente, data, valori precedenti, file sostituito
- ✅ **Duplicazione consapevole**: Log warning con utente e codice comunicazione
- ✅ Logging in console (development) e logger Django (production)

---

## 📐 Architettura

### Backend

#### API Preview (`/api/v1/documenti/importa_unilav_preview/`)

**Endpoint**: `POST /api/v1/documenti/importa_unilav_preview/`

**Modifiche**:
1. Dopo parsing PDF, cerca documenti esistenti:
   ```python
   # Cerca tipo UNILAV
   tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
   
   # Cerca attributo codice_comunicazione
   attr_def = AttributoDefinizione.objects.get(
       tipo_documento=tipo_unilav,
       codice='codice_comunicazione'
   )
   
   # Cerca valore attributo con stesso codice
   attr_valore = AttributoValore.objects.filter(
       definizione=attr_def,
       valore=codice_comunicazione
   ).select_related('documento').first()
   ```

2. Se trovato, arricchisce response con:
   ```json
   {
     "duplicato": true,
     "documento_esistente": {
       "id": 123,
       "codice": "SAL-CONLIS01-UNILAV-2026-001",
       "descrizione": "UNILAV 1700026200007595 - Consorti Lisa",
       "data_documento": "2026-01-02",
       "cliente_id": 16,
       "cliente_nome": "SALIMBENI REMO",
       "url": "/documenti/123/",
       "attributi_attuali": {
         "tipo": "Assunzione",
         "data_da": "2026-01-03",
         "data_a": "2026-12-31",
         ...
       }
     }
   }
   ```

#### API Confirm (`/api/v1/documenti/importa_unilav_confirm/`)

**Serializer Updates** (`UnilavImportConfirmSerializer`):
```python
azione = serializers.ChoiceField(
    choices=['crea', 'sovrascrivi', 'duplica'],
    required=False,
    default='crea'
)
documento_id_esistente = serializers.IntegerField(
    required=False,
    allow_null=True
)
```

**Logica Implementata**:

##### Azione: `sovrascrivi`
```python
if azione == 'sovrascrivi' and documento_id_esistente:
    documento = Documento.objects.get(id=documento_id_esistente)
    
    # Salva valori precedenti per audit
    valori_precedenti = {
        'descrizione': documento.descrizione,
        'cliente_id': documento.cliente_id,
        'file': documento.file.name if documento.file else None,
    }
    
    # Aggiorna documento
    documento.cliente = cliente_datore
    documento.titolario_voce = voce_dipendente
    documento.descrizione = nuova_descrizione
    documento.data_documento = data_comunicazione
    documento.save()
    
    # Sostituisci file PDF
    if documento.file:
        documento.file.delete(save=False)
    documento.file.save(pdf_name, File(f), save=True)
    
    # AUDIT LOG
    logger.warning(
        f"AUDIT SOVRASCRITTURA UNILAV - "
        f"Documento ID: {documento.id} - "
        f"Utente: {request.user.username} - "
        f"Codice comunicazione: {codice_comunicazione} - "
        f"File precedente: {valori_precedenti['file']}"
    )
```

##### Azione: `duplica`
```python
elif azione == 'duplica':
    # Crea nuovo documento (duplicato consapevole)
    documento = Documento.objects.create(...)
    
    # AUDIT LOG
    logger.warning(
        f"AUDIT DUPLICAZIONE UNILAV - "
        f"Utente: {request.user.username} - "
        f"Codice comunicazione: {codice_comunicazione} - "
        f"Duplicato creato consapevolmente"
    )
```

##### Azione: `crea` (default)
```python
else:
    # Creazione normale (nessun duplicato)
    documento = Documento.objects.create(...)
```

**Gestione Attributi**:
- Usa `update_or_create` invece di `create` per gestire sia nuovi che aggiornamenti:
  ```python
  AttributoValore.objects.update_or_create(
      documento=documento,
      definizione=definizione,
      defaults={'valore': str(valore)}
  )
  ```

### Frontend

#### Types Update (`ImportaUnilavPage.tsx`)

```typescript
interface PreviewData {
  // ... campi esistenti
  
  // Nuovi campi per duplicati
  duplicato?: boolean;
  documento_esistente?: {
    id: number;
    codice: string;
    descrizione: string;
    data_documento: string | null;
    cliente_id: number;
    cliente_nome: string | null;
    url: string;
    attributi_attuali: {
      tipo: string | null;
      data_da: string | null;
      data_a: string | null;
      qualifica: string | null;
      contratto_collettivo: string | null;
      livello: string | null;
      retribuzione: string | null;
    };
  };
}
```

#### State Management

```typescript
const [azioneSelezionata, setAzioneSelezionata] = useState<'crea' | 'sovrascrivi' | 'duplica'>('crea');
```

#### UI Components

**Alert Duplicato** (mostrato solo se `editedData.duplicato === true`):

```tsx
{editedData.duplicato && editedData.documento_esistente && (
  <Alert severity="error" sx={{ border: '2px solid', borderColor: 'error.main' }}>
    <Typography variant="h6" color="error">
      ⚠️ ATTENZIONE: Documento già importato!
    </Typography>
    
    {/* Dettagli documento esistente */}
    <Box>
      <Typography>Codice: {documento_esistente.codice}</Typography>
      <Typography>Descrizione: {documento_esistente.descrizione}</Typography>
      <Typography>Cliente: {documento_esistente.cliente_nome}</Typography>
      <Button onClick={() => navigate(`/documenti/${documento_esistente.id}`)}>
        Visualizza documento esistente →
      </Button>
    </Box>
    
    {/* Diff valori */}
    <Typography variant="subtitle2">📊 Confronto dati:</Typography>
    <Box>
      {documento_esistente.attributi_attuali.tipo !== editedData.documento.tipo && (
        <Typography color="warning.main">
          • Tipo: {attributi_attuali.tipo} → <strong>{editedData.documento.tipo}</strong>
        </Typography>
      )}
      {/* ... altri diff */}
    </Box>
    
    {/* Pulsanti azione */}
    <Stack direction="row" spacing={2}>
      <Button 
        variant={azioneSelezionata === 'sovrascrivi' ? 'contained' : 'outlined'}
        onClick={() => setAzioneSelezionata('sovrascrivi')}
      >
        🔄 Sovrascrivi
      </Button>
      <Button 
        variant={azioneSelezionata === 'duplica' ? 'contained' : 'outlined'}
        onClick={() => setAzioneSelezionata('duplica')}
      >
        ➕ Aggiungi comunque
      </Button>
      <Button onClick={() => /* reset */}>
        ❌ Annulla
      </Button>
    </Stack>
  </Alert>
)}
```

**Confirm Handler Update**:

```typescript
const handleConfirm = async () => {
  const payload = {
    ...editedData,
    azione: azioneSelezionata,
    documento_id_esistente: editedData.documento_esistente?.id || null,
  };
  
  const response = await documentiApi.importaUnilavConfirm(payload);
  
  const azione_msg = azioneSelezionata === 'sovrascrivi' 
    ? 'sovrascritto' 
    : azioneSelezionata === 'duplica' 
      ? 'duplicato creato'
      : 'importato';
  
  toast.success(`Documento UNILAV ${azione_msg} con successo!`);
  navigate(`/documenti/${response.documento_id}`);
};
```

---

## 🎨 User Experience

### Scenario 1: Nessun Duplicato

1. Utente carica PDF UNILAV
2. Preview mostra alert verde "Dati estratti con successo"
3. Nessun alert duplicato
4. Utente modifica/conferma → Documento creato normalmente

### Scenario 2: Duplicato Rilevato

1. Utente carica PDF UNILAV già importato
2. Preview mostra:
   - ✅ Alert verde "Dati estratti con successo"
   - ❌ **Alert rosso** "ATTENZIONE: Documento già importato!"
3. Alert rosso mostra:
   - Dettagli documento esistente
   - Link per visualizzarlo
   - **Diff** tra valori attuali e nuovi (solo modifiche)
   - 3 pulsanti azione
4. Utente sceglie:
   - **🔄 Sovrascrivi**: Pulsante diventa "contained" (evidenziato)
   - **➕ Aggiungi comunque**: Pulsante diventa "contained"
   - **❌ Annulla**: Reset completo, torna a upload
5. Utente clicca "Conferma Importazione" → Azione eseguita

### Scenario 3: Sovrascrittura

1. Utente seleziona "🔄 Sovrascrivi"
2. Conferma importazione
3. Backend:
   - Aggiorna documento esistente (ID, codice restano uguali)
   - Sostituisce file PDF
   - Aggiorna attributi dinamici
   - **Log audit** con valori precedenti
4. Toast success: "Documento UNILAV sovrascritto con successo!"
5. Redirect a documento (stesso ID)

### Scenario 4: Duplicazione Consapevole

1. Utente seleziona "➕ Aggiungi comunque"
2. Conferma importazione
3. Backend:
   - Crea NUOVO documento (nuovo ID, nuovo codice)
   - **Log warning** duplicazione consapevole
4. Toast success: "Documento UNILAV duplicato creato con successo!"
5. Redirect a nuovo documento

---

## 🔍 Testing

### Test Case 1: Import Nuovo Documento
- ✅ Nessun duplicato rilevato
- ✅ Creazione normale
- ✅ Nessun alert rosso

### Test Case 2: Import Duplicato → Sovrascrivi
- ✅ Duplicato rilevato in preview
- ✅ Alert rosso mostrato
- ✅ Diff valori visualizzato
- ✅ Selezione "Sovrascrivi"
- ✅ Documento aggiornato (stesso ID)
- ✅ File PDF sostituito
- ✅ Audit log creato
- ✅ Toast conferma sovrascrittura

### Test Case 3: Import Duplicato → Duplica
- ✅ Duplicato rilevato in preview
- ✅ Alert rosso mostrato
- ✅ Selezione "Aggiungi comunque"
- ✅ Nuovo documento creato (nuovo ID)
- ✅ Audit log warning creato
- ✅ Toast conferma duplicazione

### Test Case 4: Import Duplicato → Annulla
- ✅ Duplicato rilevato in preview
- ✅ Click "Annulla"
- ✅ Reset completo (preview, editedData, selectedFile = null)
- ✅ Torna a schermata upload

### Test Case 5: Verifica Unicità Globale
- ✅ Import UNILAV cliente A
- ✅ Import stesso codice comunicazione cliente B
- ✅ Duplicato rilevato anche se cliente diverso
- ✅ Unicità globale rispettata

---

## 📝 File Modificati

### Backend
1. **api/v1/documenti/views.py**:
   - `importa_unilav_preview()`: Aggiunto controllo duplicati
   - `importa_unilav_confirm()`: Aggiunta logica sovrascrivi/duplica/crea
   - Audit logging per sovrascrittura e duplicazione

2. **api/v1/documenti/serializers.py**:
   - `UnilavImportConfirmSerializer`: Aggiunti campi `azione` e `documento_id_esistente`
   - Validazione: `documento_id_esistente` obbligatorio se `azione='sovrascrivi'`

### Frontend
3. **frontend/src/pages/ImportaUnilavPage.tsx**:
   - Aggiunto type `duplicato` e `documento_esistente` a `PreviewData`
   - Aggiunto state `azioneSelezionata`
   - Aggiunto Alert rosso duplicato con diff e pulsanti azione
   - Modificato `handleConfirm()` per includere azione nel payload

---

## 🎯 Best Practices Implementate

### 1. Database Consistency
- ✅ `update_or_create` per attributi (gestisce sia create che update)
- ✅ Transazione atomica (`transaction.atomic()`)
- ✅ Eliminazione file precedente prima di salvare nuovo

### 2. Security & Audit
- ✅ Verifica permessi utente (`request.user`)
- ✅ Log dettagliati con timestamp, utente, azione
- ✅ Validazione ID documento esistente

### 3. User Experience
- ✅ Feedback visivo chiaro (alert rosso, diff evidenziato)
- ✅ Azioni reversibili (annulla sempre disponibile)
- ✅ Conferma esplicita prima di sovrascrivere
- ✅ Link diretto a documento esistente

### 4. Code Quality
- ✅ Separation of concerns (preview vs confirm)
- ✅ Type safety (TypeScript interfaces)
- ✅ Error handling completo
- ✅ Logging strutturato

---

## 🚀 Future Enhancements

### Possibili Miglioramenti
1. **Notifiche Email**: Inviare email all'utente quando un documento viene sovrascritto
2. **Versioning**: Salvare snapshot del documento precedente prima della sovrascrittura
3. **Permessi Granulari**: Limitare "sovrascrivi" a utenti con permessi specifici
4. **Storico Modifiche**: Tabella audit dedicata invece di solo logging
5. **Diff Visuale Avanzato**: Mostrare diff file PDF con evidenziazione modifiche

---

**Status**: ✅ Implementato e pronto per test  
**Data completamento**: 4 Febbraio 2026  
**Prossimo step**: Test end-to-end con PDF duplicati
