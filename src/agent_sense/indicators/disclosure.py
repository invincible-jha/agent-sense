"""Universal AI transparency — AI disclosure card.

AIDisclosureCard carries all the information a user needs to understand
who or what they are interacting with: the agent identity, underlying
model, capabilities, limitations, and data-handling practices.

DisclosureLevel controls how much detail is surfaced in rendered output:
- MINIMAL  : agent name and model provider only
- STANDARD : adds capabilities list
- DETAILED : adds limitations
- FULL     : all fields including data handling and last-updated date

Example
-------
>>> card = build_disclosure(
...     agent_name="Aria",
...     model_provider="Anthropic",
...     model_name="claude-sonnet-4-6",
...     capabilities=["answering questions", "summarising documents"],
...     limitations=["no real-time data"],
...     data_handling="Conversations are not stored beyond the session.",
... )
>>> card.disclosure_level
<DisclosureLevel.STANDARD: 'standard'>
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum


class DisclosureLevel(str, Enum):
    """Controls the verbosity of disclosure card rendering."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    FULL = "full"


@dataclass(frozen=True)
class AIDisclosureCard:
    """Immutable disclosure card for an AI agent deployment.

    Attributes
    ----------
    agent_name:
        Human-readable name of the agent (e.g. ``"Aria"``).
    agent_version:
        Semantic version or build identifier (e.g. ``"1.2.0"``).
    model_provider:
        Organisation that produced the underlying model
        (e.g. ``"Anthropic"``, ``"OpenAI"``).
    model_name:
        Identifier of the specific model being used.
    capabilities:
        Ordered list of things this agent can do well.
    limitations:
        Ordered list of known constraints or failure modes.
    data_handling:
        Plain-language description of how conversation data is processed
        and retained.
    last_updated:
        UTC datetime at which this disclosure card was last revised.
    disclosure_level:
        Verbosity level used when rendering this card.
    """

    agent_name: str
    agent_version: str
    model_provider: str
    model_name: str
    capabilities: list[str]
    limitations: list[str]
    data_handling: str
    last_updated: datetime.datetime
    disclosure_level: DisclosureLevel = DisclosureLevel.STANDARD

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary suitable for JSON encoding.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "capabilities": list(self.capabilities),
            "limitations": list(self.limitations),
            "data_handling": self.data_handling,
            "last_updated": self.last_updated.isoformat(),
            "disclosure_level": self.disclosure_level.value,
        }


def build_disclosure(
    agent_name: str,
    model_provider: str,
    model_name: str = "",
    agent_version: str = "1.0.0",
    capabilities: list[str] | None = None,
    limitations: list[str] | None = None,
    data_handling: str = "",
    last_updated: datetime.datetime | None = None,
    disclosure_level: DisclosureLevel = DisclosureLevel.STANDARD,
) -> AIDisclosureCard:
    """Build an AIDisclosureCard with sensible defaults.

    Parameters
    ----------
    agent_name:
        Human-readable name of the agent.
    model_provider:
        Organisation that produced the underlying model.
    model_name:
        Specific model identifier.  Defaults to an empty string.
    agent_version:
        Version string.  Defaults to ``"1.0.0"``.
    capabilities:
        What the agent can do.  Defaults to an empty list.
    limitations:
        Known constraints.  Defaults to an empty list.
    data_handling:
        Description of data-handling practices.  Defaults to an empty
        string.
    last_updated:
        UTC datetime for the card.  Defaults to ``datetime.utcnow()``.
    disclosure_level:
        Verbosity for rendering.  Defaults to STANDARD.

    Returns
    -------
    AIDisclosureCard
        Frozen disclosure card.

    Raises
    ------
    ValueError
        If ``agent_name`` or ``model_provider`` is empty.
    """
    if not agent_name.strip():
        raise ValueError("agent_name must not be empty.")
    if not model_provider.strip():
        raise ValueError("model_provider must not be empty.")

    resolved_timestamp = (
        last_updated
        if last_updated is not None
        else datetime.datetime.now(datetime.timezone.utc)
    )

    return AIDisclosureCard(
        agent_name=agent_name.strip(),
        agent_version=agent_version,
        model_provider=model_provider.strip(),
        model_name=model_name,
        capabilities=list(capabilities) if capabilities is not None else [],
        limitations=list(limitations) if limitations is not None else [],
        data_handling=data_handling,
        last_updated=resolved_timestamp,
        disclosure_level=disclosure_level,
    )
