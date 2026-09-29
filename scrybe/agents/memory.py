"""Scrybe Memory Agent.

Coordinates the three memory subsystems:
1. Rolling Buffer — short-term action/error tracking.
2. Reflexion Loop — self-correcting extraction failures.
3. FAISS Vector Store — semantic delta detection across runs.

Provides a unified interface for the pipeline orchestrator.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from scrybe.logging_config import get_agent_logger
from scrybe.memory.buffer import RollingBuffer
from scrybe.memory.vector_store import VectorStore, text_to_embedding_simple
from scrybe.storage.models import CompetitorProductRecord, TrendDelta, DeltaType

logger = get_agent_logger("memory")


class MemoryAgent:
    """Autonomous agent coordinating all memory subsystems.

    Detects content changes between runs using semantic vector similarity,
    and computes pricing deltas for the Strategist Agent.
    """

    def __init__(
        self,
        buffer: Optional[RollingBuffer] = None,
        vector_store: Optional[VectorStore] = None,
        similarity_threshold: float = 0.995,
        embedding_dimension: int = 384,
    ):
        self.buffer = buffer or RollingBuffer()
        self.vector_store = vector_store or VectorStore(
            dimension=embedding_dimension,
            similarity_threshold=similarity_threshold,
        )
        self.similarity_threshold = similarity_threshold

    def run(
        self,
        current_records: List[CompetitorProductRecord],
        historical_records: Optional[List[CompetitorProductRecord]] = None,
    ) -> Tuple[List[TrendDelta], List[str]]:
        """Analyze current records against historical data.

        Args:
            current_records: Freshly extracted records from this pipeline run.
            historical_records: Previous run's records (if available).

        Returns:
            Tuple of (detected deltas, list of unchanged company names to skip).
        """
        deltas: List[TrendDelta] = []
        unchanged_companies: List[str] = []

        for record in current_records:
            # 1. Check semantic similarity with vector store
            record_text = self._record_to_text(record)
            embedding = text_to_embedding_simple(record_text, dimension=self.vector_store.dimension)

            is_dup, sim_score = self.vector_store.is_duplicate(embedding, company_name=record.company_name)

            if is_dup:
                unchanged_companies.append(record.company_name)
                self.buffer.record(
                    agent="memory",
                    action=f"unchanged_{record.company_name}",
                    status="SKIPPED",
                    source_url=record.source_url,
                    metadata={"similarity": round(sim_score, 4)},
                )
                logger.info(
                    f"Content unchanged for {record.company_name} (sim={sim_score:.4f})",
                    extra={"agent": "memory", "step": "delta_check", "domain": record.company_name},
                )
                continue

            # 2. Compute explicit pricing deltas against historical records
            if historical_records:
                company_history = [
                    h for h in historical_records
                    if h.company_name == record.company_name
                ]
                if company_history:
                    record_deltas = self._compute_pricing_deltas(company_history[0], record)
                    deltas.extend(record_deltas)

            # 3. Store the new embedding for future comparison
            self.vector_store.add(
                embedding,
                metadata={
                    "company_name": record.company_name,
                    "source_url": record.source_url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content_hash": hash(record_text),
                },
            )

            self.buffer.record(
                agent="memory",
                action=f"indexed_{record.company_name}",
                status="OK",
                source_url=record.source_url,
            )

        return deltas, unchanged_companies

    def save_index(self) -> None:
        """Persist the vector index to disk."""
        self.vector_store.save()

    def _record_to_text(self, record: CompetitorProductRecord) -> str:
        """Convert a CompetitorProductRecord to a text representation for embedding."""
        parts = [f"Company: {record.company_name}", f"Product: {record.product_name}"]
        for tier in record.pricing_tiers:
            tier_parts = [f"Tier: {tier.model_or_tier_name}"]
            if tier.input_price_per_m_tokens is not None:
                tier_parts.append(f"Input: ${tier.input_price_per_m_tokens}/1M")
            if tier.output_price_per_m_tokens is not None:
                tier_parts.append(f"Output: ${tier.output_price_per_m_tokens}/1M")
            if tier.context_window_tokens is not None:
                tier_parts.append(f"Context: {tier.context_window_tokens}")
            parts.append(" | ".join(tier_parts))
        return "\n".join(parts)

    def _compute_pricing_deltas(
        self,
        old_record: CompetitorProductRecord,
        new_record: CompetitorProductRecord,
    ) -> List[TrendDelta]:
        """Compare old and new records tier-by-tier to detect pricing changes."""
        deltas = []

        # Build lookup maps by tier name
        old_tiers = {t.model_or_tier_name: t for t in old_record.pricing_tiers}
        new_tiers = {t.model_or_tier_name: t for t in new_record.pricing_tiers}

        # Check for changed or removed tiers
        for tier_name, old_tier in old_tiers.items():
            if tier_name not in new_tiers:
                deltas.append(TrendDelta(
                    competitor_name=new_record.company_name,
                    product_name=new_record.product_name,
                    delta_type=DeltaType.TIER_REMOVED,
                    metric_name=tier_name,
                    old_value=tier_name,
                    new_value="REMOVED",
                    strategic_severity="MEDIUM",
                ))
                continue

            new_tier = new_tiers[tier_name]

            # Compare input prices
            if old_tier.input_price_per_m_tokens is not None and new_tier.input_price_per_m_tokens is not None:
                if old_tier.input_price_per_m_tokens != new_tier.input_price_per_m_tokens:
                    pct = ((new_tier.input_price_per_m_tokens - old_tier.input_price_per_m_tokens)
                           / old_tier.input_price_per_m_tokens * 100)
                    delta_type = DeltaType.PRICE_DECREASE if pct < 0 else DeltaType.PRICE_INCREASE
                    severity = self._classify_severity(abs(pct))
                    deltas.append(TrendDelta(
                        competitor_name=new_record.company_name,
                        product_name=new_record.product_name,
                        delta_type=delta_type,
                        metric_name=f"{tier_name}_input_price",
                        old_value=f"${old_tier.input_price_per_m_tokens:.2f}/1M",
                        new_value=f"${new_tier.input_price_per_m_tokens:.2f}/1M",
                        percentage_change=round(pct, 1),
                        strategic_severity=severity,
                    ))

            # Compare output prices
            if old_tier.output_price_per_m_tokens is not None and new_tier.output_price_per_m_tokens is not None:
                if old_tier.output_price_per_m_tokens != new_tier.output_price_per_m_tokens:
                    pct = ((new_tier.output_price_per_m_tokens - old_tier.output_price_per_m_tokens)
                           / old_tier.output_price_per_m_tokens * 100)
                    delta_type = DeltaType.PRICE_DECREASE if pct < 0 else DeltaType.PRICE_INCREASE
                    severity = self._classify_severity(abs(pct))
                    deltas.append(TrendDelta(
                        competitor_name=new_record.company_name,
                        product_name=new_record.product_name,
                        delta_type=delta_type,
                        metric_name=f"{tier_name}_output_price",
                        old_value=f"${old_tier.output_price_per_m_tokens:.2f}/1M",
                        new_value=f"${new_tier.output_price_per_m_tokens:.2f}/1M",
                        percentage_change=round(pct, 1),
                        strategic_severity=severity,
                    ))

        # Check for new tiers
        for tier_name in new_tiers:
            if tier_name not in old_tiers:
                deltas.append(TrendDelta(
                    competitor_name=new_record.company_name,
                    product_name=new_record.product_name,
                    delta_type=DeltaType.NEW_TIER,
                    metric_name=tier_name,
                    old_value=None,
                    new_value=f"NEW: {tier_name}",
                    strategic_severity="MEDIUM",
                ))

        return deltas

    @staticmethod
    def _classify_severity(abs_pct_change: float) -> str:
        """Classify the strategic severity of a price change."""
        if abs_pct_change >= 30:
            return "CRITICAL"
        elif abs_pct_change >= 15:
            return "HIGH"
        elif abs_pct_change >= 5:
            return "MEDIUM"
        else:
            return "LOW"
