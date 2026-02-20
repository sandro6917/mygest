#!/bin/bash
# Test sistema protezione path MyGest Agent
# ==========================================

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Test Sistema Protezione Path - MyGest Agent           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server e token
SERVER="http://localhost:8000"
TOKEN="aa35a2945ce816d87c5c714732312274f0b6c116"

echo -e "${BLUE}1. Test path PROTETTI (devono essere bloccati)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROTECTED_PATHS=(
    "/mnt/archivio/documenti/test.pdf"
    "/home/sandro/mygest/manage.py"
    "/etc/passwd"
    "/usr/bin/python"
)

for path in "${PROTECTED_PATHS[@]}"; do
    echo -ne "Testing: ${path}..."
    
    response=$(curl -s -X POST "$SERVER/api/v1/agent/request-deletion/" \
        -H "Authorization: Token $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"documento\": 999999, \"source_path\": \"$path\"}")
    
    if echo "$response" | grep -q "Path protetto"; then
        echo -e " ${GREEN}✅ BLOCCATO${NC}"
    else
        echo -e " ${RED}❌ NON BLOCCATO (ERRORE!)${NC}"
    fi
done

echo ""
echo -e "${BLUE}2. Test path WINDOWS validi (devono essere accettati)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

VALID_PATHS=(
    "/mnt/c/Users/Sandro/Desktop/test.pdf"
    "/mnt/c/temp/documento.pdf"
    "/mnt/d/Downloads/file.pdf"
    "/tmp/test_mygest.txt"
)

for path in "${VALID_PATHS[@]}"; do
    echo -ne "Testing: ${path}..."
    
    response=$(curl -s -X POST "$SERVER/api/v1/agent/request-deletion/" \
        -H "Authorization: Token $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"documento\": 999999, \"source_path\": \"$path\"}")
    
    if echo "$response" | grep -q "Path protetto"; then
        echo -e " ${RED}❌ BLOCCATO (NON DOVREBBE!)${NC}"
    elif echo "$response" | grep -q "non esiste"; then
        echo -e " ${GREEN}✅ ACCETTATO${NC} (errore doc non esiste OK)"
    else
        echo -e " ${YELLOW}⚠️  RISPOSTA INATTESA${NC}"
        echo "$response" | jq -r '.error // .message // empty' | head -1
    fi
done

echo ""
echo -e "${BLUE}3. Verifica mount Windows in WSL${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "/mnt/c" ]; then
    echo -e "${GREEN}✅${NC} Drive C: montato su /mnt/c"
else
    echo -e "${RED}❌${NC} Drive C: NON montato"
fi

if [ -d "/mnt/archivio" ]; then
    echo -e "${GREEN}✅${NC} Archivio montato su /mnt/archivio"
else
    echo -e "${YELLOW}⚠️${NC}  Archivio NON montato"
fi

echo ""
echo -e "${BLUE}4. Test agent locale (Python)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /home/sandro/mygest/scripts
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/sandro/mygest')

from mygest_agent import MyGestAgent

agent = MyGestAgent('http://localhost:8000', 'test_token', 30)

test_cases = [
    ("/mnt/c/Users/Test/file.pdf", False),          # Windows OK
    ("/mnt/archivio/doc.pdf", True),                 # Protetto
    ("/home/sandro/mygest/manage.py", True),         # Protetto
    ("/tmp/test.pdf", False),                        # OK
]

all_ok = True
for path, should_be_protected in test_cases:
    is_protected = agent.is_protected_path(path)
    if is_protected == should_be_protected:
        print(f"✅ {path}")
    else:
        print(f"❌ {path} (atteso: {'protetto' if should_be_protected else 'OK'})")
        all_ok = False

if all_ok:
    print("\n✅ Tutti i test agent Python passati!")
else:
    print("\n❌ Alcuni test falliti")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Test Completati                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
