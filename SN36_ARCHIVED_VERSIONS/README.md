# SN36 Archived Versions — Reference Only

**⚠️ DO NOT USE THESE. They are kept for reference/debugging only.**

## Version 1: autoppia_web_agents_subnet/ (BROKEN)

**Status:** ❌ ARCHIVED (corrupted virtualenv, outdated dependencies)
**Path:** `~/.openclaw/workspace/bittensor-workspace/autoppia_web_agents_subnet/`
**Why broken:** 
- Had conflicting virtualenv at `miner_env/`
- Outdated autoppia fork with missing synapse definitions
- Validators couldn't properly communicate

**Last used:** 2026-03-23 16:34 UTC (then crashed)

**Recovered logs show:**
- Received one StartRound from validator (UID 55)
- Then process exited due to venv corruption
- Should NOT be restarted

---

## Version 2: HTTP FastAPI Stub (WRONG PROTOCOL)

**Status:** ❌ REMOVED (incompatible with Bittensor)
**Issue:** Was running HTTP server instead of Bittensor peer-to-peer
**Port:** 8091 (but HTTP, not Bittensor)
**Why wrong:** Validators use Bittensor's native synapse protocol, not HTTP

**Lesson learned:** Always verify network protocol requirements before deployment

---

## Current Production Version ✅

See: `~/.openclaw/workspace/SN36_MINER_REFERENCE.md`

Path: `~/.openclaw/workspace/bittensor-workspace/autoppia-official/neurons/miner.py`
PM2: `skibbot-miner`
Status: ✅ RUNNING

---

**If you need to debug an old version:**
- Copy it to a separate test directory first
- NEVER modify or restart from this archive
- Document your findings in a separate analysis file
- Then return to the production miner

---

Generated: 2026-03-24 10:57 UTC
