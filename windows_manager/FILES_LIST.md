# 🎯 WSL Server Manager per MyGest

## ✅ INSTALLAZIONE COMPLETATA CON SUCCESSO!

È stato creato un sistema completo per gestire i server Django e Frontend da Windows 11.

---

## 📦 16 File Creati (Total: ~67 KB)

### 🚀 **Launcher Pronti all'Uso**
- `Start_GUI.bat` (182 bytes) - ⭐ **INIZIA DA QUI** - Interfaccia grafica
- `Start_Manager.bat` (594 bytes) - Menu interattivo console
- `Quick_Start_All.bat` (185 bytes) - Avvio rapido
- `Quick_Stop_All.bat` (187 bytes) - Arresto rapido
- `Quick_Restart_All.bat` (193 bytes) - Riavvio rapido
- `Check_Configuration.bat` (1.9 KB) - Verifica setup

### 💻 **Script PowerShell Core**
- `WSL_Server_Manager_GUI.ps1` (11 KB) - Interfaccia grafica Windows Forms
- `WSL_Server_Manager.ps1` (9.5 KB) - Menu interattivo completo
- `Build_Executable.ps1` (4.8 KB) - Creatore eseguibile .exe

### 📚 **Documentazione Completa**
- `COMPLETATO.md` (9.2 KB) - Guida post-installazione
- `README.md` (6.6 KB) - Documentazione principale
- `INDEX.md` (6.0 KB) - Indice e panoramica
- `PACKAGE_INFO.md` (8.1 KB) - Informazioni dettagliate
- `TRASFERIMENTO_WINDOWS.md` (6.5 KB) - Guide per Windows
- `QUICK_START.md` (2.6 KB) - Quick start in 3 minuti
- `FILES_LIST.md` (questo file)

---

## 🚀 COME INIZIARE (30 Secondi)

### Da Windows:

1. **Apri Esplora Risorse**
2. **Digita nella barra degli indirizzi:**
   ```
   \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
   ```
3. **Doppio click su: `Start_GUI.bat`**

✅ **Fatto!** L'interfaccia grafica si aprirà.

---

## 🎨 Cosa Offre l'Interfaccia Grafica

```
┌─────────────────────────────────────────┐
│  🖥️ Gestione Server WSL                │
├─────────────────────────────────────────┤
│                                          │
│  Django Server          [●] ATTIVO      │
│  [▶ Avvia] [⏹ Ferma] [🔄 Riavvia]     │
│                                          │
│  Frontend Server        [○] FERMO       │
│  [▶ Avvia] [⏹ Ferma] [🔄 Riavvia]     │
│                                          │
│  [▶ Avvia Tutto] [⏹ Ferma Tutto]       │
└─────────────────────────────────────────┘
```

**Caratteristiche:**
- ✅ Pulsanti colorati e intuitivi
- ✅ Indicatori di stato in tempo reale
- ✅ Aggiornamento automatico ogni 5 secondi
- ✅ Controllo separato per ogni server
- ✅ Gestione di entrambi i server insieme

---

## 📖 Quale File Usare

| Scenario | File | Descrizione |
|----------|------|-------------|
| 🎨 Uso normale | `Start_GUI.bat` | Interfaccia grafica moderna |
| 📟 Preferisco console | `Start_Manager.bat` | Menu testuale interattivo |
| ⚡ Avvio veloce | `Quick_Start_All.bat` | Avvia tutto con un click |
| 🛑 Spegni veloce | `Quick_Stop_All.bat` | Ferma tutto immediatamente |
| 🔄 Riavvio veloce | `Quick_Restart_All.bat` | Riavvia dopo modifiche |
| 🔍 Diagnostica | `Check_Configuration.bat` | Verifica configurazione |
| 📦 Crea .exe | `Build_Executable.ps1` | Genera eseguibile standalone |

---

## 🎯 URL dei Server

Dopo l'avvio, i server saranno disponibili su:

- **Django Backend:** http://localhost:8000
- **Frontend Vite:** http://localhost:5173

---

## ⚙️ Configurazione (Se Necessario)

Se usi porte diverse o altri percorsi, modifica questi valori negli script:

```powershell
$WSL_DISTRO = "Ubuntu"                    # Nome distribuzione WSL
$PROJECT_PATH = "/home/sandro/mygest"     # Percorso progetto
$DJANGO_PORT = 8000                       # Porta Django
$FRONTEND_PORT = 5173                     # Porta Frontend
```

File da modificare:
- `WSL_Server_Manager.ps1`
- `WSL_Server_Manager_GUI.ps1`

---

## 💡 Tips Utili

### Collegamento sul Desktop
1. Vai a: `\\wsl$\Ubuntu\home\sandro\mygest\windows_manager`
2. Click destro su `Start_GUI.bat`
3. "Invia a" → "Desktop (crea collegamento)"

### Avvio Automatico all'Accensione
1. Premi `Win + R`
2. Digita: `shell:startup`
3. Copia il collegamento a `Quick_Start_All.bat` nella cartella

### Crea Eseguibile .exe
```powershell
cd \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
.\Build_Executable.ps1 -Install  # Solo prima volta
.\Build_Executable.ps1            # Crea l'exe
```

---

## 🔧 Troubleshooting Rapido

### Errore: "Script non autorizzato"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Verifica se tutto funziona
```bat
Check_Configuration.bat
```

### Server non si avvia
1. Controlla i terminali aperti per errori
2. Verifica che le porte non siano già occupate
3. Usa "Riavvia" invece di "Avvia"

---

## 📚 Documentazione Completa

Per maggiori dettagli, consulta:

1. **COMPLETATO.md** - Guida completa post-installazione
2. **QUICK_START.md** - Inizia in 3 minuti
3. **README.md** - Documentazione dettagliata
4. **TRASFERIMENTO_WINDOWS.md** - Come usare su Windows
5. **PACKAGE_INFO.md** - Informazioni complete
6. **INDEX.md** - Indice generale

---

## ✨ Caratteristiche Principali

✅ **Interfaccia Grafica Moderna** - Windows Forms nativa  
✅ **Menu Interattivo Console** - Completo e colorato  
✅ **Script Rapidi** - Avvio/Stop/Riavvio con un click  
✅ **Monitoraggio Real-time** - Stato aggiornato automaticamente  
✅ **Terminali Separati** - Log dedicati per ogni server  
✅ **Gestione Robusta** - Kill graceful e forzato  
✅ **Verifica Automatica** - Diagnostica configurazione  
✅ **Creazione .exe** - Eseguibile standalone  
✅ **Documentazione Completa** - 40+ KB di guide  
✅ **Zero Dipendenze** - Usa solo PowerShell nativo  

---

## 🚀 Inizia Subito!

```
1. Apri: \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
2. Doppio click: Start_GUI.bat
3. Click: ▶ Avvia Tutto
4. Apri browser: http://localhost:5173
```

**Buon sviluppo! 🎉**

---

## 📊 Statistiche Progetto

- **Totale File:** 16
- **Totale Dimensione:** ~67 KB
- **Righe di Codice PowerShell:** ~800 linee
- **Righe di Documentazione:** ~1500 linee
- **Lingue:** PowerShell, Batch
- **Piattaforma:** Windows 11 + WSL2
- **Versione:** 1.0

---

## 🆘 Supporto

**Problemi?** → Esegui `Check_Configuration.bat`  
**Domande?** → Leggi `README.md` o `COMPLETATO.md`  
**Personalizzazioni?** → Modifica gli script .ps1  

---

*Creato: Dicembre 2024*  
*Ultima Modifica: Dicembre 2024*  
*Progetto: MyGest - Django + React*
