"""Scrybe Reflexion Agent.

Implements the Reflexion pattern (arXiv:2303.11366) for self-correcting
extraction failures. When validation fails, the agent conducts verbal
self-critique, identifies root causes, and produces corrected output.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from scrybe.logging_config import get_agent_logger
from scrybe.tools.extractor import parse_llm_json_response

logger = get_agent_logger("reflexion")


def build_reflexion_prompt(
    agent_name: str,
    input_excerpt: str,
    error_trace: str,
    recent_actions: str = "",
) -> str:
    """Build a Reflexion self-critique prompt from the error context.

    Args:
        agent_name: The agent that failed.
        input_excerpt: Truncated input that caused the failure.
        error_trace: The validation error or exception trace.
        recent_actions: Optional recent action buffer context.

    Returns:
        Formatted Reflexion prompt string.
    """
    prompt_path = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "reflexion_repair.txt"

    if prompt_path.exists():
        template = prompt_path.read_text(encoding="utf-8")
        return template.format(
            agent_name=agent_name,
            input_excerpt=input_excerpt[:2000],
            error_trace=error_trace[:1000],
        )

    # Inline fallback prompt
    return f"""You are Scrybe's Reflexion Agent. An extraction or validation failure occurred.

PREVIOUS EXECUTION ATTEMPT:
Agent: {agent_name}
Input Excerpt: {input_excerpt[:2000]}
Error: {error_trace[:1000]}

{f"RECENT ACTIONS:{chr(10)}{recent_actions}" if recent_actions else ""}

INSTRUCTIONS:
1. Conduct a brief verbal self-critique explaining WHY the previous attempt failed.
2. Formulate a concrete correction strategy.
3. Produce the corrected, validated JSON output.

OUTPUT FORMAT (JSON only):
{{
  "critique": "string",
  "root_cause": "SCHEMA_MISMATCH | TOKEN_MULTIPLIER_ERROR | INVALID_JSON | UNGROUNDED_VALUE",
  "remedy": "string",
  "corrected_output": {{ ... }}
}}"""


def apply_reflexion_repair(
    raw_reflexion_response: str,
) -> Dict[str, Any]:
    """Parse the Reflexion agent's self-repair response.

    Args:
        raw_reflexion_response: Raw LLM output from the Reflexion prompt.

    Returns:
        Dictionary containing critique, root_cause, remedy, and corrected_output.
    """
    parsed = parse_llm_json_response(raw_reflexion_response)

    logger.info(
        "Reflexion repair applied",
        extra={
            "agent": "reflexion",
            "step": "apply_repair",
            "error_type": parsed.get("root_cause", "UNKNOWN"),
        },
    )

    return {
        "critique": parsed.get("critique", ""),
        "root_cause": parsed.get("root_cause", "UNKNOWN"),
        "remedy": parsed.get("remedy", ""),
        "corrected_output": parsed.get("corrected_output", {}),
    }


class ReflexionLoop:
    """Manages the Reflexion self-correction loop for an agent.

    Tracks repair attempts and enforces a maximum retry limit
    to prevent infinite loops.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.attempts: List[Dict[str, Any]] = []

    def should_retry(self) -> bool:
        """Check if another retry is allowed."""
        return len(self.attempts) < self.max_retries

    def record_attempt(
        self,
        agent_name: str,
        error_trace: str,
        repair_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a repair attempt."""
        self.attempts.append({
            "attempt_number": len(self.attempts) + 1,
            "agent": agent_name,
            "error": error_trace,
            "repair": repair_result,
        })

    def get_history_summary(self) -> str:
        """Get a text summary of all repair attempts for context injection."""
        if not self.attempts:
            return ""
        lines = [f"Previous repair attempts ({len(self.attempts)}/{self.max_retries}):"]
        for attempt in self.attempts:
            repair = attempt.get("repair", {})
            lines.append(
                f"  Attempt {attempt['attempt_number']}: "
                f"Root cause = {repair.get('root_cause', 'N/A')}, "
                f"Remedy = {repair.get('remedy', 'N/A')[:100]}"
            )
        return "\n".join(lines)

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)
