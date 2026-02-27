"""Context packager — packages conversation context for human handoff.

When an agent escalates to a human reviewer, the ContextPackager produces a
structured ContextPackage that gives the human operator everything they need
to continue the conversation:

- A concise summary of the conversation so far
- Key decisions made by the agent and their reasoning
- The current confidence assessment
- Conversation history (recent turns)
- Recommendations for the human reviewer

The packager is intentionally simple and does not require external LLM calls —
summaries are assembled from the raw conversation data provided by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConversationTurn:
    """A single turn in the conversation history.

    Attributes
    ----------
    role:
        Message originator: ``"user"``, ``"assistant"``, or ``"system"``.
    content:
        The text content of this turn.
    timestamp:
        UTC time at which this turn occurred.
    turn_index:
        Zero-based sequential position in the conversation.
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_index: int = 0


@dataclass(frozen=True)
class DecisionRecord:
    """A decision made by the agent during the conversation.

    Attributes
    ----------
    decision:
        Short label describing the decision (e.g. ``"use_tool"``,
        ``"refuse_request"``).
    reasoning:
        Free-text explanation of why this decision was made.
    confidence:
        Confidence score for this decision in [0.0, 1.0].
    timestamp:
        UTC time at which the decision was made.
    """

    decision: str
    reasoning: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# ContextPackage
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContextPackage:
    """Structured context bundle for human handoff.

    Attributes
    ----------
    package_id:
        Unique identifier for this context package.
    created_at:
        UTC time at which the package was assembled.
    session_id:
        Identifier of the originating agent session.
    summary:
        Concise narrative summary of the conversation.
    conversation_turns:
        Recent conversation turns (may be truncated for brevity).
    key_decisions:
        Agent decisions made during the conversation.
    confidence_score:
        Final confidence score that triggered escalation.
    confidence_label:
        Human-readable confidence label (e.g. ``"Low Confidence"``).
    escalation_reason:
        Description of why this interaction is being escalated.
    recommendations:
        Suggested next actions for the human reviewer.
    metadata:
        Arbitrary additional annotations.
    """

    package_id: str
    created_at: datetime
    session_id: str
    summary: str
    conversation_turns: list[ConversationTurn]
    key_decisions: list[DecisionRecord]
    confidence_score: float
    confidence_label: str
    escalation_reason: str
    recommendations: list[str]
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dict suitable for JSON encoding.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "package_id": self.package_id,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
            "summary": self.summary,
            "conversation_turns": [
                {
                    "role": t.role,
                    "content": t.content,
                    "timestamp": t.timestamp.isoformat(),
                    "turn_index": t.turn_index,
                }
                for t in self.conversation_turns
            ],
            "key_decisions": [
                {
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp.isoformat(),
                }
                for d in self.key_decisions
            ],
            "confidence_score": self.confidence_score,
            "confidence_label": self.confidence_label,
            "escalation_reason": self.escalation_reason,
            "recommendations": list(self.recommendations),
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# ContextPackager
# ---------------------------------------------------------------------------

_CONFIDENCE_LABEL_MAP: list[tuple[float, str]] = [
    (0.70, "High Confidence"),
    (0.40, "Medium Confidence"),
    (0.00, "Low Confidence"),
]


def _label_for_score(score: float) -> str:
    """Map a numeric confidence score to a human-readable label."""
    for threshold, label in _CONFIDENCE_LABEL_MAP:
        if score >= threshold:
            return label
    return "Low Confidence"


class ContextPackager:
    """Assembles ContextPackage instances for human handoff.

    Parameters
    ----------
    session_id:
        The session identifier to embed in every package.
    max_turns:
        Maximum number of conversation turns to include in the package.
        Older turns are dropped first.

    Example
    -------
    >>> packager = ContextPackager(session_id="sess-001")
    >>> turns = [ConversationTurn(role="user", content="Hello")]
    >>> pkg = packager.package(
    ...     turns=turns,
    ...     decisions=[],
    ...     confidence_score=0.25,
    ...     escalation_reason="Confidence too low",
    ... )
    >>> pkg.confidence_label
    'Low Confidence'
    """

    def __init__(
        self,
        session_id: str = "",
        max_turns: int = 20,
    ) -> None:
        self._session_id = session_id
        self._max_turns = max(1, max_turns)

    def package(
        self,
        *,
        turns: list[ConversationTurn],
        decisions: list[DecisionRecord],
        confidence_score: float,
        escalation_reason: str,
        summary: str = "",
        recommendations: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ContextPackage:
        """Produce a ContextPackage from the current conversation state.

        Parameters
        ----------
        turns:
            All conversation turns up to the point of escalation.
        decisions:
            Agent decisions made during the conversation.
        confidence_score:
            Final confidence score that triggered escalation.
        escalation_reason:
            Human-readable description of why escalation was initiated.
        summary:
            Optional override for the package summary.  When not provided,
            a summary is auto-generated from the conversation turns.
        recommendations:
            Optional list of recommended actions for the human reviewer.
        metadata:
            Optional extra annotations.

        Returns
        -------
        ContextPackage
            Frozen context package ready for delivery to a human reviewer.
        """
        truncated_turns = turns[-self._max_turns :]
        resolved_summary = summary if summary.strip() else self._auto_summary(
            truncated_turns, confidence_score, escalation_reason
        )
        resolved_recommendations = list(recommendations or [])
        if not resolved_recommendations:
            resolved_recommendations = self._default_recommendations(confidence_score)

        return ContextPackage(
            package_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            session_id=self._session_id,
            summary=resolved_summary,
            conversation_turns=list(truncated_turns),
            key_decisions=list(decisions),
            confidence_score=confidence_score,
            confidence_label=_label_for_score(confidence_score),
            escalation_reason=escalation_reason,
            recommendations=resolved_recommendations,
            metadata=dict(metadata or {}),
        )

    def _auto_summary(
        self,
        turns: list[ConversationTurn],
        confidence_score: float,
        escalation_reason: str,
    ) -> str:
        """Generate a minimal summary from the available conversation data."""
        turn_count = len(turns)
        user_turns = [t for t in turns if t.role == "user"]
        last_user_content = user_turns[-1].content[:120] if user_turns else "(no user input)"
        return (
            f"Conversation with {turn_count} turns. "
            f"Last user message: \"{last_user_content}\". "
            f"Escalation reason: {escalation_reason}. "
            f"Confidence: {confidence_score:.0%}."
        )

    def _default_recommendations(self, confidence_score: float) -> list[str]:
        """Generate default reviewer recommendations based on confidence score."""
        if confidence_score < 0.40:
            return [
                "Review the full conversation history before responding.",
                "Verify any factual claims made by the agent.",
                "Consider whether additional specialist input is required.",
            ]
        return [
            "Review the agent's key decisions for accuracy.",
            "Confirm the proposed next steps with the user.",
        ]
