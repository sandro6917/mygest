# 🚀 QUICK START: Aggiornamento Codici Tributo F24

## ⚡ Procedura Rapida (5 minuti)

### 1. Scarica File Excel

**File necessari (2):**

1. **ERARIO/REGIONI** (.xlsx) - Obbligatorio
   ```bash
   wget -O "TABELLA_EREL_11_11_2025.xlsx" \
   "https://www.agenziaentrate.gov.it/portale/documents/20143/448357/TABELLA_EREL_11_11_2025_codice+tributo.xlsx/7195eadf-0fe4-7662-a391-59965b747eb8?t=1762853955360"
   ```

2. **INPS** (.xls) - Obbligatorio
   ```bash
   wget -O "Causali_INPS_08_09_2025.xls" \
   "https://www.agenziaentrate.gov.it/portale/documents/20143/448438/Causali_INPS_08_09_2025.xls/63a43d8a-2390-eb07-5e0c-d2052b854eff?t=1757339673317"
   ```

O scarica manualmente dalla pagina ADE:  
https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24

### 2. Sposta File

```bash
# Sposta dalla cartella Download alla directory del progetto
mv ~/Download/TABELLA_EREL*.xlsx /home/sandro/mygest/scripts/excel_ade/
mv ~/Download/Causali_INPS*.xls /home/sandro/mygest/scripts/excel_ade/
```

### 3. Esegui Parser

```bash
cd /home/sandro/mygest

# Aggiorna database
python scripts/parse_codici_tributo_excel.py --update-db

# Con output dettagliato
python scripts/parse_codici_tributo_excel.py --update-db --verbose
```

### 4. Verifica

```bash
# Controlla totali
python manage.py shell -c "
from scadenze.models import CodiceTributoF24
print(f'Totale: {CodiceTributoF24.objects.count()} codici')
"
```

---

## 📊 Risultati Attesi

```
📊 TOTALE CODICI: ~1680

📈 Per sezione:
  - ERARIO: ~1450 codici
  - INPS: ~190 codici
  - REGIONI: ~40 codici

✓ Database aggiornato:
  - Creati: XXX nuovi codici
  - Aggiornati: YYY codici esistenti
  
⏱️ Tempo: ~30 secondi
```

---

## 🔄 Aggiornamenti Futuri

**Frequenza:** Mensile o dopo comunicazioni ADE

**Procedura:**
1. Visita pagina ADE (link sopra)
2. Verifica data aggiornamento file
3. Scarica nuovo file se necessario
4. Riesegui parser: `python scripts/parse_codici_tributo_excel.py --update-db`

---

## 📁 File Supportati

| File | Priorità | Descrizione | Codici | Formato |
|------|----------|-------------|--------|---------|
| `TABELLA_EREL_*.xlsx` | ⭐ **Obbligatorio** | Erariali/Regionali | ~1450 | .xlsx |
| `Causali_INPS_*.xls` | ⭐ **Obbligatorio** | INPS/Previdenziali | ~190 | .xls |
| `Tabella_IMU_*.pdf` | ⚠️  Opzionale | Tributi Locali (IMU) | - | .pdf |

---

## 🆘 Problemi Comuni

### File non trovato

```
❌ File INPS non trovato (TAB_INPS_*.xlsx)
```

**Causa:** File non presente nella directory `scripts/excel_ade/`

**Soluzione:** 
- Se necessario, scarica il file dalla pagina ADE
- Altrimenti ignora (opzionale)

### Parser lento

**Causa:** File molto grande (>5000 righe)

**Soluzione:** Il parser limita automaticamente a 10.000 righe. Attendi ~30 secondi.

### Errore database

```
❌ Errore database: ...
```

**Soluzione:**
1. Verifica che Django sia configurato: `python manage.py check`
2. Fai backup database: `pg_dump mygest > backup.sql`
3. Riprova

---

## ✅ Vantaggi Soluzione Locale

✅ **Veloce:** Parse in ~30 secondi (vs ore di scraping)  
✅ **Affidabile:** Nessuna dipendenza da struttura HTML  
✅ **Offline:** Funziona senza connessione dopo download  
✅ **Semplice:** Un solo comando  

---

## 🔗 Link Utili

- **Pagina principale ADE:** https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti
- **Documentazione completa:** `docs/SISTEMA_AGGIORNAMENTO_CODICI_TRIBUTO.md`
- **README directory Excel:** `scripts/excel_ade/README.md`

---

## 📝 Note

- **Backup automatico:** Consigliato fare backup DB prima di aggiornare
- **Conflitti codici:** Il parser aggiorna codici esistenti preservando dati custom
- **Performance:** ~1500 codici importati in <1 minuto

---

Ultimo aggiornamento: 25 novembre 2025
