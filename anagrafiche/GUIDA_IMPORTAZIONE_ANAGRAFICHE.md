# Guida all'Importazione Anagrafiche da CSV

## Panoramica

La funzionalità di importazione anagrafiche consente di caricare massivamente i dati anagrafici tramite file CSV, con validazione automatica e report dettagliato delle operazioni.

## Accesso alla Funzionalità

1. Accedi alla sezione **Anagrafiche** del sistema
2. Clicca su **Importazione** nel menu
3. URL: `/anagrafiche/import/`

## Formato del File CSV

### Specifiche Tecniche

- **Separatore**: `;` (punto e virgola)
- **Encoding**: UTF-8 (con BOM) o Latin-1
- **Formato**: CSV standard con header nella prima riga
- **Estensione**: `.csv`

### Campi Disponibili

#### Header del CSV (obbligatorio):
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
```

#### Descrizione dei Campi:

| Campo | Tipo | Obbligatorio | Descrizione | Esempio |
|-------|------|--------------|-------------|---------|
| **tipo** | Testo | ✅ Sì | Tipo soggetto: `PF` (Persona Fisica) o `PG` (Persona Giuridica) | `PF` |
| **ragione_sociale** | Testo | Solo per PG | Denominazione della società/ente | `Acme S.r.l.` |
| **nome** | Testo | Solo per PF | Nome della persona fisica | `Mario` |
| **cognome** | Testo | Solo per PF | Cognome della persona fisica | `Rossi` |
| **codice_fiscale** | Testo | ✅ Sì | Codice fiscale (16 car. per PF, 11 cifre per PG) | `RSSMRA80A01H501U` |
| **partita_iva** | Testo | No | Partita IVA (11 cifre) | `12345678901` |
| **codice** | Testo | No | Codice cliente (auto-generato se vuoto) | `CLI0001` |
| **denominazione_abbreviata** | Testo | No | Denominazione breve (max 15 caratteri senza spazi) | `ROSSI MARIO` |
| **pec** | Email | No | Indirizzo PEC | `mario.rossi@pec.it` |
| **email** | Email | No | Indirizzo email normale | `mario@email.it` |
| **telefono** | Testo | No | Numero di telefono | `3331234567` |
| **indirizzo** | Testo | No | Indirizzo completo | `Via Roma 1, Milano` |
| **note** | Testo | No | Annotazioni varie | `Cliente preferenziale` |

### Regole di Validazione

#### Campi Obbligatori per Tipo:

**Persona Fisica (PF)**:
- ✅ tipo = "PF"
- ✅ nome
- ✅ cognome
- ✅ codice_fiscale (16 caratteri)
- ❌ ragione_sociale (deve essere vuoto)

**Persona Giuridica (PG)**:
- ✅ tipo = "PG"
- ✅ ragione_sociale
- ✅ codice_fiscale (11 cifre)
- ❌ nome (deve essere vuoto)
- ❌ cognome (deve essere vuoto)

#### Validazioni Specifiche:

1. **Codice Fiscale**:
   - PF: 16 caratteri alfanumerici con checksum valido
   - PG: 11 cifre numeriche con checksum valido (algoritmo P.IVA)
   - Deve essere univoco nel database

2. **Partita IVA**:
   - 11 cifre numeriche
   - Validazione checksum secondo l'algoritmo ufficiale
   - Deve essere univoca se presente

3. **PEC**:
   - Formato email valido
   - Deve essere univoca se presente

4. **Email**:
   - Formato email valido

5. **Codice Cliente**:
   - Se lasciato vuoto, viene auto-generato dal sistema
   - Se fornito, deve essere univoco

## Esempi di Righe CSV

### Esempio 1: Persona Fisica Completa
```csv
PF;;Mario;Rossi;RSSMRA80A01H501U;;CLI0001;ROSSI MARIO;mario.rossi@pec.it;mario.rossi@email.it;3331234567;Via Roma 1, 20121 Milano;Cliente preferenziale
```

### Esempio 2: Persona Fisica Minima
```csv
PF;;Anna;Verdi;VRDNNA85M45F205X;;;;anna.verdi@pec.it;;;Corso Italia 45;
```

### Esempio 3: Persona Giuridica Completa
```csv
PG;Acme S.r.l.;;;12345678901;12345678901;CLI0002;ACME SRL;acme@pec.it;info@acme.it;024567890;Via Milano 10, 20100 Milano;Cliente importante
```

### Esempio 4: Persona Giuridica Minima
```csv
PG;Beta Solutions S.p.A.;;;98765432109;;;;;;contatti@beta.com;;Piazza Duomo 1;
```

## File di Esempio

È disponibile un file CSV di esempio completo:
- **File**: `esempio_importazione_anagrafiche.csv`
- **Percorso**: `/anagrafiche/esempio_importazione_anagrafiche.csv`
- **Download**: Dalla pagina di importazione, clicca su "Fac-simile CSV"

## Processo di Importazione

### 1. Preparazione del File

1. Crea o modifica il file CSV seguendo il formato specificato
2. Assicurati che:
   - La prima riga contenga l'header
   - I campi siano separati da `;`
   - I campi obbligatori siano compilati correttamente
   - Non ci siano duplicati di codice fiscale, P.IVA o PEC

### 2. Caricamento

1. Accedi alla pagina di importazione
2. Clicca su "Scegli file" e seleziona il tuo CSV
3. Clicca su "Importa Anagrafiche"

### 3. Elaborazione

Il sistema elaborerà ogni riga del CSV e:
- Verificherà la presenza dei campi obbligatori
- Validerà il formato di tutti i campi
- Controllerà l'univocità di codice fiscale, P.IVA e PEC
- Applicherà le regole di business del modello Anagrafica

### 4. Report

Al termine dell'elaborazione verrà mostrato un report dettagliato con:

#### Statistiche Generali:
- **Righe totali**: numero di righe processate (escluso header)
- **Importate**: numero di anagrafiche create con successo
- **Scartate**: numero di righe non importate

#### Dettaglio Importazioni Riuscite:
Per ogni anagrafica importata:
- Numero riga nel CSV
- Nome/Ragione sociale
- Codice fiscale
- Link per visualizzare i dettagli

#### Dettaglio Righe Scartate:
Per ogni riga scartata:
- Numero riga nel CSV
- Dati parziali della riga
- **Motivi dello scarto** (lista completa degli errori)

## Motivi Comuni di Scarto

### Errori di Validazione Base

❌ **Campo 'tipo' mancante**
- Soluzione: Inserire "PF" o "PG"

❌ **Tipo 'XX' non valido**
- Soluzione: Usare solo "PF" o "PG"

❌ **Campo 'codice_fiscale' mancante**
- Soluzione: Compilare sempre il codice fiscale

❌ **Campo 'nome' obbligatorio per Persona Fisica**
- Soluzione: Per tipo=PF, compilare nome e cognome

❌ **Campo 'ragione_sociale' obbligatorio per Persona Giuridica**
- Soluzione: Per tipo=PG, compilare ragione_sociale

### Errori di Duplicazione

❌ **Codice fiscale 'XXXXXXX' già presente nel database**
- Soluzione: Verificare che il codice fiscale non sia già stato importato
- Nota: Il sistema impedisce duplicati per garantire l'integrità dei dati

❌ **Partita IVA 'XXXXXXXXXXX' già presente nel database**
- Soluzione: Controllare che la P.IVA non sia già registrata
- Nota: Puoi lasciare il campo vuoto se la P.IVA non è necessaria

❌ **PEC 'email@pec.it' già presente nel database**
- Soluzione: Usare un indirizzo PEC diverso o lasciare il campo vuoto

### Errori di Formato

❌ **codice_fiscale: Codice fiscale (persona fisica) non valido**
- Soluzione: Verificare che il codice fiscale PF abbia 16 caratteri e checksum corretto
- Tool online: Usa un validatore di codice fiscale

❌ **codice_fiscale: Codice fiscale numerico/Partita IVA non valido**
- Soluzione: Per PG, verificare che abbia 11 cifre e checksum corretto

❌ **partita_iva: Partita IVA non valida**
- Soluzione: Verificare che abbia 11 cifre e checksum corretto

❌ **pec: Inserisci un indirizzo email valido**
- Soluzione: Verificare il formato dell'indirizzo PEC

## Best Practices

### ✅ Prima dell'Importazione

1. **Scarica il file di esempio** e usalo come template
2. **Valida i dati** in un foglio di calcolo prima di esportare in CSV
3. **Fai un backup** del database prima di importazioni massive
4. **Testa con poche righe** prima di importare centinaia di record
5. **Usa codici fiscali validi** (verifica con tool online)

### ✅ Durante la Compilazione

1. **Non modificare l'header** del CSV
2. **Rispetta i separatori** (`;` non `,`)
3. **Lascia vuoti i campi non applicabili** (es: ragione_sociale per PF)
4. **Non usare virgolette** a meno che il campo contenga il separatore
5. **Mantieni coerenza** nei formati (es: telefono sempre con o senza prefisso)

### ✅ Dopo l'Importazione

1. **Leggi attentamente il report**
2. **Correggi le righe scartate** nel CSV originale
3. **Re-importa solo le righe corrette** (crea un nuovo CSV con le righe scartate)
4. **Verifica nel database** che i dati siano corretti
5. **Documenta eventuali anomalie** per migliorare il processo

## Risoluzione Problemi

### Problema: "Il file non viene accettato"
**Cause possibili**:
- Formato non CSV
- File corrotto
- Encoding non supportato

**Soluzioni**:
1. Salva come CSV UTF-8 con BOM
2. Usa un editor di testo per verificare il contenuto
3. Prova a salvare con encoding Latin-1

### Problema: "Tutte le righe vengono scartate"
**Cause possibili**:
- Header mancante o errato
- Separatore sbagliato (`,` invece di `;`)
- Campi obbligatori vuoti

**Soluzioni**:
1. Confronta l'header con quello del file di esempio
2. Verifica il separatore nel CSV
3. Controlla che tipo e codice_fiscale siano sempre compilati

### Problema: "Codici fiscali validi vengono rifiutati"
**Cause possibili**:
- Spazi bianchi prima/dopo il codice
- Caratteri minuscoli (vengono convertiti automaticamente)
- Codici fiscali già presenti

**Soluzioni**:
1. Rimuovi spazi bianchi all'inizio e alla fine
2. Verifica nel database se il codice fiscale esiste già
3. Controlla il checksum del codice fiscale

### Problema: "Importazione lenta con molti record"
**Raccomandazioni**:
- Dividi il file in batch di 100-500 righe
- Importa in orari di basso traffico
- Monitora il report per ogni batch

## Supporto Tecnico

Per assistenza:
1. Consulta questa documentazione
2. Verifica i messaggi di errore nel report
3. Contatta l'amministratore di sistema con:
   - File CSV problematico
   - Screenshot del report
   - Descrizione dettagliata del problema

## Changelog

### Versione 1.0 (Dicembre 2025)
- ✅ Implementazione iniziale
- ✅ Validazione completa campi
- ✅ Report dettagliato importazioni/scarti
- ✅ Controllo duplicati (CF, P.IVA, PEC)
- ✅ Supporto UTF-8 e Latin-1
- ✅ File di esempio scaricabile
- ✅ Documentazione completa
