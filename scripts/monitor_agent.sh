#!/bin/bash
# Monitor agent in tempo reale

echo "🔍 Monitoraggio Agent MyGest"
echo "Ctrl+C per terminare"
echo "═══════════════════════════════════════════════════════"
echo ""

tail -f ~/.mygest-agent.log 2>/dev/null || tail -f /home/sandro/mygest/scripts/agent.log
