# Funzionalità Scansione Documenti - MyGest

## 📋 Panoramica

Questa funzionalità consente di scansionare documenti direttamente dalla pagina di creazione documento in MyGest, utilizzando scanner di rete configurati sulla postazione di lavoro.

## 🖨️ Scanner Supportati

- **Brother ADS-2400N** - Scanner documentale di rete
- **HP Officejet 7510** - Multifunzione di rete
- **Kyocera ECOSYS M2540dn XPS** - Multifunzione di rete

## ⚙️ Parametri di Scansione

- **Risoluzione**: 300 DPI
- **Modalità**: Scala di grigi
- **Formato**: A4
- **Fronte/Retro**: Automatico (se supportato dallo scanner)
- **Output**: PDF/A

## 🚀 Installazione

### 1. Installa Dipendenze Python (Backend)

Sul server WSL, installa i pacchetti necessari per il servizio scanner:

```bash
cd /home/sandro/mygest
source venv/bin/activate
pip install -r scripts/scanner_requirements.txt
```

Le dipendenze includono:
- Flask (web server per API REST)
- Flask-CORS (gestione CORS)
- python-sane (interfaccia SANE per scanner)
- Pillow (manipolazione immagini)
- pikepdf (conversione PDF/A)
- img2pdf (conversione immagini in PDF)

### 2. Configura SANE (Linux)

SANE (Scanner Access Now Easy) è lo standard per l'accesso agli scanner su Linux.

```bash
# Installa SANE
sudo apt update
sudo apt install sane sane-utils libsane-dev

# Verifica scanner disponibili
scanimage -L
```

**Configurazione scanner di rete** (se non rilevati automaticamente):

Edita `/etc/sane.d/net.conf` per aggiungere gli IP degli scanner:

```bash
sudo nano /etc/sane.d/net.conf
```

Aggiungi gli indirizzi IP:
```
192.168.1.10  # Brother ADS-2400N
192.168.1.11  # HP Officejet 7510
192.168.1.12  # Kyocera ECOSYS M2540dn
```

Riavvia il servizio:
```bash
sudo systemctl restart saned
```

### 3. Configura Firewall (se necessario)

Assicurati che le porte degli scanner siano accessibili:

```bash
# Porte comuni per scanner di rete
sudo ufw allow from 192.168.1.0/24 to any port 8289  # SANE network scanning
sudo ufw allow from 192.168.1.0/24 to any port 9100  # HP JetDirect
```

## 🎮 Utilizzo

### Avvio Servizio Scanner

#### Metodo 1: Script Batch (Windows)

Dalla cartella `windows_manager`:

```batch
Quick_Start_Scanner.bat
```

#### Metodo 2: WSL Server Manager

1. Apri `Start_Manager.bat` nella cartella `windows_manager`
2. Seleziona opzione `D` (Avvia Scanner)

#### Metodo 3: Manuale (WSL/Linux)

```bash
cd /home/sandro/mygest
source venv/bin/activate
python scripts/scanner_service.py
```

Il servizio sarà disponibile su: `http://localhost:8765`

### Utilizzo dall'Interfaccia Web

1. **Vai alla pagina di creazione documento**:
   - Menu → Documenti → Nuovo Documento

2. **Verifica disponibilità servizio**:
   - Se il servizio scanner è attivo, vedrai la sezione "Scansione Documento"
   - Se non è disponibile, vedrai un messaggio con istruzioni per avviarlo

3. **Seleziona lo scanner**:
   - Dal menu dropdown, seleziona lo scanner da utilizzare
   - Gli scanner con supporto duplex saranno indicati

4. **Avvia scansione**:
   - Inserisci i documenti nel feeder dello scanner
   - Clicca "Avvia Scansione"
   - Attendi il completamento della scansione

5. **Gestisci le pagine**:
   - Visualizza le anteprime delle pagine scansionate
   - Ruota le pagine se necessario (icona rotazione)
   - Elimina pagine non desiderate (icona cestino)

6. **Crea PDF**:
   - Clicca "Unisci e Allega come PDF"
   - Il sistema creerà un PDF/A con tutte le pagine
   - Il file verrà automaticamente allegato al documento

7. **Completa il documento**:
   - Compila gli altri campi del form
   - Salva il documento

### Scansioni Multiple

Puoi fare più scansioni separate e poi unirle in un unico PDF:

1. Scansiona il primo lotto di documenti
2. Clicca "Avvia Scansione" di nuovo per il secondo lotto
3. Tutte le pagine verranno mostrate insieme
4. Clicca "Unisci e Allega come PDF" per creare un unico documento

## 📊 API Endpoints

Il servizio scanner espone le seguenti API REST:

### GET /health
Health check del servizio
```json
{
  "status": "ok",
  "sane_available": true,
  "version": "1.0.0"
}
```

### GET /scanners
Lista degli scanner disponibili
```json
{
  "scanners": [
    {
      "id": "brother_ads2400n",
      "name": "Brother ADS-2400N",
      "vendor": "Brother",
      "model": "ADS-2400N",
      "type": "network",
      "capabilities": {
        "duplex": true,
        "adf": true,
        "max_dpi": 600
      }
    }
  ],
  "count": 3
}
```

### POST /scan
Avvia una nuova scansione
```json
// Request
{
  "scanner_id": "brother_ads2400n",
  "pages": 0,  // 0 = tutte le pagine dal feeder
  "dpi": 300,
  "mode": "gray",
  "duplex": true
}

// Response
{
  "scan_id": "uuid",
  "status": "completed",
  "pages_scanned": 5,
  "message": "Scansione completata con successo"
}
```

### GET /scan/{scan_id}/status
Stato di una scansione
```json
{
  "scan_id": "uuid",
  "status": "completed",
  "pages_scanned": 5,
  "total_pages": 0
}
```

### GET /scan/{scan_id}/preview/{page}
Preview di una pagina scansionata (ritorna immagine PNG)

### POST /scan/merge
Unisce più scansioni in PDF/A
```json
// Request
{
  "scan_ids": ["uuid1", "uuid2"],
  "filename": "documento.pdf"
}

// Response: File PDF/A
```

### DELETE /scan/{scan_id}
Elimina una scansione e i file temporanei

## 🔧 Troubleshooting

### Servizio non raggiungibile

**Problema**: Messaggio "Servizio Scanner Non Disponibile"

**Soluzioni**:
1. Verifica che il servizio sia avviato:
   ```bash
   wsl -d Ubuntu bash -c "pgrep -f scanner_service.py"
   ```

2. Controlla i log:
   ```bash
   tail -f /home/sandro/mygest/logs/scanner_service.log
   ```

3. Riavvia il servizio:
   ```batch
   Quick_Restart_Scanner.bat
   ```

### Scanner non trovati

**Problema**: Lista scanner vuota o scanner non rilevati

**Soluzioni**:
1. Verifica connessione di rete:
   ```bash
   ping 192.168.1.10  # IP dello scanner
   ```

2. Verifica configurazione SANE:
   ```bash
   scanimage -L
   ```

3. Controlla `/etc/sane.d/net.conf` e `/etc/sane.d/dll.conf`

4. Riavvia SANE:
   ```bash
   sudo systemctl restart saned
   ```

### Errori durante la scansione

**Problema**: Scansione fallisce o si blocca

**Soluzioni**:
1. Verifica che lo scanner non sia in uso da altri programmi
2. Controlla lo stato dello scanner (display/LED)
3. Riavvia lo scanner fisicamente
4. Controlla i log del servizio per errori specifici

### Conversione PDF/A fallita

**Problema**: PDF creato ma non in formato PDF/A

**Nota**: Il servizio usa `pikepdf` per la conversione. Se fallisce, crea comunque un PDF standard valido.

**Soluzioni**:
1. Verifica installazione pikepdf:
   ```bash
   python -c "import pikepdf; print(pikepdf.__version__)"
   ```

2. Reinstalla pikepdf:
   ```bash
   pip install --upgrade pikepdf
   ```

## 🔒 Sicurezza

- Il servizio scanner gira solo su `localhost:8765` e non è accessibile dall'esterno
- I file temporanei vengono automaticamente eliminati dopo 24 ore
- Le scansioni sono associate alla sessione dell'utente
- CORS configurato per accettare richieste solo da `localhost:5173` (frontend)

## 📝 Note Tecniche

### Modalità Mock

Se SANE non è disponibile o non ci sono scanner configurati, il servizio opera in **modalità mock**:
- Restituisce 3 scanner fittizi
- Genera immagini di test per le scansioni
- Utile per sviluppo e testing

### Storage Temporaneo

Le scansioni vengono salvate in:
```
/tmp/mygest_scanner/{scan_id}/page_001.png
/tmp/mygest_scanner/{scan_id}/page_002.png
...
```

I file vengono eliminati quando:
- L'utente elimina manualmente la scansione
- Dopo il merge in PDF (cleanup automatico)
- Dopo 24 ore (cleanup schedulato)

### Performance

- Scansione A4 @ 300 DPI: ~2-5 secondi per pagina
- Merge PDF: ~1 secondo per 10 pagine
- Preview immagini: cache lato client

## 🆕 Funzionalità Future

- [ ] Rotazione immagini lato client
- [ ] OCR automatico (Tesseract)
- [ ] Riconoscimento automatico tipo documento
- [ ] Salvataggio preferenze scanner per utente
- [ ] Riordinamento pagine drag & drop
- [ ] Supporto scansione a colori
- [ ] Compressione immagini configurabile
- [ ] Notifiche push per scansioni lunghe

## 📞 Supporto

Per problemi o domande sulla funzionalità di scansione:
1. Controlla i log: `logs/scanner_service.log`
2. Verifica configurazione SANE: `scanimage -L`
3. Testa API direttamente: `curl http://localhost:8765/health`

---

**Versione**: 1.0.0  
**Data**: Febbraio 2026  
**Maintainer**: Sandro Chimenti
