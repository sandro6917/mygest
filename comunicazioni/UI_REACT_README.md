# UI React per il Modulo Comunicazioni

Questa è l'interfaccia utente React per il modulo di gestione delle comunicazioni in MyGest.

## 📁 Struttura File

```
frontend/src/
├── api/
│   └── comunicazioni.ts          # Client API per comunicazioni
├── types/
│   └── comunicazioni.ts          # TypeScript types e interfaces
├── pages/
│   ├── ComunicazioniListPage.tsx # Lista comunicazioni con filtri
│   ├── ComunicazioneFormPage.tsx # Form crea/modifica
│   └── ComunicazioneDetailPage.tsx # Dettaglio comunicazione
├── styles/
│   └── comunicazioni.css         # Stili specifici del modulo
└── routes/
    └── index.tsx                 # Route configurate
```

## 🎯 Funzionalità Implementate

### 1. Lista Comunicazioni (`/comunicazioni`)
- **Visualizzazione tabella** con tutte le comunicazioni
- **Filtri avanzati**:
  - Ricerca testuale (oggetto, corpo, mittente)
  - Filtro per tipo (Avviso scadenza, Invio documenti, Informativa)
  - Filtro per direzione (Entrata/Uscita)
  - Filtro per stato (Bozza, Inviata, Errore)
- **Paginazione** configurabile
- **Azioni rapide**: Visualizza, Modifica, Invia
- **Badge visivi** per stato e direzione

### 2. Creazione/Modifica Comunicazione (`/comunicazioni/create`, `/comunicazioni/:id/edit`)
- **Form completo** con validazione
- **Campi principali**:
  - Tipo di comunicazione
  - Direzione (bloccata se protocollata)
  - Oggetto e corpo del messaggio
  - Mittente personalizzato (opzionale)
- **Gestione destinatari**:
  - Inserimento manuale di email
  - Autocomplete per contatti email
  - Autocomplete per liste di distribuzione
  - Visualizzazione destinatari selezionati
- **Protezioni**:
  - Campi non modificabili se protocollata
  - Validazione lato client

### 3. Dettaglio Comunicazione (`/comunicazioni/:id`)
- **Visualizzazione completa** di tutti i dati
- **Informazioni principali**:
  - Tipo, direzione, stato
  - Date di creazione e invio
  - Mittente e destinatari
  - Protocollo (se presente)
- **Contenuto**:
  - Oggetto e corpo del messaggio
  - Supporto HTML
  - Lista allegati
- **Azioni disponibili**:
  - Modifica (se bozza)
  - Invio (se bozza)
  - Protocollazione (se possibile)
  - Eliminazione (se bozza)
- **Visualizzazione errori** di invio (se presenti)

## 🔌 API Endpoints Utilizzati

Il client API in `src/api/comunicazioni.ts` utilizza i seguenti endpoint:

```typescript
// Comunicazioni
GET    /api/v1/comunicazioni/comunicazioni/          # Lista con filtri
GET    /api/v1/comunicazioni/comunicazioni/:id/      # Dettaglio
POST   /api/v1/comunicazioni/comunicazioni/          # Crea
PATCH  /api/v1/comunicazioni/comunicazioni/:id/      # Aggiorna
DELETE /api/v1/comunicazioni/comunicazioni/:id/      # Elimina
POST   /api/v1/comunicazioni/comunicazioni/:id/send/ # Invia

// Contatti Email
GET    /api/v1/comunicazioni/contatti/               # Lista contatti

// Mailing Lists
GET    /api/v1/comunicazioni/liste/                  # Lista mailing list

// Email Import
GET    /api/v1/comunicazioni/email-import/           # Lista email importate

// Template Fields
GET    /api/v1/comunicazioni/template-fields/        # Campi template
```

## 📝 Types TypeScript

### Interfacce Principali

```typescript
interface Comunicazione {
  id: number;
  tipo: 'AVVISO' | 'DOCUMENTI' | 'INFORMATIVA';
  direzione: 'IN' | 'OUT';
  oggetto: string;
  corpo: string;
  destinatari_calcolati: string[];
  stato: 'bozza' | 'inviata' | 'errore';
  data_creazione: string;
  data_invio?: string;
  protocollo_label: string;
  // ... altri campi
}

interface EmailContatto {
  id: number;
  email: string;
  nominativo: string;
  tipo: 'email' | 'pec';
  anagrafica_display: string;
}

interface MailingList {
  id: number;
  nome: string;
  contatti_count: number;
}
```

## 🎨 Stili

Gli stili sono definiti in `src/styles/comunicazioni.css` e includono:

- **Layout responsive** con grid CSS
- **Card components** per organizzazione contenuti
- **Badge system** per stati e categorie
- **Form styling** consistente
- **Tabelle responsive** con hover effects
- **Modal dialogs** per conferme
- **Utilities** per spacing e layout

### Classi CSS Principali

```css
.page-container          # Container principale pagina
.card, .card-header      # Sistema card
.badge-*                 # Badge colorati per stati
.form-control            # Input e form elements
.btn, .btn-primary       # Pulsanti
.table                   # Tabelle
.pagination-container    # Controlli paginazione
.modal-overlay           # Modale
```

## 🔄 State Management

Utilizzo di **React Query** (`@tanstack/react-query`) per:
- Gestione cache delle chiamate API
- Invalidazione automatica dopo mutations
- Loading e error states
- Refetch automatico

```typescript
// Esempio query
const { data, isLoading } = useQuery({
  queryKey: ['comunicazioni', filters],
  queryFn: () => comunicazioniApi.list(filters),
});

// Esempio mutation
const sendMutation = useMutation({
  mutationFn: () => comunicazioniApi.send(id),
  onSuccess: () => {
    queryClient.invalidateQueries(['comunicazioni']);
  },
});
```

## 🚀 Come Utilizzare

### Navigazione
1. Clicca su "Comunicazioni" nel menu principale
2. Visualizza la lista delle comunicazioni
3. Usa i filtri per trovare comunicazioni specifiche
4. Clicca su "Nuova Comunicazione" per crearne una

### Creare una Comunicazione
1. Compila il form con tipo, oggetto e corpo
2. Aggiungi destinatari:
   - Manualmente (email separate da virgola)
   - Selezionando contatti dalla rubrica
   - Selezionando liste di distribuzione
3. Salva come bozza o invia direttamente

### Inviare una Comunicazione
1. Apri la comunicazione in dettaglio
2. Verifica i destinatari e il contenuto
3. Clicca su "Invia"
4. Conferma l'invio

### Protocollare una Comunicazione
1. La comunicazione deve avere un documento allegato
2. Clicca su "Protocolla" nel dettaglio
3. Completa i dati di protocollazione
4. Una volta protocollata, direzione e documento non sono più modificabili

## 🔧 Configurazione

### API Base URL
Configurato in `src/config.ts`:
```typescript
export const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

### Environment Variables
Crea un file `.env.development`:
```
VITE_API_BASE_URL=http://localhost:8000
```

## 📱 Responsive Design

L'interfaccia è completamente responsive:
- **Desktop**: Layout a più colonne, tabelle complete
- **Tablet**: Layout adattivo, menu compatto
- **Mobile**: Layout singola colonna, tabelle scrollabili

## 🔒 Sicurezza

- Autenticazione JWT tramite interceptor axios
- Token refresh automatico su 401
- Route protette con `ProtectedRoute`
- Validazione lato client prima dell'invio

## 🐛 Gestione Errori

- Alert visivi per errori API
- Log dettagliati degli errori di invio
- Fallback UI per stati di errore
- Messaggi user-friendly

## 📚 Dipendenze Principali

```json
{
  "@tanstack/react-query": "^5.90.10",
  "axios": "^1.13.2",
  "react": "^19.2.0",
  "react-router-dom": "^7.9.6"
}
```

## 🔄 Prossimi Sviluppi

- [ ] Editor WYSIWYG per corpo HTML
- [ ] Gestione template comunicazioni
- [ ] Anteprima email prima dell'invio
- [ ] Statistiche invii
- [ ] Gestione allegati tramite drag & drop
- [ ] Export comunicazioni in PDF
- [ ] Ricerca avanzata full-text
- [ ] Filtri salvati

## 📞 Supporto

Per problemi o domande:
- Controlla la console del browser per errori
- Verifica che il backend sia in esecuzione
- Controlla i log Django per errori API
- Consulta la documentazione API in `/api/v1/docs/`
