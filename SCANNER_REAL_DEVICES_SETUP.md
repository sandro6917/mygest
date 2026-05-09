# Configurazione Scanner Reali - Note Tecniche

## 📊 Stato Attuale

### ✅ Configurazione Completata
- **Servizio Scanner**: Attivo su `http://localhost:8765`
- **SANE installato**: ✓
- **Scanner di rete configurati**: ✓
  - `192.168.1.7` - Brother ADS-2400N (raggiungibile - ping OK)
  - `192.168.1.151` - Kyocera ECOSYS M2540dn (raggiungibile - ping OK)

### ⚠️ Scanner Non Rilevati da SANE

Gli scanner sono raggiungibili via rete ma SANE non li rileva automaticamente. Questo è **normale** e dipende da:

1. **Driver/Backend specifici** - Ogni marca richiede il proprio backend SANE
2. **Protocolli proprietari** - Alcuni scanner usano protocolli non standard
3. **Configurazione avanzata** - Potrebbe essere necessaria configurazione specifica

## 🎯 Modalità Mock (Attuale)

Il servizio funziona in **modalità mock** che è ideale per:
- ✅ Testing dell'interfaccia utente
- ✅ Sviluppo e debugging
- ✅ Demo e presentazioni
- ✅ Verifica del workflow completo

**Vantaggi modalità mock**:
- Nessun hardware necessario
- Sempre disponibile
- Performance prevedibili
- Genera immagini di test in formato A4

## 🔧 Come Abilitare Scanner Reali (Quando Necessario)

### Opzione 1: Backend Brother (per Brother ADS-2400N)

Brother fornisce driver Linux specifici:

```bash
# Scarica driver dal sito Brother
# https://support.brother.com/g/b/downloadlist.aspx?c=us&lang=en&prod=ads2400n_all&os=128

# Installa pacchetto .deb o .rpm
sudo dpkg -i brscan4-*.deb  # Per Debian/Ubuntu
# oppure
sudo rpm -i brscan4-*.rpm   # Per Red Hat/Fedora

# Configura scanner di rete
brsaneconfig4 -a name=Brother model=ADS-2400N ip=192.168.1.7
```

### Opzione 2: Backend Kyocera

```bash
# Verifica se c'è supporto nativo
scanimage -L

# Se non funziona, cerca driver proprietari:
# https://www.kyoceradocumentsolutions.com/
```

### Opzione 3: Airscan (eSCL - Scanner via HTTP)

Molti scanner moderni supportano il protocollo eSCL (AirScan/Mopria):

```bash
# Abilita backend airscan
sudo bash -c 'echo "airscan" >> /etc/sane.d/dll.conf'

# Configura scanner manualmente
sudo nano /etc/sane.d/airscan.conf

# Aggiungi:
[devices]
"Brother" = http://192.168.1.7/eSCL, eSCL
"Kyocera" = http://192.168.1.151/eSCL, eSCL

# Riavvia servizio scanner
pkill -f scanner_service.py
python scripts/scanner_service.py > logs/scanner_service.log 2>&1 &
```

### Opzione 4: SANE Network Backend

Se gli scanner hanno un servizio saned in esecuzione:

```bash
# Gli scanner sono già configurati in /etc/sane.d/net.conf:
# 192.168.1.7    # Brother
# 192.168.1.151  # Kyocera

# Verifica connettività SANE (porta 6566)
nc -zv 192.168.1.7 6566
nc -zv 192.168.1.151 6566

# Se risponde, SANE dovrebbe rilevarli automaticamente
scanimage -L
```

## 🧪 Test Scanner Reali

Quando avrai configurato i driver:

```bash
# 1. Test discovery
scanimage -L

# Output atteso:
# device `brother4:net1;dev0' is a Brother ADS-2400N scanner
# device `airscan:escl:Kyocera:http://192.168.1.151/eSCL' is a ...

# 2. Test scansione singola pagina
scanimage --device brother4:net1;dev0 \
  --format=png \
  --resolution 300 \
  --mode Gray \
  > test_scan.png

# 3. Riavvia servizio scanner
pkill -f scanner_service.py
python scripts/scanner_service.py > logs/scanner_service.log 2>&1 &

# 4. Test API
curl http://localhost:8765/scanners
# Dovrebbe mostrare gli scanner reali invece dei mock
```

## 📝 Configurazione Produzione vs Sviluppo

### Sviluppo (Attuale - Consigliato)
```bash
# Modalità Mock - Nessuna configurazione necessaria
# Scanner disponibili: 3 mock (Brother, HP, Kyocera)
# Perfetto per UI testing e sviluppo
```

### Produzione (Quando Necessario)
```bash
# Scanner reali configurati
# Richiede driver/backend specifici
# Usa per scansioni reali di documenti
```

## 🎯 Raccomandazione

**Per ora, continua con la modalità mock**. È perfetta per:
1. ✅ Testare l'interfaccia React
2. ✅ Verificare il workflow completo
3. ✅ Demo della funzionalità
4. ✅ Sviluppo senza dipendenze hardware

**Passa agli scanner reali solo quando**:
- Hai bisogno di scansionare documenti reali
- Hai tempo per configurare i driver specifici
- Gli scanner supportano protocolli standard (eSCL/AirScan)

## 🔗 Risorse Utili

### Driver Brother
- https://support.brother.com/
- Driver: brscan4
- Tool: brsaneconfig4

### Driver Kyocera
- https://www.kyoceradocumentsolutions.com/
- Cerca "Linux Scanner Driver"

### Backend SANE
- http://www.sane-project.org/
- Lista backend: http://www.sane-project.org/sane-backends.html
- Airscan (eSCL): https://github.com/alexpevzner/sane-airscan

### Test Protocolli Scanner
```bash
# Test eSCL (AirScan)
curl http://192.168.1.7/eSCL/ScannerCapabilities
curl http://192.168.1.151/eSCL/ScannerCapabilities

# Test WSD (Web Services for Devices)
curl http://192.168.1.7:5357/

# Se rispondono, puoi configurare airscan
```

## 📊 Stato Scanner

| Scanner | IP | Ping | SANE | Protocollo | Stato |
|---------|-------|------|------|------------|-------|
| Brother ADS-2400N | 192.168.1.7 | ✅ OK | ⚠️ Mock | eSCL? | Raggiungibile |
| Kyocera M2540dn | 192.168.1.151 | ✅ OK | ⚠️ Mock | eSCL? | Raggiungibile |

## 🚀 Prossimi Passi (Opzionali)

Se vuoi abilitare gli scanner reali:

1. **Test protocolli supportati**:
   ```bash
   curl -v http://192.168.1.7/eSCL/ScannerCapabilities 2>&1 | grep -i "http"
   curl -v http://192.168.1.151/eSCL/ScannerCapabilities 2>&1 | grep -i "http"
   ```

2. **Scarica driver Brother** dal sito ufficiale

3. **Configura airscan** se supportano eSCL

4. **Riavvia servizio** e testa

Per ora, **la modalità mock è sufficiente** per lo sviluppo e il testing! 🎉

---

**Nota**: Questa configurazione avanzata è **opzionale**. Il sistema funziona perfettamente in modalità mock per tutti i test e lo sviluppo dell'interfaccia.
