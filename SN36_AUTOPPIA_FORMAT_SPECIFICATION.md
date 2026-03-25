# SN36 Autoppia Format Specification — Agent Response Standards

**Source:** Analyzed from official Autoppia subnet code (autoppia_web_agents_subnet v31.0.0)  
**Date:** 2026-03-25  
**Confidence:** HIGH (extracted from validators + platform models)

---

## Executive Summary

Your agents must return **action lists**, not structured result objects. Format is flexible but requires:
1. An `actions` list (or similar)
2. Each action must have a `type` field
3. Actions should include selector/text/value/url/x/y as needed
4. Can be Pydantic models, dicts, or dataclasses (validator normalizes them)

---

## TaskSolution Expected Format

### Required Fields
```python
@dataclass
class TaskSolutionIWAP:
    solution_id: str
    task_id: str
    agent_run_id: str
    validator_round_id: str
    validator_uid: int
    validator_hotkey: str
    miner_uid: int | None
    miner_hotkey: str | None
    actions: list[dict[str, Any]]  # ← CRITICAL
    recording: Any | None = None
    metadata: dict[str, Any] = {}
```

### What Validators Expect

**Validators will call your agent with:**
```json
{
  "task_id": "task_123",
  "agent_run_id": "run_456",
  "validator_round_id": "round_789",
  "url": "https://example.com/form",
  "prompt": "Fill out the form and submit",
  "specifications": { ... },
  "tests": [ ... ],
  "payload": { ... }
}
```

**Your agent should return:**
```python
class TaskSolution:
    actions: [
        {"type": "click", "selector": "#email_field"},
        {"type": "input", "selector": "#email_field", "value": "test@example.com"},
        {"type": "click", "selector": "#submit"},
    ]
```

---

## Action Format Standards

### Required for Each Action
```json
{
  "type": "click|input|select|submit|navigate|scroll|hover|...",
  // Plus action-specific fields:
  "selector": "CSS selector or XPath",  // For click, input, select
  "value": "text to input",              // For input
  "option_value": "value to select",     // For select
  "url": "https://...",                  // For navigate
  "x": 100,                              // For click at coordinates
  "y": 200,
  // Optional metadata
  "confidence": 0.95,
  "reasoning": "Why this action",
}
```

### Supported Action Types
From fixtures and code analysis:
```python
{
  "type": "click",        # Click element at selector
  "type": "input",        # Fill text field
  "type": "select",       # Select dropdown option
  "type": "submit",       # Submit form
  "type": "navigate",     # Navigate to URL
  "type": "scroll",       # Scroll page
  "type": "wait",         # Wait for element
  "type": "hover",        # Hover over element
  "type": "type",         # Type text (alternative to input)
  "type": "key_press",    # Press keyboard key
  "type": "file_upload",  # Upload file
}
```

---

## Example Agent Response Formats

### Format 1: Simple Dict List (EASIEST)
```python
# Your agent returns:
actions = [
    {"type": "click", "selector": "#email"},
    {"type": "input", "selector": "#email", "value": "test@example.com"},
    {"type": "click", "selector": "#submit"}
]
return {"actions": actions}
```

**What validator receives:**
```python
solution.actions = [
    {"type": "click", "selector": "#email"},
    {"type": "input", "selector": "#email", "value": "test@example.com"},
    {"type": "click", "selector": "#submit"}
]
```

---

### Format 2: Pydantic Models (RECOMMENDED)
```python
from pydantic import BaseModel
from typing import Optional

class Action(BaseModel):
    type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    confidence: Optional[float] = 0.95

class TaskSolution(BaseModel):
    actions: list[Action]
    reasoning: Optional[str] = None

# Your agent returns:
solution = TaskSolution(
    actions=[
        Action(type="click", selector="#email", confidence=0.98),
        Action(type="input", selector="#email", value="test@example.com"),
        Action(type="click", selector="#submit")
    ],
    reasoning="Filled form with email and submitted"
)
return solution
```

**What validator receives:**
```python
solution = TaskSolution(...)
solution.actions = [Action(...), Action(...), ...]
# Validator calls: solution.model_dump(mode="json", exclude_none=True)
```

---

### Format 3: Dataclass (ALSO WORKS)
```python
from dataclasses import dataclass

@dataclass
class Action:
    type: str
    selector: str = None
    value: str = None

@dataclass  
class TaskSolution:
    actions: list[Action]

# Your agent returns:
return TaskSolution(actions=[
    Action(type="click", selector="#email"),
    Action(type="input", selector="#email", value="test@example.com"),
    Action(type="click", selector="#submit")
])
```

---

## How Validators Normalize Your Response

**Source:** `_normalize_action_payload()` in `task_flow.py`

Validators are **forgiving** of format variations. They:

1. ✅ Accept Pydantic models (call `model_dump()`)
2. ✅ Accept plain dicts
3. ✅ Accept objects with `__dict__` (dataclasses)
4. ✅ Flatten nested "action" or "attributes" payloads
5. ✅ Extract fields from object properties if needed
6. ✅ Convert all to JSON-serializable dicts

**Worst case:** Your action format is a bit odd, but validator still extracts `type` + common fields (selector, text, value, url, x, y)

**Best case:** Return clean dicts with `type` + needed fields

---

## What Your Server MUST Return

**Current server.py:**
```python
@app.post("/act")
async def act(request: AgentRequest) -> AgentResponse:
    result = await screenshot_agent.analyze_screenshot(...)
    return AgentResponse(
        success=True,
        agent="screenshot_analyzer",
        result=result  # ← THIS MIGHT BE WRONG
    )
```

**What validators expect:**

Option A (if server is called):
```python
# Validator expects the /act endpoint to return actions list
# But wait... SN36 validators DON'T call the server!
# They clone your repo and run agents locally in Docker sandbox.
```

**The Critical Truth:**
Your `/act` endpoint isn't used by validators in Round 11. Instead:
1. Validators clone your repo
2. Create a Docker container with your code
3. Instantiate your agents directly
4. Call agent methods directly (not via HTTP)
5. Get back action lists

So the server.py format doesn't matter for scoring — what matters is:
- **FormNavigationAgent must have async method that returns actions**
- **ScreenshotAnalyzerAgent must have async method that returns actions**

---

## Critical Fixes Needed

### Fix #1: Export ScreenshotAnalyzerAgent
**File:** `agents/__init__.py`

Add:
```python
from .screenshot_analyzer import ScreenshotAnalyzerAgent

__all__ = [
    # ... existing exports ...
    "ScreenshotAnalyzerAgent",
]
```

### Fix #2: Ensure Agents Return Actions

**Question:** Do FormNavigationAgent and ScreenshotAnalyzerAgent have methods that return action lists?

Check:
```python
# In form_navigator.py:
async def navigate_form(self, html: str) -> list[dict]:
    # Must return: [{"type": "...", "selector": "...", ...}, ...]
    pass

# In screenshot_analyzer.py:
async def analyze_and_act(self, screenshot: bytes) -> list[dict]:
    # Must return: [{"type": "...", "selector": "...", ...}, ...]
    pass
```

If agents return different formats (e.g., task completion status, confidence scores), they need to be converted to action lists.

### Fix #3: Ensure Vision Model is Available

**Question:** Is ScreenshotAnalyzerAgent using OpenAI Vision API or a local model?

- If **OpenAI**: ✅ Should work (validator sandbox has openai==2.16.0)
- If **Local model**: ❌ Must download model at runtime or fail gracefully

Check:
```python
# In screenshot_analyzer.py, find where vision model is initialized:
# If using OpenAI:
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# If using local:
# from transformers import pipeline
# vision = pipeline("image-to-text", model="...")  # ❌ Will fail
```

---

## Success Criteria

Your agents will pass validator evaluation if:

1. ✅ ScreenshotAnalyzerAgent can be imported from `agents`
2. ✅ Both agents can be instantiated without errors
3. ✅ Both agents have callable async methods that accept task data
4. ✅ Both agents return `actions: list[dict[str, Any]]`
5. ✅ Each action has a `type` field and relevant params (selector, value, etc.)
6. ✅ Vision model is available (API, not local)
7. ✅ Agents handle errors gracefully (don't crash, return empty actions)

---

## Testing Locally

Before deploying, verify:

```bash
cd /tmp/skibbot-sn36-agents

# Test import
python3 -c "from agents import FormNavigationAgent, ScreenshotAnalyzerAgent; print('✅')"

# Test instantiation
python3 << 'EOF'
from agents.form_navigator import FormNavigationAgent
from agents.screenshot_analyzer import ScreenshotAnalyzerAgent

form = FormNavigationAgent()
screenshot = ScreenshotAnalyzerAgent()
print("✅ Both agents instantiate")

# Test they have async methods
import inspect
assert inspect.iscoroutinefunction(form.navigate), "FormNavigationAgent missing async method"
print("✅ FormNavigationAgent has async methods")
EOF
```

---

## References

**Source files analyzed:**
- `autoppia_web_agents_subnet/platform/models.py` — TaskSolutionIWAP definition
- `autoppia_web_agents_subnet/platform/utils/task_flow.py` — Validator expects `solution.actions`
- `tests/fixtures/miner_fixtures.py` — Example action formats
- `autoppia_web_agents_subnet/opensource/sandbox/Dockerfile` — Sandbox environment

---

**Specification Complete.** Ready to implement fixes.
