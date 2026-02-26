"""Handoff router — select the most suitable human agent for a handoff package.

HandoffRouter implements a lightweight, configurable routing algorithm that
considers agent skills, current workload, and the urgency of the handoff
package to make assignment decisions.

All routing is performed in-process; this module does not make network calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from agent_sense.handoff.packager import HandoffPackage, UrgencyLevel


@dataclass
class HumanAgent:
    """A human agent who can receive handoff packages.

    Attributes
    ----------
    agent_id:
        Unique identifier for this agent (e.g. employee ID or username).
    name:
        Display name for UI rendering and notifications.
    skills:
        Set of skill/domain tags this agent handles (e.g. ``{"billing", "tech"}``).
    current_load:
        Current number of active assignments. Used to balance load.
    max_load:
        Maximum number of simultaneous assignments this agent can handle.
    is_available:
        Whether the agent is currently accepting new assignments.
    priority:
        Higher-priority agents (larger integer) are preferred when all else
        is equal. Default 0.
    """

    agent_id: str
    name: str
    skills: frozenset[str] = field(default_factory=frozenset)
    current_load: int = 0
    max_load: int = 5
    is_available: bool = True
    priority: int = 0

    def has_capacity(self) -> bool:
        """Return True if the agent can accept another assignment."""
        return self.is_available and self.current_load < self.max_load

    def load_ratio(self) -> float:
        """Return current_load / max_load, or 1.0 if max_load is zero."""
        if self.max_load <= 0:
            return 1.0
        return self.current_load / self.max_load

    def skill_overlap(self, required_skills: frozenset[str]) -> int:
        """Return the number of required skills matched by this agent."""
        return len(self.skills & required_skills)


class NoAvailableAgentError(RuntimeError):
    """Raised when HandoffRouter cannot find a suitable agent."""

    def __init__(self) -> None:
        super().__init__(
            "No available human agent could be found for the handoff package. "
            "Ensure at least one agent has capacity and matching skills."
        )


class HandoffRouter:
    """Route HandoffPackage instances to the most suitable available human agent.

    Routing logic (in priority order):

    1. Exclude agents that are unavailable or at capacity.
    2. Prefer agents whose skill set overlaps with the package's ``metadata``
       ``"required_skills"`` tag (comma-separated).
    3. For CRITICAL urgency, prefer agents with ``"critical"`` in their skills.
    4. Among candidates, prefer lower load ratio, then higher agent priority.

    Parameters
    ----------
    agents:
        Initial list of HumanAgent objects available for routing.

    Example
    -------
    >>> from agent_sense.handoff.packager import HandoffPackager, UrgencyLevel
    >>> agent = HumanAgent(agent_id="a1", name="Alice", skills=frozenset({"billing"}))
    >>> router = HandoffRouter(agents=[agent])
    >>> pkg = HandoffPackager().package(summary="Billing issue", urgency=UrgencyLevel.HIGH)
    >>> router.route(pkg, available=[agent])
    HumanAgent(agent_id='a1', ...)
    """

    def __init__(self, agents: list[HumanAgent] | None = None) -> None:
        self._agents: list[HumanAgent] = list(agents or [])

    def add_agent(self, agent: HumanAgent) -> None:
        """Register a new agent with the router.

        Parameters
        ----------
        agent:
            The HumanAgent to add.
        """
        self._agents.append(agent)

    def route(
        self,
        package: HandoffPackage,
        available: list[HumanAgent] | None = None,
    ) -> HumanAgent:
        """Select and return the best human agent for the given package.

        Parameters
        ----------
        package:
            The HandoffPackage to route.
        available:
            Override the router's agent pool with this list. Useful for
            injecting real-time availability data from an external system.
            If None, the router's registered agents are used.

        Returns
        -------
        HumanAgent
            The selected agent.

        Raises
        ------
        NoAvailableAgentError
            If no agent has capacity or suitable skills.
        """
        pool = available if available is not None else self._agents

        # Extract required skills from package metadata (if any).
        required_skills = self._parse_required_skills(package)

        # Filter to agents with capacity.
        candidates = [agent for agent in pool if agent.has_capacity()]

        if not candidates:
            raise NoAvailableAgentError()

        # Score each candidate.
        def _score(agent: HumanAgent) -> tuple[int, int, float, int]:
            # Higher skill overlap is better (negated for sort ascending trick).
            skill_overlap = agent.skill_overlap(required_skills)
            # Boost for critical-skilled agents on CRITICAL packages.
            critical_boost = (
                1 if package.urgency == UrgencyLevel.CRITICAL and "critical" in agent.skills
                else 0
            )
            # Lower load ratio is better (negated).
            load = agent.load_ratio()
            # Higher agent priority is better.
            priority = agent.priority
            # Sort key: largest first for overlap, critical_boost, priority;
            # smallest first for load.
            return (-skill_overlap, -critical_boost, load, -priority)

        candidates.sort(key=_score)
        return candidates[0]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_required_skills(package: HandoffPackage) -> frozenset[str]:
        """Extract required skills from package metadata.

        Reads ``package.metadata["required_skills"]`` if present, expecting a
        comma-separated list (e.g. ``"billing,tech-support"``).
        """
        raw = package.metadata.get("required_skills", "")
        if not raw:
            return frozenset()
        return frozenset(tag.strip().lower() for tag in raw.split(",") if tag.strip())
