# Guida Amministratore/Utente - Modulo Anagrafiche MyGest

## Indice

1. [Introduzione](#introduzione)
2. [Accesso al Sistema](#accesso-al-sistema)
3. [Dashboard Principale](#dashboard-principale)
4. [Gestione Anagrafiche](#gestione-anagrafiche)
5. [Creazione Nuova Anagrafica](#creazione-nuova-anagrafica)
6. [Dettaglio Anagrafica](#dettaglio-anagrafica)
7. [Gestione Indirizzi](#gestione-indirizzi)
8. [Gestione Contatti Email](#gestione-contatti-email)
9. [Sistema Comuni Italiani](#sistema-comuni-italiani)
10. [Esportazione Dati](#esportazione-dati)
11. [Stampe e Report](#stampe-e-report)
12. [Funzioni Amministratore](#funzioni-amministratore)
13. [API REST](#api-rest)
14. [Troubleshooting](#troubleshooting)

---

## 1. Introduzione

Il modulo **Anagrafiche** di MyGest è un sistema completo per la gestione di persone fisiche, persone giuridiche e clienti. Offre funzionalità avanzate per:

- Gestione completa dei dati anagrafici
- Gestione indirizzi con integrazione comuni italiani (7896 comuni)
- Gestione contatti email e PEC
- Conversione automatica in clienti
- Generazione codici anagrafica automatici
- Esportazione dati (CSV, PDF)
- Stampe professionali
- API REST per integrazioni

### Tecnologie Utilizzate

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router (navigazione)
- Axios (HTTP client)

**Backend:**
- Django 4.2
- Django REST Framework
- PostgreSQL
- JWT Authentication

---

## 2. Accesso al Sistema

### 2.1 Login

1. Aprire il browser e navigare all'URL: `http://[server]:5173`
2. Inserire le credenziali:
   - **Username**: il tuo username aziendale
   - **Password**: la tua password
3. Cliccare su **"Accedi"**

### 2.2 Logout

Cliccare sull'icona utente in alto a destra e selezionare **"Logout"**

### 2.3 Credenziali Dimenticate

Contattare l'amministratore di sistema per il reset della password.

---

## 3. Dashboard Principale

Dopo il login, viene visualizzata la **Dashboard** con:

### 3.1 Card Statistiche

Quattro card interattive mostrano:

1. **Pratiche Attive** (blu)
   - Numero pratiche in corso
   - Pratiche chiuse
   - Click per accedere alla sezione Pratiche

2. **Documenti** (viola)
   - Totale documenti in archivio
   - Click per accedere all'archivio documenti

3. **Scadenze Attive** (arancione)
   - Scadenze in corso
   - Click per accedere al calendario scadenze

4. **Clienti Attivi** (verde)
   - Numero clienti attivi (ultimi 6 mesi)
   - Click per accedere alle anagrafiche

### 3.2 Grafico Pratiche per Mese

Visualizzazione a barre delle pratiche suddivise per mese con:
- Barre colorate interattive
- Tooltip con numero pratiche al passaggio del mouse

### 3.3 Info Sistema

Pannello informativo con:
- ✓ Autenticazione JWT attiva
- ✓ API REST Django configurata
- ✓ Dashboard in tempo reale
- ✓ Gestione anagrafiche completa
- ✓ Sistema comuni italiani integrato

---

## 4. Gestione Anagrafiche

### 4.1 Accesso alla Lista Anagrafiche

Dal menu laterale, cliccare su **"Anagrafiche"** (icona persone)

### 4.2 Lista Anagrafiche

La schermata principale mostra:

**Header:**
- Titolo "Anagrafiche" con contatore
- Barra di ricerca
- Pulsante **"+ Nuova Anagrafica"**

**Filtri:**
- **Tipo**: Tutte / Persone Fisiche / Persone Giuridiche
- **Cliente**: Tutti / Solo Clienti / Non Clienti
- **Ordinamento**: Nome (A-Z) / Nome (Z-A) / Data Creazione / Codice

**Tabella:**
Colonne visualizzate:
- **Codice**: Codice univoco anagrafica
- **Nome/Ragione Sociale**: Nome completo o ragione sociale
- **Tipo**: PF (Persona Fisica) / PG (Persona Giuridica)
- **Cliente**: Badge "Cliente" se convertito
- **Email/PEC**: Indirizzi email principali
- **Azioni**: 
  - 👁️ Visualizza dettaglio
  - ✏️ Modifica
  - 🗑️ Elimina

**Paginazione:**
- Navigazione tra pagine
- Indicatore "Pagina X di Y"

### 4.3 Ricerca Anagrafiche

Nella barra di ricerca in alto:
1. Digitare il testo da cercare
2. La ricerca avviene automaticamente su:
   - Nome/Cognome
   - Ragione sociale
   - Codice fiscale
   - Partita IVA
   - Email
   - Telefono
3. I risultati si aggiornano in tempo reale

### 4.4 Filtri Avanzati

**Filtro per Tipo:**
- **Tutte**: mostra tutte le anagrafiche
- **Persone Fisiche**: solo persone fisiche
- **Persone Giuridiche**: solo aziende/enti

**Filtro Cliente:**
- **Tutti**: tutte le anagrafiche
- **Solo Clienti**: anagrafiche con flag cliente attivo
- **Non Clienti**: anagrafiche non ancora clienti

**Ordinamento:**
Ordinare la lista per:
- Nome/Ragione sociale (alfabetico A-Z o Z-A)
- Data creazione (più recenti o più vecchi)
- Codice anagrafica

---

## 5. Creazione Nuova Anagrafica

### 5.1 Avvio Creazione

1. Dalla lista anagrafiche, cliccare **"+ Nuova Anagrafica"**
2. Si apre il form di creazione

### 5.2 Compilazione Form - Dati Principali

**Sezione "Dati Principali":**

**Tipo Persona** (obbligatorio):
- Selezionare **Persona Fisica** o **Persona Giuridica**
- Il form si adatta automaticamente

**Per Persona Fisica:**
- **Nome** * (obbligatorio)
- **Cognome** * (obbligatorio)
- **Codice Fiscale**: 16 caratteri, validazione automatica
- **Sesso**: M/F (opzionale)
- **Data di Nascita**: selettore data
- **Luogo di Nascita**: città
- **Provincia di Nascita**: sigla (es. MI)

**Per Persona Giuridica:**
- **Ragione Sociale** * (obbligatorio)
- **Partita IVA**: 11 cifre, validazione automatica
- **Codice Fiscale**: 11 o 16 caratteri
- **Forma Giuridica**: es. SRL, SPA, SNC, etc.

**Checkbox "Cliente":**
- Spuntare se l'anagrafica è già un cliente
- Abilita la gestione cliente avanzata

### 5.3 Dati di Contatto

**Sezione "Dati di Contatto":**

- **Email**: indirizzo email principale
- **PEC**: indirizzo PEC (validazione formato)
- **Telefono**: numero telefono principale
- **Telefono Mobile**: cellulare
- **Fax**: numero fax (opzionale)

**Validazioni:**
- Email: formato valido (nome@dominio.ext)
- PEC: formato email valido
- Telefono: solo numeri e caratteri +, -, (, ), spazio

### 5.4 Note

Campo **Note** libero per annotazioni aggiuntive

### 5.5 Salvataggio

1. Compilare almeno i campi obbligatori (*)
2. Cliccare **"Salva"**
3. Il sistema:
   - Valida i dati
   - Genera automaticamente il codice anagrafica
   - Salva l'anagrafica
   - Mostra messaggio di conferma
   - Reindirizza al dettaglio anagrafica

**Codice Anagrafica Automatico:**
- **Persona Fisica**: `CF-COGNOME-NNNN`
  - Esempio: `CF-ROSSI-0001`
- **Persona Giuridica**: `PG-RAGIONESOCIALE-NNNN`
  - Esempio: `PG-ACMESRL-0001`

### 5.6 Annullamento

Cliccare **"Annulla"** per tornare alla lista senza salvare

---

## 6. Dettaglio Anagrafica

### 6.1 Accesso al Dettaglio

Dalla lista anagrafiche:
- Cliccare sull'icona 👁️ nella riga dell'anagrafica
- Oppure cliccare sul nome/ragione sociale

### 6.2 Struttura Pagina

La pagina dettaglio è divisa in sezioni:

**Header:**
- Nome completo / Ragione sociale
- Codice anagrafica
- Badge tipo (Persona Fisica / Persona Giuridica)
- Badge "Cliente" (se attivo)
- Pulsanti azione:
  - **← Indietro**: torna alla lista
  - **✏️ Modifica**: apre form modifica
  - **🗑️ Elimina**: elimina anagrafica (con conferma)
  - **🖨️ Stampa**: genera PDF anagrafica
  - **👤 → Cliente**: converte in cliente (se non già cliente)
  - **🔄 Ricalcola Codice**: rigenera il codice

### 6.3 Sezione Dati Anagrafici

**Card "Dati Anagrafici":**

Visualizza tutti i dati principali:
- Nome e Cognome / Ragione Sociale
- Codice Fiscale
- Partita IVA (per PG)
- Sesso, Data e Luogo di Nascita (per PF)
- Forma Giuridica (per PG)
- Data Creazione
- Ultima Modifica

### 6.4 Sezione Contatti

**Card "Contatti":**

Mostra i contatti principali:
- **PEC**: con icona email e link mailto
- **Email**: con icona email e link mailto
- **Telefono**: con icona telefono
- **Mobile**: numero cellulare
- **Fax**: se presente

**Note:** Le email lunghe vanno a capo automaticamente per evitare overflow

### 6.5 Sezione Indirizzi

Gestione completa indirizzi (vedi sezione 7)

### 6.6 Sezione Contatti Email

Gestione contatti email avanzata (vedi sezione 8)

### 6.7 Conversione in Cliente

Se l'anagrafica non è ancora cliente:

1. Cliccare pulsante **"👤 Converti in Cliente"**
2. Confermare l'operazione
3. Il sistema:
   - Attiva il flag cliente
   - Crea record cliente associato
   - Aggiorna la visualizzazione
   - Mostra messaggio di conferma

**Badge "Cliente"** appare nell'header dopo la conversione

### 6.8 Ricalcolo Codice

Per ricalcolare il codice anagrafica:

1. Cliccare **"🔄 Ricalcola Codice"**
2. Confermare l'operazione
3. Il sistema:
   - Verifica la coerenza del codice attuale
   - Genera nuovo codice se necessario
   - Mostra il risultato:
     - ✓ "Codice già corretto" (se coerente)
     - ✓ "Codice aggiornato da X a Y" (se modificato)

**Quando ricalcolare:**
- Dopo modifica nome/cognome/ragione sociale
- Se il codice non segue lo standard
- Per uniformare vecchi codici

---

## 7. Gestione Indirizzi

### 7.1 Panoramica

Ogni anagrafica può avere **multipli indirizzi** con:
- Tipologie diverse (residenza, domicilio, sede legale, etc.)
- Indirizzo principale (flag)
- Integrazione con comuni italiani (7896 comuni)
- Supporto indirizzi esteri

### 7.2 Visualizzazione Indirizzi

**Card "Indirizzi":**
- Lista indirizzi esistenti
- Ogni indirizzo mostra:
  - Badge tipo (Residenza, Domicilio, etc.)
  - Badge "Principale" (se attivo)
  - Indirizzo completo: Toponimo Via Nome Numero
  - Frazione (se presente)
  - CAP, Comune (Provincia) - Nazione
  - Note (se presenti)
  - Pulsanti: ✏️ Modifica, 🗑️ Elimina

**Sfondo azzurro** per indirizzo principale

### 7.3 Aggiunta Nuovo Indirizzo

1. Cliccare **"+ Nuovo Indirizzo"**
2. Si apre il form di inserimento

**Form Campi:**

**Tipo Indirizzo** *:
- Residenza
- Domicilio
- Sede Legale
- Sede Amministrativa
- Ufficio
- Altro

**Checkbox "Principale":**
- Spuntare per impostare come indirizzo principale
- Solo un indirizzo può essere principale

**Comune Italiano (opzionale):**
- Campo autocomplete per comuni italiani
- Digitare almeno 2 caratteri per attivare la ricerca
- Selezionare il comune dalla lista
- **Vantaggi:**
  - CAP, Comune e Provincia compilati automaticamente
  - Dati sempre corretti e aggiornati
  - Campi disabilitati (grigi) quando comune selezionato

**Campi Indirizzo:**
- **Toponimo**: Via, Viale, Piazza, Corso, Vicolo, Località
- **Indirizzo** *: nome della via/strada
- **N. Civico**: numero civico
- **Frazione**: frazione o località

**Dati Località (auto-compilati se comune selezionato):**
- **CAP** *: codice avviamento postale (5 cifre)
- **Comune** *: nome comune
- **Provincia** *: sigla provincia (2-3 caratteri, es. MI, BT)
- **Nazione**: codice ISO (default: IT)

**Note:**
- Campo libero per annotazioni

3. Cliccare **"Salva"** per confermare
4. Cliccare **"Annulla"** per tornare indietro

### 7.4 Modifica Indirizzo

1. Cliccare icona ✏️ sull'indirizzo da modificare
2. Si apre il form pre-compilato
3. Modificare i campi desiderati
4. Cliccare **"Salva"**

### 7.5 Eliminazione Indirizzo

1. Cliccare icona 🗑️ sull'indirizzo da eliminare
2. Confermare l'operazione
3. L'indirizzo viene rimosso

**Attenzione:** L'operazione è irreversibile

### 7.6 Indirizzi Esteri

Per indirizzi fuori dall'Italia:

1. **Non selezionare** alcun comune italiano
2. Compilare manualmente:
   - CAP (formato locale)
   - Comune/Città
   - Provincia/Stato
   - Nazione (codice ISO, es. FR, DE, US)

I campi restano editabili per inserimento libero

---

## 8. Gestione Contatti Email

### 8.1 Panoramica

Sistema avanzato per gestire **multipli contatti email** associati all'anagrafica:
- Email multiple per tipologia
- Contatto preferito
- Stato attivo/non attivo
- Nominativo referente
- Note per ogni contatto

### 8.2 Visualizzazione Contatti Email

**Card "Contatti Email":**
- Lista contatti esistenti
- Ogni contatto mostra:
  - Badge tipo (Generico, PEC, Amministrativo, etc.)
  - Badge "Preferito" ⭐ (se attivo)
  - Badge "Non attivo" (se disattivato)
  - Nominativo referente (se presente)
  - Indirizzo email (con link mailto)
  - Note (se presenti)
  - Pulsanti: ✏️ Modifica, 🗑️ Elimina

**Sfondo giallo** per contatto preferito
**Opacità ridotta** per contatto non attivo

### 8.3 Aggiunta Nuovo Contatto Email

1. Cliccare **"+ Nuovo Contatto"**
2. Si apre il form di inserimento

**Form Campi:**

- **Nominativo**: nome del referente (es. "Mario Rossi - Ufficio Acquisti")
- **Email** *: indirizzo email (validazione formato)
- **Tipo** *:
  - Generico
  - PEC
  - Amministrativo
  - Commerciale
  - Tecnico
  - Altro
- **Checkbox "Preferito"**: email da usare preferibilmente
- **Checkbox "Attivo"**: contatto attivo (default: spuntato)
- **Note**: annotazioni libere

3. Cliccare **"Salva"** per confermare

### 8.4 Modifica Contatto Email

1. Cliccare icona ✏️ sul contatto da modificare
2. Si apre il form pre-compilato
3. Modificare i campi desiderati
4. Cliccare **"Salva"**

### 8.5 Eliminazione Contatto Email

1. Cliccare icona 🗑️ sul contatto da eliminare
2. Confermare l'operazione
3. Il contatto viene rimosso

### 8.6 Best Practices

**Uso dei Tipi:**
- **PEC**: per comunicazioni ufficiali/certificati
- **Amministrativo**: ufficio contabilità/amministrazione
- **Commerciale**: ufficio vendite/commerciale
- **Tecnico**: supporto tecnico/assistenza
- **Generico**: email generali info@, contatti@

**Contatto Preferito:**
- Impostare il contatto principale per comunicazioni automatiche
- Solo un contatto può essere preferito

**Contatto Non Attivo:**
- Disattivare contatti non più validi invece di eliminarli
- Mantiene lo storico delle comunicazioni

---

## 9. Sistema Comuni Italiani

### 9.1 Database Comuni

Il sistema integra il **database completo ISTAT** con:
- **7896 comuni italiani** attivi
- Dati aggiornati e verificati
- Coordinate GPS
- Codici ISTAT e Belfiore
- Capoluoghi di provincia

### 9.2 Ricerca Comuni

**Funzionalità Autocomplete:**

1. Nel form indirizzo, digitare nel campo **"Comune Italiano"**
2. Dopo 2 caratteri, appare il dropdown risultati
3. La ricerca avviene su:
   - Nome comune
   - Nome alternativo
   - CAP
   - Codice ISTAT
   - Codice Belfiore

**Esempio:**
- Digitare "milano" → mostra "Milano (MI) - 20121"
- Digitare "20097" → mostra "San Donato Milanese (MI) - 20097"

### 9.3 Selezione Comune

1. Cliccare sul comune desiderato nel dropdown
2. Il sistema:
   - Compila automaticamente CAP
   - Compila automaticamente Comune
   - Compila automaticamente Provincia
   - Imposta Nazione = "IT"
   - Disabilita i campi (grigi) per evitare errori

**Visualizzazione:**
- Badge verde con comune selezionato
- Pulsante ✕ per deselezionare

### 9.4 Modifica/Rimozione Comune

Per cambiare comune o passare a inserimento manuale:

1. Cliccare pulsante **✕ rosso** sul badge verde
2. Il comune viene deselezionato
3. I campi CAP/Comune/Provincia tornano editabili
4. Possibile cercare un nuovo comune o compilare manualmente

### 9.5 Filtri e Ricerca Avanzata

**Ricerca per Provincia:**
Digitare la sigla provincia per limitare i risultati
- Esempio: "san mi" → solo comuni "san..." in provincia MI

**Ordinamento:**
Risultati ordinati alfabeticamente per nome comune

**Limite Risultati:**
Massimo 50 risultati per performance (affinare la ricerca se necessario)

---

## 10. Esportazione Dati

### 10.1 Esportazione CSV

Dalla lista anagrafiche:

1. Cliccare pulsante **"📥 Esporta CSV"** (in alto a destra)
2. Il sistema genera un file CSV con tutte le anagrafiche visibili
3. Il browser scarica il file `anagrafiche_YYYYMMDD_HHMMSS.csv`

**Dati Esportati:**
- Codice
- Tipo (PF/PG)
- Nome/Cognome o Ragione Sociale
- Codice Fiscale
- Partita IVA
- Email
- PEC
- Telefono
- Cliente (Sì/No)
- Data Creazione

**Note:**
- Il CSV rispetta i filtri applicati
- Formato UTF-8 con BOM (compatibile Excel)
- Separatore: virgola (,)
- Caratteri di escape per campi con virgole

### 10.2 Esportazione PDF Anagrafica

Dal dettaglio anagrafica:

1. Cliccare pulsante **"🖨️ Stampa"**
2. Il sistema genera un PDF professionale
3. Il PDF viene aperto in una nuova scheda del browser

**Contenuto PDF:**
- Header con logo (se configurato)
- Dati anagrafici completi
- Tutti gli indirizzi
- Tutti i contatti email
- Formattazione professionale
- Footer con data generazione

**Usi:**
- Archiviazione documenti
- Invio via email
- Stampa cartacea
- Allegato a pratiche

---

## 11. Stampe e Report

### 11.1 Stampa Anagrafica Singola

(Vedi sezione 10.2)

### 11.2 Stampa Lista Anagrafiche

**Funzionalità futura** per stampare lista completa con filtri

### 11.3 Report Statistici

**Dal pannello amministrazione Django:**

1. Accedere a `/admin/`
2. Sezione "Anagrafiche"
3. Azioni disponibili:
   - Export CSV massivo
   - Report per tipo
   - Report clienti
   - Statistiche per provincia

---

## 12. Funzioni Amministratore

### 12.1 Accesso Pannello Admin

1. Navigare a `http://[server]:8000/admin/`
2. Login con credenziali amministratore
3. Sezione **"Anagrafiche"**

### 12.2 Gestione Anagrafiche Admin

**Funzionalità disponibili:**

**Lista Anagrafiche:**
- Ricerca avanzata multi-campo
- Filtri laterali:
  - Tipo persona
  - Cliente
  - Data creazione
  - Provincia
- Azioni bulk:
  - Esporta selezionate in CSV
  - Converti in clienti
  - Elimina selezionate (con conferma)

**Dettaglio Anagrafica:**
- Modifica tutti i campi
- Visualizzazione storico modifiche
- Indirizzi inline (modifica nella stessa pagina)
- Contatti email inline
- Link a pratiche/documenti collegati

### 12.3 Gestione Comuni Italiani

**Menu Admin → Anagrafiche → Comuni Italiani:**

**Lista Comuni:**
- 7896 record
- Ricerca per: nome, CAP, codice ISTAT, provincia
- Filtri:
  - Provincia
  - Regione
  - Capoluogo
  - Attivo/Non attivo
- Paginazione: 50 per pagina

**Azioni Bulk:**
- **Attiva comuni**: riattiva comuni soppressi
- **Disattiva comuni**: disattiva comuni non più esistenti

**Dettaglio Comune:**
- Tutti i campi editabili
- Sezioni organizzate:
  - Dati Principali
  - Localizzazione
  - Coordinate GPS
  - Codici
- Visualizzazione indirizzi associati

### 12.4 Import/Update Comuni

Per aggiornare il database comuni con nuovi dati ISTAT:

**Via Management Command:**

```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py import_comuni /path/to/gi_comuni_cap.json
```

**Opzioni:**
- `--clear`: Elimina comuni esistenti prima dell'import
- `--dry-run`: Simula l'import senza salvare

**Output:**
```
Trovati 8458 record nel file JSON
Comuni unici da importare: 7896

============================================================
Import completato!
============================================================
Comuni creati:    7896
Comuni aggiornati: 0
Totale elaborati:  7896
```

### 12.5 Backup e Restore

**Backup Database:**

```bash
# Backup completo
python manage.py dumpdata anagrafiche > backup_anagrafiche.json

# Solo anagrafiche senza comuni
python manage.py dumpdata anagrafiche.Anagrafica > backup_solo_anagrafiche.json
```

**Restore:**

```bash
python manage.py loaddata backup_anagrafiche.json
```

### 12.6 Pulizia Dati

**Rimozione Duplicati:**

Via Django shell:

```python
python manage.py shell

from anagrafiche.models import Anagrafica
from django.db.models import Count

# Trova duplicati per codice fiscale
duplicates = Anagrafica.objects.values('codice_fiscale').annotate(
    count=Count('id')
).filter(count__gt=1)

for dup in duplicates:
    print(f"CF duplicato: {dup['codice_fiscale']}")
```

**Aggiornamento Massivo:**

```python
# Esempio: attiva flag cliente per anagrafiche con pratiche
from anagrafiche.models import Anagrafica
from pratiche.models import Pratica

anagrafiche_con_pratiche = Pratica.objects.values_list('cliente', flat=True).distinct()
Anagrafica.objects.filter(id__in=anagrafiche_con_pratiche).update(is_cliente=True)
```

---

## 13. API REST

### 13.1 Autenticazione

Tutte le API richiedono autenticazione JWT.

**Ottenere Token:**

```bash
curl -X POST http://[server]:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

**Risposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Usare Token:**

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  http://[server]:8000/api/v1/anagrafiche/
```

### 13.2 Endpoint Anagrafiche

**GET /api/v1/anagrafiche/**
Lista anagrafiche con filtri

Query parameters:
- `search`: ricerca testuale
- `tipo_persona`: PF o PG
- `is_cliente`: true/false
- `ordering`: campo per ordinamento
- `page`: numero pagina

Esempio:
```bash
GET /api/v1/anagrafiche/?search=rossi&tipo_persona=PF&page=1
```

**GET /api/v1/anagrafiche/{id}/**
Dettaglio anagrafica singola

Risposta include:
- Dati anagrafici completi
- Lista indirizzi
- Lista contatti email
- Dati cliente (se presente)

**POST /api/v1/anagrafiche/**
Creazione nuova anagrafica

Body (esempio Persona Fisica):
```json
{
  "tipo_persona": "PF",
  "nome": "Mario",
  "cognome": "Rossi",
  "codice_fiscale": "RSSMRA80A01F205X",
  "email": "mario.rossi@example.com",
  "is_cliente": false
}
```

**PUT /api/v1/anagrafiche/{id}/**
Aggiornamento completo anagrafica

**PATCH /api/v1/anagrafiche/{id}/**
Aggiornamento parziale anagrafica

**DELETE /api/v1/anagrafiche/{id}/**
Eliminazione anagrafica

### 13.3 Endpoint Indirizzi

**GET /api/v1/anagrafiche/{id}/indirizzi/**
Lista indirizzi di un'anagrafica

**POST /api/v1/anagrafiche/{id}/indirizzi/**
Aggiungi indirizzo

Body:
```json
{
  "tipo_indirizzo": "RES",
  "toponimo": "Via",
  "indirizzo": "Roma",
  "numero_civico": "10",
  "cap": "20121",
  "comune": "Milano",
  "provincia": "MI",
  "nazione": "IT",
  "principale": true,
  "comune_italiano": 1772
}
```

**PUT /api/v1/anagrafiche/{id}/indirizzi/{indirizzo_id}/**
Aggiorna indirizzo

**DELETE /api/v1/anagrafiche/{id}/indirizzi/{indirizzo_id}/**
Elimina indirizzo

### 13.4 Endpoint Contatti Email

**GET /api/v1/anagrafiche/{id}/contatti-email/**
Lista contatti email

**POST /api/v1/anagrafiche/{id}/contatti-email/**
Aggiungi contatto email

Body:
```json
{
  "nominativo": "Mario Rossi - Commerciale",
  "email": "commerciale@example.com",
  "tipo": "COM",
  "is_preferito": true,
  "attivo": true,
  "note": ""
}
```

### 13.5 Endpoint Comuni

**GET /api/v1/comuni/**
Ricerca comuni italiani (NO autenticazione richiesta)

Query parameters:
- `search`: testo ricerca (nome, CAP, codici)
- `provincia`: filtra per provincia
- `regione`: filtra per regione

Esempio:
```bash
GET /api/v1/comuni/?search=milano
```

Risposta:
```json
[
  {
    "id": 1772,
    "codice_istat": "015146",
    "codice_belfiore": "F205",
    "nome": "Milano",
    "provincia": "MI",
    "cap": "20121",
    "regione": "Lombardia",
    "denominazione_completa": "Milano (MI)",
    "denominazione_estesa": "Milano (MI) - CAP 20121"
  }
]
```

### 13.6 Azioni Speciali

**POST /api/v1/anagrafiche/{id}/make_cliente/**
Converte anagrafica in cliente

**POST /api/v1/anagrafiche/{id}/ricalcola_codice/**
Ricalcola codice anagrafica

Risposta:
```json
{
  "message": "Codice aggiornato con successo",
  "old_code": "CF-ROSSI-0001",
  "new_code": "CF-ROSSI-MARIO-0001",
  "unchanged": false
}
```

**GET /api/v1/anagrafiche/{id}/stampa_pdf/**
Genera PDF anagrafica

Risposta: file PDF (application/pdf)

---

## 14. Troubleshooting

### 14.1 Problemi Comuni

**Problema: "Errore di autenticazione" al login**

Soluzioni:
1. Verificare username e password corretti
2. Controllare caps lock
3. Provare logout completo e rilogin
4. Contattare amministratore per reset password

**Problema: "Codice fiscale non valido"**

Soluzioni:
1. Verificare lunghezza: 16 caratteri per PF, 11 o 16 per PG
2. Controllare caratteri validi: solo lettere maiuscole e numeri
3. Usare calcolatore codice fiscale online per verifica
4. Il sistema valida automaticamente la correttezza

**Problema: "Partita IVA non valida"**

Soluzioni:
1. Verificare lunghezza: esattamente 11 cifre
2. Solo numeri, niente lettere o caratteri speciali
3. Il sistema valida il check digit automaticamente

**Problema: "Comune italiano non trovato"**

Soluzioni:
1. Verificare di digitare almeno 2 caratteri
2. Provare con il CAP invece del nome
3. Verificare spelling (es. "san" non "s.")
4. Il comune potrebbe essere stato soppresso (compilare manualmente)

**Problema: "Email troppo lunga sborda dalla card"**

Soluzione:
- Aggiornato nella versione corrente
- Email vanno a capo automaticamente
- Aggiornare il browser (Ctrl+F5)

**Problema: "Errore salvataggio anagrafica"**

Soluzioni:
1. Controllare tutti i campi obbligatori (*)
2. Verificare formati email/PEC corretti
3. Controllare console browser (F12) per errori
4. Verificare connessione internet
5. Riprovare dopo qualche secondo

**Problema: "PDF non si genera"**

Soluzioni:
1. Verificare che popup non siano bloccati
2. Controllare connessione al server
3. Provare da browser diverso
4. Verificare log server (amministratore)

### 14.2 Limiti Sistema

**Limitazioni Tecniche:**

- **Ricerca comuni**: massimo 50 risultati (affinare ricerca)
- **Lista anagrafiche**: 20 risultati per pagina
- **Upload file**: non implementato in questa versione
- **Eliminazione**: non è possibile eliminare anagrafiche con pratiche associate

**Best Practices:**

- **Non eliminare**: preferire disattivazione
- **Backup**: esportare CSV periodicamente
- **Pulizia**: eliminare solo test o duplicati
- **Aggiornamento**: mantenere comuni aggiornati annualmente

### 14.3 Messaggi di Errore

**"Non sono state immesse le credenziali di autenticazione"**
- Token JWT scaduto
- Fare logout e login nuovamente

**"Anagrafica con questo codice già esistente"**
- Codice duplicato (raro, sistema auto-genera)
- Usare "Ricalcola Codice"

**"Impossibile eliminare: oggetto ha riferimenti"**
- Anagrafica collegata a pratiche/documenti
- Disattivare invece di eliminare

**"Validazione fallita"**
- Controllare formato campi
- Vedere dettaglio errore in rosso sotto il campo

### 14.4 Supporto

**Contatti Supporto:**

- **Email**: supporto@mygest.it
- **Telefono**: +39 XXX XXXXXXX
- **Orario**: Lun-Ven 9:00-18:00

**Documentazione Online:**
- Wiki: http://wiki.mygest.it
- FAQ: http://faq.mygest.it
- Video Tutorial: http://tutorial.mygest.it

**Richiesta Assistenza:**

Fornire sempre:
1. Username utente
2. Data e ora problema
3. Descrizione dettagliata
4. Screenshot (se possibile)
5. Browser e versione
6. Passi per riprodurre

---

## Appendici

### Appendice A: Glossario

**Anagrafica**: Scheda con dati identificativi di persona o azienda

**Cliente**: Anagrafica con flag cliente attivo e gestione avanzata

**Comune Italiano**: Comune presente nel database ISTAT (7896)

**JWT**: JSON Web Token, sistema autenticazione moderna

**API REST**: Interfaccia programmatica per integrazioni

**Codice ISTAT**: Codice univoco comune a 6 cifre

**Codice Belfiore**: Codice catastale comune a 4 caratteri

**PF**: Persona Fisica

**PG**: Persona Giuridica

**PEC**: Posta Elettronica Certificata

**CAP**: Codice Avviamento Postale

### Appendice B: Scorciatoie Tastiera

**Globali:**
- `Ctrl+K`: Focus su barra ricerca
- `Esc`: Chiudi modal/form
- `Ctrl+S`: Salva form (dove supportato)

**Lista Anagrafiche:**
- `N`: Nuova anagrafica
- `↑↓`: Naviga lista
- `Enter`: Apri dettaglio

**Form:**
- `Tab`: Campo successivo
- `Shift+Tab`: Campo precedente
- `Enter`: Salva (su alcuni campi)

### Appendice C: Codici Tipo Indirizzo

- **RES**: Residenza
- **DOM**: Domicilio
- **SLE**: Sede Legale
- **SAM**: Sede Amministrativa
- **UFI**: Ufficio
- **ALT**: Altro

### Appendice D: Codici Tipo Contatto Email

- **GEN**: Generico
- **PEC**: PEC
- **AMM**: Amministrativo
- **COM**: Commerciale
- **TEC**: Tecnico
- **ALT**: Altro

### Appendice E: Formati Dati

**Codice Fiscale PF**: 16 caratteri alfanumerici
- Esempio: RSSMRA80A01F205X

**Codice Fiscale PG**: 11 caratteri numerici
- Esempio: 12345678901

**Partita IVA**: 11 caratteri numerici
- Esempio: 01234567890

**CAP**: 5 caratteri numerici
- Esempio: 20121

**Provincia**: 2-3 caratteri alfanumerici
- Esempio: MI, BT, VB

**Telefono**: formato libero con +, -, (, ), spazi
- Esempio: +39 02 1234567, (02) 123-4567

**Email**: formato standard RFC 5322
- Esempio: nome.cognome@dominio.it

---

## Note di Versione

**Versione**: 1.0  
**Data**: 18 Novembre 2025  
**Autore**: Sistema MyGest  

**Changelog:**
- Versione iniziale documentazione
- Include tutte le funzionalità modulo Anagrafiche
- Sistema comuni italiani integrato
- API REST documentate

---

**Fine Documento**

Per assistenza: supporto@mygest.it
