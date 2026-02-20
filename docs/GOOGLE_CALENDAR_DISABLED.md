# Sincronizzazione Google Calendar - Stato: DISABILITATA

## Stato Attuale

La sincronizzazione automatica con Google Calendar è **temporaneamente disabilitata**.

### Cosa Significa

- ✅ Le scadenze e le occorrenze funzionano normalmente
- ✅ Gli alert vengono inviati correttamente
- ✅ Tutta la funzionalità di MyGest è operativa
- ❌ Le occorrenze NON vengono sincronizzate automaticamente con Google Calendar
- ❌ Il comando `python manage.py sync_google_calendar` non funzionerà fino alla configurazione

### Perché è Disabilitata

La sincronizzazione richiede:
1. Un Service Account Google Cloud configurato
2. Un file di credenziali JSON
3. Un Google Calendar condiviso con il service account

Questi requisiti non sono ancora stati configurati.

## Come Riabilitare la Sincronizzazione

Quando vorrai abilitare la sincronizzazione con Google Calendar:

### 1. Configura Google Cloud

Segui la guida completa: **[docs/GOOGLE_CALENDAR_SETUP.md](docs/GOOGLE_CALENDAR_SETUP.md)**

Oppure consulta la guida rapida: **[GOOGLE_CALENDAR_ERROR.md](GOOGLE_CALENDAR_ERROR.md)**

### 2. Verifica la Configurazione

```bash
python check_google_calendar_config.py
```

### 3. Riabilita i Signal

Modifica il file `/home/sandro/mygest/scadenze/models.py` (ultime righe):

```python
# Decommenta queste righe:
post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_sync_google")
post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_delete_google")
```

### 4. Riavvia il Server

```bash
# Se usi runserver
python manage.py runserver

# Se usi gunicorn/uwsgi in produzione
sudo systemctl restart mygest
```

### 5. Sincronizza le Occorrenze Esistenti

```bash
# Test senza modifiche
python manage.py sync_google_calendar --dry-run

# Sincronizza tutte le occorrenze
python manage.py sync_google_calendar --all
```

## Vantaggi della Sincronizzazione

Quando abilitata, la sincronizzazione con Google Calendar offre:

- 📅 **Visualizzazione centralizzata**: Vedi tutte le scadenze nel calendario Google
- 🔄 **Sincronizzazione automatica**: Modifiche in MyGest si riflettono automaticamente in Google Calendar
- 📱 **Accesso mobile**: Usa l'app Google Calendar su smartphone/tablet
- 🔔 **Notifiche multiple**: Oltre agli alert di MyGest, ricevi anche le notifiche di Google Calendar
- 👥 **Condivisione facile**: Condividi il calendario con colleghi/clienti
- 🌐 **Accessibilità**: Accedi alle scadenze da qualsiasi dispositivo con Google Calendar

## Note Tecniche

### Dove Sono Disabilitati i Signal

File: `/home/sandro/mygest/scadenze/models.py` (righe finali)

```python
# Google Calendar sync temporaneamente disabilitato
# post_save.connect(_sync_calendar_after_save, ...)
# post_delete.connect(_delete_calendar_event, ...)
```

### Funzionalità Ancora Disponibili

Anche con la sincronizzazione disabilitata:
- ✅ Comando `python manage.py sync_google_calendar` (manuale, dopo configurazione)
- ✅ API `GoogleCalendarSync` (utilizzabile via codice)
- ✅ Tutti i test passano correttamente
- ✅ Il campo `google_calendar_event_id` rimane nel database per uso futuro

### Test

I test di sincronizzazione sono ancora disponibili e funzionanti:
```bash
python manage.py test scadenze.tests.test_google_calendar_sync
python manage.py test scadenze.tests.test_sync_command
```

Questi test utilizzano mock per simulare Google Calendar, quindi funzionano anche senza credenziali configurate.

## Domande Frequenti

**Q: Posso usare MyGest senza Google Calendar?**  
A: Sì, assolutamente! MyGest funziona completamente in modo autonomo.

**Q: Perderò dati disabilitando la sincronizzazione?**  
A: No, nessun dato viene perso. Le occorrenze sono salvate nel database di MyGest.

**Q: Quando dovrei abilitare la sincronizzazione?**  
A: Quando hai bisogno di visualizzare le scadenze in Google Calendar o condividerle con altri.

**Q: Quanto tempo richiede la configurazione?**  
A: Circa 15-20 minuti seguendo la guida completa.

**Q: Posso testare la sincronizzazione senza modificare dati?**  
A: Sì, usa il comando con `--dry-run` per vedere cosa succederebbe senza fare modifiche.

## Contatti e Supporto

Per domande o problemi:
- Consulta la documentazione in `docs/GOOGLE_CALENDAR_SETUP.md`
- Usa lo script di diagnostica: `python check_google_calendar_config.py`
- Controlla i log in `ScadenzaNotificaLog` per dettagli sugli errori
