# Script di Gestione File Post-Upload

Questa directory contiene script Python per gestire l'eliminazione dei file locali dopo averli caricati nell'archivio MyGest.

## 📋 Script Disponibili

### 1. `remove_uploaded_file.py` - Eliminazione Semplice

Script da riga di comando per eliminare rapidamente uno o più file.

#### Utilizzo Base

```bash
# Elimina un singolo file (con conferma)
python scripts/remove_uploaded_file.py /percorso/al/documento.pdf

# Elimina un file dalla directory corrente
python scripts/remove_uploaded_file.py documento.pdf

# Elimina più file contemporaneamente
python scripts/remove_uploaded_file.py file1.pdf file2.docx file3.xlsx

# Salta la conferma (attenzione!)
python scripts/remove_uploaded_file.py documento.pdf --force

# Modalità verbosa
python scripts/remove_uploaded_file.py documento.pdf --verbose
```

#### Esempi

```bash
# Elimina un file dopo l'upload
cd ~/Downloads
python /path/to/mygest/scripts/remove_uploaded_file.py contratto_2024.pdf

# Elimina tutti i PDF in una cartella
python scripts/remove_uploaded_file.py ~/Downloads/*.pdf

# Modalità automatica (per script)
python scripts/remove_uploaded_file.py documento.pdf --force
```

### 2. `interactive_file_cleanup.py` - Interfaccia Interattiva

Script interattivo con menu per gestire l'eliminazione di file in modo più user-friendly.

#### Utilizzo

```bash
python scripts/interactive_file_cleanup.py
```

#### Funzionalità

1. **Elimina file specifico**: Inserisci il percorso completo di un file
2. **Cerca nella directory corrente**: Mostra e seleziona file dalla directory di lavoro
3. **Cerca in directory specifica**: Naviga e cerca in qualsiasi cartella
4. **Visualizza log**: Vedi lo storico delle eliminazioni
5. **Esci**: Chiudi il programma

#### Caratteristiche

- 🔍 **Ricerca con pattern**: Filtra file per tipo (*.pdf, *.docx, ecc.)
- ✅ **Selezione multipla**: Elimina più file contemporaneamente
- 📊 **Anteprima informazioni**: Dimensione, data modifica, percorso completo
- 📝 **Log automatico**: Tiene traccia di tutte le eliminazioni in `deleted_files.log`
- ⚠️ **Conferma sicura**: Doppia conferma prima dell'eliminazione
- 🎨 **Interfaccia colorata**: Output chiaro e intuitivo

## 🚀 Workflow Consigliato

### Scenario 1: Upload Singolo Documento

1. Apri MyGest nel browser
2. Vai su "Documenti" → "Nuovo Documento"
3. Compila i campi e seleziona il file dal tuo computer
4. **Importante**: Seleziona "Sposta" come operazione file
5. Salva il documento
6. Apri un terminale e vai nella cartella del file originale:
   ```bash
   cd ~/Downloads
   python /path/to/mygest/scripts/remove_uploaded_file.py nome_file.pdf
   ```
7. Conferma l'eliminazione quando richiesto

### Scenario 2: Upload Multipli Documenti

1. Carica tutti i documenti nell'archivio MyGest
2. Apri un terminale
3. Esegui lo script interattivo:
   ```bash
   python /path/to/mygest/scripts/interactive_file_cleanup.py
   ```
4. Seleziona opzione 2 o 3 dal menu
5. Inserisci pattern di ricerca (es: `*.pdf` per tutti i PDF)
6. Seleziona i file da eliminare (es: `1,3,5` o `1-10` o `all`)
7. Conferma l'eliminazione

### Scenario 3: Automazione con Script

Crea uno script bash per automatizzare il processo:

```bash
#!/bin/bash
# cleanup_after_upload.sh

# Directory dove si trovano i file uploadati
UPLOAD_DIR="$HOME/Downloads"

# File da eliminare (lista)
FILES=(
    "contratto_2024.pdf"
    "fattura_001.pdf"
    "verbale_riunione.docx"
)

# Cambia directory
cd "$UPLOAD_DIR"

# Elimina ogni file
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Eliminazione: $file"
        python /path/to/mygest/scripts/remove_uploaded_file.py "$file" --force
    else
        echo "File non trovato: $file"
    fi
done

echo "Pulizia completata!"
```

## 📝 Log delle Eliminazioni

Lo script interattivo mantiene un log di tutte le eliminazioni in:
```
scripts/deleted_files.log
```

Formato del log (JSON):
```json
{
  "deletions": [
    {
      "path": "/home/user/Downloads/documento.pdf",
      "name": "documento.pdf",
      "size": 1024000,
      "timestamp": "2024-11-20T10:30:00",
      "success": true
    }
  ]
}
```

## ⚠️ Avvertenze di Sicurezza

1. **L'eliminazione è permanente**: I file vengono rimossi definitivamente dal disco
2. **Non c'è recupero**: Non è possibile ripristinare i file eliminati (usa il cestino del sistema se disponibile)
3. **Verifica prima di eliminare**: Assicurati che il file sia stato correttamente uploadato nell'archivio
4. **Backup**: Mantieni sempre un backup dei documenti importanti

## 🔧 Requisiti

- Python 3.6 o superiore
- Permessi di scrittura sulla directory contenente i file
- Sistema operativo: Linux, macOS, Windows

## 💡 Suggerimenti

### Integrazione con File Manager

#### Linux (Nautilus)
Crea uno script Nautilus per eliminare file dal menu contestuale:

1. Crea `~/.local/share/nautilus/scripts/Elimina File Uploadato`
2. Contenuto:
   ```bash
   #!/bin/bash
   python /path/to/mygest/scripts/remove_uploaded_file.py "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
   ```
3. Rendi eseguibile: `chmod +x ~/.local/share/nautilus/scripts/Elimina\ File\ Uploadato`

#### macOS (Finder)
Crea un'Azione Rapida con Automator:

1. Apri Automator → Nuova Azione Rapida
2. Aggiungi "Esegui Script Shell"
3. Input: File o cartelle
4. Script:
   ```bash
   python /path/to/mygest/scripts/remove_uploaded_file.py "$@"
   ```

### Alias per Terminale

Aggiungi al tuo `~/.bashrc` o `~/.zshrc`:

```bash
# Alias MyGest
alias cleanup-upload='python /path/to/mygest/scripts/interactive_file_cleanup.py'
alias rm-uploaded='python /path/to/mygest/scripts/remove_uploaded_file.py'
```

Poi usa semplicemente:
```bash
cleanup-upload
# oppure
rm-uploaded documento.pdf
```

## 🐛 Risoluzione Problemi

### Errore: Permessi Insufficienti

Se ottieni errori di permessi:
```bash
# Linux/macOS
sudo python scripts/remove_uploaded_file.py file.pdf

# Oppure cambia proprietà del file
sudo chown $USER:$USER file.pdf
```

### Script Non Trovato

Assicurati di eseguire lo script dalla directory corretta o usa il percorso assoluto:
```bash
python /percorso/completo/mygest/scripts/remove_uploaded_file.py file.pdf
```

### Python Non Trovato

Verifica che Python sia installato:
```bash
python --version
# o
python3 --version
```

Se necessario, usa `python3` invece di `python`.

## 📚 Sviluppi Futuri

Possibili miglioramenti:

- [ ] Integrazione diretta con MyGest (API per confermare upload)
- [ ] GUI desktop con PyQt o Tkinter
- [ ] Monitoraggio automatico cartella Downloads
- [ ] Supporto per cestino di sistema invece di eliminazione permanente
- [ ] Sincronizzazione con database MyGest per verificare upload riusciti
- [ ] App mobile per gestire file da smartphone

## 📄 Licenza

Questi script fanno parte del progetto MyGest e seguono la stessa licenza.

## 🤝 Contributi

Per bug report, richieste di funzionalità o contributi, apri una issue sul repository del progetto.
