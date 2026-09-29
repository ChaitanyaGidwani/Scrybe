"""Scrybe Analyst Agent.

Extracts structured pricing and feature data from cleaned web content
using LLM-based extraction with strict zero-hallucination guardrails.
Validates all output via the grounding validator and Reflexion loop.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from scrybe.exceptions import ExtractionError
from scrybe.logging_config import get_agent_logger
from scrybe.memory.buffer import RollingBuffer
from scrybe.memory.reflection import ReflexionLoop, build_reflexion_prompt, apply_reflexion_repair
from scrybe.storage.models import CompetitorProductRecord, RawScrapedDocument
from scrybe.tools.constrained_decoder import ConstrainedDecoder
from scrybe.tools.extractor import build_extraction_prompt, parse_llm_json_response
from scrybe.tools.validator import validate_record

logger = get_agent_logger("analyst")


class AnalystAgent:
    """Autonomous agent for structured data extraction.

    Takes cleaned web content and produces validated, typed
    CompetitorProductRecord instances with confidence scoring.
    Invokes Reflexion self-repair on validation failures.
    """

    def __init__(
        self,
        llm_client=None,
        extraction_model: str = "gpt-4o-mini",
        confidence_threshold: float = 0.60,
        max_reflexion_retries: int = 2,
        buffer: Optional[RollingBuffer] = None,
    ):
        self.llm_client = llm_client
        self.extraction_model = extraction_model
        self.confidence_threshold = confidence_threshold
        self.max_reflexion_retries = max_reflexion_retries
        self.buffer = buffer or RollingBuffer()

    def run(
        self,
        documents: List[RawScrapedDocument],
    ) -> Tuple[List[CompetitorProductRecord], List[Dict[str, Any]]]:
        """Extract structured records from all scraped documents.

        Args:
            documents: List of raw scraped documents from Reader Agent.

        Returns:
            Tuple of (validated_records, flagged_records).
            Validated records have confidence >= threshold.
            Flagged records fell below threshold or had extraction errors.
        """
        validated = []
        flagged = []

        for doc in documents:
            try:
                record, is_valid = self._extract_and_validate(doc)

                if is_valid:
                    validated.append(record)
                    self.buffer.record(
                        agent="analyst",
                        action=f"extracted_{record.company_name}",
                        status="OK",
                        source_url=doc.url,
                        metadata={"confidence": record.extraction_confidence},
                    )
                else:
                    flagged.append({
                        "source_url": doc.url,
                        "domain": doc.domain,
                        "reason": f"Confidence {record.extraction_confidence:.2f} < {self.confidence_threshold}",
                        "record": record.model_dump(),
                    })
                    self.buffer.record(
                        agent="analyst",
                        action=f"flagged_{doc.domain}",
                        status="FLAGGED",
                        source_url=doc.url,
                        metadata={"confidence": record.extraction_confidence},
                    )

                logger.info(
                    f"Extraction complete: {record.company_name}",
                    extra={
                        "agent": "analyst",
                        "step": "extract",
                        "source_url": doc.url,
                        "confidence": record.extraction_confidence,
                    },
                )

            except Exception as e:
                flagged.append({
                    "source_url": doc.url,
                    "domain": doc.domain,
                    "reason": f"Extraction failed: {str(e)[:200]}",
                })
                self.buffer.record(
                    agent="analyst",
                    action=f"extraction_error_{doc.domain}",
                    status="ERROR",
                    source_url=doc.url,
                    error=str(e)[:200],
                )
                logger.error(f"Extraction failed for {doc.url}: {e}")

        return validated, flagged

    def _extract_and_validate(
        self,
        doc: RawScrapedDocument,
    ) -> Tuple[CompetitorProductRecord, bool]:
        """Extract structured data and validate with Reflexion retry.

        Args:
            doc: A single scraped document.

        Returns:
            Tuple of (validated record, is_above_threshold).
        """
        # Build the extraction prompt
        prompt = build_extraction_prompt(
            markdown_content=doc.content_markdown[:8000],  # Token budget control
            source_url=doc.url,
        )

        reflexion_loop = ReflexionLoop(max_retries=self.max_reflexion_retries)

        while True:
            try:
                # Call LLM for extraction
                raw_response = self._call_llm(prompt)
                extracted = parse_llm_json_response(raw_response)

                # Schema-constrained sanitization and character-level DOM grounding
                record, grounding_ratio, ungrounded = ConstrainedDecoder.decode_and_ground(
                    extracted, source_text=doc.content_markdown
                )

                if ungrounded:
                    logger.warning(
                        f"Ungrounded extraction fields detected for {doc.url}: {ungrounded[:3]}"
                    )

                # Validate and score
                record, is_valid = validate_record(
                    record.model_dump(),
                    source_text=doc.content_markdown,
                    confidence_threshold=self.confidence_threshold,
                )
                return record, is_valid

            except (ExtractionError, Exception) as e:
                if not reflexion_loop.should_retry():
                    logger.warning(f"Reflexion retries exhausted for {doc.url}")
                    raise

                # Attempt Reflexion self-repair
                logger.info(f"Triggering Reflexion repair (attempt {reflexion_loop.total_attempts + 1})")

                reflexion_prompt = build_reflexion_prompt(
                    agent_name="analyst",
                    input_excerpt=doc.content_markdown[:1000],
                    error_trace=str(e),
                    recent_actions=self.buffer.get_context_string(3),
                )

                repair_response = self._call_llm(reflexion_prompt)
                repair_result = apply_reflexion_repair(repair_response)
                reflexion_loop.record_attempt("analyst", str(e), repair_result)

                # Use corrected output from Reflexion with constrained decoding
                corrected = repair_result.get("corrected_output", {})
                if corrected:
                    try:
                        record, _, _ = ConstrainedDecoder.decode_and_ground(
                            corrected, source_text=doc.content_markdown
                        )
                        record, is_valid = validate_record(
                            record.model_dump(),
                            source_text=doc.content_markdown,
                            confidence_threshold=self.confidence_threshold,
                        )
                        return record, is_valid
                    except Exception:
                        continue  # Try again if still invalid

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM for extraction or repair.

        Uses the injected llm_client if available, otherwise raises.
        """
        if self.llm_client is None:
            raise ExtractionError(
                "No LLM client configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY "
                "in .env and pass an LLMClient to AnalystAgent."
            )

        return self.llm_client.generate(
            prompt=prompt,
            model=self.extraction_model,
            system_prompt="You are a precise data extraction agent. Output only valid JSON.",
            temperature=0.0,
            json_mode=True,
        )
