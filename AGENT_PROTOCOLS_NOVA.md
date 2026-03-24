# Agent Protocol for NOVA SN68 Miner Management

**Protocol Version:** 1.0  
**Effective:** 2026-03-24  
**Created by:** agent  
**Purpose:** Prevent confusion about NOVA miner versions and ensure correct mainnet deployment

---

## GOLDEN RULE

**When you think about NOVA miner — ALWAYS think: `nova_ml_build/neurons/miner.py` on MAINNET**

If you find yourself about to do something with an old testnet version or thinking about changing networks, STOP and re-read this file.

---

## The Single Source of Truth

**Location:** `~/.openclaw/workspace/NOVA_MINER_REFERENCE.md`

This file contains the AUTHORITATIVE state of:
- Current production miner location
- PM2 process name and configuration
- Wallet details and UID
- Network parameters (MAINNET, not testnet)
- Health check procedures
- Startup/restart commands
- Code version and commit hash

**Before taking ANY action on the miner, read this file.**

---

## Decision Tree: What to Do When Asked About NOVA

```
User asks about NOVA miner
    ↓
Read NOVA_MINER_REFERENCE.md (current state)
    ↓
Run: pm2 list | grep nova (verify process)
    ↓
Is nova-mainnet-miner showing ONLINE?
    ├─ YES → Check specifics with:
    │        - pm2 logs nova-mainnet-miner --lines 20 --nostream
    │        - jq .iteration /output/result.json
    │        - ps aux | grep nova_ml_build | grep -v grep
    │        └─ Report status back
    │
    └─ NO → BEFORE restarting:
            1. Read NOVA_MINER_REFERENCE.md again
            2. Check: Is the process dead or just sleeping?
            3. Check: What does PM2 config say for network?
            4. Verify: Should be NETWORK=mainnet (NOT testnet/finney)
            5. Verify: Path should be nova_ml_build/neurons/miner.py
            6. If all correct, restart: pm2 restart nova-mainnet-miner
            7. Wait 10 seconds
            8. Verify: pm2 list | grep nova (should show ONLINE)
```

---

## Mandatory Checks Before ANY Restart

**If you ever restart the miner, ALWAYS verify:**

1. ✅ **Read NOVA_MINER_REFERENCE.md** — know what you're restarting
2. ✅ **Check PM2 config** — `cat ~/.openclaw/workspace/nova-mainnet-ecosystem.config.js | grep -E "NETWORK|script|cwd"`
3. ✅ **It should say:**
   - Script: `./nova_ml_build/neurons/miner.py` (or full path)
   - CWD: `/home/openclaw/.openclaw/workspace`
   - NETWORK: `mainnet` (NOT finney, NOT testnet)
   - SUBNET_UID: `68`
   - MINER_UID: `6`
4. ✅ **After restart:** Wait 10 seconds, then run `pm2 list | grep nova`
5. ✅ **Verify output:** Run `jq .iteration /output/result.json` (should update every 2-3 seconds)
6. ✅ **Check memory:** Run `ps aux | grep nova_ml_build | grep -v grep | awk '{print $6}'` (should be 200-400 MB)

---

## What NOT to Do (Hard Stops)

❌ **DO NOT:**
- Run testnet/finney versions (this is MAINNET only)
- Change NETWORK to anything other than "mainnet"
- Modify /output/result.json path to anything else
- Restart without reading NOVA_MINER_REFERENCE.md first
- Disable garbage collection (it prevents memory leaks)
- Use old commits (e.g., before e2ffa86)
- Change PM2 process name without documenting it
- Kill process without checking NOVA_MINER_REFERENCE.md first

---

## What to Do If Confused

**If you're ever unsure about NOVA:**

1. Read this file (AGENT_PROTOCOLS_NOVA.md)
2. Read NOVA_MINER_REFERENCE.md
3. Run: `pm2 list | grep nova` (should show nova-mainnet-miner)
4. Run: `cat ~/.openclaw/workspace/nova-mainnet-ecosystem.config.js` (shows config)
5. Look for: `NETWORK: mainnet` (confirms correct version)
6. Check: `nova_ml_build/neurons/miner.py` (confirms correct path)
7. If still unsure: **Message Anthony** with current pm2 output and config

---

## Critical Configuration Points

**These MUST match this exactly:**

```
PM2 Process Name: nova-mainnet-miner
Script Path: ./nova_ml_build/neurons/miner.py (relative) OR
            /home/openclaw/.openclaw/workspace/nova_ml_build/neurons/miner.py (absolute)
CWD: /home/openclaw/.openclaw/workspace
NETWORK: mainnet
SUBNET_UID: 68
MINER_UID: 6
TARGET: HDAC6
Output Path: /output/result.json
Max Memory: 4G (4096 MB)
Garbage Collection: Yes (every 50 iterations)
```

**If ANY of these differ, you have the wrong config. Revert immediately.**

---

## Memory Management Protocol

**NOVA has strict memory requirements:**

- **Idle state:** 150-200 MB expected on startup
- **Normal operation:** 200-350 MB after warming up
- **Red flag:** Exceeds 500 MB consistently
- **Emergency stop:** Exceeds 3.5 GB (PM2 will auto-restart)

**Memory cleanup happens at:**
- Every 50 iterations (garbage collection)
- On restart (process resets)

**If memory is high:**
1. Check iteration count: `jq .iteration /output/result.json`
2. Monitor for 30 seconds: `watch -n 1 'ps aux | grep nova_ml_build | awk "{print $6}"'`
3. If stable under 1 GB → normal
4. If still climbing → restart the miner
5. If keeps growing → escalate to Anthony

---

## Logging & Documentation

**Every time you interact with the miner:**

- If you restart it: Update `memory/YYYY-MM-DD.md` with timestamp and reason
- If something breaks: Log to `memory/active-tasks.md` and notify
- If config changes: Update `NOVA_MINER_REFERENCE.md` immediately
- If you suspect a problem: Check logs first before restarting

---

## Version History

| Date | Change | Status |
|------|--------|--------|
| 2026-03-24 09:13 | Restarted after watchdog kill, optimizations applied | ✅ Complete |
| 2026-03-24 11:13 | Health check confirmed running, creating references | ✅ Active |
| 2026-03-24 11:13 | Created NOVA_MINER_REFERENCE.md and this protocol | ✅ Locked |

---

## Emergency Procedures

### If NOVA is Down

```bash
# 1. Verify it's actually down
pm2 list | grep nova
# If status shows "errored" or "stopped", proceed

# 2. Check the config is correct
cat ~/.openclaw/workspace/nova-mainnet-ecosystem.config.js | grep -E "NETWORK|script"
# Must show: NETWORK: mainnet, script: nova_ml_build

# 3. Restart
pm2 restart nova-mainnet-miner

# 4. Wait 30 seconds (initialization takes time)
sleep 30

# 5. Verify it's up
pm2 list | grep nova
# Should show: ONLINE

# 6. Verify output is being written
jq .iteration /output/result.json
# Should show a number that updates every 2-3 seconds

# 7. Check memory
ps aux | grep nova_ml_build | grep -v grep | awk '{print $6 " KB"}'
# Should be under 500 MB
```

### If Output File Is Missing

```bash
# 1. Check if /output exists
ls -la /output/

# 2. If missing, create it
sudo mkdir -p /output && sudo chmod 777 /output

# 3. Restart miner
pm2 restart nova-mainnet-miner

# 4. Wait 10 seconds
sleep 10

# 5. Verify file created
ls -lh /output/result.json
# Should exist and be recently modified
```

### If Memory Is Climbing

```bash
# 1. Check current usage
ps aux | grep nova_ml_build | grep -v grep | awk '{print $6}'

# 2. Monitor for 60 seconds
watch -n 5 'ps aux | grep nova_ml_build | grep -v grep | awk "{print $6 \" KB\"}"'

# 3. If stable → normal (wait for GC at 50-iteration marks)
# 4. If climbing → restart
pm2 restart nova-mainnet-miner

# 5. Check again after 60 seconds
ps aux | grep nova_ml_build | grep -v grep | awk '{print $6}'
# Should be under 500 MB
```

---

## Archive Reference

**Old versions are stored here (DO NOT USE):**
- `~/.openclaw/workspace/NOVA_ARCHIVED_VERSIONS/` — contains deprecated versions

**If you need to debug an old version:**
1. Copy to `/tmp/` for analysis ONLY
2. NEVER modify or run the original
3. Document findings in separate file
4. Delete from `/tmp/` when done
5. Return to production miner immediately

---

## When to Contact Anthony

Escalate immediately if:
- ❌ Memory exceeds 1 GB consistently
- ❌ Output file stops being updated for >10 seconds
- ❌ Process crashes 3+ times in an hour
- ❌ You find an error you can't diagnose
- ❌ Something in the config doesn't match this protocol
- ❌ You're unsure about whether to restart

---

**Created:** 2026-03-24 11:13 UTC  
**By:** agent  
**For:** Future agent sessions to confidently manage NOVA miner without confusion
