# Miner Documentation Index

**Last Updated:** 2026-03-24 11:15 UTC

This file indexes all miner documentation to prevent confusion across future sessions.

---

## 🟢 SN36 Miner (Web Agents)

### Authoritative References
1. **SN36_MINER_REFERENCE.md** — START HERE
   - Current production location and configuration
   - All wallet/network details
   - Health check commands
   - Startup procedures

2. **AGENT_PROTOCOLS_SN36.md** — Decision making
   - When to restart / when NOT to restart
   - Mandatory verification checks
   - Emergency procedures
   - Confusion prevention

3. **SN36_CURRENT_STATE.txt** — Status snapshot
   - Frozen state as of 11:13 UTC
   - Quick command reference
   - Absolute rules

4. **SN36_ARCHIVED_VERSIONS/** — Old versions
   - Why `autoppia_web_agents_subnet/` is broken
   - Why HTTP stub was wrong
   - Never use these

### Quick Facts
- **Path:** `~/.openclaw/workspace/bittensor-workspace/autoppia-official/neurons/miner.py`
- **PM2 Process:** `skibbot-miner`
- **UID:** 98
- **Network:** finney (mainnet)
- **Port:** 8091 (Bittensor peer-to-peer)
- **Status:** ✅ RUNNING

---

## 🟢 NOVA Miner (Biomedical)

### Authoritative References
1. **NOVA_MINER_REFERENCE.md** — START HERE
   - Current production location and configuration
   - All wallet/network details
   - Output file monitoring
   - Memory management details

2. **AGENT_PROTOCOLS_NOVA.md** — Decision making
   - When to restart / when NOT to restart
   - Mainnet-specific requirements
   - Memory monitoring procedures
   - Emergency procedures

3. **NOVA_CURRENT_STATE.txt** — Status snapshot
   - Frozen state as of 11:13 UTC
   - Quick command reference
   - Performance metrics
   - Absolute rules

4. **NOVA_ARCHIVED_VERSIONS/** — Old versions
   - Why testnet versions were deprecated
   - Why old commits had memory leaks
   - Never use these

### Quick Facts
- **Path:** `~/.openclaw/workspace/nova_ml_build/neurons/miner.py`
- **PM2 Process:** `nova-mainnet-miner`
- **UID:** 6
- **Network:** mainnet
- **Commit:** e2ffa86
- **Output:** `/output/result.json`
- **Status:** ✅ RUNNING

---

## 📋 Before Any Miner Action

**Always follow this sequence:**

1. **Identify which miner:** SN36 or NOVA?
2. **Read the reference doc:**
   - SN36 → `SN36_MINER_REFERENCE.md`
   - NOVA → `NOVA_MINER_REFERENCE.md`
3. **Read the protocol doc:**
   - SN36 → `AGENT_PROTOCOLS_SN36.md`
   - NOVA → `AGENT_PROTOCOLS_NOVA.md`
4. **Check current status:**
   - SN36: `pm2 list | grep skibbot`
   - NOVA: `pm2 list | grep nova`
5. **Take action only after reading protocols**

---

## 🚨 Golden Rules for Both Miners

1. **SN36 must use `autoppia-official/`** (NOT `autoppia_web_agents_subnet/`)
2. **NOVA must run on `mainnet`** (NOT testnet/finney)
3. **Always read reference docs before restarting**
4. **Validate config matches protocol specs**
5. **Never touch archived versions**
6. **Escalate to Anthony if unsure**

---

## 📊 Health Check Comparison

| Aspect | SN36 | NOVA |
|--------|------|------|
| Process | skibbot-miner | nova-mainnet-miner |
| Status check | `pm2 list \| grep skibbot` | `pm2 list \| grep nova` |
| Output verification | `ss -tlnp \| grep 8091` | `jq . /output/result.json` |
| Memory | 195 MB | 239 MB |
| CPU | 0% idle | 22.7% active |
| Network | Bittensor P2P | JSON file-based |

---

## 🔍 Common Questions Answered

### "Which version of SN36 should I use?"
- ALWAYS use: `autoppia-official/neurons/miner.py`
- NEVER use: `autoppia_web_agents_subnet/`
- Read: `SN36_MINER_REFERENCE.md`

### "Is NOVA running on testnet or mainnet?"
- ALWAYS mainnet (production)
- Network env var: `NETWORK: mainnet`
- Check: `cat ~/.openclaw/workspace/nova-mainnet-ecosystem.config.js | grep NETWORK`
- Read: `NOVA_MINER_REFERENCE.md`

### "What should I do if a miner is down?"
- Read the appropriate protocol doc (SN36 or NOVA)
- Follow the "Decision Tree" section
- DO NOT restart blindly
- Verify config matches reference docs first

### "How do I know which miner needs attention?"
- Run: `pm2 list`
- Both should show ONLINE
- SN36: check `ss -tlnp | grep 8091` (port listening)
- NOVA: check `jq .iteration /output/result.json` (file being updated)

---

## 📝 For Future Sessions

When you start a new session:

1. Read this file (INDEX)
2. Read `MEMORY.md` (top section on miners)
3. Identify which miner needs attention
4. Read that miner's REFERENCE doc
5. Read that miner's PROTOCOL doc
6. Take action only after reading protocols

**Never skip the reading — it only takes 2 minutes and prevents hours of debugging.**

---

## 🔗 Cross-References

**In MEMORY.md:**
- Top section lists both miners with brief status
- Links to reference docs
- Summary of what's locked in

**In ecosystem.config.js files:**
- SN36: `~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js`
- NOVA: `~/.openclaw/workspace/nova-mainnet-ecosystem.config.js`
- These define how miners are started

**In PM2:**
- Run `pm2 list` to see both running
- Run `pm2 show <process-name>` for details
- Run `pm2 logs <process-name>` to view logs

---

**Created:** 2026-03-24 11:15 UTC  
**By:** agent  
**Purpose:** Single authoritative index to prevent future miner confusion

Always refer back to this when in doubt.
