# Implementazione Fascicoli Collegati (M2M)

## 📋 Panoramica

Implementata relazione many-to-many tra fascicoli, permettendo di collegare fascicoli in modo flessibile senza vincoli di gerarchia.

## 🎯 Obiettivo

Permettere di collegare fascicoli tra loro con una relazione molti-a-molti, distinta dalla relazione gerarchica parent-child dei sottofascicoli.

**Ogni fascicolo può avere:**
- 0 o più sottofascicoli (relazione gerarchica `parent` → `sottofascicoli`)
- 0 o più fascicoli collegati (relazione M2M `fascicoli_collegati`)
- 0 o 1 parent (genitore nella gerarchia)

## 🔧 Modifiche Backend

### 1. Model (`fascicoli/models.py`)

```python
class Fascicolo(models.Model):
    # ... campi esistenti ...
    
    parent = models.ForeignKey(
        "self", 
        null=True, 
        blank=True, 
        on_delete=models.PROTECT, 
        related_name="sottofascicoli"
    )
    
    # NUOVO CAMPO M2M
    fascicoli_collegati = models.ManyToManyField(
        "self", 
        symmetrical=False,  # Unidirezionale
        blank=True,
        related_name="collegato_da",
        help_text="Altri fascicoli collegati a questo fascicolo"
    )
```

**Caratteristiche:**
- `symmetrical=False`: Relazione unidirezionale (A → B non implica B → A)
- `blank=True`: Campo opzionale
- `related_name="collegato_da"`: Per query inverse (quali fascicoli hanno collegato questo?)

### 2. Migration

```bash
# Creata e applicata
python manage.py makemigrations fascicoli
# → fascicoli/migrations/0008_fascicolo_fascicoli_collegati.py

python manage.py migrate fascicoli
# → OK
```

### 3. Serializers (`api/v1/fascicoli/serializers.py`)

#### FascicoloListSerializer
```python
num_fascicoli_collegati = serializers.SerializerMethodField()

def get_num_fascicoli_collegati(self, obj):
    return obj.fascicoli_collegati.count()
```

#### FascicoloDetailSerializer
```python
fascicoli_collegati_details = serializers.SerializerMethodField()

def get_fascicoli_collegati_details(self, obj):
    return FascicoloListSerializer(
        obj.fascicoli_collegati.all(), 
        many=True, 
        context=self.context
    ).data
```

#### FascicoloWriteSerializer
```python
class Meta:
    fields = [
        # ... altri campi ...
        'fascicoli_collegati',  # AGGIUNTO
    ]
```

### 4. ViewSet - Nuovi Endpoints (`api/v1/fascicoli/views.py`)

#### a) `GET /api/v1/fascicoli/{id}/sottofascicoli_collegabili/`

**NUOVO ENDPOINT** per fascicoli collegabili come sottofascicoli:

**Logica di filtraggio:**
- Stesso cliente del fascicolo corrente
- Stesso titolario del fascicolo corrente  
- Stesso anno del fascicolo corrente
- `parent__isnull=True` (non già collegati come sottofascicoli)
- Escludi il fascicolo corrente

**Limite:** 20 risultati

**Esempio:**
```bash
GET /api/v1/fascicoli/123/sottofascicoli_collegabili/
```

#### b) `GET /api/v1/fascicoli/{id}/fascicoli_collegabili/`

Restituisce fascicoli collegabili (relazione M2M - filtrati):

**Logica di esclusione:**
- Il fascicolo stesso
- I sottofascicoli del fascicolo
- Fascicoli già collegati

**Parametri opzionali:**
- `search`: Ricerca per codice, titolo, nome cliente
- `anno`: Filtra per anno
- `cliente`: Filtra per cliente
- `titolario`: Filtra per voce titolario

**Limite:** 100 risultati

**Esempio:**
```bash
GET /api/v1/fascicoli/123/fascicoli_collegabili/?search=contratto&anno=2025
```

#### b) `POST /api/v1/fascicoli/{id}/collega_fascicolo/`

Collega un fascicolo al fascicolo corrente (relazione M2M).

**Body:**
```json
{
  "fascicolo_id": 456
}
```

**Validazioni:**
- ✅ Fascicolo esiste
- ❌ Non può collegare a se stesso
- ❌ Non può collegare un proprio sottofascicolo
- ❌ Non può collegare se già collegato

**Response:**
```json
{
  "success": true,
  "message": "Fascicolo FAM-2025-002 collegato con successo"
}
```

#### c) `POST /api/v1/fascicoli/{id}/scollega_fascicolo/`

Scollega un fascicolo dal fascicolo corrente.

**Body:**
```json
{
  "fascicolo_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "message": "Fascicolo FAM-2025-002 scollegato con successo"
}
```

## 🎨 Modifiche Frontend

### 1. Types (`frontend/src/types/fascicolo.ts`)

```typescript
export interface FascicoloListItem {
  // ... campi esistenti ...
  num_fascicoli_collegati?: number;  // NUOVO
}

export interface Fascicolo extends FascicoloListItem {
  // ... campi esistenti ...
  fascicoli_collegati_details?: FascicoloListItem[];  // NUOVO
}

export interface FascicoloFormData {
  // ... campi esistenti ...
  fascicoli_collegati?: number[];  // NUOVO
}
```

### 2. API Client (`frontend/src/api/fascicoli.ts`)

```typescript
// Ottieni fascicoli collegabili come sottofascicoli
async getSottofascicoliCollegabili(fascicoloId: number): Promise<FascicoloListItem[]>

// Ottieni fascicoli collegabili con filtri (M2M)
async getFascicoliCollegabili(
  fascicoloId: number, 
  filters?: {
    search?: string;
    anno?: number;
    cliente?: number;
    titolario?: number;
  }
): Promise<FascicoloListItem[]>

// Collega fascicolo
async collegaFascicolo(
  fascicoloId: number, 
  fascicoloDaCollegareId: number
): Promise<{ success: boolean; message: string }>

// Scollega fascicolo
async scollegaFascicolo(
  fascicoloId: number, 
  fascicoloDaScollegareId: number
): Promise<{ success: boolean; message: string }>
```

### 3. Pagina Dettaglio (`frontend/src/pages/FascicoloDetailPage.tsx`)

#### Card 1: "Fascicoli Collegati" (M2M)
Posizionata **sotto la card Sottofascicoli**.

**Visualizzazione:**
- Mostrata solo se ci sono fascicoli collegati (`fascicolo.fascicoli_collegati_details.length > 0`)
- Tabella con: Codice, Titolo, Anno, Cliente, Stato
- Badge colorati per lo stato del fascicolo

**Azioni per ogni fascicolo:**
- 👁️ **Visualizza**: Naviga alla detail page del fascicolo collegato
- 🗑️ **Scollega**: Rimuove il collegamento M2M

#### Card 2: "Gestione Collegamenti Fascicoli"

**Caratteristiche:**
- Barra di ricerca real-time
- **Lista VUOTA all'avvio** - popolata solo quando l'utente digita nella ricerca
- Messaggio: "Inizia a digitare nella barra di ricerca per trovare fascicoli da collegare"
- Filtro automatico: esclude self, sottofascicoli, già collegati

**Ricerca:**
- Campo di testo con placeholder "Cerca fascicoli per codice, titolo o cliente..."
- Ricerca attivata `onChange` con debounce naturale
- Se campo vuoto → lista svuotata automaticamente

**Tabella fascicoli trovati:**
- Mostra: Codice, Titolo, Anno, Cliente, Stato
- Pulsante "+ Collega" per ogni fascicolo

#### Card 3: "Collega Fascicolo Esistente come Sottofascicolo"

**Caratteristiche:**
- Usa endpoint dedicato `sottofascicoli_collegabili`
- Filtra automaticamente: stesso cliente, titolario, anno
- Solo fascicoli con `parent__isnull=True`
- Caricamento automatico all'apertura della pagina

**Azioni:**
- Pulsante "+ Collega" per collegare come sottofascicolo

#### Nuove Funzioni

```typescript
// Carica fascicoli collegabili M2M
const loadFascicoliCollegabiliM2M = async (search?: string) => {
  const data = await fascicoliApi.getFascicoliCollegabili(fascicoloId, { search });
  setFascicoliCollegabiliM2M(data);
};

// Collega fascicolo M2M
const handleCollegaFascicoloM2M = async (targetId, targetCodice) => {
  await fascicoliApi.collegaFascicolo(fascicoloId, targetId);
  await loadFascicolo(); // Ricarica per aggiornare lista collegati
  await loadFascicoliCollegabiliM2M(searchCollegabili);
};

// Scollega fascicolo M2M
const handleScollegaFascicoloM2M = async (targetId, targetCodice) => {
  await fascicoliApi.scollegaFascicolo(fascicoloId, targetId);
  await loadFascicolo();
  await loadFascicoliCollegabiliM2M(searchCollegabili);
};
```

## 📊 Schema Relazioni

```
Fascicolo A
├── parent: null                        (Fascicolo radice)
├── sottofascicoli: [B, C]              (Relazione 1-N gerarchica)
└── fascicoli_collegati: [D, E]         (Relazione M-N)

Fascicolo B
├── parent: A                           (Sottofascicolo di A)
├── sottofascicoli: []
└── fascicoli_collegati: [F]

Fascicolo D
├── parent: null
├── sottofascicoli: []
├── fascicoli_collegati: []
└── collegato_da: [A]                   (Query inversa)
```

## 🧪 Testing

### Test Backend (Django Shell)

```python
from fascicoli.models import Fascicolo

# Crea fascicoli test
f1 = Fascicolo.objects.get(pk=1)
f2 = Fascicolo.objects.get(pk=2)

# Collega f2 a f1
f1.fascicoli_collegati.add(f2)

# Verifica collegamento
f1.fascicoli_collegati.all()  # [<Fascicolo: f2>]
f2.collegato_da.all()         # [<Fascicolo: f1>]

# Scollega
f1.fascicoli_collegati.remove(f2)
```

### Test API

```bash
# Lista fascicoli collegabili
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/fascicoli/123/fascicoli_collegabili/?search=test

# Collega fascicolo
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fascicolo_id": 456}' \
  http://localhost:8000/api/v1/fascicoli/123/collega_fascicolo/

# Scollega fascicolo
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fascicolo_id": 456}' \
  http://localhost:8000/api/v1/fascicoli/123/scollega_fascicolo/
```

## ✅ Checklist Implementazione

### Backend
- [x] Aggiunto campo M2M `fascicoli_collegati` al model Fascicolo
- [x] Creata e applicata migration 0008
- [x] Aggiornato FascicoloListSerializer con contatore
- [x] Aggiornato FascicoloDetailSerializer con dettagli collegati
- [x] Aggiornato FascicoloWriteSerializer per permettere editing
- [x] Endpoint `fascicoli_collegabili` modificato con logica filtro corretta
- [x] Endpoint `collega_fascicolo` con validazioni
- [x] Endpoint `scollega_fascicolo`

### Frontend
- [x] Aggiornati types TypeScript
- [x] Aggiornato API client con nuovi metodi
- [x] Nuova card "Fascicoli Collegati" in FascicoloDetailPage
- [x] Tabella fascicoli già collegati con azione "Scollega"
- [x] Barra ricerca con filtro real-time
- [x] Tabella fascicoli collegabili con azione "+ Collega"
- [x] Gestione errori e conferme utente

## 🎯 Use Cases

### UC1: Collegare Fascicoli Correlati
**Scenario:** Due fascicoli di clienti diversi ma relativi allo stesso progetto

1. Apri dettaglio Fascicolo A
2. Scorri a "Fascicoli Collegati"
3. Cerca Fascicolo B nella barra ricerca
4. Clicca "+ Collega" su Fascicolo B
5. Conferma collegamento

**Risultato:** Fascicolo B appare nella sezione "Collegati" del Fascicolo A

### UC2: Scollegare Fascicolo
1. Apri dettaglio Fascicolo A
2. Nella sezione "Collegati" trova Fascicolo B
3. Clicca "Scollega"
4. Conferma scollegamento

**Risultato:** Fascicolo B scompare dalla lista collegati

### UC3: Ricerca Fascicoli Collegabili
1. Apri dettaglio Fascicolo
2. Nella barra ricerca digita "contratto"
3. Vedi solo fascicoli con "contratto" nel codice/titolo/cliente
4. Fascicoli esclusi automaticamente: self, sottofascicoli, già collegati

## 🔒 Validazioni e Regole Business

1. **Non collegare a se stesso**
   - ❌ Fascicolo A → Fascicolo A

2. **Non collegare sottofascicoli**
   - Se B è sottofascicolo di A
   - ❌ Fascicolo A → Fascicolo B

3. **Evitare duplicati**
   - Se A → B già esiste
   - ❌ Nuovo collegamento A → B

4. **Unidirezionalità**
   - A → B NON implica B → A
   - Devi creare esplicitamente entrambi se necessario

## 📝 Note Tecniche

- **Performance**: Query ottimizzate con `select_related` e `prefetch_related`
- **Limitazione risultati**: Endpoint `fascicoli_collegabili` limita a 100 record
- **Search**: Case-insensitive, cerca in codice, titolo, nome e cognome cliente
- **Reverse lookup**: Usa `collegato_da` per trovare chi ha collegato un fascicolo

## 🚀 Deploy

```bash
# 1. Pull codice aggiornato
cd /srv/mygest/app
git pull origin main

# 2. Attiva virtual environment
source venv/bin/activate

# 3. Applica migration
python manage.py migrate fascicoli

# 4. Rebuild frontend
cd frontend
npm run build

# 5. Collectstatic
cd ..
python manage.py collectstatic --noinput

# 6. Restart services
sudo systemctl restart mygest-gunicorn
sudo systemctl restart nginx
```

## 📚 Riferimenti

- Django ManyToManyField: https://docs.djangoproject.com/en/4.2/ref/models/fields/#manytomanyfield
- DRF Serializers: https://www.django-rest-framework.org/api-guide/serializers/
- React Hooks: https://react.dev/reference/react

---

**Versione**: 1.0  
**Data**: Gennaio 2026  
**Autore**: GitHub Copilot + Sandro Chimenti
