# Gestione Occorrenze e Alert Multipli - Scadenze

## Panoramica delle Modifiche

Questa documentazione descrive le modifiche architetturali implementate per migliorare la gestione delle occorrenze e degli alert nelle scadenze.

### Principali Cambiamenti

1. **Form Scadenza Semplificato**: Il form di creazione/modifica scadenza (`ScadenzaFormPage.tsx`) è stato semplificato per gestire solo i dati base della scadenza.

2. **Gestione Occorrenze nella Detail Page**: La creazione e modifica delle occorrenze è stata spostata nella pagina di dettaglio (`ScadenzaDetailPage.tsx`).

3. **Alert Multipli per Occorrenza**: Implementata la gestione di alert multipli per ogni occorrenza tramite il modello `ScadenzaAlert`.

---

## 1. Form Scadenza Semplificato

### File: `frontend/src/pages/ScadenzaFormPage.tsx`

Il form gestisce solo i campi essenziali della scadenza:

#### Campi Gestiti

**Dati Base:**
- `titolo` (obbligatorio)
- `descrizione`
- `categoria` (campo libero, es: Fiscale, Amministrativo, Legale)
- `stato` (bozza, attiva, completata, archiviata)
- `priorita` (low, medium, high, critical)

**Periodicità:**
- `periodicita` (none, daily, weekly, monthly, yearly, custom)
- `periodicita_intervallo` (numero, es: ogni 2 settimane)

#### Nota Importante

Dopo il salvataggio, l'utente viene indirizzato alla lista scadenze. Per gestire le occorrenze deve accedere alla pagina di dettaglio della scadenza.

**Messaggio Informativo nel Form:**
```
Nota: Dopo aver salvato la scadenza, potrai gestire le occorrenze 
dalla pagina di dettaglio. Le occorrenze possono essere generate 
automaticamente in base alla periodicità configurata oppure create manualmente.
```

---

## 2. Gestione Occorrenze nella Detail Page

### File: `frontend/src/pages/ScadenzaDetailPage.tsx`

La pagina di dettaglio ora include una sezione completa per la gestione delle occorrenze.

### Funzionalità Disponibili

#### 2.1. Buttons nella Toolbar

**"Nuova Occorrenza"** (btn-secondary)
- Apre un modal per creare un'occorrenza manualmente
- Permette di specificare:
  - Titolo (opzionale, usa il titolo della scadenza se vuoto)
  - Descrizione
  - Data/ora inizio (obbligatorio)
  - Data/ora fine (opzionale)
  - Flag "Giornaliera" (occorrenza senza orario specifico)
  - Stato (solo in modifica)

**"Genera Occorrenze"** (btn-primary)
- Genera automaticamente occorrenze in base alla periodicità configurata
- Richiede che la scadenza abbia una periodicità diversa da "none"
- Chiede all'utente quante occorrenze generare (default: 10)
- Gestisce automaticamente:
  - Date in base alla periodicità
  - Evita duplicati esistenti
  - Crea occorrenze future a partire da oggi

#### 2.2. Tabella Occorrenze

Ogni riga della tabella mostra:
- **Titolo**: con badge "Giornaliera" se applicabile
- **Inizio**: data e ora formattate
- **Fine**: data e ora formattate (o "-")
- **Stato**: badge colorato con icona
- **Alert**: informazioni sull'ultimo alert inviato

**Nuova Colonna "Gestione":**
- Button **"🔔 Alert (N)"**: apre il modal di gestione alert multipli
  - N = numero di alert configurati per l'occorrenza

**Colonna "Azioni":**
1. **✏️ Modifica** (btn-primary): apre il modal di modifica occorrenza
2. **✓ Completa** (btn-success): segna l'occorrenza come completata
3. **✕ Annulla** (btn-warning): annulla l'occorrenza
4. **🗑️ Elimina** (btn-danger): elimina definitivamente l'occorrenza

#### 2.3. Stati Occorrenza

- `pending`: ⏳ Pendente
- `scheduled`: 📅 Programmata
- `alerted`: 🔔 Allertata
- `completed`: ✅ Completata
- `cancelled`: ❌ Annullata

---

## 3. Modal Gestione Occorrenza

### File: `frontend/src/components/scadenze/OccorrenzaModal.tsx`

Modal riutilizzabile per creare o modificare un'occorrenza.

### Campi del Form

```typescript
{
  scadenza: number,           // ID della scadenza (auto-popolato)
  titolo: string,             // Opzionale
  descrizione: string,        // Opzionale
  inizio: string,             // Data/ora obbligatoria (datetime-local)
  fine: string,               // Data/ora opzionale (datetime-local)
  giornaliera: boolean,       // Checkbox per occorrenze giornaliere
  stato: string               // Solo in modifica (dropdown)
}
```

### Comportamento

**Creazione:**
- `stato` impostato automaticamente a "pending"
- `scadenza` pre-popolato con l'ID della scadenza corrente

**Modifica:**
- Tutti i campi editabili
- Possibilità di cambiare lo stato
- Validazione delle date

### Validazione

- Campo `inizio` obbligatorio
- Se `fine` è specificato, deve essere successivo a `inizio`
- Formato datetime-local per compatibilità browser

---

## 4. Gestione Alert Multipli

### File: `frontend/src/components/scadenze/AlertManager.tsx`

Modal completo per gestire gli alert di un'occorrenza specifica.

### Modello Alert

Ogni alert è rappresentato dal modello `ScadenzaAlert`:

```typescript
{
  id: number,
  occorrenza: number,           // ID dell'occorrenza
  offset_minuti: number,        // Offset temporale (es: 60 = 1 ora)
  periodo_offset: 'before' | 'after',  // Prima o dopo l'occorrenza
  metodo: 'email' | 'webhook',  // Metodo di notifica
  config: Record<string, any>,  // Configurazione specifica
  programmata_il: string | null,// Quando l'alert sarà inviato
  inviata_il: string | null,    // Quando l'alert è stato inviato
  stato: 'pending' | 'sent' | 'failed' | 'cancelled',
  creato_il: string
}
```

### Funzionalità del Modal

#### Header
- Titolo: "Gestione Alert"
- Sottotitolo: titolo dell'occorrenza

#### Lista Alert
Tabella con colonne:
1. **Offset**: visualizzato in formato leggibile (es: "1h 30m prima")
2. **Metodo**: badge con icona (📧 Email / 🔗 Webhook)
3. **Stato**: badge colorato
4. **Programmata**: data/ora di programmazione
5. **Inviata**: data/ora di invio (se inviato)
6. **Azioni**: 
   - ✏️ Modifica (solo se stato = pending)
   - 🗑️ Elimina (solo se stato = pending)

#### Form Nuovo Alert

Campi:
- **Offset (minuti)**: numero intero positivo
  - Helper: "Es: 60 = 1 ora, 1440 = 1 giorno"
- **Quando**: dropdown
  - Prima dell'occorrenza
  - Dopo l'occorrenza
- **Metodo di Notifica**: dropdown
  - Email
  - Webhook

#### Stati Alert

- `pending`: ⏳ In attesa
- `sent`: ✅ Inviato
- `failed`: ❌ Fallito
- `cancelled`: • Annullato

### API Endpoints

**Lista Alert per Occorrenza:**
```
GET /api/v1/scadenze/occorrenze/{id}/alerts/
```

**Crea Alert:**
```
POST /api/v1/scadenze/occorrenze/{id}/alerts/
Body: {
  offset_minuti: number,
  periodo_offset: 'before' | 'after',
  metodo: 'email' | 'webhook',
  config: {}
}
```

**Modifica Alert:**
```
PATCH /api/v1/scadenze/alerts/{id}/
Body: { ... }
```

**Elimina Alert:**
```
DELETE /api/v1/scadenze/alerts/{id}/
```

---

## 5. Flusso Utente Completo

### Scenario 1: Creare una Scadenza con Periodicità

1. **Navigare a** `/scadenze/nuovo`
2. **Compilare il form:**
   - Titolo: "Pagamento IVA Mensile"
   - Categoria: "Fiscale"
   - Priorità: "Alta"
   - Periodicità: "Mensile"
   - Intervallo: 1
3. **Salvare** → Reindirizzato a `/scadenze`
4. **Aprire la scadenza** dalla lista
5. **Cliccare "Genera Occorrenze"**
6. **Specificare**: 12 occorrenze (un anno)
7. **Confermare** → Occorrenze generate automaticamente

### Scenario 2: Aggiungere Alert Multipli a un'Occorrenza

1. **Aprire la detail page** di una scadenza
2. **Individuare l'occorrenza** nella tabella
3. **Cliccare "🔔 Alert (0)"**
4. **Nel modal, cliccare "Nuovo Alert"**
5. **Configurare primo alert:**
   - Offset: 1440 minuti (1 giorno)
   - Quando: Prima dell'occorrenza
   - Metodo: Email
6. **Salvare**
7. **Aggiungere secondo alert:**
   - Offset: 60 minuti (1 ora)
   - Quando: Prima dell'occorrenza
   - Metodo: Email
8. **Salvare**
9. **Chiudere il modal**
10. **Verificare**: il button ora mostra "🔔 Alert (2)"

### Scenario 3: Modificare un'Occorrenza

1. **Nella tabella occorrenze**, cliccare **✏️ Modifica**
2. **Nel modal, modificare:**
   - Data inizio
   - Descrizione personalizzata
   - Flag giornaliera
3. **Salvare** → Tabella si aggiorna automaticamente

---

## 6. Stili CSS

### File: `frontend/src/styles/global.css`

#### Modal Styles

```css
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--background);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-height: 90vh;
  overflow-y: auto;
  width: 100%;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  margin-top: 1rem;
}
```

---

## 7. API Backend Requirements

### Endpoint Necessari

Il frontend richiede i seguenti endpoint backend:

#### Occorrenze

- `POST /api/v1/scadenze/occorrenze/` - Crea occorrenza
- `PATCH /api/v1/scadenze/occorrenze/{id}/` - Modifica occorrenza
- `DELETE /api/v1/scadenze/occorrenze/{id}/` - Elimina occorrenza
- `POST /api/v1/scadenze/{id}/genera_occorrenze/` - Genera occorrenze automaticamente

#### Alert

- `GET /api/v1/scadenze/occorrenze/{id}/alerts/` - Lista alert per occorrenza
- `POST /api/v1/scadenze/occorrenze/{id}/alerts/` - Crea alert
- `PATCH /api/v1/scadenze/alerts/{id}/` - Modifica alert
- `DELETE /api/v1/scadenze/alerts/{id}/` - Elimina alert

### Serializer Requirements

**ScadenzaOccorrenzaSerializer** deve includere:
```python
fields = [
    ...,
    'num_alerts',  # Conta degli alert configurati
    'alerts'       # Lista completa degli alert (opzionale)
]
```

---

## 8. Testing

### Test Manuale

1. **Test Form Scadenza:**
   - Creare scadenza senza periodicità ✓
   - Creare scadenza con periodicità giornaliera ✓
   - Creare scadenza con periodicità mensile ✓
   - Modificare scadenza esistente ✓

2. **Test Occorrenze:**
   - Generare occorrenze da periodicità ✓
   - Creare occorrenza manuale ✓
   - Modificare occorrenza ✓
   - Eliminare occorrenza ✓
   - Completare occorrenza ✓
   - Annullare occorrenza ✓

3. **Test Alert:**
   - Aprire modal alert ✓
   - Creare alert singolo ✓
   - Creare alert multipli ✓
   - Modificare alert pending ✓
   - Eliminare alert pending ✓
   - Verificare impossibilità modifica alert sent ✓

### Test di Integrazione

```bash
# 1. Avviare backend Django
cd /home/sandro/mygest
source venv/bin/activate
python manage.py runserver

# 2. Avviare frontend Vite
cd frontend
npm run dev

# 3. Navigare a http://localhost:5174/scadenze
```

---

## 9. Miglioramenti Futuri

### Priorità Bassa

1. **Validazione Avanzata:**
   - Alert non sovrapposti
   - Limite massimo alert per occorrenza
   - Validazione offset in base al tipo periodicità

2. **UX Miglioramenti:**
   - Drag & drop per riordinare alert
   - Template alert predefiniti (es: "1 giorno, 1 ora, 15 minuti prima")
   - Visualizzazione calendario per occorrenze

3. **Bulk Operations:**
   - Selezione multipla occorrenze
   - Applicazione alert template a multiple occorrenze
   - Eliminazione massiva occorrenze

4. **Notifiche Real-time:**
   - WebSocket per aggiornamenti stato alert
   - Notifiche browser quando alert viene inviato
   - Badge contatore alert pendenti nella navbar

---

## 10. Conclusioni

### Vantaggi dell'Architettura Attuale

1. **Separazione delle Responsabilità:**
   - Form = gestione dati base scadenza
   - Detail Page = gestione relazioni complesse (occorrenze, alert)

2. **Scalabilità:**
   - Facile aggiungere nuovi tipi di alert
   - Possibilità di estendere con altri tipi di notifiche

3. **UX Migliorata:**
   - Modal per operazioni complesse
   - Feedback visivo immediato
   - Informazioni contestuali chiare

4. **Manutenibilità:**
   - Componenti riutilizzabili (OccorrenzaModal, AlertManager)
   - Logica separata e testabile
   - Codice ben documentato

### Files Modificati

- ✅ `frontend/src/pages/ScadenzaFormPage.tsx` - Semplificato
- ✅ `frontend/src/pages/ScadenzaDetailPage.tsx` - Esteso con gestione occorrenze
- ✅ `frontend/src/components/scadenze/OccorrenzaModal.tsx` - Nuovo componente
- ✅ `frontend/src/components/scadenze/AlertManager.tsx` - Nuovo componente
- ✅ `frontend/src/types/scadenza.ts` - Aggiunto `num_alerts` e `alerts`
- ✅ `frontend/src/styles/global.css` - Aggiunti stili modal

### Files da Verificare Backend

- ⚠️ `api/v1/scadenze/views.py` - Verificare endpoint alert
- ⚠️ `api/v1/scadenze/serializers.py` - Aggiungere `num_alerts` field
- ⚠️ `scadenze/models.py` - Verificare modello ScadenzaAlert

---

**Data Implementazione:** 2025-11-19  
**Versione:** 1.0  
**Autore:** AI Assistant + Developer
