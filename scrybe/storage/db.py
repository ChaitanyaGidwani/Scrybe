"""Scrybe Database Engine and Session Management.

SQLite for development, PostgreSQL for production. All tables are created
automatically on first run. Uses SQLAlchemy Core for schema definitions
and async-compatible session management.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    create_engine,
    MetaData,
    Table,
    insert,
    select,
    desc,
)
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings

logger = logging.getLogger("scrybe.storage")

metadata = MetaData()

# ── Table Definitions ──

runs_table = Table(
    "runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", String(64), unique=True, nullable=False, index=True),
    Column("started_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("completed_at", DateTime, nullable=True),
    Column("target_vertical", String(128), default="B2B_AI_DEVELOPER_PLATFORMS"),
    Column("status", String(32), default="RUNNING"),  # RUNNING | COMPLETED | FAILED
    Column("sources_count", Integer, default=0),
    Column("records_extracted", Integer, default=0),
    Column("report_path", String(512), nullable=True),
    Column("execution_metrics_json", Text, nullable=True),
)

raw_documents_table = Table(
    "raw_documents",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", String(64), nullable=False, index=True),
    Column("url", String(2048), nullable=False),
    Column("domain", String(256), nullable=False),
    Column("status_code", Integer, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("scrape_tier", String(32), nullable=False),
    Column("scraped_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("content_length", Integer, default=0),
    Column("pii_redacted", Boolean, default=True),
    Column("robots_compliant", Boolean, default=True),
)

compliance_audits_table = Table(
    "compliance_audits",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("audit_id", String(64), unique=True, nullable=False),
    Column("pipeline_id", String(64), nullable=True, index=True),
    Column("timestamp", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("source_url", String(2048), nullable=False),
    Column("robots_checked", Boolean, default=True),
    Column("robots_allowed", Boolean, default=True),
    Column("crawl_delay_applied", Float, default=2.5),
    Column("pii_scrubbed_count", Integer, default=0),
    Column("compliance_status", String(32), default="APPROVED"),
)

extracted_records_table = Table(
    "extracted_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", String(64), nullable=False, index=True),
    Column("company_name", String(256), nullable=False),
    Column("product_name", String(256), nullable=False),
    Column("source_url", String(2048), nullable=False),
    Column("extraction_confidence", Float, nullable=False),
    Column("citation_text", Text, nullable=False),
    Column("pricing_data_json", Text, nullable=False),  # JSON-serialized PricingTier list
    Column("enterprise_terms_mentioned", Boolean, default=False),
    Column("rate_limits_summary", Text, nullable=True),
    Column("extracted_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

strategic_insights_table = Table(
    "strategic_insights",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", String(64), nullable=False, index=True),
    Column("category", String(64), nullable=False),
    Column("title", String(512), nullable=False),
    Column("rationale", Text, nullable=False),
    Column("actionable_next_step", Text, nullable=False),
    Column("corroborating_sources_json", Text, nullable=False),
    Column("corroboration_count", Integer, default=1),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

reports_table = Table(
    "reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("report_id", String(64), unique=True, nullable=False, index=True),
    Column("pipeline_id", String(64), nullable=False, index=True),
    Column("title", String(512), nullable=False),
    Column("generated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("target_vertical", String(128)),
    Column("executive_summary", Text, nullable=True),
    Column("markdown_content", Text, nullable=True),
    Column("pdf_path", String(512), nullable=True),
    Column("citations_json", Text, nullable=True),
)


class DatabaseManager:
    """Manages database connections and CRUD operations for Scrybe."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        # Ensure data directory exists for SQLite
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        metadata.create_all(self.engine)
        logger.info("Database initialized: %s", self.database_url)

    def get_session(self) -> Session:
        """Create a new database session."""
        return self.SessionLocal()

    # ── Run Management ──

    def create_run(self, pipeline_id: str, sources_count: int = 0) -> None:
        """Insert a new pipeline run record."""
        with self.get_session() as session:
            session.execute(
                insert(runs_table).values(
                    pipeline_id=pipeline_id,
                    sources_count=sources_count,
                    status="RUNNING",
                )
            )
            session.commit()

    def complete_run(
        self,
        pipeline_id: str,
        status: str = "COMPLETED",
        records_extracted: int = 0,
        report_path: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark a pipeline run as completed."""
        with self.get_session() as session:
            session.execute(
                runs_table.update()
                .where(runs_table.c.pipeline_id == pipeline_id)
                .values(
                    completed_at=datetime.now(timezone.utc),
                    status=status,
                    records_extracted=records_extracted,
                    report_path=report_path,
                    execution_metrics_json=json.dumps(metrics) if metrics else None,
                )
            )
            session.commit()

    # ── Compliance Audit ──

    def save_compliance_audit(self, pipeline_id: str, audit_data: Dict[str, Any]) -> None:
        """Persist a compliance audit record."""
        with self.get_session() as session:
            session.execute(
                insert(compliance_audits_table).values(
                    audit_id=audit_data.get("audit_id", ""),
                    pipeline_id=pipeline_id,
                    source_url=audit_data.get("source_url", ""),
                    robots_checked=audit_data.get("robots_checked", True),
                    robots_allowed=audit_data.get("robots_allowed", True),
                    crawl_delay_applied=audit_data.get("crawl_delay_applied_seconds", 2.5),
                    pii_scrubbed_count=audit_data.get("pii_scrubbed_count", 0),
                    compliance_status=audit_data.get("compliance_status", "APPROVED"),
                )
            )
            session.commit()

    # ── Raw Documents ──

    def save_raw_document(self, pipeline_id: str, doc_data: Dict[str, Any]) -> None:
        """Persist a raw scraped document record (without the full content)."""
        with self.get_session() as session:
            session.execute(
                insert(raw_documents_table).values(
                    pipeline_id=pipeline_id,
                    url=doc_data.get("url", ""),
                    domain=doc_data.get("domain", ""),
                    status_code=doc_data.get("status_code", 0),
                    content_hash=doc_data.get("content_hash", ""),
                    scrape_tier=doc_data.get("scrape_tier_used", "httpx"),
                    content_length=len(doc_data.get("content_markdown", "")),
                    pii_redacted=doc_data.get("pii_redacted", True),
                    robots_compliant=doc_data.get("robots_compliant", True),
                )
            )
            session.commit()

    # ── Extracted Records ──

    def save_extracted_record(self, pipeline_id: str, record_data: Dict[str, Any]) -> None:
        """Persist a structured extraction result."""
        pricing_json = json.dumps(
            [t if isinstance(t, dict) else t.model_dump() for t in record_data.get("pricing_tiers", [])],
            default=str,
        )
        with self.get_session() as session:
            session.execute(
                insert(extracted_records_table).values(
                    pipeline_id=pipeline_id,
                    company_name=record_data.get("company_name", ""),
                    product_name=record_data.get("product_name", ""),
                    source_url=record_data.get("source_url", ""),
                    extraction_confidence=record_data.get("extraction_confidence", 0.0),
                    citation_text=record_data.get("citation_text", ""),
                    pricing_data_json=pricing_json,
                    enterprise_terms_mentioned=record_data.get("enterprise_terms_mentioned", False),
                    rate_limits_summary=record_data.get("rate_limits_summary"),
                )
            )
            session.commit()

    def get_extracted_records(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Retrieve all extracted records for a pipeline run."""
        with self.get_session() as session:
            result = session.execute(
                select(extracted_records_table)
                .where(extracted_records_table.c.pipeline_id == pipeline_id)
            )
            rows = result.fetchall()
            records = []
            for row in rows:
                record = dict(row._mapping)
                record["pricing_tiers"] = json.loads(record.pop("pricing_data_json", "[]"))
                records.append(record)
            return records

    def get_latest_records_for_company(self, company_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most recent extraction records for a company."""
        with self.get_session() as session:
            result = session.execute(
                select(extracted_records_table)
                .where(extracted_records_table.c.company_name == company_name)
                .order_by(desc(extracted_records_table.c.extracted_at))
                .limit(limit)
            )
            rows = result.fetchall()
            records = []
            for row in rows:
                record = dict(row._mapping)
                record["pricing_tiers"] = json.loads(record.pop("pricing_data_json", "[]"))
                records.append(record)
            return records

    # ── Strategic Insights ──

    def save_strategic_insight(self, pipeline_id: str, insight_data: Dict[str, Any]) -> None:
        """Persist a strategic recommendation."""
        with self.get_session() as session:
            session.execute(
                insert(strategic_insights_table).values(
                    pipeline_id=pipeline_id,
                    category=insight_data.get("category", ""),
                    title=insight_data.get("title", ""),
                    rationale=insight_data.get("rationale", ""),
                    actionable_next_step=insight_data.get("actionable_next_step", ""),
                    corroborating_sources_json=json.dumps(
                        insight_data.get("corroborating_sources", [])
                    ),
                    corroboration_count=insight_data.get("corroboration_count", 1),
                )
            )
            session.commit()

    # ── Reports ──

    def save_report(self, report_data: Dict[str, Any]) -> None:
        """Persist a generated report record."""
        with self.get_session() as session:
            session.execute(
                insert(reports_table).values(
                    report_id=report_data.get("report_id", ""),
                    pipeline_id=report_data.get("pipeline_id", ""),
                    title=report_data.get("title", ""),
                    target_vertical=report_data.get("target_vertical", ""),
                    executive_summary=report_data.get("executive_summary"),
                    markdown_content=report_data.get("markdown_content"),
                    pdf_path=report_data.get("pdf_path"),
                    citations_json=json.dumps(report_data.get("citations", [])),
                )
            )
            session.commit()

    def get_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve the most recent reports."""
        with self.get_session() as session:
            result = session.execute(
                select(reports_table).order_by(desc(reports_table.c.generated_at)).limit(limit)
            )
            return [dict(row._mapping) for row in result.fetchall()]

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single report by its ID."""
        with self.get_session() as session:
            result = session.execute(
                select(reports_table).where(reports_table.c.report_id == report_id)
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
