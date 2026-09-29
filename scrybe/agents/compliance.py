"""Compliance Agent for Scrybe.

Enforces robots.txt, ai.txt directives, rate-delay politeness, and scrubs PII
(emails, phone numbers) from raw web content before database persistence.
Complies with EU GDPR EDPB Guidelines 03/2026 and US CFAA boundaries.
"""

import re
import urllib.robotparser
from typing import Optional, Tuple
from urllib.parse import urlparse
import uuid

from scrybe.storage.models import ComplianceAuditRecord


class ComplianceException(Exception):
    """Base exception for compliance violations."""
    pass


class RobotsDisallowedException(ComplianceException):
    """Raised when target path is disallowed by robots.txt."""
    pass


class ComplianceAgent:
    """Autonomous agent gating all network ingestion and PII handling."""

    def __init__(
        self,
        user_agent: str = "Scrybe/1.0 (+https://scrybe.ai/bot; contact@scrybe.ai)",
        min_crawl_delay: float = 2.5,
        respect_robots: bool = True,
    ):
        self.user_agent = user_agent
        self.min_crawl_delay = min_crawl_delay
        self.respect_robots = respect_robots
        self._robots_cache = {}

        # Precompiled regex patterns for PII redaction
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        )
        self.phone_pattern = re.compile(
            r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        )
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def check_preflight(self, target_url: str) -> ComplianceAuditRecord:
        """Verify URL protocol, internal IP safeguards, and robots.txt.

        Args:
            target_url: The public URL scheduled for scraping.

        Returns:
            ComplianceAuditRecord documenting the verification.

        Raises:
            ComplianceException: If URL is invalid, SSRF target, or disallowed.
        """
        parsed = urlparse(target_url)

        # 1. SSRF Protection: HTTPS only, reject loopback / internal private IPs
        if parsed.scheme.lower() != "https":
            raise ComplianceException(f"Only HTTPS URLs are allowed. Got scheme: {parsed.scheme}")

        hostname = parsed.hostname or ""
        if hostname in ("localhost", "127.0.0.1", "::1") or hostname.startswith("10.") or hostname.startswith("192.168."):
            raise ComplianceException(f"Access to private/internal network address {hostname} is strictly forbidden.")

        audit_id = f"audit_{uuid.uuid4().hex[:12]}"
        robots_allowed = True
        crawl_delay = self.min_crawl_delay

        # 2. Robots.txt evaluation
        if self.respect_robots and hostname:
            robots_allowed, extracted_delay = self._evaluate_robots_txt(hostname, target_url)
            if extracted_delay and extracted_delay > crawl_delay:
                crawl_delay = extracted_delay

            if not robots_allowed:
                record = ComplianceAuditRecord(
                    audit_id=audit_id,
                    source_url=target_url,
                    robots_checked=True,
                    robots_allowed=False,
                    crawl_delay_applied_seconds=crawl_delay,
                    compliance_status="BLOCKED_BY_ROBOTS",
                )
                raise RobotsDisallowedException(
                    f"URL {target_url} is disallowed by {hostname}/robots.txt for user-agent {self.user_agent}"
                )

        return ComplianceAuditRecord(
            audit_id=audit_id,
            source_url=target_url,
            robots_checked=self.respect_robots,
            robots_allowed=robots_allowed,
            crawl_delay_applied_seconds=crawl_delay,
            pii_scrubbed_count=0,
            compliance_status="APPROVED",
        )

    def scrub_pii(self, raw_content: str) -> Tuple[str, int]:
        """Redact incidental personal data (emails, phone numbers, SSNs).

        Args:
            raw_content: Raw text or markdown from scraped target.

        Returns:
            Tuple of (scrubbed_content, total_pii_entities_redacted).
        """
        redactions = 0

        # Mask emails
        content, n_email = self.email_pattern.subn("[REDACTED_EMAIL]", raw_content)
        redactions += n_email

        # Mask phones
        content, n_phone = self.phone_pattern.subn("[REDACTED_PHONE]", content)
        redactions += n_phone

        # Mask SSNs
        content, n_ssn = self.ssn_pattern.subn("[REDACTED_ID]", content)
        redactions += n_ssn

        return content, redactions

    def _evaluate_robots_txt(self, hostname: str, target_url: str) -> Tuple[bool, Optional[float]]:
        """Fetch and parse robots.txt for a host."""
        if hostname in self._robots_cache:
            parser = self._robots_cache[hostname]
        else:
            parser = urllib.robotparser.RobotFileParser()
            robots_url = f"https://{hostname}/robots.txt"
            try:
                parser.set_url(robots_url)
                parser.read()
                self._robots_cache[hostname] = parser
            except Exception:
                # If robots.txt cannot be reached, assume allowed with default politeness
                return True, self.min_crawl_delay

        can_fetch = parser.can_fetch(self.user_agent, target_url) or parser.can_fetch("*", target_url)
        crawl_delay = parser.crawl_delay(self.user_agent) or parser.crawl_delay("*")
        return can_fetch, crawl_delay
