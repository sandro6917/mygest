#!/bin/bash

# Script per controllare lo stato dei workflow GitHub Actions

set -e

echo "=========================================="
echo "🔍 VERIFICA STATO WORKFLOW GITHUB ACTIONS"
echo "=========================================="
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# URL del repository
REPO_URL="https://github.com/sandro6917/mygest"
ACTIONS_URL="${REPO_URL}/actions"

echo -e "${BLUE}📦 Repository:${NC} ${REPO_URL}"
echo -e "${BLUE}🎯 Actions:${NC} ${ACTIONS_URL}"
echo ""

# Verifica ultimo commit
echo -e "${YELLOW}📝 Ultimo commit:${NC}"
git log -1 --oneline
echo ""

# Verifica branch
echo -e "${YELLOW}🌿 Branch corrente:${NC}"
git branch --show-current
echo ""

# Verifica se ci sono commit da pushare
UNPUSHED=$(git log origin/main..HEAD --oneline | wc -l)
if [ "$UNPUSHED" -gt 0 ]; then
    echo -e "${RED}⚠️  Hai $UNPUSHED commit da pushare!${NC}"
    git log origin/main..HEAD --oneline
    echo ""
else
    echo -e "${GREEN}✅ Tutto sincronizzato con GitHub${NC}"
    echo ""
fi

# Lista workflow disponibili
echo -e "${YELLOW}📋 Workflow disponibili:${NC}"
ls -1 .github/workflows/
echo ""

# Istruzioni
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}📖 ISTRUZIONI:${NC}"
echo ""
echo "1. Vai su: ${ACTIONS_URL}"
echo ""
echo "2. Esegui manualmente il workflow 'Test SSH Connection':"
echo "   - Clicca su 'Test SSH Connection'"
echo "   - Clicca su 'Run workflow' > 'Run workflow'"
echo "   - Attendi che completi (dovrebbe essere verde ✅)"
echo ""
echo "3. Verifica il workflow 'Deploy to Production':"
echo "   - Dovrebbe essere già partito automaticamente dopo il push"
echo "   - Se verde ✅ = deploy OK!"
echo "   - Se rosso ❌ = controlla i log per errori"
echo ""
echo "4. Per vedere lo stato in tempo reale:"
echo "   ${ACTIONS_URL}/workflows/deploy-production.yml"
echo ""
echo -e "${GREEN}✅ Setup completato! Controlla GitHub Actions.${NC}"
echo ""
