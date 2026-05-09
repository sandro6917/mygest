# 🚀 Quick Start - Funzionalità Scansione

## Installazione Rapida

### 1. Installa Dipendenze (Prima Volta)

```bash
cd /home/sandro/mygest
source venv/bin/activate
pip install -r scripts/scanner_requirements.txt
```

### 2. Installa SANE (Prima Volta - se non presente)

```bash
sudo apt update
sudo apt install sane sane-utils libsane-dev
```

### 3. Configura Scanner di Rete (Prima Volta)

```bash
# Edita configurazione SANE
sudo nano /etc/sane.d/net.conf

# Aggiungi gli IP degli scanner:
# 192.168.1.10  # Brother ADS-2400N
# 192.168.1.11  # HP Officejet 7510
# 192.168.1.12  # Kyocera ECOSYS M2540dn

# Verifica scanner rilevati
scanimage -L
```

## Uso Quotidiano

### Avvia Servizio Scanner

**Windows** (metodo consigliato):
```
Doppio click su: windows_manager/Quick_Start_Scanner.bat
```

**WSL Server Manager**:
```
1. Apri Start_Manager.bat
2. Seleziona opzione 'D'
```

**Manuale**:
```bash
cd /home/sandro/mygest
source venv/bin/activate
python scripts/scanner_service.py &
```

### Arresta Servizio Scanner

**Windows**:
```
Doppio click su: windows_manager/Quick_Stop_Scanner.bat
```

**Manuale**:
```bash
pkill -f scanner_service.py
```

## Verifica Funzionamento

```bash
# Test rapido
curl http://localhost:8765/health

# Output atteso:
# {"status":"ok","sane_available":true,"version":"1.0.0"}
```

## Uso nell'Applicazione

1. Vai su **Documenti → Nuovo Documento**
2. Nella sezione "File" vedi "Scansione Documento"
3. Seleziona scanner
4. Clicca "Avvia Scansione"
5. Clicca "Unisci e Allega come PDF"
6. Fine! 🎉

## Risoluzione Problemi Rapida

### Servizio non risponde?
```bash
./scripts/test_scanner_service.sh
```

### Scanner non trovati?
```bash
scanimage -L
```

### Log errori?
```bash
tail -f logs/scanner_service.log
```

## Link Documentazione Completa

- `FEATURE_SCANNER_INTEGRATION.md` - Guida completa
- `RIEPILOGO_SCANNER_IMPLEMENTATION.md` - Riepilogo implementazione

---

💡 **Tip**: Aggiungi `Quick_Start_Scanner.bat` ai programmi di avvio automatico di Windows per avere il servizio sempre pronto!
