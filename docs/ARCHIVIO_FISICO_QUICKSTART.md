# Quick Start - Archivio Fisico Frontend

## Installazione Rapida

### 1. Backend Setup

Le API sono già configurate. Verifica solo che l'app sia attiva:

```python
# mygest/settings.py
INSTALLED_APPS = [
    ...
    'archivio_fisico',
    ...
]

# Configura unità di scarico (obbligatorio per operazioni di uscita)
ARCHIVIO_FISICO_UNITA_SCARICO_ID = 1  # Sostituisci con ID reale
```

### 2. Frontend Setup

```bash
cd frontend

# Installa dipendenze se necessario
npm install @mui/material @mui/icons-material
npm install date-fns react-toastify lodash

# Avvia dev server
npm run dev
```

### 3. Aggiungi Routes

Modifica `frontend/src/routes/index.tsx` (o il tuo file di routing):

```typescript
import {
  OperazioniArchivioList,
  OperazioneArchivioDetail,
  OperazioneArchivioForm,
} from '../pages/ArchivioFisico';

// Aggiungi al tuo router:
const routes = [
  // ... altre route
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
  },
];
```

### 4. Aggiungi al Menu

Aggiungi link al menu principale della tua applicazione:

```typescript
// Nel tuo componente di navigazione
<MenuItem component={Link} to="/archivio-fisico/operazioni">
  <ArchiveIcon />
  <ListItemText primary="Archivio Fisico" />
</MenuItem>
```

## Primo Utilizzo

### 1. Crea Unità Fisiche

Prima di creare operazioni, devi avere unità fisiche nel sistema.

**Via Django Admin:**
```
http://localhost:8000/admin/archivio_fisico/unitafisica/
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/archivio-fisico/unita/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prefisso_codice": "UFF",
    "nome": "Ufficio Principale",
    "tipo": "ufficio",
    "attivo": true
  }'
```

### 2. Crea Prima Operazione

**Via UI:**
1. Vai a `/archivio-fisico/operazioni`
2. Clicca "Nuova Operazione"
3. Seleziona tipo operazione
4. Inserisci referente interno (tuo user ID)
5. Aggiungi righe con documenti/fascicoli
6. Specifica unità di destinazione
7. Salva

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/archivio-fisico/operazioni/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_operazione": "entrata",
    "referente_interno": 1,
    "note": "Prima archiviazione",
    "righe": [
      {
        "documento": 123,
        "unita_fisica_destinazione": 5,
        "stato_successivo": "archiviato"
      }
    ]
  }'
```

### 3. Processa Operazione

Dopo aver creato l'operazione, processala per aggiornare stati e collocazioni:

**Via UI:**
1. Apri dettaglio operazione
2. Clicca "Processa"
3. Conferma

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/archivio-fisico/operazioni/1/process/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Genera Verbale

**Via UI:**
1. Apri dettaglio operazione
2. Clicca "Verbale" → Seleziona template
3. Il file DOCX verrà scaricato

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/archivio-fisico/operazioni/1/verbale/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output verbale.docx
```

## Test Rapido

### Test API

```bash
# 1. Lista operazioni
curl http://localhost:8000/api/v1/archivio-fisico/operazioni/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Lista unità fisiche
curl http://localhost:8000/api/v1/archivio-fisico/unita/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Albero unità
curl http://localhost:8000/api/v1/archivio-fisico/unita/tree/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Documenti tracciabili
curl "http://localhost:8000/api/v1/archivio-fisico/documenti-tracciabili/?search=DOC" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test UI

1. Avvia server: `npm run dev`
2. Login all'applicazione
3. Naviga a `/archivio-fisico/operazioni`
4. Verifica che la pagina carichi correttamente
5. Prova filtri e ricerca
6. Crea nuova operazione

## Componenti Disponibili

### Pagine Complete

```typescript
import {
  OperazioniArchivioList,
  OperazioneArchivioDetail,
  OperazioneArchivioForm,
} from '../pages/ArchivioFisico';
```

### Componenti Riutilizzabili

```typescript
import {
  UnitaFisicaTreeView,
  DocumentoSelector,
  FascicoloSelector,
} from '../components/ArchivioFisico';

// Esempio utilizzo TreeView
<UnitaFisicaTreeView
  onSelectNode={(node) => console.log('Selected:', node)}
  selectedNodeId={selectedId}
  showAddButton={true}
  onAdd={() => navigate('/nuova-unita')}
/>

// Esempio utilizzo DocumentoSelector
<DocumentoSelector
  value={selectedDocumento}
  onChange={setSelectedDocumento}
  label="Seleziona Documento"
  required
/>

// Esempio utilizzo FascicoloSelector
<FascicoloSelector
  value={selectedFascicolo}
  onChange={setSelectedFascicolo}
  label="Seleziona Fascicolo"
/>
```

## Troubleshooting Comune

### Problema: "Unità di scarico non configurata"
**Soluzione:** Imposta `ARCHIVIO_FISICO_UNITA_SCARICO_ID` in settings.py

### Problema: "Documento non tracciabile"
**Soluzione:** Il documento deve avere:
- `tracciabile = True`
- `digitale = False`

### Problema: Errori TypeScript
**Soluzione:** Gli errori di tipo MUI sono dovuti alla compilazione. L'app funziona a runtime.
Per risolverli definitivamente:
```bash
npm install --save-dev @types/react @types/react-dom
```

### Problema: "Failed to fetch"
**Soluzione:** Verifica che:
1. Backend sia in esecuzione su porta 8000
2. Frontend sia configurato con il proxy corretto
3. Token di autenticazione sia valido

### Problema: Verbale non si scarica
**Soluzione:** Verifica che:
1. Esista almeno un `VerbaleConsegnaTemplate` attivo
2. Il file DOCX del template sia accessibile
3. Il modulo `python-docx` sia installato nel backend

## Configurazione Avanzata

### Custom Permissions

```python
# api/v1/archivio_fisico/views.py
from rest_framework.permissions import DjangoModelPermissions

class OperazioneArchivioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
```

### Custom Serializer Fields

```python
# api/v1/archivio_fisico/serializers.py
class OperazioneArchivioDetailSerializer(serializers.ModelSerializer):
    custom_field = serializers.SerializerMethodField()
    
    def get_custom_field(self, obj):
        return "custom value"
```

### Filtri Aggiuntivi

```python
# api/v1/archivio_fisico/views.py
class OperazioneArchivioViewSet(viewsets.ModelViewSet):
    filterset_fields = ['tipo_operazione', 'referente_interno', 'custom_field']
```

## Prossimi Passi

1. **Personalizza Stili:** Modifica i componenti per adattarli al tema della tua applicazione
2. **Aggiungi Validazioni:** Estendi le validazioni client-side nel form
3. **Dashboard:** Crea una dashboard con statistiche archivio
4. **QR Code:** Implementa generazione QR code per unità fisiche
5. **Mobile:** Crea versione mobile per scanner

## Risorse

- **Documentazione Completa:** `/docs/ARCHIVIO_FISICO_FRONTEND.md`
- **Modelli Backend:** `/archivio_fisico/models.py`
- **API Serializers:** `/api/v1/archivio_fisico/serializers.py`
- **Tipi TypeScript:** `/frontend/src/types/archivioFisico.ts`

## Supporto

Per problemi o domande:
1. Controlla i log del backend: `python manage.py runserver`
2. Controlla la console del browser per errori JS
3. Verifica le chiamate API nella tab Network
4. Consulta la documentazione completa

---

**Buon lavoro con l'Archivio Fisico! 📦**
