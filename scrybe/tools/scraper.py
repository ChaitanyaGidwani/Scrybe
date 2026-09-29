"""Tier 1 HTTP Scraping Tool for Scrybe.

Executes polite, asynchronous HTTP/2 requests using httpx.
Serves as the high-speed Tier 1 ingestion mechanism before escalating to
Tier 2 (curl_cffi) or Tier 3 (Crawl4AI / Playwright).
"""

import asyncio
import hashlib
import random
import time
from typing import Optional
from urllib.parse import urlparse
import httpx

from scrybe.agents.compliance import ComplianceAgent, ComplianceException
from scrybe.storage.models import RawScrapedDocument, ScrapeTier


class Tier1Scraper:
    """Polite async HTTP scraper for static and SSR web pages."""

    def __init__(
        self,
        compliance_agent: Optional[ComplianceAgent] = None,
        timeout_seconds: float = 15.0,
        user_agent: str = "Scrybe/1.0 (+https://scrybe.ai/bot; contact@scrybe.ai)",
    ):
        self.compliance = compliance_agent or ComplianceAgent(user_agent=user_agent)
        self.timeout = timeout_seconds
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
        }

    async def fetch_page(self, target_url: str) -> RawScrapedDocument:
        """Fetch URL content via Tier 1 HTTP.

        Args:
            target_url: Public target URL to fetch.

        Returns:
            RawScrapedDocument containing raw content and metadata.

        Raises:
            ComplianceException: If compliance pre-flight checks fail.
            httpx.HTTPError: If network request fails.
        """
        # 1. Compliance Pre-Flight Gate
        audit_record = self.compliance.check_preflight(target_url)

        # 2. Politeness jitter delay
        delay = audit_record.crawl_delay_applied_seconds + random.uniform(0.1, 0.5)
        await asyncio.sleep(min(delay, 5.0))  # Cap delay at 5s in dev

        # 3. Network Request
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
            http2=True,
        ) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            raw_text = response.text

        # 4. Post-Scrape Compliance PII Scrubbing
        clean_text, scrub_count = self.compliance.scrub_pii(raw_text)

        # 5. Content Hashing (SHA-256)
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        domain = urlparse(target_url).hostname or ""

        return RawScrapedDocument(
            url=target_url,
            domain=domain,
            status_code=response.status_code,
            content_markdown=clean_text,
            content_hash=content_hash,
            scrape_tier_used=ScrapeTier.TIER1_HTTPX,
            pii_redacted=True,
            robots_compliant=True,
        )
