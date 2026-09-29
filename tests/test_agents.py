"""Unit tests for Scrybe Strategist and Formatter agents."""

import pytest
from scrybe.agents.strategist import StrategistAgent
from scrybe.agents.formatter import FormatterAgent
from scrybe.storage.models import (
    CompetitorProductRecord,
    PricingTier,
    TrendDelta,
    DeltaType,
)


def _make_record(company: str, model: str, input_price: float, output_price: float, ctx: int = 128000):
    return CompetitorProductRecord(
        company_name=company,
        product_name="API",
        source_url=f"https://{company.lower().replace(' ', '')}.com/pricing/",
        pricing_tiers=[
            PricingTier(
                model_or_tier_name=model,
                input_price_per_m_tokens=input_price,
                output_price_per_m_tokens=output_price,
                context_window_tokens=ctx,
                currency="USD",
            )
        ],
        extraction_confidence=0.92,
        citation_text=f"{model} costs ${input_price:.2f}/1M input tokens",
    )


class TestStrategistAgent:
    """Tests for the rule-based strategist (no LLM)."""

    def test_basic_synthesis(self):
        records = [
            _make_record("OpenAI", "GPT-4o", 2.50, 10.00),
            _make_record("Anthropic", "Claude 3.5 Sonnet", 3.00, 15.00),
        ]
        agent = StrategistAgent()
        result = agent.run(records, deltas=[])

        assert "executive_summary" in result
        assert "OpenAI" in result["executive_summary"]
        assert "Anthropic" in result["executive_summary"]

    def test_delta_analysis_in_synthesis(self):
        records = [_make_record("OpenAI", "GPT-4o", 2.50, 10.00)]
        deltas = [
            TrendDelta(
                competitor_name="OpenAI",
                product_name="API",
                delta_type=DeltaType.PRICE_DECREASE,
                metric_name="GPT-4o_input_price",
                old_value="$5.00/1M",
                new_value="$2.50/1M",
                percentage_change=-50.0,
                strategic_severity="CRITICAL",
            )
        ]
        agent = StrategistAgent()
        result = agent.run(records, deltas)

        assert len(result["key_market_deltas"]) >= 1
        assert result["key_market_deltas"][0]["impact_severity"] == "CRITICAL"

    def test_empty_records(self):
        agent = StrategistAgent()
        result = agent.run([], [])
        assert "No competitor data" in result["executive_summary"]

    def test_battlecard_generation(self):
        records = [
            _make_record("OpenAI", "GPT-4o", 2.50, 10.00),
            _make_record("Anthropic", "Claude 3.5 Sonnet", 3.00, 15.00),
        ]
        agent = StrategistAgent()
        result = agent.run(records, [])
        cards = result.get("sales_battlecard_snippets", {})
        assert len(cards) >= 1


class TestFormatterAgent:
    """Tests for report formatting."""

    def test_markdown_generation(self, tmp_path):
        records = [
            _make_record("OpenAI", "GPT-4o", 2.50, 10.00),
            _make_record("Anthropic", "Claude 3.5 Sonnet", 3.00, 15.00),
        ]
        deltas = [
            TrendDelta(
                competitor_name="OpenAI",
                product_name="API",
                delta_type=DeltaType.PRICE_DECREASE,
                metric_name="GPT-4o_input",
                old_value="$5.00/1M",
                new_value="$2.50/1M",
                percentage_change=-50.0,
                strategic_severity="HIGH",
            )
        ]
        strategy_result = {
            "executive_summary": "Major price cuts detected in the LLM inference market.",
            "key_market_deltas": [],
            "strategic_recommendations": [
                {
                    "category": "PRICING",
                    "title": "Respond to OpenAI Price Cut",
                    "rationale": "OpenAI cut input prices by 50%.",
                    "actionable_next_step": "Consider matching or introducing volume discount.",
                    "corroborating_sources": ["https://openai.com/pricing"],
                    "corroboration_count": 1,
                }
            ],
            "sales_battlecard_snippets": {},
        }

        formatter = FormatterAgent(output_dir=str(tmp_path))
        result = formatter.run(
            pipeline_id="test_pipe_001",
            records=records,
            deltas=deltas,
            strategy_result=strategy_result,
        )

        md = result["report_markdown"]
        assert "Competitive Intelligence Report" in md
        assert "GPT-4o" in md
        assert "$2.50" in md
        assert "OpenAI" in md
        assert result["report_markdown_path"].endswith(".md")

    def test_json_payload(self):
        records = [_make_record("OpenAI", "GPT-4o", 2.50, 10.00)]
        formatter = FormatterAgent()
        payload = formatter.generate_json_payload(records, [], {"executive_summary": "Test"})
        import json
        data = json.loads(payload)
        assert data["competitors"][0]["company_name"] == "OpenAI"
