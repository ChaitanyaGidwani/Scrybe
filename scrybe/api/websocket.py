"""WebSocket handler for real-time pipeline progress streaming.

Provides a WebSocket endpoint that the frontend connects to for
live updates during pipeline execution. Each connected client
receives JSON messages for every pipeline stage transition.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("websocket")


class PipelineProgressManager:
    """Manages WebSocket connections for real-time pipeline updates.

    Maintains a set of active connections and broadcasts pipeline
    progress events to all connected clients.

    Usage:
        manager = PipelineProgressManager()

        # In WebSocket handler:
        await manager.connect(websocket)

        # From orchestrator progress callback:
        await manager.broadcast(event_data)
    """

    def __init__(self):
        self._connections: Set = set()
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    async def connect(self, websocket) -> None:
        """Register a new WebSocket connection.

        Sends the current event history to catch up the new client.
        """
        await websocket.accept()
        self._connections.add(websocket)

        # Send event history for catch-up
        for event in self._event_history[-50:]:
            try:
                await websocket.send_json(event)
            except Exception:
                break

        logger.info(f"WebSocket client connected. Total: {len(self._connections)}")

    def disconnect(self, websocket) -> None:
        """Remove a WebSocket connection."""
        self._connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, event: Dict[str, Any]) -> None:
        """Broadcast an event to all connected WebSocket clients.

        Failed connections are automatically cleaned up.
        """
        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Broadcast to all connections
        dead_connections = set()
        for ws in self._connections:
            try:
                await ws.send_json(event)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        self._connections -= dead_connections

    def progress_callback(self, agent: str, event: str, data: Dict[str, Any]) -> None:
        """Synchronous callback adapter for the A2A orchestrator.

        The orchestrator calls this synchronously; we schedule the
        broadcast onto the event loop.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(data))
        except RuntimeError:
            # No running loop — store the event for later
            if "timestamp" not in data:
                data["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._event_history.append(data)

    @property
    def connected_count(self) -> int:
        return len(self._connections)

    @property
    def event_history(self) -> List[Dict[str, Any]]:
        return list(self._event_history)


# Global instance shared across the application
progress_manager = PipelineProgressManager()
