# Verbali di consegna – Guida operativa ai template Word

Questa guida spiega come predisporre, caricare e utilizzare i template Word collegati alle operazioni di archivio fisico. La funzionalità è alimentata dal modello `VerbaleConsegnaTemplate` e dal motore di rendering `docxtpl`, che permette di inserire segnaposto Jinja all'interno dei file `.docx`.

## 1. Prerequisiti
- **Dipendenze Python**: assicurarsi che l'ambiente abbia installato `docxtpl` (`pip install docxtpl`). Per generare esempi locali è utile anche `python-docx`.
- **Permessi**: l'utente deve avere accesso all'area amministrativa (`/admin`) per creare o modificare i template.
- **Percorso file**: i documenti vengono caricati all'interno dello storage configurato in `ARCHIVIO_BASE_PATH` (cartella `archivio_fisico/verbali/`).

## 2. Creazione di un template in amministrazione
1. Accedere a **Amministrazione → Archivio fisico → Template verbali di consegna**.
2. Compilare i campi principali:
   - **Nome**: descrizione leggibile (es. `Verbale consegna uscita esterna`).
   - **File template**: caricare il `.docx` predisposto con i segnaposto.
   - **Filename pattern** *(opzionale)*: definire la regola di generazione del nome file (es. `verbale_{operazione_tipo}_{timestamp:%Y%m%d}.docx`).
   - **Default**: spuntare se deve essere proposto automaticamente nel download.
3. Salvare; se impostato `Default`, gli altri template verranno automaticamente marcati come non predefiniti.

## 3. Struttura del contesto disponibile nei template
Nel file `.docx` possono essere utilizzate le seguenti variabili (sintassi `{{ ... }}` oppure blocchi `{% ... %}`):

| Path | Descrizione |
| --- | --- |
| `operazione.id` | ID interno dell'operazione |
| `operazione.tipo` / `operazione.tipo_label` | Codice e etichetta dell'operazione (`entrata`, `uscita`, `movimento interno`) |
| `operazione.data_ora.date_it` | Data in formato `gg/mm/aaaa` |
| `operazione.data_ora.time_it` | Ora locale `HH:MM` |
| `operazione.referente_interno.full_name` | Nome e cognome del referente interno |
| `operazione.referente_esterno.display` | Denominazione dell'anagrafica esterna, se presente |
| `unita.sorgente.*` / `unita.destinazione.*` | Dati delle unità fisiche coinvolte (codice, nome, full_path, ecc.) |
| `movimento_protocollo.protocollo` | Numero di protocollo formattato `anno/000123` (solo se tutte le righe condividono lo stesso movimento) |
| `righe[n].movimento_protocollo.*` | Movimento di protocollo collegato alla singola riga (se presente) |
| `righe` | Lista di dizionari, uno per ogni documento/fascicolo movimentato |
| `righe[n].documento.*` | Dati del documento, compreso `movimenti_protocollo` (lista) |
| `righe[n].fascicolo.*` | Dati del fascicolo, con eventuale elenco movimenti |
| `timestamp.date_it` | Data/ora di generazione del verbale |

### Esempio di percorso completo
```text
{{ righe[0].documento.cliente.display }}
{{ righe[0].documento.movimenti_protocollo[-1].destinatario }}
```

## 4. Creazione del file `.docx`
Di seguito due casi pratici per costruire un template.

### 4.1 Template lineare (paragrafi)
1. Aprire Microsoft Word o LibreOffice Writer.
2. Inserire i seguenti paragrafi:
   ```text
   Verbale di consegna – {{ operazione.tipo_label }}
   Data operazione: {{ operazione.data_ora.date_it }} alle ore {{ operazione.data_ora.time_it }}
   Referente interno: {{ operazione.referente_interno.full_name }}
   Referente esterno: {{ operazione.referente_esterno.display or "-" }}
   ```
3. Aggiungere un blocco per l'elenco delle righe:
   ```text
   Documenti consegnati:
   {% for riga in righe %}
   • {{ riga.documento.codice }} – {{ riga.documento.descrizione }} (da {{ riga.stato_precedente }} a {{ riga.stato_successivo }})
   {% endfor %}
   ```
4. Salvare il file come `verbale_base.docx` e caricarlo nel back-office.

### 4.2 Template tabellare (Word + tabella)
1. Inserire una tabella 4 colonne × N righe e impostare l'intestazione:
   ```text
   Codice | Descrizione | Stato precedente | Stato successivo
   ```
2. Nella riga successiva usare la sintassi dei segnaposto all'interno della tabella:
   ```text
   {% for riga in righe %}
   {{ riga.documento.codice or riga.fascicolo.codice }} | {{ riga.documento.descrizione or riga.fascicolo.titolo }} | {{ riga.stato_precedente }} | {{ riga.stato_successivo }}
   {% endfor %}
   ```
   > Nota: in Word, ogni cella deve contenere il placeholder corrispondente. È possibile visualizzare i codici di campo per verificare la corretta formattazione.
3. Aggiungere eventuali blocchi condizionali, per esempio la sezione Protocollo:
   ```text
   {% if movimento_protocollo %}
   Protocollo collegato: {{ movimento_protocollo.protocollo }} del {{ movimento_protocollo.data.date_it }}
   {% endif %}
   ```

## 5. Esempi completi da riutilizzare
Per comodità si riportano due esempi di contenuto che è possibile copiare in un documento Word.

### Esempio A – Verbale standard
```
Verbale di consegna – {{ operazione.tipo_label }}
Data operazione: {{ operazione.data_ora.date_it }} alle ore {{ operazione.data_ora.time_it }}

Responsabile interno: {{ operazione.referente_interno.full_name }} ({{ operazione.referente_interno.email }})
Destinatario: {{ operazione.referente_esterno.display or movimento_protocollo.destinatario or righe[0].movimento_protocollo.destinatario or "-" }}

Unità sorgente: {{ unita.sorgente.full_path or "N/D" }}
Unità destinazione: {{ unita.destinazione.full_path or "N/D" }}

{% if movimento_protocollo %}
Protocollo collegato: {{ movimento_protocollo.protocollo }} del {{ movimento_protocollo.data.date_it }}
{% endif %}

Documenti movimentati:
{% for riga in righe %}
- {{ riga.documento.codice }} – {{ riga.documento.descrizione }}
  Stato: {{ riga.stato_precedente }} → {{ riga.stato_successivo }}
  Note: {{ riga.note or "Nessuna" }}
{% endfor %}
```

### Esempio B – Verbale per fascicoli
```
Verbale di consegna fascicoli – {{ operazione.tipo_label }}
Cliente: {{ righe[0].fascicolo.cliente.anagrafica.display }}

{% for riga in righe %}
Fascicolo {{ riga.fascicolo.codice }} – {{ riga.fascicolo.titolo }}
Classificazione: {{ riga.fascicolo.titolario.codice }} - {{ riga.fascicolo.titolario.titolo }}
Movimenti di protocollo:
{% for mov in riga.fascicolo.movimenti_protocollo %}
  * {{ mov.protocollo }} – {{ mov.direzione_label }} ({{ mov.data.date_it }})
{% endfor %}
{% endfor %}
```

## 6. Distribuzione e utilizzo
- Dopo aver salvato il template, aprire l'operazione di archivio (`/archivio_fisico/operazioni/<id>/`).
- Nel pannello **Verbale di consegna** selezionare il template desiderato e premere **Scarica verbale Word**.
- Il file generato verrà nominato secondo il pattern indicato e conterrà i dati dell'operazione correntemente visualizzata.

## 7. Troubleshooting
- **Segnaposto non sostituiti**: verificare che la sintassi sia corretta (`{{ variabile }}`) e che non ci siano caratteri invisibili (ad esempio formattazione “Rich Text” in Word). In caso di problemi usare la funzione “Mostra/Nascondi ¶” e riscrivere i placeholder.
- **File danneggiato**: se Word segnala errori all'apertura, riaprire il template master e assicurarsi che non siano stati inseriti tag incompleti o parentesi sbilanciate.
- **Assenza di template**: confermare che il record sia `attivo` e che l'utente disponga dei permessi di lettura; senza template attivi il download restituirà un errore 404.
- **Nuovi campi**: in caso di modifiche al modello (es. nuovi attributi dell'operazione) aggiornare la guida o aggiungere riferimenti con un commento nel template stesso.

## 8. FAQ
- **Posso usare immagini o loghi?** Sì, Word gestisce normalmente le immagini. I segnaposto possono convivere con elementi grafici o intestazioni/piedipagina.
- **È possibile creare più versioni (ITA/ENG)?** Creare un template per lingua e usare il flag `Default` per impostare quella predefinita.
- **Come gestire firme digitali?** Si possono preparare campi vuoti nel documento per firme manuali oppure integrare soluzioni di firma elettronica a valle, salvando il `.docx` generato in PDF.

Con questa guida è possibile produrre verbali di consegna uniformi, sfruttando i dati presenti nel sistema e garantendo la tracciabilità delle movimentazioni di archivio.
