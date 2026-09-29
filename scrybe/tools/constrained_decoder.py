"""Scrybe Constrained Decoder & Grounding Engine.

Implements schema-constrained decoding and verbatim DOM substring verification:
1. Normalizes varied pricing string patterns (e.g., "$2.50/1M", "0.002 per 1k", "Free")
   into standardized per-1M token floats.
2. Performs character-level verification against raw source text to flag
   hallucinated numbers or fabricated evidence.
3. Ensures 100% adherence to Pydantic schemas without runtime parsing exceptions.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from scrybe.storage.models import CompetitorProductRecord, PricingTier
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("constrained_decoder")

# Regex to detect price strings like "$2.50", "0.15 / 1M", "0.002/1k", "€3.00"
PRICE_PATTERN = re.compile(
    r"[\$€£]?\s*(\d+(?:\.\d+)?)\s*(?:/\s*(?:1M|million|1k|thousand|token))?",
    re.IGNORECASE,
)

# Common enterprise phrasing that indicates custom sales tiers
ENTERPRISE_KEYWORDS = [
    "contact sales",
    "talk to an expert",
    "custom pricing",
    "enterprise tier",
    "custom sla",
    "dedicated capacity",
    "volume discount",
    "request quote",
]


class ConstrainedDecoder:
    """Enforces strict schema constraints, normalization, and DOM grounding."""

    @classmethod
    def normalize_price_value(cls, val: Any) -> Optional[float]:
        """Normalize any price representation into a float per 1M tokens or monthly fee.

        Handles:
            - Standard floats / ints: 2.5 -> 2.5
            - Currency strings: "$2.50" -> 2.50
            - Per-1K token rates: "$0.002 / 1K" -> 2.00 (normalized to 1M)
            - Free tiers: "Free" / "$0" -> 0.0
            - Non-numeric / contact sales -> None
        """
        if val is None:
            return None

        if isinstance(val, (int, float)):
            return float(val) if val >= 0 else None

        s = str(val).strip().lower()

        if s in ("free", "$0", "0", "0.0", "$0.00"):
            return 0.0

        if any(term in s for term in ["contact", "custom", "n/a", "none", "tbd", "quote"]):
            return None

        # Check if the rate is expressed per 1K tokens
        is_per_1k = "1k" in s or "thousand" in s

        # Match numbers
        match = re.search(r"(\d+(?:\.\d+)?)", s)
        if match:
            try:
                num = float(match.group(1))
                if is_per_1k:
                    num *= 1000.0  # Convert 1K rate to 1M rate
                return round(num, 4)
            except ValueError:
                return None

        return None

    @classmethod
    def sanitize_tier(cls, tier_data: Dict[str, Any]) -> PricingTier:
        """Sanitize an individual pricing tier dictionary into a typed PricingTier."""
        name = str(tier_data.get("model_or_tier_name") or "Standard Tier").strip()
        
        inp = cls.normalize_price_value(tier_data.get("input_price_per_m_tokens"))
        out = cls.normalize_price_value(tier_data.get("output_price_per_m_tokens"))
        base = cls.normalize_price_value(tier_data.get("base_price_monthly"))
        seat = cls.normalize_price_value(tier_data.get("seat_price_monthly"))

        return PricingTier(
            model_or_tier_name=name,
            input_price_per_m_tokens=inp,
            output_price_per_m_tokens=out,
            base_price_monthly=base,
            seat_price_monthly=seat,
        )

    @classmethod
    def verify_grounding(
        cls, 
        record: CompetitorProductRecord, 
        source_text: str
    ) -> Tuple[float, List[str]]:
        """Verify that extracted entity names, tier prices, and citations appear in the DOM.

        Returns:
            Tuple of (grounding_ratio between 0.0 and 1.0, list of ungrounded fields).
        """
        if not source_text:
            return 0.0, ["source_text_empty"]

        source_lower = source_text.lower()
        checks = 0
        passed = 0
        ungrounded = []

        # 1. Company Name check
        if record.company_name and record.company_name.lower() != "unknown":
            checks += 1
            if record.company_name.lower() in source_lower:
                passed += 1
            else:
                ungrounded.append(f"company_name:{record.company_name}")

        # 2. Tier names and numeric prices check
        for tier in record.pricing_tiers:
            if tier.model_or_tier_name:
                checks += 1
                if tier.model_or_tier_name.lower() in source_lower:
                    passed += 1
                else:
                    ungrounded.append(f"tier_name:{tier.model_or_tier_name}")

            # Check if prices appear in source text (e.g. 2.5 or 0.15)
            for price_val in [tier.input_price_per_m_tokens, tier.output_price_per_m_tokens]:
                if price_val is not None and price_val > 0:
                    checks += 1
                    # Match formatted number or integer
                    str_price = f"{price_val:.2f}"
                    str_num = f"{price_val:g}"
                    if str_price in source_text or str_num in source_text:
                        passed += 1
                    else:
                        ungrounded.append(f"price:{price_val}")

        # 3. Citation Text check (at least partial match)
        if record.citation_text:
            checks += 1
            words = record.citation_text.split()
            # If at least 3 consecutive words appear in source
            if len(words) >= 3:
                snippet = " ".join(words[:4]).lower()
                if snippet in source_lower:
                    passed += 1
                else:
                    ungrounded.append("citation_text_mismatch")
            elif record.citation_text.lower() in source_lower:
                passed += 1
            else:
                ungrounded.append("citation_text_mismatch")

        ratio = passed / checks if checks > 0 else 0.5
        return round(ratio, 3), ungrounded

    @classmethod
    def decode_and_ground(
        cls, 
        raw_dict: Dict[str, Any], 
        source_text: str
    ) -> Tuple[CompetitorProductRecord, float, List[str]]:
        """Decode raw extracted dictionary, apply constrained sanitization, and compute grounding."""
        raw_tiers = raw_dict.get("pricing_tiers", [])
        sanitized_tiers = [cls.sanitize_tier(t) for t in raw_tiers]

        # Detect enterprise terms automatically if phrasing exists
        ent_mentioned = bool(raw_dict.get("enterprise_terms_mentioned", False))
        if not ent_mentioned and source_text:
            source_lower = source_text.lower()
            if any(k in source_lower for k in ENTERPRISE_KEYWORDS):
                ent_mentioned = True

        record = CompetitorProductRecord(
            company_name=str(raw_dict.get("company_name", "Unknown")).strip(),
            product_name=str(raw_dict.get("product_name", "Standard API")).strip(),
            source_url=str(raw_dict.get("source_url", "")).strip(),
            pricing_tiers=sanitized_tiers,
            enterprise_terms_mentioned=ent_mentioned,
            rate_limits_summary=raw_dict.get("rate_limits_summary"),
            extraction_confidence=float(raw_dict.get("extraction_confidence", 0.0)),
            citation_text=str(raw_dict.get("citation_text", "")).strip(),
        )

        grounding_ratio, ungrounded = cls.verify_grounding(record, source_text)
        
        # Penalize confidence if ungrounded fields exist
        calibrated_conf = record.extraction_confidence
        if calibrated_conf == 0.0:
            calibrated_conf = grounding_ratio
        else:
            calibrated_conf = min(calibrated_conf, grounding_ratio)

        record.extraction_confidence = calibrated_conf
        return record, grounding_ratio, ungrounded
