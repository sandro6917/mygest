#!/bin/bash
# Test Scanner Service Installation

echo "=================================="
echo "  Test Scanner Service - MyGest"
echo "=================================="
echo ""

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Test dipendenze Python
echo "1. Verifica dipendenze Python..."
python3 -c "import flask; print('✓ Flask')" 2>/dev/null || echo -e "${RED}✗ Flask non installato${NC}"
python3 -c "import flask_cors; print('✓ Flask-CORS')" 2>/dev/null || echo -e "${RED}✗ Flask-CORS non installato${NC}"
python3 -c "import PIL; print('✓ Pillow')" 2>/dev/null || echo -e "${RED}✗ Pillow non installato${NC}"
python3 -c "import pikepdf; print('✓ pikepdf')" 2>/dev/null || echo -e "${RED}✗ pikepdf non installato${NC}"
python3 -c "import img2pdf; print('✓ img2pdf')" 2>/dev/null || echo -e "${RED}✗ img2pdf non installato${NC}"
python3 -c "import sane; print('✓ python-sane')" 2>/dev/null || echo -e "${YELLOW}⚠ python-sane non installato (modalità mock)${NC}"

echo ""

# 2. Test SANE
echo "2. Verifica SANE..."
if command -v scanimage &> /dev/null; then
    echo -e "${GREEN}✓ SANE installato${NC}"
    echo "Scanner disponibili:"
    scanimage -L 2>/dev/null || echo -e "${YELLOW}⚠ Nessuno scanner trovato${NC}"
else
    echo -e "${RED}✗ SANE non installato${NC}"
    echo "  Installa con: sudo apt install sane sane-utils libsane-dev"
fi

echo ""

# 3. Test servizio
echo "3. Verifica servizio scanner..."
if pgrep -f "scanner_service.py" > /dev/null; then
    echo -e "${GREEN}✓ Servizio scanner in esecuzione${NC}"
    PID=$(pgrep -f "scanner_service.py")
    echo "  PID: $PID"
else
    echo -e "${YELLOW}⚠ Servizio scanner non in esecuzione${NC}"
    echo "  Avvia con: python scripts/scanner_service.py"
fi

echo ""

# 4. Test endpoint
echo "4. Test API endpoints..."
if curl -s http://localhost:8765/health &> /dev/null; then
    echo -e "${GREEN}✓ API raggiungibile${NC}"
    RESPONSE=$(curl -s http://localhost:8765/health)
    echo "  $RESPONSE"
else
    echo -e "${RED}✗ API non raggiungibile${NC}"
    echo "  Verifica che il servizio sia avviato"
fi

echo ""

# 5. Test directory temporanea
echo "5. Verifica directory temporanea..."
TEMP_DIR="/tmp/mygest_scanner"
if [ -d "$TEMP_DIR" ]; then
    echo -e "${GREEN}✓ Directory temporanea esistente${NC}"
    echo "  Path: $TEMP_DIR"
    FILE_COUNT=$(find "$TEMP_DIR" -type f 2>/dev/null | wc -l)
    echo "  File presenti: $FILE_COUNT"
else
    echo -e "${YELLOW}⚠ Directory temporanea non esistente${NC}"
    echo "  Verrà creata automaticamente al primo avvio"
fi

echo ""

# 6. Suggerimenti
echo "=================================="
echo "  Suggerimenti"
echo "=================================="
echo ""

if ! pgrep -f "scanner_service.py" > /dev/null; then
    echo "Per avviare il servizio scanner:"
    echo "  cd /home/sandro/mygest"
    echo "  source venv/bin/activate"
    echo "  python scripts/scanner_service.py"
    echo ""
    echo "Oppure usa lo script Windows:"
    echo "  windows_manager/Quick_Start_Scanner.bat"
fi

if ! command -v scanimage &> /dev/null; then
    echo ""
    echo "Per installare SANE:"
    echo "  sudo apt update"
    echo "  sudo apt install sane sane-utils libsane-dev"
fi

echo ""
echo "Per maggiori informazioni, consulta:"
echo "  FEATURE_SCANNER_INTEGRATION.md"
echo ""
