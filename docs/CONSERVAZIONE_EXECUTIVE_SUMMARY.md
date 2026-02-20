# Conservazione Digitale a Norma - Executive Summary

## Sintesi per Decision Maker

### Cos'è la Conservazione Digitale a Norma?

È il processo che garantisce **validità legale permanente** ai documenti digitali attraverso:
- **Integrità**: Il documento non può essere modificato
- **Autenticità**: Certezza su chi ha creato il documento e quando
- **Leggibilità**: Garanzia di lettura nel tempo (anche tra 10-30 anni)

### Normativa di Riferimento

- **CAD** (Codice Amministrazione Digitale)
- **DPCM 3 dicembre 2013** (Regole tecniche)
- **Linee Guida AgID 2021**
- **Regolamento eIDAS** (UE)

---

## Architettura Soluzione Proposta

### Nuova App Django: `conservazione`

```
MyGest (attuale)
    ├── documenti/          [ESISTENTE]
    ├── fascicoli/          [ESISTENTE]
    ├── anagrafiche/        [ESISTENTE]
    └── conservazione/      [NUOVA] ← App dedicata
```

**Perché una app separata?**
1. **Isolamento**: Logica complessa separata dal core
2. **Manutenibilità**: Facile aggiornare per nuove normative
3. **Opzionalità**: Attivabile solo se necessario
4. **Certificabilità**: Più facile ottenere audit/certificazioni

---

## Workflow Semplificato

```
1. Utente seleziona documenti da conservare
   ↓
2. Sistema crea Pacchetto di Versamento (PdV)
   ↓
3. Conversione automatica in PDF/A
   ↓
4. Calcolo hash (impronta digitale)
   ↓
5. Firma digitale (con token USB)
   ↓
6. Marca temporale (timestamp certificato)
   ↓
7. Pacchetto PRONTO per conservazione
   ↓
8. Conservazione permanente (archivio sicuro)
```

**Durata processo**: 5-10 minuti per pacchetto (automatico)

---

## Componenti Tecnici Necessari

### 1. Modelli Database

| Modello | Scopo |
|---------|-------|
| **PacchettoVersamento** | Contenitore documenti da conservare |
| **DocumentoConservazione** | Documento singolo in formato conservativo |
| **LottoConservazione** | Raggruppa più pacchetti |
| **VerificaIntegrita** | Log verifiche periodiche obbligatorie |
| **EventoConservazione** | Audit trail (tracciamento azioni) |

### 2. Servizi di Integrazione

| Servizio | Fornitore | Costo Annuale |
|----------|-----------|---------------|
| **Firma Digitale** | ArubaPEC / InfoCert | €40-50 |
| **Marca Temporale** | ArubaPEC / InfoCert | €0.08-0.10 per marca |
| **Conservatore** (opzionale) | ArchiWorld / Namirial | €500-700 |

**Stima costi**: 
- Startup: ~€500
- Annuale: ~€100-200 (se gestito internamente)
- Annuale: ~€600-900 (con conservatore esterno)

### 3. Software Richiesto

| Software | Scopo | Installazione |
|----------|-------|---------------|
| **Ghostscript** | Conversione PDF/A | `apt install ghostscript` |
| **VeraPDF** | Validazione PDF/A | Download da sito |
| **OpenSSL** | Firma e crittografia | Già presente |
| **Celery** | Task automatici | `pip install celery` |
| **Redis** | Queue per Celery | `apt install redis` |

---

## Features Principali

### Per l'Utente

1. **Dashboard Conservazione**
   - Lista documenti conservabili
   - Stato pacchetti
   - Storico conservazioni

2. **Creazione Guidata PdV**
   - Selezione documenti per periodo
   - Anteprima pacchetto
   - Conferma e invio

3. **Verifica e Ricerca**
   - Ricerca documenti conservati
   - Download con marca temporale
   - Verifica integrità on-demand

### Per l'Amministratore

1. **Gestione Lotti**
   - Creazione lotti periodici (es: trimestrale)
   - Versamento massivo
   - Report statistici

2. **Monitoring**
   - Stato firma digitale (scadenza certificato)
   - Verifiche integrità automatiche
   - Alert anomalie

3. **Audit e Compliance**
   - Log completo operazioni
   - Report conformità AgID
   - Export per controlli esterni

---

## Processo Operativo Tipo

### Scenario: Conservazione Fatture Trimestre

**Input**: 150 fatture del Q1 2025

**Step**:
1. Utente: "Crea PdV fatture Q1 2025"
2. Sistema: Seleziona fatture gennaio-marzo
3. Sistema: Converte in PDF/A (automatico)
4. Sistema: Calcola hash di ogni file
5. Utente: "Sigilla pacchetto"
6. Sistema: Chiede inserimento token USB
7. Sistema: Firma + marca temporale
8. Sistema: Genera rapporto versamento PDF
9. **RISULTATO**: Pacchetto conservato validità 10+ anni

**Tempo richiesto**: ~10 minuti
**Costo**: 1 marca temporale (€0.10)

---

## Conformità Normativa

### Requisiti Obbligatori ✅

- [x] **Identificazione univoca**: UUID per ogni documento
- [x] **Integrità**: Hash SHA-256
- [x] **Immodificabilità**: Firma digitale qualificata
- [x] **Marcatura temporale**: Timestamp certificato
- [x] **Formato conservativo**: PDF/A-2b
- [x] **Metadati obbligatori**: XML secondo standard AgID
- [x] **Indice conservazione**: XML per ogni PdV
- [x] **Rapporto versamento**: PDF firmato
- [x] **Verifiche periodiche**: Ogni 90 giorni (automatico)
- [x] **Audit trail**: Log di tutte le operazioni

### Responsabilità

**Responsabile della Conservazione** (figura obbligatoria):
- Deve essere nominato formalmente
- Supervisiona processo conservazione
- Firma rapporti versamento
- Risponde di conformità normativa

**Suggerimento**: Nominare titolare studio/direttore amministrativo

---

## Timeline Implementazione

### Fase 1: Setup Base (Settimane 1-2)
- Creazione app `conservazione`
- Modelli database
- Migrazioni
- Admin panel base

### Fase 2: Servizi Core (Settimane 3-4)
- Conversione PDF/A
- Calcolo hash
- Generazione metadati XML
- Creazione pacchetti ZIP

### Fase 3: Firma e Marca (Settimana 5)
- Integrazione firma digitale
- Integrazione marca temporale
- Test con fornitori

### Fase 4: Workflow (Settimana 6)
- Processo completo creazione PdV
- Sigillatura automatica
- Rapporto versamento

### Fase 5: UI/UX (Settimana 7)
- Dashboard conservazione
- Form guidati
- Ricerca e verifica

### Fase 6: Testing e Deploy (Settimana 8)
- Test completi
- Validazione conformità
- Deploy produzione
- Formazione utenti

**TOTALE: 8 settimane (~2 mesi)**

---

## Costi di Implementazione

### Sviluppo

| Voce | Stima Ore | Costo (€50/h) |
|------|-----------|---------------|
| Analisi e design | 20 | €1.000 |
| Sviluppo modelli | 40 | €2.000 |
| Servizi integrazione | 60 | €3.000 |
| UI/Frontend | 30 | €1.500 |
| Testing e debug | 30 | €1.500 |
| Deploy e docs | 20 | €1.000 |
| **TOTALE** | **200h** | **€10.000** |

### Servizi Esterni (Annuali)

| Servizio | Costo |
|----------|-------|
| Firma digitale (token USB) | €50 |
| Marche temporali (~500/anno) | €50 |
| Certificato SSL (se serve) | €0-100 |
| **TOTALE Anno 1** | €100-200 |

**Opzionale**: Conservatore accreditato (+€500-700/anno)

### Hardware

| Componente | Costo |
|------------|-------|
| Token USB firma digitale | Incluso |
| Server storage (se serve upgrade) | Variabile |

---

## Vantaggi Business

### 1. Conformità Legale
- ✅ Documenti validi legalmente a tempo indeterminato
- ✅ Nessun rischio sanzionatorio
- ✅ Pronto per audit fiscali

### 2. Risparmio Costi
- 💰 Elimina archivio cartaceo
- 💰 Riduce spazio fisico necessario
- 💰 Nessun costo spedizione/conservazione fisica

### 3. Efficienza Operativa
- ⚡ Ricerca istantanea documenti
- ⚡ Zero rischio smarrimento
- ⚡ Accesso remoto sicuro

### 4. Valore Aggiunto
- 🎯 Servizio premium per clienti
- 🎯 Differenziazione competitiva
- 🎯 Aumenta valore percepito

### 5. Scalabilità
- 📈 Gestione illimitata documenti
- 📈 Costi marginali bassissimi
- 📈 Processo totalmente automatizzato

---

## ROI (Return on Investment)

### Scenario: Studio con 50 clienti

**Costi Tradizionali (cartaceo)**:
- Archivio fisico: €2.000/anno (affitto spazio)
- Gestione documenti: 10h/mese × €30/h × 12 = €3.600/anno
- Rischio smarrimento/danno: Quantificabile
- **TOTALE**: ~€5.600/anno

**Costi Conservazione Digitale**:
- Sviluppo (one-time): €10.000
- Servizi annuali: €200/anno
- **TOTALE Anno 1**: €10.200
- **TOTALE Anni successivi**: €200/anno

**Break-even**: ~2 anni
**Risparmio da anno 3**: €5.400/anno

---

## Rischi e Mitigazioni

### Rischi Tecnici

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Perdita dati | Bassa | Alto | Backup giornaliero + NAS |
| Errore firma | Media | Alto | Test estensivi + fallback |
| Bug software | Media | Medio | Test automatici + review |
| Marca temporale fallita | Bassa | Medio | Retry automatico |

### Rischi Normativi

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Cambio normativa | Media | Medio | Monitoring AgID + update |
| Non conformità | Bassa | Alto | Checklist + audit periodici |
| Certificato scaduto | Media | Alto | Alert automatici 30gg prima |

### Rischi Operativi

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Utente non formato | Alta | Basso | Formazione + wizard guidato |
| Token USB perso | Media | Medio | Backup token + procedura revoca |
| Fornitore cambia servizio | Bassa | Medio | Contratto + alternative |

---

## Raccomandazioni

### Priorità Alta (Must Have)

1. ✅ **Implementare app `conservazione`**
   - Fondamentale per conformità
   - Valore aggiunto clienti
   - Ammortizzabile in 2 anni

2. ✅ **Automatizzare verifiche integrità**
   - Obbligatorio per normativa
   - Riduce rischi
   - Zero overhead operativo

3. ✅ **Audit trail completo**
   - Richiesto in caso di controlli
   - Dimostra conformità
   - Tracciabilità totale

### Priorità Media (Should Have)

4. 🔶 **Integrazione con conservatore accreditato**
   - Opzionale ma consigliato
   - Maggiore sicurezza legale
   - Costo contenuto (€500-700/anno)

5. 🔶 **Dashboard analytics**
   - KPI conservazione
   - Report automatici
   - Insight operativi

### Priorità Bassa (Nice to Have)

6. ⚪ **Mobile app**
   - Accesso da smartphone
   - Verifica documenti in mobilità
   - Fase 2 sviluppo

7. ⚪ **AI per categorizzazione**
   - Auto-classificazione documenti
   - Suggerimenti metadati
   - Innovazione futura

---

## Decision Matrix

### Opzione A: Sviluppo Completo In-House

**PRO**:
- ✅ Controllo totale processo
- ✅ Personalizzazione massima
- ✅ Zero costi ricorrenti (dopo sviluppo)
- ✅ Competenza interna

**CONTRO**:
- ❌ Investimento iniziale alto (€10k)
- ❌ Responsabilità conformità interna
- ❌ Richiede competenze tecniche

**COSTO TOTALE 3 ANNI**: €10.600
**BEST FOR**: Studi strutturati, 50+ clienti

### Opzione B: Conservatore Esterno + Integrazione

**PRO**:
- ✅ Conformità garantita
- ✅ Zero responsabilità tecnica
- ✅ Certificazioni incluse
- ✅ Deploy veloce

**CONTRO**:
- ❌ Costi ricorrenti alti (€700/anno)
- ❌ Dipendenza fornitore
- ❌ Meno flessibilità

**COSTO TOTALE 3 ANNI**: €3.100 (solo integrazione API)
**BEST FOR**: Studi piccoli, < 20 clienti

### Opzione C: Ibrida (Sviluppo + Conservatore)

**PRO**:
- ✅ Massima sicurezza legale
- ✅ Flessibilità operativa
- ✅ Audit facilitati

**CONTRO**:
- ❌ Costi più alti
- ❌ Complessità gestione

**COSTO TOTALE 3 ANNI**: €12.700
**BEST FOR**: Studi enterprise, clienti enterprise

---

## Next Steps

### Immediati (Settimana 1)

1. **Decisione strategica**: Go/No-go su conservazione
2. **Scelta opzione**: In-house vs Esterno vs Ibrido
3. **Budget approval**: Allocazione risorse
4. **Nomina responsabile**: Responsabile conservazione

### Breve Termine (Mese 1)

1. **Fornitori**: Scelta provider firma/marca
2. **Contratti**: Setup account e certificati
3. **Planning**: Sprint planning sviluppo
4. **Kick-off**: Inizio sviluppo

### Medio Termine (Mesi 2-3)

1. **Sviluppo**: Implementazione completa
2. **Testing**: Validazione funzionale e conformità
3. **Formazione**: Training utenti
4. **Go-live**: Deploy produzione

### Lungo Termine (Mese 6+)

1. **Monitoring**: KPI e metriche
2. **Optimization**: Miglioramenti processo
3. **Scaling**: Estensione altri tipi documento
4. **Certification**: Eventuale certificazione ISO

---

## Conclusioni

La **conservazione digitale a norma** è:

### ✅ Necessaria
- Requisito di legge per molti documenti
- Tendenza in crescita (obbligatoria dal 2026 per alcune categorie)
- Best practice settore

### ✅ Fattibile
- Tecnologia matura e consolidata
- Fornitori affidabili disponibili
- Costi contenuti e prevedibili

### ✅ Vantaggiosa
- ROI positivo in 2 anni
- Risparmio costi archivio fisico
- Valore aggiunto per clienti

### ✅ Raccomandabile
- Differenziazione competitiva
- Efficienza operativa
- Preparazione per futuro digitale

---

## Contatti e Riferimenti

### Fornitori Consigliati

**Firma Digitale**:
- ArubaPEC: https://www.pec.it
- InfoCert: https://www.infocert.it
- Namirial: https://www.namirial.com

**Conservazione**:
- ArchiWorld: https://www.archiworld.it
- Namirial Conservazione: https://conservazione.namirial.it

**Software**:
- VeraPDF: https://verapdf.org
- Ghostscript: https://www.ghostscript.com

### Risorse Normative

- **AgID**: https://www.agid.gov.it
- **CAD**: https://www.normattiva.it (D.Lgs. 82/2005)
- **Linee Guida**: https://www.agid.gov.it/it/linee-guida

---

**Documento preparato il**: 17 Novembre 2025  
**Versione**: 1.0 Executive Summary  
**Per**: Decision Maker MyGest  
**Da**: Team Tecnico MyGest
