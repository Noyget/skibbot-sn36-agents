# SN36 Agent Performance Crisis — Root Cause Analysis

**Date:** 2026-03-24  
**Issue:** Earning 0 TAO despite miner being online and receiving validator tasks  
**Root Cause:** Agents scoring below 1.0 on IWA benchmark (binary pass/fail threshold)

---

## The Scoring System (Binary)

### How Validator Scores Your Agent

**Step 1: Task Evaluation**
```python
# evaluator.reset() + evaluator.step(action) * N iterations
score = final_score.raw_score  # From IWA evaluator (0.0 - 1.0)
```

**Step 2: Task Reward (Binary Function)**
```python
def calculate_reward_for_task(eval_score, execution_time, token_cost):
    # Binary success: eval_score >= 1.0 to get ANY reward
    solved = float(eval_score) >= 1.0
    
    if not solved:
        return 0.0  # ZERO REWARD - not 0.5, not 0.1, but ZERO
    
    # Only if fully solved:
    time_penalty = execution_time / 900s
    cost_penalty = token_cost / $X
    reward = 1.0 + (1.0 - time_penalty) * 0.3 + (1.0 - cost_penalty) * 0.2
    return reward
```

**THE CRITICAL THRESHOLD:** `eval_score >= 1.0`

### What This Means

- **eval_score = 0.99** → Reward = **0.0** (complete failure in system's eyes)
- **eval_score = 1.0** → Reward = **0.8-1.2** (partial credit + time/cost bonuses)
- **eval_score = 1.5+** → Reward = **max(1.2)** (capped at perfect execution + bonuses)

**You're probably scoring 0.2-0.7 range** — which returns exactly 0 TAO.

---

## Where eval_score Comes From

### The IWA Evaluator (Black Box)

```python
# In stateful_cua_eval.py
final_score = step_result.score  # From AsyncStatefulEvaluator
score = max(0.0, min(final_score.raw_score, 1.0))
```

**The evaluator measures:**
1. **Task completion** — Did agent achieve the task goal?
2. **Action quality** — Are the actions semantically correct?
3. **Page interaction success** — Did actions actually modify page state?

**The evaluator tracks:**
- Task state before/after each action
- Whether page changed as expected
- Whether goal was achieved

**The scoring:**
- Full completion (goal achieved) = 1.0
- Partial completion (some progress) = 0.1-0.9
- No progress = 0.0

---

## Why Your Agents Are Failing

### Likely Failure Modes (Top 3)

#### 1. **Form Navigator Crashes on Dynamic Elements**
**Symptom:** Agent can't find or interact with form inputs  
**Root Cause:** 
- Form inputs appear after page loads (JavaScript rendering)
- Selector finds element, but element isn't clickable/typeable
- Agent tries to click hidden input field

**Test Case:** Any task with a form on a modern website
```
Goal: Fill out checkout form
Agent sees form in HTML, tries to click address field
But field is position:absolute, off-screen, or within shadow DOM
Agent fails silently or errors
```

#### 2. **Screenshot Analyzer Misidentifies Page Content**
**Symptom:** Agent sees screenshot but makes wrong decisions  
**Root Cause:**
- Complex layouts confuse LLM model
- Agent can't distinguish interactive vs. decorative elements
- Screenshot has changed state (loading spinner, modal opened) but agent uses old HTML snapshot

**Test Case:** Multi-step task with modal dialogs
```
Step 1: Agent clicks "Add to Cart" → Modal opens
Step 2: HTML snapshot is from BEFORE modal; screenshot shows modal
Step 3: Agent confused about which HTML to trust
Step 4: Makes wrong click → page state broken
```

#### 3. **Action Timing Issues (Race Conditions)**
**Symptom:** Agent returns action, page isn't ready  
**Root Cause:**
- Agent sends `{"type": "click", "selector": ".checkout-button"}`
- Button exists in HTML but isn't ready (JavaScript still loading)
- Click happens on wrong element or does nothing

**Test Case:** Any task on slow/complex website
```
Task: Buy product
Step 1: Navigate to product page
Step 2: Agent sees "Add to Cart" button in HTML
Step 3: Agent clicks immediately
Step 4: Page still loading, button click queued but doesn't register
Step 5: No state change, agent stuck in loop or fails
```

---

## What Validators Actually Test (IWA Benchmark)

### Demo Web Projects Used

From `tasks.py`:
```python
demo_web_projects = [
    # Various e-commerce, form-based, navigation-heavy websites
    # Each with 3-5 "use cases" (different task types)
]
```

**Task Categories:**
1. **E-Commerce** (search, filter, add to cart)
2. **Form Filling** (contact, checkout, signup)
3. **Navigation** (find information, search results)
4. **Dynamic Content** (click to load, pagination)

**Success Criteria (for IWA Evaluator):**
- Task goal must be 100% achieved
- No partial credit for "almost working"
- Multi-step tasks require ALL steps completed

---

## The Path to 1.0+ Scores (and TAO)

### What Needs to Change

**1. Make FormNavigator Wait for Readiness**
```python
# Current (probably): click immediately after seeing selector
await element.click()

# Needed: Wait for element to be ready
await element.wait_for_element_state("visible")
await element.wait_for_element_state("enabled")
await element.click()
```

**2. Handle Dynamic Content / JavaScript Rendering**
```python
# Current: Use HTML snapshot immediately
html = snapshot.html

# Needed: Wait for JS to finish, then take new snapshot
await page.wait_for_load_state("networkidle")
snapshot = await evaluator.reset()  # or similar
```

**3. Sync Screenshot & HTML State**
```python
# Current: Send stale HTML with new screenshot
actions = await agent.act(
    task=task,
    snapshot_html=html_from_5_steps_ago,  # WRONG
    screenshot=latest_screenshot,  # NOW
)

# Needed: Refresh HTML after each major state change
snapshot = await evaluator.step(action)
html = sanitize_snapshot_html(snapshot.html, uid)  # Fresh
```

**4. Implement Proper Error Recovery**
```python
# Current: "action failed, stop and return 0"
if not exec_ok:
    break  # GIVES UP IMMEDIATELY

# Needed: Try alternative approach
if not exec_ok:
    # Try different selector, scroll, wait, try again
    alternate_actions = agent.get_alternate_actions(...)
    # Retry
```

---

## The Action Plan

### Phase 1: Diagnostic (Next 1-2 Hours)
1. **Run eval_github.py locally** against your agents
   ```bash
   python scripts/miner/eval_github.py \
     --github "https://github.com/Noyget/skibbot-sn36-agents/commit/782862b" \
     --tasks 5 \
     --max-steps 12 \
     --output-json results.json
   ```

2. **Examine output** — Find which tasks score highest/lowest
   - Which use cases fail? (form, nav, ecommerce?)
   - Where does agent get stuck? (which step?)
   - Are actions being sent? Are they executing?

3. **Look at logs** — Check your miner's `/act` responses
   - Is agent returning actions consistently?
   - Are actions valid (selectors exist)?
   - Are actions being executed?

### Phase 2: Fix FormNavigator (Highest Priority)
1. **Add wait_for_element_state() checks**
2. **Implement scroll-to-element before interact**
3. **Add retry logic for failed interactions**
4. **Test against any form-based demo website**

### Phase 3: Fix ScreenshotAnalyzer
1. **Re-sync HTML after major state changes**
2. **Handle modal dialogs / overlays**
3. **Detect and wait for loading states**

### Phase 4: Deploy & Iterate
1. **Push changes to GitHub**
2. **Wait for next validator cycle (24-48h)**
3. **Monitor miner logs for /act success rates**
4. **If still failing, debug specific failing tasks**

---

## Key Files to Examine

**Validator Evaluation:**
- `autoppia_web_agents_subnet/validator/evaluation/stateful_cua_eval.py` — How your agent is tested
- `autoppia_web_agents_subnet/validator/evaluation/rewards.py` — Binary scoring function (1.0+ or 0.0)

**Your Agent Code (in your miner repo):**
- `FormNavigator` — Interacts with form elements
- `ScreenshotAnalyzer` — Reads screenshots
- `/act` endpoint — Receives tasks, returns actions

**IWA Library (not directly accessible, but imported):**
- `autoppia_iwa.src.data_generation.tasks` — Task generation
- `autoppia_iwa.src.evaluation.stateful_evaluator` — Scoring

---

## Critical Insight

**The evaluator doesn't care about "trying"** — it only cares about success.

- 99% task completion = 0 TAO
- 100% task completion = 0.8-1.2 TAO (+ bonuses)

This is why you're earning 0. Your agents are probably at 60-80% completion on average. To move from 0 TAO to earning significantly, **you need to jump to near-100% completion**.

**The fix is not incremental improvements — it's fixing the failure modes that break tasks completely.**

---

## Timeline

- **Now → 1 hour:** Run local eval, identify failure modes
- **1-4 hours:** Fix FormNavigator wait/retry logic
- **4-6 hours:** Fix screenshot/HTML sync
- **6+ hours:** Deploy to GitHub, push commit
- **Next validator cycle:** New test results (could be 12-48h)
- **2-3 cycles:** Iterate to 90%+ completion rate
- **Then:** TAO earnings ramp up (2-10 TAO/day possible)

---

**Next Step:** Run `eval_github.py` and show me the results. That will tell us exactly which agents are failing and why.
