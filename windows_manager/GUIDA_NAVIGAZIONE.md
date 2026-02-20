# 🗂️ Windows Manager - Guida Rapida alla Documentazione

## 🎯 Dove Trovare Cosa

### 🚀 Per Iniziare Subito

| Voglio... | Leggi Questo |
|-----------|--------------|
| **Usare subito SSH** | [SSH_QUICK_START.md](SSH_QUICK_START.md) |
| **Capire il Windows Manager** | [README.md](README.md) |
| **Vedere tutti i file disponibili** | [INDEX.md](INDEX.md) |

### 🔧 Configurazione e Setup

| Voglio... | Leggi Questo |
|-----------|--------------|
| **Configurare SSH completo** | [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md) |
| **Setup port forwarding** | Esegui [Setup_SSH_PortForward.ps1](Setup_SSH_PortForward.ps1) |
| **Verificare la configurazione WSL** | Esegui [Check_Configuration.bat](Check_Configuration.bat) |

### 📖 Documentazione Tecnica

| Voglio... | Leggi Questo |
|-----------|--------------|
| **Capire come funziona SSH** | [FEATURE_SSH_MANAGEMENT.md](FEATURE_SSH_MANAGEMENT.md) |
| **Vedere cosa è cambiato** | [CHANGELOG.md](CHANGELOG.md) |
| **Testare le funzionalità** | [CHECKLIST_SSH.md](CHECKLIST_SSH.md) |
| **Riepilogo completo** | [IMPLEMENTAZIONE_SSH_COMPLETATA.md](IMPLEMENTAZIONE_SSH_COMPLETATA.md) |

### ⚡ Script Rapidi

| Voglio... | Usa Questo |
|-----------|------------|
| **GUI completa** | [Start_GUI.bat](Start_GUI.bat) |
| **Menu interattivo** | [Start_Manager.bat](Start_Manager.bat) |
| **Avviare SSH velocemente** | [Quick_Start_SSH.bat](Quick_Start_SSH.bat) |
| **Fermare SSH velocemente** | [Quick_Stop_SSH.bat](Quick_Stop_SSH.bat) |
| **Riavviare SSH velocemente** | [Quick_Restart_SSH.bat](Quick_Restart_SSH.bat) |
| **Avviare tutto (Django+Frontend)** | [Quick_Start_All.bat](Quick_Start_All.bat) |

---

## 📚 Ordine di Lettura Consigliato

### Per Utenti Nuovi

1. **[README.md](README.md)** - Panoramica generale (10 min)
2. **[SSH_QUICK_START.md](SSH_QUICK_START.md)** - Setup SSH rapido (5 min)
3. **[INDEX.md](INDEX.md)** - Indice completo (2 min)

### Per Configurazione Avanzata

1. **[SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md)** - Configurazione completa SSH (30 min)
2. Esegui **[Setup_SSH_PortForward.ps1](Setup_SSH_PortForward.ps1)** (2 min)
3. Leggi sezioni sicurezza in SSH_SETUP_GUIDE.md (15 min)

### Per Sviluppatori/Tecnici

1. **[FEATURE_SSH_MANAGEMENT.md](FEATURE_SSH_MANAGEMENT.md)** - Documentazione tecnica (20 min)
2. **[CHANGELOG.md](CHANGELOG.md)** - Modifiche versione (5 min)
3. **[CHECKLIST_SSH.md](CHECKLIST_SSH.md)** - Test da eseguire (variabile)

---

## 🎯 FAQ - Domande Frequenti

### Come avvio SSH?

**Risposta Rapida**: Doppio click su `Quick_Start_SSH.bat`

**Risposta Completa**: Vedi [SSH_QUICK_START.md](SSH_QUICK_START.md)

### Come mi connetto da altro PC?

**Risposta Rapida**: 
```bash
ssh tuo_utente@IP_PC_WINDOWS
```

**Risposta Completa**: Vedi sezione "Come Connetterti" in [SSH_QUICK_START.md](SSH_QUICK_START.md)

### Come configuro il port forwarding?

**Risposta Rapida**: Esegui `Setup_SSH_PortForward.ps1` da PowerShell come Amministratore

**Risposta Completa**: Vedi [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md) sezione "Port Forwarding"

### SSH non si avvia, cosa faccio?

**Risposta Rapida**: 
```bash
sudo apt install openssh-server -y
```

**Risposta Completa**: Vedi sezione "Troubleshooting" in [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md)

### Come rendo SSH più sicuro?

**Risposta Completa**: Vedi sezione "Sicurezza" in [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md)

### Quali file devo leggere per sviluppare?

**Risposta**: 
1. [FEATURE_SSH_MANAGEMENT.md](FEATURE_SSH_MANAGEMENT.md)
2. [WSL_Server_Manager.ps1](WSL_Server_Manager.ps1)
3. [WSL_Server_Manager_GUI.ps1](WSL_Server_Manager_GUI.ps1)

---

## 🗺️ Mappa Mentale della Documentazione

```
Windows Manager
├── 📖 Guide Utente
│   ├── README.md (Generale)
│   ├── SSH_QUICK_START.md (Quick start SSH)
│   └── SSH_SETUP_GUIDE.md (Setup completo SSH)
│
├── 📋 Riferimenti
│   ├── INDEX.md (Indice file)
│   └── CHANGELOG.md (Versioni)
│
├── 🔧 Documentazione Tecnica
│   ├── FEATURE_SSH_MANAGEMENT.md (Implementazione)
│   ├── CHECKLIST_SSH.md (Test)
│   └── IMPLEMENTAZIONE_SSH_COMPLETATA.md (Riepilogo)
│
├── ⚡ Script PowerShell
│   ├── WSL_Server_Manager.ps1 (Console)
│   ├── WSL_Server_Manager_GUI.ps1 (GUI)
│   └── Setup_SSH_PortForward.ps1 (Setup)
│
└── 🚀 Script Batch
    ├── Start_GUI.bat
    ├── Start_Manager.bat
    ├── Quick_Start_SSH.bat
    ├── Quick_Stop_SSH.bat
    └── Quick_Restart_SSH.bat
```

---

## 🏃 Percorsi Veloci

### Scenario 1: "Voglio solo far funzionare SSH"

1. Doppio click `Quick_Start_SSH.bat` ✅ Fatto!

### Scenario 2: "Voglio connettermi da rete locale"

1. Leggi [SSH_QUICK_START.md](SSH_QUICK_START.md) sezione "Setup Iniziale"
2. Esegui `Setup_SSH_PortForward.ps1` come Amministratore
3. Esegui `Quick_Start_SSH.bat`
4. Connettiti con `ssh utente@IP_PC`

### Scenario 3: "Voglio usare l'interfaccia grafica"

1. Doppio click `Start_GUI.bat`
2. Nella sezione SSH, click "▶ Avvia"
3. Osserva stato diventare "● ATTIVO"

### Scenario 4: "Voglio configurare tutto in modo sicuro"

1. Leggi [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md) completo
2. Segui sezione "Sicurezza: Autenticazione con Chiave SSH"
3. Segui sezione "Best Practices"
4. Esegui test in [CHECKLIST_SSH.md](CHECKLIST_SSH.md)

---

## 📞 Supporto

**Problemi?** Cerca in questo ordine:

1. 🔍 **FAQ sopra** - Domande comuni
2. 📖 **SSH_SETUP_GUIDE.md** - Sezione Troubleshooting
3. ✅ **CHECKLIST_SSH.md** - Verifica test
4. 📝 **FEATURE_SSH_MANAGEMENT.md** - Documentazione tecnica

---

## 🎓 Glossario

- **SSH**: Secure Shell, protocollo per accesso remoto sicuro
- **WSL**: Windows Subsystem for Linux
- **Port Forwarding**: Reindirizzamento porte da Windows a WSL
- **GUI**: Graphical User Interface (interfaccia grafica)
- **Batch**: File .bat eseguibili su Windows
- **PowerShell**: Shell di Windows per scripting

---

**Ultima modifica**: 15 Febbraio 2026  
**Versione**: 1.1.0  
**Autore**: GitHub Copilot
