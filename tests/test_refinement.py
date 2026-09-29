"""Tests for Scrybe Benchmark Datasets, Constrained Decoding, and Model Refinement."""

import json
from pathlib import Path
import pytest

from scrybe.tools.benchmark_catalog import BenchmarkCatalogLoader, GOLDEN_AI_PRICING_CATALOG
from scrybe.tools.constrained_decoder import ConstrainedDecoder
from scrybe.tools.finetuning import FineTuningPipeline
from scrybe.tools.evaluation_harness import EvaluationHarness
from scrybe.agents.strategist_refiner import StrategistRefiner
from scrybe.storage.models import CompetitorProductRecord, DeltaType, PricingTier, TrendDelta


class TestBenchmarkCatalog:
    """Tests for the benchmark catalog loader."""

    def test_golden_catalog_has_entries(self):
        loader = BenchmarkCatalogLoader(use_offline_only=True)
        catalog = loader.get_golden_benchmark()
        assert len(catalog) >= 5
        companies = [c["company_name"] for c in catalog]
        assert "OpenAI" in companies
        assert "Anthropic" in companies
        assert "Groq" in companies

    def test_openrouter_fallback(self):
        loader = BenchmarkCatalogLoader(use_offline_only=True)
        res = loader.fetch_openrouter_catalog()
        assert len(res) >= 5
        assert any(c["company_name"] == "OpenAI" for c in res)


class TestConstrainedDecoder:
    """Tests for price normalization, unit conversion, and DOM grounding."""

    def test_price_normalization(self):
        # Floats
        assert ConstrainedDecoder.normalize_price_value(2.50) == 2.50
        # String currency
        assert ConstrainedDecoder.normalize_price_value("$10.00") == 10.00
        # Free tiers
        assert ConstrainedDecoder.normalize_price_value("Free") == 0.0
        assert ConstrainedDecoder.normalize_price_value("$0") == 0.0
        # Per 1K tokens converted to per 1M tokens
        assert ConstrainedDecoder.normalize_price_value("$0.002 / 1K tokens") == 2.00
        assert ConstrainedDecoder.normalize_price_value("0.0015 per thousand") == 1.50
        # Enterprise non-numeric
        assert ConstrainedDecoder.normalize_price_value("Contact Sales") is None
        assert ConstrainedDecoder.normalize_price_value("Custom") is None

    def test_decode_and_ground_verbatim_match(self):
        raw_dict = {
            "company_name": "Groq",
            "product_name": "Inference",
            "source_url": "https://groq.com",
            "pricing_tiers": [
                {"model_or_tier_name": "Llama 3.1 8B", "input_price_per_m_tokens": 0.05}
            ],
            "citation_text": "Llama 3.1 8B is $0.05 per 1M input tokens.",
        }
        source_text = "Groq pricing: Llama 3.1 8B is $0.05 per 1M input tokens. Blazing fast."

        record, grounding_ratio, ungrounded = ConstrainedDecoder.decode_and_ground(
            raw_dict, source_text
        )
        assert record.company_name == "Groq"
        assert len(record.pricing_tiers) == 1
        assert record.pricing_tiers[0].input_price_per_m_tokens == 0.05
        assert grounding_ratio >= 0.80
        assert len(ungrounded) == 0

    def test_decode_and_ground_flags_hallucination(self):
        raw_dict = {
            "company_name": "FabricatedAI",
            "product_name": "FakeModel",
            "source_url": "https://fake.ai",
            "pricing_tiers": [
                {"model_or_tier_name": "Fake Tier 99", "input_price_per_m_tokens": 99.99}
            ],
            "citation_text": "Fake Tier 99 costs $99.99",
        }
        source_text = "Welcome to Our Corporate Blog. We have exciting updates regarding our series A."

        record, grounding_ratio, ungrounded = ConstrainedDecoder.decode_and_ground(
            raw_dict, source_text
        )
        assert grounding_ratio <= 0.30
        assert any("company_name:FabricatedAI" in u for u in ungrounded)
        assert any("price:99.99" in u for u in ungrounded)


class TestFineTuningPipeline:
    """Tests for distillation dataset formatting and export."""

    def test_format_chatml_sample(self):
        pipeline = FineTuningPipeline()
        dom = "<div><h2>GPT-4o</h2><span>$2.50/1M</span></div>"
        target = {
            "company_name": "OpenAI",
            "product_name": "API",
            "pricing_tiers": [{"model_or_tier_name": "GPT-4o", "input_price_per_m_tokens": 2.5}],
        }
        sample = pipeline.format_chatml_sample(dom, target)
        assert "messages" in sample
        assert len(sample["messages"]) == 3
        assert sample["messages"][0]["role"] == "system"
        assert sample["messages"][1]["role"] == "user"
        assert sample["messages"][2]["role"] == "assistant"
        assistant_content = json.loads(sample["messages"][2]["content"])
        assert assistant_content["company_name"] == "OpenAI"

    def test_format_alpaca_sample(self):
        pipeline = FineTuningPipeline()
        dom = "<div>$0.05 / 1M</div>"
        target = {"company_name": "Groq", "pricing_tiers": []}
        sample = pipeline.format_alpaca_sample(dom, target)
        assert "instruction" in sample
        assert "input" in sample
        assert "output" in sample

    def test_export_dataset(self, tmp_path):
        pipeline = FineTuningPipeline()
        samples = [
            {
                "company_name": "OpenAI",
                "sample_html_snippet": "<div>GPT-4o $2.50</div>",
                "pricing_tiers": [{"model_or_tier_name": "GPT-4o", "input_price_per_m_tokens": 2.5}],
            }
        ]
        out_file = tmp_path / "train.jsonl"
        count = pipeline.export_dataset(samples, out_file, format_type="chatml", include_negatives=True)
        assert count >= 2  # 1 positive + 2 negatives = 3
        assert out_file.exists()


class TestEvaluationHarness:
    """Tests for benchmark scoring and metric calculation."""

    def test_evaluation_perfect_match(self):
        harness = EvaluationHarness()
        gold = {
            "company_name": "OpenAI",
            "sample_html_snippet": "OpenAI GPT-4o is $2.50 per 1M tokens",
            "pricing_tiers": [
                {"model_or_tier_name": "GPT-4o", "input_price_per_m_tokens": 2.50, "output_price_per_m_tokens": None}
            ],
            "citation_text": "GPT-4o is $2.50 per 1M tokens",
        }
        pred = gold.copy()
        res = harness.evaluate_sample(gold, pred, gold["sample_html_snippet"])
        assert res["matched_tier_count"] == 1
        assert res["gold_tier_count"] == 1
        assert res["grounding_ratio"] >= 0.80

    def test_run_benchmark_summary(self):
        harness = EvaluationHarness()
        catalog = GOLDEN_AI_PRICING_CATALOG[:2]
        metrics = harness.run_benchmark(catalog)
        assert metrics.total_samples == 2
        assert metrics.schema_validity_rate == 1.0
        assert metrics.tier_precision >= 0.90
        report = harness.generate_markdown_report(metrics)
        assert "Quantitative Performance Metrics" in report
        assert "Tier Extraction Precision" in report


class TestStrategistRefiner:
    """Tests for multi-source corroboration and battlecard generation."""

    def test_corroborates_macro_trend_with_two_sources(self):
        refiner = StrategistRefiner(min_corroboration_sources=2)
        records = [
            CompetitorProductRecord(
                company_name="OpenAI", product_name="API", source_url="https://openai.com",
                pricing_tiers=[PricingTier(model_or_tier_name="GPT-4o", input_price_per_m_tokens=2.5)],
                extraction_confidence=0.95, citation_text="GPT-4o is $2.50",
            ),
            CompetitorProductRecord(
                company_name="Anthropic", product_name="API", source_url="https://anthropic.com",
                pricing_tiers=[PricingTier(model_or_tier_name="Claude 3.5 Sonnet", input_price_per_m_tokens=3.0)],
                extraction_confidence=0.92, citation_text="Claude 3.5 is $3.00",
            ),
        ]
        deltas = [
            TrendDelta(
                competitor_name="OpenAI", product_name="API", delta_type=DeltaType.PRICE_DECREASE,
                metric_name="token_price", old_value="$5.00", new_value="$2.50"
            ),
            TrendDelta(
                competitor_name="Anthropic", product_name="API", delta_type=DeltaType.PRICE_DECREASE,
                metric_name="token_price", old_value="$4.00", new_value="$3.00"
            ),
        ]

        macro_trends, isolated_moves = refiner.corroborate_signals(records, deltas)
        assert len(macro_trends) >= 1
        assert macro_trends[0]["corroboration_count"] >= 2
        assert len(isolated_moves) == 0

    def test_isolates_single_source_move(self):
        refiner = StrategistRefiner(min_corroboration_sources=2)
        records = [
            CompetitorProductRecord(
                company_name="OpenAI", product_name="API", source_url="https://openai.com",
                pricing_tiers=[PricingTier(model_or_tier_name="GPT-4o", input_price_per_m_tokens=2.5)],
                extraction_confidence=0.95, citation_text="GPT-4o is $2.50",
            )
        ]
        deltas = [
            TrendDelta(
                competitor_name="OpenAI", product_name="API", delta_type=DeltaType.PRICE_DECREASE,
                metric_name="token_price", old_value="$5.00", new_value="$2.50"
            ),
        ]

        macro_trends, isolated_moves = refiner.corroborate_signals(records, deltas)
        assert len(isolated_moves) == 1
        assert isolated_moves[0]["company_name"] == "OpenAI"

    def test_generate_battlecards(self):
        refiner = StrategistRefiner()
        records = [
            CompetitorProductRecord(
                company_name="Groq", product_name="LPU", source_url="https://groq.com",
                pricing_tiers=[PricingTier(model_or_tier_name="8B", input_price_per_m_tokens=0.05)],
                enterprise_terms_mentioned=False,
                extraction_confidence=0.98, citation_text="Llama 3.1 8B is $0.05",
            )
        ]
        battlecards = refiner.generate_battlecards(records)
        assert len(battlecards) == 1
        assert battlecards[0]["competitor"] == "Groq"
        assert len(battlecards[0]["strengths"]) >= 1
        assert len(battlecards[0]["vulnerabilities"]) >= 1
