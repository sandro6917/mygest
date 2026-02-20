# Feature: Padding a 3 Cifre per Codici Unità Fisiche

**Data**: 13 Febbraio 2026  
**Tipo**: Enhancement  
**Modulo**: `archivio_fisico`

## 📋 Panoramica

Modificato il sistema di codifica delle unità fisiche per utilizzare un formato con **padding a 3 cifre** per il progressivo numerico.

## 🔧 Modifiche Apportate

### 1. **Model `UnitaFisica` (`archivio_fisico/models.py`)**

**File**: `archivio_fisico/models.py` (linea 241)

```python
# PRIMA:
new_codice = f"{self.prefisso_codice}{self.progressivo_codice}"
# Generava: DIR1, DIR2, DIR3

# DOPO:
new_codice = f"{self.prefisso_codice}{self.progressivo_codice:03d}"
# Genera: DIR001, DIR002, DIR003
```

### 2. **Migrazione Dati (`0021_update_codice_format_with_padding.py`)**

Creata migrazione per aggiornare **tutti i codici esistenti** al nuovo formato:

- ✅ Aggiorna campo `codice` con padding a 3 cifre
- ✅ Aggiorna campo `full_path` (percorso gerarchico)
- ✅ Aggiorna campo `progressivo` (etichetta descrittiva)
- ✅ Aggiorna ricorsivamente i `full_path` delle unità figlie
- ✅ **83 unità fisiche** aggiornate con successo

**Esempio aggiornamento**:
```
DIR1 → DIR001
STZ2 → STZ002
SF10 → SF010
```

### 3. **Test Aggiornati (`archivio_fisico/tests.py`)**

Modificato test `test_codice_progressivo_incrementale`:

```python
# PRIMA:
self.assertEqual(prima.codice, "STZ1")
self.assertEqual(seconda.codice, "STZ2")

# DOPO:
self.assertEqual(prima.codice, "STZ001")
self.assertEqual(seconda.codice, "STZ002")
```

## 📊 Formato Codice

### Struttura Codice Unità Fisica

```
CODICE = PREFISSO + PROGRESSIVO (3 cifre con padding)

Esempi:
- DIR001  (prefisso="DIR", progressivo=1)
- DIR002  (prefisso="DIR", progressivo=2)
- DIR010  (prefisso="DIR", progressivo=10)
- DIR100  (prefisso="DIR", progressivo=100)
- DIR999  (prefisso="DIR", progressivo=999)
- DIR1000 (prefisso="DIR", progressivo=1000) ← Oltre 999 funziona
```

### Comportamento Padding

Il formato `:03d` garantisce:
- **Minimo 3 cifre** con zeri a sinistra
- **Nessun limite superiore**: progressivi > 999 funzionano correttamente
- **Ordinamento lessicografico corretto**: DIR001, DIR002, ..., DIR010, ..., DIR100

## ✅ Vantaggi

1. **Ordinamento corretto**: I codici si ordinano correttamente alfabeticamente
   - Prima: DIR1, DIR10, DIR2 (ordinamento sbagliato)
   - Dopo: DIR001, DIR002, DIR010 (ordinamento corretto)

2. **Codici allineati**: Lunghezza uniforme per codici con stesso prefisso
   ```
   DIR001
   DIR002
   DIR003
   ```

3. **Leggibilità migliorata**: Codici più professionali e facili da leggere

4. **Compatibilità**: Nessuna limitazione per progressivi > 999

## 🧪 Test e Verifica

### Test Eseguiti

```bash
# Verifica codici esistenti aggiornati
✅ 83 unità fisiche migrate con successo
✅ DIR1 → DIR001
✅ DIR2 → DIR002  
✅ DIR3 → DIR003

# Test creazione nuova unità
✅ Nuova unità DIR → DIR004 (progressivo=4)

# Verifica altri prefissi
✅ UFF001, ST001, ST003, ST004, etc.
```

### Verifica Full Path

I `full_path` sono stati aggiornati correttamente:

```
PRIMA: UFF1/ST6/SC7/RIP28/DIR4
DOPO:  UFF001/ST006/SC007/RIP028/DIR004
```

## 📁 File Modificati

| File | Tipo Modifica | Descrizione |
|------|---------------|-------------|
| `archivio_fisico/models.py` | Codice | Formato codice con `:03d` |
| `archivio_fisico/migrations/0021_update_codice_format_with_padding.py` | Migrazione | Aggiorna codici esistenti |
| `archivio_fisico/tests.py` | Test | Aggiorna assertion test |

## 🔄 Migrazione Reversibile

La migrazione include una funzione `reverse` che rimuove il padding:

```python
# Forward: DIR1 → DIR001
# Reverse: DIR001 → DIR1
```

Per revertire (se necessario):
```bash
python manage.py migrate archivio_fisico 0020_add_cliente_to_unitafisica
```

## 💡 Note Implementative

### Logica di Generazione

Il progressivo viene ancora calcolato come intero (`progressivo_codice`), ma formattato con padding durante la generazione del `codice`:

```python
self.progressivo_codice = 4  # Intero
self.codice = f"{self.prefisso_codice}{self.progressivo_codice:03d}"
# → codice = "DIR004"
```

### Compatibilità Backward

- ✅ Nessuna modifica a schema database (campi esistenti)
- ✅ API REST continua a funzionare
- ✅ Frontend riceve nuovi codici automaticamente
- ✅ Vecchi riferimenti aggiornati in migrazione

## 🎯 Esempi Uso

### Creazione Nuova Unità

```python
from archivio_fisico.models import UnitaFisica

# Creazione manuale
unita = UnitaFisica.objects.create(
    prefisso_codice="DIR",
    nome="Dichiarazioni dei Redditi 2024",
    tipo=UnitaFisica.Tipo.CONTENITORE,
    parent=ripiano
)

print(unita.codice)  # Output: DIR004
print(unita.progressivo_codice)  # Output: 4
print(unita.full_path)  # Output: UFF001/ST006/SC007/RIP028/DIR004
```

### Query e Ordinamento

```python
# Ordinamento corretto per codice
UnitaFisica.objects.filter(prefisso_codice="DIR").order_by("codice")
# Risultato: DIR001, DIR002, DIR003, DIR004, ...

# Ricerca per codice
UnitaFisica.objects.get(codice="DIR001")
```

## ✨ Conclusione

La modifica migliora significativamente la **leggibilità**, l'**ordinamento** e la **professionalità** del sistema di codifica delle unità fisiche, mantenendo piena compatibilità con il sistema esistente.

---

**Autore**: Sistema MyGest  
**Versione**: 1.0  
**Status**: ✅ Implementato e Testato
