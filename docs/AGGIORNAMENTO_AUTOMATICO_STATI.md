# Gestione Automatica Stati Scadenze

## Descrizione

Il sistema aggiorna automaticamente lo stato delle scadenze in base alla **prima occorrenza attiva** (non completata né annullata):

### Logica di Aggiornamento

1. **Recupero Scadenze**: Scadenze con stato `BOZZA`, `ATTIVA` o `IN_SCADENZA`

2. **Recupero Occorrenze**: Per ogni scadenza, trova occorrenze con stato diverso da `COMPLETATA` o `ANNULLATA`, ordinate per data `inizio` crescente

3. **Scadenze Senza Occorrenze**: Vengono **ignorate** (nessuna modifica applicata)

4. **Determinazione Stato**:
   - **SCADUTA**: Se `inizio occorrenza < data odierna`
     - Stato: → `SCADUTA`
     - Priorità: → `CRITICA`
   
   - **IN_SCADENZA**: Se `data odierna ≤ inizio occorrenza ≤ data odierna + 3 giorni`
     - Stato: → `IN_SCADENZA`
     - Priorità: → `CRITICA`
   
   - **ATTIVA**: Se `inizio occorrenza > data odierna + 3 giorni`
     - Stato: → `ATTIVA`
     - Priorità: → `MEDIA`

### Esempio Pratico

```
Oggi: 2025-11-19

Scadenza A:
  - Occorrenza 1: 2025-11-15 (PENDING) → Prima occorrenza
  - Occorrenza 2: 2025-12-15 (PENDING)
  → Risultato: SCADUTA (4 giorni fa)

Scadenza B:
  - Occorrenza 1: 2025-11-19 (PENDING) → Prima occorrenza
  - Occorrenza 2: 2025-12-19 (PENDING)
  → Risultato: IN_SCADENZA (oggi)

Scadenza C:
  - Occorrenza 1: 2025-11-26 (PENDING) → Prima occorrenza
  → Risultato: ATTIVA (tra 7 giorni)

Scadenza D:
  - Occorrenza 1: 2025-11-01 (COMPLETATA)
  - Occorrenza 2: 2025-12-01 (PENDING) → Prima occorrenza attiva
  → Risultato: ATTIVA (tra 12 giorni)

Scadenza E:
  - Nessuna occorrenza
  → Risultato: IGNORATA (nessuna modifica)
```

## Comando Django

### Esecuzione manuale

```bash
# Modalità normale
python manage.py aggiorna_stati_scadenze

# Modalità dry-run (simula senza salvare)
python manage.py aggiorna_stati_scadenze --dry-run --verbose

# Con output dettagliato
python manage.py aggiorna_stati_scadenze --verbose
```

### Opzioni disponibili

- `--dry-run`: Simula le modifiche senza salvarle nel database
- `--verbose`: Mostra output dettagliato di tutte le scadenze elaborate

## Configurazione Cron Job

### 1. Esecuzione giornaliera (ore 1:00 AM)

```bash
# Apri il crontab
crontab -e

# Aggiungi questa riga (modifica i path secondo la tua installazione)
0 1 * * * cd /home/sandro/mygest && /home/sandro/mygest/venv/bin/python manage.py aggiorna_stati_scadenze >> /home/sandro/mygest/logs/aggiorna_stati.log 2>&1
```

### 2. Esecuzione ogni 6 ore

```bash
0 */6 * * * cd /home/sandro/mygest && /home/sandro/mygest/venv/bin/python manage.py aggiorna_stati_scadenze >> /home/sandro/mygest/logs/aggiorna_stati.log 2>&1
```

### 3. Con notifica email in caso di errori

```bash
MAILTO=admin@example.com
0 1 * * * cd /home/sandro/mygest && /home/sandro/mygest/venv/bin/python manage.py aggiorna_stati_scadenze >> /home/sandro/mygest/logs/aggiorna_stati.log 2>&1
```

## Creazione directory log

```bash
mkdir -p /home/sandro/mygest/logs
chmod 755 /home/sandro/mygest/logs
```

## Verifica cron job

```bash
# Visualizza i cron job attivi
crontab -l

# Verifica esecuzione nel log di sistema
grep CRON /var/log/syslog | tail -20

# Controlla il log dell'applicazione
tail -f /home/sandro/mygest/logs/aggiorna_stati.log
```

## Test

### 1. Test con dry-run

```bash
python manage.py aggiorna_stati_scadenze --dry-run --verbose
```

### 2. Verifica modifiche

```bash
# Prima del comando
python manage.py shell -c "from scadenze.models import Scadenza; print(Scadenza.objects.filter(stato='scaduta').count())"

# Esegui il comando
python manage.py aggiorna_stati_scadenze

# Dopo il comando
python manage.py shell -c "from scadenze.models import Scadenza; print(Scadenza.objects.filter(stato='scaduta').count())"
```

## Monitoraggio

### Log di esempio

```
=== Aggiornamento Stati Scadenze - 2025-11-19 ===

Scadenze da marcare come SCADUTE: 3
  - [15] Pagamento IMU (data: 2025-11-15) -> SCADUTA + CRITICA
  - [22] Scadenza ISEE (data: 2025-11-10) -> SCADUTA + CRITICA
  - [34] Rinnovo certificato (data: 2025-11-01) -> SCADUTA + CRITICA

Scadenze da marcare come IN_SCADENZA: 2
  - [45] Pagamento tasse (data: 2025-11-21, giorni rimanenti: 2) -> IN_SCADENZA + CRITICA
  - [56] Consegna documenti (data: 2025-11-20, giorni rimanenti: 1) -> IN_SCADENZA + CRITICA

============================================================
✓ Scadenze marcate come SCADUTE: 3
✓ Scadenze marcate come IN_SCADENZA: 2
✓ Totale aggiornate: 5

✓ Aggiornamenti completati con successo!
```

## Troubleshooting

### Problema: Il cron non si esegue

```bash
# Verifica che il cron service sia attivo
sudo systemctl status cron

# Riavvia il service se necessario
sudo systemctl restart cron
```

### Problema: Errori di permessi

```bash
# Assicurati che il file di log sia scrivibile
touch /home/sandro/mygest/logs/aggiorna_stati.log
chmod 664 /home/sandro/mygest/logs/aggiorna_stati.log
```

### Problema: Virtual environment non trovato

```bash
# Verifica il path del python nel venv
which python  # Con venv attivato
# Usa il path completo nel crontab
```

## Integrazione con sistemi di notifica

Puoi estendere il comando per inviare notifiche:

```python
# In scadenze/management/commands/aggiorna_stati_scadenze.py
from comunicazioni.services import invia_notifica

# Dopo l'aggiornamento
if scadute_count > 0:
    invia_notifica(
        titolo="Scadenze Aggiornate",
        messaggio=f"{scadute_count} scadenze sono ora SCADUTE"
    )
```

## Best Practices

1. **Esegui sempre un dry-run** prima di configurare il cron
2. **Monitora i log** regolarmente per i primi giorni
3. **Imposta notifiche email** per errori critici
4. **Esegui backup** prima di modifiche massive
5. **Testa il comando** in ambiente di sviluppo prima di produzione
