# 📦 Come Trasferire e Usare su Windows

## 🎯 3 Modi per Usare il Manager su Windows

---

## ✅ METODO 1: Accesso Diretto via Rete WSL (PIÙ SEMPLICE)

### Vantaggi
- ✅ Nessuna copia necessaria
- ✅ Sempre aggiornato automaticamente
- ✅ Zero configurazione

### Passi
1. **Apri Esplora Risorse di Windows**
2. **Nella barra degli indirizzi digita:**
   ```
   \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
   ```
3. **Premi INVIO**
4. **Vedi tutti i file!** Doppio click per usarli

### Per Accesso Rapido
- Clicca con il tasto destro nella cartella
- Seleziona "Aggiungi ai Preferiti" o "Pin to Quick access"

---

## ✅ METODO 2: Copia sul Desktop di Windows

### Vantaggi
- ✅ File nativi su Windows
- ✅ Più veloce all'avvio
- ✅ Funziona offline (senza WSL montato)

### Passi (Da WSL/Linux)

Apri un terminale WSL e esegui:

```bash
# Copia tutta la cartella sul Desktop di Windows
# Sostituisci 'TUO_USERNAME' con il tuo username Windows
cp -r /home/sandro/mygest/windows_manager /mnt/c/Users/TUO_USERNAME/Desktop/

# OPPURE copia in Documenti
cp -r /home/sandro/mygest/windows_manager /mnt/c/Users/TUO_USERNAME/Documents/
```

### Passi (Da Windows PowerShell)

Apri PowerShell e esegui:

```powershell
# Copia sul Desktop
Copy-Item -Path "\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager" -Destination "$env:USERPROFILE\Desktop\" -Recurse

# OPPURE copia in Documenti
Copy-Item -Path "\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager" -Destination "$env:USERPROFILE\Documents\" -Recurse
```

### Dopo la Copia
1. Vai alla cartella copiata sul Desktop/Documenti
2. Doppio click su `Start_GUI.bat` per la versione grafica
3. OPPURE `Start_Manager.bat` per il menu testuale

---

## ✅ METODO 3: Crea Eseguibile Standalone

### Vantaggi
- ✅ Un singolo file .exe
- ✅ Portabile
- ✅ Professionale

### Passi

1. **Apri PowerShell come Amministratore**
   - Premi `Win + X`
   - Seleziona "Windows PowerShell (Admin)"

2. **Vai alla cartella del manager:**
   ```powershell
   cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
   ```

3. **Installa PS2EXE (solo la prima volta):**
   ```powershell
   .\Build_Executable.ps1 -Install
   ```
   - Quando chiede, premi `Y` per confermare

4. **Crea l'eseguibile:**
   ```powershell
   .\Build_Executable.ps1
   ```

5. **Troverai `WSL_Server_Manager.exe` nella stessa cartella!**

### Dopo la Creazione
- Copia `WSL_Server_Manager.exe` dove vuoi (Desktop, C:\Tools\, ecc.)
- Doppio click per avviare
- Puoi creare un collegamento sul Desktop

---

## 🎨 Creare Collegamenti sul Desktop

### Collegamento al Manager Grafico (GUI)

1. **Clicca con il tasto destro sul Desktop**
2. **Nuovo → Collegamento**
3. **Incolla questo percorso:**
   ```
   powershell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager\WSL_Server_Manager_GUI.ps1"
   ```
4. **Nome:** "MyGest Server Manager"
5. **Fine**

### Collegamento Avvio Rapido

1. **Clicca con il tasto destro sul Desktop**
2. **Nuovo → Collegamento**
3. **Incolla questo percorso:**
   ```
   powershell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager\WSL_Server_Manager.ps1" -Action start
   ```
4. **Nome:** "Avvia MyGest"
5. **Fine**

---

## 🚀 Avvio Automatico all'Accensione Windows

Se vuoi che i server partano automaticamente quando accendi Windows:

1. **Premi `Win + R`**
2. **Digita:** `shell:startup`
3. **Premi INVIO** (si apre la cartella Esecuzione automatica)
4. **Crea un collegamento a `Quick_Start_All.bat` in quella cartella**

Metodo alternativo con copia diretta:
```powershell
# Copia lo script di avvio nella cartella startup
Copy-Item "\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager\Quick_Start_All.bat" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\"
```

---

## 📍 Percorsi Utili di Windows

### Trovare il Tuo Username
```powershell
echo $env:USERNAME
```

### Trovare la Tua Home Directory
```powershell
echo $env:USERPROFILE
```

### Cartelle Comuni
- Desktop: `$env:USERPROFILE\Desktop`
- Documenti: `$env:USERPROFILE\Documents`
- Download: `$env:USERPROFILE\Downloads`

---

## 🔍 Verifica Prima di Usare

Prima di trasferire o usare, verifica che tutto funzioni:

```powershell
# Test 1: WSL funziona?
wsl echo "OK"

# Test 2: Progetto raggiungibile?
wsl ls /home/sandro/mygest

# Test 3: Python disponibile?
wsl python3 --version

# Test 4: Node.js disponibile?
wsl node --version
```

Se tutti i comandi danno risultati positivi, sei pronto!

---

## 📦 Condividere con Altri Sviluppatori

### Metodo 1: Condividi la Cartella
1. Zippa la cartella `windows_manager`
2. Condividi lo zip
3. Gli altri devono solo estrarre e usare

### Metodo 2: Condividi l'Eseguibile
1. Crea l'eseguibile con `Build_Executable.ps1`
2. Condividi solo `WSL_Server_Manager.exe`
3. **NOTA:** Devono avere la stessa struttura WSL e percorsi

---

## 🎯 Uso Consigliato per Scenari Diversi

### Per Uso Quotidiano Personale
➡️ **Metodo 1** (Accesso Diretto) + Collegamento Desktop

### Per Dimostrazione/Presentazioni
➡️ **Metodo 3** (Eseguibile) sul Desktop

### Per Distribuzione Team
➡️ **Metodo 2** (Copia) + Documentazione

---

## ⚡ Troubleshooting Trasferimento

### "Accesso Negato" su \\wsl$\
**Soluzione:**
1. Assicurati che WSL sia in esecuzione: `wsl echo test`
2. Riavvia WSL: `wsl --shutdown` poi `wsl`

### "File non trovato" dopo copia
**Soluzione:**
Verifica che tutti i file .ps1 siano stati copiati insieme ai .bat

### "Script non autorizzato"
**Soluzione:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📱 Accesso Veloce - Riepilogo

| File | Cosa Fa | Quando Usare |
|------|---------|--------------|
| `Start_GUI.bat` | Apre interfaccia grafica | Uso quotidiano (migliore) |
| `Start_Manager.bat` | Menu testuale interattivo | Alternative alla GUI |
| `Quick_Start_All.bat` | Avvia tutto subito | Avvio rapido |
| `Quick_Stop_All.bat` | Ferma tutto subito | Spegnimento rapido |
| `Quick_Restart_All.bat` | Riavvia tutto | Dopo modifiche |
| `Check_Configuration.bat` | Verifica configurazione | Troubleshooting |

---

## ✨ Tips Finali

### Per Massima Velocità
1. Usa Metodo 2 (copia su Windows)
2. Crea collegamenti sul Desktop
3. Pin alla Taskbar per accesso istantaneo

### Per Massima Affidabilità
1. Usa Metodo 1 (accesso diretto)
2. Sempre sincronizzato con il codice
3. Nessuna gestione di copie

### Per Massima Portabilità
1. Usa Metodo 3 (eseguibile)
2. Un solo file da portare
3. Funziona anche da USB

---

**Hai finito! Buon lavoro! 🚀**

Per ulteriori dettagli, consulta README.md e PACKAGE_INFO.md
