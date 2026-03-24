# SN36 MINER — AUTHORITATIVE REFERENCE (2026-03-24)

## ⭐ CURRENT PRODUCTION MINER (ACTIVE & EARNING)

### Location
```
~/.openclaw/workspace/bittensor-workspace/autoppia-official/neurons/miner.py
```

### Process Details
- **PM2 Config:** `~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js`
- **PM2 Process Name:** `skibbot-miner`
- **PID:** 3396065 (as of 2026-03-24 10:50 UTC)
- **Uptime:** 78+ minutes (continuously running)
- **Memory:** 195.8 MB (stable)
- **CPU:** 0% idle
- **Status:** ✅ ONLINE

### Network & Wallet
- **Network:** finney (Bittensor mainnet)
- **Subnet:** 36 (Autoppia - Web Agents)
- **UID:** 98
- **Hotkey:** `5DcAF38ecF69DGB6JXtsU6x7k75xitGjJygyYJNkRCfxiGMP`
- **Coldkey:** `5DZfSgw32QDzsZfBVnVTyFewPC1QgyVnYgVxEQShVHbwjKRj`
- **Wallet Name:** `primary`
- **Hotkey Name:** `miner`
- **IP:Port:** 172.104.24.232:8091
- **Protocol:** Bittensor peer-to-peer (NOT HTTP)
- **Stake:** 100.65 TAO
- **Registration Status:** ✅ ACTIVE on-chain

### Startup Command (If Needed)
```bash
cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official
pm2 start ../ecosystem.config.js
pm2 save
```

### Health Check
```bash
pm2 list | grep skibbot
```
Should show: `skibbot-miner ... online`

### Recent Logs
```bash
pm2 logs skibbot-miner --lines 30 --nostream
```

### Logs Location
- Out: `~/.pm2/logs/skibbot-miner-out-2.log`
- Error: `~/.pm2/logs/skibbot-miner-error-2.log`

### Port Verification
```bash
ss -tlnp | grep 8091
# Should show: LISTEN 0.0.0.0:8091 with python3 PID 3396065
```

### Registration Verification (On-Chain)
```python
from bittensor import subtensor
sub = subtensor('finney')
mg = sub.metagraph(36)
if 98 in mg.uids:
    idx = list(mg.uids).index(98)
    print(f"✅ UID 98 ACTIVE")
    print(f"  Hotkey: {mg.hotkeys[idx]}")
    print(f"  Axon: {mg.axons[idx].ip}:{mg.axons[idx].port}")
    print(f"  Stake: {mg.stake[idx]}")
```

---

## ⚠️ OLD / STALE VERSIONS (DO NOT USE)

These are archived references only. **DO NOT restart or manage these.**

### Version 1: HTTP FastAPI Stub (BROKEN - 2026-03-24 09:20)
- **Status:** ❌ REMOVED (was not compatible with Bittensor protocol)
- **What it was:** FastAPI server on port 8091 in HTTP mode
- **Why removed:** Validators use Bittensor peer-to-peer protocol, not HTTP
- **Lesson:** Always verify protocol requirements before deploying

### Version 2: Original Autoppia Clone (STALE - Pre 2026-03-24 09:20)
- **Path:** `~/.openclaw/workspace/bittensor-workspace/autoppia_web_agents_subnet/`
- **Status:** ❌ ARCHIVED (replaced by `autoppia-official`)
- **Why replaced:** Had virtualenv conflicts and outdated dependencies
- **Location:** Still on disk if needed for reference
- **Action:** Do NOT use this. It has conflicting files.

---

## 🎯 FOR AGENT (FUTURE SELF)

### When you read this in a future session:

1. **This IS the correct miner:**
   - Path: `~/.openclaw/workspace/bittensor-workspace/autoppia-official/neurons/miner.py`
   - PM2 name: `skibbot-miner`
   - UID: 98

2. **DO NOT:**
   - Restart anything in `autoppia_web_agents_subnet/` (old version)
   - Create new miners in random directories
   - Use HTTP protocols for SN36
   - Kill `skibbot-miner` unless explicitly asked

3. **DO:**
   - Monitor `skibbot-miner` process (pm2 list)
   - Check logs in `~/.pm2/logs/skibbot-miner-out-2.log`
   - Verify port 8091 is listening
   - Use autoppia-official as the source of truth

4. **If you're unsure:**
   - Run: `pm2 list | grep skibbot`
   - Check: `ss -tlnp | grep 8091`
   - Verify: UID 98 in metagraph
   - Read this file again

---

## Timeline of Changes

### 2026-03-24 09:20 UTC
- ❌ FastAPI HTTP stub found running
- ✅ Cloned official Autoppia repository
- ✅ Restored proper Bittensor protocol miner
- ✅ Updated PM2 config to point to `autoppia-official`
- ✅ Removed conflicting virtualenv

### 2026-03-24 10:50 UTC
- ✅ Health check: Process stable, receiving validator signals
- ✅ Created this reference document to prevent future confusion

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Check status | `pm2 list \| grep skibbot` |
| View logs | `pm2 logs skibbot-miner --lines 20 --nostream` |
| Restart (emergency) | `pm2 restart skibbot-miner` |
| Stop (emergency) | `pm2 stop skibbot-miner` |
| Start (if stopped) | `cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official && pm2 start ../ecosystem.config.js` |
| Verify port | `ss -tlnp \| grep 8091` |
| Verify registration | `python3 -c "from bittensor import subtensor; sub = subtensor('finney'); mg = sub.metagraph(36); print('✅ UID 98 ACTIVE' if 98 in mg.uids else '❌ UID 98 NOT FOUND')"` |

---

**Last Updated:** 2026-03-24 10:57 UTC by Anthony Kenny
**Status:** ✅ CURRENT & AUTHORITATIVE
