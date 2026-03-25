# SN36 Quick Fix Reference — Copy-Paste Solutions

**Use this for rapid implementation**

---

## Fix #1: Export ScreenshotAnalyzerAgent (2 min)

**File:** `agents/__init__.py`

**Replace entire file with:**
```python
"""
Bittensor Subnet 36 Autonomous Web Agents - Agent Implementations

Day 5: Form Navigation Agent
- Autonomous form structure extraction and navigation
- Multi-step form handling with state persistence
- <10ms performance, 95%+ confidence scoring
"""

from .form_navigator import (
    FormNavigationAgent,
    FormNavigationResult,
    FormState,
    FormFieldInfo,
    FormStep,
    NavigationPath,
    NavigationAction,
    FieldType,
    ValidationStatus,
    NavigationType,
    FormFlowType,
    handle_form_navigation_request,
)
from .screenshot_analyzer import ScreenshotAnalyzerAgent  # ADD THIS LINE

__all__ = [
    "FormNavigationAgent",
    "FormNavigationResult",
    "FormState",
    "FormFieldInfo",
    "FormStep",
    "NavigationPath",
    "NavigationAction",
    "FieldType",
    "ValidationStatus",
    "NavigationType",
    "FormFlowType",
    "handle_form_navigation_request",
    "ScreenshotAnalyzerAgent",  # ADD THIS LINE
]

__version__ = "1.0.0"
__author__ = "Bittensor Subnet 36"
```

---

## Fix #2: Add Action Generator to FormNavigationAgent (10 min)

**File:** `agents/form_navigator.py`

**Add this method at the end of the FormNavigationAgent class:**

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
            
            # Pattern matching for email
            email_match = re.search(r'email[:\s]+([^\s,\.]+@[^\s,\.]+)', prompt_lower)
            if email_match:
                field_values['email'] = email_match.group(1)
            
            # Pattern matching for name
            name_match = re.search(r'name[:\s]+([^,\.]+)', prompt_lower)
            if name_match:
                field_values['name'] = name_match.group(1).strip()
            
            # Pattern matching for phone
            phone_match = re.search(r'phone[:\s]+([0-9\-\+\(\)]+)', prompt_lower)
            if phone_match:
                field_values['phone'] = phone_match.group(1).strip()
            
            # Step 3: Generate click + fill actions
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
            
            # Step 4: Find and click submit
            for path in analysis.navigation_paths:
                if "submit" in path.target_selector.lower():
                    actions.append({
                        "type": "click",
                        "selector": path.target_selector
                    })
                    break
            
            return actions[:max_steps]
        
        except Exception as e:
            logger.error(f"Error generating form actions: {e}")
            return []
```

---

## Fix #3: Add Action Generator to ScreenshotAnalyzerAgent (10 min)

**File:** `agents/screenshot_analyzer.py`

**Add this method at the end of the ScreenshotAnalyzerAgent class:**

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
            List of actions: [{"type": "click", ...}, ...]
        """
        try:
            # Save screenshot temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(screenshot_data)
                tmp_path = tmp.name
            
            # Analyze screenshot
            analysis = await self.analyze_screenshot(tmp_path, enable_vision=True)
            
            actions = []
            prompt_lower = prompt.lower()
            
            # Find elements matching task
            for element in analysis.elements:
                element_text = (element.text or "").lower()
                element_type = (element.type or "").lower()
                
                # Look for submit buttons
                if any(word in element_text for word in ['submit', 'send', 'continue', 'next']):
                    if "button" in element_type or "submit" in element_text:
                        actions.append({
                            "type": "click",
                            "selector": element.selector or f"button:contains('{element.text}')",
                            "text": element.text
                        })
                
                # Look for input fields to fill
                elif "input" in element_type and "fill" in prompt_lower:
                    actions.append({
                        "type": "click",
                        "selector": element.selector or f"[name='{element.element_id}']"
                    })
                    # Add generic fill (task-specific fill would need better matching)
                    actions.append({
                        "type": "input",
                        "selector": element.selector or f"[name='{element.element_id}']",
                        "value": "test_value"
                    })
            
            # Clean up
            import os
            os.unlink(tmp_path)
            
            return actions[:max_steps]
        
        except Exception as e:
            logger.error(f"Error solving from screenshot: {e}")
            return []
```

---

## Fix #4: Update server.py /act endpoint (5 min)

**File:** `agents/server.py`

**Replace the /act endpoint with:**

```python
@app.post("/act")
async def act(request: AgentRequest) -> AgentResponse:
    """
    Main agent endpoint for handling validator requests.
    Supports: form_navigator, screenshot_analyzer
    """
    try:
        if request.agent_type == "form_navigator":
            logger.info(f"Form Navigator task: {request.task}")
            # NEW: Call solve_form_task instead
            result = await form_agent.solve_form_task(
                html=request.data.get("html", ""),
                prompt=request.data.get("prompt", ""),
                max_steps=request.data.get("max_steps", 12)
            )
            return AgentResponse(
                success=True,
                agent="form_navigator",
                result={"actions": result}
            )
        
        elif request.agent_type == "screenshot_analyzer":
            logger.info(f"Screenshot Analyzer task: {request.task}")
            # NEW: Call solve_from_screenshot instead
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

---

## Testing (Before Deploy)

```bash
cd /tmp/skibbot-sn36-agents

# Test 1: Imports work
python3 -c "from agents import FormNavigationAgent, ScreenshotAnalyzerAgent; print('✅ Imports OK')"

# Test 2: New methods exist
python3 << 'EOF'
from agents.form_navigator import FormNavigationAgent
import asyncio

agent = FormNavigationAgent()

# Test method exists
assert hasattr(agent, 'solve_form_task'), "Missing solve_form_task"

# Test async
import inspect
assert inspect.iscoroutinefunction(agent.solve_form_task), "Not async"

print("✅ Form agent methods OK")
EOF

# Test 3: Screenshot agent
python3 << 'EOF'
from agents.screenshot_analyzer import ScreenshotAnalyzerAgent

agent = ScreenshotAnalyzerAgent()
assert hasattr(agent, 'solve_from_screenshot'), "Missing solve_from_screenshot"

print("✅ Screenshot agent methods OK")
EOF

# Test 4: Method execution
python3 << 'EOF'
from agents.form_navigator import FormNavigationAgent
import asyncio

async def test():
    agent = FormNavigationAgent()
    result = await agent.solve_form_task(
        html='<form><input name="email"></form>',
        prompt='Fill email with test@example.com'
    )
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    print(f"✅ Returns list: {len(result)} actions")
    return result

actions = asyncio.run(test())
for action in actions:
    assert isinstance(action, dict), "Action not dict"
    assert 'type' in action, "Action missing 'type'"

print("✅ All tests pass")
EOF
```

---

## Deployment

```bash
cd ~/.openclaw/workspace/skibbot-sn36-agents

# 1. Stage changes
git add agents/__init__.py agents/form_navigator.py agents/screenshot_analyzer.py agents/server.py

# 2. Commit
git commit -m "Add action generators: solve_form_task + solve_from_screenshot"

# 3. Push
git push origin main

# 4. Verify commit is live
git log -1 --oneline

# 5. Check GitHub
# Go to: https://github.com/Noyget/skibbot-sn36-agents
# Verify your commit appears in commit history
```

---

## Timeline

| Step | Time | Action |
|---|---|---|
| 1 | 5 min | Make 4 code changes |
| 2 | 5 min | Test locally (run test commands above) |
| 3 | 5 min | Git commit + push |
| 4 | 2-12 hrs | Validators discover new commit |
| 5 | 12-24 hrs | First evaluation results |
| 6 | 24 hrs+ | TAO starts flowing (if >0% success) |

---

## Success Metrics

**You'll know it's working when:**
- [ ] Commit appears on GitHub
- [ ] Miner announces new commit hash to validators
- [ ] Next validator cycle starts (check logs)
- [ ] Leaderboard shows non-zero eval_score
- [ ] TAO earnings appear (may take 24-48 hrs)

---

## Troubleshooting

**Problem:** Tests fail on imports
```
Solution: Verify you're in the repo root directory
cd /tmp/skibbot-sn36-agents  # Not ~/.openclaw/workspace/...
```

**Problem:** New methods don't exist
```
Solution: Verify you pasted the ENTIRE method with correct indentation
Use: python3 -c "from agents.form_navigator import FormNavigationAgent; print(dir(FormNavigationAgent()))"
Check output includes: solve_form_task
```

**Problem:** Commit doesn't push
```
Solution: Check git remote
git remote -v
Should show: origin https://github.com/Noyget/skibbot-sn36-agents.git
git branch -vv
Should show: main tracking origin/main
```

---

**Ready to implement?**  
Use the 4 fixes above in order (1-4).  
Test with the Test section.  
Deploy with Deployment commands.  
Done.
