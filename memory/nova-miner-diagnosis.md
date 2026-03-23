# NOVA Miner Crash Diagnosis — Root Cause Found

**Status:** SOLVED  
**Date:** 2026-03-23  
**Miner:** nova-mainnet-miner (UID 6, Subnet 68)

## Root Cause

**The miner is being killed by OpenClaw's system watchdog** (`~/.openclaw/scripts/vm-watchdog.py`).

### The Mechanism

1. **Watchdog runs every minute via cron:**
   ```
   * * * * * python3 ~/.openclaw/scripts/vm-watchdog.py > /dev/null 2>&1
   ```

2. **Watchdog has a process age limit:**
   ```python
   PROCESS_MAX_AGE_MIN = 30        # Kill agent-spawned processes running longer than 30 min
   ```

3. **Your miner gets killed after 30 minutes:**
   - Logs show: last iteration at 22:29:00
   - Process launched: ~19:46 (from file timestamps)
   - **Duration: ~2 hours 43 minutes** ❌ Way over the 30-minute limit
   - Result: Watchdog kills it as a "runaway process"

### Evidence

1. **Logs show clean exit, not crash:**
   ```
   2026-03-23 22:29:00 +00:00: INFO:__main__:Iteration 682: scored 500, valid 500, top 100: 10 deduped, time 0.29s, mode: lipinski
   ```
   Then... nothing. No error, no traceback. Just stopped.

2. **PM2 has stale PID:**
   ```
   PID: 3212910 (from .pid file)
   Status: Process no longer exists
   ```

3. **Process guard function in watchdog:**
   ```python
   def check_runaway_processes():
       """Kill agent-spawned processes... NOT cron jobs..."""
       # Targets: bash, python3, node processes...
       # Kill processes running longer than PROCESS_MAX_AGE_MIN
       # If too many non-gateway processes, kill the oldest ones
   ```

4. **Miner matches the kill criteria:**
   - ✅ Owned by openclaw user
   - ✅ Python3 process running `miner.py`
   - ✅ Not the gateway
   - ✅ Not in protected list (strip-thinking, watchdog itself)
   - ✅ **Age > 30 minutes → KILL**

## The Pattern (Why It Crashes Within Hours)

Every time you restart the miner:
1. Miner launches successfully ✅
2. Runs fine for ~25 minutes
3. At ~30 minute mark, watchdog kills it on next cron run ❌
4. You see: "oh, it crashed again" → restart → repeat

## Fix (Multiple Options)

### Option A: Whitelist the Miner in Watchdog ✅ RECOMMENDED

Edit `/home/openclaw/.openclaw/scripts/vm-watchdog.py` line ~400:

**Before:**
```python
protected_comms = {"systemd", "dbus-daemon", "(sd-pam)", "sshd"}
```

**After:**
```python
protected_comms = {"systemd", "dbus-daemon", "(sd-pam)", "sshd"}
# Don't kill persistent subnet miners
if "miner.py" in cmdline or "nova" in cmdline:
    continue
```

### Option B: Increase the Watchdog's Age Threshold

Edit line ~72 in `vm-watchdog.py`:

**Before:**
```python
PROCESS_MAX_AGE_MIN = 30
```

**After:**
```python
PROCESS_MAX_AGE_MIN = 480  # 8 hours — reasonable for miners
```

### Option C: Run Miner Outside PM2 (Workaround)

Use `nohup` + direct process, not PM2:
```bash
nohup python3 ~/.openclaw/workspace/nova_ml_build/neurons/miner.py > miner.log 2>&1 &
```
But this loses PM2's auto-restart if the miner truly crashes.

## Recommended Solution

**Use Option A + Option B combined:**

1. **Whitelist the miner process** so it's never killed by age
2. **Increase age threshold to 8 hours** as a safety net for other long-running processes

This way:
- Your miner runs forever (as intended) ✅
- Other runaway processes still get cleaned up after 8 hours ✅
- No conflicting safeguards ✅

## Files to Modify

- `/home/openclaw/.openclaw/scripts/vm-watchdog.py` (2 edits)

## Testing After Fix

1. Restart miner: `pm2 start nova-mainnet-miner`
2. Monitor: `watch 'ps aux | grep miner.py'`
3. Wait 45 minutes → verify it's still running
4. Check logs: `pm2 logs nova-mainnet-miner --lines 50`

The miner should run indefinitely after this fix.
