# Implementazione Funzionalità Avanzate - Modulo Scadenze

Documento di sintesi delle funzionalità avanzate implementate nel modulo scadenze.

## Indice

1. [Calendario Visuale con FullCalendar.js](#1-calendario-visuale)
2. [Export PDF/Excel](#2-export-pdfexcel)
3. [Widget Dashboard Potenziato](#3-widget-dashboard)
4. [Statistiche Avanzate con Chart.js](#4-statistiche-avanzate)
5. [Scadenziario Completo](#5-scadenziario-completo)
6. [Gestione Automatica Stati](#6-gestione-automatica-stati)

---

## 1. Calendario Visuale

### Tecnologia
- **Frontend**: FullCalendar.js v6.1.10
- **Componente**: `frontend/src/pages/CalendarioPage.tsx`
- **API**: `/api/v1/scadenze/occorrenze/calendar_events/`

### Funzionalità
- Vista mensile interattiva
- Filtri per stato e priorità
- Colori per priorità:
  - 🟢 Bassa: `#10b981`
  - 🟡 Media: `#f59e0b`
  - 🟠 Alta: `#ef4444`
  - 🔴 Critica: `#dc2626`
- Eventi cliccabili con dettagli
- Navigazione mese per mese

### Endpoint API

**GET** `/api/v1/scadenze/occorrenze/calendar_events/?start=2025-11-01&end=2025-11-30`

Risposta:
```json
[
  {
    "id": "occ_123",
    "title": "Pagamento IMU",
    "start": "2025-11-20T00:00:00",
    "end": "2025-11-20T23:59:59",
    "backgroundColor": "#ef4444",
    "borderColor": "#ef4444",
    "extendedProps": {
      "occorrenza_id": 123,
      "scadenza_id": 45,
      "priorita": "high",
      "stato": "attiva",
      "descrizione": "Scadenza pagamento IMU..."
    }
  }
]
```

---

## 2. Export PDF/Excel

### Backend Django
- **File**: `api/v1/scadenze/views.py`
- **Librerie**: ReportLab (PDF), openpyxl (Excel)

### Endpoint

**GET** `/api/v1/scadenze/export_pdf/?stato=attiva&priorita=high`

Genera PDF con:
- Intestazione con logo e titolo
- Tabella formattata
- Colonne: Titolo, Descrizione, Categoria, Periodicità, Priorità, Stato, Data Scadenza

**GET** `/api/v1/scadenze/export_excel/?stato=attiva`

Genera Excel con:
- Sheet "Scadenze"
- Formattazione automatica larghezza colonne
- Header in grassetto
- Tutte le colonne principali

### Utilizzo React

```typescript
const handleExportPDF = async () => {
  const params = new URLSearchParams({
    stato: filters.stato,
    priorita: filters.priorita,
  });
  
  window.location.href = `/api/v1/scadenze/export_pdf/?${params}`;
};
```

---

## 3. Widget Dashboard

### Componente React
- **File**: `frontend/src/components/ScadenzeWidget.tsx`
- **Posizione**: Dashboard principale (porta 5173)

### Contenuto
1. **Statistiche rapide** (4 card):
   - Totale scadenze
   - Attive
   - In scadenza
   - Scadute

2. **Prossime scadenze** (lista):
   - Titolo e descrizione
   - Data inizio/fine
   - Badge priorità colorato
   - Icona categoria
   - Link a dettaglio

### Dati API

**GET** `/api/v1/scadenze/occorrenze/?limit=5&ordering=inizio`

---

## 4. Statistiche Avanzate

### Componente React
- **File**: `frontend/src/pages/StatistichePage.tsx`
- **Librerie**: Chart.js v4.4.0, react-chartjs-2

### Grafici Implementati

1. **Distribuzione per Priorità** (Doughnut)
   - Conta scadenze per priorità
   - Colori: verde, giallo, arancio, rosso

2. **Distribuzione per Stato** (Pie)
   - Conta scadenze per stato
   - Colori personalizzati per stato

3. **Andamento Mensile** (Bar)
   - Numero scadenze per mese
   - Ultimi 12 mesi

4. **Top 5 Scadenze** (Ranking)
   - Ordinate per numero occorrenze
   - Mostra titolo e contatore

### Endpoint API

**GET** `/api/v1/scadenze/statistiche/`

Risposta:
```json
{
  "priorita": {
    "low": 15,
    "medium": 28,
    "high": 12,
    "critical": 5
  },
  "stato": {
    "bozza": 3,
    "attiva": 45,
    "completata": 12,
    "in_scadenza": 8,
    "scaduta": 2
  },
  "andamento_mensile": [
    {"mese": "2025-01", "count": 12},
    {"mese": "2025-02", "count": 18}
  ],
  "top_scadenze": [
    {"titolo": "Pagamento IMU", "count": 45},
    {"titolo": "ISEE", "count": 32}
  ],
  "totali": {
    "totale": 60,
    "attive": 45,
    "in_scadenza": 8,
    "scadute": 2
  }
}
```

---

## 5. Scadenziario Completo

### Componente React
- **File**: `frontend/src/pages/ScadenziarioPage.tsx`

### Tabella a 9 Colonne

| Colonna | Contenuto | Icone/Badge |
|---------|-----------|-------------|
| Data Inizio | Data + badge giornaliera | 📅 |
| Data Fine | Data occorrenza | - |
| Scadenza | Titolo + descrizione | - |
| Categoria | Badge colorato | 🏷️ |
| Periodicità | Icona periodicità | ⚡📅📆🗓️ |
| Priorità | Badge colorato | Bassa/Media/Alta/Critica |
| Stato Occ. | Badge con icona | ⏳📅🔄✅❌ |
| Alert | Numero alert attivi | 🔔 |
| Azioni | Link dettaglio | 👁️ |

### Filtri Disponibili
- **Stato**: Tutti, Bozza, Attiva, In Scadenza, Completata, Scaduta, Archiviata
- **Priorità**: Tutte, Bassa, Media, Alta, Critica
- **Date**: Data da / Data a
- **Ricerca**: Cerca in titolo e descrizione

### Paginazione
- 10 elementi per pagina
- Navigazione Precedente/Successivo

### Export
- Pulsante "Esporta PDF"
- Pulsante "Esporta Excel"

### API Serializer Potenziato

Il serializer `ScadenzaOccorrenzaSerializer` restituisce l'oggetto scadenza completo:

```python
class ScadenzaOccorrenzaSerializer(serializers.ModelSerializer):
    scadenza = serializers.SerializerMethodField()
    
    def get_scadenza(self, obj):
        return {
            'id': obj.scadenza.id,
            'titolo': obj.scadenza.titolo,
            'descrizione': obj.scadenza.descrizione,
            'priorita': obj.scadenza.priorita,
            'categoria': obj.scadenza.categoria,
            'periodicita': obj.scadenza.periodicita,
            'stato': obj.scadenza.stato,
        }
```

---

## 6. Gestione Automatica Stati

### Comando Django Management
- **File**: `scadenze/management/commands/aggiorna_stati_scadenze.py`
- **Documentazione**: `docs/AGGIORNAMENTO_AUTOMATICO_STATI.md`

### Logica Automatica

1. **Scadenze SCADUTE**
   - Condizione: `data_scadenza < oggi`
   - Da stati: `BOZZA` o `ATTIVA`
   - A stato: `SCADUTA`
   - Priorità: → `CRITICA`

2. **Scadenze IN_SCADENZA**
   - Condizione: `oggi ≤ data_scadenza ≤ oggi + 3 giorni`
   - Da stati: `BOZZA` o `ATTIVA`
   - A stato: `IN_SCADENZA`
   - Priorità: → `CRITICA`

### Esecuzione Manuale

```bash
# Esecuzione normale
python manage.py aggiorna_stati_scadenze

# Test senza salvare (dry-run)
python manage.py aggiorna_stati_scadenze --dry-run --verbose

# Con output dettagliato
python manage.py aggiorna_stati_scadenze --verbose
```

### Cron Job Configurato

```cron
# Esecuzione automatica ogni giorno alle 1:00 AM
0 1 * * * cd /home/sandro/mygest && /home/sandro/mygest/venv/bin/python manage.py aggiorna_stati_scadenze >> /home/sandro/mygest/logs/aggiorna_stati.log 2>&1
```

### Output Esempio

```
=== Aggiornamento Stati Scadenze - 2025-11-19 ===

Scadenze da marcare come SCADUTE: 3
  - [15] Pagamento IMU (data: 2025-11-15) -> SCADUTA + CRITICA
  - [22] Scadenza ISEE (data: 2025-11-10) -> SCADUTA + CRITICA

Scadenze da marcare come IN_SCADENZA: 2
  - [45] Pagamento tasse (data: 2025-11-21, giorni rimanenti: 2) -> IN_SCADENZA + CRITICA

✓ Scadenze marcate come SCADUTE: 3
✓ Scadenze marcate come IN_SCADENZA: 2
✓ Totale aggiornate: 5

✓ Aggiornamenti completati con successo!
```

### Monitoraggio

```bash
# Visualizza log in tempo reale
tail -f /home/sandro/mygest/logs/aggiorna_stati.log

# Verifica cron job
crontab -l

# Controlla esecuzioni nel syslog
grep CRON /var/log/syslog | grep aggiorna_stati
```

---

## Riepilogo Implementazione

### ✅ Funzionalità Completate

1. ✅ Calendario visuale con FullCalendar.js
2. ✅ Export PDF/Excel con ReportLab e openpyxl
3. ✅ Widget dashboard potenziato con statistiche
4. ✅ Statistiche avanzate con Chart.js (4 grafici)
5. ✅ Scadenziario completo (tabella 9 colonne)
6. ✅ Gestione automatica stati con cron job

### ❌ Funzionalità Non Implementate

- ❌ App mobile (esclusa per complessità)
- ❌ Notifiche WebSocket (esclusa per complessità)

### Stack Tecnologico

**Frontend (React):**
- React 18 + TypeScript
- FullCalendar.js v6.1.10
- Chart.js v4.4.0 + react-chartjs-2
- React Router v6
- Axios per API calls
- Tailwind CSS

**Backend (Django):**
- Django 5.2.8
- Django REST Framework
- ReportLab (PDF generation)
- openpyxl (Excel generation)
- PostgreSQL con dj-db-conn-pool

**Infrastruttura:**
- Frontend: Vite dev server (porta 5173)
- Backend: Django API (porta 8000)
- Cron: Esecuzione automatica giornaliera
- Logs: `/home/sandro/mygest/logs/`

---

## Link Utili

- [Documentazione aggiornamento automatico stati](./AGGIORNAMENTO_AUTOMATICO_STATI.md)
- [Guida scadenze per principianti](./guida_scadenze_principianti.md)
- [Setup cron jobs](./CRON_SETUP.md)

---

**Data ultimo aggiornamento**: 19 Novembre 2025  
**Versione**: 1.0  
**Autore**: Sistema MyGest
