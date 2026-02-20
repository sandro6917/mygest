# Mailing list e compliance privacy

Questo documento riassume le funzionalità introdotte per supportare la gestione del consenso e della disiscrizione dalle mailing list di studio.

## Novità principali

- **Finalità della mailing list**: ogni lista ora espone il campo `finalita` (`SERVIZIO` oppure `MARKETING`). Le liste marketing richiedono un consenso esplicito dei destinatari.
- **Tracciamento del consenso**: i contatti (`EmailContatto`) e gli indirizzi extra delle liste memorizzano:
  - `marketing_consent`
  - `marketing_consent_acquired_at`
  - `marketing_consent_source`
- **Opt-out puntuale**: sia le membership sia gli indirizzi extra tengono traccia di una eventuale disiscrizione (`disiscritto_il`, `disiscritto_note`).
- **Token di disiscrizione**: il modello `MailingListUnsubscribeToken` genera link univoci inviati tramite email per completare il processo self-service.
- **Form pubblico**: `/comunicazioni/preferenze/` consente ai destinatari di richiedere un link di opt-out in autonomia.
- **Verifiche in fase di invio**: il form delle comunicazioni blocca l'invio a contatti privi di consenso quando vengono selezionate liste marketing; l'estrazione dei destinatari filtra automaticamente chi si è disiscritto o non ha autorizzato l'uso marketing.
- **Template email**: `newsletter_studio.html` include il link alle preferenze per soddisfare gli obblighi informativi.

## Flusso operativo suggerito

1. Imposta `finalita = MARKETING` sulle liste dedicate ad aggiornamenti volontari e registra l'informativa specifica (campo `informativa_privacy_url`).
2. Raccogli il consenso segnando i nuovi campi su `EmailContatto` o sugli indirizzi extra.
3. Durante la composizione delle comunicazioni, seleziona esclusivamente liste con contatti che abbiano espresso consenso; eventuali violazioni vengono segnalate dal form.
4. Inserisci nei template il link alla pagina preferenze per permettere agli utenti di richiedere il token di disiscrizione.
5. Quando l'utente conferma l'opt-out, il sistema revoca automaticamente il consenso e marca la membership come disattiva, preservando l'audit trail.

## TODO / estensioni

- Automatizzare la generazione del token durante l'invio per includerlo dinamicamente in ogni messaggio.
- Esporre API per interrogare/storicizzare il registro dei consensi.
- Integrare report periodici sullo stato dei consensi per supportare il registro dei trattamenti.
