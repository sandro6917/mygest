# Feature: Destinatari Email Personalizzati per Occorrenze

**Data**: 2 Febbraio 2026  
**Tipo**: Enhancement  
**Moduli**: Scadenze, Alert System

## 📋 Overview

Implementata la possibilità di **specificare destinatari email personalizzati** per singole occorrenze di scadenze, sovrascrivendo i destinatari configurati a livello di scadenza padre.

## 🎯 Requisiti Implementati

### Backend (già esistente)
- ✅ Campo `ScadenzaOccorrenza.alert_config.destinatari` (JSON field)
- ✅ Validazione: se `alert_config.destinatari` è vuoto → fallback a `scadenza.comunicazione_destinatari`
- ✅ Logica dispatch alert con priorità occorrenza > scadenza

### Frontend (NUOVO)
1. ✅ **Type TypeScript**: Creato `ScadenzaOccorrenzaAlertConfig` interface
2. ✅ **Component**: Integrato `DestinatariEmailInput` in `OccorrenzaModal`
3. ✅ **UX**: Campo con placeholder "Lascia vuoto per usare i destinatari della scadenza"
4. ✅ **State Management**: Gestione `alert_config.destinatari` separata

---

## 🔧 Modifiche Tecniche

### 1. Types TypeScript (`frontend/src/types/scadenza.ts`)

```typescript
// NUOVO interface per tipizzare alert_config
export interface ScadenzaOccorrenzaAlertConfig {
  destinatari?: string;  // Email comma-separated (sovrascrive scadenza.comunicazione_destinatari)
  url?: string;  // Webhook URL
  [key: string]: unknown;
}

// MODIFICATO: tipizzazione alert_config
export interface ScadenzaOccorrenza {
  // ... altri campi
  alert_config: ScadenzaOccorrenzaAlertConfig; // era: Record<string, unknown>
}
```

**Motivo**: Tipizzazione forte per migliorare intellisense e type safety.

---

### 2. OccorrenzaModal (`frontend/src/components/scadenze/OccorrenzaModal.tsx`)

#### Import aggiunto
```typescript
import { DestinatariEmailInput } from '../DestinatariEmailInput';
```

#### State aggiornato
```typescript
const [formData, setFormData] = useState<Partial<ScadenzaOccorrenza>>({
  // ... campi esistenti
  alert_config: {},  // NUOVO: inizializzazione
});

useEffect(() => {
  if (occorrenza) {
    setFormData({
      // ... campi esistenti
      alert_config: occorrenza.alert_config || {},  // NUOVO: caricamento dati
    });
  }
}, [occorrenza]);
```

#### Handler aggiunto
```typescript
const handleDestinatariChange = (value: string) => {
  setFormData(prev => ({
    ...prev,
    alert_config: {
      ...prev.alert_config,
      destinatari: value,
    },
  }));
};
```

#### Campo UI aggiunto (dopo descrizione, prima delle date)
```tsx
<div className="form-group">
  <label htmlFor="destinatari">
    Destinatari Email Alert
    <small style={{ display: 'block', color: '#666', fontWeight: 'normal' }}>
      Lascia vuoto per usare i destinatari della scadenza
    </small>
  </label>
  <DestinatariEmailInput
    value={formData.alert_config?.destinatari || ''}
    onChange={handleDestinatariChange}
  />
</div>
```

---

## 🎨 UI/UX

### Posizionamento Campo
```
[Modal: Nuova/Modifica Occorrenza]
├── Titolo
├── Descrizione
├── 📧 Destinatari Email Alert  ← NUOVO
├── Inizio / Fine (datetime-local)
├── Giornaliera (checkbox)
└── Stato (select)
```

### Comportamento
1. **Creazione Occorrenza**:
   - Campo vuoto → usa destinatari della scadenza padre
   - Campo compilato → usa destinatari personalizzati

2. **Modifica Occorrenza**:
   - Carica `alert_config.destinatari` esistenti (se presenti)
   - Può modificare/rimuovere destinatari personalizzati

3. **Input Email**:
   - Input manuale (comma-separated)
   - Autocomplete clienti (carica email automaticamente)
   - Display chips con rimozione individuale

---

## 🔍 Logica Backend (esistente)

### Validazione (`scadenze/models.py`)
```python
def clean(self) -> None:
    if self.metodo_alert == self.MetodoAlert.EMAIL:
        destinatari = (self.alert_config or {}).get("destinatari")
        if not destinatari and not self.scadenza.comunicazione_destinatari:
            raise ValidationError({
                "alert_config": "Specificare almeno un destinatario email "
                               "oppure configurare la scadenza.",
            })
```

**Regola**: 
- Se occorrenza.alert_config.destinatari = vuoto/assente
  - E scadenza.comunicazione_destinatari = vuoto/assente
    - → ERRORE ❌

### Dispatch Alert (`scadenze/services.py`)
```python
# AlertDispatcher._send_email_alert()
destinatari_occorrenza = (alert.alert_config or {}).get("destinatari")
destinatari = (
    destinatari_occorrenza 
    if destinatari_occorrenza 
    else alert.occorrenza.scadenza.comunicazione_destinatari
)
```

**Priorità**: `occorrenza.alert_config.destinatari` > `scadenza.comunicazione_destinatari`

---

## 🧪 Testing

### Scenario Test 1: Destinatari personalizzati occorrenza
```
1. Apri http://localhost:5174/scadenze/{id}
2. Click "Modifica" su una occorrenza
3. Inserisci email in "Destinatari Email Alert": test@example.com
4. Salva
5. Verifica DB: alert_config = {"destinatari": "test@example.com"}
6. Quando alert viene inviato → email a test@example.com (non scadenza.comunicazione_destinatari)
```

### Scenario Test 2: Fallback a destinatari scadenza
```
1. Crea nuova occorrenza
2. Lascia vuoto "Destinatari Email Alert"
3. Salva
4. Verifica DB: alert_config = {} oppure {"destinatari": ""}
5. Quando alert viene inviato → email a scadenza.comunicazione_destinatari
```

### Scenario Test 3: Autocomplete cliente
```
1. Apri modal occorrenza
2. In "Destinatari Email Alert", usa autocomplete cliente
3. Seleziona "Mario Rossi" (email: mario.rossi@example.com)
4. Verifica chip con email aggiunta
5. Salva e controlla alert_config.destinatari
```

---

## 📊 Impatto Sistema

### Database
- **Nessuna migrazione necessaria** (campo JSON già esistente)
- Compatibilità backward: occorrenze esistenti continuano a usare fallback

### API
- **Nessuna modifica endpoint** (alert_config già serializzato)
- Frontend può leggere/scrivere alert_config.destinatari

### Performance
- **Impatto minimo**: lettura JSON field già esistente
- Nessuna query aggiuntiva

---

## 📁 Files Modificati

### Frontend
1. **`frontend/src/types/scadenza.ts`**
   - ➕ `ScadenzaOccorrenzaAlertConfig` interface
   - ✏️ `ScadenzaOccorrenza.alert_config` tipizzato

2. **`frontend/src/components/scadenze/OccorrenzaModal.tsx`**
   - ➕ Import `DestinatariEmailInput`
   - ➕ Handler `handleDestinatariChange`
   - ➕ Campo "Destinatari Email Alert" nel form
   - ✏️ State `alert_config` inizializzato e gestito

### Backend
- **Nessuna modifica** (funzionalità già implementata)

---

## 🎯 Use Cases

### Use Case 1: Alert diversificati per cliente
```
Scadenza: "Scadenza F24" 
├── Destinatari default: contabilita@studio.it
├── Occorrenza 10/02/2026 (Cliente A)
│   └── Destinatari custom: clienteA@example.com, contabilita@studio.it
└── Occorrenza 15/02/2026 (Cliente B)
    └── Destinatari custom: clienteB@example.com, contabilita@studio.it
```

**Risultato**: 
- Alert 10/02 → clienteA@example.com, contabilita@studio.it
- Alert 15/02 → clienteB@example.com, contabilita@studio.it

### Use Case 2: Occorrenza urgente con CC multipli
```
Scadenza: "Riunione settimanale"
├── Destinatari default: team@studio.it
└── Occorrenza 05/02/2026 (con ospite esterno)
    └── Destinatari custom: team@studio.it, ospite@external.com, admin@studio.it
```

---

## ✅ Checklist Completamento

- [x] Type `ScadenzaOccorrenzaAlertConfig` creato
- [x] Type `ScadenzaOccorrenza.alert_config` tipizzato
- [x] Import `DestinatariEmailInput` in `OccorrenzaModal`
- [x] State `alert_config` inizializzato
- [x] Handler `handleDestinatariChange` implementato
- [x] Campo UI aggiunto al form
- [x] Label con helper text
- [x] Compilazione TypeScript senza errori
- [x] Dev server attivo per testing

---

## 🚀 Deployment

### Build Frontend
```bash
cd /home/sandro/mygest/frontend
npm run build
```

### Deploy Produzione (quando testato)
```bash
cd /home/sandro/mygest
./scripts/deploy.sh
```

**Note**: 
- Backend già funzionante (nessuna migrazione)
- Solo frontend necessita deploy

---

## 📚 Documentazione Correlata

- **Alert System**: Vedi conversazione iniziale su funzionamento alert
- **DestinatariEmailInput**: Component creato per Scadenza, riusato per Occorrenze
- **Backend Logic**: `scadenze/models.py` (righe 255-275), `scadenze/services.py`

---

**Status**: ✅ IMPLEMENTATO  
**Testing**: 🔄 IN CORSO  
**Deployment**: ⏳ PENDING
