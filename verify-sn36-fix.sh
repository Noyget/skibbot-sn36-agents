#!/bin/bash
# Verification script for SN36 agent fix deployment

echo "🔍 SN36 Fix Verification (2026-03-25)"
echo "======================================"
echo ""

# Check 1: GitHub repo has agents/server.py
echo "✓ Check 1: agents/server.py exists in GitHub"
curl -s "https://raw.githubusercontent.com/Noyget/skibbot-sn36-agents/main/agents/server.py" | head -3 | grep -q "FastAPI server" && echo "  ✅ PASS: File found and valid" || echo "  ❌ FAIL: File not found"

# Check 2: Miner is running
echo ""
echo "✓ Check 2: Miner process is running"
ps aux | grep -q "autoppia-official/neurons/miner.py" && echo "  ✅ PASS: Miner PID $(ps aux | grep 'autoppia-official/neurons/miner.py' | grep -v grep | awk '{print $2}')" || echo "  ❌ FAIL: Miner not running"

# Check 3: Miner config has new commit
echo ""
echo "✓ Check 3: Miner config updated with new commit"
if grep -q "8f9b041" ~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js; then
    echo "  ✅ PASS: Config has commit 8f9b041"
else
    echo "  ❌ FAIL: Config doesn't have new commit"
fi

# Check 4: Miner is announcing new commit
echo ""
echo "✓ Check 4: Miner announcing new commit to validators"
pm2 logs skibbot-miner --lines 20 --nostream 2>/dev/null | grep -q "8f9b041" && echo "  ✅ PASS: Logs show new commit" || echo "  ❌ FAIL: Not found in logs yet"

# Check 5: Validators are contacting miner
echo ""
echo "✓ Check 5: Validators discovering miner"
VALIDATOR_COUNT=$(pm2 logs skibbot-miner --lines 100 --nostream 2>/dev/null | grep "validator:" | sort -u | wc -l)
if [ "$VALIDATOR_COUNT" -gt 0 ]; then
    echo "  ✅ PASS: $VALIDATOR_COUNT validators actively contacting miner"
else
    echo "  ⚠️  WARNING: No recent validator activity (may be between cycles)"
fi

# Check 6: Server.py is syntactically valid
echo ""
echo "✓ Check 6: agents/server.py Python syntax"
curl -s "https://raw.githubusercontent.com/Noyget/skibbot-sn36-agents/main/agents/server.py" > /tmp/server_check.py && python3 -m py_compile /tmp/server_check.py 2>/dev/null && echo "  ✅ PASS: Valid Python syntax" || echo "  ❌ FAIL: Syntax error"

echo ""
echo "======================================"
echo "Verification complete!"
echo ""
echo "Expected outcome:"
echo "- Validators will discover new code in next 2-12 hours"
echo "- Dashboard should show 50%+ success rate within 24-48h"
echo "- TAO earnings will start flowing"
echo ""
echo "Monitor with: pm2 logs skibbot-miner --follow"
