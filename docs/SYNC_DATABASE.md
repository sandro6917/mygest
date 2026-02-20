# Sistema di Sincronizzazione Database Dev/Prod

Sistema completo per sincronizzazione bidirezionale dei dati tra ambiente di sviluppo (locale) e produzione (VPS).

## 🎯 Caratteristiche

- **Merge Intelligente**: Unifica dati da entrambi gli ambienti senza perdite
- **Full Replace**: Opzione per sovrascrittura completa (con conferma)
- **Backup Automatico**: Backup pre-sync per rollback rapido
- **Dry-Run**: Anteprima modifiche senza applicarle
- **Bidirezionale**: Dev→Prod e Prod→Dev
- **File Condivisi NAS**: I file allegati sono già sincronizzati via NAS

## 📋 Comandi Disponibili

### 1. Sincronizzazione DEV → PROD

```bash
# Merge intelligente (default - consigliato)
./scripts/sync_dev_to_prod.sh

# Anteprima modifiche senza applicare
./scripts/sync_dev_to_prod.sh --dry-run

# Sovrascrittura completa (elimina tutto in prod)
./scripts/sync_dev_to_prod.sh --full-replace

# Senza backup (più veloce, meno sicuro)
./scripts/sync_dev_to_prod.sh --no-backup

# Combinazioni
./scripts/sync_dev_to_prod.sh --dry-run --full-replace
./scripts/sync_dev_to_prod.sh --force  # No conferma
```

### 2. Sincronizzazione PROD → DEV

```bash
# Sincronizza dati da produzione a sviluppo
./scripts/sync_prod_to_dev.sh

# Anteprima
./scripts/sync_prod_to_dev.sh --dry-run

# Senza conferma
./scripts/sync_prod_to_dev.sh --force
```

### 3. Rollback

```bash
# Ripristina ultimo backup (solo su PROD)
./scripts/rollback_last_sync.sh
```

## 🔄 Workflow Fase 1: Sviluppo/Testing (Attuale)

**Ambiente Master**: Sviluppo (locale)

### Scenario tipico

```bash
# 1. Lavori in locale
#    - Crei clienti, pratiche, documenti
#    - Testi funzionalità
#    - Verifichi tutto funziona

# 2. Anteprima sincronizzazione
./scripts/sync_dev_to_prod.sh --dry-run

# Output:
# 📊 ANTEPRIMA MODIFICHE (dry-run)
# ➕ Record CREATI:
#    • anagrafiche.Cliente: 15
#    • pratiche.Pratica: 23
#    TOTALE: 38
# 🔄 Record AGGIORNATI:
#    • anagrafiche.Cliente: 8
#    TOTALE: 8

# 3. Applica sincronizzazione
./scripts/sync_dev_to_prod.sh

# 4. Verifica su VPS
#    https://mygest.sandrochimenti.it
#    → Vedi i nuovi dati

# 5. Se qualcosa va male
./scripts/rollback_last_sync.sh
```

### Comportamento Merge Intelligente

```
Situazione iniziale:
├─ DEV:  100 clienti, 50 pratiche
└─ PROD: 100 clienti, 50 pratiche

Modifiche in DEV:
├─ Aggiungi Cliente #101
├─ Modifica Cliente #50 (nuovo telefono)
└─ Aggiungi Pratica #51

Modifiche in PROD (manualmente):
└─ Aggiungi Cliente #102 (test fatto su VPS)

Dopo sync_dev_to_prod.sh:
└─ PROD: 102 clienti (mantiene #102!), 51 pratiche
   ├─ Cliente #101 (da dev) ✅
   ├─ Cliente #102 (da prod) ✅ MANTENUTO
   ├─ Cliente #50 (aggiornato da dev) ✅
   └─ Pratica #51 (da dev) ✅
```

**NESSUNA PERDITA DATI** con merge intelligente! 🎉

### Comportamento Full Replace

```bash
./scripts/sync_dev_to_prod.sh --full-replace

# ⚠️  ATTENZIONE: Cliente #102 (creato in PROD) VIENE ELIMINATO
# PROD diventa ESATTA copia di DEV
```

## 🚀 Workflow Fase 2: Produzione Operativa (Futuro)

**Ambiente Master**: Produzione (VPS)

### Quando passare alla Fase 2

Quando:
- ✅ Applicazione è stabile
- ✅ Utenti iniziano a lavorare in produzione
- ✅ Dati di produzione diventano "source of truth"

### Cambio modalità

```bash
# Crea file di configurazione
cat > .env.sync << EOF
# Fase 1: Sviluppo (attuale)
SYNC_MODE=dev_to_prod

# Fase 2: Produzione operativa (futuro)
# SYNC_MODE=prod_to_dev
EOF
```

### Workflow Fase 2

```bash
# 1. Utenti lavorano su VPS (PROD)
#    - Inseriscono clienti reali
#    - Gestiscono pratiche
#    - Caricano documenti

# 2. Tu vuoi testare nuova funzionalità con dati reali
./scripts/sync_prod_to_dev.sh

# 3. Sviluppi e testi in locale con dati prod

# 4. Deploy codice su VPS (via GitHub Actions)
git push origin main

# 5. Prod ha nuovo codice + dati reali aggiornati
```

## 📊 Dati Sincronizzati

### ✅ Tabelle Incluse

- **Anagrafiche**: Anagrafica, Cliente, ContattoEmail, Indirizzo
- **Pratiche**: Pratica, PraticaNota, TipoPratica
- **Fascicoli**: Fascicolo, FascicoloDocumento
- **Documenti**: Documento, DocumentiTipo, Allegato (metadati)
- **Scadenze**: Scadenza, ScadenzaAlert, TipoScadenza
- **Protocollo**: MovimentoProtocollo
- **Archivio Fisico**: UnitaFisica, CollocazioneFisica, OperazioneArchivio
- **Titolario**: TitolarioVoce

### ❌ Tabelle Escluse

- **Utenti**: auth.User (ogni ambiente ha i suoi utenti)
- **Sessioni**: django_session
- **Admin Log**: django_admin_log
- **Migrations**: django_migrations

### 📁 File (Media)

**NON sincronizzati via questo sistema** perché:
- ✅ File già condivisi via NAS montato su `/mnt/archivio`
- ✅ Stesso storage accessibile da dev (Windows/WSL) e prod (VPS)
- ✅ Path file nel DB puntano allo stesso NAS

## 🔍 Management Commands Django

### Export Dati

```bash
# Export completo
python manage.py export_data

# Export con output personalizzato
python manage.py export_data --output=my_export.json

# Export solo alcune tabelle
python manage.py export_data --models=anagrafiche.Cliente,pratiche.Pratica

# Export con indentazione maggiore (più leggibile)
python manage.py export_data --indent=4
```

### Import Dati

```bash
# Import con merge
python manage.py import_data --input=export.json

# Anteprima
python manage.py import_data --input=export.json --dry-run

# Full replace (elimina tutto prima)
python manage.py import_data --input=export.json --full-replace

# Senza backup
python manage.py import_data --input=export.json --no-backup
```

## 🛡️ Sicurezza e Backup

### Backup Automatici

```
Ogni sync DEV→PROD crea:
/srv/mygest/backups/sync/pre_sync_YYYYMMDD_HHMMSS.sql

Esempio:
/srv/mygest/backups/sync/pre_sync_20260220_153045.sql (7.2MB)
```

### Rollback

```bash
# Ripristina ultimo backup
./scripts/rollback_last_sync.sh

# Output:
# ✅ Backup trovato: pre_sync_20260220_153045.sql (7.2MB)
# ⚠️  Confermi il ripristino? (yes/no): yes
# 🔄 Ripristino database...
# ✅ Database ripristinato
```

### Retention Backup

- **Backup sync**: Mantenuti ultimi 10
- **Export files**: Mantenuti ultimi 5
- **Pulizia automatica**: Ogni sync

## 📈 Output Esempio

### Sync DEV→PROD (Merge)

```
===== SYNC DEV → PROD - START =====
Dev:  SandroWin11 - Database locale
Prod: 72.62.34.249 - Database VPS

=== Step 1/4: Export dati da DEV ===
Export dati locali...
  📦 anagrafiche.Cliente: 101 record
  📦 pratiche.Pratica: 97 record
  📦 documenti.Documento: 500 record
  ...
✅ Export completato: fixtures/sync/dev_export_20260220_153045.json (2.3MB)

=== Step 2/4: Backup database PROD ===
Creazione backup su VPS...
✅ Backup creato: /srv/mygest/backups/sync/pre_sync_20260220_153045.sql (7.2MB)

=== Step 3/4: Upload dati su PROD ===
Upload fixtures/sync/dev_export_20260220_153045.json → VPS:/tmp/sync_import_20260220_153045.json
✅ Upload completato

=== Step 4/4: Import dati su PROD ===
Esecuzione import su VPS...
📥 Fase 2: Import e merge record...

============================================================
✅ IMPORT COMPLETATO
============================================================

➕ Record CREATI:
   • anagrafiche.Cliente: 15
   • pratiche.Pratica: 8
   • documenti.Documento: 23
   TOTALE: 46

🔄 Record AGGIORNATI:
   • anagrafiche.Cliente: 86
   • pratiche.Pratica: 89
   TOTALE: 175

============================================================

✅ Import completato

=== Cleanup ===
Pulizia export vecchi...
✅ Cleanup completato

=== Riepilogo ===
✅ Sincronizzazione DEV → PROD completata con successo!
📊 Database PROD aggiornato con dati da DEV

===== SYNC DEV → PROD - END =====
```

## 🚨 Troubleshooting

### Errore: "Export fallito"

```bash
# Verifica virtual environment
source venv/bin/activate
python manage.py export_data

# Controlla permessi
ls -l fixtures/sync/
```

### Errore: "Upload fallito"

```bash
# Testa connessione SSH
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249

# Verifica chiave SSH
ls -l ~/.ssh/github_actions_mygest
```

### Errore: "Import fallito"

```bash
# Controlla log su VPS
ssh mygest@72.62.34.249 "tail -50 /srv/mygest/logs/sync.log"

# Verifica database prod
ssh mygest@72.62.34.249 "cd /srv/mygest/app && source /srv/mygest/venv/bin/activate && python manage.py dbshell"
```

### Record duplicati dopo sync

**Causa**: Primary key conflicts

**Soluzione**: Usa `--full-replace` per reset completo:

```bash
./scripts/sync_dev_to_prod.sh --full-replace
```

## 📝 Note Importanti

### File Allegati

I **file fisici** (PDF, immagini, etc.) sono sul **NAS condiviso**:
- Path locale (dev): `/mnt/archivio/`
- Path VPS (prod): `/srv/mygest/archivio/` (montato via SSH tunnel)
- **Stesso storage fisico** → sincronizzazione automatica ✅

### Performance

- Export: ~2-3 secondi per 1000 record
- Upload: ~1 secondo per 10MB (dipende da connessione)
- Import merge: ~5-10 secondi per 1000 record
- Import full-replace: ~3-5 secondi per 1000 record

### Limiti

- **Relazioni circolari**: Non supportate (ordine import è fisso)
- **File binari**: Solo metadati (file via NAS)
- **Sequence reset**: Post-import potrebbero essere necessari ajustamenti

## 🎯 Best Practices

1. **Usa sempre --dry-run** prima del primo sync
2. **Backup manuale** prima di `--full-replace`
3. **Sync frequenti** (giornaliero) per evitare grandi divergenze
4. **Documenta modifiche** manuali fatte in prod
5. **Passa a Fase 2** quando prod è operativo

---

**Versione**: 1.0
**Data**: 2026-02-20
**Autore**: Sandro Chimenti
