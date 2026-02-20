# Aggiornamento Detail Page Scadenze

## Data: 19 Novembre 2025

## Panoramica

La pagina di dettaglio delle scadenze (`ScadenzaDetailPage.tsx`) è stata completamente aggiornata per integrarsi con le nuove funzionalità implementate nel modulo scadenze, inclusa la gestione automatica degli stati e visualizzazioni più informative.

---

## Modifiche Implementate

### 1. Aggiornamento Types TypeScript

#### `scadenza.ts` - Nuovi Stati e Campi

**Stati Aggiuntivi:**
- `in_scadenza`: Scadenza entro 3 giorni (gestito automaticamente)
- `scaduta`: Scadenza superata (gestito automaticamente)

**Nuovi Campi:**

```typescript
export interface Scadenza {
  // ... altri campi esistenti
  stato: 'bozza' | 'attiva' | 'completata' | 'archiviata' | 'in_scadenza' | 'scaduta';
  data_scadenza: string | null;  // NUOVO: data di scadenza per calcolo automatico stati
}

export interface ScadenzaOccorrenza {
  // ... altri campi esistenti
  giornaliera: boolean;  // NUOVO: flag per occorrenze giornaliere
}
```

### 2. Banner Alert per Scadenze Critiche

Aggiunto banner visibile nella parte superiore della pagina per scadenze con stato `in_scadenza` o `scaduta`:

**Caratteristiche:**
- 🔴 **Scaduta**: Sfondo rosso chiaro, bordo rosso, icona ❌
- 🟡 **In Scadenza**: Sfondo giallo chiaro, bordo arancione, icona ⏰
- Mostra giorni rimanenti o giorni di ritardo
- Visualizza data di scadenza formattata

**Esempio Visivo:**

```
┌────────────────────────────────────────────────────────────┐
│ ❌  Scadenza Superata!                                      │
│     Scaduta da 5 giorni - Data: 14 novembre 2025          │
└────────────────────────────────────────────────────────────┘
```

### 3. Sezione Informazioni Principali Potenziata

#### Nuove Visualizzazioni:

**Icone per Stato:**
- ⏰ Per stato "In Scadenza"
- ❌ Per stato "Scaduta"

**Badge Categoria Migliorato:**
- 🏷️ Icona categoria
- Badge colorato con sfondo primary

**Periodicità con Icone:**
- ⚡ Giornaliera (daily)
- 📅 Settimanale (weekly)
- 📆 Mensile (monthly)
- 🗓️ Annuale (yearly)
- ⚙️ Personalizzata (custom)
- ⏱️ Nessuna (none)

**Data Scadenza con Countdown:**

```
Data Scadenza
├─ 15 dicembre 2025
└─ ⏰ Scade tra 3 giorni  (colorato in arancione)
```

Colori dinamici basati sui giorni rimanenti:
- 🟢 Verde: > 7 giorni
- 🔵 Blu: 4-7 giorni
- 🟡 Arancione: 1-3 giorni
- 🔴 Rosso: Oggi o scaduta

### 4. Statistiche Occorrenze

Aggiunta sezione con 5 card statistiche prima della tabella occorrenze:

```
┌──────────────────────────────────────────────────────────────────┐
│  ⏳        📅         🔔          ✅          ❌                   │
│   5         12        3           45          2                   │
│ Pendenti  Programmate Allertate  Completate  Annullate          │
└──────────────────────────────────────────────────────────────────┘
```

**Metriche Visualizzate:**
1. **Pendenti** (⏳): Occorrenze con stato `pending` - grigio
2. **Programmate** (📅): Occorrenze con stato `scheduled` - blu
3. **Allertate** (🔔): Occorrenze con stato `alerted` - arancione
4. **Completate** (✅): Occorrenze con stato `completed` - verde
5. **Annullate** (❌): Occorrenze con stato `cancelled` - rosso

### 5. Tabella Occorrenze Migliorata

#### Colonne Riorganizzate:

| Colonna | Contenuto | Modifiche |
|---------|-----------|-----------|
| **Titolo** | Titolo occorrenza + badge giornaliera | Badge "📅 Giornaliera" se applicabile |
| **Inizio** | Data/ora inizio | Dimensione font ridotta |
| **Fine** | Data/ora fine | Dimensione font ridotta |
| **Stato** | Badge stato con icona | Icone: ⏳📅🔔✅❌ |
| **Alert** | Metodo + data invio | 2 righe: metodo e "✓ data" |
| **Azioni** | Pulsanti completa/annulla | Colorati e centrati |

#### Pulsanti Azioni Migliorati:

**Occorrenze Attive:**
- ✅ **Completa** (verde): Marca come completata
- ❌ **Annulla** (rosso): Annulla l'occorrenza

**Occorrenze Terminate:**
- Mostra testo "✓ Completata" o "✗ Annullata" invece dei pulsanti

### 6. Funzioni Utility Aggiunte

#### `formatDate(dateString)`
Formatta date in formato lungo italiano:
```
Input:  "2025-11-20"
Output: "20 novembre 2025"
```

#### `getPeriodicityIcon(periodicita)`
Restituisce emoji per tipo periodicità:
```typescript
daily   → ⚡
weekly  → 📅
monthly → 📆
yearly  → 🗓️
custom  → ⚙️
none    → ⏱️
```

#### `getGiorniRimanenti()`
Calcola giorni tra oggi e `data_scadenza`:
```typescript
Oggi: 19 nov 2025
Scadenza: 22 nov 2025
Risultato: 3 (giorni rimanenti)
```

#### `getStatoInfo()`
Genera oggetto con informazioni visuali sullo stato:
```typescript
{
  text: "Scade tra 3 giorni",
  color: "#f59e0b",
  icon: "⏰"
}
```

---

## Benefici degli Aggiornamenti

### 1. **Visibilità Immediata delle Criticità**
- Banner alert in evidenza per scadenze imminenti o superate
- Colori distintivi per priorità e urgenza
- Countdown giorni rimanenti sempre visibile

### 2. **Informazioni Più Complete**
- Data scadenza con calcolo automatico giorni
- Icone intuitive per periodicità e categorie
- Statistiche aggregate sulle occorrenze

### 3. **UX Migliorata**
- Tabella occorrenze più leggibile e compatta
- Pulsanti azioni colorati e chiaramente identificabili
- Badge giornaliera per occorrenze specifiche

### 4. **Integrazione con Gestione Automatica Stati**
- Visualizzazione corretta stati `in_scadenza` e `scaduta`
- Sincronizzazione con comando `aggiorna_stati_scadenze`
- Alert visivi coerenti con priorità critica automatica

### 5. **Monitoraggio Occorrenze**
- Overview statistiche in 5 categorie
- Filtro visivo rapido dello stato occorrenze
- Identificazione immediata occorrenze completate/annullate

---

## Compatibilità

### Backend Django
- ✅ API `/api/v1/scadenze/{id}/` restituisce campo `data_scadenza`
- ✅ Serializer `ScadenzaSerializer` include `stato_display` per nuovi stati
- ✅ Serializer `ScadenzaOccorrenzaSerializer` include campo `giornaliera`

### Database
- ✅ Model `Scadenza` include campo `data_scadenza` (DateField, nullable)
- ✅ Model `Scadenza.Stato` include choices `IN_SCADENZA` e `SCADUTA`
- ✅ Model `ScadenzaOccorrenza` include campo `giornaliera` (BooleanField)

### Frontend React
- ✅ Types aggiornati in `frontend/src/types/scadenza.ts`
- ✅ Componente compatibile con API esistenti
- ✅ Nessuna breaking change per altre pagine

---

## Screenshot Funzionalità

### Banner Alert Scadenza Superata
```
┌─────────────────────────────────────────────────────────────┐
│ ❌  Scadenza Superata!                                       │
│     Scaduta da 5 giorni - Data: 14 novembre 2025           │
└─────────────────────────────────────────────────────────────┘
```

### Banner Alert In Scadenza
```
┌─────────────────────────────────────────────────────────────┐
│ ⏰  Attenzione: Scadenza Imminente                          │
│     Scade tra 2 giorni - Data: 21 novembre 2025            │
└─────────────────────────────────────────────────────────────┘
```

### Statistiche Occorrenze
```
┌────────┬────────────┬──────────┬───────────┬──────────┐
│   ⏳    │     📅     │    🔔    │     ✅    │    ❌    │
│    5    │     12     │     3    │     45    │     2    │
│ Pendenti│ Programmate│ Allertate│Completate │Annullate │
└────────┴────────────┴──────────┴───────────┴──────────┘
```

---

## Test Consigliati

### 1. Test Stati Automatici

**Prerequisito:** Eseguire `python manage.py aggiorna_stati_scadenze`

**Scenari:**
1. Scadenza con `data_scadenza` passata → Mostra banner rosso "Scaduta"
2. Scadenza con `data_scadenza` tra 1-3 giorni → Mostra banner giallo "In Scadenza"
3. Scadenza senza `data_scadenza` → Nessun banner, nessun countdown

### 2. Test Occorrenze

**Scenari:**
1. Occorrenza con `giornaliera=True` → Mostra badge "📅 Giornaliera"
2. Occorrenze con diversi stati → Verifica icone corrette (⏳📅🔔✅❌)
3. Completamento occorrenza → Pulsanti scompaiono, appare testo "✓ Completata"

### 3. Test Periodicità

**Scenari:**
1. Periodicità giornaliera → Icona ⚡
2. Periodicità mensile → Icona 📆
3. Periodicità personalizzata → Icona ⚙️

### 4. Test Countdown

**Scenari:**
1. Scadenza tra 10 giorni → Verde, "10 giorni rimanenti"
2. Scadenza tra 2 giorni → Arancione, "Scade tra 2 giorni"
3. Scadenza oggi → Rosso, "Scade oggi"
4. Scadenza passata 3 giorni fa → Rosso, "Scaduta da 3 giorni"

---

## Migliorie Future (Opzionali)

### 1. Filtri Occorrenze
Aggiungere filtri dropdown sopra la tabella:
- Filtra per stato (Tutte/Pendenti/Completate/etc.)
- Filtra per range date
- Filtra per metodo alert

### 2. Azioni Bulk su Occorrenze
Checkbox per selezionare multiple occorrenze:
- Completa selezionate
- Annulla selezionate
- Rigenera alert

### 3. Grafico Timeline Occorrenze
Vista grafica con linea temporale:
- Occorrenze passate
- Occorrenze future
- Evidenzia completate/annullate

### 4. Notifiche Browser
Integrazione con Notification API:
- Notifica quando si apre scadenza in_scadenza
- Notifica countdown automatico

### 5. Export Singola Scadenza PDF
Pulsante export nella detail page:
- PDF completo di scadenza
- Include tutte le occorrenze
- Formato stampabile

---

## Note Tecniche

### Performance
- Calcolo `getGiorniRimanenti()` ottimizzato (senza librerie esterne)
- Statistiche occorrenze calcolate lato client (filtering nativo JS)
- Nessuna richiesta API aggiuntiva

### Accessibilità
- Colori con contrasto sufficiente (WCAG AA)
- Icone accompagnate da testo descrittivo
- Pulsanti con `title` attribute per tooltip

### Responsive
- Layout 2 colonne su desktop
- Statistiche occorrenze: grid responsive
- Tabella con scroll orizzontale su mobile

---

## Link Correlati

- [Implementazione Funzionalità Avanzate](./IMPLEMENTAZIONE_FUNZIONALITA_AVANZATE.md)
- [Aggiornamento Automatico Stati](./AGGIORNAMENTO_AUTOMATICO_STATI.md)
- [Guida Scadenze Principianti](./guida_scadenze_principianti.md)
- [API Django React Setup](./API_DJANGO_REACT_SETUP.md)

---

**Autore**: Sistema MyGest  
**Versione**: 1.0  
**Data**: 19 Novembre 2025
