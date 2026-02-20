# 🧪 Test Manuale - Importazione Anagrafiche

## Prerequisiti

Prima di iniziare il test:
- [ ] Server Django in esecuzione
- [ ] Database configurato
- [ ] Utente autenticato
- [ ] Accesso alla sezione Anagrafiche

## Avvio Server

```bash
cd /home/sandro/mygest
source venv/bin/activate  # Se usi virtualenv
python manage.py runserver
```

## Test Case 1: Download File Esempio

### Obiettivo
Verificare che il file CSV di esempio sia scaricabile e formattato correttamente.

### Passi
1. Naviga a: `http://localhost:8000/anagrafiche/import/`
2. Clicca sul pulsante **"Fac-simile CSV"**
3. Verifica che il file `facsimile_anagrafiche.csv` venga scaricato

### Verifica
- [ ] File scaricato con nome corretto
- [ ] Apri il file con un editor di testo
- [ ] Verifica header: `tipo;ragione_sociale;nome;...`
- [ ] Verifica separatore: `;` (punto e virgola)
- [ ] Verifica presenza di almeno 2 righe esempio (PF e PG)

### Risultato Atteso
✅ File CSV valido con esempi compilati correttamente

---

## Test Case 2: Importazione Persona Fisica Valida

### Obiettivo
Verificare che una persona fisica valida venga importata correttamente.

### Preparazione
Crea un file `test_pf.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Mario;Rossi;RSSMRA80A01H501U;;TEST001;ROSSI MARIO;mariorossi@pec.test.it;mario@test.it;3331234567;Via Roma 1, Milano;Test PF
```

### Passi
1. Naviga a: `http://localhost:8000/anagrafiche/import/`
2. Clicca su "Scegli file" e seleziona `test_pf.csv`
3. Clicca su **"Importa Anagrafiche"**

### Verifica Report
- [ ] Visualizzato report con statistiche
- [ ] Totale righe: 1
- [ ] Importate: 1
- [ ] Scartate: 0
- [ ] Tabella "Anagrafiche importate" visibile
- [ ] Riga con: "Mario Rossi", CF "RSSMRA80A01H501U"
- [ ] Link "Dettagli" presente e cliccabile

### Verifica Database
1. Clicca sul link "Dettagli" dalla tabella
2. Verifica che si apra la pagina dettaglio anagrafica
3. Controlla che i dati siano corretti:
   - [ ] Tipo: Persona Fisica
   - [ ] Nome: Mario
   - [ ] Cognome: Rossi
   - [ ] CF: RSSMRA80A01H501U
   - [ ] PEC: mariorossi@pec.test.it
   - [ ] Email: mario@test.it
   - [ ] Telefono: 3331234567

### Risultato Atteso
✅ Anagrafica creata correttamente con tutti i dati

---

## Test Case 3: Importazione Persona Giuridica Valida

### Obiettivo
Verificare che una persona giuridica valida venga importata correttamente.

### Preparazione
Crea un file `test_pg.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PG;Test Solutions S.r.l.;;;12345678901;12345678901;TEST002;TEST SRL;testsrl@pec.test.it;info@testsrl.it;024567890;Via Milano 10, Milano;Test PG
```

### Passi
1. Naviga a: `http://localhost:8000/anagrafiche/import/`
2. Upload `test_pg.csv`
3. Clicca "Importa Anagrafiche"

### Verifica Report
- [ ] Totale: 1, Importate: 1, Scartate: 0
- [ ] Nome visualizzato: "Test Solutions S.r.l."
- [ ] CF: 12345678901

### Verifica Database
- [ ] Tipo: Persona Giuridica
- [ ] Ragione Sociale: Test Solutions S.r.l.
- [ ] CF: 12345678901
- [ ] P.IVA: 12345678901

### Risultato Atteso
✅ Persona giuridica creata correttamente

---

## Test Case 4: Codice Fiscale Duplicato

### Obiettivo
Verificare che venga rifiutata l'importazione di un CF duplicato.

### Preparazione
1. Prima importa un'anagrafica (usa Test Case 2)
2. Crea `test_duplicato.csv` con lo STESSO CF:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Luigi;Bianchi;RSSMRA80A01H501U;;;;luigi@test.it;;;;Test duplicato
```

### Passi
1. Upload `test_duplicato.csv`
2. Importa

### Verifica Report
- [ ] Totale: 1
- [ ] Importate: 0
- [ ] Scartate: 1
- [ ] Tabella "Righe scartate" visibile
- [ ] Riga 2 con motivo: "Codice fiscale 'RSSMRA80A01H501U' già presente nel database"

### Verifica Database
1. Vai a lista anagrafiche
2. Cerca CF "RSSMRA80A01H501U"
3. Verifica che esista solo "Mario Rossi" (NON Luigi Bianchi)

### Risultato Atteso
✅ Import rifiutato con motivo chiaro nel report

---

## Test Case 5: Campi Obbligatori Mancanti

### Obiettivo
Verificare validazione campi obbligatori.

### Preparazione
Crea `test_campi_mancanti.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;;Rossi;RSSVRD85M45F205Y;;;;;;;;
PF;;Mario;;BNCLGI90A01H501Z;;;;;;;;
PG;;;;87654321098;87654321098;;;;;;;
```

### Verifica Report
- [ ] Totale: 3
- [ ] Importate: 0
- [ ] Scartate: 3
- [ ] Riga 2: motivo "Campo 'nome' obbligatorio per Persona Fisica"
- [ ] Riga 3: motivo "Campo 'cognome' obbligatorio per Persona Fisica"
- [ ] Riga 4: motivo "Campo 'ragione_sociale' obbligatorio per Persona Giuridica"

### Risultato Atteso
✅ Tutte le righe scartate con motivi specifici

---

## Test Case 6: Tipo Non Valido

### Obiettivo
Verificare validazione campo tipo.

### Preparazione
Crea `test_tipo_invalido.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
XX;;Mario;Rossi;RSSMRA90A01H501P;;;;;;;;
ABC;Azienda Srl;;;11111111111;11111111111;;;;;;;
```

### Verifica Report
- [ ] Scartate: 2
- [ ] Motivi contengono "Tipo 'XX' non valido" e "Tipo 'ABC' non valido"

### Risultato Atteso
✅ Righe scartate per tipo non valido

---

## Test Case 7: Importazione Multipla Mista

### Obiettivo
Verificare importazione batch con righe valide e non valide.

### Preparazione
Crea `test_misto.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Anna;Verdi;VRDNNA85M45F205X;;TEST010;;anna@pec.test.it;anna@test.it;;;Valida
PG;Beta Srl;;;98765432109;98765432109;TEST011;;beta@pec.test.it;beta@test.it;;;Valida
PF;;Luigi;Bianchi;RSSMRA80A01H501U;;;;luigi@test.it;;;;Duplicato
XX;;Carlo;Neri;NRECRL88A01H501W;;;;carlo@test.it;;;;Tipo invalido
PF;;Sara;;SRRSRA92A41H501T;;;;sara@test.it;;;;Cognome mancante
```

### Verifica Report
- [ ] Totale: 5
- [ ] Importate: 2 (Anna Verdi, Beta Srl)
- [ ] Scartate: 3
- [ ] Tabella importate con 2 righe
- [ ] Tabella scartate con 3 righe e motivi dettagliati

### Risultato Atteso
✅ Import parziale corretto, report dettagliato

---

## Test Case 8: Encoding e Caratteri Speciali

### Obiettivo
Verificare gestione encoding UTF-8 e caratteri accentati.

### Preparazione
Crea `test_encoding.csv` (UTF-8):
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;José;Martínez;MRTJSE75C15Z210H;;;;jose@test.it;;+34 123456789;Calle España 5, Barcelona;Cliente spagnolo
PF;;François;Dupont;DPNFNC80D12Z110A;;;;francois@test.it;;+33 123456789;Rue de la Liberté, Paris;Cliente francese
PG;Società à Responsabilità Limitata;;;55555555555;55555555555;;;srl@pec.test.it;;;;;Caratteri accentati
```

### Verifica
- [ ] Tutti i caratteri accentati visualizzati correttamente
- [ ] Nomi con accenti salvati correttamente
- [ ] Ragione sociale con caratteri speciali OK

### Risultato Atteso
✅ Encoding gestito correttamente

---

## Test Case 9: PEC e Email Duplicate

### Obiettivo
Verificare check univocità PEC.

### Preparazione
1. Importa prima:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Marco;Bianchi;BNCMRC85A01H501D;;;;marco@pec.test.it;marco@test.it;;;Prima
```

2. Poi tenta:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Luca;Verdi;VRDLCU90A01H501E;;;;marco@pec.test.it;luca@test.it;;;PEC duplicata
```

### Verifica Report
- [ ] Seconda importazione: scartata
- [ ] Motivo: "PEC 'marco@pec.test.it' già presente nel database"

### Risultato Atteso
✅ PEC duplicata rilevata e rifiutata

---

## Test Case 10: Normalizzazione Automatica

### Obiettivo
Verificare che i dati vengano normalizzati automaticamente.

### Preparazione
Crea `test_normalizzazione.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;  mario  ;  rossi  ;rssmra70a01h501x;;;;MARIO@PEC.IT;MARIO@EMAIL.IT; 333 1234567 ;  via roma 1  ;
```

### Verifica Database
Dopo l'importazione, controlla che:
- [ ] Nome: "Mario" (title case, trim)
- [ ] Cognome: "Rossi" (title case, trim)
- [ ] CF: "RSSMRA70A01H501X" (uppercase)
- [ ] PEC: "mario@pec.it" (lowercase)
- [ ] Email: "mario@email.it" (lowercase)
- [ ] Telefono: "333 1234567" (trim)
- [ ] Indirizzo: "via roma 1" (trim)

### Risultato Atteso
✅ Dati normalizzati automaticamente

---

## Test Case 11: Codice Cliente Auto-Generato

### Obiettivo
Verificare auto-generazione codice cliente.

### Preparazione
Crea `test_codice_auto.csv`:
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
PF;;Test;Auto;TSTTST85A01H501K;;;;test@test.it;;;;Codice vuoto
```

### Verifica
1. Importa file
2. Apri dettaglio anagrafica
3. Verifica che il campo "Codice" sia stato popolato automaticamente

### Risultato Atteso
✅ Codice cliente generato automaticamente se vuoto

---

## Test Case 12: UI e Responsiveness

### Obiettivo
Verificare interfaccia utente e design responsive.

### Verifica Desktop
- [ ] Layout chiaro e ordinato
- [ ] Sezioni ben separate (Istruzioni, Form, Report)
- [ ] Tabelle leggibili
- [ ] Bottoni styled correttamente
- [ ] Colori appropriati (success verde, warning giallo)
- [ ] Icone visibili (Bootstrap Icons)

### Verifica Mobile (ridimensiona browser)
- [ ] Layout si adatta
- [ ] Tabelle scrollabili orizzontalmente se necessario
- [ ] Bottoni cliccabili facilmente
- [ ] Testo leggibile

### Risultato Atteso
✅ UI professionale e responsive

---

## Test Case 13: Messaggi e Feedback

### Obiettivo
Verificare messaggi utente.

### Verifica Messaggi Success
Quando ci sono importazioni riuscite:
- [ ] Messaggio verde con icona ✓
- [ ] Testo: "Importate con successo X anagrafiche"

### Verifica Messaggi Warning
Quando ci sono scarti:
- [ ] Messaggio giallo/arancione con icona ⚠
- [ ] Testo: "Scartate X righe. Vedi dettagli sotto"

### Risultato Atteso
✅ Feedback chiaro e immediato

---

## Checklist Finale Test Manuale

### Funzionalità Core
- [ ] Download file esempio funziona
- [ ] Upload file CSV funziona
- [ ] Importazione PF valida
- [ ] Importazione PG valida
- [ ] Report visualizzato correttamente

### Validazioni
- [ ] Codice fiscale duplicato rilevato
- [ ] Campi obbligatori verificati
- [ ] Tipo invalido rilevato
- [ ] PEC duplicata rilevata
- [ ] P.IVA duplicata rilevata

### User Experience
- [ ] UI chiara e intuitiva
- [ ] Messaggi comprensibili
- [ ] Link dettaglio funzionano
- [ ] Responsive design OK
- [ ] Errori ben documentati nel report

### Data Quality
- [ ] Normalizzazione automatica funziona
- [ ] Encoding UTF-8 gestito
- [ ] Caratteri speciali OK
- [ ] Spazi e trim corretti

---

## Note Test

### Ambiente
- OS: Linux
- Browser: _____________
- Django: _____________
- Database: _____________

### Risultati
- Test eseguiti: ____/13
- Test passati: ____/13
- Test falliti: ____/13

### Problemi Rilevati
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

### Raccomandazioni
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

---

## Conclusione Test

**Data**: _______________  
**Tester**: _______________  
**Esito Generale**: ☐ PASS  ☐ FAIL  ☐ REVIEW NEEDED

**Note Finali**:
```
_____________________________________________________
_____________________________________________________
_____________________________________________________
```

---

**Versione**: 1.0  
**Tipo**: Test Manuale  
**Scope**: Importazione Anagrafiche CSV
