# Archivio Fisico - Gestione Operazioni e Verbali di Consegna

## Descrizione

Sistema completo per la gestione delle operazioni di archivio fisico con tracciabilità di documenti e fascicoli, gestione delle unità fisiche di archiviazione e generazione automatica dei verbali di consegna.

## Caratteristiche Principali

### Backend (Django REST Framework)

#### API Endpoints

**Unità Fisiche** (`/api/v1/archivio-fisico/unita/`)
- `GET /` - Lista unità fisiche con filtri
- `POST /` - Crea nuova unità fisica
- `GET /{id}/` - Dettaglio unità fisica
- `PATCH /{id}/` - Aggiorna unità fisica
- `DELETE /{id}/` - Elimina unità fisica
- `GET /tree/` - Struttura ad albero completa
- `GET /{id}/children/` - Figli diretti
- `GET /{id}/ancestors/` - Antenati
- `GET /radici/` - Solo unità radice

**Operazioni Archivio** (`/api/v1/archivio-fisico/operazioni/`)
- `GET /` - Lista operazioni con filtri e paginazione
- `POST /` - Crea nuova operazione (con righe)
- `GET /{id}/` - Dettaglio operazione completo
- `PATCH /{id}/` - Aggiorna operazione
- `DELETE /{id}/` - Elimina operazione
- `POST /{id}/process/` - Processa operazione (aggiorna stati e collocazioni)
- `GET /{id}/verbale/` - Download verbale DOCX
- `GET /{id}/verbale/?template={slug}` - Download con template specifico
- `GET /templates/` - Lista template verbali disponibili

**Righe Operazioni** (`/api/v1/archivio-fisico/righe/`)
- `GET /?operazione={id}` - Righe di un'operazione
- `POST /` - Crea nuova riga
- `PATCH /{id}/` - Aggiorna riga
- `DELETE /{id}/` - Elimina riga

**Collocazioni Fisiche** (`/api/v1/archivio-fisico/collocazioni/`)
- `GET /` - Lista collocazioni con filtri
- `GET /?unita={id}` - Collocazioni per unità
- `GET /?documento={id}` - Collocazioni per documento
- `GET /?solo_attive=true` - Solo collocazioni attive

**Ricerca Oggetti Tracciabili**
- `GET /api/v1/archivio-fisico/documenti-tracciabili/` - Ricerca documenti
- `GET /api/v1/archivio-fisico/fascicoli-tracciabili/` - Ricerca fascicoli
- `GET /api/v1/archivio-fisico/movimenti-protocollo/` - Ricerca movimenti protocollo

#### Filtri Disponibili

**Operazioni Archivio:**
- `tipo_operazione`: entrata | uscita | interna
- `referente_interno`: ID utente
- `referente_esterno`: ID anagrafica
- `data_dal`: data inizio (YYYY-MM-DD)
- `data_al`: data fine (YYYY-MM-DD)
- `search`: ricerca full-text in note e referenti

**Unità Fisiche:**
- `tipo`: ufficio | stanza | scaffale | mobile | anta | ripiano | contenitore | cartellina
- `attivo`: true | false
- `archivio_fisso`: true | false
- `parent`: ID parent
- `search`: ricerca in codice, nome, full_path

### Frontend (React + TypeScript)

#### Componenti Principali

1. **OperazioniArchivioList**
   - Lista paginata delle operazioni
   - Filtri avanzati (tipo, date, ricerca)
   - Azioni rapide (visualizza, modifica, elimina)
   - Chip colorati per tipo operazione
   - Contatori per numero righe

2. **OperazioneArchivioDetail**
   - Visualizzazione completa dell'operazione
   - Informazioni generali e referenti
   - Tabella righe con dettagli completi
   - Azioni: Processa, Download verbale, Modifica, Elimina
   - Menu per selezione template verbale

3. **OperazioneArchivioForm**
   - Form per creazione/modifica operazione
   - Gestione dinamica righe
   - Selezione unità fisiche sorgente/destinazione
   - Upload verbale scansionato
   - Validazione campi obbligatori

#### Tipi TypeScript

Tutti i tipi sono definiti in `/frontend/src/types/archivioFisico.ts`:
- `UnitaFisica`, `UnitaFisicaDetail`, `UnitaFisicaTreeNode`
- `OperazioneArchivio`, `OperazioneArchivioFormData`
- `RigaOperazioneArchivio`, `RigaOperazioneFormData`
- `DocumentoTracciabile`, `FascicoloTracciabile`
- `MovimentoProtocollo`, `CollocazioneFisica`
- `VerbaleConsegnaTemplate`

#### Servizi API

File: `/frontend/src/api/archivioFisico.ts`

Funzioni principali:
- `getUnitaFisiche()`, `getUnitaFisicheTree()`, `getUnitaFisicheRadici()`
- `getOperazioniArchivio()`, `createOperazioneArchivio()`, `updateOperazioneArchivio()`
- `processOperazioneArchivio()` - Processa operazione
- `downloadVerbaleConsegna()` - Download verbale DOCX
- `getDocumentiTracciabili()`, `getFascicoliTracciabili()`

## Routing

Aggiungi al file delle routes (`/frontend/src/routes/index.tsx`):

```typescript
import {
  OperazioniArchivioList,
  OperazioneArchivioDetail,
  OperazioneArchivioForm,
} from '../pages/ArchivioFisico';

// Nel router:
{
  path: '/archivio-fisico',
  children: [
    {
      path: 'operazioni',
      element: <OperazioniArchivioList />,
    },
    {
      path: 'operazioni/nuova',
      element: <OperazioneArchivioForm />,
    },
    {
      path: 'operazioni/:id',
      element: <OperazioneArchivioDetail />,
    },
    {
      path: 'operazioni/:id/modifica',
      element: <OperazioneArchivioForm />,
    },
  ],
}
```

## Funzionalità Avanzate

### Processamento Operazioni

Il processamento di un'operazione esegue:

1. **Per ENTRATA:**
   - Determina unità destinazione (da riga o da protocollo)
   - Aggiorna stato oggetto con quello successivo
   - Crea/aggiorna collocazione fisica

2. **Per USCITA:**
   - Determina unità sorgente (da riga o da protocollo)
   - Sposta a unità di scarico configurata
   - Aggiorna stato a "SCARICATO"

3. **Per MOVIMENTO INTERNO:**
   - Sposta da unità sorgente a destinazione
   - Mantiene stato o lo aggiorna se specificato

### Verbali di Consegna

Sistema di generazione verbali DOCX basato su template:
- Template default o personalizzati
- Variabili disponibili automatiche
- Download diretto da UI
- Supporto file scansionati allegati

### Validazioni

- Solo documenti tracciabili non digitali
- Solo fascicoli con ubicazione fisica
- Controllo esistenza movimenti protocollo
- Validazione stati ammessi per documento/fascicolo
- Prevenzione cicli nella gerarchia unità fisiche

## Installazione e Setup

### Backend

```bash
# Le API sono già registrate in /api/v1/urls.py
# Nessuna migrazione aggiuntiva necessaria se i modelli esistono già

# Verifica che l'app sia in INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'archivio_fisico',
    ...
]
```

### Frontend

```bash
cd frontend

# Le dipendenze MUI dovrebbero già essere installate
# Se mancano:
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install date-fns react-toastify
```

## Configurazione

### Settings Django

```python
# Unità di scarico per operazioni di uscita
ARCHIVIO_FISICO_UNITA_SCARICO_ID = 1  # ID dell'unità "Scarico"
```

### Permessi

Tutte le API richiedono autenticazione (`IsAuthenticated`).
Estendi con permessi custom se necessario:

```python
from rest_framework.permissions import DjangoModelPermissions

class OperazioneArchivioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
```

## Testing

### Test API

```bash
# Test API operazioni
curl -X GET "http://localhost:8000/api/v1/archivio-fisico/operazioni/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test creazione operazione
curl -X POST "http://localhost:8000/api/v1/archivio-fisico/operazioni/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_operazione": "entrata",
    "referente_interno": 1,
    "righe": [
      {
        "documento": 123,
        "unita_fisica_destinazione": 5,
        "stato_successivo": "archiviato"
      }
    ]
  }'
```

### Test Frontend

```bash
cd frontend
npm run dev
# Naviga a http://localhost:5173/archivio-fisico/operazioni
```

## Estensioni Future

- [ ] QR Code per unità fisiche
- [ ] Scanner mobile per ricerca rapida
- [ ] Dashboard statistiche archivio
- [ ] Notifiche per scadenze collocazioni
- [ ] Export Excel elenchi
- [ ] Integrazione con sistemi esterni
- [ ] Audit log completo movimentazioni
- [ ] Ricerca avanzata documenti in archivio

## Troubleshooting

### Errore "Unità di scarico non configurata"
Imposta `ARCHIVIO_FISICO_UNITA_SCARICO_ID` in `settings.py`

### Errore "Documento non tracciabile"
Verifica che il documento abbia `tracciabile=True` e `digitale=False`

### Errore download verbale
Controlla che il template DOCX esista e sia accessibile

### Errore processamento operazione
Verifica che tutti i documenti/fascicoli abbiano movimenti protocollo associati

## Supporto

Per problemi o domande, consulta:
- Documentazione modelli: `/archivio_fisico/models.py`
- Documentazione servizi: `/archivio_fisico/services.py`
- Guida template verbali: `/archivio_fisico/VERBALE_TEMPLATE_GUIDE.md`
