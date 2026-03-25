# Miner Stability Fixes — 2026-03-25 05:12 UTC

## Problem Identified

**Both miners stopped running and fell out of PM2 management on 2026-03-25 between 03:21-03:27 UTC.**

### Root Cause Analysis

**Timeline:**
1. **03:21:50** — SN36 miner became unkillable (SIGTERM failed 15+ times)
2. **03:21:52** — PM2 forced SIGKILL, then auto-restarted
3. **03:21:59 → 03:22:10** — Process got stuck again, multiple restart cycles
4. **03:27:30** — PM2 daemon itself crashed from repeated restart stress
5. **03:27 → 05:07** — 1.5 hour period with NO PM2 daemon running
6. **05:07:07** — PM2 daemon restarted but processes were orphaned
7. **05:08-05:10** — Manual restart required to get miners back

**Why PM2 crashed:**
- SN36 miner became unkillable (stuck in kernel wait/I/O)
- PM2 hung trying to stop it
- Daemon eventually ran out of resources and crashed
- When daemon restarted 90 minutes later, it lost all process context

**Why miners weren't auto-recovered:**
- No PM2 systemd service
- No cron job to monitor PM2 health
- Miners kept running in background but orphaned from PM2 management
- No autorestart triggers because PM2 didn't know about them

---

## Solutions Implemented (2026-03-25 05:12 UTC)

### 1. ✅ Shorter Kill Timeout
**File:** `ecosystem.config.js` and `nova-mainnet-ecosystem.config.js`

Added:
```javascript
kill_timeout: 5000,        // Force SIGKILL after 5 seconds if SIGTERM hangs
listen_timeout: 10000,     // Allow 10s for process to start
```

**Effect:** If a miner gets stuck and won't respond to SIGTERM, PM2 will force-kill it within 5 seconds instead of hanging indefinitely.

### 2. ✅ PM2 Health Monitor Cron Job
**Location:** `/tmp/pm2-watchdog.sh` (runs every 5 minutes via crontab)

**What it does:**
- Checks if PM2 daemon is running
- If daemon crashed, automatically restarts it with `pm2 resurrect`
- Logs all activity to `~/.openclaw/logs/pm2-watchdog.log`
- Prevents orphaned processes

**Cron entry:**
```
*/5 * * * * /tmp/pm2-watchdog.sh
```

**Effect:** If PM2 crashes again, it will be auto-recovered within 5 minutes.

### 3. ⏳ (Optional) Add PM2 Startup on Boot
If the machine reboots, PM2 will auto-start via the saved dump:
```bash
pm2 save              # Already done
pm2 startup          # Optional: creates system init scripts
```

---

## Testing the Fixes

**Verify kill_timeout is active:**
```bash
cd ~/.openclaw/workspace/bittensor-workspace && pm2 show skibbot-miner | grep -i timeout
```

**Check PM2 watchdog:**
```bash
tail -20 ~/.openclaw/logs/pm2-watchdog.log
```

**Verify both miners are running:**
```bash
pm2 list
```

---

## What Would Happen Now if Miner Freezes

**Before fix:** Process hung → PM2 hung → Daemon crashed → Miners orphaned → 90 min+ downtime
**After fix:**
1. Process stuck → PM2 sends SIGTERM
2. SIGTERM ignored for 5s → PM2 sends SIGKILL
3. Hard kill succeeds → `autorestart: true` triggers new process
4. Miner reboots within 10s
5. **Total downtime: ~10 seconds instead of 90 minutes**

---

## Remaining Risk: Why Did Miner Freeze?

The miner code itself seems to have a hang/deadlock issue. The fixes above **mitigate the impact** but don't eliminate the root cause.

**Likely causes (in miner code):**
1. Bittensor connection/subnet handshake deadlock
2. Wallet interaction frozen
3. Network socket stuck
4. System call blocking indefinitely

**Next diagnostics needed:**
- Add timeout wrappers around Bittensor operations
- Add health check heartbeat (miner writes timestamp every 30s)
- Monitor system call behavior (strace)
- Check for resource exhaustion (file descriptors, threads)

---

## Files Modified (2026-03-25)

- ✅ `~/.openclaw/workspace/bittensor-workspace/ecosystem.config.js` — Added kill_timeout & listen_timeout
- ✅ `~/.openclaw/workspace/nova-mainnet-ecosystem.config.js` — Added kill_timeout & listen_timeout
- ✅ `/tmp/pm2-watchdog.sh` — New cron-based PM2 health monitor
- ✅ `crontab` — Added `*/5 * * * * /tmp/pm2-watchdog.sh` entry

---

## Rollback Plan (If Issues Arise)

```bash
# Remove PM2 watchdog
crontab -l | grep -v pm2-watchdog | crontab -

# Revert to old kill timeout (remove the lines we added)
# Edit ecosystem.config.js and nova-mainnet-ecosystem.config.js
# Remove: kill_timeout, listen_timeout

# Reload
pm2 reload ecosystem.config.js
pm2 reload nova-mainnet-ecosystem.config.js
```

---

## Status (2026-03-25 05:12 UTC)

- ✅ Both miners reloaded with new settings
- ✅ Both online and running
- ✅ PM2 watchdog installed
- ✅ Changes saved to PM2 persist layer
- ✅ Ready for 24/7 operation

**Expected outcome:** No more 90-minute outages from PM2 daemon crashes.
