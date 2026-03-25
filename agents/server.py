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
    """
    try:
        if request.agent_type == "form_navigator":
            logger.info(f"Form Navigator task: {request.task}")
            result = await handle_form_navigation_request(request.task, request.data)
            return AgentResponse(
                success=True,
                agent="form_navigator",
                result=result
            )
        
        elif request.agent_type == "screenshot_analyzer":
            logger.info(f"Screenshot Analyzer task: {request.task}")
            # Call the async analyze method
            result = await screenshot_agent.analyze_screenshot(
                screenshot_data=request.data.get("screenshot"),
                analysis_type=request.task
            )
            return AgentResponse(
                success=True,
                agent="screenshot_analyzer",
                result=result
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
