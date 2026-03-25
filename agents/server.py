"""
FastAPI server for Autoppia SN36 agents.
Runs in Docker container to handle validator requests.
"""

import asyncio
import json
import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from .form_navigator import FormNavigationAgent, handle_form_navigation_request
from .screenshot_analyzer import ScreenshotAnalyzerAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SkibBot Web Agents", version="1.0.0")

# Initialize agents
form_agent = FormNavigationAgent()
screenshot_agent = ScreenshotAnalyzerAgent()


class AgentRequest(BaseModel):
    """Request format for agent calls"""
    agent_type: str  # "form_navigator" or "screenshot_analyzer"
    task: str
    data: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response format from agents"""
    success: bool
    agent: str
    result: Any
    error: str = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agents": ["form_navigator", "screenshot_analyzer"]}


@app.post("/act")
async def act(request: AgentRequest) -> AgentResponse:
    """
    Main agent endpoint for handling validator requests.
    Supports: form_navigator, screenshot_analyzer
    
    NEW: Returns action lists instead of analysis for direct task solving.
    Validators execute these actions in a browser to complete tasks.
    """
    try:
        if request.agent_type == "form_navigator":
            logger.info(f"Form Navigator task: {request.task}")
            
            # NEW: Use solve_form_task to generate actions
            html = request.data.get("html", "")
            prompt = request.data.get("prompt", request.task)
            max_steps = request.data.get("max_steps", 12)
            
            actions = await form_agent.solve_form_task(
                html=html,
                prompt=prompt,
                max_steps=max_steps
            )
            
            return AgentResponse(
                success=True,
                agent="form_navigator",
                result={
                    "actions": actions,
                    "action_count": len(actions),
                    "status": "ready_for_execution"
                }
            )
        
        elif request.agent_type == "screenshot_analyzer":
            logger.info(f"Screenshot Analyzer task: {request.task}")
            
            # NEW: Use solve_from_screenshot to generate actions
            screenshot_data = request.data.get("screenshot")
            prompt = request.data.get("prompt", request.task)
            max_steps = request.data.get("max_steps", 12)
            
            if not screenshot_data:
                return AgentResponse(
                    success=False,
                    agent="screenshot_analyzer",
                    result=None,
                    error="screenshot data required"
                )
            
            actions = await screenshot_agent.solve_from_screenshot(
                screenshot_data=screenshot_data,
                prompt=prompt,
                max_steps=max_steps
            )
            
            return AgentResponse(
                success=True,
                agent="screenshot_analyzer",
                result={
                    "actions": actions,
                    "action_count": len(actions),
                    "status": "ready_for_execution"
                }
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


@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {
                "name": "form_navigator",
                "description": "Autonomous form structure extraction and navigation",
                "endpoint": "/act"
            },
            {
                "name": "screenshot_analyzer",
                "description": "Website screenshot analysis and element detection",
                "endpoint": "/act"
            }
        ]
    }


@app.get("/status")
async def status():
    """Get agent status"""
    return {
        "name": "SkibBot Web Agents",
        "version": "1.0.0",
        "agents_ready": ["form_navigator", "screenshot_analyzer"],
        "timestamp": asyncio.get_event_loop().time()
    }


if __name__ == "__main__":
    # Run server on port 8000 (default for Docker)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
