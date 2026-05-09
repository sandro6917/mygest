# Gestione File Documenti - Flusso Completo

## 📋 Panoramica

Questo documento descrive come vengono gestiti i file nella pagina di creazione/modifica documento, sia per file **importati** (upload manuale) che **scansionati**.

---

## 🔄 Flusso File Importati (Upload Manuale)

### Frontend (`DocumentoFormPage.tsx`)

1. **Upload File**
   ```typescript
   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
     const file = e.target.files?.[0];
     if (file) {
       setFormData((prev) => ({ ...prev, file }));
     }
   };
   ```
   - Il file viene **mantenuto in memoria** nel browser come oggetto `File`
   - **NON viene caricato** immediatamente sul server
   - Resta nel form fino al submit

2. **Submit Form**
   ```typescript
   const hasNewFile = formData.file instanceof File;
   if (hasNewFile) {
     submitData = new FormData();
     formPayload.append('file', value);  // ✅ File originale inviato
   }
   ```
   - Il file originale viene inviato al backend via `multipart/form-data`
   - **Il file originale resta intatto** sul disco dell'utente
   - Opzionalmente può essere eliminato dopo il salvataggio (vedi sotto)

### Backend (`DocumentoCreateUpdateSerializer.create()`)

3. **Salvataggio Django**
   ```python
   documento = Documento(**validated_data)
   documento._file_operation = file_operation  # 'copy' o 'move'
   documento._skip_auto_rename = True
   documento.save()
   ```
   - Django salva il file in **directory temporanea** dello storage NAS:
     ```
     /mnt/archivio/tmp/YYYY/CLI-TIT-ANNO-SEQ_originale.pdf
     ```
   - Il file viene **copiato** dalla richiesta HTTP nel NAS tmp

4. **Rinomina e Spostamento**
   ```python
   documento._rename_file_if_needed(current_basename, only_new=False, attrs=attrs_map)
   documento._move_file_into_archivio(attrs=attrs_map)
   ```
   
   **`_move_file_into_archivio()`**:
   - Calcola percorso definitivo: `/mnt/archivio/CLI/TIT/ANNO/`
   - Genera nome file dal pattern: `CLI-TIT-ANNO-SEQ-ATTR1-ATTR2.pdf`
   - **Comportamento dipende da `file_operation`**:
     - **`copy`** (default): Copia in archivio definitivo, **mantiene copia in tmp**
     - **`move`**: Copia in archivio definitivo, **elimina da tmp**

5. **Eliminazione File Originale (opzionale)**
   ```python
   if delete_source and source_path:
       self._create_deletion_request(documento, source_path)
   ```
   - Se l'utente spunta "Elimina file originale dopo import"
   - Crea una `RichiestaEliminazioneFile` per tracciabilità
   - Il file viene eliminato dal path originale sul PC/rete

---

## 📷 Flusso File Scansionati

### Scanner Service (`scanner_service.py`)

1. **Scansione**
   ```python
   scan_dir = TEMP_DIR / scan_id  # /tmp/mygest_scanner/<uuid>/
   cmd = [
       'scanimage',
       '--batch=' + str(scan_dir / 'page_%03d.png'),
       ...
   ]
   subprocess.run(cmd)
   ```
   - Le pagine vengono salvate in **directory temporanea sistema**:
     ```
     /tmp/mygest_scanner/<uuid>/page_001.png
     /tmp/mygest_scanner/<uuid>/page_002.png
     ...
     ```
   - Ogni scansione ha un UUID univoco

2. **Ottimizzazione (se richiesta)**
   ```python
   if optimize:
       optimize_scanned_image(page_file, optimize=True)
   ```
   - Conversione in B/N, aumento contrasto, compressione
   - **Modifica in-place** i PNG nella temp

3. **Merge PDF**
   ```python
   @app.route('/scan/merge', methods=['POST'])
   def merge_scans():
       # Crea PDF da tutti i PNG scansionati
       pdf_path = TEMP_DIR / filename
       img2pdf.convert(..., outputstream=f)
   ```
   - Unisce tutti i PNG in un **PDF unico**
   - Salvato in: `/tmp/mygest_scanner/scansione_YYYY-MM-DD.pdf`
   - **Il PDF resta in temp sul server**

### Frontend (`ScannerSection.tsx`)

4. **Download PDF**
   ```typescript
   const response = await axios.post(
     `${SCANNER_SERVICE_URL}/scan/merge`,
     { scan_ids: scanIds, filename: '...' },
     { responseType: 'blob' }
   );
   ```
   - Il PDF viene scaricato dal server come `Blob`
   - **Non viene salvato su disco** lato client

5. **Conversione in File Object**
   ```typescript
   const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
   const pdfFile = new File([pdfBlob], `scansione_${Date.now()}.pdf`, {
     type: 'application/pdf',
   });
   onFileGenerated(pdfFile);  // ✅ Passa al form
   ```
   - Il blob viene convertito in `File` JavaScript
   - **File esiste solo in memoria browser**
   - Viene passato al form documento come se fosse un upload

6. **Cleanup Scansioni**
   ```typescript
   for (const scanId of scanIds) {
     await axios.delete(`${SCANNER_SERVICE_URL}/scan/${scanId}`);
   }
   ```
   - **Elimina PNG originali** dal server: `/tmp/mygest_scanner/<uuid>/`
   - **Elimina PDF temporaneo** dal server
   - Pulizia immediata dopo il download

### Backend (identico a file importato)

7. **Submit Form** → Stesso flusso dei file importati
   - Il `File` JavaScript viene inviato come `multipart/form-data`
   - Django lo salva in tmp NAS
   - Rinomina e sposta in archivio definitivo

---

## 🗂️ Riepilogo Posizioni File

### File Importato (Upload)

| Fase | Posizione | Tipo | Persistente |
|------|-----------|------|-------------|
| **Pre-submit** | Memoria browser | `File` object | ❌ No |
| **Upload** | `/mnt/archivio/tmp/YYYY/...` | File fisico | ⚠️ Dipende da `file_operation` |
| **Post-save** | `/mnt/archivio/CLI/TIT/ANNO/CLI-TIT-...pdf` | File fisico | ✅ Sì |
| **Originale PC** | Path originale utente | File fisico | ⚠️ Solo se `delete_source=false` |

### File Scansionato

| Fase | Posizione | Tipo | Persistente |
|------|-----------|------|-------------|
| **Scansione** | `/tmp/mygest_scanner/<uuid>/page_*.png` | File fisico | ❌ No (eliminato dopo merge) |
| **Merge PDF** | `/tmp/mygest_scanner/scansione_*.pdf` | File fisico | ❌ No (eliminato dopo download) |
| **Download** | Memoria browser | `File` object | ❌ No |
| **Upload** | `/mnt/archivio/tmp/YYYY/...` | File fisico | ⚠️ Dipende da `file_operation` |
| **Post-save** | `/mnt/archivio/CLI/TIT/ANNO/CLI-TIT-...pdf` | File fisico | ✅ Sì |

---

## ⚠️ Comportamenti Specifici

### `file_operation` (Backend)

Controllato dall'attributo `_file_operation` sul modello `Documento`:

```python
# Default: 'copy'
documento._file_operation = 'copy'  # Mantiene copia in tmp
documento._file_operation = 'move'  # Elimina da tmp dopo spostamento
```

**Implementazione in `_move_file_into_archivio()`**:

```python
# Copia sempre in archivio definitivo
with storage.open(current_name, "rb") as src:
    new_name = storage.save(target_rel, File(src))

# Elimina tmp solo se 'move'
if file_operation == 'move':
    storage.delete(current_name)  # ✅ Elimina tmp
    logger.info("File originale eliminato: %s", current_name)
else:
    logger.info("File originale mantenuto: %s", current_name)  # ⚠️ Resta in tmp
```

### `delete_source_file` (Frontend)

Controllato dal checkbox "Elimina file originale":

```typescript
if (deleteSourceFile && sourceFilePath.trim()) {
  formPayload.append('delete_source_file', 'true');
  formPayload.append('source_file_path', sourceFilePath.trim());
}
```

**Backend**:
```python
if delete_source and source_path:
    self._create_deletion_request(documento, source_path)
```

Crea una `RichiestaEliminazioneFile` che elimina il file dal path originale (PC/rete).

### Cleanup Automatico (Scanner Service)

```python
def cleanup_old_scans():
    """Pulisce scansioni vecchie (> 24 ore)"""
    for scan_id in to_delete:
        delete_scan(scan_id)  # Elimina PNG e directory
```

- Eseguito periodicamente
- Elimina scansioni non completate dopo 24h
- **Previene accumulo spazzatura** in `/tmp/mygest_scanner/`

---

## 🎯 Risposte alle Domande

### 1. File importato viene spostato o copiato in temp?

**Risposta**: Viene **COPIATO** dalla richiesta HTTP nella temp NAS:
- File originale sul PC **resta intatto** (salvo `delete_source_file=true`)
- Django crea una **nuova copia** in `/mnt/archivio/tmp/...`

### 2. Dopo la creazione directory archivio, file viene spostato o copiato?

**Risposta**: Dipende da `file_operation`:
- **`move` (default)**: File viene **COPIATO** in archivio definitivo, **copia tmp eliminata** ✅
- **`copy`**: File viene **COPIATO** in archivio definitivo, **copia tmp rimane** ⚠️

**Nota**: Il default è stato cambiato da `'copy'` a `'move'` per evitare accumulo di file temporanei.

### 3. File scansionati, rimane copia in temp?

**Risposta**: **NO**, vengono eliminati immediatamente:
1. PNG scansionati in `/tmp/mygest_scanner/<uuid>/` → **eliminati dopo merge PDF**
2. PDF temporaneo → **eliminato dopo download nel browser**
3. File in memoria browser → **eliminato dopo submit form**
4. Solo l'archivio definitivo **persiste**: `/mnt/archivio/CLI/TIT/ANNO/...pdf`

---

## 🔧 Ottimizzazioni Possibili

### 1. Pulizia tmp automatica
Attualmente con `file_operation='copy'`, i file in tmp si accumulano. Opzioni:
- **Cambio default**: Usare `'move'` come default
- **Cleanup periodico**: Cronjob che pulisce `/mnt/archivio/tmp/` oltre 7 giorni

### 2. Storage scansioni
Scanner service usa `/tmp/` di sistema che:
- ✅ Si pulisce al reboot
- ⚠️ Spazio limitato per scansioni massive
- Potenziale miglioramento: Configurabile in `settings.py`

### 3. Streaming upload
Attualmente il PDF scansionato:
1. Viene scaricato completamente nel browser (memoria)
2. Re-caricato al server via multipart

Alternativa:
- Frontend passa solo `scan_id` al backend
- Backend prende PDF direttamente da temp scanner service
- Risparmio banda e memoria browser

---

## 📊 Diagramma Flusso Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE IMPORTATO (Upload)                      │
└─────────────────────────────────────────────────────────────────┘

PC Utente                Browser              Backend Django              NAS Storage
    │                        │                       │                         │
    │  File selezionato      │                       │                         │
    ├──────────────────────>│                       │                         │
    │                        │  multipart/form-data  │                         │
    │                        ├──────────────────────>│                         │
    │                        │                       │  save() → tmp/          │
    │                        │                       ├────────────────────────>│
    │                        │                       │  copy: tmp/ persiste    │
    │                        │                       │  move: tmp/ eliminato   │
    │                        │                       │ _move_file_into_archivio│
    │                        │                       ├────────────────────────>│
    │                        │                       │     archivio/CLI/TIT/   │
    │  delete_source=true    │                       │                         │
    │<───────────────────────┼───────────────────────┤                         │
    │  (file eliminato)      │                       │                         │


┌─────────────────────────────────────────────────────────────────┐
│                  FILE SCANSIONATO (Scanner)                     │
└─────────────────────────────────────────────────────────────────┘

Scanner            Scanner Service         Browser            Backend Django        NAS
    │                     │                     │                     │               │
    │  Scansione          │                     │                     │               │
    ├────────────────────>│                     │                     │               │
    │                     │  page_*.png         │                     │               │
    │                     ├────> /tmp/mygest_   │                     │               │
    │                     │                     │                     │               │
    │                     │  merge PDF          │                     │               │
    │                     ├────> /tmp/scan.pdf  │                     │               │
    │                     │                     │                     │               │
    │                     │  Download PDF blob  │                     │               │
    │                     ├────────────────────>│                     │               │
    │                     │  DELETE scans       │                     │               │
    │                     │<────────────────────┤ (elimina PNG+PDF)   │               │
    │                     │  (cleanup tmp)      │                     │               │
    │                     │                     │  multipart upload   │               │
    │                     │                     ├────────────────────>│               │
    │                     │                     │                     │  save() → tmp │
    │                     │                     │                     ├──────────────>│
    │                     │                     │                     │  _move_...    │
    │                     │                     │                     ├──────────────>│
    │                     │                     │                     │  archivio/    │
```

---

**Data Documento**: 2026-02-24  
**Versione**: 1.1  
**Autore**: System Analysis  
**Ultimo aggiornamento**: 2026-02-24 - Default `file_operation` cambiato da `'copy'` a `'move'`
