"""Scrybe Rolling Action Buffer.

Short-term memory maintaining the last N agent actions, errors,
and outcomes for error recovery and context injection.
"""

from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional


class ActionEntry:
    """A single recorded agent action."""

    __slots__ = ("timestamp", "agent", "action", "source_url", "status", "error", "metadata")

    def __init__(
        self,
        agent: str,
        action: str,
        status: str = "OK",
        source_url: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.agent = agent
        self.action = action
        self.status = status  # OK | ERROR | SKIPPED | RETRIED
        self.source_url = source_url
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "source_url": self.source_url,
            "error": self.error,
            "metadata": self.metadata,
        }


class RollingBuffer:
    """Fixed-size circular buffer of recent agent actions.

    Used for error recovery context: when an extraction fails,
    the Reflexion agent can inspect recent actions to understand
    what went wrong and adjust strategy.
    """

    def __init__(self, max_size: int = 20):
        self._buffer: Deque[ActionEntry] = deque(maxlen=max_size)

    def record(
        self,
        agent: str,
        action: str,
        status: str = "OK",
        source_url: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an agent action in the buffer."""
        self._buffer.append(
            ActionEntry(
                agent=agent,
                action=action,
                status=status,
                source_url=source_url,
                error=error,
                metadata=metadata,
            )
        )

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent actions as dictionaries."""
        items = list(self._buffer)
        return [item.to_dict() for item in items[-n:]]

    def get_recent_errors(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get only recent error entries."""
        errors = [e for e in self._buffer if e.status == "ERROR"]
        return [e.to_dict() for e in errors[-n:]]

    def get_context_string(self, n: int = 5) -> str:
        """Generate a text summary of recent actions for prompt injection."""
        recent = self.get_recent(n)
        if not recent:
            return "No recent actions recorded."

        lines = ["Recent pipeline actions:"]
        for entry in recent:
            status_icon = "✅" if entry["status"] == "OK" else "❌"
            line = f"  {status_icon} [{entry['agent']}] {entry['action']}"
            if entry.get("source_url"):
                line += f" @ {entry['source_url']}"
            if entry.get("error"):
                line += f" — Error: {entry['error']}"
            lines.append(line)
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        self._buffer.clear()

    @property
    def size(self) -> int:
        return len(self._buffer)
