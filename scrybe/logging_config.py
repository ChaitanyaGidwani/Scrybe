"""Scrybe Structured JSON Logger.

All agents emit structured JSON log lines for observability.
Each log line includes agent name, step, source URL, and confidence.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach extra structured fields if present
        for key in ("agent", "step", "source_url", "confidence", "pipeline_id",
                     "scrape_tier", "domain", "error_type", "delta_type"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for the entire application."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Create a namespaced logger for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'reader', 'analyst').

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(f"scrybe.agents.{agent_name}")
