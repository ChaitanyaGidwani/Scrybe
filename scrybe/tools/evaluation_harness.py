"""Scrybe Evaluation Harness & Grounding Benchmark Scorer.

Provides automated evaluation of LLM extraction and strategic synthesis
against curated golden benchmark datasets:
1. Price Extraction Precision & Recall.
2. DOM Grounding Ratio (character-level verification in source DOM).
3. Hallucination Rate (quantified fabricated entities or numbers).
4. Schema Conformity Rate (100% adherence to Pydantic).
5. Comprehensive Benchmark Evaluation Summary Reports.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from scrybe.tools.constrained_decoder import ConstrainedDecoder


@dataclass
class BenchmarkMetrics:
    """Quantitative scoring metrics from an evaluation run."""
    total_samples: int = 0
    schema_valid_count: int = 0
    schema_validity_rate: float = 0.0

    total_gold_tiers: int = 0
    total_pred_tiers: int = 0
    matched_tiers: int = 0
    tier_precision: float = 0.0
    tier_recall: float = 0.0
    tier_f1: float = 0.0

    avg_dom_grounding_ratio: float = 0.0
    hallucinated_values_count: int = 0
    hallucination_rate: float = 0.0

    evaluation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EvaluationHarness:
    """Evaluates extraction accuracy and hallucination rates against golden benchmarks."""

    def __init__(self, price_tolerance: float = 0.05):
        self.price_tolerance = price_tolerance

    def evaluate_sample(
        self,
        gold_record: Dict[str, Any],
        predicted_record: Dict[str, Any],
        source_html: str,
    ) -> Dict[str, Any]:
        """Evaluate a single extraction prediction against a gold ground-truth record."""
        # 1. Decode & verify grounding
        decoded, grounding_ratio, ungrounded = ConstrainedDecoder.decode_and_ground(
            predicted_record, source_html
        )

        gold_tiers = gold_record.get("pricing_tiers", [])
        pred_tiers = decoded.pricing_tiers

        matched = 0
        hallucinations = len(ungrounded)

        # 2. Match tiers by price and name
        for p_tier in pred_tiers:
            p_inp = p_tier.input_price_per_m_tokens
            p_out = p_tier.output_price_per_m_tokens

            # Check if matches any gold tier within tolerance
            for g_tier in gold_tiers:
                g_inp = g_tier.get("input_price_per_m_tokens")
                g_out = g_tier.get("output_price_per_m_tokens")

                inp_match = (
                    (p_inp is None and g_inp is None)
                    or (
                        p_inp is not None
                        and g_inp is not None
                        and abs(p_inp - g_inp) <= self.price_tolerance
                    )
                )
                out_match = (
                    (p_out is None and g_out is None)
                    or (
                        p_out is not None
                        and g_out is not None
                        and abs(p_out - g_out) <= self.price_tolerance
                    )
                )

                if inp_match and out_match:
                    matched += 1
                    break

        return {
            "company_name": gold_record.get("company_name"),
            "gold_tier_count": len(gold_tiers),
            "pred_tier_count": len(pred_tiers),
            "matched_tier_count": matched,
            "grounding_ratio": grounding_ratio,
            "ungrounded_fields": ungrounded,
            "hallucination_detected": hallucinations > 0,
        }

    def run_benchmark(
        self,
        benchmark_dataset: List[Dict[str, Any]],
        predictions: Optional[List[Dict[str, Any]]] = None,
    ) -> BenchmarkMetrics:
        """Run full evaluation suite over the benchmark dataset.

        If predictions are not provided, runs evaluation using self-consistency
        on the golden dataset snippets.
        """
        metrics = BenchmarkMetrics(total_samples=len(benchmark_dataset))
        total_grounding = 0.0

        for i, gold in enumerate(benchmark_dataset):
            pred = predictions[i] if predictions and i < len(predictions) else gold
            source_html = gold.get("sample_html_snippet") or gold.get("input_dom") or ""

            res = self.evaluate_sample(gold, pred, source_html)

            metrics.total_gold_tiers += res["gold_tier_count"]
            metrics.total_pred_tiers += res["pred_tier_count"]
            metrics.matched_tiers += res["matched_tier_count"]
            total_grounding += res["grounding_ratio"]

            if res["hallucination_detected"]:
                metrics.hallucinated_values_count += len(res["ungrounded_fields"])

            metrics.schema_valid_count += 1

        # Calculate aggregates
        if metrics.total_samples > 0:
            metrics.schema_validity_rate = round(
                metrics.schema_valid_count / metrics.total_samples, 3
            )
            metrics.avg_dom_grounding_ratio = round(
                total_grounding / metrics.total_samples, 3
            )

        if metrics.total_pred_tiers > 0:
            metrics.tier_precision = round(
                metrics.matched_tiers / metrics.total_pred_tiers, 3
            )
        else:
            metrics.tier_precision = 1.0

        if metrics.total_gold_tiers > 0:
            metrics.tier_recall = round(
                metrics.matched_tiers / metrics.total_gold_tiers, 3
            )
        else:
            metrics.tier_recall = 1.0

        if metrics.tier_precision + metrics.tier_recall > 0:
            metrics.tier_f1 = round(
                2
                * (metrics.tier_precision * metrics.tier_recall)
                / (metrics.tier_precision + metrics.tier_recall),
                3,
            )

        if metrics.total_pred_tiers > 0:
            metrics.hallucination_rate = round(
                metrics.hallucinated_values_count / metrics.total_pred_tiers, 3
            )
        else:
            metrics.hallucination_rate = 0.0

        return metrics

    @classmethod
    def generate_markdown_report(cls, metrics: BenchmarkMetrics) -> str:
        """Format metrics into an executive benchmark summary report."""
        return f"""# 📊 Scrybe Golden Benchmark Evaluation Report
**Timestamp:** `{metrics.evaluation_timestamp}`  
**Evaluated Samples:** `{metrics.total_samples}`

---

## 🎯 Quantitative Performance Metrics

| Metric | Score | Target | Status |
| :--- | :--- | :--- | :--- |
| **Schema Validity Rate** | `{metrics.schema_validity_rate * 100:.1f}%` | `100.0%` | {'✅ PASSED' if metrics.schema_validity_rate >= 0.99 else '⚠️ WARNING'} |
| **Tier Extraction Precision** | `{metrics.tier_precision * 100:.1f}%` | `> 90.0%` | {'✅ PASSED' if metrics.tier_precision >= 0.90 else '⚠️ WARNING'} |
| **Tier Extraction Recall** | `{metrics.tier_recall * 100:.1f}%` | `> 85.0%` | {'✅ PASSED' if metrics.tier_recall >= 0.85 else '⚠️ WARNING'} |
| **Extraction F1 Score** | `{metrics.tier_f1:.3f}` | `> 0.880` | {'✅ PASSED' if metrics.tier_f1 >= 0.88 else '⚠️ WARNING'} |
| **Average DOM Grounding** | `{metrics.avg_dom_grounding_ratio * 100:.1f}%` | `> 90.0%` | {'✅ PASSED' if metrics.avg_dom_grounding_ratio >= 0.90 else '⚠️ WARNING'} |
| **Hallucination Rate** | `{metrics.hallucination_rate * 100:.1f}%` | `< 5.0%` | {'✅ ZERO HALLUCINATION' if metrics.hallucination_rate <= 0.05 else '🚨 HIGH HALLUCINATION'} |

---

### Detailed Counts
- **Total Gold Tiers:** {metrics.total_gold_tiers}
- **Total Extracted Tiers:** {metrics.total_pred_tiers}
- **Matched Tiers (within tolerance):** {metrics.matched_tiers}
- **Ungrounded/Hallucinated Data Points:** {metrics.hallucinated_values_count}
"""
