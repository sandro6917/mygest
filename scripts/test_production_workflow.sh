#!/bin/bash
################################################################################
# Test Simulazione Produzione
################################################################################
# Questo script simula il workflow di deploy produzione per verificare che
# settings_local.py funzioni correttamente.
#
# USO: ./scripts/test_production_workflow.sh
################################################################################

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Test Workflow Produzione ===${NC}\n"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Test 1: Verifica che settings_local.py.example esista
echo -e "${BLUE}[1/6]${NC} Verifica template settings_local.py.example..."
if [[ -f "mygest/settings_local.py.example" ]]; then
    echo -e "${GREEN}✓${NC} Template trovato"
else
    echo "✗ Template non trovato!"
    exit 1
fi

# Test 2: Verifica che settings_local.py NON sia su git
echo -e "${BLUE}[2/6]${NC} Verifica che settings_local.py sia in .gitignore..."
if grep -q "mygest/settings_local.py" .gitignore; then
    echo -e "${GREEN}✓${NC} settings_local.py in .gitignore"
else
    echo "✗ settings_local.py NON è in .gitignore!"
    exit 1
fi

# Test 3: Verifica che settings.py importi settings_local
echo -e "${BLUE}[3/6]${NC} Verifica import in settings.py..."
if grep -q "from .settings_local import" mygest/settings.py; then
    echo -e "${GREEN}✓${NC} Import settings_local presente in settings.py"
else
    echo "✗ Import settings_local NON trovato in settings.py!"
    exit 1
fi

# Test 4: Simula deploy (rimuovi settings_local.py temporaneamente)
echo -e "${BLUE}[4/6]${NC} Simula deploy (senza settings_local.py)..."
if [[ -f "mygest/settings_local.py" ]]; then
    mv mygest/settings_local.py mygest/settings_local.py.backup
    echo -e "${YELLOW}⚠${NC} settings_local.py rimosso temporaneamente"
fi

# Verifica che Django funzioni anche senza settings_local.py
if venv/bin/python manage.py check 2>&1 | grep -q "⚠ settings_local.py non trovato"; then
    echo -e "${GREEN}✓${NC} Django funziona con fallback a default"
else
    echo "✗ Django non gestisce correttamente la mancanza di settings_local.py"
    [[ -f "mygest/settings_local.py.backup" ]] && mv mygest/settings_local.py.backup mygest/settings_local.py
    exit 1
fi

# Test 5: Ripristina settings_local.py (simula creazione post-deploy)
echo -e "${BLUE}[5/6]${NC} Simula creazione settings_local.py post-deploy..."
if [[ -f "mygest/settings_local.py.backup" ]]; then
    mv mygest/settings_local.py.backup mygest/settings_local.py
    echo -e "${GREEN}✓${NC} settings_local.py ripristinato"
fi

# Test 6: Verifica caricamento settings_local.py
echo -e "${BLUE}[6/6]${NC} Verifica caricamento settings_local.py..."
if venv/bin/python manage.py check 2>&1 | grep -q "✓ Settings locali caricati"; then
    echo -e "${GREEN}✓${NC} Settings locali caricati correttamente"
else
    echo "✗ Settings locali NON caricati!"
    exit 1
fi

# Riepilogo
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Test Workflow Produzione COMPLETATO${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Scenario testato:"
echo "  1. Template presente su git ✓"
echo "  2. settings_local.py NON su git ✓"
echo "  3. Import in settings.py funzionante ✓"
echo "  4. Deploy senza settings_local.py (fallback OK) ✓"
echo "  5. Creazione post-deploy settings_local.py ✓"
echo "  6. Caricamento settings_local.py ✓"
echo ""
echo "Workflow produzione verificato con successo!"
