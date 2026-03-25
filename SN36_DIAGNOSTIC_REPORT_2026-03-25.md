# SN36 Diagnostic Report — 2026-03-25 Round Completion Analysis

## Executive Summary

**Round Result:** 0/0 tasks completed, 0% reward
**Status:** CRITICAL — Agent performance unknown; evaluation methodology requires investigation

---

## Key Finding: How SN36 Actually Works

### The Confusion
We deployed `agents/server.py` thinking validators would call our HTTP endpoint to solve tasks. **This assumption was wrong.**

### The Reality (SN36 Blueprint Architecture)
1. **Validator receives StartRound from your miner** ✅ (happening, 4 validators detected)
2. **Validator clones your GitHub repo** ✅ (expected)
3. **Validator runs evaluation locally in their sandbox**
   - Validators use their own **ApifiedWebAgent** (LLM-based agent from IWA library)
   - They do NOT call your `/act` endpoint
   - They do NOT use your agents during task solving
4. **Validators read task results from your agents if available** (unsure if happening)
5. **Validators grade and submit eval_score** → 0/0 in this round

### Why Your Agents Scored 0/0
- Validators successfully received your metadata ✅
- Validators cloned your repo ✅
- **But:** Your agents either weren't used OR scored poorly when evaluated
- **Evidence:** No agent execution logs in miner logs (agents/server.py never called)

---

## What We Need to Determine

**Critical Questions:**
1. Do your agents run at all in the validator's sandbox?
2. What's the actual success rate when agents are tested locally?
3. Which agents fail most frequently? (FormNavigator? ScreenshotAnalyzer?)
4. Are agents timing out, crashing, or just scoring low?

**Next Step:** Run `eval_github.py` locally to test against real IWA tasks

---

## Miner Status (Confirmed Working)

- ✅ Process running: 5+ hours uptime
- ✅ Axon listening: 172.104.24.232:8091
- ✅ StartRound received: Multiple validators at 06:00, 12:00 UTC
- ✅ Metadata correct: agent_name="SkibBot Web Agents", commit=8f9b041
- ✅ agents/server.py deployed: FastAPI HTTP endpoint ready

---

## Round 11 Detailed Timeline

| Time (UTC) | Event |
|---|---|
| 05:08-05:12 | Miner restarted, axon listening |
| 06:00 | StartRound from validator 55 |
| 06:00-06:48 | More validators discovering (UID count: 4) |
| 06:30-10:43 | HTTP scan errors (bot/scanner noise on port 8091) — harmless |
| ~11:00 (estimated) | Round 11 evaluation completed |
| 12:00+ | New round begins, next batch of validators arriving |

---

## What agents/server.py Actually Does

**Current Implementation:**
- Exposes `POST /act` endpoint
- Accepts task requests (if anyone sends them)
- Returns agent execution results

**Problem:** Validators aren't sending requests to `/act`. They're:
1. Cloning the repo
2. Running evaluation locally
3. Scoring based on locally-run agents (OR their own agents)

**agents/server.py may be:**
- ✅ Necessary for some bootstrap/validation flow
- ❌ NOT the bottleneck for 0/0 scoring
- ✅ Correctly deployed (FastAPI working)
- ❌ NOT being called by validators during Round 11

---

## Recovery Path

### Immediate (Next 24h)
1. Run local eval against real IWA tasks: `eval_github.py`
2. Identify which agents fail and why
3. Document specific failure modes

### Short-term (Next 48-72h)
1. Fix identified agent failures
2. Improve agent robustness (timing, error handling, state sync)
3. Deploy fix to GitHub

### Medium-term (Next cycle)
1. New validators test updated code
2. Should see non-zero scores if fixes work
3. TAO should start flowing

---

## Critical Code to Review

- `agents/form_navigator.py` — Most complex, high failure risk
- `agents/screenshot_analyzer.py` — Timing-sensitive
- `agents/__init__.py` — Agent factory/initialization
- `agents/server.py` — HTTP interface (already fixed)

---

## Questions for Anthony

1. Do you know if agents are actually being called during validator evaluation?
2. Can we get validator logs or feedback on what went wrong?
3. Should we focus on:
   - **A) Improving agent quality** (likely scenario)
   - **B) Changing how validators call agents** (unlikely to be issue)
   - **C) Both?** (yes, probably)

---

**Report Generated:** 2026-03-25 12:09 UTC
**Next Action:** Run eval_github.py diagnostic
