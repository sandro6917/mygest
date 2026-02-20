# Automazione Pulizia File Upload

Guida completa per automatizzare la pulizia dei file dopo l'upload in MyGest.

## Panoramica Soluzioni

Sono disponibili **3 approcci** per automatizzare la pulizia:

1. **Servizio Systemd** (Daemon) - ⭐ Consigliato per produzione
2. **Cron Job** - Semplice e versatile
3. **Script Manuale** - Per uso occasionale

---

## 1. Servizio Systemd (Daemon)

Il servizio systemd monitora continuamente una directory e elimina i file automaticamente.

### Caratteristiche
- ✅ Monitoraggio in tempo reale
- ✅ Riavvio automatico in caso di crash
- ✅ Logging integrato con systemd
- ✅ Stato persistente tra i riavvii

### Setup

```bash
# 1. Crea una directory di staging
mkdir -p /home/sandro/upload-staging

# 2. Configura il servizio (come root)
cd /home/sandro/mygest/scripts
sudo bash setup_systemd_service.sh

# 3. Verifica lo stato
sudo systemctl status mygest-cleanup
```

### Configurazione

Il file `mygest-cleanup.service` contiene:

```ini
ExecStart=/usr/bin/python3 /home/sandro/mygest/scripts/auto_cleanup_watcher.py \
    --watch-dir /home/sandro/upload-staging \
    --delay 300 \
    --interval 60
```

**Parametri:**
- `--watch-dir`: Directory da monitorare
- `--delay`: Secondi di attesa prima di eliminare (300 = 5 minuti)
- `--interval`: Intervallo tra le scansioni (60 = 1 minuto)
- `--marker`: Nome del file marker (default: `.uploaded`)

### Workflow

1. L'utente carica un file nell'applicazione web
2. Il browser copia il file in `/home/sandro/upload-staging/`
3. Dopo l'upload riuscito, viene creato un file marker `.uploaded`
4. Il daemon rileva il marker e marca il file per eliminazione
5. Dopo `--delay` secondi, il file viene eliminato automaticamente

### Comandi Utili

```bash
# Vedere i log in tempo reale
sudo journalctl -u mygest-cleanup -f

# Fermare il servizio
sudo systemctl stop mygest-cleanup

# Riavviare il servizio
sudo systemctl restart mygest-cleanup

# Disabilitare il servizio
sudo systemctl disable mygest-cleanup

# Riabilitare il servizio
sudo systemctl enable mygest-cleanup

# Vedere lo stato
sudo systemctl status mygest-cleanup
```

### Log

I log sono disponibili in:
- `/home/sandro/mygest/scripts/auto_cleanup.log`
- `journalctl -u mygest-cleanup`
- `/var/log/mygest-cleanup.log`

---

## 2. Cron Job

Alternativa più semplice: lo script viene eseguito periodicamente.

### Caratteristiche
- ✅ Semplice da configurare
- ✅ Non richiede permessi root per configurazione
- ✅ Perfetto per pulizie programmate
- ❌ Non monitora in tempo reale

### Setup

```bash
# 1. Apri il crontab
crontab -e

# 2. Aggiungi una delle configurazioni (vedi sotto)

# 3. Salva e verifica
crontab -l
```

### Configurazioni Esempio

```bash
# Pulizia ogni 5 minuti (file più vecchi di 5 minuti)
*/5 * * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300

# Pulizia ogni ora (file più vecchi di 1 ora)
0 * * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 3600

# Pulizia notturna alle 2:00 AM (file più vecchi di 24 ore)
0 2 * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 86400

# Pulizia solo PDF ogni 15 minuti
*/15 * * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 900 --extensions .pdf
```

### Parametri

- `--staging-dir`: Directory da pulire (obbligatorio)
- `--max-age`: Età massima in secondi (default: 3600)
- `--extensions`: Estensioni da considerare (es: `.pdf,.docx`)
- `--dry-run`: Test senza eliminare file

### Test

```bash
# Test in modalità dry-run
python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300 --dry-run

# Esecuzione reale
python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300
```

### Log

I log vengono salvati in:
- `/home/sandro/mygest/scripts/cron_cleanup.log`

Per visualizzarli:
```bash
tail -f /home/sandro/mygest/scripts/cron_cleanup.log
```

---

## 3. Script Manuali

Gli script originali rimangono disponibili per uso manuale.

### remove_uploaded_file.py

Elimina uno o più file specifici:

```bash
# File singolo
python3 remove_uploaded_file.py /percorso/al/file.pdf

# File multipli
python3 remove_uploaded_file.py /percorso/file1.pdf /percorso/file2.docx

# Senza conferma
python3 remove_uploaded_file.py /percorso/al/file.pdf --force

# Verbose
python3 remove_uploaded_file.py /percorso/al/file.pdf --verbose
```

### interactive_file_cleanup.py

Interfaccia interattiva per gestire più file:

```bash
python3 interactive_file_cleanup.py
```

Permette di:
- Cercare file per pattern
- Selezionare file multipli
- Confermare prima di eliminare
- Vedere statistiche

---

## Confronto Soluzioni

| Caratteristica | Systemd | Cron | Manuale |
|----------------|---------|------|---------|
| Setup | Complesso | Semplice | Nessuno |
| Automazione | Completa | Periodica | No |
| Tempo reale | ✅ | ❌ | ❌ |
| Richiede root | ✅ (setup) | ❌ | ❌ |
| Logging | Integrato | File | Console |
| Persistenza | ✅ | ❌ | ❌ |
| Uso | Produzione | Prod/Dev | Test/Debug |

---

## Raccomandazioni

### Produzione
**Usa Systemd** per:
- Monitoraggio continuo
- Eliminazione rapida dopo upload
- Gestione affidabile

### Sviluppo/Test
**Usa Cron** per:
- Setup semplice
- Pulizie periodiche
- Meno risorse

### Debug
**Usa Script Manuali** per:
- Test funzionalità
- Debug problemi
- Pulizie occasionali

---

## Workflow Consigliato

### Setup Iniziale

```bash
# 1. Crea directory staging
mkdir -p /home/sandro/upload-staging

# 2. Test con script manuale
python3 remove_uploaded_file.py /home/sandro/upload-staging/test.pdf --dry-run

# 3. Test con cron (ogni 5 minuti)
crontab -e
# Aggiungi: */5 * * * * cd /home/sandro/mygest/scripts && python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300

# 4. Se tutto funziona, passa a systemd
sudo bash setup_systemd_service.sh
```

### Monitoraggio

```bash
# Vedere attività systemd
sudo journalctl -u mygest-cleanup -f --since "10 minutes ago"

# Vedere attività cron
tail -f /home/sandro/mygest/scripts/cron_cleanup.log

# Statistiche directory
du -sh /home/sandro/upload-staging
ls -la /home/sandro/upload-staging
```

---

## Troubleshooting

### Il servizio non si avvia

```bash
# Controlla errori
sudo journalctl -u mygest-cleanup -n 50

# Verifica path Python
which python3

# Testa script manualmente
python3 /home/sandro/mygest/scripts/auto_cleanup_watcher.py --watch-dir /home/sandro/upload-staging --delay 60 --interval 30
```

### Cron non funziona

```bash
# Verifica cron attivo
sudo systemctl status cron

# Controlla log cron di sistema
grep CRON /var/log/syslog

# Testa comando manualmente
cd /home/sandro/mygest/scripts && python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300 --dry-run
```

### File non vengono eliminati

```bash
# Verifica permessi
ls -la /home/sandro/upload-staging

# Verifica età file
find /home/sandro/upload-staging -type f -mmin +5

# Test in dry-run
python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300 --dry-run
```

---

## Sicurezza

⚠️ **IMPORTANTE**:

1. **Backup**: Assicurati che i file siano stati caricati correttamente prima di eliminarli
2. **Test**: Usa sempre `--dry-run` prima in produzione
3. **Monitoring**: Controlla i log regolarmente
4. **Delay**: Usa un delay ragionevole (almeno 5 minuti) per evitare eliminazioni premature
5. **Permessi**: Limita l'accesso alla directory staging

---

## File Coinvolti

```
scripts/
├── auto_cleanup_watcher.py        # Daemon per monitoraggio continuo
├── cron_cleanup.py                # Script per esecuzione cron
├── mygest-cleanup.service         # File service systemd
├── setup_systemd_service.sh       # Setup automatico systemd
├── create_upload_marker.sh        # Helper per creare marker
├── crontab.example                # Esempi configurazione cron
├── remove_uploaded_file.py        # Script manuale singolo file
├── interactive_file_cleanup.py    # Script interattivo
└── AUTOMAZIONE_CLEANUP.md         # Questa documentazione
```

---

## Riferimenti

- [systemd.service manual](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html)
- [Python logging](https://docs.python.org/3/library/logging.html)
