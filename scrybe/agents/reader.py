"""Scrybe Reader Agent.

Orchestrates tiered web scraping with automatic tier escalation:
Tier 1 (httpx) → Tier 2 (curl_cffi) → Tier 3 (Crawl4AI/Playwright).

Each tier respects compliance gates and politeness delays.
"""

import asyncio
import hashlib
import logging
import random
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from scrybe.agents.compliance import ComplianceAgent, ComplianceException
from scrybe.exceptions import ScrapingError, TierEscalationExhaustedError
from scrybe.logging_config import get_agent_logger
from scrybe.memory.buffer import RollingBuffer
from scrybe.storage.models import RawScrapedDocument, ScrapeTier, SourceTargetConfig
from scrybe.tools.extractor import clean_html_to_text

logger = get_agent_logger("reader")


class ReaderAgent:
    """Autonomous agent responsible for web content ingestion.

    Implements tiered scraping with automatic escalation, compliance
    pre-flight checks, PII scrubbing, and content hashing.
    """

    def __init__(
        self,
        compliance_agent: Optional[ComplianceAgent] = None,
        buffer: Optional[RollingBuffer] = None,
        user_agent: str = "Scrybe/1.0 (+https://scrybe.ai/bot; contact@scrybe.ai)",
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
    ):
        self.compliance = compliance_agent or ComplianceAgent(user_agent=user_agent)
        self.buffer = buffer or RollingBuffer()
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }

    async def run(self, sources: List[SourceTargetConfig]) -> List[RawScrapedDocument]:
        """Scrape all enabled sources with tiered escalation.

        Args:
            sources: List of source configurations to scrape.

        Returns:
            List of successfully scraped documents.
        """
        documents = []
        for source in sources:
            if not source.enabled:
                continue

            try:
                doc = await self._scrape_with_escalation(source)
                documents.append(doc)
                self.buffer.record(
                    agent="reader",
                    action=f"scraped_{source.id}",
                    status="OK",
                    source_url=source.target_url,
                    metadata={"tier": doc.scrape_tier_used.value, "hash": doc.content_hash[:12]},
                )
                logger.info(
                    f"Successfully scraped {source.company_name}",
                    extra={
                        "agent": "reader",
                        "step": "scrape_complete",
                        "source_url": source.target_url,
                        "scrape_tier": doc.scrape_tier_used.value,
                        "domain": source.company_name,
                    },
                )
            except ComplianceException as e:
                self.buffer.record(
                    agent="reader", action=f"compliance_blocked_{source.id}",
                    status="SKIPPED", source_url=source.target_url, error=str(e),
                )
                logger.warning(f"Compliance blocked {source.company_name}: {e}")
            except Exception as e:
                self.buffer.record(
                    agent="reader", action=f"scrape_failed_{source.id}",
                    status="ERROR", source_url=source.target_url, error=str(e),
                )
                logger.error(f"Failed to scrape {source.company_name}: {e}")

        return documents

    async def _scrape_with_escalation(self, source: SourceTargetConfig) -> RawScrapedDocument:
        """Attempt scraping with tier escalation on failure.

        Order: preferred_tier → next tier → ... → Tier 3 (Playwright).
        """
        tiers = self._get_tier_order(source.preferred_tier)

        last_error = None
        for tier in tiers:
            try:
                if tier == ScrapeTier.TIER1_HTTPX:
                    return await self._scrape_tier1(source)
                elif tier == ScrapeTier.TIER2_CURL_CFFI:
                    return await self._scrape_tier2(source)
                elif tier == ScrapeTier.TIER3_PLAYWRIGHT:
                    return await self._scrape_tier3(source)
            except Exception as e:
                last_error = e
                logger.warning(f"Tier {tier.value} failed for {source.company_name}: {e}")
                continue

        raise TierEscalationExhaustedError(
            f"All scraping tiers exhausted for {source.target_url}: {last_error}"
        )

    def _get_tier_order(self, preferred: ScrapeTier) -> List[ScrapeTier]:
        """Determine tier escalation order starting from preferred."""
        all_tiers = [ScrapeTier.TIER1_HTTPX, ScrapeTier.TIER2_CURL_CFFI, ScrapeTier.TIER3_PLAYWRIGHT]
        if preferred in all_tiers:
            idx = all_tiers.index(preferred)
            return all_tiers[idx:]
        return all_tiers

    async def _scrape_tier1(self, source: SourceTargetConfig) -> RawScrapedDocument:
        """Tier 1: Fast async HTTP via httpx."""
        audit = self.compliance.check_preflight(source.target_url)
        delay = audit.crawl_delay_applied_seconds + random.uniform(0.1, 0.5)
        await asyncio.sleep(min(delay, 5.0))

        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout,
            follow_redirects=True, http2=True,
        ) as client:
            response = await client.get(source.target_url)
            response.raise_for_status()
            raw_html = response.text

        # Check if content is too thin (likely JS-rendered SPA)
        cleaned = clean_html_to_text(raw_html)
        if len(cleaned.strip()) < 100:
            raise ScrapingError(f"Tier 1 returned thin content ({len(cleaned)} chars) — likely SPA")

        return self._build_document(source, raw_html, cleaned, response.status_code, ScrapeTier.TIER1_HTTPX)

    async def _scrape_tier2(self, source: SourceTargetConfig) -> RawScrapedDocument:
        """Tier 2: TLS-impersonating HTTP via curl_cffi."""
        audit = self.compliance.check_preflight(source.target_url)
        delay = audit.crawl_delay_applied_seconds + random.uniform(0.1, 0.5)
        await asyncio.sleep(min(delay, 5.0))

        try:
            from curl_cffi.requests import AsyncSession
        except ImportError:
            raise ScrapingError("curl_cffi not installed — cannot use Tier 2. Run: pip install curl_cffi")

        async with AsyncSession() as session:
            response = await session.get(
                source.target_url,
                impersonate="chrome120",
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                raise ScrapingError(f"Tier 2 returned HTTP {response.status_code}")
            raw_html = response.text

        cleaned = clean_html_to_text(raw_html)
        if len(cleaned.strip()) < 100:
            raise ScrapingError(f"Tier 2 returned thin content ({len(cleaned)} chars)")

        return self._build_document(source, raw_html, cleaned, response.status_code, ScrapeTier.TIER2_CURL_CFFI)

    async def _scrape_tier3(self, source: SourceTargetConfig) -> RawScrapedDocument:
        """Tier 3: Headless browser via Playwright (or Crawl4AI)."""
        audit = self.compliance.check_preflight(source.target_url)
        delay = audit.crawl_delay_applied_seconds + random.uniform(0.5, 1.0)
        await asyncio.sleep(min(delay, 5.0))

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ScrapingError("playwright not installed — cannot use Tier 3. Run: pip install playwright && playwright install")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                await page.goto(source.target_url, wait_until="networkidle", timeout=30000)
                # Wait for dynamic content
                await page.wait_for_timeout(2000)
                raw_html = await page.content()
            finally:
                await browser.close()

        cleaned = clean_html_to_text(raw_html)
        return self._build_document(source, raw_html, cleaned, 200, ScrapeTier.TIER3_PLAYWRIGHT)

    def _build_document(
        self,
        source: SourceTargetConfig,
        raw_html: str,
        cleaned_text: str,
        status_code: int,
        tier: ScrapeTier,
    ) -> RawScrapedDocument:
        """Build a RawScrapedDocument with PII scrubbing and hashing."""
        # PII scrubbing
        scrubbed_text, pii_count = self.compliance.scrub_pii(cleaned_text)

        # Content hash for delta detection
        content_hash = hashlib.sha256(scrubbed_text.encode("utf-8")).hexdigest()
        domain = urlparse(source.target_url).hostname or ""

        return RawScrapedDocument(
            url=source.target_url,
            domain=domain,
            status_code=status_code,
            content_markdown=scrubbed_text,
            content_hash=content_hash,
            scrape_tier_used=tier,
            pii_redacted=pii_count > 0 or True,
            robots_compliant=True,
        )
