# Agent Protocol for SN36 Miner Management

**Protocol Version:** 1.0  
**Effective:** 2026-03-24  
**Created by:** Anthony Kenny  
**Purpose:** Prevent future miner confusion and restore cycles

---

## GOLDEN RULE

**When you think about SN36 miner — ALWAYS think: `autoppia-official/`**

If you find yourself about to do something with `autoppia_web_agents_subnet/` or any other path, STOP and re-read this file.

---

## The Single Source of Truth

**Location:** `~/.openclaw/workspace/SN36_MINER_REFERENCE.md`

This file contains the AUTHORITATIVE state of:
- Current production miner location
- PM2 process name and configuration
- Wallet details and UID
- Network parameters
- Health check procedures
- Startup/restart commands

**Before taking ANY action on the miner, read this file.**

---

## Decision Tree: What to Do When Asked About SN36

```
User asks about SN36 miner
    ↓
Read SN36_MINER_REFERENCE.md (current state)
    ↓
Run: pm2 list | grep skibbot (verify process)
    ↓
Is skibbot-miner showing ONLINE?
    ├─ YES → Check specifics with:
    │        - pm2 logs skibbot-miner --lines 20 --nostream
    │        - ss -tlnp | grep 8091
    │        └─ Report status back
    │
    └─ NO → BEFORE restarting:
            1. Read SN36_MINER_REFERENCE.md again
            2. Check: What path does PM2 config point to?
            3. Verify: Is it pointing to autoppia-official/?
            4. If not, update PM2 config to autoppia-official
            5. Then restart: pm2 restart skibbot-miner
```

---

## Mandatory Checks Before ANY Restart

**If you ever restart the miner, ALWAYS verify:**

1. ✅ **Read SN36_MINER_REFERENCE.md** — know what you're restarting
2. ✅ **Check PM2 config** — `cat ~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js | grep autoppia`
3. ✅ **It should say:** `autoppia-official/neurons/miner.py` (NOT `autoppia_web_agents_subnet`)
4. ✅ **After restart:** Wait 10 seconds, then run `pm2 list | grep skibbot`
5. ✅ **Verify port:** Run `ss -tlnp | grep 8091` (should show listening)

---

## What NOT to Do (Hard Stops)

❌ **DO NOT:**
- Touch files in `autoppia_web_agents_subnet/` without explicit permission
- Restart anything that's not the `skibbot-miner` process
- Change PM2 process names without updating this protocol
- Create new miner instances without documenting in SN36_MINER_REFERENCE.md
- Use HTTP protocols for SN36 (always Bittensor peer-to-peer)
- Kill processes without checking SN36_MINER_REFERENCE.md first

---

## What to Do If Confused

**If you're ever unsure which miner is correct:**

1. Read this file (AGENT_PROTOCOLS_SN36.md)
2. Read SN36_MINER_REFERENCE.md
3. Run: `pm2 list | grep skibbot` (should show current status)
4. Run: `cat ~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js` (shows config)
5. Look for: `autoppia-official/neurons/miner.py` (confirms correct version)
6. If still unsure: **Message Anthony** with current ps output and PM2 config

---

## Logging & Documentation

**Every time you interact with the miner:**

- If you restart it: Update `memory/YYYY-MM-DD.md` with timestamp and reason
- If something breaks: Log to `memory/active-tasks.md` and notify
- If config changes: Update `SN36_MINER_REFERENCE.md` immediately

---

## Version History

| Date | Change | Status |
|------|--------|--------|
| 2026-03-24 09:20 | Switched from corrupted autoppia_web_agents_subnet to official autoppia-official | ✅ Complete |
| 2026-03-24 10:50 | Health check confirmed running, receiving validator tasks | ✅ Active |
| 2026-03-24 10:57 | Created SN36_MINER_REFERENCE.md and this protocol | ✅ Locked |

---

## Emergency Restart Procedure

**Only do this if the miner is down and you have explicit approval:**

```bash
# 1. Verify you're using the right path
cat ~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js | grep autoppia
# Should output: ... autoppia-official/neurons/miner.py ...

# 2. Restart
pm2 restart skibbot-miner

# 3. Wait 10 seconds
sleep 10

# 4. Verify
pm2 list | grep skibbot
# Should show: ONLINE

# 5. Verify port is listening
ss -tlnp | grep 8091
# Should show: LISTEN 0.0.0.0:8091

# 6. Check logs
pm2 logs skibbot-miner --lines 20 --nostream
```

---

## Archive Reference

**Old versions are stored here (DO NOT USE):**
- `~/.openclaw/workspace/SN36_ARCHIVED_VERSIONS/README.md` — documents why old versions were retired

**If you need to debug an old version:**
1. Copy it to `/tmp/` for analysis
2. NEVER modify or run the original
3. Document findings in a separate analysis file
4. Delete from `/tmp/` when done
5. Return to production miner

---

**Created:** 2026-03-24 10:57 UTC  
**By:** Anthony Kenny  
**For:** Future agent sessions to never get confused about which SN36 miner to use
