#!/bin/bash
# NOVA Miner Health Check Script
# Run this daily to verify your miner is healthy

echo "╔════════════════════════════════════════════════╗"
echo "║     NOVA SN68 Miner Health Check               ║"
echo "║     UID 6 - Blueprint Submission-Based        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. PM2 Status
echo "1️⃣  PM2 Process Status"
echo "─────────────────────────────────────────────────"
pm2_output=$(pm2 list | grep nova-mainnet-miner)
if [ -z "$pm2_output" ]; then
    echo -e "${RED}❌ Miner NOT found in PM2${NC}"
else
    echo "$pm2_output"
    if echo "$pm2_output" | grep -q "online"; then
        echo -e "${GREEN}✅ Status: ONLINE${NC}"
    else
        echo -e "${RED}❌ Status: NOT ONLINE${NC}"
    fi
fi
echo ""

# 2. Process Memory/CPU
echo "2️⃣  Memory & CPU Usage"
echo "─────────────────────────────────────────────────"
proc_output=$(ps aux | grep "miner.py" | grep -v grep)
if [ -z "$proc_output" ]; then
    echo -e "${RED}❌ Process not running${NC}"
else
    memory=$(echo "$proc_output" | awk '{print $6}')
    cpu=$(echo "$proc_output" | awk '{print $3}')
    echo "Memory: ${memory} KB ($(echo "scale=1; $memory / 1024" | bc) MB)"
    echo "CPU: ${cpu}%"
    
    if [ "$memory" -lt 500000 ]; then
        echo -e "${GREEN}✅ Memory usage OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Memory usage high (>500MB)${NC}"
    fi
fi
echo ""

# 3. Output File
echo "3️⃣  Output File (What Validators See)"
echo "─────────────────────────────────────────────────"
if [ ! -f "/output/result.json" ]; then
    echo -e "${RED}❌ File not found: /output/result.json${NC}"
else
    file_info=$(ls -lh /output/result.json)
    echo "$file_info"
    
    # Check file age
    file_time=$(stat -c %Y /output/result.json 2>/dev/null || stat -f %m /output/result.json 2>/dev/null)
    current_time=$(date +%s)
    age_seconds=$((current_time - file_time))
    age_minutes=$((age_seconds / 60))
    
    echo "File age: ${age_minutes} minutes"
    
    if [ "$age_minutes" -lt 5 ]; then
        echo -e "${GREEN}✅ File is fresh (updated recently)${NC}"
    elif [ "$age_minutes" -lt 10 ]; then
        echo -e "${YELLOW}⚠️  File is getting stale (>5 min)${NC}"
    else
        echo -e "${RED}❌ File is STALE (>10 min) - Miner may be hung${NC}"
    fi
fi
echo ""

# 4. Current Iteration
echo "4️⃣  Latest Iteration"
echo "─────────────────────────────────────────────────"
if [ -f "/output/result.json" ]; then
    iteration=$(jq -r '.iteration' /output/result.json 2>/dev/null)
    timestamp=$(jq -r '.timestamp' /output/result.json 2>/dev/null)
    molecules=$(jq -r '.molecules | length' /output/result.json 2>/dev/null)
    
    if [ -n "$iteration" ]; then
        echo "Iteration: $iteration"
        echo "Timestamp: $timestamp"
        echo "Top molecules: $molecules"
        echo -e "${GREEN}✅ Miner is generating valid JSON${NC}"
    else
        echo -e "${RED}❌ Could not parse /output/result.json${NC}"
    fi
fi
echo ""

# 5. Recent Logs
echo "5️⃣  Recent Log Activity (Last 10 lines)"
echo "─────────────────────────────────────────────────"
pm2 logs nova-mainnet-miner --lines 10 --nostream 2>/dev/null | tail -10
echo ""

# 6. Restart Count
echo "6️⃣  Crash Detection"
echo "─────────────────────────────────────────────────"
restart_count=$(pm2 show nova-mainnet-miner 2>/dev/null | grep "↺" | awk '{print $2}')
if [ -z "$restart_count" ]; then
    echo -e "${RED}❌ Could not get restart count${NC}"
else
    echo "Restart count (↺): $restart_count"
    if [ "$restart_count" = "0" ]; then
        echo -e "${GREEN}✅ No crashes detected${NC}"
    else
        echo -e "${YELLOW}⚠️  Miner has restarted $restart_count time(s)${NC}"
    fi
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════╗"
echo "║                    SUMMARY                     ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "Golden Rule: If /output/result.json is updating every"
echo "few seconds and PM2 shows 'online', your miner is healthy."
echo ""
echo "Next steps:"
echo "• Check back in 24 hours"
echo "• Monitor UID 6 on Taostats for Active/Emission changes"
echo "• Validators will pull and score at next cycle"
echo ""
