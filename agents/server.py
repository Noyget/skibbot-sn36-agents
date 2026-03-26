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
        logger.info(f"Received /act request: task_type={body.get('task', {}).get('type', '?')}, step={body.get('step_index', 0)}")
        
        # Extract parameters
        task = body.get("task", {})
        snapshot_html = body.get("snapshot_html", "")
        screenshot = body.get("screenshot")  # base64-encoded screenshot
        url = body.get("url", "")
        step_index = body.get("step_index", 0)
        history = body.get("history", [])
        
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
                    max_steps=1  # One action per call
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
                    max_steps=1  # One action per call
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


def _clean_actions(actions: list) -> list:
    """
    Clean actions to ensure they match expected format.
    Removes extra fields that might confuse validators.
    
    Expected fields:
    - type: action type
    - selector: for click
    - text: for type  
    - key: for press
    - timeout: for wait
    """
    cleaned = []
    
    for action in actions:
        if not isinstance(action, dict):
            continue
        
        action_type = action.get("type", "").lower()
        if not action_type:
            continue
        
        # Build clean action with only relevant fields
        clean_action = {"type": action_type}
        
        if action_type == "click":
            selector = action.get("selector")
            if selector:
                clean_action["selector"] = str(selector)
            else:
                continue  # Skip click without selector
        
        elif action_type == "type":
            text = action.get("text") or action.get("value")
            if text is not None:
                clean_action["text"] = str(text)
            else:
                continue  # Skip type without text
        
        elif action_type == "press" or action_type == "key":
            clean_action["type"] = "press"
            key = action.get("key")
            if key:
                clean_action["key"] = str(key)
            else:
                continue
        
        elif action_type == "wait":
            timeout = action.get("timeout", 5)
            try:
                clean_action["timeout"] = float(timeout)
            except (ValueError, TypeError):
                clean_action["timeout"] = 5.0
        
        # All other action types pass through with minimal validation
        
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
        port=8000,
        log_level="info"
    )
