"""Unit tests for Scrybe Tier 1 HTTP Scraper."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from scrybe.agents.compliance import ComplianceAgent
from scrybe.tools.scraper import Tier1Scraper
from scrybe.storage.models import ScrapeTier


@pytest.mark.asyncio
async def test_scraper_fetches_and_redacts(monkeypatch):
    """Verify that scraper coordinates compliance pre-flight, fetches, and redacts PII."""
    compliance = ComplianceAgent()
    monkeypatch.setattr(compliance, "_evaluate_robots_txt", lambda host, url: (True, 0.0))

    scraper = Tier1Scraper(compliance_agent=compliance)

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><body><h1>OpenAI API Pricing</h1>"
        "<p>Contact sales at support@openai.com or call 555-123-4567.</p>"
        "<p>GPT-4o costs $2.50 per 1M input tokens.</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        doc = await scraper.fetch_page("https://openai.com/api/pricing/")

        assert doc.status_code == 200
        assert doc.domain == "openai.com"
        assert doc.scrape_tier_used == ScrapeTier.TIER1_HTTPX
        assert "[REDACTED_EMAIL]" in doc.content_markdown
        assert "support@openai.com" not in doc.content_markdown
        assert "[REDACTED_PHONE]" in doc.content_markdown
        assert "GPT-4o costs $2.50 per 1M input tokens." in doc.content_markdown
        assert doc.content_hash is not None
        assert doc.pii_redacted is True
