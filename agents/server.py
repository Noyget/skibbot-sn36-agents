"""
FastAPI server for Autoppia SN36 agents.
Implements the /act endpoint compatible with ApifiedWebAgent.

ApifiedWebAgent makes HTTP POST requests to this endpoint with:
- task: Task object (JSON-serializable)
- snapshot_html: HTML snapshot as string
- screenshot: Screenshot as base64 string
- url: Current URL
- step_index: Step number
- history: List of previous actions taken
"""

import asyncio
import json
import logging
import re
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Request
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SkibBot Web Agents", version="1.0.0")

# Import agents
try:
    from agents.form_navigator import FormNavigationAgent
    from agents.screenshot_analyzer import ScreenshotAnalyzerAgent
except ImportError:
    logger.warning("Could not import agents locally, will handle via generic endpoints")
    FormNavigationAgent = None
    ScreenshotAnalyzerAgent = None


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "SkibBot Web Agents"}


@app.post("/act")
async def act(request: Request) -> list:
    """
    Main /act endpoint that ApifiedWebAgent calls.
    
    This endpoint receives task information and must return a list of actions.
    Actions are dictionaries with keys like:
    - type: "click", "type", "wait", "press", etc.
    - selector: CSS selector for click actions
    - text: text to type for type actions
    - key: key name for press actions
    - timeout: timeout in seconds for wait actions
    
    Returns empty list if agent cannot generate actions (safe fallback).
    """
    try:
        # Get request body as JSON
        body = await request.json()
        # Extract parameters
        task = body.get("task", {})
        # Handle case where task might be a string instead of dict
        if isinstance(task, str):
            task = {"query": task}
        
        snapshot_html = body.get("snapshot_html", "")
        screenshot = body.get("screenshot")  # base64-encoded screenshot
        url = body.get("url", "")
        step_index = body.get("step_index", 0)
        history = body.get("history", [])
        
        logger.info(f"Received /act request: task_type={task.get('type', '?')}, step={step_index}")
        
        # Get task prompt/description
        task_prompt = task.get("query") or task.get("description") or "Complete the task"
        
        # Route to agent based on available data
        actions = []
        
        # Try form navigation if we have HTML
        if snapshot_html and FormNavigationAgent:
            try:
                agent = FormNavigationAgent()
                actions = await agent.solve_form_task(
                    html=snapshot_html,
                    prompt=task_prompt,
                    max_steps=12  # ✅ FIX #1: Changed from 1 to 12 (CRITICAL)
                )
                if actions:
                    logger.info(f"Form navigator returned {len(actions)} action(s)")
                    return _clean_actions(actions)
            except Exception as e:
                logger.warning(f"Form navigator failed: {e}")
        
        # Fallback: try screenshot analysis if we have screenshot
        if screenshot and ScreenshotAnalyzerAgent:
            try:
                agent = ScreenshotAnalyzerAgent()
                actions = await agent.solve_from_screenshot(
                    screenshot_data=screenshot,
                    prompt=task_prompt,
                    max_steps=12  # ✅ FIX #1: Changed from 1 to 12 (CRITICAL)
                )
                if actions:
                    logger.info(f"Screenshot analyzer returned {len(actions)} action(s)")
                    return _clean_actions(actions)
            except Exception as e:
                logger.warning(f"Screenshot analyzer failed: {e}")
        
        # No actions generated
        logger.info("No actions generated, returning empty list")
        return []
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in /act: {e}", exc_info=True)
        return []


def _normalize_selector(selector_value) -> dict:
    """
    ✅ FIX #3: Convert string CSS selector to Selector object format
    that validators expect (Selector with type, attribute, value).
    
    Examples:
    - "[name='email']" → {"type": "attributeValueSelector", "attribute": "name", "value": "email"}
    - "#submit-btn" → {"type": "attributeValueSelector", "attribute": "id", "value": "submit-btn"}
    - ".btn-primary" → {"type": "attributeValueSelector", "attribute": "class", "value": "btn-primary"}
    - "button[type='submit']" → handled as complex selector (pass-through)
    """
    if isinstance(selector_value, dict):
        # Already a Selector object, return as-is
        return selector_value
    
    if isinstance(selector_value, list):
        # List of selectors (from alternative_selectors)
        # Convert each one
        return [_normalize_selector(s) for s in selector_value]
    
    selector_str = str(selector_value).strip()
    
    # Handle ID selectors: #id-name
    if selector_str.startswith("#"):
        return {
            "type": "attributeValueSelector",
            "attribute": "id",
            "value": selector_str[1:],
            "case_sensitive": False
        }
    
    # Handle class selectors: .class-name
    if selector_str.startswith("."):
        return {
            "type": "attributeValueSelector",
            "attribute": "class",
            "value": selector_str[1:],
            "case_sensitive": False
        }
    
    # Handle attribute selectors: [name='value'], [type='submit'], etc.
    # Pattern: [attribute='value'] or [attribute="value"]
    attr_match = None
    if "[" in selector_str and "]" in selector_str:
        import re
        # Try to match [attr='value'] or [attr="value"]
        match = re.match(r'\[([^=\]]+)=["\']?([^"\'"\]]+)["\']?\]', selector_str)
        if match:
            attr_name, attr_value = match.groups()
            return {
                "type": "attributeValueSelector",
                "attribute": attr_name.strip(),
                "value": attr_value.strip(),
                "case_sensitive": False
            }
    
    # Handle XPath selectors: //, (//
    if selector_str.startswith("//") or selector_str.startswith("(//"):
        return {
            "type": "xpathSelector",
            "value": selector_str,
            "case_sensitive": False
        }
    
    # Complex selectors (tag[attr='val'], multiple conditions, etc.)
    # Pass through as-is for validator to handle
    if selector_str:
        return {
            "type": "cssSelector",
            "value": selector_str,
            "case_sensitive": False
        }
    
    # Fallback: empty selector
    return {"type": "unknown", "value": ""}


def _clean_actions(actions: list) -> list:
    """
    ✅ FIX #2: Normalize action format for validators.
    - Convert "value" field to "text" for type/input actions (CRITICAL)
    - Convert string selectors to Selector objects (CRITICAL)
    - Preserve metadata: alternative_selectors, retry_count, retry_delay, etc.
    - Handle wait_for_element as first-class action type
    
    Rich metadata fields (from FormNavigator):
    - alternative_selectors: fallback selectors for robust targeting
    - retry_count: number of retries for transient failures
    - retry_delay: delay in ms between retries
    - visible: require element visibility before action
    - clickable: require element to be clickable
    - reason: why this action is being taken
    """
    cleaned = []
    
    for action in actions:
        if not isinstance(action, dict):
            continue
        
        action_type = action.get("type", "").lower()
        if not action_type:
            continue
        
        # Start with type (always required)
        clean_action = {"type": action_type}
        
        # Copy all top-level fields that validators recognize
        for field in [
            "selector",           # Will be normalized to Selector object
            "alternative_selectors",  # Fallback selectors
            "text",              # Text to input (preferred)
            "value",             # Will be converted to "text" (legacy support)
            "key",               # Key to press
            "timeout",           # Timeout in ms
            "visible",           # Require visibility
            "clickable",         # Require clickability
            "retry_count",       # Number of retries
            "retry_delay",       # Delay between retries in ms
            "reason",            # Why this action (debugging/analysis)
        ]:
            if field not in action:
                continue
            
            value = action[field]
            if value is None:
                continue
            
            # ✅ FIX #2: Handle "value" → "text" conversion for input actions
            if field == "value":
                # For type/input actions, use "text" not "value"
                if action_type in ["type", "input", "typeaction"]:
                    clean_action["text"] = str(value)
                    continue  # Don't add "value" field
                else:
                    # For other actions, keep "value" if present
                    clean_action[field] = str(value)
                    continue
            
            # ✅ FIX #3: Normalize selector to Selector object format
            if field == "selector":
                normalized = _normalize_selector(value)
                clean_action[field] = normalized
                continue
            
            if field == "alternative_selectors":
                # Normalize each alternative selector
                if isinstance(value, list):
                    clean_action[field] = [_normalize_selector(s) for s in value]
                else:
                    clean_action[field] = _normalize_selector(value)
                continue
            
            # Type conversion for known numeric fields
            if field in ["timeout", "retry_delay", "retry_count"]:
                try:
                    clean_action[field] = float(value) if field == "timeout" else int(value)
                except (ValueError, TypeError):
                    pass  # Skip invalid numeric values
                continue
            
            if field in ["visible", "clickable"]:
                clean_action[field] = bool(value)  # Ensure boolean
                continue
            
            # All other fields: pass through as strings
            clean_action[field] = str(value) if value is not None else value
        
        # Minimal validation: some actions need core fields
        if action_type == "click" and "selector" not in clean_action:
            continue  # Skip click without selector
        
        if action_type in ["type", "input", "typeaction"] and "text" not in clean_action and "value" not in clean_action:
            continue  # Skip input without text
        
        if action_type in ["press", "key"] and "key" not in clean_action:
            continue  # Skip key press without key
        
        # wait_for_element now supported (was previously missing)
        if action_type == "wait_for_element" and "selector" not in clean_action:
            continue  # Skip wait without selector
        
        cleaned.append(clean_action)
    
    return cleaned


@app.get("/status")
async def status():
    """Status endpoint"""
    return {
        "service": "SkibBot Web Agents",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
