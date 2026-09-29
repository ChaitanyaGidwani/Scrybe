"""Scrybe Grounding Validator.

Validates extracted data against source content to ensure no hallucinations.
Calculates confidence scores based on DOM grounding, schema completeness,
and cross-field sanity checks.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from scrybe.storage.models import CompetitorProductRecord, PricingTier
from scrybe.exceptions import ConfidenceBelowThresholdError
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("validator")


def calculate_confidence(
    extracted: Dict[str, Any],
    source_text: str,
) -> float:
    """Calculate extraction confidence score.

    Formula: 0.5 × DOM_Grounding + 0.3 × Schema_Completeness + 0.2 × Cross_Field_Sanity

    Args:
        extracted: The extracted record dictionary.
        source_text: The cleaned source text for grounding verification.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    dom_grounding = _score_dom_grounding(extracted, source_text)
    schema_completeness = _score_schema_completeness(extracted)
    cross_field_sanity = _score_cross_field_sanity(extracted)

    confidence = (0.5 * dom_grounding) + (0.3 * schema_completeness) + (0.2 * cross_field_sanity)

    # Grounding gate: if data is not grounded in source DOM, cap confidence below threshold
    if dom_grounding < 0.25:
        confidence = min(confidence, 0.40)

    return round(min(max(confidence, 0.0), 1.0), 3)


def validate_record(
    extracted: Dict[str, Any],
    source_text: str,
    confidence_threshold: float = 0.60,
) -> Tuple[CompetitorProductRecord, bool]:
    """Validate an extracted record and construct a typed model.

    Args:
        extracted: Raw extracted dictionary from LLM.
        source_text: The cleaned source text for grounding checks.
        confidence_threshold: Minimum confidence to consider record valid.

    Returns:
        Tuple of (validated CompetitorProductRecord, is_above_threshold).
    """
    # Override LLM confidence with our calculated score
    confidence = calculate_confidence(extracted, source_text)
    extracted["extraction_confidence"] = confidence

    # Build validated Pydantic model
    tiers = []
    for tier_data in extracted.get("pricing_tiers", []):
        tiers.append(PricingTier(**tier_data))

    record = CompetitorProductRecord(
        company_name=extracted.get("company_name", "Unknown"),
        product_name=extracted.get("product_name", "Unknown"),
        source_url=extracted.get("source_url", ""),
        pricing_tiers=tiers,
        enterprise_terms_mentioned=extracted.get("enterprise_terms_mentioned", False),
        rate_limits_summary=extracted.get("rate_limits_summary"),
        extraction_confidence=confidence,
        citation_text=extracted.get("citation_text", ""),
    )

    is_above_threshold = confidence >= confidence_threshold

    logger.info(
        "Validation complete",
        extra={
            "agent": "validator",
            "step": "validate_record",
            "source_url": record.source_url,
            "confidence": confidence,
        },
    )

    return record, is_above_threshold


def _score_dom_grounding(extracted: Dict[str, Any], source_text: str) -> float:
    """Score how well the extracted values are grounded in the source text.

    Checks if key price values and model names appear verbatim in the source.
    """
    source_lower = source_text.lower()
    checks = 0
    matches = 0

    # Check company name
    company = extracted.get("company_name", "")
    if company:
        checks += 1
        if company.lower() in source_lower:
            matches += 1

    # Check citation text exists in source
    citation = extracted.get("citation_text", "")
    if citation and len(citation) > 5:
        checks += 1
        # Allow partial match (at least 60% of words found)
        citation_words = citation.lower().split()
        found_words = sum(1 for w in citation_words if w in source_lower)
        if found_words >= len(citation_words) * 0.6:
            matches += 1

    # Check model/tier names from pricing tiers
    for tier in extracted.get("pricing_tiers", []):
        name = tier.get("model_or_tier_name", "")
        if name:
            checks += 1
            if name.lower() in source_lower:
                matches += 1

        # Check if price values are plausible (appear as numbers in source)
        for price_key in ("input_price_per_m_tokens", "output_price_per_m_tokens"):
            val = tier.get(price_key)
            if val is not None:
                checks += 1
                # Look for the number in any reasonable format in source
                val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
                short_val = val_str.rstrip("0").rstrip(".")
                if short_val in source_text or val_str in source_text:
                    matches += 1

    if checks == 0:
        return 0.5  # No data to ground → middle confidence
    return matches / checks


def _score_schema_completeness(extracted: Dict[str, Any]) -> float:
    """Score how completely the extraction filled in the required schema fields."""
    total_fields = 0
    filled_fields = 0

    # Top-level required fields
    for field in ("company_name", "product_name", "source_url", "citation_text"):
        total_fields += 1
        if extracted.get(field):
            filled_fields += 1

    # Pricing tiers presence
    tiers = extracted.get("pricing_tiers", [])
    total_fields += 1
    if tiers:
        filled_fields += 1

    # Per-tier completeness
    for tier in tiers:
        for key in ("model_or_tier_name", "input_price_per_m_tokens", "output_price_per_m_tokens"):
            total_fields += 1
            if tier.get(key) is not None:
                filled_fields += 1

    if total_fields == 0:
        return 0.0
    return filled_fields / total_fields


def _score_cross_field_sanity(extracted: Dict[str, Any]) -> float:
    """Score internal consistency of extracted data.

    Checks for obviously wrong values like negative prices or
    impossibly large context windows.
    """
    issues = 0
    checks = 0

    for tier in extracted.get("pricing_tiers", []):
        # Price sanity: must be non-negative
        for price_key in ("input_price_per_m_tokens", "output_price_per_m_tokens",
                          "cache_read_price_per_m_tokens", "fixed_monthly_price"):
            val = tier.get(price_key)
            if val is not None:
                checks += 1
                if val < 0:
                    issues += 1
                if val > 10000:
                    issues += 1  # Suspiciously high for per-1M token pricing

        # Context window sanity
        ctx = tier.get("context_window_tokens")
        if ctx is not None:
            checks += 1
            if ctx < 0 or ctx > 10_000_000:
                issues += 1

        # Output should generally be >= input price (for most models)
        inp = tier.get("input_price_per_m_tokens")
        out = tier.get("output_price_per_m_tokens")
        if inp is not None and out is not None:
            checks += 1
            if out < inp * 0.1:
                # Output price unrealistically low vs input
                issues += 0.5

    if checks == 0:
        return 1.0  # No data to check → assume sane
    return max(0.0, 1.0 - (issues / checks))
