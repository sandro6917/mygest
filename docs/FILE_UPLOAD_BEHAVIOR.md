# Comportamento Upload e Gestione File

## Limitazioni del Browser Web

### File Originale sul Computer dell'Utente

**IMPORTANTE**: Per ragioni di sicurezza, i browser web moderni **NON** permettono alle applicazioni web di:
- Accedere al percorso completo del file sul filesystem dell'utente
- Eliminare file dal computer dell'utente
- Modificare file sul disco locale dell'utente

Quando un utente seleziona un file tramite l'input file (`<input type="file">`), il browser:
1. Carica il file in memoria o in una directory temporanea del browser
2. Fornisce solo il nome del file (non il percorso completo)
3. Invia il contenuto del file al server quando viene fatto l'upload

**Il file originale sul computer dell'utente rimane sempre intatto**, indipendentemente dall'opzione "Copia" o "Sposta" selezionata.

## Opzioni "Copia" vs "Sposta"

Le opzioni "Copia" e "Sposta" si riferiscono alla gestione del file **sul server**, non sul computer dell'utente:

### Opzione "Copia" (Copy)
1. Il file viene uploadato dal browser al server
2. Il server salva il file in una directory temporanea
3. Il file viene **copiato** dalla directory temporanea alla directory di archivio definitiva
4. Il file nella directory temporanea **viene mantenuto** (utile per debug o backup)

### Opzione "Sposta" (Move)
1. Il file viene uploadato dal browser al server
2. Il server salva il file in una directory temporanea
3. Il file viene **spostato** dalla directory temporanea alla directory di archivio definitiva
4. Il file nella directory temporanea **viene eliminato** (risparmio spazio disco)

## Flusso Completo

```
[Computer Utente]
    ↓ (Upload via browser)
[Directory Temporanea Server] (/tmp o simile)
    ↓
    ├─ COPIA → [Archivio] + Mantiene file in temp
    └─ SPOSTA → [Archivio] + Elimina file in temp
```

## Workflow Consigliato

### Per l'Utente:
1. Selezionare il file dal proprio computer
2. Scegliere l'opzione "Sposta" (consigliata per risparmiare spazio su server)
3. Salvare il documento
4. **Se necessario**, eliminare manualmente il file dal proprio computer

### Automazione dell'Eliminazione Locale
Se si desidera automatizzare l'eliminazione del file locale, sarebbe necessario:
- Creare un'applicazione desktop dedicata (non web)
- Usare tecnologie come Electron o applicazioni native
- Richiedere permessi espliciti all'utente

## Implementazione Tecnica

### Backend (Django)

Il file viene gestito nel metodo `_move_file_into_archivio()` del modello `Documento`:

```python
def _move_file_into_archivio(self):
    # ...
    file_operation = getattr(self, '_file_operation', 'copy')
    
    # Copia il file nella destinazione finale
    with storage.open(current_name, "rb") as src:
        new_name = storage.save(target_rel, File(src))
    
    # Se 'move', elimina il file temporaneo
    if file_operation == 'move':
        storage.delete(current_name)
```

### Frontend (React)

Il campo viene inviato tramite FormData:

```typescript
if (hasNewFile) {
    const submitData = new FormData();
    submitData.append('file', fileObject);
    submitData.append('file_operation', 'move'); // o 'copy'
    // ...
}
```

## Log e Debug

Per verificare il corretto funzionamento dell'opzione "Sposta", controllare i log del server:

```bash
tail -f /var/log/django/debug.log | grep "file_operation"
```

Log attesi:
- `file_operation=move` - Operazione richiesta
- `File originale eliminato: tmp/...` - Conferma eliminazione
- `File originale mantenuto: tmp/...` - File non eliminato (copia)

## Conclusione

L'opzione "Sposta" **funziona correttamente** per ottimizzare lo spazio disco sul server eliminando i file temporanei dopo l'upload, ma **non può** eliminare file dal computer dell'utente per limitazioni di sicurezza del browser.

Se è necessaria questa funzionalità, valutare lo sviluppo di un'applicazione desktop dedicata.
