"""Confidence annotator — attach confidence levels to agent responses.

ConfidenceAnnotator maps a raw numeric confidence score (0.0–1.0) to a
ConfidenceLevel enum value and packages the result in an AnnotatedResponse.

Default thresholds (overridable via ConfidenceThresholds):
- HIGH    : score >= 0.85
- MEDIUM  : 0.60 <= score < 0.85
- LOW     : 0.30 <= score < 0.60
- UNKNOWN : score < 0.30
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_sense.confidence.thresholds import ConfidenceThresholds


class ConfidenceLevel(str, Enum):
    """Categorical confidence tier for an agent response."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnnotatedResponse:
    """An agent response paired with its confidence annotation.

    Attributes
    ----------
    content:
        The original response text.
    confidence_level:
        The categorical confidence tier.
    confidence_score:
        The raw numeric score (0.0–1.0) that produced the level.
    domain:
        Optional domain label (e.g. ``"medical"``, ``"legal"``).
    metadata:
        Arbitrary key/value metadata attached by the annotator caller.
    """

    content: str
    confidence_level: ConfidenceLevel
    confidence_score: float
    domain: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def is_high_confidence(self) -> bool:
        """Return True if level is HIGH."""
        return self.confidence_level == ConfidenceLevel.HIGH

    def needs_disclaimer(self) -> bool:
        """Return True if the response should carry a disclaimer."""
        return self.confidence_level in {ConfidenceLevel.LOW, ConfidenceLevel.UNKNOWN}


# Default threshold boundaries (upper-exclusive except HIGH).
_DEFAULT_HIGH_THRESHOLD: float = 0.85
_DEFAULT_MEDIUM_THRESHOLD: float = 0.60
_DEFAULT_LOW_THRESHOLD: float = 0.30


def _score_to_level(
    score: float,
    high: float,
    medium: float,
    low: float,
) -> ConfidenceLevel:
    if score >= high:
        return ConfidenceLevel.HIGH
    if score >= medium:
        return ConfidenceLevel.MEDIUM
    if score >= low:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNKNOWN


class ConfidenceAnnotator:
    """Annotate agent responses with a ConfidenceLevel.

    Parameters
    ----------
    thresholds:
        Optional :class:`~agent_sense.confidence.thresholds.ConfidenceThresholds`
        instance. If omitted, the module-level defaults are used.

    Example
    -------
    >>> annotator = ConfidenceAnnotator()
    >>> result = annotator.annotate("The capital is Paris.", score=0.92)
    >>> result.confidence_level
    <ConfidenceLevel.HIGH: 'high'>
    """

    def __init__(
        self,
        thresholds: "ConfidenceThresholds | None" = None,
    ) -> None:
        self._thresholds = thresholds

    def _resolve_bounds(
        self, domain: str
    ) -> tuple[float, float, float]:
        """Return (high, medium, low) threshold bounds for a domain."""
        if self._thresholds is not None:
            return self._thresholds.bounds_for(domain)
        return (
            _DEFAULT_HIGH_THRESHOLD,
            _DEFAULT_MEDIUM_THRESHOLD,
            _DEFAULT_LOW_THRESHOLD,
        )

    def annotate(
        self,
        content: str,
        score: float,
        domain: str = "",
        metadata: dict[str, str] | None = None,
    ) -> AnnotatedResponse:
        """Produce an AnnotatedResponse for the given content and score.

        Parameters
        ----------
        content:
            The agent response text.
        score:
            Numeric confidence score in [0.0, 1.0].
        domain:
            Optional domain label used to select domain-specific thresholds.
        metadata:
            Optional extra metadata to attach to the result.

        Returns
        -------
        AnnotatedResponse
            Response with level, raw score, and optional metadata.

        Raises
        ------
        ValueError
            If ``score`` is outside [0.0, 1.0].
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Confidence score must be in [0.0, 1.0]; got {score!r}."
            )
        high, medium, low = self._resolve_bounds(domain)
        level = _score_to_level(score, high, medium, low)
        return AnnotatedResponse(
            content=content,
            confidence_level=level,
            confidence_score=score,
            domain=domain,
            metadata=metadata or {},
        )

    def level_for_score(self, score: float, domain: str = "") -> ConfidenceLevel:
        """Return the ConfidenceLevel for a score without wrapping a response.

        Parameters
        ----------
        score:
            Numeric confidence score in [0.0, 1.0].
        domain:
            Optional domain label.

        Returns
        -------
        ConfidenceLevel
        """
        high, medium, low = self._resolve_bounds(domain)
        return _score_to_level(score, high, medium, low)
