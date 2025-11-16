# Guida per principianti: backend e frontend di MyGest

Questa guida accompagna passo passo nello sviluppo sia lato backend sia lato frontend dell'applicazione MyGest. E' pensata per chi non ha mai lavorato con il progetto e vuole un riferimento pratico immediato.

---

## 1. Requisiti di base

- Sistema operativo: Linux o macOS (funziona anche su Windows tramite WSL).
- Python 3.10 o successivo.
- Git per la gestione del codice sorgente.
- Accesso a un database PostgreSQL o SQLite (di default viene usato SQLite in sviluppo).
- Editor consigliato: Visual Studio Code con estensioni Python e Django.

### Installazione rapida su Linux/WSL

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git
```

---

## 2. Clonare il progetto e creare il virtualenv

```bash
git clone <URL_DEL_REPO> mygest
cd mygest
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> Suggerimento: aggiungi `source venv/bin/activate` al tuo file `~/.bashrc` per attivare l'ambiente in automatico quando entri nella cartella del progetto.

---

## 3. Configurazione locale

1. Copia il file degli esempi di impostazioni (se disponibile) oppure crea `mygest/local_settings.py` per sovrascrivere valori sensibili.
2. Imposta variabili d'ambiente utili:

```bash
export DJANGO_SETTINGS_MODULE=mygest.settings
export DEBUG=1
```

3. Se usi PostgreSQL, configura l'accesso nel file `local_settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mygest",
        "USER": "mygest",
        "PASSWORD": "mypassword",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
```

---

## 4. Avviare il database e applicare le migrazioni

```bash
python manage.py migrate
```

Questo comando crea tutte le tabelle necessarie, incluse quelle della nuova app `scadenze` che gestisce in modo centralizzato le scadenze.

Per creare un utente amministratore:

```bash
python manage.py createsuperuser
```

---

## 5. Avvio del server di sviluppo

```bash
python manage.py runserver
```

Visita `http://127.0.0.1:8000/` per verificare che tutto funzioni. L'area admin e' disponibile su `/admin/`.

---

## 6. Panoramica dell'architettura backend

### 6.1 Struttura Django principale

- `mygest/settings.py`: configurazione generale del progetto (apps, database, middleware, static files).
- `mygest/urls.py`: routing principale che include le url delle singole app (`pratiche`, `scadenze`, ecc.).
- `mygest/views.py`: pagine generiche (home, help) che aggregano dati da piu' app.

### 6.2 App chiave

| App        | Responsabilita' principali |
|------------|-----------------------------|
| `pratiche` | Gestione pratiche, note, relazioni e viste legate al lavoro operativo. |
| `scadenze` | Gestione autonoma delle scadenze con modelli, occorrenze, sincronizzazione e notifiche. |
| `documenti`, `fascicoli`, `comunicazioni` | Altre aree funzionali integrate con le scadenze tramite relazioni M2M. |

### 6.3 Modelli della nuova app `scadenze`

- `Scadenza`: definisce la scadenza di alto livello con metadati, periodicita', assegnatari, relazioni M2M verso pratiche, fascicoli e documenti.
- `ScadenzaOccorrenza`: singola istanza con data/ora, metodo di alert, stato e integrazione con Google Calendar.
- `ScadenzaNotificaLog`: storico dei tentativi di alert, sincronizzazioni e webhook.
- `ScadenzaWebhookPayload`: memorizza payload e risposte HTTP quando viene inviato un webhook.

Ogni occorrenza fa riferimento a una scadenza, e i servizi dedicati generano occorrenze periodiche, inviano notifiche ed eseguono sincronizzazioni esterne.

### 6.4 Servizi principali (`scadenze/services.py`)

- `OccurrenceGenerator`: calcola serie di occorrenze usando i parametri di periodicita'.
- `AlertDispatcher`: prepara ed invia notifiche (es. tramite app `comunicazioni` o webhook).
- `GoogleCalendarSync`: interfaccia verso Google Calendar, con import condizionale della libreria Google.

### 6.5 Forms e formset

- `ScadenzaForm`: form base per creare/modificare scadenze (gestione M2M con pratiche e documenti).
- `ScadenzaOccorrenzaForm` e `ScadenzaOccorrenzaFormSet`: gestione inline delle occorrenze collegate.
- `ScadenzaBulkOccurrencesForm`: consente la generazione massiva di occorrenze partendo da una scadenza.

### 6.6 Migrazioni

Dopo la separazione della logica, la sequenza corretta e':

1. `scadenze/0001_initial.py` crea le nuove tabelle.
2. `scadenze/0002_migrate_pratiche_scadenze.py` copia i dati ereditati da `pratiche`.
3. `pratiche/0008_remove_scadenza...` elimina i vecchi modelli.
4. `scadenze/0003_alter...` aggiorna indici e constraint.

Se modifichi i modelli, esegui:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6.7 Test automatizzati

I test vivono per ogni app (es. `pratiche/tests.py`). Dopo ogni modifica significativa:

```bash
python manage.py test
```

Per eseguire test di una sola app:

```bash
python manage.py test pratiche
```

---

## 7. Flusso di lavoro backend consigliato

1. **Crea o aggiorna un modello**: modifica `models.py` nella app interessata.
2. **Genera migrazioni**: `python manage.py makemigrations app_name`.
3. **Esegui le migrazioni**: `python manage.py migrate`.
4. **Scrivi/aggiorna test**: controlla che i nuovi scenari siano coperti.
5. **Esegui i test**: `python manage.py test`.
6. **Controlla il server**: avvialo e verifica le pagine coinvolte.

Suggerimento: usa `python manage.py shell_plus` (dopo aver installato `django-extensions`) per sperimentare rapidamente con ORM e servizi.

---

## 8. Panoramica frontend (temi, template, asset)

### 8.1 Template Django

- Le pagine ereditano da `templates/base.html` o `templates/base_home.html`.
- Ogni app tiene i propri template in `app/templates/app/...` (es. `scadenze/templates/scadenze/home.html`).
- I template usano blocchi standard: `block title`, `block content`, `block extra_js`, ecc.

### 8.2 Static files

- CSS globale in `static/css/`.
- Per aggiungere risorse custom, usa la cartella `static/` dell'app o del progetto.
- Ricorda di includere `{% load static %}` all'inizio del template e referenziare i file con `{% static 'percorso/file.css' %}`.

### 8.3 Componenti esistenti

- **Dashboard pratiche** (`pratiche/templates/pratiche/home.html`): mostra ultimi elementi, scadenze imminenti, filtri per tipo.
- **Dettaglio scadenza** (`scadenze/templates/scadenze/detail.html`): presenta metadati, occorrenze collegate, azioni di trigger.
- **Form scadenza** (`scadenze/templates/scadenze/form.html`): form layout con sezioni per metadati, assegnazioni e configurazioni di alert.
- **Bulk generate** (`scadenze/templates/scadenze/bulk_generate.html`): wizard per creare occorrenze in serie.

---

## 9. Flusso di lavoro frontend consigliato

1. Identifica il template da modificare o duplicare.
2. Aggiungi il blocco di contenuto desiderato utilizzando HTML + template tag.
3. Per logiche di presentazione complesse, valuta template filter o inclusion tag (da definire in `templatetags/`).
4. Usa la classe `select2` per i campi select multipli integrati (gia' presente in `ScadenzaForm`).
5. Per layout responsivi semplici, sfrutta le classi `.container`, `.card`, `.list` gia' presenti nel progetto.

### Debug frontend

- Usa `python manage.py runserver` e strumenti dev del browser.
- Per vedere il contesto passato a un template, inserisci temporaneamente `{{ variable|json_script:"id" }}` o `{{ variable }}`.
- Ricordati di rimuovere debug print finali.

---

## 10. Collegare backend e frontend

1. **Definisci la vista** in `views.py` che prepara i dati (QuerySet, form, ecc.).
2. **Configura l'URL** in `urls.py` con `path()` o `re_path()`.
3. **Crea/aggiorna il template** per visualizzare i dati.
4. **Aggiungi test** per la vista (status code, contenuto, permessi).
5. **Verifica manuale** dal browser e in admin se necessario.

Esempio rapido (scadenza detail):

- Vista: `scadenze/views.py::detail` prepara `scadenza`, `occorrenze`, `formset`.
- URL: `scadenze/urls.py` include `path("<int:pk>/", views.detail, name="detail")`.
- Template: `scadenze/templates/scadenze/detail.html` mostra dati e formset.

---

## 11. Strumenti utili

- `python manage.py shell`: interagisce con ORM.
- `python manage.py dumpdata app.Model`: esportazione dati di prova.
- `python manage.py check --deploy`: controlli di sicurezza per la produzione.
- `python manage.py collectstatic`: prepara asset statici per deploy (non necessario in sviluppo).

---

## 12. Checklist prima del commit

- [ ] Ambiente virtuale attivo.
- [ ] Migrazioni generate e applicate.
- [ ] Test automatizzati eseguiti con successo.
- [ ] Template e statici verificati nel browser.
- [ ] Nessun file temporaneo o credenziale nel commit.

---

## 13. Prossimi passi suggeriti

1. Leggi il codice di `scadenze/services.py` per capire come integrare nuovi canali di notifica.
2. Aggiungi test personalizzati in `scadenze/tests/` per coprire i tuoi casi d'uso.
3. Se devi creare una pagina complessa, valuta l'uso di componenti riutilizzabili (inclusion tag o partial template).
4. Documenta ogni nuova funzionalita' in `docs/` per facilitare altri sviluppatori.

---

## 14. Risorse di approfondimento

- Documentazione Django: https://docs.djangoproject.com/en/4.2/
- Guida Django ORM: https://docs.djangoproject.com/en/4.2/topics/db/queries/
- Template language: https://docs.djangoproject.com/en/4.2/ref/templates/language/
- Guida a Django Rest Framework (se servono API REST): https://www.django-rest-framework.org/
- Bootstrap (per UI responsive): https://getbootstrap.com/

---

Benvenuto in MyGest! Segui questa guida per prendere confidenza con il codice; sperimentando con piccole modifiche imparerai rapidamente le basi del progetto.
