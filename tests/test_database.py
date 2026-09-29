"""Tests for Scrybe database operations."""

import json
import os
import pytest
from pathlib import Path

from scrybe.storage.db import DatabaseManager


@pytest.fixture
def db(tmp_path):
    """Create a test database in a temporary directory."""
    db_path = tmp_path / "test_scrybe.db"
    db_url = f"sqlite:///{db_path}"
    return DatabaseManager(database_url=db_url)


class TestDatabaseManager:
    """Tests for CRUD operations."""

    def test_create_and_complete_run(self, db):
        db.create_run("pipe_test_001", sources_count=5)
        db.complete_run("pipe_test_001", status="COMPLETED", records_extracted=3)

    def test_save_and_retrieve_compliance_audit(self, db):
        db.save_compliance_audit("pipe_test_001", {
            "audit_id": "audit_abc123",
            "source_url": "https://openai.com/api/pricing/",
            "robots_checked": True,
            "robots_allowed": True,
            "crawl_delay_applied_seconds": 2.5,
            "pii_scrubbed_count": 0,
            "compliance_status": "APPROVED",
        })

    def test_save_and_retrieve_extracted_record(self, db):
        db.save_extracted_record("pipe_test_001", {
            "company_name": "OpenAI",
            "product_name": "API",
            "source_url": "https://openai.com/api/pricing/",
            "extraction_confidence": 0.92,
            "citation_text": "GPT-4o costs $2.50/1M input tokens",
            "pricing_tiers": [
                {"model_or_tier_name": "GPT-4o", "input_price_per_m_tokens": 2.50}
            ],
            "enterprise_terms_mentioned": True,
        })

        records = db.get_extracted_records("pipe_test_001")
        assert len(records) == 1
        assert records[0]["company_name"] == "OpenAI"
        assert len(records[0]["pricing_tiers"]) == 1

    def test_save_and_retrieve_report(self, db):
        db.save_report({
            "report_id": "rpt_test_001",
            "pipeline_id": "pipe_test_001",
            "title": "Test Report",
            "target_vertical": "B2B_AI",
            "executive_summary": "Summary text",
            "markdown_content": "# Report\nContent here",
            "citations": ["https://openai.com"],
        })

        reports = db.get_reports(limit=10)
        assert len(reports) >= 1

        report = db.get_report_by_id("rpt_test_001")
        assert report is not None
        assert report["title"] == "Test Report"

    def test_get_nonexistent_report(self, db):
        result = db.get_report_by_id("nonexistent_id")
        assert result is None

    def test_save_strategic_insight(self, db):
        db.save_strategic_insight("pipe_test_001", {
            "category": "PRICING",
            "title": "Test Recommendation",
            "rationale": "Because reasons.",
            "actionable_next_step": "Do this.",
            "corroborating_sources": ["https://openai.com", "https://anthropic.com"],
            "corroboration_count": 2,
        })
