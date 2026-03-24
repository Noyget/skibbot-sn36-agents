# NOVA SN68 MINER — AUTHORITATIVE REFERENCE (2026-03-24)

## ⭐ CURRENT PRODUCTION MINER (ACTIVE & EARNING-READY)

### Location
```
~/.openclaw/workspace/nova_ml_build/neurons/miner.py
```

### Process Details
- **PM2 Config:** `~/.openclaw/workspace/nova-mainnet-ecosystem.config.js`
- **PM2 Process Name:** `nova-mainnet-miner`
- **PID:** 3391163 (as of 2026-03-24 11:13 UTC)
- **Uptime:** 2+ hours (continuously running)
- **Memory:** 239 MB (stable, well below 4GB limit)
- **CPU:** 22.7% (active scoring)
- **Status:** ✅ ONLINE

### Network & Wallet
- **Network:** mainnet (Bittensor primary network)
- **Subnet:** 68 (Biomedical / Molecular Scout)
- **UID:** 6
- **Coldkey:** `biomedical_research`
- **Hotkey:** `miner`
- **Wallet Name:** `biomedical_research`
- **Hotkey Name:** `miner`
- **Registration Status:** ✅ ACTIVE (configured in PM2)

### Code Version
- **Repository:** https://github.com/Noyget/nova-molecular-scout
- **Commit:** e2ffa86
- **Algorithm:** Infinite molecular sampling with ML guidance
- **Target:** HDAC6 (protein target for molecular docking)
- **Molecules/Iteration:** 500 sampled → 100 valid → 10 deduplicated
- **Iteration Pace:** ~0.5 iterations/second (one every ~2 seconds)

### Output File (Blueprint-Compatible)
- **Path:** `/output/result.json`
- **Update Frequency:** Every 2-3 seconds
- **Content:** JSON with molecules, scores, descriptors
- **Size:** 6.0 KB
- **Validators Read This:** Yes, during validation cycles
- **Status:** ✅ Actively being written

### Memory Management
- **Current Usage:** 239 MB
- **Max Limit:** 4 GB (PM2 restart if exceeded)
- **Garbage Collection:** Every 50 iterations
- **Memory Trend:** ✅ STABLE (no creep)
- **Last GC:** Iteration 5570 (working as designed)

### Iteration Performance
- **Molecules Scored:** 500 per iteration
- **Valid Molecules:** 100 per iteration (Lipinski Rule of 5)
- **Top Molecules Kept:** 10 deduplicated
- **Time per Iteration:** 0.25-0.50 seconds
- **Status:** ✅ Consistent and efficient

### Recent Activity
- **Latest Iteration:** 5579 (as of 11:13 UTC)
- **Error Rate:** 0 (last 30 iterations all success)
- **Status:** ✅ Running smoothly
- **Output:** Being generated continuously

### Startup Command (If Needed)
```bash
cd ~/.openclaw/workspace
pm2 start nova-mainnet-ecosystem.config.js
pm2 save
```

### Health Check
```bash
pm2 list | grep nova
# Should show: nova-mainnet-miner ... online
```

### View Logs (Real-Time)
```bash
pm2 logs nova-mainnet-miner --lines 30 --nostream
```

### Logs Location
- Out: `~/.pm2/logs/nova-mainnet-miner-out-0.log` (current)
- Out (old): `~/.pm2/logs/nova-mainnet-miner-out.log` (from earlier restarts)
- Error: `~/.pm2/logs/nova-mainnet-miner-error-0.log` (current)
- Error (old): `~/.pm2/logs/nova-mainnet-miner-error.log` (from earlier restarts)

### Monitor Iterations (Live)
```bash
watch -n 2 'jq .iteration /output/result.json'
# Updates every 2 seconds showing current iteration count
```

### Check Output Quality
```bash
jq '.molecules[0]' /output/result.json
# See what validators will score
```

### Memory Usage Check
```bash
ps aux | grep nova_ml_build | grep -v grep | awk '{print $6 " KB (" int($6/1024) " MB)"}'
```

### Registration Verification (On-Chain)
```python
from bittensor import subtensor
sub = subtensor('mainnet')
mg = sub.metagraph(68)
if 6 in mg.uids:
    idx = list(mg.uids).index(6)
    print(f"✅ UID 6 ACTIVE")
    print(f"  Hotkey: {mg.hotkeys[idx]}")
    print(f"  Stake: {mg.stake[idx]}")
```

---

## ⚠️ OLD / STALE VERSIONS (DO NOT USE)

**Archive Directory:** `~/.openclaw/workspace/NOVA_ARCHIVED_VERSIONS/`

### Version 1: Finney Testnet Miner (DEPRECATED)
- **Path:** (was in nova_ml_build but old code)
- **Status:** ❌ REPLACED
- **Reason:** Testnet version, moved to mainnet
- **Lesson:** Always verify NETWORK and NETWORK_TESTNET flags

### Version 2: Earlier Commits (OUTDATED)
- **Status:** ❌ SUPERSEDED by commit e2ffa86
- **Last Used:** Various dates
- **Reason:** Had memory leaks, no GC, inefficient I/O

---

## 🎯 FOR AGENT (FUTURE SELF)

### When you read this in a future session:

1. **This IS the correct miner:**
   - Path: `~/.openclaw/workspace/nova_ml_build/neurons/miner.py`
   - Commit: e2ffa86
   - PM2 name: `nova-mainnet-miner`
   - UID: 6
   - Network: mainnet (NOT testnet/finney)

2. **DO NOT:**
   - Restart anything for old/testnet versions
   - Change the network from mainnet
   - Modify the output path from `/output/result.json`
   - Disable garbage collection
   - Stop monitoring memory

3. **DO:**
   - Monitor `nova-mainnet-miner` process (pm2 list)
   - Check logs in `~/.pm2/logs/nova-mainnet-miner-out-0.log`
   - Verify `/output/result.json` is being updated
   - Watch memory stays under 500 MB normally
   - Use this reference when in doubt

4. **If you're unsure:**
   - Run: `pm2 list | grep nova`
   - Check: `cat ~/.openclaw/workspace/nova-mainnet-ecosystem.config.js | grep NETWORK`
   - Verify: Network should say "mainnet"
   - Verify: Path should say `nova_ml_build/neurons/miner.py`
   - Read this file again

---

## Timeline of Changes

### 2026-03-24 09:13 UTC
- ✅ Miner restarted after watchdog killed it
- ✅ Optimizations applied: GC, history trimming, error handling
- ✅ Running continuously since

### 2026-03-24 11:13 UTC
- ✅ Health check: Process healthy, 2 hours uptime, 5579 iterations
- ✅ Output file verified being updated
- ✅ Memory stable at 239 MB
- ✅ Created this reference document

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Check status | `pm2 list \| grep nova` |
| View logs | `pm2 logs nova-mainnet-miner --lines 20 --nostream` |
| Check output | `jq . /output/result.json` |
| Monitor iterations | `watch -n 2 'jq .iteration /output/result.json'` |
| Get memory | `ps aux \| grep nova_ml_build \| grep -v grep \| awk '{print $6 " KB"}'` |
| Restart (if needed) | `pm2 restart nova-mainnet-miner` |
| Stop (emergency) | `pm2 stop nova-mainnet-miner` |
| Start (if stopped) | `cd ~/.openclaw/workspace && pm2 start nova-mainnet-ecosystem.config.js` |

---

**Last Updated:** 2026-03-24 11:13 UTC by agent
**Status:** ✅ CURRENT & AUTHORITATIVE
**Confidence:** HIGH — Process running, output verified, memory stable
