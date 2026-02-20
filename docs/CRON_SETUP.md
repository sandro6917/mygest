# Istruzioni per Configurare Cron Job - Pulizia File Temporanei

## Installazione Automatica del Cron Job

### Opzione 1: Aggiungere manualmente al crontab

```bash
# Apri il crontab per l'utente corrente
crontab -e

# Aggiungi questa riga alla fine del file:
# Pulizia file temporanei ogni notte alle 2:00 AM
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7

# Salva e chiudi (CTRL+X, poi Y, poi ENTER in nano)
```

### Opzione 2: Usando un one-liner

```bash
# Aggiungi automaticamente al crontab (senza aprire editor)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7") | crontab -
```

### Opzione 3: Schedule alternativo (ogni 12 ore)

```bash
# Alle 2:00 AM e alle 2:00 PM
0 2,14 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7
```

### Opzione 4: Schedule settimanale (solo domenica)

```bash
# Ogni domenica alle 3:00 AM
0 3 * * 0 /home/sandro/mygest/scripts/cleanup_tmp.sh 14
```

## Verifica Installazione

### 1. Lista crontab corrente
```bash
crontab -l
```

Dovresti vedere:
```
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7
```

### 2. Verifica servizio cron attivo
```bash
sudo systemctl status cron
```

### 3. Test manuale script
```bash
/home/sandro/mygest/scripts/cleanup_tmp.sh 7
```

### 4. Verifica log
```bash
cat /home/sandro/mygest/logs/cleanup_tmp.log
```

## Personalizzazione

### Cambiare retention (giorni)

Modifica il numero finale nello script cron:

```bash
# 3 giorni di retention
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 3

# 14 giorni di retention
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 14

# 30 giorni di retention
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 30
```

### Cambiare orario esecuzione

Formato cron: `minuto ora giorno_mese mese giorno_settimana`

```bash
# Ogni giorno alle 3:30 AM
30 3 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7

# Ogni 6 ore
0 */6 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7

# Solo nei giorni feriali alle 2 AM
0 2 * * 1-5 /home/sandro/mygest/scripts/cleanup_tmp.sh 7

# Primo giorno del mese alle 1 AM
0 1 1 * * /home/sandro/mygest/scripts/cleanup_tmp.sh 30
```

## Monitoraggio

### Alert email su errori (opzionale)

```bash
# Invia email solo se ci sono errori
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7 || echo "Cleanup tmp fallito" | mail -s "MyGest: Errore cleanup" admin@example.com
```

### Log rotation

Se il log diventa troppo grande, aggiungi log rotation:

```bash
# Crea file /etc/logrotate.d/mygest-cleanup
sudo nano /etc/logrotate.d/mygest-cleanup

# Contenuto:
/home/sandro/mygest/logs/cleanup_tmp.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

### Monitoring spazio disco

Aggiungi check spazio dopo cleanup:

```bash
# Script con check finale
0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7 && du -sh /home/sandro/mygest/media/tmp
```

## Troubleshooting

### Cron non esegue lo script

1. **Verifica permessi**:
```bash
ls -l /home/sandro/mygest/scripts/cleanup_tmp.sh
# Deve essere -rwxr-xr-x
```

2. **Verifica path assoluti**:
Il cron non usa le stesse variabili ambiente della shell.
Lo script già usa path assoluti.

3. **Verifica log cron di sistema**:
```bash
grep CRON /var/log/syslog | tail -20
```

4. **Test con utente cron**:
```bash
# Simula ambiente cron
env -i HOME="$HOME" /bin/bash -c '/home/sandro/mygest/scripts/cleanup_tmp.sh 7'
```

### Lo script non trova Python/Django

Verifica che il path nel file `scripts/cleanup_tmp.sh` sia corretto:
```bash
VENV_PYTHON="/home/sandro/mygest/venv/bin/python"
```

### Log non viene creato

Verifica permessi directory:
```bash
mkdir -p /home/sandro/mygest/logs
chmod 755 /home/sandro/mygest/logs
```

## Rimozione Cron Job

Per disabilitare/rimuovere:

```bash
# Apri crontab
crontab -e

# Commenta la riga (aggiungi # all'inizio):
# 0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7

# O elimina completamente la riga

# Salva e chiudi
```

## Best Practices

1. **Retention consigliato**: 7-14 giorni
2. **Orario consigliato**: 2-4 AM (basso traffico)
3. **Frequenza**: Giornaliera o ogni 12 ore
4. **Monitoraggio**: Controlla log settimanalmente
5. **Alert**: Configura alert se spazio disco > 80%

## Quick Install (Tutto in un comando)

```bash
# Aggiungi cron job e verifica
(crontab -l 2>/dev/null; echo "0 2 * * * /home/sandro/mygest/scripts/cleanup_tmp.sh 7") | crontab - && \
echo "✓ Cron job aggiunto" && \
crontab -l | grep cleanup_tmp
```

## Status Check

Esegui questo per verificare tutto:

```bash
#!/bin/bash
echo "=== Status Cleanup Tmp ==="
echo ""
echo "Script eseguibile:"
ls -l /home/sandro/mygest/scripts/cleanup_tmp.sh
echo ""
echo "Cron job installato:"
crontab -l | grep cleanup_tmp || echo "⚠ Nessun cron job trovato"
echo ""
echo "Log esistente:"
ls -lh /home/sandro/mygest/logs/cleanup_tmp.log 2>/dev/null || echo "⚠ Nessun log ancora"
echo ""
echo "Servizio cron:"
systemctl is-active cron
```

Salva come `scripts/check_cleanup_status.sh` e esegui quando necessario.
