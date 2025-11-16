# Comunicazioni – Guida Completa e Operativa

Questa guida ti accompagna passo passo nell'utilizzo dell'app `comunicazioni`, dalla creazione di un messaggio all'invio e protocollazione finale. Include suggerimenti pratici per gli operatori, note per gli amministratori di sistema e riferimenti tecnici per gli sviluppatori.

---

## 1. Cos'è l'app Comunicazioni

- **Obiettivo**: generare, storicizzare e inviare comunicazioni via e-mail, mantenendo un legame con i documenti gestiti nel sistema e con il protocollo ufficiale.
- **Quando usarla**: ogni volta che devi avvisare un cliente, inoltrare documenti, inviare solleciti o archiviare una comunicazione ricevuta.
- **Dove si trova**: menu principale di MyGest, voce "Comunicazioni". Da qui accedi all'elenco generale e alle azioni rapide.
- **Prerequisiti**: profilo con permesso di lettura/scrittura sulle comunicazioni; rubriche aggiornate in `anagrafiche`; documenti caricati in `documenti` se vuoi allegarli o protocollarli.

---

## 2. Panorama rapido

| Funzione | Dove accederla | Chi la usa | Cosa fa |
|----------|----------------|-----------|---------|
| Elenco comunicazioni | Lista principale | Operatori | Filtra, cerca, apre le comunicazioni registrate |
| Nuova comunicazione | Pulsante "+ Nuova" | Operatori | Crea una bozza con destinatari, oggetto e corpo |
| Gestione allegati | Scheda dettaglio | Operatori | Collega documenti esistenti al messaggio |
| Invio e-mail | Azione "Invia" | Operatori | Spedisce la comunicazione e registra l'esito |
| Protocollazione | Azione "Protocolla" | Operatori autorizzati | Apre il form protocollo e collega movimento |
| Gestione template | `comunicazioni/models_template.py` | Admin funzionali | Aggiorna modelli precompilati |
| Invii massivi | `comunicazioni/services_massivo.py` | Admin funzionali | Avvia invii a liste o gruppi |

---

## 3. Flusso di lavoro consigliato

1. **Pianifica**: raccogli le informazioni chiave (destinatari, oggetto, messaggio, allegati necessari).
2. **Crea la bozza**: usa "Nuova comunicazione" e compila i campi base senza preoccuparti dell'invio immediato.
3. **Aggiungi allegati**: collega eventuali documenti già caricati. In caso manchino, caricali prima in `documenti`.
4. **Rivedi e valida**: apri il dettaglio, controlla anteprima, verificando recapiti e protocollazione prevista.
5. **Invia**: se tutto è corretto, conferma l'invio. In caso di comunicazioni inbound (ricevute), aggiorna manualmente lo stato.
6. **Protocolla**: se la comunicazione richiede protocollazione, completa l'iter dedicato subito dopo l'invio.
7. **Monitora**: verifica lo stato (Bozza, Inviata, Errore, Protocollata) e utilizza i filtri dell'elenco per report e controlli.

---

## 4. Creare una nuova comunicazione

- **Percorso**: Elenco comunicazioni → pulsante `+ Nuova comunicazione`.
- **Campi principali**:
  - `Oggetto`: titolo sintetico visibile anche nell'elenco.
  - `Destinatari`: uno o più indirizzi; supporta suggerimenti da `anagrafiche` se configurato.
  - `Corpo`: testo dell'e-mail; usa il formatter WYSIWYG incluso per grassetto, elenchi, link.
  - `Tipo`: scegli la categoria (es. Avviso, Invio documenti, Sollecito). Utile per filtri e statistiche.
  - `Direzione`: `OUT` per invii verso l'esterno, `IN` per comunicazioni ricevute da protocollare.
  - `Cliente` (facoltativo): collega la comunicazione a un'anagrafica per navigare più rapidamente tra le schede cliente.
  - `Documento da protocollare`: scegli un documento se prevedi la protocollazione successiva.
- **Salvataggio**: clicca "Salva". La comunicazione rimane in stato **Bozza** finché non avvii l'invio.

Suggerimento: usa le note interne (campo "Note" se abilitato) per riepilogare telefonate o decisioni collegate all'invio.

---

## 5. Gestire gli allegati

- **Aggiunta**: dalla scheda dettaglio, sezione "Allegati" → `Aggiungi allegato`.
- **Selezione**: compare la lista dei documenti caricati nel modulo `documenti`. Puoi filtrare per nome o codice.
- **Vincoli**:
  - un allegato può essere associato una sola volta alla stessa comunicazione;
  - il peso totale della e-mail dipende dal backend e-mail (verifica il limite configurato dall'amministratore).
- **Rimozione**: dalla lista allegati usa l'icona `x` accanto al documento da scollegare.
- **Ordine**: l'ordine di allegati segue l'inserimento. Se l'ordine è importante, eliminali e reinseriscili in sequenza.

---

## 6. Invio della comunicazione

- **Azione**: dalla scheda dettaglio clicca `Invia comunicazione`.
- **Conferma**: appare una pagina di riepilogo con tutti i dati (mittente, destinatari, allegati, anteprima corpo). Verifica e conferma.
- **Log invio**:
  - stato passa a **Inviata** se il backend email restituisce successo;
  - in caso di problemi, lo stato diventa **Errore**, con messaggio diagnostico visibile nella sezione "Attività".
- **Ritenta invio**: è possibile ritentare dall'azione dedicata dopo aver risolto il problema (es. correzione indirizzo).
- **Tracciamento**: tutti gli invii sono registrati nel modello `ComunicazioneLog` (consultabile da admin per audit dettagliati).

Per comunicazioni in ingresso (direzione `IN`), l'invio non è previsto: usa lo stato **Ricevuta** o personalizza il campo stato tramite admin se necessario.

---

## 7. Protocollare una comunicazione

- **Requisiti**:
  - `direzione` coerente con il tipo di movimento di protocollo (OUT per partenza, IN per arrivo);
  - `documento_protocollo` selezionato nella scheda principale;
  - permesso "Può protocollare comunicazioni" attivo.
- **Procedura**:
  1. Apri la comunicazione e scegli `Protocolla`.
  2. Compila i campi proposti dal form `protocollo` (ufficio, descrizione sintetica, classificazione, allegati di protocollo).
  3. Conferma: il sistema crea un `MovimentoProtocollo` e lo collega alla comunicazione.
- **Dopo la protocollazione**:
  - il campo `protocollo_movimento` diventa in sola lettura;
  - `direzione` e `documento_protocollo` non sono più modificabili dal form standard;
  - nell'elenco appare l'etichetta con numero e anno di protocollo.

Se devi annullare o correggere un protocollo, rivolgiti agli amministratori del modulo `protocollo`: non eliminare manualmente il collegamento senza seguire la procedura di annullamento.

---

## 8. Monitorare lo stato e trovare le comunicazioni

- **Filtri rapidi**: nell'elenco sono disponibili filtri per stato, tipo, direzione, cliente e intervallo di date.
- **Ricerca testo**: usa il campo ricerca per oggetto, protocollo, numero pratica o email destinatario.
- **Colori stato** (configurabili via CSS):
  - Bozza: grigio
  - Inviata: verde
  - Errore: rosso
  - Protocollata: blu
- **Esportazione**: se abilitata, trovi il pulsante `Esporta` per generare un CSV con i risultati filtrati.

---

## 9. Modelli, automazioni e invii massivi

- **Modelli di testo**: gestiti in `comunicazioni/models_template.py`. Gli admin funzionali possono aggiungere modelli via backend per precompilare oggetto e corpo.
- **Invio massivo**: `comunicazioni/services_massivo.py` offre helper per spedire la stessa comunicazione a gruppi selezionati. Prima di usarlo valuta:
  - limiti del server SMTP;
  - tracking e privacy (CCN vs invii individuali);
  - necessità di log dedicati.
- **Workflow automatizzati**: il modulo `tasks.py` può schedulare invii ricorrenti (cron Celery o RQ). Verifica con l'IT prima di attivarli in produzione.

---

## 10. Suggerimenti operativi

- Pianifica le comunicazioni importanti con anticipo per evitare sovrapposizioni.
- Usa nomi oggetto coerenti e ripetibili per facilitare la ricerca futura.
- Ricorda di aggiornare i contatti in `anagrafiche`: evita errori di invio dovuti a indirizzi obsoleti.
- Dopo un errore di invio, controlla il messaggio diagnostico; spesso indica problemi di autenticazione SMTP o destinatari non validi.
- Per comunicazioni con allegati voluminosi valuta l'uso di link di download protetti anziché allegare file pesanti.

---

## 11. Risoluzione dei problemi più comuni

- **Errore invio SMTP**: verifica le credenziali in `settings.py` o nei secret del server; controlla il log applicativo.
- **Destinatario non valido**: correggi l'indirizzo nel form e salva prima di ritentare.
- **Protocollazione bloccata**: assicurati che la comunicazione abbia `documento_protocollo` impostato e che tu abbia i permessi necessari.
- **Non vedo la comunicazione**: controlla i filtri attivi o i permessi associati al tuo profilo.
- **Allegato mancante**: se il documento non compare tra quelli selezionabili, verifica che sia pubblicato e visibile all'utente corrente nel modulo `documenti`.

Per problemi ricorrenti coinvolgi il team IT allegando l'ID comunicazione (`COM-XXXX`).

---

## 12. Note per amministratori di sistema

- **Configurazione e-mail**: l'app usa le impostazioni Django (`EMAIL_BACKEND`, `EMAIL_HOST`, ecc.). Assicurati che siano aggiornate e testate con `python manage.py check --deploy`.
- **Limiti allegati**: gestibili a livello SMTP o tramite middleware personalizzato.
- **Permessi**: i gruppi gestiscono le azioni (visualizzazione, creazione, invio, protocollazione). Aggiorna i ruoli dal pannello admin.
- **Log e audit**: le spedizioni sono tracciate in `ComunicazioneLog`; valuta rotazione log e backup periodici.
- **Integrazione con protocollo**: la correttezza dei dati dipende dal modulo `protocollo`. Mantieni allineate le classificazioni e i registri.
- **Monitoraggio code**: se usi Celery o sistemi asincroni per l'invio, verifica la salute dei worker.

---

## 13. Approfondimenti per sviluppatori

- **Struttura file**:
  - `models.py`: definizione di `Comunicazione`, `AllegatoComunicazione` e modelli di supporto.
  - `services.py`: include `protocolla_comunicazione` con transazioni e validazioni di business.
  - `services_massivo.py`: helper per invii in batch.
  - `tasks.py`: entry point per scheduler.
  - `api/`: eventuali endpoint REST/GraphQL.
- **Form**: `forms.py` protegge da modifiche improprie alle comunicazioni già protocollate.
- **Views**: `views.py` gestisce CRUD, invio e protocollazione; usa messaggi flash (`django.contrib.messages`).
- **Template**: in `templates/comunicazioni/` trovi `home.html`, `form.html`, `detail.html`, `invia.html`, `protocolla.html`. Tutti estendono i layout comuni del progetto.
- **Test**: esegui `python manage.py test comunicazioni` per validare protocollazione e casi limite sugli invii.
- **Migrazioni**: in `migrations/` le evoluzioni del modello; ricordati di generare nuove migrazioni al variare dei campi.

---

## 14. Checklist rapida prima del rilascio

1. Aggiorna dipendenze con `pip install -r requirements.txt` se sono cambiati servizi o integrazioni.
2. Esegui `python manage.py makemigrations && python manage.py migrate` per applicare eventuali modifiche strutturali.
3. Lancia i test di regressione: `python manage.py test comunicazioni`.
4. Fai un invio di prova verso un ambiente di test o una casella tecnica.
5. Verifica dall'interfaccia admin che protocollazione e allegati siano correttamente collegati.

Per ulteriori domande confrontati con i referenti dei moduli `documenti`, `protocollo` e `anagrafiche`, oppure contatta il team di sviluppo.
