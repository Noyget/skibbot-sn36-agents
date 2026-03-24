# SN36 Agent Recovery Plan — From 0 TAO to Earning

**Document:** Strategic Recovery Plan  
**Status:** Ready to Execute  
**Prepared by:** agent  
**For:** Anthony Kenny  
**Date:** 2026-03-24 21:40 UTC

---

## Executive Summary

Your SN36 miner is **deployed and receiving validator tasks correctly**. You're earning 0 TAO not because of deployment issues, but because agents score **below the 1.0 threshold** on the IWA benchmark.

**The Challenge:** Validators have a binary reward system — eval_score must be >= 1.0 to earn **any** TAO. Below 1.0 = 0.0 reward.

**The Opportunity:** You're close. Probably scoring 0.3-0.7 on average. To hit 1.0+, need to fix specific failure modes in your agents.

**Timeline to Recovery:** 6-12 hours of work, then 24-48h to next validator cycle.

---

## Part 1: Understand the Scoring System

### Binary Reward Function

```python
# This is what validators use (autoppia_web_agents_subnet/validator/evaluation/rewards.py)

def calculate_reward_for_task(eval_score, execution_time, token_cost):
    # BINARY THRESHOLD
    if eval_score < 1.0:
        return 0.0  # NOT partial credit, NOT 0.5, but ZERO
    
    # Only if eval_score >= 1.0:
    time_penalty = execution_time / 900_seconds
    cost_penalty = token_cost / $50
    reward = 1.0 + (1.0 - time_penalty) * 0.3 + (1.0 - cost_penalty) * 0.2
    return min(reward, 1.2)  # Capped at 1.2
```

**What This Means:**
- eval_score 0.99 → Reward 0.0 TAO
- eval_score 1.0 → Reward 0.8-1.2 TAO (depending on speed/cost)
- eval_score 1.5+ → Same as 1.0 (capped at 1.2)

### Where eval_score Comes From

```python
# From stateful_cua_eval.py, the IWA evaluator scores each task

# Evaluator initializes task environment
step_result = await evaluator.reset()  # Loads page, captures initial state

# Loop: Agent acts, evaluator measures progress
while not task_complete:
    actions = await agent.act(task, snapshot_html, screenshot)
    step_result = await evaluator.step(actions[0])
    final_score = step_result.score  # Updated after each action

# Return the raw score
score = final_score.raw_score  # This becomes eval_score (0.0-1.0)
return score, elapsed_time, solution
```

**The evaluator measures:**
1. Goal achieved? (100% completion needed for high score)
2. Progress made? (partial progress gives 0.2-0.9)
3. No progress? (0.0)

---

## Part 2: Why You're Below 1.0

### The Three Most Likely Failure Modes

#### Failure Mode 1: FormNavigator - Dynamic Elements

**The Problem:**
```javascript
// Website has form fields rendered by JavaScript
// HTML shows: <input id="email" />
// But the field isn't actually interactive yet (still loading)
```

**Your Agent Does This:**
```python
# Agent sees selector in HTML snapshot
actions = agent.act(...)
# Returns: [{"type": "type", "selector": "#email", "text": "user@example.com"}]

# Validator executes action
# But field isn't interactive, click/type does nothing or times out
```

**Result:** Action fails, no progress → eval_score 0.2-0.4 → 0 TAO

**The Fix:**
```python
# FormNavigator needs to wait for element readiness BEFORE sending action

async def interact_with_form_field(field_selector, action):
    element = await page.query_selector(field_selector)
    
    # Wait for it to be interactive
    await element.wait_for_element_state("visible")
    await element.wait_for_element_state("enabled")
    await page.wait_for_load_state("networkidle")  # JS finished
    
    # NOW it's safe
    if action == "type":
        await element.type(text)
    elif action == "click":
        await element.click()
```

#### Failure Mode 2: Screenshot ↔ HTML State Mismatch

**The Problem:**
```
Step 1: Validator gets HTML snapshot (captures form fields)
Step 2: Agent acts (sends action)
Step 3: Evaluator executes action (page changes)
Step 4: New page state = modal dialog opens
Step 5: Validator sends NEW screenshot (shows modal)
But sends OLD HTML (doesn't show modal!)
Step 6: Agent confused: "HTML says click X, but screenshot shows modal covering X"
Step 7: Agent makes wrong decision → action fails
```

**Result:** Agent confused, makes bad decisions → eval_score drops → 0 TAO

**The Fix:**
```python
# After each evaluator.step(), get fresh snapshot
step_result = await evaluator.step(action)

# Refresh HTML to match new screenshot
fresh_snapshot = step_result.snapshot
fresh_html = sanitize_snapshot_html(fresh_snapshot.html, uid)

# Next iteration uses matching HTML + screenshot
actions = await agent.act(
    task=task,
    snapshot_html=fresh_html,  # Fresh, not stale!
    screenshot=fresh_snapshot.screenshot_after,
)
```

#### Failure Mode 3: Race Conditions

**The Problem:**
```
Button exists in HTML but isn't ready to click yet
Agent: "I see 'Add to Cart' button, will click"
Validator: Tries to click
Page: "Not ready, click queued but ignored"
Result: No state change, agent stuck in loop
```

**Result:** Multiple failed actions, timeout, eval_score 0.0-0.3 → 0 TAO

**The Fix:** (Same as Failure Mode 1 — wait for readiness)

---

## Part 3: How to Diagnose Your Specific Issues

### Step 1: Run Local Evaluation

```bash
cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official

# Run against 5 sample tasks
python3 scripts/miner/eval_github.py \
    --github "https://github.com/Noyget/skibbot-sn36-agents/commit/782862b" \
    --tasks 5 \
    --max-steps 12 \
    --output-json /tmp/results.json \
    --keep-containers  # Keep for debugging if needed
```

**This will:**
- Clone your repo
- Build Docker image
- Deploy miner HTTP server
- Run 5 realistic validator tasks against it
- Show exactly which tasks pass/fail and why

### Step 2: Analyze Results

```bash
# View results
cat /tmp/results.json | jq .

# Look for:
# - "eval_score": [0.1, 0.3, 0.5, ...] (these are the per-task scores)
# - "success_rate": X% (how many scored >= 1.0?)
# - Error messages in logs
```

**Key Metrics:**
- If all eval_scores < 1.0 → All tasks incomplete
- If some > 1.0 → Some working, some not → Intermittent failure
- If patterns (all form tasks fail, all nav tasks pass) → Specific agent broken

### Step 3: Check Miner Logs

Your miner logs will show `/act` endpoint behavior:

```
[stateful_cua_eval] miner 98 /act returned no actions at step 2
  → Agent stopped sending actions (crash or deadlock)

[stateful_cua_eval] miner 98 /act failed: <error>
  → Agent HTTP endpoint threw exception

[stateful_cua_eval] miner 98 hard timeout during /act
  → Agent took >300s to respond (too slow)
```

**These logs tell you exactly what agent is doing wrong.**

---

## Part 4: The Fixes (In Priority Order)

### Priority 1: FormNavigator Wait-for-Readiness

**File:** Your miner code, FormNavigator module

**Change:** Add element state checks before interaction
```python
# Before: interact immediately
# After: wait for element to be visible, enabled, and loaded

async def click_element(selector):
    await page.wait_for_selector(selector)
    element = await page.query_selector(selector)
    await element.wait_for_element_state("visible")
    await element.wait_for_element_state("enabled")
    await page.wait_for_load_state("networkidle")
    await element.click()
```

**Impact:** Fixes race conditions and dynamic element issues  
**Effort:** 1 hour (1-2 files)  
**Expected Score Improvement:** +0.15-0.25 (assuming form tasks are 30% of suite)

### Priority 2: Screenshot ↔ HTML Sync

**File:** Your `/act` endpoint or evaluator integration

**Change:** Use fresh snapshot after state changes
```python
# In the validator's evaluation loop:
step_result = await evaluator.step(action)

# Before: used old HTML
# After: refresh HTML from latest snapshot
snapshot = step_result.snapshot
html = sanitize_snapshot_html(snapshot.html, uid)

# Use both together in next /act call
actions = await agent.act(
    task=task,
    snapshot_html=html,
    screenshot=snapshot.screenshot_after,
)
```

**Impact:** Fixes modal dialogs, dynamic content, state confusion  
**Effort:** 30 minutes (validation framework, not agent code)  
**Expected Score Improvement:** +0.1-0.2

### Priority 3: Add Retry/Error Recovery

**File:** Your agent's main act() logic

**Change:** If action fails, retry or try alternatives
```python
# Before: action fails → return no actions → agent gives up
# After: action fails → try alternate selector or wait longer → retry

if not action_result.success:
    # Try alternate
    alternate_action = try_xpath_selector(...)
    if not alternate_action:
        # Try scrolling to element first
        scroll_to_element(...)
        alternate_action = original_action
    if alternate_action:
        # Retry
        actions = [alternate_action]
    else:
        # Give up
        actions = []
```

**Impact:** Handles edge cases, selector robustness  
**Effort:** 2 hours (3-4 files, agent logic)  
**Expected Score Improvement:** +0.1-0.15

---

## Part 5: Implementation Roadmap

### Phase 1: Diagnostic (0.5-1 hour)
**Deliverable:** Know exactly which tasks are failing

1. Run `eval_github.py` locally (5-10 min execution)
2. Parse results JSON
3. Identify failure patterns:
   - All fail? (fundamental issue)
   - Form tasks fail? (FormNavigator broken)
   - Navigation tasks fail? (ScreenshotAnalyzer confused)
   - Intermittent? (timing/race condition)

### Phase 2: Priority Fix (2-3 hours)
**Deliverable:** Implement wait-for-readiness in FormNavigator

1. Update FormNavigator to use `wait_for_element_state()`
2. Add `page.wait_for_load_state("networkidle")` before interact
3. Test locally against form-heavy demo website
4. Run `eval_github.py` again → compare scores

### Phase 3: Sync Fix (0.5-1 hour)
**Deliverable:** Refresh HTML after state changes

1. Update evaluation loop to use fresh snapshots
2. Ensure HTML and screenshot are synchronized
3. Run `eval_github.py` again → compare scores

### Phase 4: Deploy (0.5 hour)
**Deliverable:** Push improvements to GitHub

1. Commit changes
2. Push commit to GitHub (get new commit hash)
3. Update miner to point to new commit (if needed)

### Phase 5: Wait for Validator Cycle (12-48 hours)
**Deliverable:** New eval_score results from mainnet validators

1. Monitor miner logs for validator requests
2. Check earned TAO in wallet
3. If still issues, iterate again

---

## Part 6: Success Criteria

### Minimum Success (Move Off Zero)
- **Target eval_score:** 1.0 on first task attempted
- **Expected TAO:** 0.5-1.0 per validator cycle
- **Effort:** 2-3 hours of fixes

### Good Performance (Early Stage)
- **Target eval_score:** 1.0 on 50% of tasks
- **Expected TAO:** 10-30 per validator cycle
- **Effort:** 4-6 hours of fixes + iteration

### Strong Performance (Competitive)
- **Target eval_score:** 1.0 on 80% of tasks
- **Expected TAO:** 50-150 per validator cycle
- **Effort:** 1-2 weeks of iteration

---

## Part 7: Quick Reference

### Commands You'll Need

```bash
# 1. Run diagnostic
cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official
python3 scripts/miner/eval_github.py \
    --github "https://github.com/Noyget/skibbot-sn36-agents/commit/782862b" \
    --tasks 5 --max-steps 12 --output-json /tmp/results.json

# 2. View results
cat /tmp/results.json | jq '.results[] | {task_id, eval_score, status}'

# 3. Check miner logs (after deploying fixes)
pm2 logs skibbot-miner --lines 50 --nostream | grep -i "error\|timeout\|/act"

# 4. Commit and push fixes
cd ~/your-miner-repo
git add -A
git commit -m "Fix: wait-for-readiness, HTML sync, error recovery"
git push origin main

# 5. Update miner config (if commit changed)
# Update GITHUB_URL env var to new commit hash
```

### Files to Monitor

**Your Miner Repo:**
- `neurons/miner.py` — HTTP server, /act endpoint
- Agent modules:
  - `agents/form_navigator.py` — Form interactions (Priority 1 to fix)
  - `agents/screenshot_analyzer.py` — Screenshot parsing (Priority 2)
  - Main agent logic — Error recovery (Priority 3)

**Validator Code (for reference):**
- `~/.openclaw/workspace/bittensor-workspace/autoppia-official/autoppia_web_agents_subnet/validator/evaluation/stateful_cua_eval.py` — How agents are tested
- `~/.openclaw/workspace/bittensor-workspace/autoppia-official/autoppia_web_agents_subnet/validator/evaluation/rewards.py` — Binary scoring (eval_score >= 1.0)

---

## Summary

| Phase | Time | Deliverable | Impact |
|-------|------|-------------|--------|
| Diagnostic | 15 min | Know exact failure modes | Guides fixes |
| FormNavigator fix | 1 hour | Wait-for-readiness | +0.15-0.25 score |
| HTML sync fix | 30 min | Fresh snapshots after state change | +0.1-0.2 score |
| Error recovery | 2 hours | Retry logic | +0.1-0.15 score |
| Deploy | 30 min | Push to GitHub | Ready for validation |
| **Total** | **~4.5 hours** | **eval_score likely 1.0+** | **TAO earnings begin** |

---

## Next Step: Run the Diagnostic

The diagnostic is the most important first step. It will tell us:
1. Are your agents working at all? (getting actions?)
2. Are actions executing? (getting state changes?)
3. Which specific tasks fail?
4. What are the error patterns?

Once we know this, we can target the exact fixes needed.

**Ready?**

```bash
cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official
python3 scripts/miner/eval_github.py \
    --github "https://github.com/Noyget/skibbot-sn36-agents/commit/782862b" \
    --tasks 5 \
    --max-steps 12 \
    --output-json /tmp/results.json
```

Run this and paste the results/errors. We'll analyze immediately and identify exactly what to fix.
