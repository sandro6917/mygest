# Quick Start - Importazione Anagrafiche

## 🚀 Come Utilizzare la Funzionalità

### Accesso alla Funzionalità
1. Accedi all'applicazione MyGest
2. Vai al menu **Anagrafiche**
3. Clicca su **Importazione**
4. URL: `http://tuoserver/anagrafiche/import/`

### Passi per l'Importazione

#### 1. Scarica il Template CSV
- Nella pagina di importazione, clicca sul pulsante **"Fac-simile CSV"**
- Si scaricherà il file `facsimile_anagrafiche.csv`
- In alternativa, usa il file statico: `/anagrafiche/esempio_importazione_anagrafiche.csv`

#### 2. Compila il File CSV
Apri il file con un editor di testo o foglio di calcolo e compila i dati:

**Formato Header (NON modificare):**
```csv
tipo;ragione_sociale;nome;cognome;codice_fiscale;partita_iva;codice;denominazione_abbreviata;pec;email;telefono;indirizzo;note
```

**Esempio Persona Fisica:**
```csv
PF;;Mario;Rossi;RSSMRA80A01H501U;;CLI0001;ROSSI MARIO;mario.rossi@pec.it;mario@email.it;3331234567;Via Roma 1, Milano;
```

**Esempio Persona Giuridica:**
```csv
PG;Acme S.r.l.;;;12345678901;12345678901;CLI0002;ACME SRL;acme@pec.it;info@acme.it;024567890;Via Milano 10, Milano;
```

#### 3. Regole Importanti

**Campi Obbligatori:**
- `tipo`: Deve essere "PF" (Persona Fisica) o "PG" (Persona Giuridica)
- `codice_fiscale`: Sempre obbligatorio
- Per **PF**: `nome` e `cognome`
- Per **PG**: `ragione_sociale`

**Validazioni:**
- Codice fiscale PF: 16 caratteri con checksum valido
- Codice fiscale PG: 11 cifre con checksum valido
- Partita IVA: 11 cifre con checksum valido
- PEC: formato email valido
- Separatore: `;` (punto e virgola)
- Encoding: UTF-8 o Latin-1

**Unicità:**
- Codice fiscale deve essere unico
- Partita IVA deve essere unica (se presente)
- PEC deve essere unica (se presente)

#### 4. Carica il File
- Nella pagina di importazione
- Clicca su "Scegli file"
- Seleziona il tuo CSV compilato
- Clicca su **"Importa Anagrafiche"**

#### 5. Verifica il Report
Dopo l'elaborazione vedrai un report dettagliato con:

**Statistiche:**
- Righe totali elaborate
- Anagrafiche importate con successo ✅
- Righe scartate ⚠️

**Tabella Importazioni Riuscite:**
- Elenco completo delle anagrafiche create
- Link per visualizzare ogni anagrafica

**Tabella Righe Scartate:**
- Numero riga nel CSV
- Dati parziali
- **Motivi dettagliati dello scarto**

#### 6. Correggi Eventuali Errori
Se ci sono righe scartate:
1. Leggi i motivi dello scarto nel report
2. Correggi il CSV originale
3. Crea un nuovo CSV con solo le righe corrette
4. Re-importa

## 📋 Checklist Pre-Importazione

Prima di importare, verifica:
- [ ] File salvato come CSV con separatore `;`
- [ ] Encoding UTF-8
- [ ] Header presente e corretto
- [ ] Campo `tipo` compilato (PF o PG)
- [ ] Campo `codice_fiscale` compilato
- [ ] Per PF: nome e cognome compilati
- [ ] Per PG: ragione_sociale compilata
- [ ] Nessun codice fiscale duplicato nel file
- [ ] Nessun codice fiscale già presente nel database
- [ ] Partite IVA valide (se presenti)

## ⚠️ Problemi Comuni e Soluzioni

### Problema: "Tutte le righe vengono scartate"
**Soluzione:**
- Verifica che l'header sia esattamente quello del template
- Controlla che il separatore sia `;` e non `,`
- Assicurati che tipo e codice_fiscale siano compilati

### Problema: "Codice fiscale non valido"
**Soluzione:**
- Usa codici fiscali reali e validi
- Verifica con un validatore online
- Rimuovi spazi bianchi prima/dopo il codice
- Per PG deve essere numerico (11 cifre)
- Per PF deve essere alfanumerico (16 caratteri)

### Problema: "Codice fiscale già presente"
**Soluzione:**
- Quel codice fiscale esiste già nel database
- Verifica nel sistema se l'anagrafica è già registrata
- Non puoi importare duplicati (è intenzionale)

### Problema: "Campo obbligatorio mancante"
**Soluzione:**
- Per PF: compila nome e cognome
- Per PG: compila ragione_sociale
- Non lasciare vuoti campi obbligatori

## 🎯 Tips & Best Practices

### Prima dell'Importazione:
✅ Fai un backup del database  
✅ Testa con 2-3 righe prima di importare 100+  
✅ Usa il file di esempio come template  
✅ Verifica i dati in Excel/LibreOffice prima di esportare  

### Durante la Compilazione:
✅ Mantieni l'header originale  
✅ Lascia vuoti i campi non applicabili (non scrivere "N/A")  
✅ Per PF lascia vuoto ragione_sociale  
✅ Per PG lascia vuoti nome e cognome  
✅ Codice cliente può essere vuoto (auto-generato)  

### Dopo l'Importazione:
✅ Leggi sempre il report completo  
✅ Clicca sui link per verificare i dati importati  
✅ Correggi subito le righe scartate  
✅ Conserva il CSV originale per riferimento  

## 📞 Supporto

Per maggiori informazioni consulta:
- **Guida Utente Completa**: `/anagrafiche/GUIDA_IMPORTAZIONE_ANAGRAFICHE.md`
- **Documentazione Tecnica**: `/anagrafiche/IMPORTAZIONE_README.md`
- **Report Implementazione**: `/anagrafiche/REPORT_IMPLEMENTAZIONE_IMPORTAZIONE.md`

---

**Versione**: 1.0  
**Data**: Dicembre 2025  
**Status**: ✅ Pronto all'uso
