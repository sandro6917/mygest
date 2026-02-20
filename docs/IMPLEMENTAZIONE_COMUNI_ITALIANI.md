# Sistema Comuni Italiani - Implementazione Completa

## 📋 Panoramica

Il sistema gestisce l'archivio completo dei comuni italiani (7896 comuni) importato da dati ISTAT, con integrazione automatica nel modulo indirizzi dell'applicazione.

## ✅ Componenti Implementati

### 1. Backend Django

#### Model ComuneItaliano
- **File**: `anagrafiche/models_comuni.py`
- **Campi**:
  - `codice_istat`: Codice univoco ISTAT (6 cifre)
  - `codice_belfiore`: Codice Belfiore (4 caratteri)
  - `nome`: Nome del comune
  - `nome_alternativo`: Nome alternativo (es. dialettale)
  - `provincia`: Sigla provincia (2-3 caratteri)
  - `nome_provincia`: Nome esteso provincia
  - `cap`: Codice Avviamento Postale
  - `regione`: Nome regione
  - `codice_regione`: Codice regione ISTAT
  - `flag_capoluogo`: SI/NO (capoluogo di provincia)
  - `latitudine`: Coordinate GPS
  - `longitudine`: Coordinate GPS
  - `attivo`: Boolean per gestione comuni soppressi

- **Indici ottimizzati**:
  - `nome` + `provincia` (ricerca combinata)
  - `provincia` + `nome` (filtro per provincia)
  - `cap` (ricerca per CAP)
  - `codice_belfiore` (ricerca per codice)
  - `attivo` + `provincia` (filtro comuni attivi)

#### Integrazione Indirizzo
- **Campo aggiunto**: `comune_italiano` (ForeignKey nullable a ComuneItaliano)
- **Sincronizzazione automatica** nel metodo `save()`:
  ```python
  if self.comune_italiano_id:
      comune = self.comune_italiano
      self.cap = comune.cap
      self.comune = comune.nome
      self.provincia = comune.provincia
      self.nazione = "IT"
  ```
- **Validazione intelligente**: Skip validazione CAP/Comune/Provincia quando `comune_italiano` è impostato
- **Provincia**: Campo esteso da 2 a 3 caratteri (per province come BT, VB)

#### API REST (DRF)
- **Endpoint**: `/api/v1/anagrafiche/comuni/`
- **Operazioni**: Read-only (GET, LIST)
- **Ricerca**: 
  - `?search={query}` - Cerca in nome, nome_alternativo, cap, codice_istat, codice_belfiore
  - `?provincia={sigla}` - Filtra per provincia
  - `?regione={nome}` - Filtra per regione
  - `?flag_capoluogo={SI|NO}` - Filtra capoluoghi
- **Ottimizzazione**: Limite 50 risultati per autocomplete
- **Serializer**: Restituisce oggetto completo con proprietà calcolate:
  - `denominazione_completa`: "Milano (MI)"
  - `denominazione_estesa`: "Milano (MI) - 20121"

#### Management Command
- **Comando**: `python manage.py import_comuni [json_file]`
- **Opzioni**:
  - `--clear`: Elimina comuni esistenti prima dell'import
  - `--dry-run`: Simula import senza salvare
- **Features**:
  - Gestione comuni con multipli CAP (raggruppa per codice_istat)
  - `update_or_create` per import idempotente
  - Transaction handling con rollback su dry-run
  - Report dettagliato: creati/aggiornati/elaborati
  - Gestione errori: file mancante, JSON invalido, coordinate

#### Django Admin
- **List Display**: nome, provincia, cap, regione, codici, flag_capoluogo, attivo
- **Search**: nome, cap, codice_istat, codice_belfiore, provincia
- **Filters**: provincia, regione, flag_capoluogo, attivo
- **Actions**:
  - `attiva_comuni`: Attivazione massiva comuni
  - `disattiva_comuni`: Disattivazione massiva comuni
- **Fieldsets**: Organizzati per categoria (Dati principali, Localizzazione, Coordinate)
- **Pagination**: 50 record per pagina

### 2. Frontend React

#### ComuneAutocomplete Component
- **File**: `frontend/src/components/ComuneAutocomplete.tsx`
- **Features**:
  - Ricerca debounced (300ms) per performance
  - Autocomplete con dropdown risultati
  - Visualizzazione comune selezionato con badge verde
  - Click outside per chiudere dropdown
  - Loader durante ricerca
  - Pulsante clear per deselezionare
  - Limite minimo 2 caratteri per attivare ricerca

#### IndirizziManager Integration
- **File**: `frontend/src/components/IndirizziManager.tsx`
- **Modifiche**:
  - Aggiunto campo `comune_italiano` e `comune_italiano_display` in interface Indirizzo
  - Nuovo state `selectedComune` per gestire selezione comune
  - Handler `handleComuneChange`: 
    - Popola automaticamente cap, comune, provincia, nazione
    - Resetta a compilazione manuale se deselezionato
  - **Form UI**:
    - ComuneAutocomplete posizionato in evidenza (span 3 colonne)
    - Helper text dinamico: indica se campi sono auto-compilati o manuali
    - Campi CAP/Comune/Provincia/Nazione **disabled e grigi** quando comune selezionato
    - Campi editabili per indirizzi esteri o compilazione manuale

## 🚀 Utilizzo

### Import Dati (One-time Setup)
```bash
# Test import (dry-run)
python manage.py import_comuni --dry-run

# Import effettivo
python manage.py import_comuni

# Import con file custom e pulizia
python manage.py import_comuni /path/to/file.json --clear
```

### API Usage
```bash
# Ricerca comuni
GET /api/v1/anagrafiche/comuni/?search=milano

# Filtra per provincia
GET /api/v1/anagrafiche/comuni/?provincia=MI

# Combina ricerca e filtro
GET /api/v1/anagrafiche/comuni/?search=san&provincia=MI
```

### Frontend Workflow

#### Per indirizzi italiani:
1. Clicca "Nuovo Indirizzo"
2. Cerca comune nella barra autocomplete (es. "Milano")
3. Seleziona comune dalla lista
4. ✅ CAP, Comune, Provincia compilati automaticamente
5. Completa toponimo, indirizzo, numero civico
6. Salva

#### Per indirizzi esteri:
1. Clicca "Nuovo Indirizzo"
2. Lascia vuoto il campo "Comune Italiano"
3. Compila manualmente CAP, Comune, Provincia, Nazione
4. Salva

## 📊 Database

### Tabelle
- `anagrafiche_comuneitaliano`: 7896 comuni (dopo import)
- `anagrafiche_indirizzo`: FK nullable a comuni

### Migration
- **File**: `anagrafiche/migrations/0007_alter_indirizzo_provincia_comuneitaliano_and_more.py`
- **Operazioni**:
  - Alter: provincia VARCHAR(2) → VARCHAR(3)
  - Create: tabella ComuneItaliano con 5 indici
  - Add: campo comune_italiano_id a Indirizzo

## 🎯 Benefici

1. **Dati Standardizzati**: CAP/Comune/Provincia sempre corretti per indirizzi italiani
2. **Riduzione Errori**: Eliminata digitazione manuale per comuni italiani
3. **UX Migliorata**: Ricerca veloce con autocomplete
4. **Flessibilità**: Supporto sia indirizzi italiani (auto) che esteri (manual)
5. **Performance**: Ricerca ottimizzata con indici e limite risultati
6. **Manutenibilità**: Comando import per aggiornamenti periodici dati ISTAT
7. **Backward Compatible**: Indirizzi esistenti continuano a funzionare

## 🔧 Configurazione

### Requisiti
- Django REST Framework
- File JSON comuni (gi_comuni_cap.json)
- React + TypeScript

### Settings
Nessuna configurazione aggiuntiva richiesta. Il sistema utilizza la configurazione Django esistente.

## 📝 Note Tecniche

### Gestione Comuni con Multipli CAP
Il file JSON contiene 8458 record ma solo 7896 comuni unici. Alcuni comuni hanno più CAP per diverse zone/frazioni. Il comando di import gestisce questo automaticamente:
- Raggruppa per `codice_istat` (chiave univoca)
- Prende il primo CAP incontrato
- I CAP aggiuntivi sono gestiti manualmente dall'utente se necessario

### Performance
- API limitata a 50 risultati per autocomplete
- Ricerca debounced (300ms) per ridurre carico server
- 5 indici database per ottimizzare query comuni
- Serializer ottimizzato con proprietà calcolate

### Sicurezza
- API read-only per comuni (no create/update/delete da frontend)
- Validazione backend sempre attiva
- Sanitizzazione input in autocomplete
- Transaction handling per import atomico

## 🧪 Testing

### Backend
```python
# Shell Django
from anagrafiche.models import ComuneItaliano

# Verifica import
print(ComuneItaliano.objects.count())  # 7896

# Test ricerca
ComuneItaliano.objects.filter(nome__icontains='milano')

# Test API
GET /api/v1/anagrafiche/comuni/?search=roma
```

### Frontend
1. Apri form nuovo indirizzo
2. Cerca "Milano" in autocomplete
3. Verifica popolamento automatico CAP (20121), Comune (Milano), Provincia (MI)
4. Deseleziona comune → verifica campi editabili
5. Riseleziona comune → verifica campi disabled e grigi

## 📚 Risorse

- **Dati ISTAT**: gi_comuni_cap.json (fornito)
- **Documentazione DRF**: https://www.django-rest-framework.org/
- **API Endpoint**: http://localhost:8000/api/v1/anagrafiche/comuni/

## 🎉 Stato Implementazione

- ✅ Model ComuneItaliano
- ✅ Integrazione Indirizzo con FK
- ✅ Migration database
- ✅ API REST endpoints
- ✅ Serializers ottimizzati
- ✅ Django Admin interface
- ✅ Management command import
- ✅ Import 7896 comuni completato
- ✅ ComuneAutocomplete React component
- ✅ IndirizziManager integration
- ✅ Auto-sync CAP/Comune/Provincia
- ✅ Supporto indirizzi esteri

**Sistema completo e operativo!** 🚀
