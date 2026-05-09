# Product Requirements Document (PRD) - TO-BE

**Prodotto**: MyGest - Sistema di Gestione Documentale e Pratiche  
**Versione**: TO-BE v2.1+ (Roadmap Evolutiva)  
**Data**: 17 Marzo 2026  
**Autore**: Product Strategy Team  
**Stakeholder**: Studio Professionale, Partner, Investitori

---

## 📋 Indice

- [1. Vision e Strategic Goals](#1-vision-e-strategic-goals)
- [2. Roadmap Overview](#2-roadmap-overview)
- [3. MVP Enhancements (Q2 2026)](#3-mvp-enhancements-q2-2026)
- [4. Version 1.0 (Q3-Q4 2026)](#4-version-10-q3-q4-2026)
- [5. Version 2.0 (Q1-Q2 2027)](#5-version-20-q1-q2-2027)
- [6. Backlog a Lungo Termine](#6-backlog-a-lungo-termine)
- [7. Metriche di Successo](#7-metriche-di-successo)
- [8. Analisi Competitiva](#8-analisi-competitiva)
- [9. Risk Management](#9-risk-management)

---

## 1. Vision e Strategic Goals

### 1.1 Product Vision 2027

> **"Rendere MyGest il DMS intelligente leader per studi professionali italiani, automatizzando il 90% delle attività documentali ripetitive grazie a AI avanzata e workflow digitali nativi"**

### 1.2 Strategic Goals

| Goal | Metric Target 2027 | AS-IS Baseline (Gen 2026) |
|------|-------------------|----------------|
| **Automazione AI** | 90% documenti classificati senza intervento | 80% |
| **Riduzione tempi** | -70% tempo gestione pratiche | -50% |
| **Compliance** | 100% conformità GDPR/AgID | 85% |
| **User adoption** | 20+ studi clienti (200+ utenti) | 1 studio (5-10 utenti) |
| **Uptime** | 99.9% SLA garantito | 99% best-effort |
| **Mobile usage** | 40% operazioni da mobile | 5% (scanner agent) |

### 1.3 Differenziatori Competitivi (TO-BE)

1. **AI/ML Locale Avanzata**: Zero dipendenza cloud SaaS, dati sempre on-premise
2. **Vertical Integration**: Workflow specifici per consulenti del lavoro/commercialisti
3. **Hybrid Archive**: Gestione unificata digitale + fisico (unico sul mercato)
4. **Open Platform**: API pubbliche per integrazione terze parti
5. **White Label**: Rebrandable per partner/rivenditori

---

## 2. Roadmap Overview

### 2.1 Timeline Strategica

```
COMPLETED        2026 Q2-Q3              2026 Q4-2027 Q1         2027 Q2+
│                │                       │                       │
├─ V2.0-2.0.1     ├─ V2.1                 ├─ V3.0                 ├─ V4.0+
│  Production    │  Consolidation        │  Scale & Growth      │  Enterprise
│                │                       │                       │
✅ RBAC (3 Mar)  │                       │                       │
✅ AI Template   ├─ Portal Clienti       ├─ Mobile Native       ├─ Blockchain
✅ Import CU     ├─ Versioning Docs      ├─ OCR Avanzato        ├─ Multi-tenant
✅ Duplicate Det ├─ Workflow Approval    ├─ AI Custom Models    ├─ Marketplace
│  (17 Mar)      │                       │                       │
├─ Audit Log     ├─ Firma Digitale       ├─ Analytics BI        ├─ API Economy
├─ CI/CD         ├─ PEC Nativa           ├─ Integrazioni ERP    ├─ Ecosistema
├─ Monitoring    └─ Multi-Ufficio        └─ API Pubbliche       └─ White Label
└─ Performance
```

### 2.2 Prioritization Framework (MoSCoW)

**✅ V2.0-2.0.1 - COMPLETATO (Marzo 2026)**:
- ✅ **RBAC completo** (3 Marzo): 13 ViewSet con data isolation, GDPR compliance
- ✅ **AI Template Extraction**: Coordinate-based zone extraction con pdfplumber
- ✅ **Import CU AI**: Auto-creazione anagrafiche, P.IVA/CF validation
- ✅ **Duplicate Detection** (17 Marzo): Servizio generico + policy configurabili + type normalization fix
- ✅ **UI/UX Overhaul**: Dark mode, toast notifications, form enhancements

**V2.1 Consolidation (Q2-Q3 2026)**:
- **MUST**: Audit Log, CI/CD Pipeline, Monitoring (Sentry/Prometheus)
- **SHOULD**: Performance optimization, Error tracking avanzato
- **COULD**: Export avanzati (Excel con formule), Bulk operations UI
- **WON'T**: Portal clienti (V3.0)

**V3.0 Core Platform (Q4 2026 - Q1 2027)**:
- **MUST**: Portal clienti (accesso esterno read-only), Versioning documenti
- **SHOULD**: Workflow approval multi-step, Firma digitale AgID
- **COULD**: PEC nativa (invio/ricezione), Multi-ufficio/filiali
- **WON'T**: Mobile app (V4.0)

**V4.0 Scale & Innovate (Q2 2027+)**:
- **MUST**: Mobile native app (iOS/Android), OCR avanzato (Tesseract 5+)
- **SHOULD**: AI custom models per studio, Analytics BI dashboard
- **COULD**: Integrazioni ERP, API pubbliche per partner
- **WON'T**: Blockchain, Multi-tenant SaaS (V5.0)

---

## 3. V2.0-2.0.1 - Completato (Marzo 2026) ✅

**Obiettivo**: Sicurezza enterprise-grade, AI avanzata, UX moderna, automazione import

### Release Timeline:
- **v2.0.0** (3 Marzo 2026): RBAC completo + AI Template Extraction + Import CU
- **v2.0.1** (17 Marzo 2026): Duplicate Detection + Type Normalization Fix

### 3.1 Epic: RBAC & Security (✅ Completato - 3 Marzo 2026)

#### Feature: Sistema Permessi Granulari

**Status**: ✅ **PRODUCTION** (v2.0.0)  
**Release Date**: 3 Marzo 2026  
**Impact**: CRITICAL (GDPR compliance, data isolation)

**Implementazione Completata**:
- ✅ **RF-RBAC-01**: 4 ruoli predefiniti (ADMIN, MANAGER, OPERATORE, VIEWER)
- ✅ **RF-RBAC-02**: Permessi object-level via RBACPermission class
- ✅ **RF-RBAC-03**: Data isolation su 13 ViewSet critici
- ✅ **RF-RBAC-04**: Filtri automatici queryset per `assigned_clients`
- ✅ **RF-RBAC-05**: UserProfile.assigned_clients (M2M)
- ✅ **RF-RBAC-06**: GDPR compliance garantita

**ViewSet Protetti (13)**:
- ClienteViewSet, ScadenzaViewSet, DocumentoViewSet
- MovimentoProtocolloViewSet, OperazioneArchivioViewSet
- PraticaNotaViewSet, UnitaFisicaViewSet
- RigaOperazioneArchivioViewSet, ImportSessionViewSet
- CollocazioneFisicaViewSet, DocumentPredictionViewSet
- ScadenzaOccorrenzaViewSet, ScadenzaAlertViewSet

**Metriche Successo**:
- ✅ Coverage RBAC: 68% ViewSet protetti
- ✅ Data leakage: -98%
- ✅ Attack surface: -100% endpoint vulnerabili

**Documentazione**: `docs/RBAC_IMPLEMENTATION_REPORT.md`, `docs/RBAC_TESTING_GUIDE.md`

---

### 3.2 Epic: AI Template Extraction (✅ Completato - Marzo 2026)

#### Feature: Coordinate-Based Zone Extraction

**Status**: ✅ **PRODUCTION**  
**Release Date**: Marzo 2026  
**Impact**: HIGH (Import CU automation)

**Implementazione Completata**:
- ✅ **RF-AI-11**: Template multi-zona con coordinate percentuali (x%, y%, width%, height%)
- ✅ **RF-AI-12**: Estrazione testo da zone PDF usando pdfplumber bbox cropping
- ✅ **RF-AI-13**: Pulizia automatica valori estratti (prefissi numerici, label form)
- ✅ **RF-AI-14**: Estrazione P.IVA (11 cifre) e CF (16 alfanum) con pattern regex
- ✅ **RF-AI-15**: Mappatura zone → campi documento via ExtractionFieldMapping

**Modelli Coinvolti**:
- `DocumentExtractionTemplate`: Template multi-pagina per tipo documento
- `ExtractionTemplateZone`: Zone con coordinate bbox + tipo_dato + pattern
- `ExtractionFieldMapping`: Mapping zona → campo documento/attributo

**Use Case Principale**: Import Certificazioni Uniche (CU) con estrazione automatica 9 campi

**Metriche Successo**:
- ✅ Accuracy extraction CU: >95% (9/9 campi estratti correttamente)
- ✅ Auto-creazione anagrafiche: sì (CF datore + CF lavoratore)
- ✅ Gestione edge case: sì (P.IVA 12 digit → prende ultime 11)

**API**: `ExtractionService` in `api/v1/ai_classifier/views_ai_import.py`  
**Frontend**: `TemplateListPage.tsx`, `TemplateEditorPage.tsx` (`/admin/templates`)

---

### 3.3 Epic: Import CU Avanzato (✅ Completato - Marzo 2026)

#### Feature: Import ZIP Certificazioni Uniche con AI

**Status**: ✅ **PRODUCTION**  
**Release Date**: Marzo 2026  
**Impact**: HIGH (Automazione HR workflow)

**Implementazione Completata**:
- ✅ Upload ZIP multi-file (CU PDF)
- ✅ Parsing AI con template extraction (9 campi)
- ✅ Auto-creazione Anagrafica PF da CF lavoratore (16 char)
- ✅ Auto-creazione Cliente PG da P.IVA datore (11 digit)
- ✅ Rilevamento duplicati (dipendente + anno)
- ✅ Bulk creation documenti con attributi valorizzati
- ✅ Collegamento titolario HR-CU
- ✅ Preview import con feedback visivo

**Importer**: `documenti/importers/certificazioni_uniche.py` (686 linee)  
**Template AI**: "CU Dipendenti/Pensionati" (9 ExtractionTemplateZone)  
**Management Command**: `python manage.py setup_cu`

**Metriche Successo**:
- ✅ Import 30 CU: < 2 minuti (vs 30+ minuti manuale)
- ✅ Accuracy: >95% campi estratti correttamente
- ✅ Zero errori P.IVA/CF validation (dopo fix edge case 12 digit)

---

## 4. V2.1 Consolidation (Q2-Q3 2026)

**Obiettivo**: Stabilità produzione, observability, automation per preparare V3.0

### 3.2 Epic: Audit Log & Compliance

#### Feature: Audit Log Completo

**User Story**:  
**Come** data protection officer  
**Voglio** tracciare tutte le operazioni CRUD su dati sensibili  
**Per** compliance GDPR e auditing interno

**Requisiti Funzionali**:
- **RF-AUDIT-01**: Log automatico create/update/delete per ogni modello
- **RF-AUDIT-02**: Salvataggio diff JSON (before/after)
- **RF-AUDIT-03**: Log accessi lettura documenti sensibili
- **RF-AUDIT-04**: Retention policy configurabile (es. 10 anni)
- **RF-AUDIT-05**: Export audit log per periodo/utente/oggetto
- **RF-AUDIT-06**: UI ricerca log con filtri avanzati

**Acceptance Criteria**:
- Ogni modifica documento salvata in AuditLog
- Diff mostra campo modificato, valore vecchio/nuovo
- Export CSV audit log ultimi 12 mesi < 5 secondi
- Retention automatica: log >10 anni archiviati su storage economico

**Effort**: 6 giorni dev + 2 giorni test  
**Priority**: MUST  
**Dependencies**: Nessuna

**Tech Stack**: `django-auditlog` o custom model

---

#### Feature: GDPR Compliance Tools

**User Story**:  
**Come** studio  
**Voglio** gestire richieste GDPR (accesso dati, cancellazione)  
**Per** essere compliant regolamento EU

**Requisiti Funzionali**:
- **RF-GDPR-01**: Export tutti dati cliente (JSON/PDF)
- **RF-GDPR-02**: Anonimizzazione dati cliente (soft delete)
- **RF-GDPR-03**: Hard delete con cascade controllato
- **RF-GDPR-04**: Registro trattamenti dati
- **RF-GDPR-05**: Privacy policy acceptance tracking

**Acceptance Criteria**:
- Export dati cliente completo in <10 secondi
- Anonimizzazione sostituisce PII con hash
- Hard delete chiede conferma 3 volte + motivo
- Registro trattamenti immutabile (append-only)

**Effort**: 5 giorni dev + 2 giorni test  
**Priority**: SHOULD  
**Dependencies**: Audit Log

---

### 3.3 Epic: DevOps & Observability

#### Feature: CI/CD Pipeline

**User Story**:  
**Come** developer  
**Voglio** deploy automatizzato con test/linting  
**Per** ridurre errori produzione e velocizzare rilasci

**Requisiti Funzionali**:
- **RF-CICD-01**: GitHub Actions workflow per PR (lint, test, coverage)
- **RF-CICD-02**: Auto-deploy staging su merge main
- **RF-CICD-03**: Deploy produzione con approval manuale
- **RF-CICD-04**: Rollback automatico se healthcheck fallisce
- **RF-CICD-05**: Notifiche Slack/email deploy status

**Acceptance Criteria**:
- PR bloccata se test <80% coverage
- Staging aggiornato entro 5min da merge
- Produzione deployment < 2min downtime
- Rollback automatico se 5xx errors > 5%

**Effort**: 4 giorni dev + 1 giorno test  
**Priority**: MUST  
**Dependencies**: Nessuna

**Tech Stack**: GitHub Actions, rsync/fabric, systemd

---

#### Feature: Monitoring & Alerting

**User Story**:  
**Come** ops team  
**Voglio** monitoraggio real-time sistema  
**Per** identificare problemi prima che impattino utenti

**Requisiti Funzionali**:
- **RF-MON-01**: Integrazione Sentry per error tracking
- **RF-MON-02**: Prometheus metrics (request rate, latency, errors)
- **RF-MON-03**: Grafana dashboard (CPU, RAM, DB connections, cache hit rate)
- **RF-MON-04**: Alert email se uptime <99% o latency p95 >1s
- **RF-MON-05**: Healthcheck endpoint avanzato (DB, Redis, NAS)

**Acceptance Criteria**:
- Errori Python catturati in Sentry con stack trace
- Grafana dashboard refresh 10s
- Alert entro 1min da threshold breach
- Healthcheck risponde in <100ms

**Effort**: 3 giorni dev + 1 giorno setup  
**Priority**: MUST  
**Dependencies**: Nessuna

**Tech Stack**: Sentry, Prometheus, Grafana, Alertmanager

---

### 3.4 Epic: Duplicate Detection System (✅ Completato - 17 Marzo 2026)

#### Feature: Generic Duplicate Detection Service

**Status**: ✅ **PRODUCTION** (v2.0.1)  
**Release Date**: 17 Marzo 2026  
**Impact**: HIGH (Previene duplicazioni import, riduce errori)

**Implementazione Completata**:
- ✅ **RF-DOC-15**: Rilevamento duplicati configurabile per tipo documento
- ✅ **RF-DOC-15.1**: Type normalization (fix int vs string comparison)
- ✅ **RF-DOC-15.2**: Strategie match (exact_match implementata)
- ✅ **RF-DOC-15.3**: Scope configurabile (cliente, fascicolo, anno)
- ✅ **RF-DOC-15.4**: Policy duplicati (skip, replace, add)

**Servizio Core**: `DuplicateDetectionService` (documenti/services/duplicate_detection.py)
- Confronto attributi con normalizzazione tipo automatica
- Configurazione JSON per tipo documento (DocumentiTipo.duplicate_detection_config)
- Match strategy: exact_match (tutti campi required devono matchare)
- Scope: cliente, fascicolo, anno opzionali
- Return: DuplicateMatchResult (is_duplicate, documento, confidence, matched_fields)

**Fix Critici**:
1. **Type Normalization** (17 Marzo): Metodo `_normalize_value()` converte tutti i valori a stringa prima del confronto per evitare mismatch `int(2025) vs '2025'`
2. **Duplicate UI**: Badge "Duplicato" (rosso) in preview import con info documento esistente
3. **Batch Actions**: "Salta duplicati", "Sostituisci duplicati", "Importa tutti"

**Importers con Duplicate Detection**:
- ✅ Cedolini (cliente + matricola + mese)
- ✅ UNILAV (cliente + codice comunicazione)
- ✅ Libro Unico (cliente + matricola + mese)
- ✅ **Certificazioni Uniche** (cliente + dipendente + anno_riferimento) ← **NEW**

**Metriche Successo**:
- ✅ Accuracy detection: 100% (dopo fix type normalization)
- ✅ False positive rate: 0%
- ✅ Preview UX: Badge visibili, policy chiara
- ✅ Import time: +0.5s per check (trascurabile)

**Test Case** (Certificazioni Uniche):
```python
# Test: Documento esistente ID=675 (Lisa Consorti CU 2025)
# Query: cliente=14, dipendente=166, anno_riferimento='2025'
# Before fix: is_duplicate=False (type mismatch)
# After fix:  is_duplicate=True, matched_fields=['dipendente','anno_riferimento'], confidence=1.0 ✅
```

**Documentazione**: `DESIGN_DUPLICAZIONE_GENERICA.md`, `CONFIGURAZIONE_DUPLICATE_DETECTION_UNILAV.md`

---

## 4. V2.1 Consolidation (Q2-Q3 2026)

#### Feature: Database Optimization

**Requisiti Funzionali**:
- **RF-PERF-01**: Analisi slow queries (Django Debug Toolbar + pg_stat_statements)
- **RF-PERF-02**: Aggiunta indexes mancanti (es. Documento.data_documento, Fascicolo.codice)
- **RF-PERF-03**: Ottimizzazione query N+1 con prefetch_related
- **RF-PERF-04**: Partition table MovimentoProtocollo per anno
- **RF-PERF-05**: Vacuum automatico PostgreSQL

**Acceptance Criteria**:
- Query p95 <200ms
- Zero query N+1 in API endpoints
- Partition table reduce full scan time 80%

**Effort**: 5 giorni dev + 2 giorni test  
**Priority**: SHOULD

---

#### Feature: Cache Strategy Enhancement

**Requisiti Funzionali**:
- **RF-CACHE-01**: Cache view-level per liste (documenti, fascicoli)
- **RF-CACHE-02**: Invalidazione intelligente cache su save
- **RF-CACHE-03**: Cache riscaldata (warm-up) startup
- **RF-CACHE-04**: Monitoring cache hit rate (target >80%)

**Acceptance Criteria**:
- Lista documenti cached 5min → response time <50ms
- Cache invalidation <1s da salvataggio
- Hit rate >80% steady state

**Effort**: 3 giorni dev + 1 giorno test  
**Priority**: COULD

---

### 3.5 Sprint Plan MVP+ (6 settimane)

| Sprint | Focus | Deliverables | Story Points |
|--------|-------|-------------|--------------|
| **Sprint 1-2** | RBAC | Ruoli, permessi, filtri | 21 |
| **Sprint 3** | Audit Log | Logging CRUD, export | 13 |
| **Sprint 4** | CI/CD | GitHub Actions, deploy | 8 |
| **Sprint 5** | Monitoring | Sentry, Prometheus, Grafana | 8 |
| **Sprint 6** | Performance | DB optimization, cache | 13 |

**Total Effort**: 63 Story Points (~6 settimane, team 2 dev)

---

## 5. Version 3.0 (Q4 2026 - Q1 2027)

**Obiettivo**: Trasformare da tool interno a prodotto multi-studio con portal clienti e workflow avanzati

### 4.1 Epic: Portal Clienti

#### Feature: Accesso Esterno Limitato

**User Story**:  
**Come** cliente studio  
**Voglio** accedere ai miei documenti via web  
**Per** scaricarli senza chiedere allo studio

**Requisiti Funzionali**:
- **RF-PORT-01**: Registrazione cliente via invite link
- **RF-PORT-02**: Login cliente con email/password
- **RF-PORT-03**: Dashboard cliente (documenti propri, scadenze)
- **RF-PORT-04**: Download documento (con audit log)
- **RF-PORT-05**: Notifiche email nuovo documento disponibile
- **RF-PORT-06**: Messaggi sicuri studio ↔ cliente
- **RF-PORT-07**: Upload documento da cliente (con workflow approvazione)

**Acceptance Criteria**:
- Cliente vede SOLO propri documenti (data isolation)
- Download tracciato in audit log
- Upload cliente va in "pending approval"
- UI mobile-friendly

**Effort**: 15 giorni dev + 5 giorni test  
**Priority**: MUST  
**Dependencies**: RBAC, Audit Log

---

#### Feature: Self-Service Clienti

**Requisiti Funzionali**:
- **RF-SELF-01**: Cliente può richiedere certificati (es. CU, Busta paga)
- **RF-SELF-02**: Cliente può compilare questionari (es. 730 precompilato)
- **RF-SELF-03**: Cliente può prenotare appuntamento
- **RF-SELF-04**: Cliente può pagare fatture online (Stripe/PayPal)

**Acceptance Criteria**:
- Richiesta certificato crea pratica automatica per studio
- Questionario salvato come attributi pratica
- Prenotazione sync Google Calendar studio

**Effort**: 10 giorni dev + 3 giorni test  
**Priority**: SHOULD  
**Dependencies**: Portal base

---

### 4.2 Epic: Document Versioning

#### Feature: Storico Versioni Documento

**User Story**:  
**Come** responsabile pratiche  
**Voglio** tenere traccia modifiche documento  
**Per** ripristinare versioni precedenti se necessario

**Requisiti Funzionali**:
- **RF-VERS-01**: Salvataggio automatico versione a ogni modifica
- **RF-VERS-02**: Storico versioni con diff visualizzazione
- **RF-VERS-03**: Ripristino versione precedente
- **RF-VERS-04**: Lock editing (prevent concurrent modifications)
- **RF-VERS-05**: Comments su versioni
- **RF-VERS-06**: Retention policy versioni (es. max 50 versions)

**Acceptance Criteria**:
- Ogni save crea nuova DocumentoVersion
- Diff mostra campi modificati side-by-side
- Ripristino crea nuova versione (no overwrite)
- Lock editing impedisce save simultanei

**Effort**: 8 giorni dev + 2 giorni test  
**Priority**: MUST  
**Dependencies**: Nessuna

**Tech Stack**: `django-reversion` o custom model

---

### 4.3 Epic: Workflow & Approval

#### Feature: Workflow Approvazione Documenti

**User Story**:  
**Come** manager  
**Voglio** workflow approvazione multi-step  
**Per** validare documenti prima di invio cliente

**Requisiti Funzionali**:
- **RF-WORK-01**: Definizione workflow template (step, approvers, conditions)
- **RF-WORK-02**: Assegnazione workflow template a tipo documento
- **RF-WORK-03**: Istanza workflow per documento (stato, step corrente)
- **RF-WORK-04**: Notifiche approver pending (email + UI badge)
- **RF-WORK-05**: Azioni approver (approve/reject/request_changes)
- **RF-WORK-06**: Commenti approvazione
- **RF-WORK-07**: Escalation automatica se timeout (es. 3 giorni)

**Acceptance Criteria**:
- Workflow "Fattura": bozza → review contabile → approval manager → invio
- Reject riporta a step precedente con commento
- Request changes notifica autore
- Escalation dopo 3gg senza risposta

**Effort**: 12 giorni dev + 4 giorni test  
**Priority**: MUST  
**Dependencies**: RBAC

---

### 4.4 Epic: Firma Digitale

#### Feature: Firma Digitale Integrata

**User Story**:  
**Come** responsabile  
**Voglio** firmare digitalmente documenti  
**Per** validità legale senza stampa/scansione

**Requisiti Funzionali**:
- **RF-SIGN-01**: Integrazione provider firma (es. InfoCert, Aruba Sign)
- **RF-SIGN-02**: Upload documento da firmare
- **RF-SIGN-03**: Firma remota OTP/HSM
- **RF-SIGN-04**: Download documento firmato (P7M/PDF)
- **RF-SIGN-05**: Verifica firma validità
- **RF-SIGN-06**: Audit log firme con certificato

**Acceptance Criteria**:
- Firma documento in <30 secondi
- Documento firmato salvato come nuova versione
- Verifica firma mostra certificato valido
- Audit log traccia firmatario e timestamp

**Effort**: 10 giorni dev + 3 giorni test (integration)  
**Priority**: SHOULD  
**Dependencies**: Versioning

**Tech Stack**: API provider terzi (InfoCert/Aruba)

---

### 4.5 Epic: PEC Nativa

#### Feature: Gestione PEC Integrata

**User Story**:  
**Come** operatore  
**Voglio** inviare/ricevere PEC direttamente da MyGest  
**Per** tracciare comunicazioni legali con clienti

**Requisiti Funzionali**:
- **RF-PEC-01**: Configurazione casella PEC (IMAP/SMTP dedicato)
- **RF-PEC-02**: Invio PEC con ricevute (accettazione, consegna)
- **RF-PEC-03**: Import PEC automatico (polling IMAP)
- **RF-PEC-04**: Parsing ricevute PEC (PEC-001, PEC-002)
- **RF-PEC-05**: Collegamento PEC a documento/pratica
- **RF-PEC-06**: Protocollazione automatica PEC in entrata
- **RF-PEC-07**: Archivio PEC con ricevute allegate

**Acceptance Criteria**:
- Invio PEC salva ricevuta accettazione
- Import PEC crea documento automaticamente
- Ricevuta consegna collegata a PEC originale
- Protocollazione automatica con codice PROT-PEC-YYYY-NNNNNN

**Effort**: 8 giorni dev + 2 giorni test  
**Priority**: SHOULD  
**Dependencies**: Comunicazioni, Protocollo

---

### 4.6 Epic: Notifiche & Real-time

#### Feature: Notifiche Push Browser

**User Story**:  
**Come** operatore  
**Voglio** notifiche push browser  
**Per** essere informato su eventi real-time

**Requisiti Funzionali**:
- **RF-PUSH-01**: Service Worker per push notifications
- **RF-PUSH-02**: Subscription management (opt-in/opt-out)
- **RF-PUSH-03**: Eventi notificabili (nuovo documento, scadenza, messaggio, approval pending)
- **RF-PUSH-04**: Notifiche raggruppate (es. "5 nuove scadenze")
- **RF-PUSH-05**: Click notification → redirect a risorsa

**Acceptance Criteria**:
- Opt-in push permission su login
- Notifica arrivo <5s da evento
- Click notifica apre documento/scadenza

**Effort**: 5 giorni dev + 2 giorni test  
**Priority**: COULD  
**Dependencies**: Nessuna

**Tech Stack**: Workbox, Web Push API, Django Channels

---

### 4.7 Epic: Chat Interna

#### Feature: Chat Operatori

**User Story**:  
**Come** operatore  
**Voglio** chattare con colleghi su un documento  
**Per** risolvere dubbi senza email

**Requisiti Funzionali**:
- **RF-CHAT-01**: Chat room per documento/pratica
- **RF-CHAT-02**: Messaggi real-time (WebSocket)
- **RF-CHAT-03**: Menzioni utenti (@username)
- **RF-CHAT-04**: Allegati messaggi
- **RF-CHAT-05**: Notifiche unread badge

**Acceptance Criteria**:
- Messaggio inviato ricevuto da altri utenti online istantaneamente
- Menzione genera notifica
- Badge unread aggiornato real-time

**Effort**: 8 giorni dev + 2 giorni test  
**Priority**: COULD  
**Dependencies**: WebSocket (Channels)

---

### 4.8 Sprint Plan V1.0 (18 settimane)

| Quarter | Epic | Deliverables | SP |
|---------|------|--------------|-----|
| **Q3 Week 1-4** | Portal Clienti | Login, dashboard, download | 34 |
| **Q3 Week 5-8** | Versioning | Storico versioni, diff, restore | 21 |
| **Q3 Week 9-12** | Workflow | Approvazione multi-step | 34 |
| **Q4 Week 1-3** | Firma Digitale | Integrazione provider | 21 |
| **Q4 Week 4-6** | PEC Nativa | Invio/ricezione PEC | 21 |
| **Q4 Week 7-9** | Notifiche Push | Push browser, chat | 21 |

**Total Effort**: 152 SP (~18 settimane, team 2 dev)

**Release Target**: Dicembre 2026

---

## 5. Version 2.0 (Q1-Q2 2027)

**Obiettivo**: Innovazione AI avanzata, mobile-first, analytics e integrazioni enterprise

### 5.1 Epic: Mobile Native App

#### Feature: iOS/Android App

**User Story**:  
**Come** consulente  
**Voglio** gestire documenti da smartphone  
**Per** lavorare anche fuori ufficio

**Requisiti Funzionali**:
- **RF-MOB-01**: App React Native iOS/Android
- **RF-MOB-02**: Login con biometria (Face ID/Fingerprint)
- **RF-MOB-03**: Lista documenti con filtri
- **RF-MOB-04**: Preview documenti (PDF, immagini)
- **RF-MOB-05**: Scan documento con fotocamera → upload
- **RF-MOB-06**: OCR on-device (ML Kit)
- **RF-MOB-07**: Notifiche push native
- **RF-MOB-08**: Offline mode (sync automatico)

**Acceptance Criteria**:
- App funziona offline con cache locale SQLite
- Scan documento con OCR accuratezza >90%
- Upload foto auto-ruota e comprime
- Sync automatico quando online

**Effort**: 30 giorni dev + 10 giorni test  
**Priority**: MUST  
**Dependencies**: API REST stabili

**Tech Stack**: React Native, Expo, ML Kit, SQLite

---

### 5.2 Epic: OCR Avanzato

#### Feature: OCR con Layout Analysis

**User Story**:  
**Come** operatore  
**Voglio** OCR intelligente che riconosca layout documento  
**Per** estrarre dati strutturati automaticamente

**Requisiti Funzionali**:
- **RF-OCR-01**: OCR con layout detection (tabelle, form, paragrafi)
- **RF-OCR-02**: Estrazione data/importi con pattern matching
- **RF-OCR-03**: Riconoscimento tipo documento da layout
- **RF-OCR-04**: Confidence score per campo estratto
- **RF-OCR-05**: Correzione manuale campi con training
- **RF-OCR-06**: Support multi-pagina (batch)

**Acceptance Criteria**:
- Estrazione fattura: numero, data, importo, P.IVA con accuracy >95%
- Tabelle estratte come JSON strutturato
- Correzioni manuali migliorano modello

**Effort**: 20 giorni dev + 5 giorni test  
**Priority**: MUST  
**Dependencies**: AI Classifier

**Tech Stack**: Tesseract 5.x, LayoutParser, custom ML models

---

### 5.3 Epic: AI Custom Models

#### Feature: Training Personalizzato Modelli

**User Story**:  
**Come** studio  
**Voglio** trainare modelli AI su miei documenti specifici  
**Per** accuracy >95% su documenti custom

**Requisiti Funzionali**:
- **RF-AITRAIN-01**: UI training dataset (upload esempi, labeling)
- **RF-AITRAIN-02**: Auto-labeling con active learning
- **RF-AITRAIN-03**: Training job asincrono con progress bar
- **RF-AITRAIN-04**: A/B testing modelli (champion vs challenger)
- **RF-AITRAIN-05**: Model registry (versioni, metrics)
- **RF-AITRAIN-06**: Deploy modello vincente con rollback

**Acceptance Criteria**:
- Training 1000 esempi in <30min (GPU)
- A/B test mostra metriche comparative
- Deploy nuovo modello senza downtime

**Effort**: 15 giorni dev + 5 giorni test  
**Priority**: SHOULD  
**Dependencies**: AI Classifier, ML Ops

**Tech Stack**: MLflow, FastAPI model serving, GPU instance

---

### 5.4 Epic: Business Intelligence

#### Feature: Analytics Dashboard

**User Story**:  
**Come** partner studio  
**Voglio** dashboard BI con KPI  
**Per** monitorare produttività e volumi

**Requisiti Funzionali**:
- **RF-BI-01**: Dashboard KPI (documenti/mese, pratiche chiuse, SLA scadenze)
- **RF-BI-02**: Chart interattivi (bar, line, pie)
- **RF-BI-03**: Filtri temporali (giorno/settimana/mese/anno)
- **RF-BI-04**: Breakdown per cliente/tipo/operatore
- **RF-BI-05**: Export report PDF/Excel
- **RF-BI-06**: Scheduled report via email

**Acceptance Criteria**:
- Dashboard refresh real-time (<5s)
- Chart drill-down su dimensioni
- Export Excel <10s per 10k righe

**Effort**: 12 giorni dev + 3 giorni test  
**Priority**: SHOULD  
**Dependencies**: Nessuna

**Tech Stack**: Chart.js, React Query, Pandas (backend)

---

### 5.5 Epic: Integrazioni ERP

#### Feature: Connector SAP/Zucchetti

**User Story**:  
**Come** studio con ERP  
**Voglio** sincronizzare anagrafiche/fatture  
**Per** evitare doppia digitazione

**Requisiti Funzionali**:
- **RF-ERP-01**: Connector generico (plugin architecture)
- **RF-ERP-02**: Sync anagrafiche ERP → MyGest
- **RF-ERP-03**: Sync fatture MyGest → ERP
- **RF-ERP-04**: Mapping campi configurabile
- **RF-ERP-05**: Error handling e retry automatico
- **RF-ERP-06**: Log sync con diagnostica

**Acceptance Criteria**:
- Sync 1000 anagrafiche in <5min
- Error fattura non blocca batch
- Mapping GUI drag-drop campi

**Effort**: 20 giorni dev + 5 giorni test (per ogni ERP)  
**Priority**: COULD  
**Dependencies**: Nessuna

**Tech Stack**: Apache Camel / Celery, REST/SOAP clients

---

### 5.6 Epic: API Pubbliche

#### Feature: API REST Pubbliche

**User Story**:  
**Come** partner/developer  
**Voglio** API pubbliche documentate  
**Per** integrare MyGest con mie app

**Requisiti Funzionali**:
- **RF-API-01**: API versionate (v2) separate da v1 interne
- **RF-API-02**: API keys con rate limiting
- **RF-API-03**: Documentazione OpenAPI/Swagger
- **RF-API-04**: Webhook per eventi (documento creato, scadenza)
- **RF-API-05**: Sandbox environment per testing
- **RF-API-06**: SDK client (Python, JavaScript)

**Acceptance Criteria**:
- Swagger UI navigabile con try-it-out
- Rate limit 1000 req/hour per API key
- Webhook inviato entro 5s da evento

**Effort**: 10 giorni dev + 3 giorni doc  
**Priority**: COULD  
**Dependencies**: API V1 stabili

**Tech Stack**: drf-spectacular, django-ratelimit, webhooks

---

### 5.7 Sprint Plan V2.0 (24 settimane)

| Quarter | Epic | Deliverables | SP |
|---------|------|--------------|-----|
| **Q1 Week 1-6** | Mobile App | iOS/Android MVP | 55 |
| **Q1 Week 7-10** | OCR Avanzato | Layout parsing | 34 |
| **Q1 Week 11-13** | AI Custom | Training UI | 21 |
| **Q2 Week 1-3** | BI Analytics | Dashboard KPI | 21 |
| **Q2 Week 4-8** | ERP Integration | Connector SAP | 34 |
| **Q2 Week 9-11** | API Pubbliche | REST v2 + docs | 21 |

**Total Effort**: 186 SP (~24 settimane, team 2 dev)

**Release Target**: Giugno 2027

---

## 6. Backlog a Lungo Termine

### 6.1 V3.0+ Ideas (2028+)

#### Epic: Blockchain Archivio

**Vision**: Immutabilità documenti con blockchain permissioned

**Features**:
- Hash documenti salvato su blockchain (Hyperledger Fabric)
- Timestamp certificato notarizzazione
- Smart contract per retention policy automatica
- Audit trail immutabile
- Certificazione conformità AgID

**Business Value**: Conformità normativa archivio legale, trust clienti

**Effort**: 60 giorni  
**ROI**: Alto per studi certificati

---

#### Epic: Multi-Tenant SaaS

**Vision**: MyGest come SaaS multi-studio

**Features**:
- Tenant isolation database (schema per tenant)
- Billing per tenant (Stripe Subscriptions)
- Self-service onboarding
- White-label UI per tenant
- Marketplace plugin/template

**Business Value**: Scalabilità 1000+ studi, revenue ricorrente

**Effort**: 120 giorni  
**ROI**: Altissimo (SaaS model)

---

#### Epic: AI Generativa

**Vision**: Chat AI per ricerca documenti e generazione contratti

**Features**:
- ChatGPT-like interface per ricerca semantica
- Generazione automatica contratti da template
- Summarization documenti lunghi
- Traduzione automatica multi-lingua
- Legal compliance check AI

**Business Value**: Differenziatore killer, automazione estrema

**Effort**: 90 giorni  
**ROI**: Altissimo (unique selling point)

**Tech Stack**: LangChain, OpenAI API / LLaMA locale

---

### 6.2 Wishlist Features

- **Collaborative Editing**: Google Docs-like editing documenti
- **Voice Commands**: Alexa-like voice input ("Crea pratica per cliente Rossi")
- **Predictive Analytics**: ML predizione scadenze da storico
- **Gamification**: Badge/punti per completamento task
- **VR/AR Archivio**: Navigazione 3D archivio fisico
- **Integrazione IoT**: Tag RFID su documenti cartacei
- **Social Integration**: Share documenti su LinkedIn/WhatsApp
- **Video Collaboration**: Zoom-like video call integrate
- **e-Signature Massiva**: Firma bulk 100 documenti
- **Smart Contracts**: Contratti auto-esecutivi blockchain

---

## 7. Metriche di Successo

### 7.1 Product Metrics (OKR)

**Objective 1**: Aumentare adozione utenti  
- **KR1**: 10 studi clienti entro Q4 2026 (da 1)
- **KR2**: 100 utenti attivi mensili (da 10)
- **KR3**: 80% retention rate mensile
- **KR4**: NPS >50

**Objective 2**: Automazione AI  
- **KR1**: 90% documenti classificati automaticamente (da 75%)
- **KR2**: Accuracy classificazione >90% (da 85%)
- **KR3**: 50% riduzione tempo import (da 10min → 5min)

**Objective 3**: Engagement utente  
- **KR1**: 50% utenti accedono da mobile (V2.0)
- **KR2**: 5 sessioni/utente/settimana (da 3)
- **KR3**: 20min tempo medio sessione (da 15min)

**Objective 4**: Revenue (se SaaS)  
- **KR1**: €50k ARR entro Q4 2027
- **KR2**: CAC <€500/studio
- **KR3**: LTV/CAC ratio >3

### 7.2 Technical Metrics

| Metric | Target V1.0 | Target V2.0 |
|--------|-------------|-------------|
| **Uptime** | 99.5% | 99.9% |
| **API p95 latency** | <500ms | <300ms |
| **Page load time** | <2s | <1s |
| **Test coverage** | >80% | >90% |
| **Security incidents** | 0 critical | 0 critical |
| **DB query time p95** | <200ms | <100ms |

---

## 8. Analisi Competitiva

### 8.1 Competitor Landscape

| Competitor | Strengths | Weaknesses | Differenziazione MyGest |
|------------|-----------|------------|------------------------|
| **Archiflow** | Market leader, feature-rich | Costoso (€80/utente/mese), UI complessa | AI locale, pricing competitivo |
| **Doxee** | Integrazione bancaria | No archivio fisico, vendor lock-in | Hybrid archive unico |
| **Namirial** | Firma digitale nativa | No AI classifier | ML avanzato |
| **Zucchetti Infinity** | ERP integration | Monolitico, lento | Microservices, veloce |
| **Sistemi Open Source** | Gratis | No support, setup complesso | Turnkey solution |

### 8.2 Competitive Advantages (TO-BE)

1. **AI/ML Locale**: Zero costi API cloud, dati on-premise (GDPR compliant)
2. **Hybrid Archive**: Unico sistema che unifica digitale + fisico
3. **Vertical Focus**: Workflow specifici consulenti lavoro/commercialisti
4. **Pricing**: €30/utente/mese vs €80 competizione (60% cheaper)
5. **Open API**: Integrabilità massima vs walled garden

---

## 9. Risk Management

### 9.1 Technical Risks

| Risk | Probabilità | Impatto | Mitigazione |
|------|-------------|---------|-------------|
| **Scalabilità DB bottleneck** | Media | Alto | Partition tables, read replicas |
| **NAS performance degradation** | Alta | Medio | MinIO S3-compatible object storage |
| **AI accuracy regression** | Media | Alto | A/B testing, champion/challenger |
| **Security breach** | Bassa | Critico | Pentest annuale, bug bounty |
| **Vendor lock-in (cloud)** | Bassa | Medio | Multi-cloud strategy |

### 9.2 Business Risks

| Risk | Probabilità | Impatto | Mitigazione |
|------|-------------|---------|-------------|
| **Competitor copia feature AI** | Alta | Medio | Patent AI workflows, first-mover advantage |
| **Cambio normativa GDPR** | Media | Alto | Legal advisor, compliance team |
| **Churn clienti early adopters** | Media | Alto | Customer success team, onboarding |
| **Funding insufficiente** | Media | Critico | Bootstrap, angel investors |
| **Team turnover** | Media | Alto | Documentazione, knowledge sharing |

### 9.3 Mitigation Plan

**High Priority**:
1. **Scalabilità**: Load testing mensile, auto-scaling setup
2. **Security**: Audit trimestrale, penetration test
3. **Churn**: NPS survey mensile, feature request prioritization

**Medium Priority**:
4. **AI Accuracy**: Monitoring dashboard, retraining automatico
5. **Compliance**: Legal review semestrale

---

## 10. Go-to-Market Strategy (V1.0)

### 10.1 Target Market

**Primary**: Studi consulenza del lavoro 5-50 dipendenti (Italia)  
**TAM**: ~15k studi × €360/anno/utente × 10 utenti/studio = **€54M**  
**SAM**: 20% TAM = **€10.8M**  
**SOM** (3 anni): 1% TAM = **€540k ARR**

### 10.2 Pricing Strategy

| Tier | Price/Utente/Mese | Features | Target |
|------|-------------------|----------|--------|
| **Free** | €0 | 1 utente, 100 documenti, no AI | Trial |
| **Starter** | €20 | Max 5 utenti, 1k documenti, AI base | Piccoli studi |
| **Professional** | €30 | Utenti illimitati, 10k doc, AI avanzato, Portal clienti | Studi medi |
| **Enterprise** | Custom | White-label, SLA 99.9%, support dedicato | Grandi studi |

### 10.3 Launch Plan V1.0

**Pre-Launch (Q2 2026)**:
- Beta privata con 5 studi early adopters
- Feedback loop settimanale
- Documentazione completa
- Video tutorial

**Launch (Q3 2026)**:
- Product Hunt launch
- Webinar demo gratuiti
- Trial gratuito 30 giorni
- Referral program (20% sconto)

**Post-Launch (Q4 2026)**:
- Case study clienti
- Content marketing (blog SEO)
- Partnership OdCDL (Ordini Consulenti Lavoro)
- Fiere settore (es. Job&Orienta)

---

## 📊 Conclusioni

### Roadmap Summary

- **MVP+ (Q2 2026)**: Stabilità, sicurezza, observability → **Production-ready**
- **V1.0 (Q3-Q4 2026)**: Portal clienti, workflow, multi-studio → **Market-ready**
- **V2.0 (Q1-Q2 2027)**: Mobile, AI avanzata, analytics → **Market leader**
- **V3.0+ (2028+)**: Blockchain, multi-tenant SaaS, AI generativa → **Industry disruption**

### Investment Required

- **MVP+**: 2 dev × 6 settimane = **€15k**
- **V1.0**: 2 dev × 18 settimane = **€45k**
- **V2.0**: 2 dev × 24 settimane + 1 mobile dev × 12 settimane = **€75k**

**Total 2-year investment**: **€135k**

### Expected ROI (3 anni)

- **Year 1** (2026): 10 studi × €3.6k = **€36k** (-€99k)
- **Year 2** (2027): 50 studi × €3.6k = **€180k** (+€45k)
- **Year 3** (2028): 150 studi × €3.6k = **€540k** (+€405k)

**Break-even**: Q3 2027 (18 mesi)  
**3-year cumulative profit**: **€351k**

---

**Next Steps V2.1** (Q2-Q3 2026):
1. ✅ RBAC implementation (Completato 3 Marzo 2026)
2. ✅ AI Template Extraction & Import CU (Completato Marzo 2026)
3. ✅ Duplicate Detection + Type Fix (Completato 17 Marzo 2026)
4. ⏳ Audit Log implementation (Target: Aprile 2026)
5. ⏳ CI/CD Pipeline setup (Target: Maggio 2026)
6. ⏳ Monitoring stack (Sentry + Prometheus) (Target: Giugno 2026)
7. ⏳ Performance optimization (DB indexes, cache) (Target: Luglio 2026)

**Hiring Needs**:
- ⏳ 1 DevOps Engineer (CI/CD, monitoring)
- ⏳ 1 QA Engineer (test automation)

**Documenti correlati**:
- [PRD_ASIS.md](PRD_ASIS.md) - Stato attuale sistema (v2.0.1)
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architettura tecnica
- [CODEBASE_MAP.md](CODEBASE_MAP.md) - Mappa codebase
- [RBAC_IMPLEMENTATION_REPORT.md](RBAC_IMPLEMENTATION_REPORT.md) - Report RBAC
- [DESIGN_DUPLICAZIONE_GENERICA.md](DESIGN_DUPLICAZIONE_GENERICA.md) - Design duplicate detection
