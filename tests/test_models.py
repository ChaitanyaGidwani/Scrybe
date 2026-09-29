"""Unit tests for Scrybe core models and state validation."""

import pytest
from pydantic import ValidationError
from scrybe.storage.models import (
    PricingTier,
    CompetitorProductRecord,
    ScrybeState,
    TrendDelta,
    DeltaType,
    StrategicRecommendation,
    ComplianceAuditRecord,
    ScrapeTier,
)


def test_pricing_tier_defaults_to_null_for_missing_values():
    """Verify that unspecified prices remain null/None without hallucinated defaults."""
    tier = PricingTier(model_or_tier_name="GPT-4o")
    assert tier.input_price_per_m_tokens is None
    assert tier.output_price_per_m_tokens is None
    assert tier.cache_read_price_per_m_tokens is None
    assert tier.fixed_monthly_price is None
    assert tier.currency == "USD"
    assert tier.notable_features == []


def test_pricing_tier_with_values():
    """Verify valid population of normalized token metrics."""
    tier = PricingTier(
        model_or_tier_name="Claude 3.5 Sonnet",
        input_price_per_m_tokens=3.00,
        output_price_per_m_tokens=15.00,
        cache_read_price_per_m_tokens=0.30,
        context_window_tokens=200000,
    )
    assert tier.input_price_per_m_tokens == 3.00
    assert tier.output_price_per_m_tokens == 15.00
    assert tier.context_window_tokens == 200000


def test_competitor_record_confidence_bounds():
    """Confidence score must be strictly between 0.0 and 1.0."""
    tier = PricingTier(model_or_tier_name="Base")
    
    # Valid confidence
    record = CompetitorProductRecord(
        company_name="OpenAI",
        product_name="API",
        source_url="https://openai.com/api/pricing/",
        pricing_tiers=[tier],
        extraction_confidence=0.95,
        citation_text="GPT-4o costs $2.50 / 1M input tokens.",
    )
    assert record.extraction_confidence == 0.95

    # Invalid confidence > 1.0
    with pytest.raises(ValidationError):
        CompetitorProductRecord(
            company_name="OpenAI",
            product_name="API",
            source_url="https://openai.com/api/pricing/",
            pricing_tiers=[tier],
            extraction_confidence=1.5,
            citation_text="Snippet",
        )


def test_scrybe_state_initialization():
    """Verify sequential state container initialization."""
    state = ScrybeState(pipeline_id="pipe_20260929_001")
    assert state.pipeline_id == "pipe_20260929_001"
    assert len(state.raw_scrapes) == 0
    assert len(state.extracted_records) == 0
    assert len(state.strategic_insights) == 0
