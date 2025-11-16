# Guida per principianti – App "Scadenze"

Questa guida introduce passo passo la nuova app `scadenze`, pensata per gestire scadenze condivise tra pratiche, fascicoli e documenti. Troverai indicazioni sia backend (modelli, servizi, test) sia frontend (template, form) con esempi pratici per iniziare subito.

---

## 1. Setup iniziale

### 1.1 Ambiente di sviluppo

1. Attiva il virtualenv del progetto (vedi guida generale in `docs/guida_principianti_backend_frontend.md`).
2. Assicurati di avere la app registrata in `INSTALLED_APPS` (già presente in `mygest/settings.py`).
3. Esegui le migrazioni per avere il nuovo schema completo:

```bash
python manage.py migrate scadenze
```

> Nota: la migrazione `scadenze/0002_migrate_pratiche_scadenze.py` importa le vecchie scadenze dal modulo `pratiche`.

### 1.2 Dati di prova

Crea un superuser e accedi all'admin per inserire alcuni dati reali:

```bash
python manage.py createsuperuser
```

Dal pannello admin (
`/admin/scadenze/scadenza/`
) potrai creare le scadenze di test da riutilizzare negli esempi.

---

## 2. Architettura backend della app

### 2.1 Modelli principali (`scadenze/models.py`)

- **Scadenza**: contiene le informazioni di alto livello (titolo, stato, priorità, periodicità) e le relazioni M2M con pratiche, fascicoli, documenti.
- **ScadenzaOccorrenza**: rappresenta un evento puntuale (data di inizio/fine, metodo di alert, stato, eventuale sync Google Calendar).
- **ScadenzaNotificaLog**: traccia le notifiche inviate o gli errori di sincronizzazione.
- **ScadenzaWebhookPayload**: memorizza i payload inviati ai webhook esterni.

Schema semplificato:

```
Scadenza (M2M) ──< ScadenzaOccorrenza ──< ScadenzaNotificaLog
                                     └─< ScadenzaWebhookPayload
```

### 2.2 Servizi chiave (`scadenze/services.py`)

- **OccurrenceGenerator**: genera serie di occorrenze future in base alla periodicità. Metodi principali:
  ```python
  generator = OccurrenceGenerator(scadenza)
  generator.generate(start=timezone.now(), count=5)
  ```

- **AlertDispatcher**: invia alert via app `comunicazioni` o webhook. Esempio:
  ```python
  dispatcher = AlertDispatcher()
  dispatcher.dispatch(occorrenza)
  ```

- **GoogleCalendarSync**: sincronizza le occorrenze con Google Calendar (se configurato con credenziali).

### 2.3 Form e formset (`scadenze/forms.py`)

- **ScadenzaForm**: form principale, con widget Select2 per collegare facilmente pratiche/fascicoli/documenti.
- **ScadenzaOccorrenzaFormSet**: inline formset per gestire occorrenze direttamente dalla pagina di editing.
- **ScadenzaBulkOccurrencesForm**: utilizzato dalla vista `bulk_generate` per creare occorrenze in serie.

### 2.4 Viste (`scadenze/views.py`)

- `home`: elenco scadenze filtrabili e ordinabili.
- `detail`: mostra la scadenza con occorrenze e log.
- `create` / `update`: form di creazione e modifica, con inline formset.
- `bulk_generate`: procedura guidata per generare occorrenze massive.
- `trigger_alert`: endpoint per inviare manualmente l'alert di una occorrenza.

### 2.5 URL (`scadenze/urls.py`)

```python
urlpatterns = [
    path("", views.home, name="home"),
    path("nuova/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifica/", views.update, name="update"),
    path("<int:pk>/bulk/", views.bulk_generate, name="bulk_generate"),
    path("occorrenze/<int:occorrenza_pk>/trigger-alert/", views.trigger_alert, name="trigger_alert"),
]
```

### 2.6 Test di base (`scadenze/tests/`)

Scrivi test per verificare:
- Creazione di scadenze e occorrenze.
- Generazione massiva.
- Trigger degli alert (mockando comunicazioni/webhook).

Esempio rapido:

```python
from django.test import TestCase
from django.utils import timezone

from scadenze.models import Scadenza
from scadenze.services import OccurrenceGenerator


class OccurrenceGeneratorTests(TestCase):
    def test_generate_occurrences(self):
        scadenza = Scadenza.objects.create(titolo="Scadenza di prova")
        OccurrenceGenerator(scadenza).generate(
            start=timezone.now(),
            count=3,
            metodo_alert="email",
        )
        self.assertEqual(scadenza.occorrenze.count(), 3)
```

Esegui i test:

```bash
python manage.py test scadenze
```

---

## 3. Esempi pratici backend

### 3.1 Creare una scadenza via shell

```python
python manage.py shell
```

```python
from django.utils import timezone
from scadenze.models import Scadenza, ScadenzaOccorrenza

scad = Scadenza.objects.create(
    titolo="Monitoraggio tasa di bollo",
    descrizione="Verifica documenti trimestrali",
)

ScadenzaOccorrenza.objects.create(
    scadenza=scad,
    titolo="Scadenza Q1",
    inizio=timezone.now() + timezone.timedelta(days=7),
    metodo_alert="email",
    alert_config={"destinatari": "team@azienda.it"},
)
```

### 3.2 Generare occorrenze massive con periodicità

```python
from django.utils import timezone
from scadenze.models import Scadenza
from scadenze.services import OccurrenceGenerator

scad = Scadenza.objects.create(
    titolo="Riunione follow-up",
    periodicita="weekly",
    periodicita_intervallo=2,
)

generator = OccurrenceGenerator(scad)
occ = generator.generate(
    start=timezone.now(),
    count=5,
    metodo_alert="email",
    alert_config={"destinatari": "responsabili@azienda.it"},
)
print(f"Generate {len(occ)} occorrenze")
```

### 3.3 Sincronizzare manualmente con Google Calendar (pseudo)

```python
from scadenze.services import GoogleCalendarSync
from scadenze.models import Scadenza

sync = GoogleCalendarSync()
scad = Scadenza.objects.get(pk=1)
sync.ensure_calendar(scad)
sync.sync_occurrences(scad)
```

> Assicurati di aver configurato le credenziali Google in `settings.py` e impostato `google_calendar_calendar_id` sulla scadenza.

---

## 4. Frontend: template e UX

### 4.1 Template principali

- `scadenze/templates/scadenze/home.html`: panoramica scadenze con filtri.
- `scadenze/templates/scadenze/detail.html`: dettaglio della scadenza, occorrenze, log e azioni.
- `scadenze/templates/scadenze/form.html`: form di creazione/modifica (con riassunto selezioni M2M e inline formset per le occorrenze).
- `scadenze/templates/scadenze/bulk_generate.html`: procedura guidata per generare le occorrenze massivamente.

### 4.2 Consigli UX già integrati

- **Select2** per scegliere pratiche, fascicoli, documenti: ricerca rapida con label arricchite (codice, titoli, clienti).
- **Riepilogo selezioni** nel form della scadenza: chip che riassumono le scelte attuali.
- **Sezioni chiare**: metadati, collegamenti e occorrenze sono separati visivamente.

### 4.3 Aggiungere azioni rapide

Per aggiungere un pulsante rapido nel dettaglio scadenza (es. invio alert manuale):

```django
<!-- scadenze/detail.html -->
<a class="btn btn-sm btn-outline-primary" href="{% url 'scadenze:trigger_alert' occ.pk %}">
  Invia alert
</a>
```

### 4.4 Snippet per mostrare occorrenze imminenti altrove

Nel template di una pratica (`pratiche/dettaglio.html`):

```django
{% if scadenze %}
  <section class="card">
    <h2>Scadenze correlate</h2>
    <ul class="list">
      {% for scad in scadenze %}
        <li>
          {{ scad.titolo }} – prossima: {{ scad.prossima_occorrenza.inizio|date:"d/m/Y H:i" }}
          <a href="{% url 'scadenze:detail' scad.pk %}" class="btn btn-xs">Dettaglio scadenza</a>
        </li>
      {% endfor %}
    </ul>
  </section>
{% endif %}
```

### 4.5 Componenti riutilizzabili

- Valuta la creazione di tag personalizzati (in `scadenze/templatetags/`) per elementi ricorrenti, ad es. badge di stato delle occorrenze o link all’ultimo log registrato.

---

## 5. Esempi pratici frontend

### 5.1 Creare una nuova scadenza dal browser

1. Vai su `Scadenze → Nuova scadenza`.
2. Compila titolo, priorità, periodicità.
3. Associa pratiche e documenti digitando nel campo (si popola via Select2).
4. Crea almeno un’occorrenza (data e metodo di alert).
5. Salva: verrai reindirizzato al dettaglio, dove puoi aggiungere log, inviare alert, generare occorrenze massivamente.

### 5.2 Generazione massiva dal frontend

1. Dal dettaglio scadenza, clicca su “Genera occorrenze”.
2. Imposta data di partenza, numero occorrenze e canale di notifica.
3. Conferma: verrai reindirizzato al dettaglio, con lista aggiornata delle occorrenze.

### 5.3 Personalizzare il layout

Per adattare il form a una grafica aziendale:
- Modifica `static/css/app.css` o crea un file dedicato sotto `static/scadenze/css/`.
- Estendi `base.html` aggiungendo blocchi in `{% block extra_head %}` se servono stili/JS aggiuntivi.

```django
{% block extra_head %}
<link rel="stylesheet" href="{% static 'scadenze/css/custom.css' %}">
{% endblock %}
```

---

## 6. Checklist per il deploy

- [ ] Migrazioni eseguite (`python manage.py migrate scadenze`).
- [ ] Credenziali Google Calendar caricate (se necessarie).
- [ ] Test automatizzati verdi (`python manage.py test scadenze`).
- [ ] Job pianificato per generare/controllare occorrenze (es. comando cron che richiama un `management command`).
- [ ] Documentazione aggiornata (`docs/guida_scadenze_principianti.md`).

---

## 7. Risorse utili

- Documentazione Django: https://docs.djangoproject.com/en/4.2/
- Guida Select2: https://select2.org/
- Google Calendar API (Python): https://developers.google.com/calendar/api

---

Prendi confidenza sperimentando con i servizi e i template forniti: la separazione tra dominio (backend) e presentazione (frontend) ti permette di estendere l’app scadenze in modo trasversale a tutto MyGest.
