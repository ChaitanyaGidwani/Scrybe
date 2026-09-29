"""Scrybe FastAPI Application — Enhanced with A2A Protocol.

Provides:
- REST endpoints for pipeline execution and report retrieval
- WebSocket endpoint for real-time pipeline progress
- A2A agent management and discovery endpoints
- SSE streaming for task progress
- Agent health monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config.settings import settings
from scrybe.api.routes import router
from scrybe.api.websocket import progress_manager
from scrybe.logging_config import setup_logging

setup_logging(settings.log_level)

app = FastAPI(
    title="Scrybe API",
    description=(
        "Scrybe — Autonomous Multi-Agent Web Intelligence System with A2A Protocol. "
        "Scrape, extract, validate, analyze, and generate cited market intelligence reports "
        "using decoupled A2A agent-to-agent communication."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix="/api/v1")


# ── Health Check ─────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint with A2A agent status."""
    return {
        "status": "healthy",
        "service": "scrybe-api",
        "version": "0.2.0",
        "protocol": "a2a/1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "websocket_clients": progress_manager.connected_count,
    }


# ── WebSocket for Real-Time Pipeline Progress ───────────────────

@app.websocket("/ws/pipeline")
async def websocket_pipeline_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline progress streaming.

    Clients receive JSON messages for each pipeline stage transition:
    {
        "pipeline_id": "pipe_20240929_...",
        "agent": "reader|analyst|strategist|...",
        "event": "starting|completed|failed",
        "timestamp": "ISO8601",
        ...stage-specific data...
    }
    """
    await progress_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; receive pings or commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket)


# ── A2A Agent Discovery ─────────────────────────────────────────

@app.get("/api/v1/agents")
async def list_agents():
    """List all registered A2A agents with their capabilities."""
    from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
    return {
        "protocol": "a2a/1.0",
        "agents": [card.model_dump(mode="json") for card in ALL_AGENT_CARDS],
        "count": len(ALL_AGENT_CARDS),
    }


@app.get("/api/v1/agents/{agent_name}/card")
async def get_agent_card(agent_name: str):
    """Get the A2A Agent Card for a specific agent."""
    from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
    for card in ALL_AGENT_CARDS:
        if card.name.lower() == agent_name.lower():
            return JSONResponse(card.model_dump(mode="json"))
    raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")


# ── A2A Pipeline Execution ───────────────────────────────────────

class A2APipelineRequest(BaseModel):
    sources_config_path: Optional[str] = None
    mode: str = "in_process"


@app.post("/api/v1/a2a/run")
async def trigger_a2a_pipeline(
    request: A2APipelineRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger a pipeline run using the A2A protocol.

    The pipeline executes asynchronously in the background.
    Connect to ws://host/ws/pipeline for real-time progress.
    """
    from scrybe.a2a.orchestrator import A2AOrchestrator

    orchestrator = A2AOrchestrator(
        settings=settings,
        mode=request.mode,
        progress_callback=progress_manager.progress_callback,
    )

    pipeline_id = orchestrator.pipeline_id

    async def run_background():
        try:
            await orchestrator.run_pipeline(request.sources_config_path)
        except Exception as e:
            logging.getLogger("scrybe.api").error(f"A2A pipeline failed: {e}")

    background_tasks.add_task(run_background)

    return {
        "status": "accepted",
        "pipeline_id": pipeline_id,
        "protocol": "a2a/1.0",
        "mode": request.mode,
        "message": f"A2A pipeline {pipeline_id} started. Connect to ws://host/ws/pipeline for progress.",
    }


# ── Pipeline Progress History ────────────────────────────────────

@app.get("/api/v1/a2a/progress")
async def get_pipeline_progress(limit: int = 100):
    """Get recent pipeline progress events."""
    events = progress_manager.event_history[-limit:]
    return {
        "events": events,
        "count": len(events),
        "websocket_clients": progress_manager.connected_count,
    }


# ── Static Frontend SPA Mount ────────────────────────────────────

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    assets_dir = _FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(_FRONTEND_DIST / "index.html")

