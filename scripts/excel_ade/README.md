# 📥 File Excel Codici Tributo F24

Questa directory contiene i file Excel scaricati dal sito ufficiale dell'Agenzia delle Entrate.

## 🔗 Link Download

### Pagina principale
https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24

---

## 📋 File da Scaricare

### 1️⃣ Codici Tributo Erariali e Regionali ⭐ **PRIORITARIO**

**Pagina:** https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabella-codici-tributo-erariali-e-regionali

**File da scaricare:**
- ✅ **TABELLA_EREL_11_11_2025_codice tributo.xlsx** (aggiornamento 11 novembre 2025)
  - Link diretto: https://www.agenziaentrate.gov.it/portale/documents/20143/448357/TABELLA_EREL_11_11_2025_codice+tributo.xlsx/7195eadf-0fe4-7662-a391-59965b747eb8?t=1762853955360

**Contiene:**
- Ritenute (1001, 1002, 1012, etc.)
- IVA (6099, 6001, etc.)
- IRPEF/IRES
- Addizionali comunali/regionali
- IRAP

**Codici:** ~1450

---

### 2️⃣ Codici INPS ed Enti Previdenziali ⭐ **PRIORITARIO**

**Pagina:** https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-inps-e-enti-previdenziali-ed-assicurativi

**File da scaricare:**
- ✅ **Causali_INPS_08_09_2025.xls** (aggiornamento 8 settembre 2025)
  - Link diretto: https://www.agenziaentrate.gov.it/portale/documents/20143/448438/Causali_INPS_08_09_2025.xls/63a43d8a-2390-eb07-5e0c-d2052b854eff?t=1757339673317

**Contiene:**
- Contributi gestione separata
- Artigiani e commercianti
- Contributi previdenziali dipendenti
- Causali DM10, RC01, AF-CF, etc.

**Codici:** ~190

⚠️ **Formato:** File .xls (vecchio formato Excel)

---

### 3️⃣ Codici Tributi Locali (IMU, TASI, TARI) ⚠️ **OPZIONALE**

**Pagina:** https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-per-tributi-locali

**File disponibile:**
- Tabella_IMU_ICI e altri tributi comunali_13_03_2024.pdf
  - Link: https://www.agenziaentrate.gov.it/portale/documents/20143/448384/Tabella_IMU_ICI+e+altri+tributi+comunali_13_03_2024.pdf/23808f04-662f-d49b-27d8-709f1ea886fb?t=1710340610624

⚠️ **Nota:** File in formato PDF, non supportato dal parser automatico.  
Per IMU/TARI, consultare il file PDF manualmente se necessario.

---

## 📥 Procedura Download

### Opzione A: Download Manuale (Consigliato)

1. Apri i link diretti sopra
2. I file si scaricano automaticamente
3. Sposta i file in questa directory: `/home/sandro/mygest/scripts/excel_ade/`

```bash
# Esempio: sposta file dalla cartella Download
mv ~/Download/TABELLA_EREL_*.xlsx /home/sandro/mygest/scripts/excel_ade/
mv ~/Download/TAB_INPS_*.xlsx /home/sandro/mygest/scripts/excel_ade/
```

### Opzione B: Download con wget/curl

```bash
cd /home/sandro/mygest/scripts/excel_ade/

# File Erariali/Regionali (.xlsx)
wget -O "TABELLA_EREL_11_11_2025.xlsx" "https://www.agenziaentrate.gov.it/portale/documents/20143/448357/TABELLA_EREL_11_11_2025_codice+tributo.xlsx/7195eadf-0fe4-7662-a391-59965b747eb8?t=1762853955360"

# File INPS (.xls - vecchio formato)
wget -O "Causali_INPS_08_09_2025.xls" "https://www.agenziaentrate.gov.it/portale/documents/20143/448438/Causali_INPS_08_09_2025.xls/63a43d8a-2390-eb07-5e0c-d2052b854eff?t=1757339673317"
```

---

## ✅ Verifica File

Controlla che i file siano presenti:

```bash
ls -lh /home/sandro/mygest/scripts/excel_ade/

# Output atteso:
# TABELLA_EREL_11_11_2025.xlsx         (~120 KB)
# Causali_INPS_08_09_2025.xls          (~100 KB)
```

---

## 🚀 Uso Parser

Una volta scaricati i file, esegui il parser:

```bash
# Vai alla directory root del progetto
cd /home/sandro/mygest

# Solo export CSV/JSON (per testare)
python scripts/parse_codici_tributo_excel.py

# Aggiorna database Django
python scripts/parse_codici_tributo_excel.py --update-db

# Con output dettagliato
python scripts/parse_codici_tributo_excel.py --update-db --verbose
```

---

## 📅 Aggiornamenti

L'Agenzia delle Entrate aggiorna periodicamente questi file (di solito mensilmente).

**Controllo aggiornamenti:**
- Visita la pagina principale: https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24
- Verifica date aggiornamento
- Scarica nuovi file se necessario
- Ri-esegui il parser

**Frequenza consigliata:** Mensile o dopo comunicazioni ufficiali ADE

---

## 📝 Note

- I file hanno sempre lo stesso formato ma nome diverso (con data)
- Il parser cerca pattern `TABELLA_EREL_*.xlsx` e `TAB_INPS_*.xlsx`
- Se ci sono più versioni, usa automaticamente la più recente
- I file tributi locali sono opzionali (molto pesanti)

---

## 🆘 Troubleshooting

**Problema:** File non trovato

```
❌ Directory scripts/excel_ade non trovata!
```

**Soluzione:** Scarica i file e mettili in questa directory

---

**Problema:** Parser lento

**Causa:** File Excel molto grandi (>5000 righe)

**Soluzione:** Il parser limita automaticamente a 10.000 righe per velocità

---

**Problema:** Link non funzionante

**Soluzione:** 
1. Vai alla pagina principale ADE
2. Cerca manualmente i file Excel
3. Scarica dalla pagina web

---

## 📊 Struttura File Excel

### File Erariali/Regionali

| Colonna | Descrizione |
|---------|-------------|
| Codice tributo | Codice numerico (es: 1001, 6099) |
| Descrizione | Descrizione completa del tributo |
| Note | Eventuali note/periodicità |

### File INPS

| Colonna | Descrizione |
|---------|-------------|
| Codice tributo | Codice alfanumerico (es: PXX, AP23) |
| Causale contributo | Descrizione del contributo |

---

Ultimo aggiornamento: 25 novembre 2025
