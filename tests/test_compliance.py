"""Unit tests for Scrybe Compliance Agent."""

import pytest
from scrybe.agents.compliance import ComplianceAgent, ComplianceException, RobotsDisallowedException


def test_compliance_pii_scrubbing():
    """Verify that sensitive PII (emails, phones, IDs) are sanitized."""
    agent = ComplianceAgent()
    dirty_text = (
        "For sales inquiries, contact alice.smith@competitor.ai or call +1 (555) 234-5678. "
        "Tax ID: 123-45-6789. Base rate is $20/month."
    )
    clean_text, count = agent.scrub_pii(dirty_text)

    assert "[REDACTED_EMAIL]" in clean_text
    assert "alice.smith@competitor.ai" not in clean_text
    assert "[REDACTED_PHONE]" in clean_text
    assert "(555) 234-5678" not in clean_text
    assert "[REDACTED_ID]" in clean_text
    assert "$20/month" in clean_text
    assert count == 3


def test_compliance_ssrf_protection_http():
    """Reject plain HTTP schemes for security."""
    agent = ComplianceAgent()
    with pytest.raises(ComplianceException, match="Only HTTPS URLs are allowed"):
        agent.check_preflight("http://example.com/pricing")


def test_compliance_ssrf_protection_internal_ip():
    """Reject requests targeting internal or loopback IP ranges."""
    agent = ComplianceAgent()
    with pytest.raises(ComplianceException, match="strictly forbidden"):
        agent.check_preflight("https://127.0.0.1/admin")

    with pytest.raises(ComplianceException, match="strictly forbidden"):
        agent.check_preflight("https://10.0.0.5/secrets")


def test_compliance_preflight_approval_mocked(monkeypatch):
    """Verify approval of standard public HTTPS endpoint."""
    agent = ComplianceAgent()

    # Mock _evaluate_robots_txt to avoid live network query during test
    monkeypatch.setattr(agent, "_evaluate_robots_txt", lambda host, url: (True, 2.5))

    audit = agent.check_preflight("https://openai.com/api/pricing/")
    assert audit.compliance_status == "APPROVED"
    assert audit.robots_allowed is True
    assert audit.crawl_delay_applied_seconds >= 2.5
    assert audit.source_url == "https://openai.com/api/pricing/"
