"""
FastAPI HTTP Server for Subnet 36 Autonomous Web Agents
Exposes /act endpoint for validator task requests

This file should be copied to: agents/server.py
And can be run via: python -m agents.server
"""

import json
import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from agents.form_navigator import (
    FormNavigationAgent,
    handle_form_navigation_request,
)
from agents.screenshot_analyzer import (
    ScreenshotAnalyzerAgent,
    act_handler as screenshot_act_handler,
)

# Initialize FastAPI app
app = FastAPI(
    title="SN36 Web Agents Server",
    description="HTTP interface for Autoppia Web Agents Subnet 36",
    version="1.0.0",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize agents
form_agent = FormNavigationAgent()

logger.info("✅ Agents initialized: FormNavigationAgent, ScreenshotAnalyzer")


# ──────────────────────── Request/Response Models ──────────────────────────


class ActRequest(BaseModel):
    """HTTP request model for /act endpoint"""

    action: str  # "extract_form", "classify_fields", "analyze_screenshot", etc.
    html: Optional[str] = None  # For form-based actions
    image_path: Optional[str] = None  # For screenshot analysis
    payload: Optional[dict] = None  # Generic payload for flexibility
    debug: bool = False


class ActResponse(BaseModel):
    """HTTP response model for /act endpoint"""

    success: bool
    action: str
    result: Optional[dict] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# ──────────────────────── Health Check ──────────────────────────────────────


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "server": "SN36 Web Agents Server",
        "agents": "FormNavigationAgent, ScreenshotAnalyzerAgent",
    }


# ──────────────────────── Main /act Endpoint ──────────────────────────────────


@app.post("/act")
async def act(request: ActRequest) -> ActResponse:
    """
    Main action endpoint for validator requests.

    Supported actions:
    - extract_form: Extract form structure from HTML
    - classify_fields: Classify form field types
    - validate_fields: Validate form fields
    - detect_paths: Detect navigation paths through form
    - detect_flow: Detect form flow type (linear, wizard, etc.)
    - assess_readiness: Assess form submission readiness
    - trace_sequence: Trace navigation sequence through form
    - detect_errors: Detect form validation errors
    - persist_state: Persist form state
    - analyze_screenshot: Analyze screenshot and detect elements
    - batch_analyze: Batch analyze multiple screenshots
    """

    import time

    start_time = time.time()

    try:
        action = request.action.lower().strip()
        debug = request.debug

        logger.info(f"[/act] Received action: {action}")

        # ──────────── Form Navigation Actions ────────────
        if action in [
            "extract_form",
            "classify_fields",
            "validate_fields",
            "detect_paths",
            "detect_flow",
            "assess_readiness",
            "trace_sequence",
            "detect_errors",
            "persist_state",
        ]:
            # Build payload from request
            payload = request.payload or {}
            
            # If html is provided directly, add it to payload
            if request.html and "html" not in payload:
                payload["html"] = request.html

            if not payload.get("html"):
                raise ValueError("Missing 'html' in payload or direct 'html' parameter for form action")

            result = await handle_form_navigation_request(
                action=action,
                payload=payload,
                agent=form_agent,
            )

            if result is None:
                raise ValueError(f"Form action '{action}' returned None")

            execution_time_ms = (time.time() - start_time) * 1000

            # Convert result to dict if it has a to_dict method
            result_dict = None
            if result is not None:
                if isinstance(result, dict):
                    result_dict = result
                elif hasattr(result, 'to_dict') and callable(result.to_dict):
                    result_dict = result.to_dict()
                elif hasattr(result, '__dict__'):
                    result_dict = result.__dict__
            
            return ActResponse(
                success=True,
                action=action,
                result=result_dict,
                execution_time_ms=execution_time_ms,
            )

        # ──────────── Screenshot Analysis Actions ────────────
        elif action in ["analyze_screenshot", "batch_analyze"]:
            if not request.image_path:
                raise ValueError("Missing 'image_path' parameter for screenshot action")

            # Call screenshot handler with proper request format
            result = await screenshot_act_handler({
                "image_path": request.image_path,
                "enable_vision": request.payload.get("enable_vision", False) if request.payload else False,
            })

            if result is None:
                raise ValueError(f"Screenshot action '{action}' returned None")

            execution_time_ms = (time.time() - start_time) * 1000

            return ActResponse(
                success=True,
                action=action,
                result=result,
                execution_time_ms=execution_time_ms,
            )

        # ──────────── Unknown Action ────────────
        else:
            raise ValueError(
                f"Unknown action: '{action}'. Supported: extract_form, classify_fields, "
                f"validate_fields, detect_paths, detect_flow, assess_readiness, trace_sequence, "
                f"detect_errors, persist_state, analyze_screenshot, batch_analyze"
            )

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        logger.error(f"[/act] Error: {str(e)}", exc_info=True)

        return ActResponse(
            success=False,
            action=request.action,
            error=str(e),
            execution_time_ms=execution_time_ms,
        )


# ──────────────────────── Startup/Shutdown ──────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 SN36 Web Agents Server starting...")
    logger.info("📡 Listening on 0.0.0.0:8000")
    logger.info("✅ Ready to receive validator requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 SN36 Web Agents Server shutting down...")


# ──────────────────────── Main Entry Point ──────────────────────────────────


def main():
    """Run the server"""
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
