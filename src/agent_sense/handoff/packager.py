"""Handoff packager — assemble context bundles for human agent handoff.

When an AI agent cannot resolve a user request, it must hand off to a human
agent with enough structured context to continue the conversation without
repeating information the user already provided.

HandoffPackager creates a HandoffPackage — a structured, human-readable
snapshot of the conversation state at the moment of escalation.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum


class UrgencyLevel(str, Enum):
    """Urgency classification for a handoff request."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class HandoffPackage:
    """Immutable bundle of context passed to a human agent at handoff time.

    Attributes
    ----------
    summary:
        One or two sentence summary of what the user needs.
    key_facts:
        Ordered list of important facts established during the conversation.
    unresolved_questions:
        Questions the AI could not answer that the human should address.
    attempted_actions:
        Actions the AI already tried, so the human does not repeat them.
    urgency:
        How urgently a human agent should respond.
    timestamp:
        UTC datetime when this package was created.
    session_id:
        Optional identifier linking this package to an upstream session.
    metadata:
        Arbitrary string key/value pairs for downstream routing or logging.
    """

    summary: str
    key_facts: list[str]
    unresolved_questions: list[str]
    attempted_actions: list[str]
    urgency: UrgencyLevel
    timestamp: datetime.datetime
    session_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary for JSON encoding.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "summary": self.summary,
            "key_facts": list(self.key_facts),
            "unresolved_questions": list(self.unresolved_questions),
            "attempted_actions": list(self.attempted_actions),
            "urgency": self.urgency.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
        }


class HandoffPackager:
    """Assemble HandoffPackage instances from conversation state.

    Parameters
    ----------
    session_id:
        Optional session identifier carried into every package produced.
    default_urgency:
        The urgency level assigned when the caller does not specify one.

    Example
    -------
    >>> packager = HandoffPackager(session_id="sess-001")
    >>> pkg = packager.package(
    ...     summary="User cannot reset their password.",
    ...     key_facts=["User email: alice@example.com"],
    ...     unresolved_questions=["Is the account locked?"],
    ...     attempted_actions=["Sent password-reset email (no response)"],
    ...     urgency=UrgencyLevel.HIGH,
    ... )
    >>> pkg.urgency
    <UrgencyLevel.HIGH: 'high'>
    """

    def __init__(
        self,
        session_id: str = "",
        default_urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
    ) -> None:
        self._session_id = session_id
        self._default_urgency = default_urgency

    def package(
        self,
        summary: str,
        key_facts: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        attempted_actions: list[str] | None = None,
        urgency: UrgencyLevel | None = None,
        metadata: dict[str, str] | None = None,
    ) -> HandoffPackage:
        """Create a HandoffPackage from the supplied conversation state.

        Parameters
        ----------
        summary:
            Brief description of the user's unresolved need.
        key_facts:
            Facts established during the AI interaction. Defaults to ``[]``.
        unresolved_questions:
            Open questions for the human agent. Defaults to ``[]``.
        attempted_actions:
            Things the AI already tried. Defaults to ``[]``.
        urgency:
            Urgency level. Falls back to ``default_urgency`` if omitted.
        metadata:
            Optional string key/value pairs for routing.

        Returns
        -------
        HandoffPackage
            Frozen package ready for routing to a human agent.

        Raises
        ------
        ValueError
            If ``summary`` is empty.
        """
        if not summary.strip():
            raise ValueError("HandoffPackage summary must not be empty.")

        return HandoffPackage(
            summary=summary.strip(),
            key_facts=list(key_facts or []),
            unresolved_questions=list(unresolved_questions or []),
            attempted_actions=list(attempted_actions or []),
            urgency=urgency if urgency is not None else self._default_urgency,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            session_id=self._session_id,
            metadata=dict(metadata or {}),
        )
