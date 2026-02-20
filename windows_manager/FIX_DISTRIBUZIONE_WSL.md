# ⚠️ IMPORTANTE - Configurazione Distribuzione WSL

## 🔧 Problema Risolto

Gli script ora usano il nome corretto della distribuzione WSL: **Ubuntu-22.04**

## ✅ Cosa è stato corretto

Tutti i file sono stati aggiornati per usare "Ubuntu-22.04" invece di "Ubuntu":

- ✅ WSL_Server_Manager.ps1
- ✅ WSL_Server_Manager_GUI.ps1
- ✅ Test_Script.ps1
- ✅ Check_Configuration.bat
- ✅ Tutta la documentazione

## 🎯 Gli script ora funzionano!

Puoi provare nuovamente:

### Da Windows PowerShell:

```powershell
cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager

# Test rapido
.\Test_Script.ps1

# GUI
.\Start_GUI.bat

# Menu console
.\Start_Manager.bat
```

## 🔍 Come Verificare il Nome della Tua Distribuzione

Se hai dubbi sul nome della distribuzione WSL:

```powershell
wsl -l -v
```

Output esempio:
```
  NAME              STATE           VERSION
* Ubuntu-22.04      Running         2
  Ubuntu-20.04      Stopped         2
```

Il nome da usare è quello nella colonna NAME (es: Ubuntu-22.04, Ubuntu-20.04, etc.)

## ⚙️ Se Hai un Nome Diverso

Se la tua distribuzione ha un nome diverso (es: "Ubuntu-20.04", "Debian", etc.):

1. **Apri questi file con un editor di testo:**
   - `WSL_Server_Manager.ps1`
   - `WSL_Server_Manager_GUI.ps1`
   - `Test_Script.ps1`

2. **Trova la riga:**
   ```powershell
   $WSL_DISTRO = "Ubuntu-22.04"
   ```

3. **Cambia con il tuo nome:**
   ```powershell
   $WSL_DISTRO = "IL-TUO-NOME"
   ```

4. **Salva e riprova!**

## 📋 Percorsi Aggiornati

### Da Windows Esplora Risorse:
```
\\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
```

### Da Windows PowerShell:
```powershell
cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
```

### Da WSL/Linux (non cambia):
```bash
cd /home/sandro/mygest/windows_manager
```

## ✨ Ora Funziona!

Gli script ora dovrebbero funzionare perfettamente senza errori "WSL_E_DISTRO_NOT_FOUND".

Prova subito! 🚀
