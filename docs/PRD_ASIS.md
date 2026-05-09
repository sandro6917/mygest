# Product Requirements Document (PRD) - AS-IS

**Prodotto**: MyGest - Sistema di Gestione Documentale e Pratiche  
**Versione**: 2.0.1 (AS-IS - Stato Attuale)  
**Data**: 17 Marzo 2026  
**Autore**: Product Analysis Team  
**Stakeholder**: Studio Professionale, Dipendenti, Amministratori

---

## 📋 Indice

- [1. Executive Summary](#1-executive-summary)
- [2. Target Utenti](#2-target-utenti)
- [3. Scope AS-IS](#3-scope-as-is)
- [4. User Stories e User Flows](#4-user-stories-e-user-flows)
- [5. Requisiti Funzionali](#5-requisiti-funzionali)
- [6. Requisiti Non Funzionali](#6-requisiti-non-funzionali)
- [7. Modello Dati](#7-modello-dati)
- [8. UX/UI](#8-uxui)
- [9. Acceptance Criteria](#9-acceptance-criteria)
- [10. Assunzioni](#10-assunzioni)

---

## 1. Executive Summary

### 1.1 Panoramica Prodotto

**MyGest** è un sistema integrato di gestione documentale (DMS), pratiche e archivio fisico progettato per studi professionali. Il sistema implementa un workflow completo che copre:

- **Gestione Anagrafiche**: Persone fisiche e giuridiche con validazione CF/P.IVA
- **Gestione Documenti**: Upload, classificazione automatica (ML), protocollazione
- **Gestione Fascicoli**: Organizzazione gerarchica secondo titolario
- **Gestione Pratiche**: Workflow stati con relazioni padre-figlio
- **Scadenze e Alert**: Sistema ricorrente multi-canale (email, WhatsApp)
- **Archivio Fisico**: Tracciamento ubicazioni con gerarchia unità fisiche
- **Protocollazione**: Numerazione progressiva annuale documenti/fascicoli
- **AI Classifier**: Classificazione automatica documenti con ML locale

### 1.2 Valore per il Business

1. **Dematerializzazione**: Riduzione carta fisica del 70%+
2. **Compliance**: Protocollazione conforme normativa
3. **Tracciabilità**: Storia completa movimentazioni archivio fisico
4. **Automazione**: Classificazione AI documenti (riduzione tempi 60%)
5. **Alert proattivi**: Zero dimenticanze scadenze critiche (F24, tributi)

### 1.3 Stato Corrente (AS-IS)

- **Ambiente**: Produzione VPS + Sviluppo locale
- **Utenti attivi**: ~5-10 (studio professionale)
- **Documenti gestiti**: ~10.000+
- **Maturità**: Versione 2.0.1 Production-Ready con RBAC, AI avanzata, Duplicate Detection
- **Versione Backend**: Django 5.2.8 + DRF 3.15.2
- **Versione Frontend**: React 19.2 + TypeScript 5.9 + Vite 7.2
- **Release recente**: 
  - v2.0.0 (3 Marzo 2026) - RBAC completo su 13 ViewSet
  - v2.0.1 (17 Marzo 2026) - Duplicate Detection CU + Fix Type Normalization

---

## 2. Target Utenti

### 2.1 Personas

#### Persona 1: Operatore Studio
- **Ruolo**: Segretaria/Impiegato amministrativo
- **Obiettivi**:
  - Upload veloce documenti ricevuti (email, scanner)
  - Classificazione corretta secondo titolario
  - Protocollazione documenti in entrata/uscita
  - Gestione scadenze clienti (F24, tributi)
- **Pain points**:
  - Classificazione manuale richiede conoscenza titolario
  - Dimenticanza scadenze → sanzioni cliente
  - Ricerca documenti archiviati richiede tempo
- **Skills tecnici**: Base (uso PC, email, browser)

#### Persona 2: Responsabile Pratiche
- **Ruolo**: Consulente del lavoro / Commercialista
- **Obiettivi**:
  - Overview stato pratiche clienti
  - Accesso rapido a documenti/fascicoli cliente
  - Verifica protocollazione corretta
  - Export report per clienti
- **Pain points**:
  - Difficoltà monitoraggio pratiche multiple in parallelo
  - Mancanza visibilità stato archivio fisico
  - Report manuali richiedono troppo tempo
- **Skills tecnici**: Medio-alto

#### Persona 3: Amministratore Sistema
- **Ruolo**: IT Manager / Owner studio
- **Obiettivi**:
  - Configurazione tipi documento e workflow
  - Gestione utenti e permessi
  - Monitoraggio sistema e performance
  - Training modelli AI
- **Pain points**:
  - Configurazione complessa titolario/attributi
  - Manutenzione modelli ML richiede competenze
  - Backup e disaster recovery manuale
- **Skills tecnici**: Alto

### 2.2 Utenti Secondari

- **Clienti esterni**: Visibilità limitata (solo documenti propri) - **ASSUNZIONE**: Non implementato in AS-IS
- **Scanner automatici**: Integrazione via Agent Desktop

---

## 3. Scope AS-IS

### 3.1 Moduli Implementati

| Modulo | Stato | Completezza | Note |
|--------|-------|-------------|------|
| **Anagrafiche** | ✅ Completo | 100% | Validazione CF/P.IVA, import CSV |
| **Documenti** | ✅ Completo | 98% | Upload, attributi dinamici, import AI, duplicate detection |
| **Fascicoli** | ✅ Completo | 90% | Gerarchia, collegamento M2M pratiche |
| **Pratiche** | ✅ Completo | 85% | Stati, relazioni padre-figlio, note |
| **Scadenze** | ✅ Completo | 95% | Ricorrenti, alert multipli, Google Calendar sync |
| **Archivio Fisico** | ✅ Completo | 90% | Unità fisiche, operazioni, stampa etichette |
| **Protocollo** | ✅ Completo | 100% | Entrata/uscita, numerazione progressiva |
| **Comunicazioni** | ✅ Completo | 80% | Email IMAP/SMTP, PEC, tracking |
| **WhatsApp** | ⚠️ Parziale | 40% | Webhook setup, invio messaggi base |
| **AI Classifier** | ✅ Completo | 90% | Classificazione locale, extraction template, import CU |
| **Stampe** | ✅ Completo | 70% | Etichette DYMO, report PDF |
| **Help System** | ✅ Completo | 60% | Documentazione inline tipi documento |
| **RBAC** | ✅ Completo | 100% | 4 ruoli, data isolation, 13+ ViewSet protetti |

### 3.2 Feature Map (AS-IS)

```
MyGest AS-IS
│
├── Gestione Anagrafiche
│   ├── CRUD Anagrafiche (PF/PG)
│   ├── Validazione CF/P.IVA con checksum
│   ├── Generazione codice CLI automatico
│   ├── Import CSV bulk
│   ├── Gestione contatti email multipli
│   ├── Gestione indirizzi multipli
│   └── Mailing list
│
├── Gestione Documenti
│   ├── Upload file (drag-drop, scanner)
│   ├── Tipi documento configurabili
│   ├── Attributi dinamici per tipo
│   ├── Pattern nome file personalizzabile
│   ├── Classificazione automatica (AI)
│   ├── Storage NAS con path gerarchico
│   ├── Protocollazione IN/OUT
│   ├── Stati documento (bozza→definitivo→archiviato→uscito→scaricato)
│   ├── Collegamento a fascicolo
│   ├── Ubicazione fisica (documenti cartacei)
│   ├── Attributi dinamici valorizzati
│   ├── Import ZIP multiplo con AI
│   ├── Import specializzati (Cedolini, Unilav, Libro Unico, Certificazioni Uniche)
│   ├── Rilevamento duplicati configurabile per tipo (con policy: skip/replace/add)
│   ├── Duplicate detection service generico (DuplicateDetectionService)
│   ├── Type normalization per confronto attributi (fix 17 Marzo 2026)
│   └── Preview PDF inline
│
├── Gestione Fascicoli
│   ├── Creazione fascicolo con titolario
│   ├── Sottofascicoli (gerarchia parent)
│   ├── Titolario con voci intestate ad anagrafiche (HR-PERS/{CLI})
│   ├── Collegamento M2M pratiche
│   ├── Collegamento M2M fascicoli (fascicoli collegati)
│   ├── Protocollazione fascicolo IN/OUT
│   ├── Ubicazione fisica opzionale
│   ├── Stati fascicolo (corrente→storico→chiuso→deposito→archivio_deposito→scaricato)
│   ├── Path archivio NAS automatico
│   └── Retention policy (anni)
│
├── Gestione Pratiche
│   ├── CRUD pratiche con tipo
│   ├── Stati pratica (aperta→lavorazione→attesa→chiusa)
│   ├── Periodo riferimento (anno/mese/giorno)
│   ├── Relazioni padre-figlio M2M
│   ├── Note pratiche con timestamp
│   ├── Responsabile pratica
│   ├── Collegamento documenti
│   └── Tag pratiche
│
├── Scadenze
│   ├── Scadenze singole
│   ├── Scadenze ricorrenti (giornaliera/settimanale/mensile/annuale)
│   ├── Alert multipli per scadenza
│   ├── Canali alert (email, WhatsApp, notifica)
│   ├── Anticipi configurabili (giorni/ore)
│   ├── Messaggi personalizzati
│   ├── Occorrenze generate automaticamente
│   ├── Completamento occorrenze
│   ├── Calendario FullCalendar
│   ├── Scadenziario lista
│   ├── Google Calendar sync
│   └── Codici tributo F24
│
├── Archivio Fisico
│   ├── Gerarchia unità fisiche (ufficio→stanza→scaffale→...→cartellina)
│   ├── Codici auto-padded progressivi
│   ├── Operazioni archivio (versamento/prelievo/ricollocazione/scarto)
│   ├── Righe operazione (documenti/fascicoli)
│   ├── Tracciamento movimentazioni
│   ├── Stati unità (disponibile/in_uso/pieno/danneggiato/scaricato)
│   ├── Stampa etichette DYMO
│   ├── Stampa lista contenuti
│   ├── Ubicazioni descrittive
│   └── Catalogo unità
│
├── Protocollo
│   ├── Registrazione entrata documento/fascicolo
│   ├── Registrazione uscita documento/fascicolo
│   ├── Numerazione progressiva annuale
│   ├── Formato: PROT-{ANNO}-{SEQ:06d}
│   ├── Storia movimenti protocollo
│   ├── Ubicazione destinazione
│   └── Log protocollazione completo
│
├── Comunicazioni
│   ├── Invio email SMTP
│   ├── Import email IMAP
│   ├── Gestione mailbox multiple
│   ├── Allegati comunicazioni
│   ├── Blacklist email
│   ├── Salvataggio email inviate su IMAP
│   ├── Tracking email
│   └── Template messaggi
│
├── AI Classifier
│   ├── Training modelli ML locali
│   ├── Classificazione tipo documento
│   ├── Estrazione campi (template-based)
│   ├── Feedback loop per miglioramento
│   ├── Import documenti con preview AI
│   ├── Correzione predizioni
│   ├── Training job asincroni
│   └── Metriche accuracy modelli
│
└── Sistema
    ├── Autenticazione JWT
    ├── Multi-auth (JWT, Token, Session)
    ├── Dashboard statistiche
    ├── Help inline
    ├── Stampe etichette/report
    ├── Export CSV/Excel
    ├── API REST complete
    ├── GraphQL (legacy)
    └── Health check endpoints
```

### 3.3 Out of Scope (AS-IS)

❌ **Non implementato**:
- Portal clienti (accesso esterno)
- Firma digitale documenti
- OCR avanzato (solo estrazione testo base)
- Integrazione PEC nativa
- Workflow approval documenti
- Versioning documenti
- API pubbliche (tutte richiedono autenticazione)
- Mobile app nativa
- Notifiche push browser
- Chat interna
- Audit log completo (solo protocollo)
- CI/CD automatizzato
- Monitoring centralizzato (Sentry/Prometheus)

---

## 4. User Stories e User Flows

### 4.1 Epic 1: Gestione Documenti

#### US-DOC-01: Upload Documento Base
**Come** operatore studio  
**Voglio** caricare velocemente un documento ricevuto  
**Per** archiviarlo correttamente nel sistema

**Acceptance Criteria**:
- Upload file PDF/DOCX/IMG (max 50MB)
- Selezione cliente da autocomplete
- Selezione tipo documento da dropdown
- Data documento pre-compilata (oggi)
- Generazione automatica codice documento
- Salvataggio su NAS con path corretto
- Conferma visiva caricamento completato

**Flow**:
```
1. User: Naviga a "Documenti" → Click "Nuovo Documento"
2. System: Mostra form vuoto
3. User: Drag & drop file PDF
4. System: Carica file, mostra preview
5. User: Seleziona cliente (autocomplete)
6. User: Seleziona tipo "Fattura"
7. System: Mostra campi attributi dinamici (es. "Numero fattura", "Importo")
8. User: Compila attributi richiesti
9. User: Click "Salva"
10. System: Valida dati, genera codice, salva su NAS
11. System: Redirect a detail page documento
12. System: Toast "Documento creato con successo"
```

**Moduli coinvolti**: `documenti`, `anagrafiche`, `titolario`  
**API**: `POST /api/v1/documenti/`  
**Pagine**: `DocumentoFormPage.tsx`, `DocumentoDetailPage.tsx`

---

#### US-DOC-02: Protocollazione Documento
**Come** operatore studio  
**Voglio** protocollare un documento in entrata  
**Per** registrarlo ufficialmente con numero di protocollo

**Acceptance Criteria**:
- Pulsante "Protocolla" visibile solo se documento non ancora protocollato
- Selezione direzione (IN/OUT)
- Per documento cartaceo: selezione ubicazione fisica obbligatoria
- Per documento digitale: ubicazione ignorata
- Generazione numero protocollo formato PROT-2026-000123
- Impossibile ri-protocollare documento già protocollato
- Log movimento protocollo salvato

**Flow**:
```
1. User: Apre dettaglio documento
2. System: Mostra stato "Non protocollato"
3. User: Click "Protocolla"
4. System: Mostra dialog protocollazione
5. User: Seleziona direzione "IN"
6. System: Se documento cartaceo → mostra campo ubicazione
7. User: (Documento cartaceo) Seleziona ubicazione "Scaffale A - Ripiano 2"
8. User: Click "Conferma Protocollazione"
9. System: Genera numero protocollo (lock su counter)
10. System: Crea MovimentoProtocollo
11. System: Aggiorna stato documento
12. System: Chiude dialog, aggiorna UI
13. System: Mostra numero protocollo generato
```

**Moduli coinvolti**: `protocollo`, `documenti`, `archivio_fisico`  
**API**: `POST /api/v1/protocollo/movimenti/registra_entrata/`  
**Pagine**: `DocumentoDetailPage.tsx`, `ProtocollazionePopupPage.tsx`

---

#### US-DOC-03: Import Documenti AI
**Come** operatore studio  
**Voglio** importare uno ZIP con 50 cedolini  
**Per** evitare upload manuale e classificazione uno-per-uno

**Acceptance Criteria**:
- Upload file ZIP (max 100MB)
- Estrazione automatica file
- Analisi AI tipo documento per ogni file
- Estrazione automatica attributi (es. cedolino → matricola, mese)
- **Rilevamento duplicati secondo config tipo documento**
- **Badge visivo "Duplicato" per documenti già esistenti**
- **Policy duplicati configurabile (skip/replace/add)**
- Preview risultati classificazione
- Possibilità correggere classificazione errata
- Conferma bulk import
- Creazione massiva documenti
- Feedback visivo progresso (barra)

**Flow**:
```
1. User: Naviga a "Importa Documenti" → Click "Importa ZIP"
2. System: Mostra dialog upload
3. User: Seleziona file "Cedolini_2025.zip"
4. User: Click "Avvia Analisi"
5. System: Upload ZIP, crea ImportSession
6. System: Estrae file (50 PDF)
7. System: Per ogni PDF: estrai testo → ML predict tipo
8. System: Per ogni PDF: ML extract campi (matricola, mese, importo)
9. System: Mostra preview grid (50 righe)
10. User: Revisiona classificazioni
11. User: Corregge 2 classificazioni errate
12. User: Click "Conferma Import"
13. System: Bulk create 50 Documento
14. System: Salva feedback correzioni (training)
15. System: Toast "50 documenti importati con successo"
16. System: Redirect a lista documenti
```

**Moduli coinvolti**: `ai_classifier`, `documenti`  
**API**: `POST /api/v1/ai-classifier/import/start/`, `POST /api/v1/ai-classifier/import/{id}/confirm/`  
**Pagine**: `ImportSelectionPage.tsx`, `ImportDocumentPreviewPage.tsx`

---

#### US-DOC-04: Import Certificazioni Uniche (CU)
**Come** operatore studio  
**Voglio** importare uno ZIP con 30 Certificazioni Uniche dello stesso datore di lavoro  
**Per** creare automaticamente documenti CU per ogni dipendente senza inserimento manuale

**Acceptance Criteria**:
- Upload file ZIP contenente CU PDF (stesso datore di lavoro)
- Parsing automatico dati: sostituto (datore), percipiente (dipendente), dati fiscali
- **Estrazione via AI Template con coordinate zona PDF (x%, y%, width%, height%)**
- **Uso pdfplumber per bbox cropping e text extraction da zone**
- **Pulizia automatica valori estratti (prefissi numerici, label form PDF)**
- **P.IVA extraction: prende ultime 11 cifre da stringa numerica (gestisce 12 digit edge case)**
- **CF extraction: pattern regex 16 caratteri alfanumerici**
- Estrazione CF, P.IVA, importi (redditi, ritenute, addizionali, contributi)
- Creazione/match automatico anagrafiche dipendenti da CF (PF) e datore da P.IVA (PG)
- Auto-creazione Cliente per datore se non esiste (da P.IVA 11 digit)
- Auto-creazione Anagrafica per dipendente se non esiste (da CF 16 char)
- **Rilevamento duplicati dipendente+anno via DuplicateDetectionService (fix 17 Marzo)**
- **Type normalization attributi per confronto (int vs string) - fix type mismatch**
- **Badge "Duplicato" visibile in preview per CU già esistenti**
- **Policy duplicati: skip (default), replace (cancella vecchio), add (ignora check)**
- Classificazione sotto titolario HR-CU (Certificazioni Uniche)
- Opzionale: intestazione a voce titolario HR-PERS/{CLI_dipendente}
- Bulk creation documenti con attributi dinamici valorizzati
- Preview import con riassunto: tot. file, tot. dipendenti, duplicati rilevati
- Log dettagliato estrazione (DEBUG level) per troubleshooting

**Flow**:
```
1. User: Naviga a "Importa Documenti" → Click "Certificazioni Uniche"
2. System: Mostra dialog upload ZIP
3. User: Seleziona "CU_Azienda_XYZ_2025.zip" (30 PDF)
4. User: Click "Avvia Import"
5. System: Estrae file, crea ImportSession tipo='certificazioni_uniche'
6. System: Carica DocumentExtractionTemplate "CU Dipendenti/Pensionati"
7. System: Per ogni PDF:
   a. Apre PDF con pdfplumber
   b. Per ogni ExtractionTemplateZone (9 zone):
      - Calcola bbox: (x0=page_width*x%/100, y0=page_height*y%/100, x1=x0+width, y1=y0+height)
      - Croppa page: cropped_page = page.crop(bbox)
      - Estrae testo: text = cropped_page.extract_text()
      - Pulisce valore: _clean_extracted_value(text, zona)
   c. Estrae CF datore (P.IVA 11 cifre): prende ultime 11 da stringa numerica
   d. Estrae CF lavoratore (16 char): pattern regex CF
   e. Estrae cognome/nome: rimuove label "C2ognome o Denominazione", "3 NOME"
8. System: Per ogni CU:
   a. CF datore → cerca Cliente con CF=P.IVA (11 digit) o crea PG
   b. CF lavoratore → cerca Anagrafica con CF (16 char) o crea PF
9. System: Rileva duplicati (dipendente+anno già esistenti): 2/30
10. System: Mostra preview grid (30 righe, 2 con flag duplicato)
11. User: Revisiona preview, decide skip duplicati
12. User: Click "Conferma Import"
13. System: Crea 28 documenti CU (skip 2 duplicati)
14. System: Salva attributi: anno_riferimento, dipendente, redditi, ritenute, etc.
15. System: Collega a titolario HR-CU (o HR-PERS/{CLI_dipendente})
16. System: Toast "28 Certificazioni Uniche importate, 2 duplicati saltati"
17. System: Redirect a lista documenti filtrati per tipo=CU
```

**Moduli coinvolti**: `documenti` (importers.certificazioni_uniche), `ai_classifier` (views_ai_import.ExtractionService), `anagrafiche`  
**API**: `POST /api/v1/documenti/import-sessions/`, `POST /api/v1/documenti/import-sessions/{uuid}/confirm/`  
**Pagine**: `ImportSelectionPage.tsx`, `ImportDocumentsListPage.tsx`, `ImportDocumentPreviewPage.tsx`  
**Template AI**: DocumentExtractionTemplate "CU Dipendenti/Pensionati" con 9 ExtractionTemplateZone  
**Management Command**: `python manage.py setup_cu` (setup iniziale tipo documento + attributi)

---

### 4.2 Epic 2: Gestione Fascicoli

#### US-FAS-01: Creazione Fascicolo con Sottofascicoli
**Come** responsabile pratiche  
**Voglio** creare un fascicolo "Personale 2025" con sottofascicoli per dipendente  
**Per** organizzare documenti in modo gerarchico

**Acceptance Criteria**:
- Selezione cliente
- Selezione voce titolario (es. "01 - Personale")
- Generazione automatica codice fascicolo
- Creazione sottofascicolo da fascicolo padre
- Ereditarietà proprietà (cliente, titolario)
- Path NAS automatico
- Visualizzazione tree gerarchia

**Flow**:
```
1. User: Naviga a "Fascicoli" → Click "Nuovo Fascicolo"
2. User: Seleziona cliente "Azienda XYZ"
3. User: Seleziona titolario "01 - Personale"
4. User: Inserisce titolo "Personale 2025"
5. User: Click "Salva"
6. System: Genera codice "XYZ-01-2025-001"
7. System: Crea directory NAS "/mnt/archivio/XYZ/01_Personale/2025/Fascicolo_XYZ-01-2025-001/"
8. System: Redirect a detail page
9. User: Click "Crea Sottofascicolo"
10. User: Titolo "Dipendente - Mario Rossi"
11. System: Genera codice "XYZ-01-2025-001-001"
12. System: Crea subdirectory NAS
13. System: Aggiorna tree gerarchia
```

**Moduli coinvolti**: `fascicoli`, `titolario`, `anagrafiche`  
**API**: `POST /api/v1/fascicoli/`, `POST /api/v1/fascicoli/{id}/create_sottofascicolo/`  
**Pagine**: `FascicoloFormPage.tsx`, `FascicoloDetailPage.tsx`

---

### 4.3 Epic 3: Scadenze e Alert

#### US-SCA-01: Scadenza F24 Ricorrente con Alert Multipli
**Come** operatore studio  
**Voglio** creare scadenza F24 mensile per un cliente  
**Per** ricevere alert automatici via email e WhatsApp

**Acceptance Criteria**:
- Selezione tipo ricorrenza "Mensile"
- Giorno mese fisso (es. 16)
- Alert email 7 giorni prima
- Alert WhatsApp 1 giorno prima
- Generazione automatica occorrenze future (3 mesi)
- Invio automatico email/WhatsApp (cron)
- Marcatura occorrenza completata
- Sync Google Calendar opzionale

**Flow**:
```
1. User: Naviga a "Scadenze" → Click "Nuova Scadenza"
2. User: Seleziona cliente "Mario Rossi"
3. User: Titolo "F24 Mensile"
4. User: Tipo ricorrenza "Mensile"
5. User: Giorno mese "16"
6. User: Data inizio "2026-01-16"
7. User: Click "Aggiungi Alert"
8. User: Metodo "Email", giorni anticipo "7"
9. User: Destinatari "mario@example.com"
10. User: Click "Aggiungi Alert"
11. User: Metodo "WhatsApp", giorni anticipo "1"
12. User: Destinatari "+39123456789"
13. User: Click "Salva"
14. System: Crea Scadenza
15. System: Crea 2 ScadenzaAlert
16. System: Genera occorrenze (2026-01-16, 2026-02-16, 2026-03-16)
17. System: (Cron daily) Genera nuove occorrenze se necessario
18. System: (Cron hourly) Controlla occorrenze in scadenza
19. System: (7 giorni prima) Invia email a mario@example.com
20. System: (1 giorno prima) Invia WhatsApp a +39123456789
21. System: Salva ScadenzaNotificaLog
```

**Moduli coinvolti**: `scadenze`, `comunicazioni`, `whatsapp`  
**API**: `POST /api/v1/scadenze/`  
**Pagine**: `ScadenzaFormPage.tsx`, `ScadenziarioPage.tsx`, `CalendarioPage.tsx`  
**Commands**: `genera_occorrenze_scadenze`, `invia_notifiche_scadenze`

---

### 4.4 Epic 4: Archivio Fisico

#### US-ARC-01: Versamento Documenti in Archivio
**Come** operatore studio  
**Voglio** versare 10 documenti cartacei in una scatola  
**Per** tracciare la loro ubicazione fisica

**Acceptance Criteria**:
- Creazione operazione tipo "Versamento"
- Selezione unità fisica destinazione
- Aggiunta righe operazione (documenti)
- Solo documenti cartacei + tracciabili + protocollati
- Conferma operazione → aggiorna ubicazione documenti
- Stampa etichetta scatola opzionale
- Completamento operazione

**Flow**:
```
1. User: Naviga a "Archivio Fisico" → "Operazioni" → "Nuova Operazione"
2. User: Tipo "Versamento"
3. User: Data operazione (oggi)
4. User: Unità destinazione "Scaffale A - Ripiano 2 - Scatola 15"
5. User: Click "Aggiungi Documento"
6. User: Cerca documento "PROT-2026-000123"
7. System: Verifica documento cartaceo, tracciabile, protocollato
8. System: Aggiunge riga operazione
9. User: (Ripete per altri 9 documenti)
10. User: Click "Completa Operazione"
11. System: Per ogni documento: aggiorna ubicazione
12. System: Marca operazione completata
13. System: Salva data completamento
14. User: Click "Stampa Etichetta Scatola"
15. System: Genera etichetta DYMO con QR code
16. System: Invia a stampante
```

**Moduli coinvolti**: `archivio_fisico`, `documenti`, `protocollo`, `stampe`  
**API**: `POST /api/v1/archivio-fisico/operazioni/`, `POST /api/v1/archivio-fisico/operazioni/{id}/completa/`  
**Pagine**: `ArchivioFisico/OperazioneArchivioForm.tsx`, `ArchivioFisico/OperazioneArchivioDetail.tsx`

---

### 4.5 Epic 5: RBAC e Sicurezza (v2.0 - 3 Marzo 2026)

#### US-RBAC-01: Data Isolation per Operatore
**Come** administrator  
**Voglio** assegnare clienti specifici a un operatore  
**Per** garantire che veda solo i dati dei suoi clienti assegnati (GDPR compliance)

**Acceptance Criteria**:
- UserProfile con campo `assigned_clients` (M2M)
- Ruoli: ADMIN, MANAGER, OPERATORE, VIEWER
- ADMIN/MANAGER: accesso completo
- OPERATORE/VIEWER: solo dati clienti assegnati
- Filtro applicato a 13+ ViewSet critici
- API return 403 per dati non autorizzati
- UI nasconde sezioni/azioni non permesse
- Log accesso per audit trail

**Flow**:
```
1. Admin: Naviga a Django Admin → "User Profiles"
2. Admin: Seleziona user "operatore1"
3. Admin: Ruolo "OPERATORE"
4. Admin: Assigned Clients: [Cliente A, Cliente B]
5. Admin: Click "Save"
6. Operatore1: Login a MyGest
7. Operatore1: Naviga a "Documenti"
8. System: Filtra query Documento.objects.filter(cliente_id__in=[A.id, B.id])
9. System: Mostra solo 50 documenti (appartenenti a Cliente A e B)
10. Operatore1: Naviga a "Anagrafiche" → "Clienti"
11. System: Mostra solo Cliente A e Cliente B
12. Operatore1: Tenta accesso diretto API /api/v1/documenti/?cliente=C (Cliente C non assegnato)
13. System: Filtra queryset, result = [] (empty)
14. Operatore1: Tenta GET /api/v1/documenti/999/ (documento di Cliente C)
15. System: 404 Not Found (documento filtrato da RBAC)
```

**Moduli coinvolti**: `core.permissions.RBACPermission`, tutti ViewSet con filtri RBAC  
**API**: 13 ViewSet con RBAC applicato (ClienteViewSet, DocumentoViewSet, ScadenzaViewSet, ecc.)  
**Pagine**: Tutte (filtro dati lato server trasparente)  
**Models**: `core.models.UserProfile` (assigned_clients, role)

#### US-RBAC-02: Role-Based UI Actions
**Come** VIEWER  
**Voglio** visualizzare documenti senza possibilità di modifica/cancellazione  
**Per** conformità policy aziendale

**Acceptance Criteria**:
- VIEWER: solo lettura (no create/update/delete)
- OPERATORE: CRUD su clienti assegnati
- MANAGER: CRUD completo + no config sistema
- ADMIN: full access + Django admin
- Pulsanti create/edit/delete nascosti per VIEWER
- API return 403 su operazioni non permesse
- Messaggi errore user-friendly

**Flow**:
```
1. Viewer: Login a MyGest (role=VIEWER, assigned_clients=[A,B])
2. Viewer: Naviga a lista documenti
3. System: Mostra documenti Cliente A e B (read-only)
4. System: Nascondi pulsanti "Nuovo Documento", "Modifica", "Elimina"
5. Viewer: Apre dettaglio documento DOC-001
6. System: Mostra tutti campi in read-only
7. Viewer: Tenta PATCH /api/v1/documenti/DOC-001/ (via API diretta)
8. System: RBACPermission.has_object_permission() → False
9. System: Response 403 Forbidden {"detail": "You do not have permission to perform this action."}
```

**Moduli coinvolti**: `core.permissions.RBACPermission`  
**API**: Tutti ViewSet protetti  
**Pagine**: Conditional rendering pulsanti per ruolo  
**Frontend**: `useAuthStore().user.role` per UI logic

---

## 5. Requisiti Funzionali

### 5.1 Anagrafiche (APP: `anagrafiche`)

**RF-ANA-01**: Il sistema DEVE permettere creazione anagrafica con tipo Persona Fisica o Giuridica  
**RF-ANA-02**: Il sistema DEVE validare codice fiscale PF (16 caratteri alfanumerici + checksum)  
**RF-ANA-03**: Il sistema DEVE validare codice fiscale PG (11 cifre numeriche + checksum mod 10)  
**RF-ANA-04**: Il sistema DEVE generare automaticamente codice CLI (8 caratteri) se mancante  
**RF-ANA-05**: Il sistema DEVE permettere import CSV anagrafiche bulk  
**RF-ANA-06**: Il sistema DEVE supportare contatti email multipli per anagrafica  
**RF-ANA-07**: Il sistema DEVE supportare indirizzi multipli per anagrafica  
**RF-ANA-08**: Il sistema DEVE autocomplete anagrafica in tutti i form (min 2 caratteri)  
**RF-ANA-09**: Il sistema DEVE associare Cliente a Anagrafica (relazione 1:1)  
**RF-ANA-10**: Il sistema DEVE supportare mailing list con membri dinamici  

### 5.2 Documenti (APP: `documenti`)

**RF-DOC-01**: Il sistema DEVE permettere upload file (PDF, DOCX, JPG, PNG, TIFF) max 50MB  
**RF-DOC-02**: Il sistema DEVE generare codice documento univoco secondo pattern tipo documento  
**RF-DOC-03**: Il sistema DEVE salvare file su NAS con path gerarchico (CLI/Titolario/Anno/Fascicolo)  
**RF-DOC-04**: Il sistema DEVE rinominare file secondo pattern configurabile per tipo  
**RF-DOC-05**: Il sistema DEVE supportare attributi dinamici configurabili per tipo documento (STRING, INT, DECIMAL, DATE, BOOL, CHOICE)  
**RF-DOC-06**: Il sistema DEVE validare: documenti digitali NON possono avere ubicazione fisica  
**RF-DOC-07**: Il sistema DEVE validare: documenti cartacei fascicolati → ubicazione DEVE coincidere con fascicolo.ubicazione  
**RF-DOC-08**: Il sistema DEVE validare: documenti cartacei NON fascicolati → ubicazione obbligatoria  
**RF-DOC-09**: Il sistema DEVE permettere collegamento documento a fascicolo (FK opzionale)  
**RF-DOC-10**: Il sistema DEVE supportare stati documento (bozza/definitivo/archiviato/uscito/consegnato/scaricato)  
**RF-DOC-11**: Il sistema DEVE permettere protocollazione documento IN/OUT  
**RF-DOC-12**: Il sistema DEVE impedire ri-protocollazione documento già protocollato  
**RF-DOC-13**: Il sistema DEVE supportare import ZIP multiplo con classificazione AI  
**RF-DOC-14**: Il sistema DEVE supportare import specializzati: Cedolini, Unilav, Libro Unico, Certificazioni Uniche  
**RF-DOC-15**: Il sistema DEVE rilevare duplicati secondo config tipo documento (campi chiave configurabili)  
**RF-DOC-15.1**: Il sistema DEVE normalizzare valori attributi a stringa per confronto (fix type mismatch int vs string)  
**RF-DOC-15.2**: Il sistema DEVE supportare strategie duplicate match (exact_match, fuzzy, custom)  
**RF-DOC-15.3**: Il sistema DEVE supportare scope duplicati (cliente, fascicolo, anno)  
**RF-DOC-15.4**: Il sistema DEVE offrire policy duplicati (skip, replace, add)  
**RF-DOC-16**: Il sistema DEVE mostrare preview PDF inline  
**RF-DOC-17**: Il sistema DEVE validare: solo documenti tracciabili possono essere protocollati  
**RF-DOC-18**: Il sistema DEVE validare: documenti non tracciabili NON possono essere movimentati in archivio fisico  

### 5.3 Fascicoli (APP: `fascicoli`)

**RF-FAS-01**: Il sistema DEVE generare codice fascicolo univoco (CLI-TIT-ANNO-PROG)  
**RF-FAS-02**: Il sistema DEVE creare path archivio NAS automaticamente  
**RF-FAS-03**: Il sistema DEVE supportare sottofascicoli con gerarchia (parent)  
**RF-FAS-04**: Il sistema DEVE generare codice sottofascicolo (padre + sub-progressivo)  
**RF-FAS-05**: Il sistema DEVE permettere collegamento M2M fascicolo-pratiche  
**RF-FAS-06**: Il sistema DEVE permettere collegamento M2M fascicolo-fascicoli  
**RF-FAS-07**: Il sistema DEVE supportare ubicazione fisica opzionale  
**RF-FAS-08**: Il sistema DEVE protocollare fascicolo (IN/OUT)  
**RF-FAS-09**: Il sistema DEVE applicare retention policy (anni)  
**RF-FAS-10**: Il sistema DEVE impedire cancellazione fascicolo con documenti collegati  

### 5.4 Pratiche (APP: `pratiche`)

**RF-PRA-01**: Il sistema DEVE generare codice pratica secondo pattern tipo (CLI-TIPO-PER-SEQ)  
**RF-PRA-02**: Il sistema DEVE supportare periodo riferimento (anno/annomese/annomesegiorno)  
**RF-PRA-03**: Il sistema DEVE generare periodo_key automaticamente da data_riferimento  
**RF-PRA-04**: Il sistema DEVE incrementare progressivo per [cliente, tipo, periodo_key]  
**RF-PRA-05**: Il sistema DEVE supportare relazioni M2M padre-figlio via PraticaRelazione  
**RF-PRA-06**: Il sistema DEVE impedire auto-relazione pratica (parent ≠ child)  
**RF-PRA-07**: Il sistema DEVE supportare stati pratica (aperta/lavorazione/attesa/chiusa)  
**RF-PRA-08**: Il sistema DEVE supportare note pratiche con timestamp  
**RF-PRA-09**: Il sistema DEVE permettere assegnazione responsabile pratica  
**RF-PRA-10**: Il sistema DEVE supportare tag pratiche (testo libero)  

### 5.5 Scadenze (APP: `scadenze`)

**RF-SCA-01**: Il sistema DEVE supportare scadenze singole e ricorrenti  
**RF-SCA-02**: Il sistema DEVE supportare tipi ricorrenza (giornaliera/settimanale/mensile/annuale)  
**RF-SCA-03**: Il sistema DEVE generare occorrenze future automaticamente (cron daily)  
**RF-SCA-04**: Il sistema DEVE supportare alert multipli per scadenza  
**RF-SCA-05**: Il sistema DEVE supportare canali alert (email/WhatsApp/notifica)  
**RF-SCA-06**: Il sistema DEVE inviare alert secondo anticipi configurati (giorni/ore)  
**RF-SCA-07**: Il sistema DEVE loggare invio notifiche (ScadenzaNotificaLog)  
**RF-SCA-08**: Il sistema DEVE permettere completamento occorrenze  
**RF-SCA-09**: Il sistema DEVE sincronizzare scadenze con Google Calendar (opzionale)  
**RF-SCA-10**: Il sistema DEVE supportare codici tributo F24 configurabili  

### 5.6 Archivio Fisico (APP: `archivio_fisico`)

**RF-ARC-01**: Il sistema DEVE supportare gerarchia unità fisiche (ufficio→stanza→scaffale→...→cartellina)  
**RF-ARC-02**: Il sistema DEVE validare tipi figli ammessi per tipo padre  
**RF-ARC-03**: Il sistema DEVE generare codici unità auto-padded progressivi  
**RF-ARC-04**: Il sistema DEVE supportare operazioni (versamento/prelievo/ricollocazione/scarto)  
**RF-ARC-05**: Il sistema DEVE validare: solo documenti cartacei + tracciabili + protocollati in operazioni  
**RF-ARC-06**: Il sistema DEVE validare: solo fascicoli protocollati + con ubicazione in operazioni  
**RF-ARC-07**: Il sistema DEVE aggiornare ubicazione documenti/fascicoli al completamento operazione  
**RF-ARC-08**: Il sistema DEVE impedire cancellazione unità con figli  
**RF-ARC-09**: Il sistema DEVE stampare etichette DYMO per unità  
**RF-ARC-10**: Il sistema DEVE stampare lista contenuti unità  

### 5.7 Protocollo (APP: `protocollo`)

**RF-PRO-01**: Il sistema DEVE generare numero protocollo formato PROT-{ANNO}-{SEQ:06d}  
**RF-PRO-02**: Il sistema DEVE incrementare progressivo annuale con lock (concorrenza)  
**RF-PRO-03**: Il sistema DEVE supportare direzione IN/OUT  
**RF-PRO-04**: Il sistema DEVE registrare entrata documento/fascicolo  
**RF-PRO-05**: Il sistema DEVE registrare uscita documento/fascicolo  
**RF-PRO-06**: Il sistema DEVE impedire protocollazione documento non tracciabile  
**RF-PRO-07**: Il sistema DEVE ignorare ubicazione per documenti digitali  
**RF-PRO-08**: Il sistema DEVE richiedere ubicazione per documenti cartacei  
**RF-PRO-09**: Il sistema DEVE salvare MovimentoProtocollo con GenericForeignKey  
**RF-PRO-10**: Il sistema DEVE loggare utente e timestamp movimento  

### 5.8 AI Classifier (APP: `ai_classifier`)

**RF-AI-01**: Il sistema DEVE classificare tipo documento da testo estratto (ML locale)  
**RF-AI-02**: Il sistema DEVE calcolare confidence score classificazione  
**RF-AI-03**: Il sistema DEVE fornire top-N predizioni alternative  
**RF-AI-04**: Il sistema DEVE estrarre campi dinamici da template zone con coordinate bbox  
**RF-AI-05**: Il sistema DEVE supportare training modelli da TrainingExample  
**RF-AI-06**: Il sistema DEVE salvare feedback utente per miglioramento  
**RF-AI-07**: Il sistema DEVE supportare training job asincroni  
**RF-AI-08**: Il sistema DEVE salvare metriche accuracy modelli  
**RF-AI-09**: Il sistema DEVE supportare import ZIP con preview classificazione  
**RF-AI-10**: Il sistema DEVE permettere correzione manuale classificazione  
**RF-AI-11**: Il sistema DEVE supportare template multi-zona con coordinate percentuali (x%, y%, width%, height%)  
**RF-AI-12**: Il sistema DEVE estrarre testo da zone PDF usando pdfplumber con bbox cropping  
**RF-AI-13**: Il sistema DEVE pulire valori estratti da prefissi numerici e label form  
**RF-AI-14**: Il sistema DEVE estrarre P.IVA (11 cifre) e CF (16 alfanumerico) con pattern regex  
**RF-AI-15**: Il sistema DEVE mappare zone template a campi documento via ExtractionFieldMapping  

### 5.9 Comunicazioni (APP: `comunicazioni`)

**RF-COM-01**: Il sistema DEVE inviare email via SMTP  
**RF-COM-02**: Il sistema DEVE importare email da IMAP  
**RF-COM-03**: Il sistema DEVE supportare mailbox multiple  
**RF-COM-04**: Il sistema DEVE salvare allegati comunicazioni  
**RF-COM-05**: Il sistema DEVE supportare blacklist email  
**RF-COM-06**: Il sistema DEVE salvare email inviate su cartella IMAP  
**RF-COM-07**: Il sistema DEVE tracciare apertura email (opzionale)  
**RF-COM-08**: Il sistema DEVE supportare template messaggi  

### 5.10 Titolario (APP: `titolario`)

**RF-TIT-01**: Il sistema DEVE supportare gerarchia voci titolario (parent)  
**RF-TIT-02**: Il sistema DEVE validare profondità massima titolario (max 6 livelli)  
**RF-TIT-03**: Il sistema DEVE supportare pattern codice personalizzabile per voce  
**RF-TIT-04**: Il sistema DEVE permettere voci intestate ad anagrafiche  
**RF-TIT-05**: Il sistema DEVE validare: voce intestata richiede parent con `consente_intestazione=True`  
**RF-TIT-06**: Il sistema DEVE validare: voce con `consente_intestazione=True` NON può avere anagrafica  
**RF-TIT-07**: Il sistema DEVE garantire unicità anagrafica per parent  
**RF-TIT-08**: Il sistema DEVE impedire loop circolari nella gerarchia  
**RF-TIT-09**: Il sistema DEVE impedire cancellazione voce con fascicoli/documenti collegati  
**RF-TIT-10**: Il sistema DEVE generare path NAS basato su gerarchia titolario  

### 5.11 RBAC e Permessi (APP: `core`)

**RF-RBAC-01**: Il sistema DEVE supportare 4 ruoli utente (ADMIN, MANAGER, OPERATORE, VIEWER)  
**RF-RBAC-02**: Il sistema DEVE filtrare dati per `assigned_clients` (OPERATORE, VIEWER)  
**RF-RBAC-03**: Il sistema DEVE permettere accesso completo a ADMIN/MANAGER  
**RF-RBAC-04**: Il sistema DEVE applicare data isolation su 13+ ViewSet critici  
**RF-RBAC-05**: Il sistema DEVE filtrare Clienti per `id__in=accessible_clients_ids`  
**RF-RBAC-06**: Il sistema DEVE filtrare Scadenze via M2M (pratiche/fascicoli/documenti → cliente)  
**RF-RBAC-07**: Il sistema DEVE filtrare Documenti per `cliente_id__in=accessible_clients_ids`  
**RF-RBAC-08**: Il sistema DEVE filtrare MovimentiProtocollo per cliente  
**RF-RBAC-09**: Il sistema DEVE filtrare OperazioniArchivio via righe → documento/fascicolo → cliente  
**RF-RBAC-10**: Il sistema DEVE garantire GDPR compliance con data isolation  

### 5.12 Sistema (APP: `core`, `api`)

**RF-SYS-01**: Il sistema DEVE autenticare utenti con JWT (access 24h, refresh 30d)  
**RF-SYS-02**: Il sistema DEVE supportare autenticazione Token (Agent Desktop)  
**RF-SYS-03**: Il sistema DEVE supportare autenticazione Session (Django Admin)  
**RF-SYS-04**: Il sistema DEVE fornire API REST complete con paginazione  
**RF-SYS-05**: Il sistema DEVE supportare filtri, ricerca, ordinamento su tutte le liste  
**RF-SYS-06**: Il sistema DEVE fornire health check endpoints (/health, /ready, /live)  
**RF-SYS-07**: Il sistema DEVE generare statistiche dashboard  
**RF-SYS-08**: Il sistema DEVE fornire help inline per tipi documento  
**RF-SYS-09**: Il sistema DEVE supportare export CSV/Excel  
**RF-SYS-10**: Il sistema DEVE loggare operazioni protocollo con audit trail  

---

## 6. Requisiti Non Funzionali

### 6.1 Performance

**RNF-PERF-01**: Il sistema DEVE rispondere a chiamate API in < 500ms (p95)  
**RNF-PERF-02**: Il sistema DEVE supportare 10 utenti concorrenti senza degrado  
**RNF-PERF-03**: Il sistema DEVE usare caching Redis per query frequenti  
**RNF-PERF-04**: Il sistema DEVE usare connection pooling PostgreSQL (min 10, max 30)  
**RNF-PERF-05**: Il sistema DEVE ottimizzare query con select_related/prefetch_related  
**RNF-PERF-06**: Il sistema DEVE comprimere static files (WhiteNoise + Brotli)  

### 6.2 Scalabilità

**RNF-SCAL-01**: Il sistema DEVE gestire 100.000+ documenti senza degrado  
**RNF-SCAL-02**: Il sistema DEVE gestire 10.000+ anagrafiche  
**RNF-SCAL-03**: Il sistema DEVE gestire upload file fino a 50MB  
**RNF-SCAL-04**: Il sistema DEVE gestire import ZIP fino a 100MB  
**RNF-SCAL-05**: Il sistema DEVE generare occorrenze scadenze per 3 mesi futuri  

### 6.3 Sicurezza

**RNF-SEC-01**: Il sistema DEVE richiedere autenticazione per tutte le API  
**RNF-SEC-02**: Il sistema DEVE usare HTTPS in produzione  
**RNF-SEC-03**: Il sistema DEVE hashare password con algoritmo Django standard  
**RNF-SEC-04**: Il sistema DEVE gestire CORS per SPA React  
**RNF-SEC-05**: Il sistema DEVE gestire CSRF token per form  
**RNF-SEC-06**: Il sistema DEVE validare upload file (estensione, dimensione)  
**RNF-SEC-07**: Il sistema DEVE sanitizzare nomi file prima del salvataggio  

### 6.4 Affidabilità

**RNF-AFF-01**: Il sistema DEVE garantire uptime > 99% (esclusa manutenzione)  
**RNF-AFF-02**: Il sistema DEVE gestire transazioni atomiche per operazioni critiche  
**RNF-AFF-03**: Il sistema DEVE validare dati in backend (non solo frontend)  
**RNF-AFF-04**: Il sistema DEVE loggare errori con timestamp e stack trace  
**RNF-AFF-05**: Il sistema DEVE gestire failure email (fallback console in dev)  

### 6.5 Usabilità

**RNF-USA-01**: Il sistema DEVE avere UI responsive (mobile-first)  
**RNF-USA-02**: Il sistema DEVE fornire feedback visivo per operazioni async  
**RNF-USA-03**: Il sistema DEVE mostrare toast notifications per conferme/errori  
**RNF-USA-04**: Il sistema DEVE supportare autocomplete con min 2 caratteri  
**RNF-USA-05**: Il sistema DEVE mostrare breadcrumbs di navigazione  
**RNF-USA-06**: Il sistema DEVE mostrare loader durante caricamenti  

### 6.6 Manutenibilità

**RNF-MAN-01**: Il sistema DEVE avere codebase modulare per app Django  
**RNF-MAN-02**: Il sistema DEVE avere separazione frontend/backend (SPA)  
**RNF-MAN-03**: Il sistema DEVE avere migration database tracciabili  
**RNF-MAN-04**: Il sistema DEVE avere management commands per task cron  
**RNF-MAN-05**: Il sistema DEVE avere deploy automatizzato via script  

### 6.7 Compatibilità

**RNF-COMP-01**: Il sistema DEVE funzionare su browser moderni (Chrome, Firefox, Edge)  
**RNF-COMP-02**: Il sistema DEVE funzionare su PostgreSQL 12+  
**RNF-COMP-03**: Il sistema DEVE funzionare su Python 3.10+  
**RNF-COMP-04**: Il sistema DEVE funzionare su Node.js 18+  

---

## 7. Modello Dati

### 7.1 Entità Core e Relazioni

```
┌─────────────────┐
│   Anagrafica    │◄─────┐
│  (PF/PG)        │      │ 1:1
└────────┬────────┘      │
         │ 1:N           │
         ▼               │
┌─────────────────┐      │
│    Cliente      │──────┘
└────────┬────────┘
         │ 1:N
         ├─────────────┬─────────────┬──────────────┐
         ▼             ▼             ▼              ▼
┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Documento  │  │Fascicolo │  │ Pratica  │  │ Scadenza │
└─────┬───────┘  └────┬─────┘  └────┬─────┘  └──────────┘
      │               │              │
      │ N:1           │ N:1          │
      ▼               ▼              │
┌─────────────────┐                  │
│ TitolarioVoce   │◄─────────────────┘ N:1
│   (gerarchia)   │
└─────────────────┘

┌─────────────────┐
│  UnitaFisica    │
│  (gerarchia)    │
└────────┬────────┘
         │ N:1
         ├─────────────────┬──────────────┐
         ▼                 ▼              ▼
    Documento         Fascicolo    OperazioneArchivio
   (cartacei)        (opzionale)

┌─────────────────────┐
│ MovimentoProtocollo │
│  (GenericFK)        │
└─────────┬───────────┘
          │
          ▼
    Documento/Fascicolo
```

### 7.2 Entità Principali

| Entità | Chiave | Campi Critici | Constraints |
|--------|-------|---------------|-------------|
| **Anagrafica** | `id` | `codice_fiscale` (unique), `codice` (unique), `tipo` (PF/PG) | Validazione CF/P.IVA |
| **Cliente** | `id` | `anagrafica_id` (unique FK) | 1:1 con Anagrafica |
| **Documento** | `id` | `codice` (unique), `file`, `path_archivio` | Validazioni digitale/ubicazione |
| **Fascicolo** | `id` | `codice` (unique), `parent_id`, `path_archivio` | Progressivi coerenti |
| **Pratica** | `id` | `codice` (unique), `periodo_key`, `progressivo` | Unique [cliente, tipo, periodo_key, progressivo] |
| **Scadenza** | `id` | `tipo_ricorrenza`, `data_inizio` | - |
| **UnitaFisica** | `id` | `codice` (unique), `tipo`, `parent_id` | Gerarchia tipi valida |
| **MovimentoProtocollo** | `id` | `numero_protocollo` (unique), `content_type`, `object_id` | - |

### 7.3 Vincoli di Business (Database)

1. **Documento**:
   - `CHECK (digitale=true AND ubicazione_id IS NULL) OR digitale=false`
   - `CHECK tracciabile=true` per protocollazione
   
2. **Fascicolo**:
   - `CHECK (parent IS NULL AND sub_progressivo=0) OR (parent IS NOT NULL AND progressivo=0)`
   - `CHECK progressivo >= 0 AND sub_progressivo >= 0`

3. **Pratica**:
   - `UNIQUE (cliente_id, tipo_id, periodo_key, progressivo)`

4. **PraticaRelazione**:
   - `CHECK parent_id != child_id` (no auto-relazione)
   - `UNIQUE (parent_id, child_id)`

5. **UnitaFisica**:
   - Gerarchia tipi validata in `clean()`

6. **RigaOperazioneArchivio**:
   - `CHECK (documento_id IS NOT NULL) OR (fascicolo_id IS NOT NULL)`

---

## 8. UX/UI

### 8.1 Pagine Frontend (React)

| Pagina | Path | Funzionalità |
|--------|------|-------------|
| **LoginPage** | `/login` | Login JWT |
| **DashboardPage** | `/` | Dashboard statistiche |
| **AnagraficheListPage** | `/anagrafiche` | Lista anagrafiche (filtri, ricerca) |
| **AnagraficaDetailPage** | `/anagrafiche/:id` | Dettaglio anagrafica (tabs: documenti, pratiche, scadenze) |
| **AnagraficaFormPage** | `/anagrafiche/nuovo`, `/anagrafiche/:id/modifica` | Form CRUD anagrafica |
| **AnagraficheImportPage** | `/anagrafiche/import` | Import CSV anagrafiche |
| **DocumentiListPage** | `/documenti` | Lista documenti (filtri, ricerca, sorting) |
| **DocumentoDetailPage** | `/documenti/:id` | Dettaglio documento (tabs: info, attributi, protocollo, movimenti) |
| **DocumentoFormPage** | `/documenti/nuovo`, `/documenti/:id/modifica` | Form CRUD documento + upload |
| **ImportSelectionPage** | `/import/selezione` | Hub import (cedolini, unilav, ZIP generico) |
| **ImportDocumentsListPage** | `/import/sessioni` | Lista sessioni import |
| **ImportDocumentPreviewPage** | `/import/sessioni/:id` | Preview classificazione AI + conferma |
| **FascicoliListPage** | `/fascicoli` | Lista fascicoli (tree view opzionale) |
| **FascicoloDetailPage** | `/fascicoli/:id` | Dettaglio fascicolo (tabs: documenti, sottofascicoli, pratiche) |
| **FascicoloFormPage** | `/fascicoli/nuovo`, `/fascicoli/:id/modifica` | Form CRUD fascicolo |
| **PraticheListPage** | `/pratiche` | Lista pratiche (filtri per stato, cliente, tipo) |
| **PraticaDetailPage** | `/pratiche/:id` | Dettaglio pratica (tabs: info, note, documenti, relazioni) |
| **PraticaFormPage** | `/pratiche/nuovo`, `/pratiche/:id/modifica` | Form CRUD pratica |
| **ScadenzeListPage** | `/scadenze` | Lista scadenze (filtri per cliente, tipo) |
| **ScadenzaDetailPage** | `/scadenze/:id` | Dettaglio scadenza (tabs: info, alert, occorrenze) |
| **ScadenzaFormPage** | `/scadenze/nuovo`, `/scadenze/:id/modifica` | Form CRUD scadenza + alert |
| **ScadenziarioPage** | `/scadenziario` | Lista occorrenze (filtri per data, completate) |
| **CalendarioPage** | `/calendario` | FullCalendar occorrenze |
| **ArchivioPage** | `/archivio` | Tree unità fisiche + ricerca |
| **UnitaFisicaDetailPage** | `/archivio-fisico/unita/:id` | Dettaglio unità (tabs: figli, contenuti) |
| **OperazioniArchivioList** | `/archivio-fisico/operazioni` | Lista operazioni archivio |
| **OperazioneArchivioDetail** | `/archivio-fisico/operazioni/:id` | Dettaglio operazione (righe) |
| **OperazioneArchivioForm** | `/archivio-fisico/operazioni/nuovo` | Form creazione operazione + righe |
| **MovimentoProtocolloListPage** | `/protocollo` | Lista movimenti protocollo |
| **MovimentoProtocolloDetailPage** | `/protocollo/:id` | Dettaglio movimento |
| **ComunicazioniListPage** | `/comunicazioni` | Lista comunicazioni |
| **ComunicazioneDetailPage** | `/comunicazioni/:id` | Dettaglio comunicazione |
| **ComunicazioneFormPage** | `/comunicazioni/nuovo` | Form invio email |

### 8.2 Componenti UI Chiave

**Layout**:
- `MainLayout`: Sidebar + content area + breadcrumbs
- `Sidebar`: Navigazione menu collapsabile
- `Breadcrumbs`: Path navigazione automatico

**Common**:
- `LoadingSpinner`: Loader async
- `ErrorMessage`: Display errori
- `ConfirmDialog`: Conferma azioni distruttive
- `DataTable`: Tabella with sorting/filtering (MUI DataGrid)
- `SearchBar`: Ricerca testuale

**Feature-specific**:
- `AnagraficaAutocomplete`: Autocomplete anagrafica
- `DocumentiTable`: Tabella documenti con azioni
- `FascicoloTree`: Tree gerarchia fascicoli
- `PraticaCard`: Card pratica con stato
- `ScadenzaCalendar`: Calendario FullCalendar
- `UnitaFisicaSelector`: Selezione unità fisica tree

### 8.3 Stati UI

**Documento**:
- Bozza: colore grigio, azioni: modifica, protocolla, elimina
- Definitivo: colore blu, azioni: visualizza, protocolla (se non fatto)
- Archiviato: colore verde, azioni: visualizza, movimenta archivio
- Uscito: colore arancione, azioni: visualizza, registra rientro
- Consegnato: colore viola, azioni: visualizza
- Scaricato: colore rosso, read-only

**Pratica**:
- Aperta: badge verde, azioni: chiudi, modifica
- In lavorazione: badge giallo, azioni: cambia stato
- In attesa: badge arancione, azioni: cambia stato
- Chiusa: badge grigio, read-only

**Scadenza occorrenza**:
- Non completata + scaduta: rosso, alert visivo
- Non completata + futura: normale
- Completata: verde, checkbox checked

---

## 9. Acceptance Criteria

### 9.1 AC-DOC-001: Upload e Salvataggio Documento

**Given** operatore autenticato su pagina "Nuovo Documento"  
**When** seleziona file PDF "Fattura_123.pdf", cliente "Azienda XYZ", tipo "Fattura"  
**And** compila attributi "Numero fattura: 123", "Importo: 1000.00"  
**And** click "Salva"  
**Then** sistema genera codice documento "XYZ-FAT-20260303-001"  
**And** sistema salva file su NAS "/mnt/archivio/XYZ/05_Fatture/2026/FAT_1_123_20260303.pdf"  
**And** sistema redirect a detail page documento  
**And** sistema mostra toast "Documento creato con successo"  
**And** attributi salvati correttamente nel database

---

### 9.2 AC-DOC-002: Protocollazione Documento Digitale

**Given** documento digitale non protocollato aperto in detail page  
**When** click "Protocolla"  
**And** seleziona direzione "IN"  
**And** click "Conferma"  
**Then** sistema genera numero protocollo "PROT-2026-000123" (progressivo annuale)  
**And** sistema crea MovimentoProtocollo con direzione=IN, ubicazione=NULL  
**And** sistema aggiorna documento.stato_protocollo = "PROTOCOLLATO"  
**And** sistema mostra numero protocollo in UI  
**And** pulsante "Protocolla" diventa disabilitato

---

### 9.3 AC-DOC-003: Validazione Documento Digitale con Ubicazione

**Given** operatore su form "Nuovo Documento"  
**When** seleziona tipo "Fattura" (digitale=True)  
**And** seleziona cliente "XYZ"  
**And** seleziona ubicazione fisica "Scaffale A"  
**And** click "Salva"  
**Then** sistema mostra errore "I documenti digitali non possono avere ubicazione fisica"  
**And** documento NON viene salvato  
**And** form rimane aperto con errore evidenziato

---

### 9.4 AC-DOC-004: Import ZIP con Classificazione AI

**Given** operatore su pagina "Importa Documenti"  
**When** upload file "Cedolini_2025.zip" (50 PDF)  
**And** click "Avvia Analisi"  
**Then** sistema estrae 50 file  
**And** sistema classifica ogni file con AI (tipo + confidence)  
**And** sistema estrae attributi (matricola, mese, importo)  
**And** sistema mostra preview grid con 50 righe  
**When** operatore revisiona e corregge 2 classificazioni  
**And** click "Conferma Import"  
**Then** sistema crea 50 documenti  
**And** sistema salva feedback correzioni  
**And** sistema mostra toast "50 documenti importati con successo"  
**And** sistema redirect a lista documenti

---

### 9.5 AC-FAS-001: Creazione Fascicolo con Path NAS

**Given** operatore su form "Nuovo Fascicolo"  
**When** seleziona cliente "ABC", titolario "01 - Personale", anno "2025", titolo "Dipendenti"  
**And** click "Salva"  
**Then** sistema genera codice "ABC-01-2025-001"  
**And** sistema crea directory NAS "/mnt/archivio/ABC/01_Personale/2025/Fascicolo_ABC-01-2025-001/"  
**And** sistema salva path_archivio nel database  
**And** sistema redirect a detail page fascicolo

---

### 9.6 AC-FAS-002: Creazione Sottofascicolo

**Given** fascicolo padre "ABC-01-2025-001" aperto in detail page  
**When** click "Crea Sottofascicolo"  
**And** inserisce titolo "Mario Rossi"  
**And** click "Salva"  
**Then** sistema genera codice "ABC-01-2025-001-001" (padre + sub_progressivo)  
**And** sistema verifica progressivo=0, sub_progressivo=1  
**And** sistema crea subdirectory NAS "...Fascicolo_ABC-01-2025-001/Sottofascicolo_001/"  
**And** sistema aggiorna tree gerarchia in UI

---

### 9.7 AC-SCA-001: Scadenza Ricorrente con Alert

**Given** operatore su form "Nuova Scadenza"  
**When** seleziona cliente "XYZ", tipo ricorrenza "Mensile", giorno 16  
**And** aggiunge alert email 7gg prima  
**And** aggiunge alert WhatsApp 1gg prima  
**And** click "Salva"  
**Then** sistema crea Scadenza  
**And** sistema crea 2 ScadenzaAlert  
**And** sistema genera occorrenze (16/gen, 16/feb, 16/mar)  
**When** cron daily esegue "genera_occorrenze_scadenze"  
**Then** sistema genera nuove occorrenze se necessario  
**When** cron hourly esegue "invia_notifiche_scadenze" 7gg prima del 16/feb  
**Then** sistema invia email a destinatari configurati  
**And** sistema salva ScadenzaNotificaLog

---

### 9.8 AC-ARC-001: Versamento Documenti con Validazione

**Given** operatore su form "Nuova Operazione Archivio"  
**When** seleziona tipo "Versamento", unità destinazione "Scatola 15"  
**And** aggiunge documento "DOC-001" (cartaceo + protocollato + tracciabile)  
**And** tenta aggiungere documento "DOC-002" (digitale)  
**Then** sistema mostra errore "Documento digitale non movimentabile"  
**And** riga NON viene aggiunta  
**When** rimuove "DOC-002" e click "Completa Operazione"  
**Then** sistema aggiorna ubicazione "DOC-001" → "Scatola 15"  
**And** sistema marca operazione completata  
**And** sistema salva data_completamento

---

### 9.9 AC-PRO-001: Protocollazione con Lock Concorrenza

**Given** 2 operatori protocollano 2 documenti simultaneamente  
**When** operatore A click "Protocolla" su DOC-A  
**And** operatore B click "Protocolla" su DOC-B (nello stesso momento)  
**Then** sistema acquisisce lock su ProtocolloCounter  
**And** sistema assegna PROT-2026-000100 a DOC-A  
**And** sistema rilascia lock  
**And** sistema acquisisce lock per DOC-B  
**And** sistema assegna PROT-2026-000101 a DOC-B  
**And** NO duplicati numeri protocollo

---

### 9.10 AC-AI-001: Classificazione Documento con Confidence

**Given** sistema ha modello ML trained  
**When** upload PDF cedolino con testo estratto  
**Then** sistema classifica tipo="Cedolino" con confidence=0.95  
**And** sistema fornisce top-3 alternative [(Cedolino, 0.95), (Busta paga, 0.03), (Documento, 0.02)]  
**And** sistema estrae campi {matricola: "MRVLSN65", mese: "01/2025", importo: "2500.00"}  
**When** confidence < 0.7  
**Then** sistema marca predizione come "low confidence"  
**And** sistema suggerisce review manuale

---

## 10. Assunzioni

### 10.1 Assunzioni Tecniche

**ASS-TEC-01**: Il NAS `/mnt/archivio` è sempre montato e accessibile in lettura/scrittura  
**ASS-TEC-02**: Redis è sempre disponibile (fallback su cache locale non implementato)  
**ASS-TEC-03**: PostgreSQL supporta transaction isolation SERIALIZABLE per lock protocollo  
**ASS-TEC-04**: SMTP Aruba è sempre raggiungibile per invio email  
**ASS-TEC-05**: WhatsApp Cloud API ha quota messaggi sufficiente  
**ASS-TEC-06**: Google Calendar API non ha limiti rate per sync scadenze  

### 10.2 Assunzioni Business

**ASS-BUS-01**: Ogni cliente ha un codice CLI univoco generato automaticamente  
**ASS-BUS-02**: Titolario è configurato a priori (non gestito dinamicamente da utenti base)  
**ASS-BUS-03**: Tipi documento sono configurati da admin (non creabili da operatori)  
**ASS-BUS-04**: Documenti digitali possono essere protocollati senza ubicazione fisica  
**ASS-BUS-05**: Fascicoli senza ubicazione fisica sono ammessi (solo logici)  
**ASS-BUS-06**: Pratiche possono non avere fascicolo collegato  
**ASS-BUS-07**: Scadenze possono non essere collegate a cliente (scadenze generiche)  

### 10.3 Assunzioni Utente

**ASS-USR-01**: Operatori conoscono il titolario aziendale (training preliminare)  
**ASS-USR-02**: Operatori usano browser moderni (Chrome 90+, Firefox 88+)  
**ASS-USR-03**: Operatori hanno connessione Internet stabile (min 10 Mbps)  
**ASS-USR-04**: Admin ha competenze tecniche per configurare tipi documento e pattern  
**ASS-USR-05**: Operatori non modificano manualmente file su NAS (solo via UI)  

### 10.4 Assunzioni Dati

**ASS-DAT-01**: Codici fiscali sono univoci nel sistema (no duplicati)  
**ASS-DAT-02**: Import CSV anagrafiche ha header con nomi colonne standard  
**ASS-DAT-03**: File PDF sono leggibili (non corrotti, non protetti da password)  
**ASS-DAT-04**: ZIP import contiene solo file supportati (PDF, DOCX, IMG)  
**ASS-DAT-05**: Classificazione AI ha accuracy > 85% su documenti tipici  

### 10.5 Assunzioni Operative

**ASS-OPE-01**: Backup database giornaliero è eseguito esternamente (non gestito da app)  
**ASS-OPE-02**: Cron job sono configurati e attivi (scadenze, training ML)  
**ASS-OPE-03**: Deploy su VPS è manuale via script (no CI/CD)  
**ASS-OPE-04**: Monitoraggio errori è fatto via log file (no Sentry)  
**ASS-OPE-05**: Disaster recovery plan esiste ma è esterno all'app  

---

## 🎯 Conclusioni

### Stato AS-IS v2.0.1: Production-Ready Enterprise System

Il sistema MyGest nella sua configurazione attuale (AS-IS v2.0.1, 17 Marzo 2026) rappresenta un **sistema enterprise-ready** con feature di sicurezza, automazione AI e compliance GDPR complete:

✅ **Feature complete**: 98% funzionalità core implementate  
✅ **RBAC completo**: Data isolation, 4 ruoli, 13+ ViewSet protetti (v2.0.0 - 3 Marzo)  
✅ **AI avanzata**: Template extraction con coordinate, import CU automatizzato (Marzo 2026)  
✅ **Duplicate Detection**: Servizio generico con type normalization (v2.0.1 - 17 Marzo)  
✅ **Production ready**: Deploy attivo su VPS con utenti reali  
✅ **Scalabile**: Architettura pronta per crescita (100k+ documenti)  
✅ **Manutenibile**: Codebase modulare Django 5.2.8 + React 19.2  
✅ **Innovativo**: AI/ML locale per automazione (zero dipendenza cloud)

### Gap Principali vs TO-BE

Per evoluzione V2.1+ (vedi `PRD_TOBE.md`):
1. ✅ ~~**RBAC granulari**~~ - **COMPLETATO v2.0.0**
2. ✅ ~~**AI Template Extraction**~~ - **COMPLETATO v2.0.0**
3. ✅ ~~**Import CU Automatizzato**~~ - **COMPLETATO v2.0.0**
4. ✅ ~~**Duplicate Detection**~~ - **COMPLETATO v2.0.1**
5. ⏳ **Audit Log completo**: Tracciamento CRUD con diff (Target Q2 2026)
6. ⏳ **CI/CD Pipeline**: Deploy automatizzato con test (Target Q2 2026)
7. ⏳ **Monitoring**: Sentry/Prometheus/Grafana (Target Q3 2026)
8. ⏳ **Portal clienti**: Accesso limitato esterni (Target Q4 2026)
9. ⏳ **Versioning documenti**: Storico modifiche (Target Q4 2026)
10. ⏳ **Mobile app**: App nativa iOS/Android (Target Q1 2027)

### Release History

- **v2.0.0** (3 Marzo 2026): RBAC completo + AI Template + Import CU
- **v2.0.1** (17 Marzo 2026): Duplicate Detection + Type Normalization Fix
- **v2.1.0** (Target Q2-Q3 2026): Audit Log + CI/CD + Monitoring + Performance
- **v3.0.0** (Target Q4 2026-Q1 2027): Portal Clienti + Versioning + Workflow Approval

### Metriche Correnti (Marzo 2026)

| Metrica | Valore Attuale | Target v2.1 | Target v3.0 |
|---------|----------------|-------------|-------------|
| **Accuracy AI Import** | 95%+ | 97% | 98% |
| **RBAC Coverage** | 68% ViewSet | 80% | 90% |
| **Uptime** | 99% | 99.5% | 99.9% |
| **API Response Time (p95)** | <500ms | <300ms | <200ms |
| **Duplicate Detection Accuracy** | 100% | - | - |
| **Test Coverage** | ~60% | 80% | 90% |

---

**Documento approvato da**: Product Owner  
**Prossimo step**: Generazione `PRD_TOBE.md` per roadmap evolutiva  
**Riferimenti**: [ARCHITECTURE.md](ARCHITECTURE.md), [CODEBASE_MAP.md](CODEBASE_MAP.md)
