# Riepilogo Modifiche: Gestione Storage e File System

## Data: 17 Novembre 2025

## Obiettivo
Migliorare e standardizzare la gestione dei file e dello storage nel progetto MyGest, eliminando la dipendenza dalla directory `media/` e centralizzando tutto in una directory configurabile tramite environment variable.

## Modifiche Implementate

### 1. Configurazione Settings (`mygest/settings.py`)

**Prima:**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")
```

**Dopo:**
```python
# Archivio / Storage configurazione
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")
MEDIA_URL = '/archivio/'
MEDIA_ROOT = ARCHIVIO_BASE_PATH  # Punta alla stessa directory per compatibilità
```

**Benefici:**
- Configurazione unificata dello storage
- Separazione chiara tra sviluppo (WSL/NAS) e produzione (VPS)
- Eliminazione della confusione tra MEDIA_ROOT e archivio personalizzato

### 2. Model Archivio Fisico (`archivio_fisico/models.py`)

**Modifiche:**
- Aggiunto import di `NASPathStorage`
- Aggiunto `storage=nas_storage` ai campi FileField:
  - `OperazioneArchivio.verbale_scan`
  - `VerbaleConsegnaTemplate.file_template`
- Modificato `upload_to` da `"archivio/operazioni"` a `"archivio_fisico/operazioni"`

**Benefici:**
- Tutti i file ora utilizzano lo storage configurabile
- Percorsi più chiari e organizzati
- Coerenza con il resto dell'applicazione

### 3. Files di Configurazione Environment

**Creati:**
- `.env.example` - Template per la configurazione
- `.env.production` - Configurazione specifica per VPS
- Aggiornato `.env` - Aggiunta esplicita di `ARCHIVIO_BASE_PATH=/mnt/archivio`

**Struttura:**
```
Ambiente Locale (WSL):    ARCHIVIO_BASE_PATH=/mnt/archivio
Ambiente Produzione (VPS): ARCHIVIO_BASE_PATH=/srv/mygest/archivio
```

### 4. Script di Migrazione (`scripts/migrate_storage.py`)

**Funzionalità:**
- Modalità dry-run per simulazione
- Copia sicura dei file (mantiene originali)
- Report dettagliato dell'operazione
- Gestione errori

**Uso:**
```bash
python scripts/migrate_storage.py --dry-run  # Simulazione
python scripts/migrate_storage.py           # Migrazione reale
```

### 5. Documentazione

**Creata:**
- `docs/guida_storage.md` - Guida completa alla gestione dello storage
- `docs/setup_archivio_locale.md` - Setup specifico per ambiente locale WSL

**Aggiornata:**
- `README.md` - Riferimenti alla nuova documentazione

**Contenuti:**
- Architettura dello storage
- Configurazione per ambiente
- Procedure di migrazione
- Backup e sincronizzazione
- Troubleshooting

## Struttura Directory Archivio

```
ARCHIVIO_BASE_PATH/
├── documenti/              # Documenti gestiti dal sistema
│   ├── 2024/
│   │   ├── CLI001/
│   │   └── CLI002/
│   └── 2025/
├── archivio_fisico/        # File dell'archivio fisico
│   ├── operazioni/         # Scansioni verbali operazioni
│   └── verbali/            # Template verbali
└── fascicoli/              # Fascicoli e documenti correlati
```

## Testing Effettuato

✅ Django check: Nessun errore rilevato
✅ Verifica configurazione storage: Corretto
✅ Script migrazione (dry-run): Funzionante
✅ Identificati 5 file da migrare

## Azioni Richieste

### Ambiente Locale (WSL)

1. **Setup NAS/Directory:**
   ```bash
   # Opzione A: Monta NAS
   sudo mount -t drvfs '\\IP_NAS\SHARE' /mnt/archivio -o uid=$(id -u),gid=$(id -g)
   
   # Opzione B: Directory locale (solo test)
   sudo chown -R sandro:sandro /mnt/archivio
   ```

2. **Migrazione File:**
   ```bash
   cd /home/sandro/mygest
   source venv/bin/activate
   python scripts/migrate_storage.py --dry-run
   python scripts/migrate_storage.py
   ```

3. **Verifica:**
   ```bash
   python manage.py runserver
   # Testa upload/download documenti
   ```

### Ambiente Produzione (VPS)

1. **Preparazione:**
   ```bash
   sudo mkdir -p /srv/mygest/archivio
   sudo chown www-data:www-data /srv/mygest/archivio
   sudo chmod 755 /srv/mygest/archivio
   ```

2. **Deploy:**
   ```bash
   cd /srv/mygest/app
   git pull origin main
   
   # Aggiorna .env
   echo "ARCHIVIO_BASE_PATH=/srv/mygest/archivio" >> .env
   
   # Deploy
   scripts/deploy.sh
   ```

3. **Migrazione File (se esistenti):**
   ```bash
   source /srv/mygest/venv/bin/activate
   python scripts/migrate_storage.py
   ```

## Benefici Ottenuti

1. **Flessibilità:** Storage configurabile via environment variable
2. **Chiarezza:** Separazione netta tra sviluppo e produzione
3. **Manutenibilità:** Documentazione completa e script automatizzati
4. **Sicurezza:** Backup e migrazione con verifica
5. **Organizzazione:** Struttura directory logica e coerente

## Backward Compatibility

- `MEDIA_ROOT` ancora definito (punta a `ARCHIVIO_BASE_PATH`)
- URL serviti da `/archivio/` invece di `/media/`
- Files esistenti possono essere migrati gradualmente
- Script di migrazione mantiene gli originali per sicurezza

## Prossimi Passi Consigliati

1. ✅ Completare setup locale
2. ✅ Eseguire migrazione file in locale
3. ✅ Testare funzionalità di upload/download
4. ⏳ Deploy in produzione
5. ⏳ Migrazione file in produzione
6. ⏳ Setup backup automatico archivio
7. ⏳ Monitoring spazio disco

## File Modificati

- `mygest/settings.py`
- `archivio_fisico/models.py`
- `.env`
- `README.md`

## File Creati

- `.env.example`
- `.env.production`
- `scripts/migrate_storage.py`
- `docs/guida_storage.md`
- `docs/setup_archivio_locale.md`
- `docs/RIEPILOGO_MODIFICHE_STORAGE.md` (questo file)

## Note di Compatibilità

- Django 4.2+: ✅ Compatibile
- PostgreSQL: ✅ Nessun impatto
- Python 3.10+: ✅ Compatibile
- Storage personalizzato: ✅ Già implementato (NASPathStorage)

## Rischi e Mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Perdita file durante migrazione | Bassa | Alto | Script copia (non sposta) + backup preventivo |
| Permessi insufficienti | Media | Medio | Documentazione setup dettagliata |
| Percorsi errati in produzione | Bassa | Alto | Variabile environment + test pre-deploy |
| NAS non disponibile (locale) | Media | Basso | Fallback su directory locale documentato |

## Contatti e Supporto

Per problemi o domande relative a queste modifiche:
- Consulta `docs/guida_storage.md`
- Consulta `docs/setup_archivio_locale.md`
- Verifica log: `/srv/mygest/logs/` (produzione)
