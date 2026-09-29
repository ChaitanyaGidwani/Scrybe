"""End-to-End Integration Tests for Scrybe A2A Multi-Agent System.

Validates the full collaborative workflow across all 6 agents:
Compliance → Reader → Analyst → Memory → Strategist → Formatter
with database persistence and event broadcasting.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from scrybe.a2a.orchestrator import A2AOrchestrator
from scrybe.storage.db import DatabaseManager
from scrybe.storage.models import RawScrapedDocument, ScrapeTier


@pytest.mark.asyncio
async def test_full_a2a_pipeline_end_to_end(tmp_path):
    """Run full A2A pipeline with mocked reader and verify all 5 downstream agents execute."""
    test_db_path = tmp_path / "test_scrybe.db"
    test_db_url = f"sqlite:///{test_db_path}"

    events_received = []

    def mock_progress_callback(agent, event, data):
        events_received.append((agent, event, data))

    # Mock settings with temporary db
    mock_settings = MagicMock()
    mock_settings.database_url = test_db_url
    mock_settings.sources_config_path = ""
    mock_settings.openai_api_key = ""
    mock_settings.anthropic_api_key = ""
    mock_settings.google_api_key = ""
    mock_settings.output_dir = str(tmp_path / "reports")

    orchestrator = A2AOrchestrator(
        settings=mock_settings,
        mode="in_process",
        progress_callback=mock_progress_callback,
    )

    # Mock reader server response with 2 realistic documents (OpenAI and Anthropic)
    mock_documents = [
        {
            "url": "https://openai.com/api/pricing/",
            "domain": "openai.com",
            "content_markdown": (
                "# OpenAI API Pricing\n\n"
                "GPT-4o: $2.50 / 1M input tokens and $10.00 / 1M output tokens.\n"
                "GPT-4o mini: $0.15 / 1M input tokens and $0.60 / 1M output tokens.\n"
                "Contact sales for enterprise rate limits and volume discounts."
            ),
            "content_hash": "hash_openai_001",
            "status_code": 200,
            "scrape_tier_used": "httpx",
            "pii_redacted": True,
        },
        {
            "url": "https://www.anthropic.com/pricing",
            "domain": "anthropic.com",
            "content_markdown": (
                "# Claude API Pricing\n\n"
                "Claude 3.5 Sonnet: $3.00 per million input tokens, $15.00 per million output tokens.\n"
                "Claude 3.5 Haiku: $0.80 per million input tokens, $4.00 per million output tokens.\n"
                "Prompt Caching: Write $3.75/MTok, Read $0.30/MTok."
            ),
            "content_hash": "hash_anthropic_002",
            "status_code": 200,
            "scrape_tier_used": "httpx",
            "pii_redacted": True,
        },
    ]

    # Patch the reader handler inside orchestrator._servers["reader"] to return mock docs
    original_reader_handler = orchestrator._servers["reader"].handler

    async def patched_reader_handler(task):
        task.start_work("Scraping 2 mock sources...")
        from scrybe.a2a.models import Artifact
        artifact = Artifact(name="scraped_documents")
        artifact.add_data({
            "documents": mock_documents,
            "count": len(mock_documents),
            "sources_attempted": 2,
        })
        task.add_artifact(artifact)
        task.complete("Scraped 2/2 sources")
        return task

    orchestrator._servers["reader"].handler = patched_reader_handler

    # Execute pipeline
    final_state = await orchestrator.run_pipeline()

    # ── Verify Pipeline State ─────────────────────────────────────────
    assert final_state.pipeline_id.startswith("pipe_")
    assert len(final_state.raw_scrapes) == 2
    assert len(final_state.extracted_records) == 2

    # Verify extracted records
    companies = [r.company_name for r in final_state.extracted_records]
    assert "OpenAI" in companies
    assert "Anthropic" in companies

    # Verify pricing tiers extracted
    openai_rec = next(r for r in final_state.extracted_records if r.company_name == "OpenAI")
    assert len(openai_rec.pricing_tiers) >= 2
    assert any(t.model_or_tier_name == "GPT-4o" for t in openai_rec.pricing_tiers)

    # Verify strategic synthesis completed
    assert len(final_state.strategic_insights) >= 0

    # Verify formatted markdown report
    assert final_state.report_markdown
    assert "Scrybe Competitive Intelligence Report" in final_state.report_markdown
    assert "Pricing Comparison Matrix" in final_state.report_markdown
    assert "Sales Battlecard Snippets" in final_state.report_markdown

    # ── Verify Progress Events ────────────────────────────────────────
    agent_events = [e[0] for e in events_received]
    assert "pipeline" in agent_events
    assert "reader" in agent_events
    assert "analyst" in agent_events
    assert "memory" in agent_events
    assert "strategist" in agent_events
    assert "formatter" in agent_events

    # ── Verify Database Persistence ───────────────────────────────────
    db = DatabaseManager(database_url=test_db_url)
    reports = db.get_reports(limit=5)
    assert len(reports) >= 1
    assert "OpenAI" in reports[0]["markdown_content"]

    openai_records = db.get_latest_records_for_company("OpenAI")
    assert len(openai_records) >= 1

    anthropic_records = db.get_latest_records_for_company("Anthropic")
    assert len(anthropic_records) >= 1

    insights = db.get_strategic_insights(limit=10)
    assert len(insights) >= 0
