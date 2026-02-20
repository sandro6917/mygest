# Commit Message Suggerito

```
feat(documenti): Sistema Help Builder user-friendly per tipi documento

Implementato sistema combinato per gestione help_data con:

✨ Funzionalità Principali:
- Auto-generazione sezioni tecniche (attributi, pattern, archiviazione)
- Form Admin user-friendly per sezioni discorsive
- Wizard CLI interattivo per setup completo
- Segnali Django per auto-aggiornamento
- Validazione JSON Schema

📦 Componenti Aggiunti:
- help_builder.py: Generatore automatico sezioni tecniche
- help_forms.py: Form customizzato Django Admin
- configure_help_wizard.py: Management command interattivo
- signals.py: Auto-aggiornamento su modifica attributi
- help_admin.css/js: UI enhancements
- help_data_schema.json: Validazione struttura

🔄 Workflow Auto-Aggiornamento:
- Creazione DocumentiTipo → help_data inizializzato
- Modifica AttributoDefinizione → attributi_dinamici rigenerato
- Salvataggio Admin → sezioni tecniche aggiornate
- Preservazione sezioni discorsive

📝 Sezioni Gestite:
AUTO: attributi_dinamici, pattern_codice, archiviazione, campi_obbligatori
MANUALE: descrizione_breve, quando_usare, workflow, note_speciali, faq

✅ Testato:
- Comando wizard eseguito con successo
- Rebuild technical verificato su tipo CED
- Validazione JSON funzionante
- Compatibilità frontend/export PDF preservata

📚 Documentazione:
- FEATURE_HELP_BUILDER_USER_FRIENDLY.md (800+ righe)
- IMPLEMENTAZIONE_HELP_BUILDER_SUMMARY.md (riepilogo completo)
- QUICK_REFERENCE_HELP_BUILDER.md (guida rapida)

Closes: Issue help_data troppo complesso
Refs: FEATURE_EXPORT_HELP_PDF.md
```

---

# File da Committare

```bash
# Nuovi file
git add documenti/help_builder.py
git add documenti/help_forms.py
git add documenti/management/commands/configure_help_wizard.py
git add static/admin/css/help_admin.css
git add static/admin/js/help_admin.js
git add static/schemas/help_data_schema.json
git add test_help_builder.py
git add FEATURE_HELP_BUILDER_USER_FRIENDLY.md
git add IMPLEMENTAZIONE_HELP_BUILDER_SUMMARY.md
git add QUICK_REFERENCE_HELP_BUILDER.md
git add COMMIT_MESSAGE_HELP_BUILDER.md

# File modificati
git add documenti/admin.py
git add documenti/signals.py

# Commit
git commit -F COMMIT_MESSAGE_HELP_BUILDER.md

# Tag (opzionale)
git tag -a v1.1.0-help-builder -m "Sistema Help Builder user-friendly"
```
