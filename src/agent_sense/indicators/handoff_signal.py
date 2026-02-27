"""Universal AI transparency — handoff signal.

A HandoffSignal is produced when an AI agent determines it should not
continue handling a request and needs to escalate to another agent
or a human specialist.

HandoffReason documents why the escalation is happening.  Signals with
reason SAFETY_CONCERN are always considered urgent.

Example
-------
>>> from agent_sense.indicators.confidence import from_score
>>> confidence = from_score(0.12, reasoning="Topic outside training data")
>>> signal = HandoffSignal(
...     reason=HandoffReason.CONFIDENCE_TOO_LOW,
...     confidence=confidence,
...     suggested_specialist="domain expert",
...     context_summary="User asked about proprietary legal contracts.",
...     timestamp=datetime.datetime.now(datetime.timezone.utc),
... )
>>> signal.is_urgent()
False
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum

from agent_sense.indicators.confidence import ConfidenceIndicator


class HandoffReason(str, Enum):
    """Reasons an agent may escalate a conversation."""

    CONFIDENCE_TOO_LOW = "confidence_too_low"
    OUT_OF_SCOPE = "out_of_scope"
    USER_REQUEST = "user_request"
    SAFETY_CONCERN = "safety_concern"
    COMPLEXITY_EXCEEDED = "complexity_exceeded"
    REQUIRES_HUMAN_JUDGMENT = "requires_human_judgment"


# Reasons that always result in an urgent handoff.
_ALWAYS_URGENT: frozenset[HandoffReason] = frozenset({HandoffReason.SAFETY_CONCERN})


@dataclass(frozen=True)
class HandoffSignal:
    """Structured escalation signal emitted by an AI agent.

    Attributes
    ----------
    reason:
        Why the handoff is happening.
    confidence:
        The agent's confidence indicator at the moment of escalation.
    suggested_specialist:
        Description of the ideal handler (e.g. ``"human agent"``,
        ``"billing specialist"``).
    context_summary:
        Brief, human-readable summary of the conversation state
        passed to the receiving specialist.
    timestamp:
        UTC datetime when this signal was created.
    """

    reason: HandoffReason
    confidence: ConfidenceIndicator
    suggested_specialist: str
    context_summary: str
    timestamp: datetime.datetime

    def is_urgent(self) -> bool:
        """Return True if this handoff requires immediate attention.

        SAFETY_CONCERN signals are always urgent regardless of confidence
        score.  All other reasons return False.

        Returns
        -------
        bool
        """
        return self.reason in _ALWAYS_URGENT

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary suitable for JSON encoding.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "reason": self.reason.value,
            "confidence": self.confidence.to_dict(),
            "suggested_specialist": self.suggested_specialist,
            "context_summary": self.context_summary,
            "timestamp": self.timestamp.isoformat(),
            "is_urgent": self.is_urgent(),
        }
