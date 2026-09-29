"""A2A Protocol Client — For sending tasks to remote A2A agents.

Provides a typed client for:
1. Discovering agents via Agent Cards
2. Sending tasks via JSON-RPC 2.0 (agent/sendMessage)
3. Polling task status (agent/getTask)
4. Streaming task updates via SSE
5. Canceling tasks (agent/cancelTask)

Used by the A2A Orchestrator to coordinate the Scrybe pipeline.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from scrybe.a2a.models import (
    AgentCard,
    Artifact,
    JsonRpcRequest,
    Message,
    Task,
    TaskState,
    TextPart,
    DataPart,
)
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("a2a_client")


class A2AClient:
    """Client for communicating with A2A-compliant agent servers.

    Handles JSON-RPC 2.0 request/response, agent discovery,
    task submission, polling, and SSE streaming.

    Usage:
        client = A2AClient()
        card = await client.discover("http://localhost:8001")
        task = await client.send_task(
            agent_url="http://localhost:8001",
            message=Message().add_text("Scrape openai.com/pricing"),
        )
        result = await client.wait_for_completion(agent_url, task.task_id)
    """

    def __init__(
        self,
        timeout: float = 120.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ── Agent Discovery ──────────────────────────────────────────

    async def discover(self, agent_url: str) -> AgentCard:
        """Discover an agent by fetching its Agent Card.

        Args:
            agent_url: Base URL of the A2A agent server.

        Returns:
            Validated AgentCard object.

        Raises:
            httpx.HTTPError: If the agent is unreachable.
        """
        card_url = f"{agent_url.rstrip('/')}/.well-known/agent-card.json"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(card_url)
            response.raise_for_status()
            card_data = response.json()

        card = AgentCard(**card_data)
        logger.info(
            f"Discovered agent: {card.name} at {agent_url}",
            extra={"agent": "a2a_client", "step": "discover"},
        )
        return card

    # ── Task Submission ──────────────────────────────────────────

    async def send_task(
        self,
        agent_url: str,
        message: Message,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Send a message to an agent, creating or continuing a task.

        Args:
            agent_url: Base URL of the target A2A agent.
            message: The Message to send (with text/data parts).
            task_id: Optional existing task ID to continue.
            metadata: Optional metadata to attach to the task.

        Returns:
            The created/updated Task object.
        """
        request = JsonRpcRequest(
            method="agent/sendMessage",
            params={
                "message": message.model_dump(mode="json"),
                "task_id": task_id,
                "metadata": metadata or {},
            },
        )

        response = await self._send_jsonrpc(agent_url, request)

        if response.get("error"):
            raise RuntimeError(
                f"A2A error from {agent_url}: {response['error'].get('message', 'Unknown error')}"
            )

        return Task(**response["result"])

    # ── Task Retrieval ───────────────────────────────────────────

    async def get_task(self, agent_url: str, task_id: str) -> Task:
        """Retrieve the current state of a task.

        Args:
            agent_url: Base URL of the agent.
            task_id: The task to retrieve.

        Returns:
            Current Task state.
        """
        request = JsonRpcRequest(
            method="agent/getTask",
            params={"task_id": task_id},
        )

        response = await self._send_jsonrpc(agent_url, request)

        if response.get("error"):
            raise RuntimeError(
                f"A2A error: {response['error'].get('message', 'Unknown')}"
            )

        return Task(**response["result"])

    # ── Task Cancellation ────────────────────────────────────────

    async def cancel_task(
        self, agent_url: str, task_id: str, reason: str = "Canceled by orchestrator"
    ) -> Task:
        """Cancel a running task.

        Args:
            agent_url: Base URL of the agent.
            task_id: The task to cancel.
            reason: Reason for cancellation.

        Returns:
            Updated Task with CANCELED state.
        """
        request = JsonRpcRequest(
            method="agent/cancelTask",
            params={"task_id": task_id, "reason": reason},
        )

        response = await self._send_jsonrpc(agent_url, request)
        return Task(**response["result"])

    # ── Polling ──────────────────────────────────────────────────

    async def wait_for_completion(
        self,
        agent_url: str,
        task_id: str,
        poll_interval: float = 1.0,
        timeout: Optional[float] = None,
    ) -> Task:
        """Poll a task until it reaches a terminal state.

        Args:
            agent_url: Base URL of the agent.
            task_id: Task to poll.
            poll_interval: Seconds between polls.
            timeout: Maximum seconds to wait (None = use client timeout).

        Returns:
            The completed/failed/canceled Task.

        Raises:
            asyncio.TimeoutError: If the timeout is exceeded.
        """
        effective_timeout = timeout or self.timeout
        start = asyncio.get_event_loop().time()

        while True:
            task = await self.get_task(agent_url, task_id)

            if task.is_terminal:
                return task

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= effective_timeout:
                raise asyncio.TimeoutError(
                    f"Task {task_id} did not complete within {effective_timeout}s"
                )

            await asyncio.sleep(poll_interval)

    # ── SSE Streaming ────────────────────────────────────────────

    async def stream_task(
        self, agent_url: str, task_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream task updates via Server-Sent Events.

        Args:
            agent_url: Base URL of the agent.
            task_id: Task to stream.

        Yields:
            Parsed SSE event data dicts.
        """
        stream_url = f"{agent_url.rstrip('/')}/tasks/{task_id}/stream"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", stream_url) as response:
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        event = self._parse_sse_event(event_str)
                        if event:
                            yield event

    # ── List Tasks ───────────────────────────────────────────────

    async def list_tasks(
        self, agent_url: str, state: Optional[str] = None, limit: int = 50
    ) -> List[Task]:
        """List tasks on an agent with optional state filtering.

        Args:
            agent_url: Base URL of the agent.
            state: Optional state to filter by.
            limit: Maximum tasks to return.

        Returns:
            List of Task objects.
        """
        request = JsonRpcRequest(
            method="agent/listTasks",
            params={"state": state, "limit": limit},
        )

        response = await self._send_jsonrpc(agent_url, request)

        if response.get("error"):
            raise RuntimeError(f"A2A error: {response['error'].get('message')}")

        tasks_data = response["result"].get("tasks", [])
        return [Task(**t) for t in tasks_data]

    # ── JSON-RPC Transport ───────────────────────────────────────

    async def _send_jsonrpc(
        self, agent_url: str, request: JsonRpcRequest
    ) -> Dict[str, Any]:
        """Send a JSON-RPC 2.0 request to an agent with retry logic."""
        url = agent_url.rstrip("/") + "/"
        payload = request.model_dump(mode="json")

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"A2A request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)

        raise RuntimeError(
            f"A2A request to {agent_url} failed after {self.max_retries} attempts: {last_error}"
        )

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_sse_event(event_str: str) -> Optional[Dict[str, Any]]:
        """Parse a single SSE event string into a dict."""
        event_type = "message"
        data_lines = []

        for line in event_str.strip().split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if data_lines:
            data_str = "\n".join(data_lines)
            try:
                return {"event": event_type, "data": json.loads(data_str)}
            except json.JSONDecodeError:
                return {"event": event_type, "data": data_str}

        return None

    @staticmethod
    def create_message(
        text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        role: str = "user",
    ) -> Message:
        """Convenience factory for creating A2A Messages.

        Args:
            text: Optional text content.
            data: Optional structured data content.
            role: Message sender role.

        Returns:
            A new Message with the specified parts.
        """
        msg = Message(role=role)
        if text:
            msg.add_text(text)
        if data:
            msg.add_data(data)
        return msg
