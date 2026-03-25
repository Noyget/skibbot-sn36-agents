# SN36 Format Investigation — CRITICAL ARCHITECTURE MISMATCH DISCOVERED

**Investigation Date:** 2026-03-25 12:20 UTC  
**Severity:** 🔴 CRITICAL  
**Status:** ARCHITECTURE MISMATCH CONFIRMED

---

## The Problem (In Plain English)

Your agents are **analysis tools**, not **action generators**. This is why they score 0/0.

**What Validators Need:**
- Input: HTML + task prompt
- Output: List of browser actions (click, fill, submit, etc.)
- Example: `[{"type": "click", "selector": "#email"}, {"type": "input", "text": "test@example.com"}]`

**What Your Agents Currently Do:**
- FormNavigationAgent: Analyzes form structure, returns insights & navigation paths
- ScreenshotAnalyzerAgent: Analyzes screenshot, returns UI elements & layout info
- Neither returns action sequences validators can execute

---

## Architecture Mismatch Confirmed

### FormNavigationAgent (❌ Wrong Architecture)
**Current:**
```python
async def extract_form_structure(self, html: str) -> FormNavigationResult:
    # Returns:
    {
        "success": true,
        "form_state": {...},
        "navigation_paths": [...],  # Analysis, not actions
        "recommendations": [...]
    }
```

**What Validators Need:**
```python
async def solve_form_task(self, html: str, prompt: str) -> list[dict]:
    # Returns:
    [
        {"type": "click", "selector": "#email"},
        {"type": "input", "selector": "#email", "value": "user@example.com"},
        {"type": "click", "selector": "#submit"}
    ]
```

### ScreenshotAnalyzerAgent (❌ Wrong Architecture)
**Current:**
```python
async def analyze_screenshot(self, image_path: str) -> AnalysisResult:
    # Returns:
    {
        "elements": [
            {"type": "button", "text": "Submit", "bounds": {...}},
            {"type": "input", "name": "email", "bounds": {...}}
        ],
        "layout_type": "form",
        "overall_confidence": 0.92
    }
```

**What Validators Need:**
```python
async def solve_from_screenshot(self, image: bytes, prompt: str) -> list[dict]:
    # Returns:
    [
        {"type": "click", "selector": "button:contains('Submit')"},
        {"type": "input", "selector": "[name='email']", "value": "test@example.com"}
    ]
```

---

## Root Cause: Design Disconnect

Your agents were designed as **analysis/insight tools** for a different use case. But SN36 validators need **action-generating agents** that:

1. **Understand the task** (prompt + specifications)
2. **Analyze the page** (HTML or screenshot)
3. **Generate action sequence** to complete task
4. **Return actions as list** for validator to execute

---

## Recovery Options

### Option A: Wrapper Functions (FAST - 2-3 hours)
Create new methods that use analysis agents → generate actions

```python
# In form_navigator.py (NEW):
async def solve_form_task(self, html: str, prompt: str, max_steps: int = 12) -> list[dict]:
    """
    Solve form task by analyzing structure + generating actions.
    """
    # Step 1: Analyze form structure
    form_analysis = await self.extract_form_structure(html)
    
    # Step 2: Determine actions needed based on prompt
    # "Fill out the form with email test@example.com and submit"
    actions = []
    if "email" in prompt.lower():
        # Find email field from analysis
        email_field = next((f for f in form_analysis.form_state.current_fields 
                           if "email" in f.name.lower()), None)
        if email_field:
            actions.append({"type": "click", "selector": f"[name='{email_field.name}']"})
            actions.append({"type": "input", "selector": f"[name='{email_field.name}']", 
                          "value": "test@example.com"})
    
    # Step 3: Find and click submit
    for path in form_analysis.navigation_paths:
        if path.action_type == "submit":
            actions.append({"type": "click", "selector": path.target_selector})
            break
    
    return actions
```

**Pros:**
- ✅ Reuses existing analysis code
- ✅ Fast to implement
- ✅ Leverages form structure insights

**Cons:**
- ⚠️ May not handle complex interactions
- ⚠️ Dependent on analysis quality

### Option B: LLM-Based Action Generator (ROBUST - 4-6 hours)
Use GPT to convert analysis → actions

```python
async def solve_form_task(self, html: str, prompt: str) -> list[dict]:
    """
    Use OpenAI to generate actions from form analysis + prompt.
    """
    # Step 1: Analyze form
    form_analysis = await self.extract_form_structure(html)
    
    # Step 2: Build prompt for LLM
    llm_prompt = f"""
    Task: {prompt}
    
    Form structure:
    {json.dumps(form_analysis.form_state.__dict__, default=str, indent=2)}
    
    Generate a JSON list of actions to complete this task.
    Return ONLY valid JSON, no explanation.
    Each action must have: {{"type": "...", "selector": "...", ...}}
    """
    
    # Step 3: Call OpenAI
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": llm_prompt}],
        temperature=0
    )
    
    # Step 4: Parse and return actions
    actions = json.loads(response.choices[0].message.content)
    return actions
```

**Pros:**
- ✅ Highly flexible
- ✅ Can handle complex interactions
- ✅ Learns from multiple agents

**Cons:**
- ⚠️ Slower (API call per task)
- ⚠️ More expensive (GPT-4 tokens)
- ⚠️ Less deterministic

### Option C: Redesign Agents (COMPREHENSIVE - 8-12 hours)
Rewrite agents from scratch as action generators

**What this looks like:**
```python
class WebAgentV2:
    """Autonomous web task solver (generates actions, not analysis)."""
    
    async def solve(self, html: str, prompt: str, screenshot: bytes = None) -> list[dict]:
        """
        Main entry point: HTML + task → actions
        """
        # 1. Parse HTML
        # 2. Analyze screenshot if provided
        # 3. Understand task from prompt
        # 4. Generate action sequence
        # 5. Return actions
```

**Pros:**
- ✅ Clean architecture
- ✅ Purpose-built for SN36
- ✅ Best long-term solution

**Cons:**
- ❌ Requires significant rewrite
- ❌ Most time-consuming
- ❌ Highest risk

---

## Recommendation: Hybrid Approach (FASTEST PATH TO TAO)

### Hour 1: Emergency Fix
1. Fix export issue (2 min) — ScreenshotAnalyzerAgent in __init__.py
2. Add wrapper method to FormNavigationAgent (10 min)
3. Deploy to GitHub (5 min)

### Hours 2-3: Improved Wrapper
1. Add LLM-based action generator using OpenAI GPT (30 min)
2. Test locally against sample forms (30 min)
3. Deploy v2 (5 min)

### Total Recovery Time: 3-4 hours
**Expected Result:** 40-70% success rate on easy-medium tasks

---

## Implementation Guide: Option A (Recommended)

### Step 1: Add Wrapper to FormNavigationAgent

**File:** `agents/form_navigator.py` (add new method at end)

```python
async def solve_form_task(
    self,
    html: str,
    prompt: str,
    max_steps: int = 12
) -> list[dict]:
    """
    Solve form-based task by generating action sequence.
    
    Args:
        html: Form HTML content
        prompt: Task description (e.g., "Fill email with user@example.com and submit")
        max_steps: Maximum number of actions to generate
        
    Returns:
        List of actions: [{"type": "click", "selector": "..."}, ...]
    """
    actions = []
    
    try:
        # Step 1: Analyze form structure
        analysis = await self.extract_form_structure(html)
        if not analysis.success or not analysis.form_state:
            return []
        
        # Step 2: Extract task requirements from prompt
        prompt_lower = prompt.lower()
        field_values = {}
        
        # Basic pattern matching for common field patterns
        import re
        email_match = re.search(r'email[:\s]+([^\s,\.]+@[^\s,\.]+)', prompt_lower)
        if email_match:
            field_values['email'] = email_match.group(1)
        
        name_match = re.search(r'name[:\s]+([^,\.]+)', prompt_lower)
        if name_match:
            field_values['name'] = name_match.group(1).strip()
        
        # Step 3: Generate click + fill actions for each field
        for field in analysis.form_state.current_fields:
            field_name_lower = field.name.lower()
            
            # Find value for this field
            field_value = None
            for key, value in field_values.items():
                if key in field_name_lower:
                    field_value = value
                    break
            
            if field_value:
                # Click field
                actions.append({
                    "type": "click",
                    "selector": f"[name='{field.name}']"
                })
                
                # Fill field
                actions.append({
                    "type": "input",
                    "selector": f"[name='{field.name}']",
                    "value": field_value
                })
        
        # Step 4: Find and click submit button
        for path in analysis.navigation_paths:
            if path.action_type == NavigationType.SUBMIT or "submit" in path.target_selector.lower():
                actions.append({
                    "type": "click",
                    "selector": path.target_selector
                })
                break
        
        return actions[:max_steps]
    
    except Exception as e:
        logger.error(f"Error generating actions: {e}")
        return []
```

### Step 2: Add Similar Wrapper to ScreenshotAnalyzerAgent

**File:** `agents/screenshot_analyzer.py` (add new method)

```python
async def solve_from_screenshot(
    self,
    screenshot_data: bytes,
    prompt: str,
    max_steps: int = 12
) -> list[dict]:
    """
    Generate actions from screenshot analysis + task prompt.
    
    Args:
        screenshot_data: Screenshot image bytes
        prompt: Task description
        max_steps: Maximum actions
        
    Returns:
        List of actions
    """
    try:
        # Analyze screenshot
        analysis = await self.analyze_screenshot_from_bytes(screenshot_data)
        
        # Find clickable elements that match prompt keywords
        actions = []
        prompt_lower = prompt.lower()
        
        for element in analysis.elements:
            if "click" in prompt_lower or "button" in element.type.lower():
                if element.text and any(word in element.text.lower() 
                                       for word in ['submit', 'send', 'continue']):
                    actions.append({
                        "type": "click",
                        "selector": element.selector or f"[data-element='{element.element_id}']",
                        "text": element.text
                    })
        
        return actions[:max_steps]
    
    except Exception as e:
        logger.error(f"Error solving from screenshot: {e}")
        return []
```

### Step 3: Update server.py to Use New Methods

**File:** `agents/server.py` (update /act endpoint)

```python
@app.post("/act")
async def act(request: AgentRequest) -> AgentResponse:
    """Main agent endpoint for handling validator requests."""
    try:
        if request.agent_type == "form_navigator":
            # NEW: Use solve_form_task instead of just analyzing
            result = await form_agent.solve_form_task(
                html=request.data.get("html", ""),
                prompt=request.data.get("prompt", ""),
                max_steps=request.data.get("max_steps", 12)
            )
            return AgentResponse(
                success=True,
                agent="form_navigator",
                result={"actions": result}  # Return action list
            )
        
        elif request.agent_type == "screenshot_analyzer":
            # NEW: Use solve_from_screenshot
            result = await screenshot_agent.solve_from_screenshot(
                screenshot_data=request.data.get("screenshot"),
                prompt=request.data.get("prompt", ""),
                max_steps=request.data.get("max_steps", 12)
            )
            return AgentResponse(
                success=True,
                agent="screenshot_analyzer",
                result={"actions": result}
            )
        
        else:
            raise ValueError(f"Unknown agent type: {request.agent_type}")
    
    except Exception as e:
        logger.error(f"Error in agent execution: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            agent=request.agent_type,
            result=None,
            error=str(e)
        )
```

### Step 4: Fix Export

**File:** `agents/__init__.py`

```python
from .form_navigator import FormNavigationAgent, ...
from .screenshot_analyzer import ScreenshotAnalyzerAgent  # ADD THIS

__all__ = [
    "FormNavigationAgent",
    # ... other exports ...
    "ScreenshotAnalyzerAgent",  # ADD THIS
]
```

---

## Testing Before Deploy

```bash
cd /tmp/skibbot-sn36-agents

# Test import
python3 -c "from agents import FormNavigationAgent, ScreenshotAnalyzerAgent; print('✅')"

# Test new methods exist
python3 << 'EOF'
from agents.form_navigator import FormNavigationAgent
import inspect

form = FormNavigationAgent()
assert hasattr(form, 'solve_form_task'), "Missing solve_form_task"
assert inspect.iscoroutinefunction(form.solve_form_task), "solve_form_task not async"

# Test method returns actions list
import asyncio
result = asyncio.run(form.solve_form_task(
    html='<form><input name="email"></form>',
    prompt='Fill email'
))
assert isinstance(result, list), f"Expected list, got {type(result)}"
assert all(isinstance(a, dict) for a in result), "Actions should be dicts"
assert all('type' in a for a in result), "All actions need 'type' field"
print("✅ All tests pass")
EOF
```

---

## Timeline to TAO Earnings

| Time | Action | Expected |
|---|---|---|
| **Now** | Fix export + add wrapper methods | Ready to deploy |
| **+30 min** | Deploy to GitHub | Validators see new commit |
| **+2-12 hrs** | Validators run next cycle | First evaluation of new code |
| **+12-24 hrs** | TAO assigned | Non-zero scores start flowing |

**Expected Success Rate:**
- Easy tasks (fill form, click button): 70-90%
- Medium tasks (multi-step): 40-60%
- Hard tasks (complex logic): 10-30%
- **Average:** 40-60%

**TAO Earnings (Estimate):**
- 40-60% success rate × 2-3 TAO/task × 10 tasks/cycle = 8-18 TAO/cycle
- Cycle frequency: ~12-24 hours
- Monthly: ~10-30 TAO × $30 = **$300-900/month**

---

## Final Recommendation

**DO THIS NOW:**
1. ✅ Fix export (2 min)
2. ✅ Add `solve_form_task` wrapper (10 min)
3. ✅ Deploy (5 min)
4. ✅ Monitor results

**THEN (within 24 hours):**
5. Add LLM-based action generator for robustness
6. Improve element detection accuracy
7. Add retry logic for failed actions

This gets you earning TAO immediately while you refine agents over time.

---

**Investigation Complete. Ready to implement.**
