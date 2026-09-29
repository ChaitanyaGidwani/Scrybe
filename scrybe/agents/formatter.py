"""Scrybe Formatter Agent.

Compiles validated intelligence into publication-quality reports.
Generates Markdown executive briefs, PDF reports, and structured
JSON payloads for API delivery.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from scrybe.logging_config import get_agent_logger
from scrybe.memory.buffer import RollingBuffer
from scrybe.storage.models import (
    CompetitorProductRecord,
    MarketIntelligenceReport,
    StrategicRecommendation,
    TrendDelta,
)
from scrybe.tools.reporter import (
    generate_markdown_report,
    save_markdown_report,
    save_pdf_report,
)

logger = get_agent_logger("formatter")


class FormatterAgent:
    """Autonomous agent for report compilation and multi-channel publishing.

    Takes strategic analysis output and produces:
    - Executive Markdown reports with citations
    - PDF briefs (via ReportLab)
    - Structured JSON payloads for API consumers
    """

    def __init__(
        self,
        output_dir: str = "output",
        buffer: Optional[RollingBuffer] = None,
    ):
        self.output_dir = output_dir
        self.buffer = buffer or RollingBuffer()

    def run(
        self,
        pipeline_id: str,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
        strategy_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate all report formats from the strategic analysis.

        Args:
            pipeline_id: Unique pipeline run identifier.
            records: Validated competitor product records.
            deltas: Detected market deltas.
            strategy_result: Output from the Strategist Agent.

        Returns:
            Dict containing report_markdown, report_pdf_path, and report_data.
        """
        # Build typed recommendation objects
        typed_recommendations = self._build_typed_recommendations(
            strategy_result.get("strategic_recommendations", [])
        )

        # Generate Markdown report
        markdown_content = generate_markdown_report(
            pipeline_id=pipeline_id,
            executive_summary=strategy_result.get("executive_summary", "No summary available."),
            records=records,
            deltas=deltas,
            recommendations=typed_recommendations,
            battlecards=strategy_result.get("sales_battlecard_snippets"),
        )

        # Save Markdown to disk
        md_path = save_markdown_report(markdown_content, self.output_dir, pipeline_id)

        # Attempt PDF generation
        pdf_path = save_pdf_report(markdown_content, self.output_dir, pipeline_id)

        # Build the full report data object
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        citations = list(set(r.source_url for r in records))

        report_data = {
            "report_id": report_id,
            "pipeline_id": pipeline_id,
            "title": f"Competitive Intelligence Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_vertical": "B2B_AI_DEVELOPER_PLATFORMS",
            "executive_summary": strategy_result.get("executive_summary", ""),
            "markdown_content": markdown_content,
            "pdf_path": pdf_path,
            "citations": citations,
            "records_count": len(records),
            "deltas_count": len(deltas),
            "recommendations_count": len(typed_recommendations),
        }

        self.buffer.record(
            agent="formatter",
            action="reports_generated",
            status="OK",
            metadata={
                "md_path": md_path,
                "pdf_path": pdf_path or "N/A",
                "records": len(records),
            },
        )

        logger.info(
            "Reports generated",
            extra={
                "agent": "formatter",
                "step": "generate_reports",
                "pipeline_id": pipeline_id,
            },
        )

        return {
            "report_markdown": markdown_content,
            "report_markdown_path": md_path,
            "report_pdf_path": pdf_path,
            "report_data": report_data,
        }

    def _build_typed_recommendations(
        self,
        raw_recommendations: List[Dict[str, Any]],
    ) -> List[StrategicRecommendation]:
        """Convert raw recommendation dicts to typed Pydantic objects."""
        typed = []
        for raw in raw_recommendations:
            try:
                sources = raw.get("corroborating_sources", [])
                if not sources:
                    sources = ["N/A"]
                typed.append(StrategicRecommendation(
                    category=raw.get("category", "POSITIONING"),
                    title=raw.get("title", "Untitled"),
                    rationale=raw.get("rationale", ""),
                    actionable_next_step=raw.get("actionable_next_step", ""),
                    corroborating_sources=sources,
                    corroboration_count=raw.get("corroboration_count", len(sources)),
                ))
            except Exception as e:
                logger.warning(f"Skipping malformed recommendation: {e}")
        return typed

    def generate_json_payload(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
        strategy_result: Dict[str, Any],
    ) -> str:
        """Generate a structured JSON payload for API/webhook delivery.

        Args:
            records: Validated competitor records.
            deltas: Detected deltas.
            strategy_result: Strategist output.

        Returns:
            JSON string of the complete intelligence payload.
        """
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": strategy_result.get("executive_summary", ""),
            "competitors": [r.model_dump() for r in records],
            "market_deltas": [d.model_dump() for d in deltas],
            "recommendations": strategy_result.get("strategic_recommendations", []),
            "battlecards": strategy_result.get("sales_battlecard_snippets", {}),
        }
        return json.dumps(payload, indent=2, default=str)
