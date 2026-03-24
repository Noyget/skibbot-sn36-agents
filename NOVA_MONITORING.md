# NOVA SN68 Miner Monitoring Guide

## Quick Status (Run anytime)

```bash
pm2 list | grep nova-mainnet
```
Shows: Running? Uptime? Restart count?

---

## Daily Health Check

```bash
echo "=== PM2 Status ===" && pm2 list | grep nova-mainnet-miner && \
echo "" && echo "=== Process Memory/CPU ===" && ps aux | grep "miner.py" | grep -v grep && \
echo "" && echo "=== Output File (validators see this) ===" && ls -lh /output/result.json && \
echo "" && echo "=== File Age ===" && stat /output/result.json | grep Modify && \
echo "" && echo "=== Recent Iterations ===" && pm2 logs nova-mainnet-miner --lines 15 --nostream
```

**What to look for:**
- Status: `online`
- Memory: <500MB (normal)
- Output file: Exists, recently updated (within last 2 minutes)
- Logs: Continuous iterations flowing

---

## What Changed (Blueprint vs Traditional)

### ❌ OLD (Traditional P2P)
- Miners would receive validator requests (synapses)
- You'd see "StartRound", "ReceiveTask" in logs
- Validators actively querying your miner

### ✅ NEW (Blueprint Submission-Based)
- Validators pull your CODE from MinIO automatically
- They RUN your miner in a Docker sandbox
- They read `/output/result.json` from the sandbox
- **You won't see validator interactions in your logs**
- Your job: Keep miner running 24/7, keep generating valid molecules

---

## Critical Monitoring Points

### 1. **Output File Updates** (Most important)
```bash
watch -n 5 'ls -lh /output/result.json && echo "---" && tail -5 /output/result.json | jq -r ".iteration, .timestamp"'
```
✅ Should see: Timestamp updating every 1-2 seconds, iteration incrementing constantly

❌ If file is stale (>5 minutes old): Miner crashed or hung

### 2. **Process Health**
```bash
pm2 show nova-mainnet-miner
```
✅ Look for:
- Status: `online`
- Restart count (↺): Should be 0 or 1 (expected from our code update)
- Memory: Stable, not growing over time

❌ If restart count keeps increasing: Miner crashing repeatedly (investigate logs)

### 3. **Memory Leaks** (Our fix prevents this)
```bash
watch -n 60 'ps aux | grep miner.py | grep -v grep | awk "{print \$6 \" MB memory\"}"'
```
✅ Should stay around 150-300 MB
❌ If creeping up to >500MB: Memory leak (shouldn't happen with our garbage collection fix)

### 4. **Log Health**
```bash
pm2 logs nova-mainnet-miner --lines 100 --nostream | tail -50
```
✅ Look for:
- Regular iteration messages
- Timestamps progressing
- No error messages

❌ Red flags:
- "Memory error", "JSON error", "disk full"
- Gaps in timestamps (means process hung)
- Same iteration repeated multiple times

---

## Emergency Diagnostics

### Miner crashed and won't restart?

```bash
# 1. Check error log
tail -50 ~/.pm2/logs/nova-mainnet-miner-error.log

# 2. Try manual start
cd /home/openclaw/.openclaw/workspace/nova_ml_build
python3 neurons/miner.py --target HDAC6

# 3. Check if /output directory writable
ls -la /output/
touch /output/test.txt && rm /output/test.txt

# 4. Check Python/dependencies
python3 -c "from agents.molecular_scout_ml import MolecularScoutML; print('OK')"
```

### Output file stuck/stale?

```bash
# 1. Check if process is running
ps aux | grep miner.py | grep -v grep

# 2. Check if it's hung (not outputting)
tail -f /output/result.json | head -1  # Should see output within 2 seconds

# 3. Force restart
pm2 restart nova-mainnet-miner
```

### Validators not scoring yet?

Check Taostats:
```bash
# Visit: https://taostats.io/subnets/68/metagraph
# Look for UID 6 — check Active, Incentive, Emission columns
# If still 0, validators haven't run yet (wait for next cycle)
```

---

## Monitoring Schedule

**Recommended:**
- **Daily:** Run health check (copy the full command above)
- **Weekly:** Check Taostats for Active/Emission status changes
- **On demand:** If you suspect a problem

**Automated monitoring (optional):**
```bash
# Add to crontab for daily 9 AM check
0 9 * * * /home/openclaw/.openclaw/workspace/nova-health-check.sh
```

---

## Key Metrics to Track

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Uptime | 24h+ | >1 restart/day | Crashes every hour |
| Memory | 150-300 MB | 300-500 MB | >500 MB |
| Output age | <2 min old | 2-5 min old | >5 min old |
| Iterations/min | ~60/min | 30-60/min | <30/min |
| Active status | 0 until first score | - | - |
| Emission | 0 until first epoch | 0+ after scoring | Decreasing = problem |

---

## What Happens Next

1. **Now:** Miner running, generating molecules, writing to `/output/result.json`
2. **Next 24h:** Validator cycle triggers (automatic)
3. **Validators pull:** Your code from MinIO, run in Docker
4. **They score:** Your molecules, post results
5. **Emissions flow:** Your UID 6 gets Active=1, Emission=TAO amount
6. **Repeat:** Every epoch/cycle, you earn more TAO

**Status to expect:**
- Days 1-2: Active=0, Emission=0 (validators discovering)
- Day 2-3: Active=1, Emission=small amount (first scoring)
- Day 3+: Emission growing (multiple validator scores)

---

**Golden Rule:** If `/output/result.json` is updating every few seconds and the process is `online`, you're good. Everything else is ancillary.
