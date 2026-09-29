"""Scrybe Custom Exception Hierarchy.

All exceptions inherit from ScrybeError for clean catch-all handling.
Never swallow errors silently — log structured JSON and re-raise.
"""


class ScrybeError(Exception):
    """Base exception for all Scrybe errors."""


class ComplianceError(ScrybeError):
    """Raised when a compliance check fails (robots.txt, PII, SSRF)."""


class RobotsDisallowedError(ComplianceError):
    """Raised when target path is disallowed by robots.txt."""


class SSRFProtectionError(ComplianceError):
    """Raised when a URL targets internal/private network addresses."""


class ScrapingError(ScrybeError):
    """Raised when a scraping operation fails after all tier escalations."""


class TierEscalationExhaustedError(ScrapingError):
    """All scraping tiers (httpx → curl_cffi → playwright) failed."""


class ExtractionError(ScrybeError):
    """Raised when LLM-based extraction fails to produce valid output."""


class ValidationError(ScrybeError):
    """Raised when extracted data fails Pydantic schema validation."""


class ConfidenceBelowThresholdError(ScrybeError):
    """Raised when extraction confidence is below the required threshold."""


class CorroborationError(ScrybeError):
    """Raised when a strategic claim cannot be corroborated by ≥2 sources."""


class DatabaseError(ScrybeError):
    """Raised when a database operation fails."""


class ReportGenerationError(ScrybeError):
    """Raised when report formatting/export fails."""


class LLMError(ScrybeError):
    """Raised when an LLM API call fails."""


class RateLimitError(ScrybeError):
    """Raised when rate limits are exceeded for a domain or API."""
