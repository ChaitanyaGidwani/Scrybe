"""Scrybe Strategist Agent.

Derives strategic insights, pricing deltas, competitive recommendations,
and sales battlecard snippets from validated extraction data.
Enforces the ≥2 source corroboration rule for macro-level claims.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from scrybe.exceptions import CorroborationError, LLMError
from scrybe.logging_config import get_agent_logger
from scrybe.memory.buffer import RollingBuffer
from scrybe.storage.models import (
    CompetitorProductRecord,
    StrategicRecommendation,
    TrendDelta,
)
from scrybe.tools.extractor import parse_llm_json_response

logger = get_agent_logger("strategist")


class StrategistAgent:
    """Autonomous agent for competitive strategy synthesis.

    Analyzes extracted records and pricing deltas to produce:
    - Executive summary
    - Market change highlights
    - Strategic recommendations with ≥2-source corroboration
    - Sales battlecard snippets

    Uses a frontier-tier LLM (e.g., Claude 3.5 Sonnet, GPT-4o)
    for high-quality reasoning.
    """

    def __init__(
        self,
        llm_client=None,
        reasoning_model: str = "gpt-4o",
        min_corroboration: int = 2,
        buffer: Optional[RollingBuffer] = None,
    ):
        self.llm_client = llm_client
        self.reasoning_model = reasoning_model
        self.min_corroboration = min_corroboration
        self.buffer = buffer or RollingBuffer()

    def run(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
    ) -> Dict[str, Any]:
        """Generate strategic analysis from extracted data.

        Args:
            records: Validated competitor product records.
            deltas: Detected pricing/feature deltas.

        Returns:
            Dict with keys: executive_summary, key_market_deltas,
            strategic_recommendations, sales_battlecard_snippets.
        """
        if not records:
            return self._empty_result("No competitor data available for analysis.")

        # If LLM is available, use it for deep synthesis
        if self.llm_client:
            return self._synthesize_with_llm(records, deltas)

        # Fallback: rule-based synthesis without LLM
        return self._synthesize_rules_based(records, deltas)

    def _synthesize_with_llm(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
    ) -> Dict[str, Any]:
        """Use frontier LLM for deep strategic synthesis."""
        # Build prompt
        prompt = self._build_strategy_prompt(records, deltas)

        try:
            raw_response = self.llm_client.generate(
                prompt=prompt,
                model=self.reasoning_model,
                system_prompt=(
                    "You are a senior competitive intelligence strategist. "
                    "Produce quantified, actionable, cited analysis. "
                    "Output valid JSON only."
                ),
                temperature=0.1,
                max_tokens=4096,
                json_mode=True,
            )

            result = parse_llm_json_response(raw_response)

            # Enforce corroboration rules
            result = self._enforce_corroboration(result, records)

            self.buffer.record(
                agent="strategist",
                action="llm_synthesis_complete",
                status="OK",
                metadata={"recommendations_count": len(result.get("strategic_recommendations", []))},
            )

            return result

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            self.buffer.record(
                agent="strategist", action="llm_synthesis_failed",
                status="ERROR", error=str(e),
            )
            return self._synthesize_rules_based(records, deltas)

    def _synthesize_rules_based(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
    ) -> Dict[str, Any]:
        """Generate strategic analysis using deterministic rules (no LLM)."""
        # Build executive summary
        company_names = list(set(r.company_name for r in records))
        summary = (
            f"Analyzed {len(records)} competitor product(s) across "
            f"{len(company_names)} companies: {', '.join(company_names)}. "
        )
        if deltas:
            critical = [d for d in deltas if d.strategic_severity == "CRITICAL"]
            high = [d for d in deltas if d.strategic_severity == "HIGH"]
            summary += f"Detected {len(deltas)} market changes ({len(critical)} critical, {len(high)} high severity). "
        else:
            summary += "No significant pricing changes detected since last analysis. "

        # Build market deltas
        key_deltas = []
        for d in deltas:
            key_deltas.append({
                "competitor_name": d.competitor_name,
                "summary_of_change": f"{d.delta_type.value}: {d.metric_name} {d.old_value or 'N/A'} → {d.new_value}",
                "impact_severity": d.strategic_severity,
            })

        # Build recommendations from deltas
        recommendations = self._generate_rule_based_recommendations(records, deltas)

        # Build simple battlecards
        battlecards = self._generate_rule_based_battlecards(records)

        return {
            "executive_summary": summary,
            "key_market_deltas": key_deltas,
            "strategic_recommendations": recommendations,
            "sales_battlecard_snippets": battlecards,
        }

    def _build_strategy_prompt(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
    ) -> str:
        """Build the strategist synthesis prompt."""
        prompt_path = Path(__file__).parent / "prompts" / "strategist_synthesize.txt"

        records_json = json.dumps(
            [r.model_dump() for r in records],
            default=str, indent=2,
        )
        deltas_json = json.dumps(
            [d.model_dump() for d in deltas],
            default=str, indent=2,
        )
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8")
            return template.format(
                extracted_records_json=records_json,
                historical_deltas_json=deltas_json,
                current_date=current_date,
            )

        # Inline fallback prompt
        return f"""Analyze the following competitor data and produce strategic recommendations.

EXTRACTED RECORDS:
{records_json}

HISTORICAL DELTAS:
{deltas_json}

DATE: {current_date}

Output valid JSON with: executive_summary, key_market_deltas, strategic_recommendations, sales_battlecard_snippets."""

    def _enforce_corroboration(
        self,
        result: Dict[str, Any],
        records: List[CompetitorProductRecord],
    ) -> Dict[str, Any]:
        """Enforce the ≥2 source corroboration rule on recommendations."""
        source_urls = set(r.source_url for r in records)

        valid_recs = []
        for rec in result.get("strategic_recommendations", []):
            sources = rec.get("corroborating_sources", [])
            # Filter to only sources that actually exist in our data
            valid_sources = [s for s in sources if any(s in url for url in source_urls)]

            if len(valid_sources) >= self.min_corroboration:
                rec["corroborating_sources"] = valid_sources
                rec["corroboration_count"] = len(valid_sources)
                valid_recs.append(rec)
            elif len(valid_sources) == 1:
                # Downgrade to company-specific observation
                rec["title"] = f"[Single-Source] {rec.get('title', '')}"
                rec["corroborating_sources"] = valid_sources
                rec["corroboration_count"] = 1
                valid_recs.append(rec)

        result["strategic_recommendations"] = valid_recs
        return result

    def _generate_rule_based_recommendations(
        self,
        records: List[CompetitorProductRecord],
        deltas: List[TrendDelta],
    ) -> List[Dict[str, Any]]:
        """Generate deterministic recommendations from detected deltas."""
        recommendations = []

        # Group price decreases by company
        price_drops = [d for d in deltas if d.delta_type == DeltaType.PRICE_DECREASE]
        if len(price_drops) >= 2:
            companies = list(set(d.competitor_name for d in price_drops))
            sources = list(set(
                r.source_url for r in records if r.company_name in companies
            ))
            recommendations.append({
                "category": "PRICING",
                "title": "Multiple Competitors Reducing Prices",
                "rationale": (
                    f"{len(price_drops)} price reductions detected across "
                    f"{', '.join(companies)}. This signals an industry-wide "
                    "margin compression trend."
                ),
                "actionable_next_step": (
                    "Evaluate defensive pricing options. Consider introducing "
                    "a competitive batch/volume discount tier to retain price-sensitive customers."
                ),
                "corroborating_sources": sources[:3],
                "corroboration_count": len(sources),
            })

        # New tier introductions
        new_tiers = [d for d in deltas if d.delta_type == DeltaType.NEW_TIER]
        for nt in new_tiers:
            source_urls = [r.source_url for r in records if r.company_name == nt.competitor_name]
            recommendations.append({
                "category": "PRODUCT_ROADMAP",
                "title": f"New Tier Launched by {nt.competitor_name}",
                "rationale": f"{nt.competitor_name} introduced a new tier: {nt.new_value}.",
                "actionable_next_step": "Evaluate feature parity and positioning against this new offering.",
                "corroborating_sources": source_urls[:2],
                "corroboration_count": len(source_urls),
            })

        return recommendations

    def _generate_rule_based_battlecards(
        self,
        records: List[CompetitorProductRecord],
    ) -> Dict[str, Any]:
        """Generate simple battlecard comparisons between competitors."""
        battlecards = {}

        if len(records) < 2:
            return battlecards

        # Find cheapest and most expensive per tier type
        for record in records:
            advantages = []
            disadvantages = []

            for tier in record.pricing_tiers:
                if tier.input_price_per_m_tokens is not None:
                    # Compare against other records
                    for other in records:
                        if other.company_name == record.company_name:
                            continue
                        for other_tier in other.pricing_tiers:
                            if other_tier.input_price_per_m_tokens is not None:
                                if tier.input_price_per_m_tokens < other_tier.input_price_per_m_tokens:
                                    pct = (
                                        (other_tier.input_price_per_m_tokens - tier.input_price_per_m_tokens)
                                        / other_tier.input_price_per_m_tokens * 100
                                    )
                                    advantages.append(
                                        f"{tier.model_or_tier_name} input pricing is "
                                        f"{pct:.0f}% cheaper than {other.company_name}'s {other_tier.model_or_tier_name}"
                                    )

                if tier.context_window_tokens and tier.context_window_tokens >= 128000:
                    advantages.append(
                        f"{tier.model_or_tier_name} supports {tier.context_window_tokens:,} token context window"
                    )

            battlecards[record.company_name] = {
                "our_advantages": advantages[:3],
                "competitor_advantages": disadvantages[:2],
                "recommended_talk_track": (
                    f"When competing against {record.company_name}, "
                    f"emphasize pricing advantages and context window capabilities."
                ),
            }

        return battlecards

    @staticmethod
    def _empty_result(summary: str) -> Dict[str, Any]:
        return {
            "executive_summary": summary,
            "key_market_deltas": [],
            "strategic_recommendations": [],
            "sales_battlecard_snippets": {},
        }
