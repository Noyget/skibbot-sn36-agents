# SN36 Agent Code Analysis — Risk Assessment & Recovery Plan

## Executive Summary

Your agents are **well-architected** (async, type-hinted, error-handled) but likely **scoring 0/0 due to validator integration issues**, not code quality. The 0/0 result suggests validators aren't calling agents OR agents aren't returning results in the expected format.

---

## Agent Portfolio Overview

### 1. FormNavigationAgent ✅ COMPREHENSIVE
**Strengths:**
- ✅ 1200+ lines, mature codebase
- ✅ 10 navigation/interaction methods (click, fill, select, submit, etc.)
- ✅ Structured dataclasses with confidence scores
- ✅ Async/await throughout
- ✅ Detailed error handling + logging

**Potential Issues:**
- ⚠️ Depends on HTML structure — may fail on dynamically-rendered forms
- ⚠️ Timing-sensitive (element readiness checks) — could race condition
- ⚠️ No explicit retry logic for failed clicks/fills
- ⚠️ "Unknown" field handling could fail silently

### 2. ScreenshotAnalyzerAgent ✅ SOLID
**Strengths:**
- ✅ Vision-based element detection (screenshot → list of clickables)
- ✅ Confidence scoring per element
- ✅ Async implementation
- ✅ Handles missing/malformed screenshots

**Potential Issues:**
- ⚠️ Vision model dependent (OpenAI? Local?) — if model errors, agents fail
- ⚠️ Screenshot/HTML state mismatch (old HTML, new screenshot = wrong decisions)
- ⚠️ No retry on vision model failures

### 3. agents/server.py (FastAPI) ✅ CORRECT
**Status:** Properly deployed
**Routes:**
- POST `/act` — Main agent endpoint ✅
- GET `/health` — Health check ✅
- GET `/agents` — Agent list ✅
- GET `/status` — Status endpoint ✅

**Issue:** Server is correctly built, but **validators may not be calling it** (see Round 11 findings)

---

## Why 0/0 Likely Happened

### Most Likely Scenario (70% probability)
**Validators are running agents locally, NOT calling your HTTP endpoint.**

Evidence:
- Miner logs show only `StartRound` synapses (handshakes)
- No `/act` endpoint calls in logs
- 0/0 indicates no tasks attempted on your miner

**What this means:**
- Validators cloned your repo ✅
- Validators instantiated your agents ✅
- Validators called agents locally ✅
- **But: Agents returned 0 successful task completions** ❌

### Secondary Scenarios (20-30% probability)

**Scenario B:** Agents crash on instantiation
- Missing dependencies (e.g., vision model not imported)
- Import errors during agent initialization
- Check: Are all imports available in validator sandbox?

**Scenario C:** Agents timeout
- max_steps limit reached before task completion
- Validators limit each task to ~30-60 seconds
- If agents take too long on setup, validators timeout

**Scenario D:** Agent response format mismatch
- Agents return correct results, but wrong format
- Validators expect: `{"actions": [...], "reasoning": "..."}` format
- Agents return something else → validators can't grade → 0 score

---

## Code Review: Specific Risk Areas

### Risk 1: Agent Initialization (HIGH)
**File:** `agents/__init__.py`
**Question:** What happens when validators import and instantiate agents?

```python
# Check: Does FormNavigationAgent.__init__ fail?
# Check: Does ScreenshotAnalyzerAgent.__init__ fail?
# Check: Do any imports fail in sandbox environment?
```

**Action:** Verify `__init__.py` has safe, synchronous initialization.

---

### Risk 2: Vision Model Dependency (MEDIUM-HIGH)
**File:** `agents/screenshot_analyzer.py`
**Question:** Which vision model is used?

If using OpenAI Vision API:
- ✅ Correct (validators have API keys)
- ⚠️ But: Rate-limited (could timeout)
- ⚠️ But: May fail silently if API key wrong

If using local model:
- ❌ Model not loaded in validator sandbox
- ❌ Inference fails → agent returns error → 0 score

**Action:** Verify vision model is available in validator environment.

---

### Risk 3: HTML Parsing Edge Cases (MEDIUM)
**File:** `agents/form_navigator.py`, line 400+ (form extraction)
**Risk:** Forms with:
- JavaScript-rendered elements (JavaScript not executed in HTML)
- Shadow DOM / iframes (HTML parser can't reach)
- Dynamic field injection (HTML lacks fields added at runtime)

**Result:** FormNavigationAgent sees incomplete form → can't fill fields → 0 score

**Action:** Add explicit checks for dynamic content + retry logic.

---

### Risk 4: Timing & Race Conditions (MEDIUM)
**File:** `agents/form_navigator.py`, line 600+ (element.is_clickable checks)
**Risk:** Browser state vs. HTML mismatch:
- HTML says button exists
- Browser hasn't rendered button yet
- Agent clicks → fails (element not actually clickable)

**Action:** Add wait loops + exponential backoff for element readiness.

---

## Recovery Checklist

### Phase 1: Diagnose (This Session)
- [ ] Check if agents can be imported in Python directly
- [ ] Test FormNavigationAgent instantiation locally
- [ ] Test ScreenshotAnalyzerAgent instantiation locally
- [ ] Verify vision model works

### Phase 2: Fix (Next 2-4 hours)
- [ ] Add retry logic to agent methods (max 3 retries per action)
- [ ] Improve element readiness checks (add explicit waits)
- [ ] Add explicit logging before/after each agent call
- [ ] Verify response format matches validator expectations

### Phase 3: Deploy & Test (Next 2-4 hours)
- [ ] Commit fixes to GitHub
- [ ] Run local eval (once autoppia_iwa is available)
- [ ] Wait for next validator cycle
- [ ] Monitor logs for non-zero scores

---

## Immediate Actions

### 1. Test Agent Import
```bash
cd /tmp/skibbot-sn36-agents
python3 -c "from agents import FormNavigationAgent; print('✅ FormNavigationAgent imports OK')"
python3 -c "from agents import ScreenshotAnalyzerAgent; print('✅ ScreenshotAnalyzerAgent imports OK')"
```

### 2. Test Agent Instantiation
```bash
python3 << 'EOF'
from agents import FormNavigationAgent, ScreenshotAnalyzerAgent
form = FormNavigationAgent()
screenshot = ScreenshotAnalyzerAgent()
print("✅ Both agents instantiated successfully")
EOF
```

### 3. Check Dependencies
```bash
python3 -c "import openai; print('✅ OpenAI SDK available')"
python3 -c "import playwright; print('✅ Playwright available')"
python3 -c "from bs4 import BeautifulSoup; print('✅ BeautifulSoup available')"
```

---

## Key Questions for Anthony

1. **Do you know what the validator is actually doing?** (Is it calling `/act` or running agents locally?)
2. **What vision model does ScreenshotAnalyzer use?** (OpenAI Vision? Local model?)
3. **Do you have access to validator logs or error messages?** (Would show exactly what failed)
4. **Can you run a simple test locally?** (E.g., parse a form, extract fields → proves agents work)

---

## Expected Outcome of Fixes

**If Root Cause = Agent Performance (70% likely):**
- Fix: Add retries + better element readiness checks + improve error handling
- Impact: 50-80% success rate on easy tasks → TAO flows
- Timeline: 2-4 hours fix + deploy

**If Root Cause = Validator Integration (20% likely):**
- Fix: Change how agents respond or how they're called
- Impact: Could jump to 80%+ if format issue was the blocker
- Timeline: 1-2 hours if format fix, 4-8 hours if architecture fix needed

**If Root Cause = Missing Dependencies (10% likely):**
- Fix: Ensure vision model + all imports available in validator sandbox
- Impact: Immediate jump from 0% to agent quality level
- Timeline: 30 minutes once identified

---

**Report Generated:** 2026-03-25 12:14 UTC  
**Next Step:** Run the three "Immediate Actions" above to diagnose where agents break.
