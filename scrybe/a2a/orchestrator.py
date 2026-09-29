"""A2A-Powered Pipeline Orchestrator.

Replaces the original sequential Pipeline with an A2A protocol-based
orchestrator that:
1. Discovers agents via their Agent Cards
2. Sends tasks via JSON-RPC 2.0 (agent/sendMessage)
3. Chains agent outputs as inputs to the next stage
4. Streams real-time progress via callback/SSE
5. Handles failures with retry and graceful degradation

The orchestrator acts as an A2A client, coordinating the pipeline:
    Compliance → Reader → Analyst → Memory → Strategist → Formatter

Each agent runs as an independent A2A server, and the orchestrator
discovers and communicates with them purely through the A2A protocol.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from scrybe.a2a.client import A2AClient
from scrybe.a2a.models import (
    Artifact,
    DataPart,
    Message,
    Task,
    TaskState,
    TextPart,
)
from scrybe.a2a.registry import AgentRegistry
from scrybe.agents.a2a_wrappers import (
    ALL_AGENT_CARDS,
    create_all_agent_servers,
)
from scrybe.logging_config import get_agent_logger
from scrybe.storage.db import DatabaseManager
from scrybe.storage.models import ScrybeState

logger = get_agent_logger("a2a_orchestrator")

# Type for progress callbacks
ProgressCallback = Optional[Callable[[str, str, Dict[str, Any]], None]]


class A2AOrchestrator:
    """A2A protocol-powered pipeline orchestrator.

    Coordinates the full Scrybe intelligence pipeline by communicating
    with each agent exclusively through the A2A protocol. Supports
    both in-process (direct handler calls) and remote (HTTP) modes.

    In-process mode: Agents run in the same process, handlers are
    called directly (no HTTP overhead). This is the default for
    single-machine deployments.

    Remote mode: Agents run as separate HTTP services, discovered
    via Agent Cards. This enables horizontal scaling and
    multi-machine deployments.

    Usage:
        orchestrator = A2AOrchestrator(mode="in_process")
        state = await orchestrator.run_pipeline()
    """

    def __init__(
        self,
        settings=None,
        mode: str = "in_process",
        progress_callback: ProgressCallback = None,
    ):
        self.settings = settings
        self.mode = mode
        self.progress_callback = progress_callback
        self.pipeline_id = (
            f"pipe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            f"_{uuid.uuid4().hex[:6]}"
        )

        # A2A infrastructure
        self.registry = AgentRegistry()
        self.client = A2AClient(timeout=300.0)

        # In-process servers (when mode="in_process")
        self._servers: Dict[str, Any] = {}

        # Track pipeline progress
        self._stage_results: Dict[str, Any] = {}

        self._setup_agents()

    def _setup_agents(self):
        """Register all agents in the registry."""
        if self.mode == "in_process":
            # Create in-process A2A servers for each agent
            self._servers = create_all_agent_servers(self.settings)
            for card in ALL_AGENT_CARDS:
                self.registry.register(card)
        else:
            # In remote mode, register cards with configured URLs
            for card in ALL_AGENT_CARDS:
                self.registry.register(card)

    async def run_pipeline(
        self,
        sources_config_path: Optional[str] = None,
    ) -> ScrybeState:
        """Execute the full A2A-powered intelligence pipeline.

        Pipeline stages:
            1. Reader Agent → Scrape web sources
            2. Analyst Agent → Extract structured data
            3. Memory Agent → Detect deltas
            4. Strategist Agent → Strategic synthesis
            5. Formatter Agent → Report generation

        Args:
            sources_config_path: Optional override for sources.yaml path.

        Returns:
            Final ScrybeState with all pipeline results.
        """
        start_time = time.time()
        state = ScrybeState(pipeline_id=self.pipeline_id)

        self._emit_progress("pipeline", "started", {
            "pipeline_id": self.pipeline_id,
            "mode": self.mode,
            "agents": self.registry.list_agents(),
        })

        # Initialize database
        db = DatabaseManager(
            database_url=self.settings.database_url if self.settings else None,
        )
        db.create_run(self.pipeline_id, sources_count=0)

        try:
            # ── Stage 1: Reader Agent ────────────────────────────
            self._emit_progress("reader", "starting", {"stage": 1})

            reader_result = await self._send_to_agent(
                agent_name="reader",
                data={
                    "sources_config_path": sources_config_path or (
                        self.settings.sources_config_path if self.settings else None
                    ),
                },
                description="Scrape configured web sources",
            )

            documents_data = reader_result.get("documents", [])
            state.raw_scrapes = []
            for doc_data in documents_data:
                from scrybe.storage.models import RawScrapedDocument
                state.raw_scrapes.append(RawScrapedDocument(**doc_data))
                db.save_raw_document(self.pipeline_id, doc_data)

            self._emit_progress("reader", "completed", {
                "documents_scraped": len(documents_data),
            })

            if not documents_data:
                logger.warning("No documents scraped — pipeline ending early")
                db.complete_run(self.pipeline_id, status="NO_DATA")
                return state

            # ── Stage 2: Analyst Agent ───────────────────────────
            self._emit_progress("analyst", "starting", {"stage": 2})

            analyst_result = await self._send_to_agent(
                agent_name="analyst",
                data={"documents": documents_data},
                description="Extract structured pricing data",
            )

            validated_data = analyst_result.get("validated_records", [])
            flagged_data = analyst_result.get("flagged_records", [])

            from scrybe.storage.models import CompetitorProductRecord
            state.extracted_records = [CompetitorProductRecord(**r) for r in validated_data]
            state.flagged_records = flagged_data

            for record_data in validated_data:
                db.save_extracted_record(self.pipeline_id, record_data)

            self._emit_progress("analyst", "completed", {
                "validated": len(validated_data),
                "flagged": len(flagged_data),
            })

            # ── Stage 3: Memory Agent ────────────────────────────
            self._emit_progress("memory", "starting", {"stage": 3})

            memory_result = await self._send_to_agent(
                agent_name="memory",
                data={"records": validated_data},
                description="Detect pricing changes since last run",
            )

            deltas_data = memory_result.get("deltas", [])
            unchanged = memory_result.get("unchanged_companies", [])

            from scrybe.storage.models import TrendDelta
            state.historical_deltas = [TrendDelta(**d) for d in deltas_data]

            self._emit_progress("memory", "completed", {
                "deltas": len(deltas_data),
                "unchanged": len(unchanged),
            })

            # ── Stage 4: Strategist Agent ────────────────────────
            self._emit_progress("strategist", "starting", {"stage": 4})

            # Filter to only changed records for deep synthesis
            records_for_strategy = [
                r for r in validated_data
                if r.get("company_name") not in unchanged
            ] or validated_data

            strategist_result = await self._send_to_agent(
                agent_name="strategist",
                data={
                    "records": records_for_strategy,
                    "deltas": deltas_data,
                },
                description="Generate strategic analysis and recommendations",
            )

            # Parse strategic recommendations
            from scrybe.storage.models import StrategicRecommendation
            for rec_data in strategist_result.get("strategic_recommendations", []):
                try:
                    sources_list = rec_data.get("corroborating_sources", []) or ["N/A"]
                    typed_rec = StrategicRecommendation(
                        category=rec_data.get("category", "POSITIONING"),
                        title=rec_data.get("title", ""),
                        rationale=rec_data.get("rationale", ""),
                        actionable_next_step=rec_data.get("actionable_next_step", ""),
                        corroborating_sources=sources_list,
                        corroboration_count=rec_data.get("corroboration_count", len(sources_list)),
                    )
                    state.strategic_insights.append(typed_rec)
                    db.save_strategic_insight(self.pipeline_id, rec_data)
                except Exception as e:
                    logger.warning(f"Skipping malformed recommendation: {e}")

            self._emit_progress("strategist", "completed", {
                "recommendations": len(state.strategic_insights),
            })

            # ── Stage 5: Formatter Agent ─────────────────────────
            self._emit_progress("formatter", "starting", {"stage": 5})

            formatter_result = await self._send_to_agent(
                agent_name="formatter",
                data={
                    "pipeline_id": self.pipeline_id,
                    "records": validated_data,
                    "deltas": deltas_data,
                    "strategy_result": strategist_result,
                },
                description="Generate intelligence reports",
            )

            state.report_markdown = formatter_result.get("report_markdown")
            state.report_pdf_path = formatter_result.get("report_pdf_path")

            report_data = formatter_result.get("report_data", {})
            if report_data:
                db.save_report(report_data)

            self._emit_progress("formatter", "completed", {
                "markdown_path": formatter_result.get("report_markdown_path"),
                "pdf_path": formatter_result.get("report_pdf_path"),
            })

            # ── Finalize ─────────────────────────────────────────
            elapsed = round(time.time() - start_time, 2)
            state.execution_metrics = {
                "total_seconds": elapsed,
                "protocol": "a2a/1.0",
                "mode": self.mode,
                "sources_scraped": len(documents_data),
                "records_extracted": len(validated_data),
                "records_flagged": len(flagged_data),
                "deltas_detected": len(deltas_data),
                "recommendations_generated": len(state.strategic_insights),
                "unchanged_companies": len(unchanged),
            }

            db.complete_run(
                self.pipeline_id,
                status="COMPLETED",
                records_extracted=len(validated_data),
                report_path=formatter_result.get("report_markdown_path"),
                metrics=state.execution_metrics,
            )

            self._emit_progress("pipeline", "completed", {
                "elapsed_seconds": elapsed,
                "metrics": state.execution_metrics,
            })

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            logger.error(f"Pipeline failed after {elapsed}s: {e}", exc_info=True)
            db.complete_run(self.pipeline_id, status="FAILED", metrics={"error": str(e)})
            self._emit_progress("pipeline", "failed", {"error": str(e), "elapsed": elapsed})
            raise

        return state

    # ── Agent Communication ──────────────────────────────────────

    async def _send_to_agent(
        self,
        agent_name: str,
        data: Dict[str, Any],
        description: str = "",
    ) -> Dict[str, Any]:
        """Send a task to an agent and wait for completion.

        In in_process mode, calls the handler directly.
        In remote mode, uses HTTP JSON-RPC via the A2A client.

        Args:
            agent_name: Name of the target agent.
            data: Structured data payload for the task.
            description: Human-readable task description.

        Returns:
            The artifact data from the completed task.
        """
        logger.info(
            f"Sending task to {agent_name}: {description}",
            extra={"agent": "orchestrator", "step": f"send_to_{agent_name}"},
        )

        message = A2AClient.create_message(
            text=description,
            data=data,
            role="user",
        )

        if self.mode == "in_process":
            return await self._send_in_process(agent_name, message)
        else:
            return await self._send_remote(agent_name, message)

    async def _send_in_process(
        self, agent_name: str, message: Message
    ) -> Dict[str, Any]:
        """Send a task to an in-process A2A server."""
        server = self._servers.get(agent_name)
        if not server:
            raise RuntimeError(f"No in-process server for agent: {agent_name}")

        # Build the JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "method": "agent/sendMessage",
            "params": {
                "message": message.model_dump(mode="json"),
                "metadata": {"pipeline_id": self.pipeline_id},
            },
            "id": uuid.uuid4().hex[:12],
        }

        # Send to the server
        response = await server.handle_jsonrpc(request_data)

        if response.get("error"):
            raise RuntimeError(
                f"Agent {agent_name} error: {response['error'].get('message')}"
            )

        # Get the task ID and wait for completion
        task_data = response.get("result", {})
        task_id = task_data.get("task_id")

        if not task_id:
            raise RuntimeError(f"No task_id in response from {agent_name}")

        # Poll until task completes
        max_wait = 300  # 5 minutes
        poll_interval = 0.5
        elapsed = 0

        while elapsed < max_wait:
            task = server.get_task(task_id)
            if task and task.is_terminal:
                if task.status.state == TaskState.FAILED:
                    raise RuntimeError(
                        f"Agent {agent_name} task failed: {task.status.message}"
                    )
                # Extract artifact data
                if task.artifacts:
                    return task.artifacts[-1].get_data() or {}
                return {}

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise asyncio.TimeoutError(f"Agent {agent_name} did not complete within {max_wait}s")

    async def _send_remote(
        self, agent_name: str, message: Message
    ) -> Dict[str, Any]:
        """Send a task to a remote A2A agent via HTTP."""
        agent_url = self.registry.get_url(agent_name)
        if not agent_url:
            raise RuntimeError(f"Agent not found in registry: {agent_name}")

        task = await self.client.send_task(
            agent_url=agent_url,
            message=message,
            metadata={"pipeline_id": self.pipeline_id},
        )

        # Wait for completion
        completed_task = await self.client.wait_for_completion(
            agent_url=agent_url,
            task_id=task.task_id,
            poll_interval=1.0,
            timeout=300.0,
        )

        if completed_task.status.state == TaskState.FAILED:
            raise RuntimeError(
                f"Agent {agent_name} task failed: {completed_task.status.message}"
            )

        return completed_task.latest_artifact_data or {}

    # ── Progress Emission ────────────────────────────────────────

    def _emit_progress(
        self, agent: str, event: str, data: Dict[str, Any]
    ) -> None:
        """Emit a progress event for real-time monitoring."""
        progress = {
            "pipeline_id": self.pipeline_id,
            "agent": agent,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }

        logger.info(
            f"Pipeline progress: {agent}/{event}",
            extra={"agent": "orchestrator", "step": f"{agent}_{event}"},
        )

        if self.progress_callback:
            self.progress_callback(agent, event, progress)

        # Store for retrieval
        self._stage_results[f"{agent}_{event}"] = progress

    # ── Agent Health ─────────────────────────────────────────────

    async def check_agent_health(self) -> Dict[str, Any]:
        """Check health of all registered agents.

        Returns:
            Health status for each agent.
        """
        if self.mode == "in_process":
            return {
                name: {
                    "healthy": True,
                    "active_tasks": server.active_tasks,
                    "total_tasks": server.total_tasks,
                }
                for name, server in self._servers.items()
            }
        else:
            return await self.registry.health_check_all()

    def get_pipeline_progress(self) -> Dict[str, Any]:
        """Get current pipeline progress summary."""
        return {
            "pipeline_id": self.pipeline_id,
            "mode": self.mode,
            "stages": self._stage_results,
            "agents": self.registry.list_agents(),
        }


# ── Convenience Function ─────────────────────────────────────────

def run_a2a_pipeline(
    sources_config_path: Optional[str] = None,
    mode: str = "in_process",
    progress_callback: ProgressCallback = None,
) -> ScrybeState:
    """Run the A2A-powered pipeline synchronously.

    Args:
        sources_config_path: Optional sources.yaml override.
        mode: "in_process" or "remote".
        progress_callback: Optional callback for progress events.

    Returns:
        Final ScrybeState.
    """
    from config.settings import Settings
    from scrybe.logging_config import setup_logging

    setup_logging()
    settings = Settings()

    orchestrator = A2AOrchestrator(
        settings=settings,
        mode=mode,
        progress_callback=progress_callback,
    )
    return asyncio.run(orchestrator.run_pipeline(sources_config_path))
