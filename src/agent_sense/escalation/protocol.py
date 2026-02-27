"""Escalation protocol — configurable fallback chain for agent interactions.

EscalationProtocol manages a three-level fallback chain:
  Level 1: agent         — the primary AI agent handles the request
  Level 2: supervisor    — a supervisor agent (or more capable model) reviews
  Level 3: human         — a human operator takes over

The protocol evaluates a set of configurable triggers to determine whether
escalation should be initiated and to which level.

Trigger types
-------------
LOW_CONFIDENCE    — confidence score falls below a threshold
HIGH_RISK         — agent flags the action as high-risk
REPEATED_FAILURE  — tool or LLM failure count exceeds a threshold
USER_REQUESTED    — user explicitly requested human assistance
POLICY_VIOLATION  — governance policy signals a violation
TIMEOUT           — interaction time exceeds a configured maximum
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class EscalationLevel(str, Enum):
    """The three-tier escalation hierarchy."""

    AGENT = "agent"
    SUPERVISOR = "supervisor"
    HUMAN = "human"


class EscalationTrigger(str, Enum):
    """Reasons that can initiate an escalation."""

    LOW_CONFIDENCE = "low_confidence"
    HIGH_RISK = "high_risk"
    REPEATED_FAILURE = "repeated_failure"
    USER_REQUESTED = "user_requested"
    POLICY_VIOLATION = "policy_violation"
    TIMEOUT = "timeout"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EscalationTriggerConfig:
    """Configuration for a single escalation trigger.

    Attributes
    ----------
    trigger:
        The trigger type this config governs.
    enabled:
        Whether this trigger is active.
    threshold:
        Numeric threshold for triggers that have one (e.g. LOW_CONFIDENCE
        fires when confidence < threshold; REPEATED_FAILURE fires when
        failure_count >= threshold).
    target_level:
        The escalation level to jump to when this trigger fires.
    """

    trigger: EscalationTrigger
    enabled: bool = True
    threshold: float = 0.0
    target_level: EscalationLevel = EscalationLevel.HUMAN


# ---------------------------------------------------------------------------
# Escalation record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EscalationRecord:
    """Immutable record of an escalation event.

    Attributes
    ----------
    escalation_id:
        Unique identifier for this escalation instance.
    timestamp:
        UTC time at which escalation was triggered.
    from_level:
        The level the interaction was at when escalation was triggered.
    to_level:
        The level the interaction is being escalated to.
    trigger:
        The trigger that caused the escalation.
    reason:
        Human-readable description of the escalation reason.
    metadata:
        Arbitrary extra data attached by the caller.
    """

    escalation_id: str
    timestamp: datetime
    from_level: EscalationLevel
    to_level: EscalationLevel
    trigger: EscalationTrigger
    reason: str
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "escalation_id": self.escalation_id,
            "timestamp": self.timestamp.isoformat(),
            "from_level": self.from_level.value,
            "to_level": self.to_level.value,
            "trigger": self.trigger.value,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# EscalationProtocol
# ---------------------------------------------------------------------------


_DEFAULT_TRIGGER_CONFIGS: list[EscalationTriggerConfig] = [
    EscalationTriggerConfig(
        trigger=EscalationTrigger.LOW_CONFIDENCE,
        enabled=True,
        threshold=0.40,
        target_level=EscalationLevel.SUPERVISOR,
    ),
    EscalationTriggerConfig(
        trigger=EscalationTrigger.HIGH_RISK,
        enabled=True,
        threshold=0.0,
        target_level=EscalationLevel.HUMAN,
    ),
    EscalationTriggerConfig(
        trigger=EscalationTrigger.REPEATED_FAILURE,
        enabled=True,
        threshold=3.0,
        target_level=EscalationLevel.HUMAN,
    ),
    EscalationTriggerConfig(
        trigger=EscalationTrigger.USER_REQUESTED,
        enabled=True,
        threshold=0.0,
        target_level=EscalationLevel.HUMAN,
    ),
    EscalationTriggerConfig(
        trigger=EscalationTrigger.POLICY_VIOLATION,
        enabled=True,
        threshold=0.0,
        target_level=EscalationLevel.HUMAN,
    ),
    EscalationTriggerConfig(
        trigger=EscalationTrigger.TIMEOUT,
        enabled=True,
        threshold=0.0,
        target_level=EscalationLevel.HUMAN,
    ),
]


class EscalationProtocol:
    """Manages the agent → supervisor → human fallback chain.

    Parameters
    ----------
    trigger_configs:
        List of trigger configurations.  Defaults to a standard set that
        handles all trigger types with sensible thresholds.
    initial_level:
        Starting level for new interactions.

    Example
    -------
    >>> protocol = EscalationProtocol()
    >>> protocol.current_level
    <EscalationLevel.AGENT: 'agent'>
    >>> record = protocol.evaluate(
    ...     confidence_score=0.20,
    ...     failure_count=0,
    ...     high_risk=False,
    ...     user_requested=False,
    ...     policy_violation=False,
    ... )
    >>> record is not None and record.trigger == EscalationTrigger.LOW_CONFIDENCE
    True
    """

    def __init__(
        self,
        trigger_configs: list[EscalationTriggerConfig] | None = None,
        initial_level: EscalationLevel = EscalationLevel.AGENT,
    ) -> None:
        self._current_level: EscalationLevel = initial_level
        self._configs: dict[EscalationTrigger, EscalationTriggerConfig] = {}
        configs = trigger_configs if trigger_configs is not None else _DEFAULT_TRIGGER_CONFIGS
        for cfg in configs:
            self._configs[cfg.trigger] = cfg
        self._history: list[EscalationRecord] = []

    @property
    def current_level(self) -> EscalationLevel:
        """The current escalation level for this interaction."""
        return self._current_level

    @property
    def history(self) -> list[EscalationRecord]:
        """Immutable view of all escalation records for this interaction."""
        return list(self._history)

    @property
    def is_escalated(self) -> bool:
        """True when the interaction is no longer at the AGENT level."""
        return self._current_level != EscalationLevel.AGENT

    def evaluate(
        self,
        *,
        confidence_score: float | None = None,
        failure_count: int = 0,
        high_risk: bool = False,
        user_requested: bool = False,
        policy_violation: bool = False,
        timeout: bool = False,
        reason: str = "",
        metadata: dict[str, object] | None = None,
    ) -> EscalationRecord | None:
        """Evaluate current conditions and trigger escalation if warranted.

        Only the first matching enabled trigger is applied per call.  Triggers
        are evaluated in priority order:
        1. POLICY_VIOLATION
        2. USER_REQUESTED
        3. HIGH_RISK
        4. TIMEOUT
        5. REPEATED_FAILURE
        6. LOW_CONFIDENCE

        Parameters
        ----------
        confidence_score:
            Current confidence score in [0.0, 1.0].  Used for LOW_CONFIDENCE.
        failure_count:
            Number of consecutive failures.  Used for REPEATED_FAILURE.
        high_risk:
            Whether the agent flagged this as high-risk.
        user_requested:
            Whether the user explicitly requested human assistance.
        policy_violation:
            Whether a governance policy violation was detected.
        timeout:
            Whether the interaction has timed out.
        reason:
            Optional human-readable override for the escalation reason.
        metadata:
            Optional extra data to attach to the escalation record.

        Returns
        -------
        EscalationRecord | None
            The escalation record if an escalation was triggered, else None.
        """
        trigger_checks: list[tuple[EscalationTrigger, bool, str]] = [
            (
                EscalationTrigger.POLICY_VIOLATION,
                policy_violation,
                "Policy violation detected",
            ),
            (
                EscalationTrigger.USER_REQUESTED,
                user_requested,
                "User requested human assistance",
            ),
            (
                EscalationTrigger.HIGH_RISK,
                high_risk,
                "Action flagged as high-risk",
            ),
            (
                EscalationTrigger.TIMEOUT,
                timeout,
                "Interaction timed out",
            ),
            (
                EscalationTrigger.REPEATED_FAILURE,
                (
                    failure_count > 0
                    and failure_count >= int(
                        self._configs.get(
                            EscalationTrigger.REPEATED_FAILURE,
                            EscalationTriggerConfig(EscalationTrigger.REPEATED_FAILURE),
                        ).threshold
                    )
                ),
                f"Repeated failure threshold reached ({failure_count} failures)",
            ),
        ]

        # LOW_CONFIDENCE check — must compare against per-trigger threshold
        if confidence_score is not None:
            cfg = self._configs.get(EscalationTrigger.LOW_CONFIDENCE)
            if cfg is not None and cfg.enabled:
                trigger_checks.append(
                    (
                        EscalationTrigger.LOW_CONFIDENCE,
                        confidence_score < cfg.threshold,
                        f"Confidence score {confidence_score:.2f} below threshold {cfg.threshold:.2f}",
                    )
                )

        for trigger, condition, default_reason in trigger_checks:
            if not condition:
                continue
            cfg = self._configs.get(trigger)
            if cfg is None or not cfg.enabled:
                continue
            target = cfg.target_level
            record = EscalationRecord(
                escalation_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                from_level=self._current_level,
                to_level=target,
                trigger=trigger,
                reason=reason or default_reason,
                metadata=dict(metadata or {}),
            )
            self._current_level = target
            self._history.append(record)
            return record

        return None

    def reset(self, level: EscalationLevel = EscalationLevel.AGENT) -> None:
        """Reset the protocol to a given level (default: AGENT).

        Parameters
        ----------
        level:
            The level to reset to.  Clears escalation history.
        """
        self._current_level = level
        self._history.clear()
