# Fix: Bulk Creation - Form Non Inviava i Dati

## 🐛 Problema

Dopo aver selezionato le anagrafiche e cliccato "Crea voci selezionate", **nessuna voce veniva creata** e la pagina tornava semplicemente alla lista senza messaggi di conferma o errore.

## 🔍 Causa

Il form di bulk creation non passava i parametri necessari per far capire a Django Admin che doveva richiamare nuovamente l'action `crea_voci_intestate_bulk` nel secondo POST (quello di creazione).

### Debug Output
```
[DEBUG] request.POST keys: ['csrfmiddlewaretoken', 'action', 'select_across', 'index', '_selected_action']
[DEBUG] 'apply' in request.POST: False
```

Il secondo POST (quando si clicca "Crea voci selezionate") **non conteneva**:
- `action` = nome dell'action da eseguire
- `_selected_action` = ID della voce parent selezionata
- Questi parametri servono a Django Admin per capire che deve richiamare l'action

Risultato: Il POST andava alla changelist standard invece di richiamare `crea_voci_intestate_bulk`.

## ✅ Soluzione

Aggiunti campi hidden al form per mantenere i parametri dell'action attraverso il secondo POST.

### File Modificati

#### 1. Template Form (`templates/admin/titolario/bulk_creation_form.html`)

**Prima**:
```html
<form method="post">
    {% csrf_token %}
    
    <div class="form-row">
```

**Dopo**:
```html
<form method="post" action="">
    {% csrf_token %}
    
    {# Mantieni i parametri della action originale #}
    <input type="hidden" name="action" value="{{ action_name }}">
    {% for obj in queryset %}
    <input type="hidden" name="_selected_action" value="{{ obj.pk }}">
    {% endfor %}
    
    <div class="form-row">
```

#### 2. Admin View (`titolario/admin.py`)

Aggiunto `queryset` e `action_name` al context:

```python
# Rendering template form
context = {
    'title': _('Seleziona anagrafiche per bulk creation'),
    'form': form,
    'voce_parent': voce_parent,
    'anagrafiche_count': anagrafiche_con_codice.count(),
    'opts': self.model._meta,
    'has_view_permission': self.has_view_permission(request),
    'site_title': admin.site.site_title,
    'site_header': admin.site.site_header,
    'queryset': queryset,  # ← AGGIUNTO
    'action_name': 'crea_voci_intestate_bulk',  # ← AGGIUNTO
}
```

## 🎯 Risultato

Ora quando l'utente:
1. Seleziona una voce parent con "Consente intestazione"
2. Sceglie l'action "Crea voci intestate per anagrafiche selezionate"
3. Seleziona le anagrafiche con i checkbox
4. Clicca "Crea voci selezionate"

**Il sistema**:
- ✅ Richiama correttamente `crea_voci_intestate_bulk` con `'apply' in request.POST`
- ✅ Crea le voci intestate per le anagrafiche selezionate
- ✅ Mostra messaggi di feedback (successo, già esistenti, errori)
- ✅ Torna alla lista con conferma

### Debug Output Corretto
Dopo il fix:
```
[DEBUG] === INIZIO crea_voci_intestate_bulk ===
[DEBUG] request.POST keys: [..., 'apply', 'action', '_selected_action', ...]
[DEBUG] 'apply' in request.POST: True
[DEBUG] Form is_valid: True
[DEBUG] Anagrafiche selezionate: 4
[DEBUG] Crea sottovoci: False
```

## 📝 Note Tecniche

### Perché servono questi campi hidden?

Django Admin gestisce le **admin actions** attraverso un meccanismo di POST multipli:

1. **Primo POST** (selezione action):
   - `action` = nome dell'action
   - `_selected_action` = ID(s) degli oggetti selezionati
   - Django chiama il metodo dell'action

2. **Secondo POST** (conferma/invio dati):
   - Se l'action restituisce un form, l'utente lo compila
   - Al submit, **deve ripassare** `action` e `_selected_action`
   - Django richiama la stessa action con i dati del form

Senza questi parametri, Django non sa quale action richiamare e fa un POST normale alla changelist.

### Alternativa: Redirect dopo creazione

Un'alternativa sarebbe fare redirect dopo la creazione invece di tornare alla lista:

```python
from django.shortcuts import redirect

# Dopo creazione voci
return redirect('admin:titolario_titolariovoce_changelist')
```

Ma questo impedisce di mostrare i messaggi di feedback all'utente.

## ✅ Checklist Completamento

- [x] Identificato il problema (mancanza parametri action)
- [x] Aggiunto `queryset` e `action_name` al context
- [x] Aggiornato template con campi hidden
- [x] Rimossi messaggi debug
- [x] Testato funzionamento corretto
- [x] Documentazione creata

---

**Versione**: 1.0  
**Data**: 22 Gennaio 2026  
**Correlato**: FIX_BULK_CREATION_JS_ERRORS.md (fix JavaScript separato)
