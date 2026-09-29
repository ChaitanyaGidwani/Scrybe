"""Scrybe Pipeline Orchestrator.

Coordinates the sequential execution of all six agents:
Compliance → Reader → Analyst → Memory → Strategist → Formatter.

Each agent receives the ScrybeState and mutates it before passing
to the next stage. Failures in any stage are logged and the pipeline
degrades gracefully.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import Settings, load_sources
from scrybe.agents.compliance import ComplianceAgent
from scrybe.agents.reader import ReaderAgent
from scrybe.agents.analyst import AnalystAgent
from scrybe.agents.memory import MemoryAgent
from scrybe.agents.strategist import StrategistAgent
from scrybe.agents.formatter import FormatterAgent
from scrybe.logging_config import get_agent_logger, setup_logging
from scrybe.memory.buffer import RollingBuffer
from scrybe.memory.vector_store import VectorStore
from scrybe.storage.db import DatabaseManager
from scrybe.storage.models import ScrybeState
from scrybe.tools.llm_client import LLMClient

logger = get_agent_logger("orchestrator")


class Pipeline:
    """Main orchestrator for the Scrybe intelligence pipeline.

    Wires all agents together and manages the sequential execution
    flow with structured logging and database persistence.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.pipeline_id = f"pipe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Shared components
        self.buffer = RollingBuffer(max_size=50)
        self.vector_store = VectorStore(
            index_path=self.settings.faiss_index_path,
            dimension=384,
        )

        # Initialize LLM client (if keys are available)
        self.llm_client = None
        if self.settings.openai_api_key or self.settings.anthropic_api_key or self.settings.google_api_key:
            self.llm_client = LLMClient(
                openai_api_key=self.settings.openai_api_key,
                anthropic_api_key=self.settings.anthropic_api_key,
                google_api_key=self.settings.google_api_key,
            )

        # Initialize agents
        self.compliance_agent = ComplianceAgent(
            user_agent=self.settings.user_agent,
            min_crawl_delay=self.settings.crawl_delay_min_seconds,
            respect_robots=self.settings.respect_robots_txt,
        )
        self.reader_agent = ReaderAgent(
            compliance_agent=self.compliance_agent,
            buffer=self.buffer,
            user_agent=self.settings.user_agent,
        )
        self.analyst_agent = AnalystAgent(
            llm_client=self.llm_client,
            extraction_model=self.settings.extraction_model,
            confidence_threshold=self.settings.confidence_threshold,
            buffer=self.buffer,
        )
        self.memory_agent = MemoryAgent(
            buffer=self.buffer,
            vector_store=self.vector_store,
        )
        self.strategist_agent = StrategistAgent(
            llm_client=self.llm_client,
            reasoning_model=self.settings.reasoning_model,
            min_corroboration=self.settings.multi_source_min_count,
            buffer=self.buffer,
        )
        self.formatter_agent = FormatterAgent(
            output_dir=self.settings.output_dir,
            buffer=self.buffer,
        )

        # Database manager
        self.db = DatabaseManager(database_url=self.settings.database_url)

    async def run(self, sources_config_path: Optional[str] = None) -> ScrybeState:
        """Execute the full pipeline: Reader → Analyst → Memory → Strategist → Formatter.

        Args:
            sources_config_path: Optional override path for sources.yaml.

        Returns:
            Final ScrybeState with all pipeline results.
        """
        start_time = time.time()
        state = ScrybeState(pipeline_id=self.pipeline_id)

        logger.info(
            f"Pipeline starting: {self.pipeline_id}",
            extra={"agent": "orchestrator", "step": "pipeline_start", "pipeline_id": self.pipeline_id},
        )

        # Load source configurations
        sources = load_sources(sources_config_path or self.settings.sources_config_path)
        if not sources:
            logger.warning("No sources configured. Check config/sources.yaml.")
            return state

        # Record the run in the database
        self.db.create_run(self.pipeline_id, sources_count=len(sources))

        try:
            # ── Stage 1: Reader Agent (Web Scraping) ──
            logger.info(f"Stage 1: Reader Agent — scraping {len(sources)} sources",
                       extra={"agent": "orchestrator", "step": "stage_1_reader"})

            state.raw_scrapes = await self.reader_agent.run(sources)

            for doc in state.raw_scrapes:
                self.db.save_raw_document(self.pipeline_id, doc.model_dump())

            logger.info(f"Reader complete: {len(state.raw_scrapes)}/{len(sources)} sources scraped")

            if not state.raw_scrapes:
                logger.warning("No documents scraped — pipeline ending early")
                self.db.complete_run(self.pipeline_id, status="NO_DATA")
                return state

            # ── Stage 2: Analyst Agent (Structured Extraction) ──
            logger.info(f"Stage 2: Analyst Agent — extracting from {len(state.raw_scrapes)} documents",
                       extra={"agent": "orchestrator", "step": "stage_2_analyst"})

            state.extracted_records, state.flagged_records = self.analyst_agent.run(state.raw_scrapes)

            for record in state.extracted_records:
                self.db.save_extracted_record(self.pipeline_id, record.model_dump())

            logger.info(
                f"Analyst complete: {len(state.extracted_records)} validated, "
                f"{len(state.flagged_records)} flagged"
            )

            # ── Stage 3: Memory Agent (Delta Detection) ──
            logger.info("Stage 3: Memory Agent — detecting deltas",
                       extra={"agent": "orchestrator", "step": "stage_3_memory"})

            state.historical_deltas, unchanged = self.memory_agent.run(state.extracted_records)

            if unchanged:
                logger.info(f"Unchanged companies (skipping deep synthesis): {', '.join(unchanged)}")

            logger.info(f"Memory complete: {len(state.historical_deltas)} deltas, {len(unchanged)} unchanged")

            # ── Stage 4: Strategist Agent (Analysis & Corroboration) ──
            logger.info("Stage 4: Strategist Agent — strategic synthesis",
                       extra={"agent": "orchestrator", "step": "stage_4_strategist"})

            # Filter to only changed records for deep synthesis
            records_to_analyze = [
                r for r in state.extracted_records
                if r.company_name not in unchanged
            ] or state.extracted_records  # Fallback to all if everything is new

            strategy_result = self.strategist_agent.run(records_to_analyze, state.historical_deltas)

            # Parse recommendations into typed models for state
            for rec_data in strategy_result.get("strategic_recommendations", []):
                try:
                    sources_list = rec_data.get("corroborating_sources", ["N/A"])
                    if not sources_list:
                        sources_list = ["N/A"]
                    from scrybe.storage.models import StrategicRecommendation
                    typed_rec = StrategicRecommendation(
                        category=rec_data.get("category", "POSITIONING"),
                        title=rec_data.get("title", ""),
                        rationale=rec_data.get("rationale", ""),
                        actionable_next_step=rec_data.get("actionable_next_step", ""),
                        corroborating_sources=sources_list,
                        corroboration_count=rec_data.get("corroboration_count", len(sources_list)),
                    )
                    state.strategic_insights.append(typed_rec)
                    self.db.save_strategic_insight(self.pipeline_id, rec_data)
                except Exception as e:
                    logger.warning(f"Skipping malformed recommendation: {e}")

            logger.info(f"Strategist complete: {len(state.strategic_insights)} recommendations")

            # ── Stage 5: Formatter Agent (Report Generation) ──
            logger.info("Stage 5: Formatter Agent — generating reports",
                       extra={"agent": "orchestrator", "step": "stage_5_formatter"})

            formatter_result = self.formatter_agent.run(
                pipeline_id=self.pipeline_id,
                records=state.extracted_records,
                deltas=state.historical_deltas,
                strategy_result=strategy_result,
            )

            state.report_markdown = formatter_result.get("report_markdown")
            state.report_pdf_path = formatter_result.get("report_pdf_path")

            # Save report to database
            self.db.save_report(formatter_result.get("report_data", {}))

            logger.info(
                f"Formatter complete: MD={formatter_result.get('report_markdown_path')}, "
                f"PDF={formatter_result.get('report_pdf_path', 'N/A')}"
            )

            # ── Finalize ──
            elapsed = round(time.time() - start_time, 2)
            state.execution_metrics = {
                "total_seconds": elapsed,
                "sources_attempted": len(sources),
                "sources_scraped": len(state.raw_scrapes),
                "records_extracted": len(state.extracted_records),
                "records_flagged": len(state.flagged_records),
                "deltas_detected": len(state.historical_deltas),
                "recommendations_generated": len(state.strategic_insights),
                "unchanged_companies": len(unchanged),
            }

            # Save vector index for next run
            self.memory_agent.save_index()

            self.db.complete_run(
                self.pipeline_id,
                status="COMPLETED",
                records_extracted=len(state.extracted_records),
                report_path=formatter_result.get("report_markdown_path"),
                metrics=state.execution_metrics,
            )

            logger.info(
                f"Pipeline complete in {elapsed}s",
                extra={
                    "agent": "orchestrator",
                    "step": "pipeline_complete",
                    "pipeline_id": self.pipeline_id,
                },
            )

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            logger.error(f"Pipeline failed after {elapsed}s: {e}", exc_info=True)
            self.db.complete_run(self.pipeline_id, status="FAILED", metrics={"error": str(e)})
            raise

        return state


def run_pipeline(sources_config_path: Optional[str] = None) -> ScrybeState:
    """Convenience function to run the pipeline synchronously.

    Args:
        sources_config_path: Optional override for sources.yaml path.

    Returns:
        Final ScrybeState.
    """
    setup_logging()
    pipeline = Pipeline()
    return asyncio.run(pipeline.run(sources_config_path))
