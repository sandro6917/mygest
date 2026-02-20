#!/bin/bash
# Script di verifica post-implementazione UI/UX
# Data: 17 Novembre 2025

echo "🔍 Verifica Implementazione UI/UX MyGest"
echo "=========================================="
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contatori
total=0
passed=0
failed=0

# Funzione di test
check_file() {
    total=$((total + 1))
    if [ -f "$1" ]; then
        size=$(du -h "$1" | cut -f1)
        echo -e "${GREEN}✓${NC} $1 ${YELLOW}($size)${NC}"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗${NC} $1 ${RED}MANCANTE!${NC}"
        failed=$((failed + 1))
    fi
}

echo "📁 Verifica File CSS..."
check_file "static/css/theme.css"
check_file "static/css/components.css"
check_file "static/css/form-enhancements.css"
check_file "static/css/app.css"
check_file "static/css/layout.css"

echo ""
echo "📁 Verifica File JavaScript..."
check_file "static/js/theme-manager.js"
check_file "static/js/toast.js"
check_file "static/js/form-enhancements.js"

echo ""
echo "📁 Verifica Template..."
check_file "templates/base.html"
check_file "templates/ui_demo.html"

echo ""
echo "📁 Verifica Documentazione..."
check_file "docs/PROPOSTA_MIGLIORAMENTO_UI_UX.md"
check_file "docs/GUIDA_NUOVE_FUNZIONALITA_UI.md"
check_file "docs/RIEPILOGO_IMPLEMENTAZIONE_UI.md"
check_file "docs/GUIDA_UTENTE_NUOVA_UI.md"
check_file "docs/INDICE_DOCUMENTAZIONE_UI.md"

echo ""
echo "📁 Verifica File Root..."
check_file "CHANGELOG.md"
check_file "QUICK_START_UI.md"

echo ""
echo "=========================================="
echo -e "Risultati: ${GREEN}$passed passati${NC}, ${RED}$failed falliti${NC} su $total"
echo ""

# Verifica server Django
echo "🌐 Verifica Server Django..."
if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Server Django attivo su http://127.0.0.1:8000/"
else
    echo -e "${RED}✗${NC} Server Django non risponde"
fi

echo ""
echo "📊 Dimensioni Bundle..."
css_size=$(du -ch static/css/*.css 2>/dev/null | grep total | cut -f1)
js_size=$(du -ch static/js/*.js 2>/dev/null | grep total | cut -f1)
docs_size=$(du -ch docs/*UI*.md 2>/dev/null | grep total | cut -f1)

echo "   CSS:  $css_size"
echo "   JS:   $js_size"
echo "   Docs: $docs_size"

echo ""
echo "✨ Test Funzionalità JavaScript (apri browser console)..."
echo "   - Apri http://127.0.0.1:8000/"
echo "   - Premi F12 per aprire Developer Tools"
echo "   - Nella Console digita: getTheme()"
echo "   - Dovrebbe ritornare: 'light' o 'dark'"
echo ""
echo "   Test Toast:"
echo "   - Console: toast.success('Test!')"
echo "   - Dovrebbe apparire notifica in alto a destra"
echo ""

echo "🎯 Prossimi Step:"
echo "   1. Apri http://127.0.0.1:8000/ nel browser"
echo "   2. Clicca l'icona sole/luna per testare dark mode"
echo "   3. Apri F12 Console e testa: toast.success('Funziona!')"
echo "   4. Naviga su una pagina con form per testare validazione"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 Tutti i file sono presenti! Implementazione completata con successo.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Alcuni file mancano. Controlla l'implementazione.${NC}"
    exit 1
fi
