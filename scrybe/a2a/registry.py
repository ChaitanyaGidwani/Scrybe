"""A2A Agent Registry — Local agent discovery and registration.

Manages the mapping between agent names and their A2A endpoints.
Supports both static configuration (from settings) and dynamic
registration (agents registering themselves at startup).

In production, this would be backed by a service registry like
Consul, etcd, or Kubernetes service discovery.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from scrybe.a2a.models import AgentCard
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("a2a_registry")


class AgentRegistration(object):
    """A single registered agent with its card and health status."""

    def __init__(self, card: AgentCard, registered_at: Optional[datetime] = None):
        self.card = card
        self.registered_at = registered_at or datetime.now(timezone.utc)
        self.last_health_check: Optional[datetime] = None
        self.healthy: bool = True
        self.consecutive_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.card.name,
            "url": self.card.url,
            "description": self.card.description,
            "version": self.card.version,
            "skills": [s.id for s in self.card.skills],
            "healthy": self.healthy,
            "registered_at": self.registered_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
        }


class AgentRegistry:
    """In-memory registry for A2A agent discovery.

    Agents register themselves with their Agent Cards, and the
    orchestrator queries the registry to find available agents
    for task delegation.

    Usage:
        registry = AgentRegistry()
        registry.register(reader_card)
        registry.register(analyst_card)

        reader = registry.get("reader")
        all_agents = registry.list_agents()
    """

    def __init__(self):
        self._agents: Dict[str, AgentRegistration] = {}

    def register(self, card: AgentCard) -> None:
        """Register an agent with its Agent Card.

        Args:
            card: The agent's A2A Agent Card.
        """
        name = card.name.lower().replace(" ", "_")
        self._agents[name] = AgentRegistration(card=card)
        logger.info(
            f"Agent registered: {card.name} at {card.url}",
            extra={"agent": "registry", "step": "register"},
        )

    def deregister(self, name: str) -> None:
        """Remove an agent from the registry.

        Args:
            name: Agent name (case-insensitive).
        """
        key = name.lower().replace(" ", "_")
        if key in self._agents:
            del self._agents[key]
            logger.info(f"Agent deregistered: {name}")

    def get(self, name: str) -> Optional[AgentCard]:
        """Look up an agent by name.

        Args:
            name: Agent name (case-insensitive, underscore-separated).

        Returns:
            The agent's AgentCard, or None if not found.
        """
        key = name.lower().replace(" ", "_")
        reg = self._agents.get(key)
        return reg.card if reg else None

    def get_url(self, name: str) -> Optional[str]:
        """Get the URL for a registered agent.

        Args:
            name: Agent name.

        Returns:
            The agent's base URL, or None.
        """
        card = self.get(name)
        return card.url if card else None

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their status.

        Returns:
            List of agent registration info dicts.
        """
        return [reg.to_dict() for reg in self._agents.values()]

    def list_healthy_agents(self) -> List[AgentCard]:
        """List only healthy agents.

        Returns:
            List of AgentCards for healthy agents.
        """
        return [reg.card for reg in self._agents.values() if reg.healthy]

    def find_by_skill(self, skill_id: str) -> List[AgentCard]:
        """Find agents that have a specific skill.

        Args:
            skill_id: The skill ID to search for.

        Returns:
            List of AgentCards with the matching skill.
        """
        results = []
        for reg in self._agents.values():
            if any(s.id == skill_id for s in reg.card.skills):
                results.append(reg.card)
        return results

    def mark_healthy(self, name: str) -> None:
        """Mark an agent as healthy after a successful health check."""
        key = name.lower().replace(" ", "_")
        if key in self._agents:
            self._agents[key].healthy = True
            self._agents[key].consecutive_failures = 0
            self._agents[key].last_health_check = datetime.now(timezone.utc)

    def mark_unhealthy(self, name: str) -> None:
        """Mark an agent as unhealthy after a failed health check."""
        key = name.lower().replace(" ", "_")
        if key in self._agents:
            self._agents[key].consecutive_failures += 1
            self._agents[key].last_health_check = datetime.now(timezone.utc)
            if self._agents[key].consecutive_failures >= 3:
                self._agents[key].healthy = False
                logger.warning(f"Agent marked unhealthy: {name}")

    async def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all registered agents.

        Fetches each agent's Agent Card to verify reachability.

        Returns:
            Dict mapping agent names to health status.
        """
        import httpx

        results = {}
        for name, reg in self._agents.items():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    card_url = f"{reg.card.url.rstrip('/')}/.well-known/agent-card.json"
                    response = await client.get(card_url)
                    response.raise_for_status()
                    self.mark_healthy(name)
                    results[name] = True
            except Exception:
                self.mark_unhealthy(name)
                results[name] = False

        return results

    @property
    def agent_count(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    @property
    def healthy_count(self) -> int:
        """Number of healthy agents."""
        return sum(1 for r in self._agents.values() if r.healthy)
