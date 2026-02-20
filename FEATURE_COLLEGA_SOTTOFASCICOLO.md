# Feature: Collegamento Sottofascicolo dalla Detail Page

## 🎯 Obiettivo
Permettere di collegare un fascicolo esistente come sottofascicolo direttamente dalla detail page di un fascicolo.

## 📝 Modifiche Implementate

### 1. View: `fascicoli/views.py` - Classe `FascicoloDetailView`

**Aggiunto al context**:
```python
# Fascicoli collegabili: stesso cliente, titolario, anno, nessun parent, escludi se stesso
ctx["fascicoli_collegabili"] = (
    Fascicolo.objects.filter(
        cliente=f.cliente,
        titolario_voce=f.titolario_voce,
        anno=f.anno,
        parent__isnull=True
    )
    .exclude(pk=f.pk)
    .select_related("titolario_voce")
    .order_by("-progressivo")[:20]
)
```

**Logica**:
- Filtra fascicoli con **stesso cliente, titolario e anno** del fascicolo corrente
- Solo fascicoli **senza parent** (non già collegati ad altri fascicoli)
- **Escludi il fascicolo corrente** (prevenzione self-reference)
- Ordinamento: progressivo decrescente
- Limite: **20 fascicoli** più recenti

---

### 2. View: `fascicoli/views.py` - Funzione `fascicolo_collega`

**Validazioni aggiunte** (prima del collegamento):

```python
# 1. Cliente deve coincidere
if target.cliente_id != fascicolo.cliente_id:
    messages.error(request, f"Impossibile collegare: il cliente del fascicolo {target.codice} non coincide.")
    return redirect(redirect_url)

# 2. Voce di titolario deve coincidere
if target.titolario_voce_id != fascicolo.titolario_voce_id:
    messages.error(request, f"Impossibile collegare: la voce di titolario del fascicolo {target.codice} non coincide.")
    return redirect(redirect_url)

# 3. Anno deve coincidere
if target.anno != fascicolo.anno:
    messages.error(request, f"Impossibile collegare: l'anno del fascicolo {target.codice} non coincide.")
    return redirect(redirect_url)

# 4. Target non deve avere già un parent
if target.parent_id:
    messages.error(request, f"Il fascicolo {target.codice} è già collegato ad un altro fascicolo.")
    return redirect(redirect_url)
```

**Perché queste validazioni?**
Rispettano le **business rules** dei sottofascicoli:
- Cliente, titolario e anno DEVONO coincidere con il parent
- Un fascicolo non può essere sottofascicolo di più fascicoli contemporaneamente

---

### 3. Template: `fascicoli/templates/fascicoli/fascicolo_detail.html`

**Modificata la Card "Gerarchia"**:

```html
<!-- Sezione per collegare fascicoli esistenti -->
{% if fascicoli_collegabili %}
  <hr style="margin: 16px 0; border: none; border-top: 1px solid #ddd;">
  <p><strong>Collega fascicolo esistente come sottofascicolo:</strong></p>
  <p class="muted" style="font-size: 0.9em; margin-bottom: 8px;">
    Fascicoli dello stesso cliente non collegati ad altri fascicoli
  </p>
  <ul class="list">
    {% for fasc in fascicoli_collegabili %}
      <li style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
        <span>
          <strong>{{ fasc.codice }}</strong> — {{ fasc.titolo|truncatewords:8 }}
          <small class="muted">[{{ fasc.titolario_voce.codice }} · {{ fasc.anno }}]</small>
        </span>
        <form method="post" action="{% url 'fascicoli:collega' fascicolo.pk %}" style="margin: 0;">
          {% csrf_token %}
          <input type="hidden" name="target_id" value="{{ fasc.pk }}">
          <button 
            type="submit" 
            class="btn btn-sm btn-secondary" 
            title="Collega {{ fasc.codice }} come sottofascicolo"
            onclick="return confirm('Collegare {{ fasc.codice }} come sottofascicolo di {{ fascicolo.codice }}?');"
          >
            + Collega
          </button>
        </form>
      </li>
    {% endfor %}
  </ul>
{% endif %}
```

**Elementi UI**:
- ✅ **Lista fascicoli collegabili** con codice, titolo (troncato a 8 parole), titolario e anno
- ✅ **Pulsante "+ Collega"** per ogni fascicolo
- ✅ **Conferma utente** (popup JavaScript) prima del collegamento
- ✅ **Form POST** verso l'endpoint `fascicoli:collega`
- ✅ **Visibilità condizionale**: mostra sezione solo se ci sono fascicoli collegabili

---

## 🎨 User Experience

### Flusso Utente

1. **Utente apre la detail page** di un fascicolo (es. `ROSSMRO-01-2025-005`)
2. **Naviga alla card "Gerarchia"**
3. **Vede la lista "Collega fascicolo esistente come sottofascicolo"**
   - Es: `ROSSMRO-01-2025-003 — Contratto preliminare [01 · 2025]`
4. **Click su "+ Collega"**
5. **Popup conferma**: "Collegare ROSSMRO-01-2025-003 come sottofascicolo di ROSSMRO-01-2025-005?"
6. **Conferma** → POST a `/fascicoli/{pk}/collega/`
7. **Redirect** alla detail page con messaggio di successo
8. **Il fascicolo collegato compare** nella lista "Sottofascicoli"

### Validazioni Visibili

Se l'utente tenta di collegare un fascicolo non valido:

- ❌ **Cliente diverso**: "Impossibile collegare: il cliente del fascicolo XXXXX non coincide."
- ❌ **Titolario diverso**: "Impossibile collegare: la voce di titolario del fascicolo XXXXX non coincide."
- ❌ **Anno diverso**: "Impossibile collegare: l'anno del fascicolo XXXXX non coincide."
- ❌ **Già collegato**: "Il fascicolo XXXXX è già collegato ad un altro fascicolo."
- ❌ **Creerebbe ciclo**: "Collegamento non valido: creerebbe un ciclo."

---

## 🔒 Business Rules Rispettate

✅ **Coerenza dati**: Cliente, titolario, anno identici (validato lato server)  
✅ **Unicità parent**: Un fascicolo può avere un solo parent  
✅ **Prevenzione cicli**: Verifica che il collegamento non crei dipendenze circolari  
✅ **Progressivi**: Auto-generazione `sub_progressivo`, reset `progressivo` a 0  
✅ **Path condiviso**: I sottofascicoli condividono il `path_archivio` del parent  

---

## 🧪 Test Manuale

### Scenario 1: Collegamento Valido

```
Fascicolo Parent: ROSSMRO-01-2025-005 (Mario Rossi, Titolario 01, Anno 2025)
Fascicolo Target: ROSSMRO-01-2025-003 (Mario Rossi, Titolario 01, Anno 2025, parent=None)

✅ RISULTATO: Collegamento riuscito
- ROSSMRO-01-2025-003 diventa sottofascicolo di ROSSMRO-01-2025-005
- progressivo → 0
- sub_progressivo → 1 (o successivo)
```

### Scenario 2: Cliente Diverso

```
Fascicolo Parent: ROSSMRO-01-2025-005 (Mario Rossi)
Fascicolo Target: VERDGIU-01-2025-002 (Giuseppe Verdi)

❌ RISULTATO: Errore
Messaggio: "Impossibile collegare: il cliente del fascicolo VERDGIU-01-2025-002 non coincide."
```

### Scenario 3: Fascicolo Già Collegato

```
Fascicolo Parent: ROSSMRO-01-2025-005
Fascicolo Target: ROSSMRO-01-2025-003 (parent_id = 10)

❌ RISULTATO: Errore
Messaggio: "Il fascicolo ROSSMRO-01-2025-003 è già collegato ad un altro fascicolo."
```

---

## 📊 Query Performance

### Ottimizzazioni Applicate

```python
.filter(cliente=f.cliente, parent__isnull=True)
.exclude(pk=f.pk)
.select_related("titolario_voce")  # JOIN per evitare N+1 query
.order_by("-anno", "-progressivo")
[:20]  # LIMIT 20 per performance
```

**Indexes utilizzati**:
- `cliente_id` (FK index)
- `parent_id` (FK index)
- Composite index: `["cliente", "titolario_voce", "anno", "progressivo"]`

**N+1 Query Evitate**: `select_related("titolario_voce")` carica il titolario in un'unica query JOIN.

---

## 🚀 Deploy

Nessuna migrazione database richiesta (solo modifiche a view e template).

### Checklist Deploy

- [x] Modifiche view (`fascicoli/views.py`)
- [x] Modifiche template (`fascicoli/templates/fascicoli/fascicolo_detail.html`)
- [x] Test sintassi: `python manage.py check fascicoli` ✅
- [x] Test query in shell ✅
- [ ] Test funzionale su staging
- [ ] Deploy su produzione

### Comandi Deploy

```bash
cd /srv/mygest/app
git pull origin main
sudo systemctl restart mygest
# oppure
./scripts/deploy.sh
```

---

## 📚 Riferimenti

- **Model**: `fascicoli/models.py` - Classe `Fascicolo`
- **View**: `fascicoli/views.py` - `FascicoloDetailView`, `fascicolo_collega`
- **Template**: `fascicoli/templates/fascicoli/fascicolo_detail.html`
- **URL**: `/fascicoli/{pk}/` (detail), `/fascicoli/{pk}/collega/` (POST collegamento)
- **Business Rules**: `.github/copilot-instructions.md` - Sezione "Fascicoli"

---

**Data implementazione**: 5 Gennaio 2026  
**Versione**: MyGest 1.0  
**Autore**: GitHub Copilot + Sandro Chimenti
