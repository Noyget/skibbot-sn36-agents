# NOVA Archived Versions — Reference Only

**⚠️ DO NOT USE THESE. They are kept for reference/debugging only.**

## Version 1: Finney Testnet Miner (DEPRECATED)

**Status:** ❌ ARCHIVED (testnet version, we moved to mainnet)
**Location:** Various early builds
**Network:** finney (testnet - WRONG for production)
**Why deprecated:** Testnet was used for development. Production moved to mainnet.

**Lesson learned:** Always verify NETWORK environment variable. Production must be "mainnet", not "finney".

---

## Version 2: Early Commits Before e2ffa86 (OUTDATED)

**Status:** ❌ SUPERSEDED
**Known Issues:**
- No garbage collection → memory leaks after ~50 minutes
- Massive history file (5-10 MB) slowed iterations
- No error handling for I/O failures
- Memory would hit system limits

**Improvements in e2ffa86:**
- ✅ GC every 50 iterations
- ✅ Efficient history tracking
- ✅ Robust error handling
- ✅ Lightweight JSON output

**Never go back to old commits.**

---

## Current Production Version ✅

See: `~/.openclaw/workspace/NOVA_MINER_REFERENCE.md`

Path: `~/.openclaw/workspace/nova_ml_build/neurons/miner.py`
Commit: e2ffa86
Network: mainnet (UID 6, Subnet 68)
PM2: `nova-mainnet-miner`
Status: ✅ RUNNING

---

**If you need to debug an old version:**
- Copy it to a separate test directory first
- NEVER modify or restart from this archive
- Document your findings in a separate analysis file
- Then return to the production miner

---

Generated: 2026-03-24 11:13 UTC
