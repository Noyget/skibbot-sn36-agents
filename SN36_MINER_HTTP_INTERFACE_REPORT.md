# SN36 Miner HTTP Interface & ApifiedWebCUA Architecture Report

**Date:** 2026-03-24  
**Subject:** How validators interact with miner HTTP servers via IWA library  
**Scope:** Autoppia SN36 (Web Agents) evaluation framework

---

## Executive Summary

The Autoppia SN36 validator framework uses the **IWA (Intelligent Web Agents) library** to evaluate miner submissions. The evaluation flow works as follows:

1. **Miner Deployment:** Miner GitHub repo is cloned and containerized; a Python HTTP server starts
2. **Agent Instantiation:** Validator creates an `ApifiedWebCUA` (alias for `ApifiedWebAgent`) with the miner's HTTP server URL
3. **Task Evaluation:** Validator sends browser tasks to the miner via HTTP `/act` endpoint
4. **Scoring:** Validator collects actions, screenshots, and execution history; scores based on task completion

This document details the HTTP interface contract between validators and miners.

---

## Architecture Overview

### Three-Layer Interaction Model

```
┌─────────────────────────────────────────────────────────┐
│ Validator (Bittensor Network)                           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ApifiedWebCUA Agent (IWA Library)                │  │
│  │                                                   │  │
│  │  • id: str (miner UID)                          │  │
│  │  • name: str (e.g., "miner-98")                 │  │
│  │  • base_url: str (miner's HTTP server URL)     │  │
│  │  • timeout: int (AGENT_STEP_TIMEOUT_SECONDS)   │  │
│  │                                                   │  │
│  │  Methods:                                         │  │
│  │    • agent.act(task, snapshot_html, ...)        │  │
│  │    • agent.reset()                              │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                                │
│                    HTTP Requests                        │
│                         ▼                                │
└─────────────────────────────────────────────────────────┘
         │
         │  POST /act
         │  GET /health
         │  (other endpoints)
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ Miner HTTP Server (Docker Container)                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ FastAPI / Flask Application                      │  │
│  │                                                   │  │
│  │  GET  /health                                    │  │
│  │  POST /act          (primary evaluation)        │  │
│  │  POST /reset        (session reset)             │  │
│  │  POST /screenshot   (capture page state)        │  │
│  │                                                   │  │
│  │  Backend: Web agent logic + LLM integration     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## ApifiedWebCUA Initialization

### Code Location
`autoppia_web_agents_subnet/validator/evaluation/stateful_cua_eval.py` (lines 80-92)

### Instantiation Pattern

```python
from autoppia_iwa.src.web_agents.apified_iterative_agent import ApifiedWebAgent

# Validator creates agent with miner's HTTP server details
agent = ApifiedWebCUA(
    id=str(uid),                           # Miner UID (e.g., "98")
    name=f"miner-{uid}",                   # Human-readable name
    base_url=base_url,                     # Miner's HTTP server (e.g., "http://172.104.24.232:8091")
    timeout=AGENT_STEP_TIMEOUT_SECONDS,    # Default: 300 seconds per step
)
```

### Configuration Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `AGENT_STEP_TIMEOUT_SECONDS` | 300 | Timeout per `/act` call (5 minutes) |
| `TASK_TIMEOUT_SECONDS` | 900 | Overall task budget (15 minutes) |
| `SHOULD_RECORD_GIF` | boolean | Whether to record GIF of agent actions |

**Source:** `autoppia_web_agents_subnet/validator/config.py`

---

## HTTP Endpoint Contract

### `/health` — Health Check (Implied)

**Purpose:** Validator verifies miner is running and responsive

**Expected Behavior:**
- **Method:** `GET`
- **Status Code:** 200 OK
- **Response:** Any JSON response (exact format not specified in code)
- **Used by:** Docker sandbox manager to confirm deployment success

**Example:**
```bash
curl http://miner-server:8000/health
# Expected: 200 OK + JSON response
```

---

### `/act` — Primary Evaluation Endpoint

**Purpose:** Send a task step to the miner agent; get back recommended actions

**Method:** `POST`

**Request Body** (from stateful_cua_eval.py lines 123-137):

```python
await agent.act(
    task=task_for_eval,                # Task object with goal/instructions
    snapshot_html=html,                # Sanitized HTML of current page
    screenshot=_to_screenshot_b64(screenshot),  # Base64-encoded PNG
    url=current_url,                   # Current page URL
    step_index=step_index,             # Current action step (0-indexed)
    history=history,                   # List of prior actions + results
)
```

**Request Payload Structure:**
```json
{
  "task": {
    "id": "task-123",
    "goal": "Buy a blue shirt from the store",
    "instructions": "Navigate to shop.example.com and add item to cart",
    "url": "https://shop.example.com",
    "expected_result": "Item in cart",
    "is_web_real": false
  },
  "snapshot_html": "<html><body>...</body></html>",
  "screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "url": "https://shop.example.com/products",
  "step_index": 0,
  "history": [
    {
      "step": 0,
      "action": "navigate",
      "candidate_id": null,
      "text": "https://shop.example.com",
      "exec_ok": true,
      "error": null
    }
  ]
}
```

**Response** (expected):
```python
# List of Action objects
[
    Action(type="click", selector="button.add-to-cart"),
    Action(type="type", selector="input.search", text="blue shirt"),
    Action(type="scroll", direction="down")
]
```

**Response Constraints:**
- If miner returns **no actions** (`[]`), validator stops task execution early
- Validator executes **at most one action per /act call** (single-step semantics)
- Actions should include: `type`, `selector` or `xpath`, optional `text` for input fields

**Timeout:** 300 seconds (AGENT_STEP_TIMEOUT_SECONDS)  
**Failure Handling:** If `/act` times out or throws exception, task evaluation stops

---

### Inferred Endpoints (from eval_github.py)

From script output message:
```
"Ensure repo starts an API with /health and /act, and includes required runtime deps."
```

**Minimum Required:**
- ✅ `GET /health` — Health check
- ✅ `POST /act` — Main evaluation endpoint

**Optional (likely):**
- `POST /reset` — Reset agent session (fresh browser state)
- `POST /screenshot` — Capture current page

---

## Task Object Structure

**Source:** `autoppia_iwa.src.data_generation.tasks.classes.Task`

### Key Fields

```python
class Task:
    id: str                      # Unique task identifier
    goal: str                    # High-level task goal (e.g., "Buy a red shirt")
    instructions: str            # Detailed step-by-step instructions
    url: str                      # Starting URL
    expected_result: str          # What success looks like
    is_web_real: bool             # True if real website, False if demo
    # Additional fields may exist in full implementation
```

### Task Augmentation for Demo Websites

For demo websites (`is_web_real=False`), validator **automatically augments the URL** with query parameters (lines 70-80):

```python
# Before sending to miner:
original_url = "https://demo.example.com/store"

# After augmentation:
augmented_url = "https://demo.example.com/store?X-WebAgent-Id=98&web_agent_id=98&X-Validator-Id=custom_validator&validator_id=custom_validator"
```

**Why:** Demo websites use localStorage to track agent/validator IDs. These IDs are required for backend event queries.

---

## Action History Tracking

### Validator Maintains History

After each `/act` call, validator records execution result (lines 141-160):

```python
history.append({
    "step": int(step_index),
    "action": getattr(action_executed, "type", None),
    "candidate_id": None,
    "text": getattr(action_executed, "text", None),
    "exec_ok": exec_ok,           # Did action execute without error?
    "error": exec_err,             # Error message if exec_ok=False
})
```

### History Sent Back to Miner

On the **next** `/act` call, this history is included so miner can:
- Detect loops (avoid repeating actions)
- Understand execution results
- Adjust strategy based on feedback

---

## Evaluation Lifecycle

### Step-by-Step Flow

**Initialization (lines 105-110):**
```python
# Validator calls evaluator.reset()
step_result = await evaluator.reset()  # Gets initial page snapshot
final_score = step_result.score
```

**Loop (lines 112-169):**
```python
while step_index < max_steps and not final_score.success:
    # 1. Get current page state (HTML + screenshot)
    html = step_result.snapshot.html
    screenshot = step_result.snapshot.screenshot_after
    
    # 2. Send to miner /act endpoint
    actions = await agent.act(
        task=task_for_eval,
        snapshot_html=html,
        screenshot=screenshot,
        url=current_url,
        step_index=step_index,
        history=history,
    )
    
    # 3. If no actions returned, stop (nothing left to do)
    if not actions:
        break
    
    # 4. Execute first action (single-step)
    action = actions[0]
    step_result = await evaluator.step(action)
    
    # 5. Record execution result in history
    history.append({...})
    
    # 6. Update final score
    final_score = step_result.score
    step_index += 1
```

**Termination Conditions:**
- `step_index >= max_steps` (default: 30 steps)
- `final_score.success == True` (task completed)
- `elapsed >= TASK_TIMEOUT_SECONDS` (900s budget exceeded)
- Miner returns no actions
- Miner `/act` call times out (300s)

### Scoring

```python
final_score: ScoreDetails  # Contains raw_score (0.0-1.0)
score = max(0.0, min(final_score.raw_score, 1.0))  # Clamp to [0, 1]
```

---

## Error Handling

### Miner Failures

**Timeout on /act:** (lines 128-131)
```python
try:
    actions = await asyncio.wait_for(agent.act(...), timeout=300)
except TimeoutError:
    bt.logging.warning(f"miner {uid} hard timeout during /act")
    break  # Stop task evaluation
```

**Exception on /act:** (lines 132-136)
```python
except Exception as exc:
    bt.logging.warning(f"miner {uid} /act failed: {exc}")
    break  # Stop task evaluation
```

**No Actions Returned:** (lines 140-144)
```python
if not actions:
    bt.logging.warning(f"miner {uid} returned no actions, stopping early")
    break
```

### Validator Cleanup

```python
finally:
    await asyncio.wait_for(evaluator.close(), timeout=5.0)
    # Collect action history and GIF recording if enabled
    solution = TaskSolution(
        task_id=...,
        actions=actions,
        web_agent_id=str(uid),
        recording=recording_payload,  # execution_history + optional GIF
    )
```

---

## IWA Library Requirements

### Installation

The `ApifiedWebAgent` class is imported from the **autoppia_iwa** package:

```python
from autoppia_iwa.src.web_agents.apified_iterative_agent import ApifiedWebAgent
```

### Fallback Handling

If import fails (lines 45-54):
```python
try:
    from autoppia_iwa.src.web_agents.apified_iterative_agent import ApifiedWebAgent
except Exception:
    try:
        from autoppia_iwa.src.web_agents import ApifiedWebAgent
    except Exception:
        class ApifiedWebAgent:
            def __init__(self, *_, **__):
                raise RuntimeError(
                    "ApifiedWebAgent unavailable: configure OPENAI_API_KEY/LLM_PROVIDER "
                    "in IWA environment or install web_agents module."
                )
```

### Environment Requirements

**For validator to evaluate miners, must have:**
- ✅ `autoppia_iwa` package installed
- ✅ `OPENAI_API_KEY` or equivalent LLM provider credentials
- ✅ LLM_PROVIDER configured in environment

**For miner HTTP server, must have:**
- ✅ FastAPI/Flask app with `/health` and `/act` endpoints
- ✅ Docker Dockerfile for containerization
- ✅ All agent dependencies (browser, LLM client, etc.)

---

## Deployment & Testing

### Validator Test Flow

**Script:** `scripts/miner/eval_github.py`

```bash
python eval_github.py \
    --github "https://github.com/user/agents/commit/abc123def" \
    --tasks 3 \
    --max-steps 12 \
    --uid 99999 \
    --output-json results.json
```

**What it does:**
1. Clones GitHub repo at specified commit
2. Builds Docker image from Dockerfile
3. Starts miner HTTP server in container
4. Creates ApifiedWebCUA agent pointing to container
5. Runs 3 sample tasks (max 12 steps each)
6. Scores task completion
7. Outputs JSON report

**Success Criteria:**
```
"Sandbox agent deployment failed. Ensure repo starts an API with /health and /act, 
 and includes required runtime deps. Re-run with --keep-containers to inspect docker logs."
```

If this error appears, check:
- ✅ Miner HTTP server listening on correct port
- ✅ `/health` endpoint responds with 200 OK
- ✅ `/act` endpoint accepts POST requests
- ✅ All dependencies installed in Docker image

---

## Practical Implementation Checklist

### For Miner Developers

**HTTP Server Setup:**
- ✅ Create FastAPI or Flask app
- ✅ Implement `GET /health` returning 200 + JSON
- ✅ Implement `POST /act` that:
  - ✅ Accepts task + snapshot + history
  - ✅ Runs your agent logic
  - ✅ Returns list of `Action` objects
  - ✅ Times out gracefully within 300s
- ✅ Dockerfile exposes HTTP port (typically 8000-9000)
- ✅ Start server on container startup

**Action Object Format:**
```python
class Action:
    type: str           # "click", "type", "scroll", "navigate", etc.
    selector: str       # CSS selector or XPath
    text: str           # Optional: text to type
    xpath: str          # Optional: XPath for element
```

**Response Format:**
```python
[
    {"type": "click", "selector": "button.submit"},
    {"type": "type", "selector": "input#search", "text": "query"},
]
```

**Docker Setup:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Key Takeaways

1. **Validator = Client:** Validator is the HTTP client; miner is the HTTP server
2. **base_url:** The miner's deployed HTTP server URL (e.g., "http://172.18.0.5:9000")
3. **ApifiedWebCUA:** IWA library class that wraps HTTP calls to miner
4. **Single-Step:** Each `/act` returns **one action** executed per loop iteration
5. **State Tracking:** Validator maintains full history (actions, errors, results)
6. **Timeout:** 300s per `/act` call; 900s total task budget
7. **Scoring:** Raw score (0-1) from task completion; higher is better
8. **Async:** All HTTP calls are async; validator runs multiple miners in parallel

---

## Appendix: Config Parameters

**File:** `autoppia_web_agents_subnet/validator/config.py`

```python
AGENT_STEP_TIMEOUT_SECONDS = 300      # Timeout per /act call
TASK_TIMEOUT_SECONDS = 900            # Total task budget
SHOULD_RECORD_GIF = False             # Record GIF of agent actions
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-24  
**Status:** Complete & Verified
