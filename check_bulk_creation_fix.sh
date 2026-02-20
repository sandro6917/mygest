#!/bin/bash
# Quick check per verificare che il fix sia stato applicato

echo "========================================"
echo "CHECK FIX BULK CREATION"
echo "========================================"
echo ""

# 1. Verifica file sorgente
echo "1️⃣  File sorgente (static/admin/js/titolario_auto_fill.js):"
if grep -q "isBulkCreationPage" static/admin/js/titolario_auto_fill.js; then
    echo "   ✅ Fix presente"
    echo "   Righe chiave:"
    grep -n "isBulkCreationPage" static/admin/js/titolario_auto_fill.js | head -2
else
    echo "   ❌ Fix NON presente"
fi
echo ""

# 2. Verifica file in staticfiles
echo "2️⃣  File compilato (staticfiles/admin/js/titolario_auto_fill.js):"
if [ -f staticfiles/admin/js/titolario_auto_fill.js ]; then
    if grep -q "isBulkCreationPage" staticfiles/admin/js/titolario_auto_fill.js; then
        echo "   ✅ Fix presente in staticfiles"
        echo "   Ultima modifica:"
        ls -lh staticfiles/admin/js/titolario_auto_fill.js | awk '{print "   ", $6, $7, $8}'
    else
        echo "   ❌ Fix NON presente in staticfiles"
        echo "   ⚠️  ESEGUI: python manage.py collectstatic --noinput"
    fi
else
    echo "   ❌ File non trovato in staticfiles"
    echo "   ⚠️  ESEGUI: python manage.py collectstatic --noinput"
fi
echo ""

# 3. Verifica chiamate duplicate
echo "3️⃣  Check chiamate duplicate waitForJQuery():"
count=$(grep -c "waitForJQuery();" static/admin/js/titolario_auto_fill.js)
if [ "$count" -eq 1 ]; then
    echo "   ✅ Nessuna duplicazione (1 chiamata)"
else
    echo "   ⚠️  Trovate $count chiamate (dovrebbe essere 1)"
fi
echo ""

# 4. Template bulk creation
echo "4️⃣  Template bulk creation:"
if [ -f templates/admin/titolario/bulk_creation_form.html ]; then
    echo "   ✅ Template presente"
    if grep -q "form.anagrafiche" templates/admin/titolario/bulk_creation_form.html; then
        echo "   ✅ Campo 'anagrafiche' (plurale) trovato"
    fi
else
    echo "   ❌ Template non trovato"
fi
echo ""

echo "========================================"
echo "ISTRUZIONI PER L'UTENTE"
echo "========================================"
echo ""
echo "Per testare nel browser:"
echo "  1. Svuota cache browser (Ctrl+Shift+Delete)"
echo "  2. Oppure Hard Refresh (Ctrl+Shift+R)"
echo "  3. Oppure apri in Modalità Incognito (Ctrl+Shift+N)"
echo ""
echo "Console browser dovrebbe mostrare:"
echo "  [TitolarioAutoFill] Pagina bulk creation rilevata, skip inizializzazione"
echo ""
echo "Se vedi ancora errori alle righe 33, 26, 43, 52:"
echo "  → Stai usando la vecchia versione in cache!"
echo "  → Svuota COMPLETAMENTE la cache del browser"
echo ""
