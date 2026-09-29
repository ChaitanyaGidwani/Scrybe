"""Unit tests for Scrybe grounding validator and confidence scoring."""

import pytest
from scrybe.tools.validator import (
    calculate_confidence,
    validate_record,
    _score_dom_grounding,
    _score_schema_completeness,
    _score_cross_field_sanity,
)


SOURCE_TEXT = """
OpenAI API Pricing
GPT-4o costs $2.50 per 1M input tokens and $10.00 per 1M output tokens.
Context window: 128,000 tokens.
GPT-4o mini costs $0.15 per 1M input tokens and $0.60 per 1M output tokens.
Enterprise plans available. Rate limits apply.
"""


class TestConfidenceScoring:
    """Tests for the 3-axis confidence scoring."""

    def test_high_confidence_well_grounded(self):
        extracted = {
            "company_name": "OpenAI",
            "product_name": "API",
            "source_url": "https://openai.com/api/pricing/",
            "citation_text": "GPT-4o costs $2.50 per 1M input tokens and $10.00",
            "pricing_tiers": [
                {
                    "model_or_tier_name": "GPT-4o",
                    "input_price_per_m_tokens": 2.50,
                    "output_price_per_m_tokens": 10.00,
                    "context_window_tokens": 128000,
                }
            ],
        }
        confidence = calculate_confidence(extracted, SOURCE_TEXT)
        assert confidence >= 0.7, f"Expected high confidence, got {confidence}"

    def test_low_confidence_hallucinated_values(self):
        extracted = {
            "company_name": "FakeCompany",
            "product_name": "FakeModel",
            "source_url": "https://fake.com",
            "citation_text": "Some completely made up text that doesnt match",
            "pricing_tiers": [
                {
                    "model_or_tier_name": "FakeModel-999",
                    "input_price_per_m_tokens": 999.99,
                    "output_price_per_m_tokens": 0.001,
                }
            ],
        }
        confidence = calculate_confidence(extracted, SOURCE_TEXT)
        assert confidence < 0.5, f"Expected low confidence for hallucinated data, got {confidence}"

    def test_empty_extraction(self):
        extracted = {
            "company_name": "",
            "product_name": "",
            "source_url": "",
            "citation_text": "",
            "pricing_tiers": [],
        }
        confidence = calculate_confidence(extracted, SOURCE_TEXT)
        assert 0.0 <= confidence <= 1.0


class TestDomGrounding:
    """Tests for DOM grounding sub-score."""

    def test_company_name_found(self):
        extracted = {"company_name": "OpenAI", "citation_text": "", "pricing_tiers": []}
        score = _score_dom_grounding(extracted, SOURCE_TEXT)
        assert score > 0.0

    def test_company_name_not_found(self):
        extracted = {"company_name": "NonExistentCorp", "citation_text": "", "pricing_tiers": []}
        score = _score_dom_grounding(extracted, SOURCE_TEXT)
        assert score < 1.0


class TestSchemaCompleteness:
    """Tests for schema completeness sub-score."""

    def test_fully_filled_schema(self):
        extracted = {
            "company_name": "OpenAI",
            "product_name": "API",
            "source_url": "https://openai.com",
            "citation_text": "test",
            "pricing_tiers": [
                {"model_or_tier_name": "GPT-4o", "input_price_per_m_tokens": 2.5, "output_price_per_m_tokens": 10.0}
            ],
        }
        score = _score_schema_completeness(extracted)
        assert score >= 0.8

    def test_empty_schema(self):
        extracted = {"company_name": "", "product_name": "", "source_url": "", "citation_text": "", "pricing_tiers": []}
        score = _score_schema_completeness(extracted)
        assert score < 0.5


class TestCrossFieldSanity:
    """Tests for cross-field sanity sub-score."""

    def test_sane_prices(self):
        extracted = {
            "pricing_tiers": [
                {"input_price_per_m_tokens": 2.50, "output_price_per_m_tokens": 10.00, "context_window_tokens": 128000}
            ]
        }
        score = _score_cross_field_sanity(extracted)
        assert score >= 0.8

    def test_negative_prices(self):
        extracted = {
            "pricing_tiers": [
                {"input_price_per_m_tokens": -5.00, "output_price_per_m_tokens": 10.00}
            ]
        }
        score = _score_cross_field_sanity(extracted)
        assert score < 1.0


class TestValidateRecord:
    """Integration tests for full record validation."""

    def test_valid_record_above_threshold(self):
        extracted = {
            "company_name": "OpenAI",
            "product_name": "API",
            "source_url": "https://openai.com/api/pricing/",
            "citation_text": "GPT-4o costs $2.50 per 1M input tokens",
            "pricing_tiers": [
                {
                    "model_or_tier_name": "GPT-4o",
                    "input_price_per_m_tokens": 2.50,
                    "output_price_per_m_tokens": 10.00,
                    "context_window_tokens": 128000,
                    "currency": "USD",
                    "notable_features": [],
                }
            ],
            "enterprise_terms_mentioned": True,
            "rate_limits_summary": "Rate limits apply",
            "extraction_confidence": 0.9,
        }
        record, is_valid = validate_record(extracted, SOURCE_TEXT, confidence_threshold=0.50)
        assert record.company_name == "OpenAI"
        assert len(record.pricing_tiers) == 1
        assert record.pricing_tiers[0].input_price_per_m_tokens == 2.50
