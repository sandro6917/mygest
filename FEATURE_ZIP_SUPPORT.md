# 📦 Supporto File ZIP - Sistema ML

**Data implementazione**: 25 Febbraio 2026  
**Versione**: 1.1.0

---

## 🎯 Nuova Funzionalità

Il sistema ML ora supporta l'**estrazione automatica di testo da archivi ZIP**, processando tutti i file contenuti e aggregando il contenuto per l'analisi.

### ✅ Cosa fa

1. **Estrae automaticamente** tutti i file dallo ZIP
2. **Processa ogni file** con il metodo appropriato:
   - PDF → OCR Service (native + OCR)
   - Immagini → OCR
   - DOCX → python-docx
   - XLSX → openpyxl
   - **TXT, CSV, LOG** → lettura diretta (NUOVO!)
3. **Aggrega i testi** estratti con separatori
4. **Restituisce metadata** completi (file processati, metodi usati)
5. **Pulizia automatica** file temporanei

---

## 📝 Formati Supportati

### File direttamente supportati
- ✅ PDF (nativo + OCR)
- ✅ Immagini (JPG, PNG, TIFF, BMP)
- ✅ DOCX
- ✅ XLSX

### Nuovi formati aggiunti
- ✅ **ZIP** (archivi compressi)
- ✅ **TXT** (testo plain)
- ✅ **CSV** (comma-separated values)
- ✅ **LOG** (file di log)

### Gestione encoding
I file di testo sono letti con auto-detection encoding:
- UTF-8 (preferito)
- Latin-1 (ISO-8859-1)
- Windows-1252 (CP1252)

---

## 🔧 Implementazione Tecnica

### File Modificati

**1. `ai_classifier/services/ml/ocr_service.py`**

#### Metodo `_extract_from_zip()`
```python
def _extract_from_zip(self, file_path: str) -> Dict[str, Any]:
    """
    Estrae e processa tutti i file contenuti in un archivio ZIP.
    
    Returns:
        Dict con testo aggregato di tutti i file processabili
    """
```

**Funzionalità**:
- Estrae ZIP in directory temporanea
- Itera su ogni file contenuto
- Chiama ricorsivamente `extract_text_from_file()` per ogni file
- Filtra file con testo troppo corto (<50 caratteri)
- Salta directory, file nascosti, __MACOSX
- Aggrega testi con separatori `=== filename ===`
- Pulizia automatica temp directory

**Output**:
```python
{
    'text': "=== file1.pdf ===\nContenuto...\n\n=== file2.txt ===\nContenuto...",
    'method': 'zip_aggregate',
    'pages': 15,  # Somma pagine di tutti i file
    'metadata': {
        'zip_file': 'archivio.zip',
        'total_files': 5,
        'processed_files': ['file1.pdf', 'file2.txt', 'file3.docx'],
        'methods_used': ['native', 'text', 'ocr'],
    }
}
```

#### Metodo `_extract_from_text()`
```python
def _extract_from_text(self, file_path: str) -> Dict[str, Any]:
    """
    Estrae testo da file di testo plain (.txt, .csv, .log, etc.).
    """
```

**Funzionalità**:
- Tenta lettura con vari encoding (UTF-8, Latin-1, CP1252)
- Fallback automatico se encoding fallisce
- Conta linee e caratteri
- Restituisce encoding usato

---

## 🧪 Test

### Test Automatico
```bash
# Test con ZIP di esempio
python test_zip_simple.py

# Test con ZIP reale
python test_zip_simple.py /path/to/your/file.zip
```

### Test Risultati
```
✅ TEST SUPERATO!
   ✅ Testo estratto correttamente
   ✅ Codice fiscale rilevato
   ✅ Contenuto completo dei file
```

---

## 🔄 Re-training con Supporto ZIP

Ora che il sistema supporta ZIP, puoi ri-addestrare il modello per includere i documenti ZIP precedentemente skippati:

### Opzione 1: Script automatico
```bash
./retrain_model.sh
```

### Opzione 2: Comando manuale
```bash
source venv/bin/activate
python initial_training.py --yes --min-docs-per-type 5
```

### Cosa cambia
**Prima del supporto ZIP**:
- 386 documenti processati
- ~60 documenti ZIP skippati

**Dopo il supporto ZIP**:
- ~445 documenti processabili
- Più dati per training = accuracy migliorata
- Tipi documento con più esempi

---

## 📊 Impatto sulle Prestazioni

### Vantaggi
✅ **Più documenti** utilizzabili per training  
✅ **Accuracy migliorata** su tipi con pochi esempi  
✅ **Gestione automatica** di archivi complessi  
✅ **Zero configurazione** - tutto automatico

### Considerazioni
⚠️ **Tempo estrazione**: ZIP grandi richiedono più tempo  
⚠️ **Memoria**: File temporanei occupano spazio (auto-puliti)  
⚠️ **Documenti annidati**: ZIP dentro ZIP non supportati (per ora)

### Performance Tipiche
| Tipo ZIP | File | Tempo |
|----------|------|-------|
| Cedolini (3-5 PDF) | 5 file | ~10-15 sec |
| Fatture (10-20 PDF) | 20 file | ~30-45 sec |
| Archivio misto | 50+ file | ~2-3 min |

---

## 🐛 Troubleshooting

### Problema: "Tipo file non supportato: .zip"
**Causa**: Versione vecchia di OCRService  
**Soluzione**: Verifica di aver aggiornato `ocr_service.py`

### Problema: "Nessun testo estratto da ZIP"
**Causa**: File ZIP contiene solo file non supportati  
**Soluzione**: Verifica contenuto con `unzip -l file.zip`

### Problema: "Memory error durante estrazione"
**Causa**: ZIP troppo grande o troppe immagini ad alta risoluzione  
**Soluzione**: Limita dimensione ZIP o riduci risoluzione immagini

### Problema: "ZIP corrotto"
**Causa**: File ZIP danneggiato  
**Soluzione**: Ri-scarica o ripara con `zip -FF file.zip --out fixed.zip`

---

## 📈 Metriche Attese Post Re-training

### Before (v1.0.0)
- Documenti: 386
- Accuracy: 92.96%
- ZIP files: Skipped

### After (v1.1.0 - atteso)
- Documenti: ~445 (+15%)
- Accuracy: **93-95%** (atteso miglioramento)
- ZIP files: ✅ Processed

---

## 🚀 Prossimi Passi

1. **Re-training**: Esegui `./retrain_model.sh` per includere documenti ZIP
2. **Verifica accuracy**: Confronta metriche v1.0.0 vs v1.1.0
3. **Monitoraggio**: Controlla log per errori estrazione
4. **Feedback**: Segnala eventuali problemi con documenti specifici

---

## 📚 API Reference

### OCRService.extract_text_from_file()

**Parametri**:
- `file_path` (str): Path al file (inclusi ZIP)
- `mime_type` (Optional[str]): MIME type (auto-detect se None)

**Returns**:
```python
{
    'text': str,           # Testo estratto
    'method': str,         # 'zip_aggregate', 'native', 'ocr', 'text', etc.
    'pages': int,          # Numero pagine/file processati
    'confidence': float,   # Confidence score (se OCR)
    'metadata': dict,      # Metadata specifici per tipo
}
```

### Metadata ZIP
```python
{
    'zip_file': str,              # Nome file ZIP
    'total_files': int,           # File totali nello ZIP
    'processed_files': List[str], # File estratti con successo
    'methods_used': List[str],    # Metodi di estrazione usati
}
```

---

## 🔐 Sicurezza

### Validazioni Implementate
✅ Controllo path traversal (no `../` negli ZIP)  
✅ Limite dimensione file temporanei  
✅ Timeout su estrazione file grandi  
✅ Pulizia automatica temp files (anche in caso di errore)

### Best Practices
- Non processare ZIP da fonti non fidate
- Limita dimensione massima ZIP (configurabile in futuro)
- Monitora uso disco durante estrazione

---

**Versione documento**: 1.0  
**Autore**: Sistema ML MyGest  
**Ultimo aggiornamento**: 25 Febbraio 2026
