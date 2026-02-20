#!/bin/bash
# Riepilogo Mount Windows/WSL per MyGest Agent
# =============================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          Mount Windows/WSL - MyGest Agent                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Drive Windows Montati${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Funzione per formattare size
format_size() {
    numfmt --to=iec-i --suffix=B $1 2>/dev/null || echo "$1"
}

# Check drive C:
if [ -d "/mnt/c" ]; then
    SIZE=$(df -B1 /mnt/c 2>/dev/null | tail -1 | awk '{print $2}')
    USED=$(df -B1 /mnt/c 2>/dev/null | tail -1 | awk '{print $3}')
    AVAIL=$(df -B1 /mnt/c 2>/dev/null | tail -1 | awk '{print $4}')
    PERCENT=$(df /mnt/c 2>/dev/null | tail -1 | awk '{print $5}')
    
    echo -e "${GREEN}✅ C:${NC} /mnt/c"
    echo "   Size: $(format_size $SIZE) | Used: $(format_size $USED) | Available: $(format_size $AVAIL) ($PERCENT)"
else
    echo -e "${RED}❌ C:${NC} /mnt/c (non montato)"
fi

# Check drive D:
if [ -d "/mnt/d" ] && df /mnt/d 2>/dev/null | grep -q "/mnt/d"; then
    SIZE=$(df -B1 /mnt/d 2>/dev/null | tail -1 | awk '{print $2}')
    USED=$(df -B1 /mnt/d 2>/dev/null | tail -1 | awk '{print $3}')
    AVAIL=$(df -B1 /mnt/d 2>/dev/null | tail -1 | awk '{print $4}')
    PERCENT=$(df /mnt/d 2>/dev/null | tail -1 | awk '{print $5}')
    
    echo -e "${GREEN}✅ D:${NC} /mnt/d"
    echo "   Size: $(format_size $SIZE) | Used: $(format_size $USED) | Available: $(format_size $AVAIL) ($PERCENT)"
else
    echo -e "${YELLOW}⚠️  D:${NC} /mnt/d (non montato o non disponibile)"
fi

# Check drive G: (Google Drive)
if [ -d "/mnt/g" ] && df /mnt/g 2>/dev/null | grep -q "/mnt/g"; then
    SIZE=$(df -B1 /mnt/g 2>/dev/null | tail -1 | awk '{print $2}')
    USED=$(df -B1 /mnt/g 2>/dev/null | tail -1 | awk '{print $3}')
    AVAIL=$(df -B1 /mnt/g 2>/dev/null | tail -1 | awk '{print $4}')
    PERCENT=$(df /mnt/g 2>/dev/null | tail -1 | awk '{print $5}')
    
    echo -e "${GREEN}✅ G:${NC} /mnt/g ${CYAN}(Google Drive)${NC}"
    echo "   Size: $(format_size $SIZE) | Used: $(format_size $USED) | Available: $(format_size $AVAIL) ($PERCENT)"
    
    # Mostra contenuto principale
    COUNT=$(ls -1 "/mnt/g/Il mio Drive/" 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        echo "   📁 Elementi in 'Il mio Drive': $COUNT"
    fi
else
    echo -e "${YELLOW}⚠️  G:${NC} /mnt/g (non montato)"
    echo "   Per montare: sudo mount -t drvfs 'G:' /mnt/g"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Mount di Rete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Check archivio NAS
if [ -d "/mnt/archivio" ] && df /mnt/archivio 2>/dev/null | grep -q "/mnt/archivio"; then
    SOURCE=$(df /mnt/archivio 2>/dev/null | tail -1 | awk '{print $1}')
    SIZE=$(df -B1 /mnt/archivio 2>/dev/null | tail -1 | awk '{print $2}')
    USED=$(df -B1 /mnt/archivio 2>/dev/null | tail -1 | awk '{print $3}')
    AVAIL=$(df -B1 /mnt/archivio 2>/dev/null | tail -1 | awk '{print $4}')
    PERCENT=$(df /mnt/archivio 2>/dev/null | tail -1 | awk '{print $5}')
    
    echo -e "${GREEN}✅ Archivio${NC} /mnt/archivio"
    echo "   Source: $SOURCE"
    echo "   Size: $(format_size $SIZE) | Used: $(format_size $USED) | Available: $(format_size $AVAIL) ($PERCENT)"
    echo -e "   ${RED}🛡️  PROTETTO${NC} - L'agent NON eliminerà file da qui"
else
    echo -e "${RED}❌ Archivio${NC} /mnt/archivio (non montato)"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Configurazione /etc/fstab${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

if [ -f "/etc/fstab" ]; then
    # Mount configurati
    MOUNTS=$(grep -v "^#" /etc/fstab | grep -v "^$" | wc -l)
    echo -e "Mount configurati: ${GREEN}$MOUNTS${NC}"
    echo ""
    
    # Mostra configurazioni (escludi commenti e righe vuote)
    grep -v "^#" /etc/fstab | grep -v "^$" | while read line; do
        MOUNT_POINT=$(echo "$line" | awk '{print $2}')
        TYPE=$(echo "$line" | awk '{print $3}')
        echo "  • $MOUNT_POINT ($TYPE)"
    done
else
    echo -e "${YELLOW}⚠️  /etc/fstab non configurato${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Path Utilizzabili nel Form MyGest${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Drive C:
if [ -d "/mnt/c" ]; then
    echo -e "${GREEN}C:\\Desktop${NC}"
    echo "  Windows: C:\\Users\\Sandro\\Desktop\\file.pdf"
    echo "  Nel form: /mnt/c/Users/Sandro/Desktop/file.pdf"
    echo ""
fi

# Drive G:
if [ -d "/mnt/g" ]; then
    echo -e "${GREEN}G:\\Google Drive${NC}"
    echo "  Windows: G:\\Il mio Drive\\documenti\\file.pdf"
    echo "  Nel form: /mnt/g/Il mio Drive/documenti/file.pdf"
    echo ""
fi

echo -e "${YELLOW}⚠️  NOTA:${NC} Non usare path in /mnt/archivio (protetto)"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Test Rapido${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Test scrittura su G:
if [ -d "/mnt/g" ]; then
    TEST_FILE="/mnt/g/Il mio Drive/.test_mygest_$(date +%s)"
    if echo "test" > "$TEST_FILE" 2>/dev/null; then
        rm -f "$TEST_FILE" 2>/dev/null
        echo -e "${GREEN}✅${NC} Scrittura su G: (Google Drive): OK"
    else
        echo -e "${RED}❌${NC} Scrittura su G: (Google Drive): FALLITA"
    fi
fi

# Test lettura C:
if [ -r "/mnt/c/Windows/System32/drivers/etc/hosts" ]; then
    echo -e "${GREEN}✅${NC} Lettura su C:: OK"
else
    echo -e "${RED}❌${NC} Lettura su C:: FALLITA"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo "Eseguito: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
