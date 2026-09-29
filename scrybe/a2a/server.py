"""A2A Protocol Server — Base class for wrapping agents as A2A services.

Turns any Scrybe agent into an A2A-compliant HTTP server that:
1. Serves an Agent Card at /.well-known/agent-card.json
2. Accepts JSON-RPC 2.0 requests (SendMessage, GetTask, CancelTask)
3. Manages task lifecycle (submitted → working → completed/failed)
4. Supports Server-Sent Events (SSE) for streaming task progress

Each agent server runs on its own port and can be discovered
by the A2A orchestrator via its Agent Card.
"""

import asyncio
import json
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional

from scrybe.a2a.models import (
    AgentCard,
    Artifact,
    DataPart,
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("a2a_server")


# Type alias for agent handler functions
AgentHandler = Callable[[Task], Coroutine[Any, Any, Task]]


class A2AServer:
    """Base A2A protocol server that wraps a Scrybe agent.

    Provides the JSON-RPC 2.0 interface for task management and
    serves the Agent Card for discovery. Designed to be mounted
    into a FastAPI application or run standalone.

    Usage:
        server = A2AServer(agent_card=my_card, handler=my_agent_handler)
        # Mount into FastAPI:
        server.mount(app, prefix="/agents/reader")
    """

    def __init__(
        self,
        agent_card: AgentCard,
        handler: AgentHandler,
        max_concurrent_tasks: int = 5,
    ):
        self.agent_card = agent_card
        self.handler = handler
        self.max_concurrent_tasks = max_concurrent_tasks

        # Task storage (in-memory; production would use Redis/DB)
        self._tasks: Dict[str, Task] = {}
        self._task_events: Dict[str, asyncio.Event] = {}  # For SSE notifications
        self._active_count = 0

    # ── Agent Card Discovery ─────────────────────────────────────

    def get_agent_card(self) -> Dict[str, Any]:
        """Return the Agent Card as a JSON-serializable dict."""
        return self.agent_card.model_dump(mode="json")

    # ── JSON-RPC 2.0 Dispatcher ──────────────────────────────────

    async def handle_jsonrpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a JSON-RPC 2.0 request to the appropriate handler.

        Supported methods:
            - agent/sendMessage: Submit a new task or continue an existing one
            - agent/getTask: Retrieve task status and artifacts
            - agent/cancelTask: Cancel a running task
            - agent/listTasks: List all tasks (with optional state filter)
        """
        try:
            request = JsonRpcRequest(**request_data)
        except Exception as e:
            return JsonRpcResponse(
                error={"code": -32700, "message": f"Parse error: {e}"},
            ).model_dump(mode="json")

        method_handlers = {
            "agent/sendMessage": self._handle_send_message,
            "agent/getTask": self._handle_get_task,
            "agent/cancelTask": self._handle_cancel_task,
            "agent/listTasks": self._handle_list_tasks,
        }

        handler_fn = method_handlers.get(request.method)
        if not handler_fn:
            return JsonRpcResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {request.method}"},
            ).model_dump(mode="json")

        try:
            result = await handler_fn(request.params)
            return JsonRpcResponse(
                id=request.id,
                result=result,
            ).model_dump(mode="json")
        except Exception as e:
            logger.error(f"JSON-RPC handler error: {e}", exc_info=True)
            return JsonRpcResponse(
                id=request.id,
                error={"code": -32603, "message": str(e)},
            ).model_dump(mode="json")

    # ── Method Handlers ──────────────────────────────────────────

    async def _handle_send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent/sendMessage — create or continue a task.

        If task_id is provided and the task exists, append the message.
        Otherwise, create a new task.
        """
        # Check capacity
        if self._active_count >= self.max_concurrent_tasks:
            raise RuntimeError(
                f"Agent busy: {self._active_count}/{self.max_concurrent_tasks} tasks active"
            )

        # Build the message
        message_data = params.get("message", {})
        message = self._build_message(message_data)

        # Get or create task
        task_id = params.get("task_id")
        if task_id and task_id in self._tasks:
            task = self._tasks[task_id]
            if task.is_terminal:
                raise RuntimeError(f"Task {task_id} is already in terminal state: {task.status.state}")
            task.add_message(message)
        else:
            task = Task(
                task_id=task_id or f"task_{uuid.uuid4().hex[:12]}",
                metadata=params.get("metadata", {}),
            )
            task.add_message(message)
            self._tasks[task.task_id] = task
            self._task_events[task.task_id] = asyncio.Event()

        # Execute the agent handler asynchronously
        asyncio.create_task(self._execute_task(task))

        return task.model_dump(mode="json")

    async def _handle_get_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent/getTask — retrieve task status and artifacts."""
        task_id = params.get("task_id")
        if not task_id or task_id not in self._tasks:
            raise RuntimeError(f"Task not found: {task_id}")

        return self._tasks[task_id].model_dump(mode="json")

    async def _handle_cancel_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent/cancelTask — cancel a running task."""
        task_id = params.get("task_id")
        if not task_id or task_id not in self._tasks:
            raise RuntimeError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if task.is_terminal:
            raise RuntimeError(f"Task {task_id} is already in terminal state")

        task.cancel(params.get("reason", "Canceled by client"))
        # Signal the event for SSE listeners
        if task_id in self._task_events:
            self._task_events[task_id].set()

        return task.model_dump(mode="json")

    async def _handle_list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent/listTasks — list tasks with optional filtering."""
        state_filter = params.get("state")
        limit = params.get("limit", 50)

        tasks = list(self._tasks.values())
        if state_filter:
            tasks = [t for t in tasks if t.status.state.value == state_filter]

        # Sort by updated_at descending
        tasks.sort(key=lambda t: t.updated_at, reverse=True)
        tasks = tasks[:limit]

        return {
            "tasks": [t.model_dump(mode="json") for t in tasks],
            "total": len(self._tasks),
        }

    # ── Task Execution ───────────────────────────────────────────

    async def _execute_task(self, task: Task) -> None:
        """Execute the agent handler for a task with lifecycle management."""
        self._active_count += 1
        task.start_work(f"Agent '{self.agent_card.name}' processing...")

        logger.info(
            f"Task started: {task.task_id}",
            extra={
                "agent": self.agent_card.name,
                "step": "task_start",
                "task_id": task.task_id,
            },
        )

        try:
            # Run the actual agent logic
            completed_task = await self.handler(task)

            # If the handler didn't mark it complete, do so now
            if not completed_task.is_terminal:
                completed_task.complete()

            # Update our stored task
            self._tasks[task.task_id] = completed_task

            logger.info(
                f"Task completed: {task.task_id}",
                extra={
                    "agent": self.agent_card.name,
                    "step": "task_complete",
                    "task_id": task.task_id,
                    "artifacts_count": len(completed_task.artifacts),
                },
            )

        except Exception as e:
            task.fail(f"{type(e).__name__}: {str(e)}")
            self._tasks[task.task_id] = task
            logger.error(
                f"Task failed: {task.task_id}: {e}",
                extra={
                    "agent": self.agent_card.name,
                    "step": "task_failed",
                    "task_id": task.task_id,
                },
            )

        finally:
            self._active_count -= 1
            # Signal completion for SSE listeners
            if task.task_id in self._task_events:
                self._task_events[task.task_id].set()

    # ── SSE Streaming ────────────────────────────────────────────

    async def stream_task_updates(self, task_id: str):
        """Yield SSE events for task state changes.

        Used for real-time streaming of agent progress to the frontend.

        Yields:
            Dict with 'event' and 'data' keys for SSE formatting.
        """
        if task_id not in self._tasks:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Task not found: {task_id}"}),
            }
            return

        task = self._tasks[task_id]
        last_state = None

        while not task.is_terminal:
            if task.status.state != last_state:
                last_state = task.status.state
                yield {
                    "event": "task_update",
                    "data": json.dumps({
                        "task_id": task.task_id,
                        "state": task.status.state.value,
                        "message": task.status.message,
                        "artifacts_count": len(task.artifacts),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }),
                }

            # Wait for the next event or timeout
            event = self._task_events.get(task_id)
            if event:
                try:
                    await asyncio.wait_for(event.wait(), timeout=2.0)
                    event.clear()
                except asyncio.TimeoutError:
                    pass  # Send heartbeat

            task = self._tasks[task_id]

        # Final state
        yield {
            "event": "task_complete",
            "data": json.dumps(task.model_dump(mode="json")),
        }

    # ── Helpers ───────────────────────────────────────────────────

    def _build_message(self, data: Dict[str, Any]) -> Message:
        """Build a Message from raw request data."""
        parts = []
        for part_data in data.get("parts", []):
            part_type = part_data.get("type", "text")
            if part_type == "text":
                parts.append(TextPart(text=part_data.get("text", "")))
            elif part_type == "data":
                parts.append(DataPart(
                    data=part_data.get("data", {}),
                    mime_type=part_data.get("mime_type", "application/json"),
                ))

        return Message(
            role=data.get("role", "user"),
            parts=parts,
            metadata=data.get("metadata", {}),
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID."""
        return self._tasks.get(task_id)

    @property
    def active_tasks(self) -> int:
        """Number of currently active tasks."""
        return self._active_count

    @property
    def total_tasks(self) -> int:
        """Total number of tasks (all states)."""
        return len(self._tasks)

    # ── FastAPI Mount ────────────────────────────────────────────

    def mount(self, app, prefix: str = "") -> None:
        """Mount A2A endpoints into a FastAPI application.

        Registers:
            GET  {prefix}/.well-known/agent-card.json  → Agent Card
            POST {prefix}/                              → JSON-RPC dispatcher
            GET  {prefix}/tasks/{task_id}/stream        → SSE stream
        """
        from fastapi import Request
        from fastapi.responses import JSONResponse
        from sse_starlette.sse import EventSourceResponse

        @app.get(f"{prefix}/.well-known/agent-card.json")
        async def agent_card():
            return JSONResponse(self.get_agent_card())

        @app.post(f"{prefix}/")
        async def jsonrpc_endpoint(request: Request):
            body = await request.json()
            result = await self.handle_jsonrpc(body)
            return JSONResponse(result)

        @app.get(f"{prefix}/tasks/{{task_id}}/stream")
        async def stream_task(task_id: str):
            return EventSourceResponse(self.stream_task_updates(task_id))

        logger.info(f"A2A server mounted at {prefix} for agent '{self.agent_card.name}'")
