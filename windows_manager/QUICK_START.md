# GUIDA RAPIDA - WSL Server Manager

## 🚀 Setup Veloce (3 minuti)

### Passo 1: Accedi ai File da Windows

Apri Esplora Risorse e vai a:
```
\\wsl$\Ubuntu\home\sandro\mygest\windows_manager
```

### Passo 2: Scegli il Tuo Stile

**Opzione A - Interfaccia Grafica (Consigliato):**
Doppio click su:
```
Start_GUI.bat
```
✅ Interfaccia grafica moderna con pulsanti!

**Opzione B - Menu Testuale:**
Doppio click su:
```
Start_Manager.bat
```
✅ Menu interattivo in console!

**Opzione C - Avvio Diretto:**
Doppio click su:
```
Quick_Start_All.bat
```
✅ Avvia tutto immediatamente!

---

## 🎯 Uso Quotidiano

### Per Sviluppo Normale

1. **Avvia tutto:** Doppio click su `Quick_Start_All.bat`
2. **Lavora sul progetto** (Django su porta 8000, Frontend su porta 5173)
3. **Chiudi tutto:** Doppio click su `Quick_Stop_All.bat`

### Per Controllo Completo

Usa `Start_Manager.bat` per accedere al menu con tutte le opzioni.

---

## 🎨 Creare l'Eseguibile (Opzionale)

Se vuoi un file `.exe` standalone:

1. **Apri PowerShell come Admin**
2. **Naviga alla cartella:**
   ```powershell
   cd \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
   ```
3. **Installa PS2EXE (solo prima volta):**
   ```powershell
   .\Build_Executable.ps1 -Install
   ```
4. **Crea EXE:**
   ```powershell
   .\Build_Executable.ps1
   ```

Ora puoi copiare `WSL_Server_Manager.exe` ovunque su Windows!

---

## 🔍 Verifica Rapida

**Test che tutto funzioni:**

```powershell
# Test 1: WSL funziona?
wsl echo "OK"

# Test 2: Progetto esiste?
wsl ls /home/sandro/mygest

# Test 3: Python funziona?
wsl python --version
```

---

## ❓ Problemi Comuni

### "Script non autorizzato"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Porta già in uso"
Usa l'opzione "Riavvia" nel menu, che ferma prima i vecchi processi.

### "Server non si avvia"
Controlla nei terminali aperti per vedere eventuali errori.

---

## 📌 URL dei Server

Dopo l'avvio:
- **Django Backend:** http://localhost:8000
- **Frontend Vite:** http://localhost:5173

---

## 🎮 Menu Comandi

```
1 - Avvia tutto          7 - Riavvia tutto
2 - Avvia Django         8 - Riavvia Django  
3 - Avvia Frontend       9 - Riavvia Frontend
4 - Ferma tutto          S - Stato servizi
5 - Ferma Django         Q - Esci
6 - Ferma Frontend
```

---

## 💡 Suggerimenti

- **Avvio automatico:** Metti un collegamento a `Quick_Start_All.bat` nella cartella Esecuzione automatica di Windows
- **Desktop:** Crea un collegamento sul Desktop per accesso rapido
- **Alias:** Rinomina i file `.bat` come preferisci

---

Per la guida completa, vedi `README.md`.
