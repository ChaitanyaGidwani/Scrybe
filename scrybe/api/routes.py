"""Scrybe API Routes.

Defines REST endpoints for pipeline execution, report retrieval,
and pricing matrix queries.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Header
from pydantic import BaseModel

from config.settings import settings
from scrybe.storage.db import DatabaseManager

router = APIRouter()
logger = logging.getLogger("scrybe.api")

# Shared database instance
_db: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


# ── Request/Response Models ──

class PipelineRunRequest(BaseModel):
    sources_config_path: Optional[str] = None


class PipelineRunResponse(BaseModel):
    status: str
    pipeline_id: str
    message: str


class ReportSummary(BaseModel):
    report_id: str
    pipeline_id: str
    title: str
    generated_at: str
    target_vertical: Optional[str] = None


# ── Auth Dependency ──

async def verify_api_key(x_api_key: str = Header(default="")):
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Background Pipeline Runner ──

def _run_pipeline_background(sources_path: Optional[str] = None):
    """Run the pipeline in a background thread."""
    from scrybe.pipeline import run_pipeline
    try:
        run_pipeline(sources_path)
    except Exception as e:
        logger.error(f"Background pipeline failed: {e}")


# ── Endpoints ──

@router.post("/run", response_model=PipelineRunResponse)
async def trigger_pipeline_run(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger a new pipeline run in the background.

    The pipeline executes asynchronously. Use GET /reports to check results.
    """
    from scrybe.pipeline import Pipeline
    pipeline = Pipeline()
    pipeline_id = pipeline.pipeline_id

    background_tasks.add_task(_run_pipeline_background, request.sources_config_path)

    return PipelineRunResponse(
        status="accepted",
        pipeline_id=pipeline_id,
        message=f"Pipeline run {pipeline_id} started in background.",
    )


@router.get("/reports")
async def list_reports(limit: int = 20):
    """List the most recent intelligence reports."""
    db = get_db()
    reports = db.get_reports(limit=limit)
    return {
        "count": len(reports),
        "reports": [
            {
                "report_id": r.get("report_id"),
                "pipeline_id": r.get("pipeline_id"),
                "title": r.get("title"),
                "generated_at": str(r.get("generated_at", "")),
                "target_vertical": r.get("target_vertical"),
                "has_pdf": bool(r.get("pdf_path")),
            }
            for r in reports
        ],
    }


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Retrieve a full report by its ID.

    Returns the Markdown content, executive summary, and citations.
    """
    db = get_db()
    report = db.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return {
        "report_id": report.get("report_id"),
        "pipeline_id": report.get("pipeline_id"),
        "title": report.get("title"),
        "generated_at": str(report.get("generated_at", "")),
        "executive_summary": report.get("executive_summary"),
        "markdown_content": report.get("markdown_content"),
        "pdf_path": report.get("pdf_path"),
        "citations": report.get("citations_json"),
    }


@router.get("/matrix")
async def get_pricing_matrix(pipeline_id: Optional[str] = None):
    """Retrieve the latest normalized pricing matrix.

    Returns structured competitor pricing data from the most recent
    pipeline run (or a specific pipeline_id if provided).
    """
    db = get_db()

    if pipeline_id:
        records = db.get_extracted_records(pipeline_id)
    else:
        # Get records from the most recent report
        reports = db.get_reports(limit=1)
        if not reports:
            return {"message": "No pipeline runs found", "competitors": []}
        records = db.get_extracted_records(reports[0].get("pipeline_id", ""))

    return {
        "pipeline_id": pipeline_id or (reports[0].get("pipeline_id") if reports else None),
        "competitors_count": len(records),
        "competitors": records,
    }


@router.get("/status")
async def get_pipeline_status():
    """Get the status of recent pipeline runs."""
    db = get_db()
    reports = db.get_reports(limit=5)
    return {
        "recent_runs": [
            {
                "pipeline_id": r.get("pipeline_id"),
                "title": r.get("title"),
                "generated_at": str(r.get("generated_at", "")),
            }
            for r in reports
        ],
    }


@router.get("/audits")
async def get_compliance_audits(pipeline_id: Optional[str] = None, limit: int = 50):
    """Retrieve compliance audit records."""
    db = get_db()
    audits = db.get_compliance_audits(pipeline_id=pipeline_id, limit=limit)
    return {
        "count": len(audits),
        "audits": [
            {
                **audit,
                "timestamp": str(audit.get("timestamp", "")),
            }
            for audit in audits
        ],
    }


@router.get("/insights")
async def get_strategic_insights(pipeline_id: Optional[str] = None, limit: int = 50):
    """Retrieve strategic insights generated by StrategistAgent."""
    db = get_db()
    insights = db.get_strategic_insights(pipeline_id=pipeline_id, limit=limit)
    return {
        "count": len(insights),
        "insights": [
            {
                **insight,
                "created_at": str(insight.get("created_at", "")),
            }
            for insight in insights
        ],
    }

