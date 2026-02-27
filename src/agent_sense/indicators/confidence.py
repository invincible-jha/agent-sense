"""Universal AI transparency — confidence indicator.

ConfidenceIndicator represents a structured, self-describing confidence
measurement with a five-tier level, a raw score, human-readable reasoning,
and a factor breakdown.

Levels map to score ranges (inclusive lower bound, exclusive upper bound,
except VERY_HIGH which extends to 1.0):

    VERY_LOW  : [0.00, 0.20)
    LOW       : [0.20, 0.40)
    MEDIUM    : [0.40, 0.60)
    HIGH      : [0.60, 0.80)
    VERY_HIGH : [0.80, 1.00]

Example
-------
>>> indicator = from_score(0.85, reasoning="Strong keyword match", factors={"keyword": 0.9})
>>> indicator.level
<ConfidenceLevel.VERY_HIGH: 'very_high'>
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Five-tier categorical confidence classification.

    Each member maps to a score band of 20 percentage points.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Score thresholds — lower bound of each tier (inclusive).
_TIER_BOUNDS: list[tuple[float, ConfidenceLevel]] = [
    (0.80, ConfidenceLevel.VERY_HIGH),
    (0.60, ConfidenceLevel.HIGH),
    (0.40, ConfidenceLevel.MEDIUM),
    (0.20, ConfidenceLevel.LOW),
    (0.00, ConfidenceLevel.VERY_LOW),
]


def _level_for_score(score: float) -> ConfidenceLevel:
    """Map a numeric score in [0.0, 1.0] to a ConfidenceLevel.

    Parameters
    ----------
    score:
        Numeric confidence score. Must be within [0.0, 1.0].

    Returns
    -------
    ConfidenceLevel
        The corresponding tier.
    """
    for threshold, level in _TIER_BOUNDS:
        if score >= threshold:
            return level
    return ConfidenceLevel.VERY_LOW  # pragma: no cover — unreachable for valid scores


@dataclass(frozen=True)
class ConfidenceIndicator:
    """Structured confidence measurement for an AI agent response.

    Attributes
    ----------
    score:
        Raw numeric confidence in [0.0, 1.0].
    level:
        Categorical tier derived from ``score``.
    reasoning:
        Human-readable explanation of the confidence assessment.
    factors:
        Mapping of contributing factor names to their individual scores.
        Each value should be in [0.0, 1.0].
    """

    score: float
    level: ConfidenceLevel
    reasoning: str
    factors: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary suitable for JSON encoding.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "score": self.score,
            "level": self.level.value,
            "reasoning": self.reasoning,
            "factors": dict(self.factors),
        }


def from_score(
    score: float,
    reasoning: str,
    factors: dict[str, float] | None = None,
) -> ConfidenceIndicator:
    """Create a ConfidenceIndicator from a raw numeric score.

    The ``level`` field is computed automatically from ``score``.

    Parameters
    ----------
    score:
        Numeric confidence value in [0.0, 1.0].
    reasoning:
        Human-readable explanation of why this score was assigned.
    factors:
        Optional breakdown of contributing factors.  Each value should
        be in [0.0, 1.0].  Defaults to an empty dict if omitted.

    Returns
    -------
    ConfidenceIndicator
        Frozen indicator with auto-computed level.

    Raises
    ------
    ValueError
        If ``score`` is outside [0.0, 1.0].
    """
    if not 0.0 <= score <= 1.0:
        raise ValueError(
            f"Confidence score must be in [0.0, 1.0]; got {score!r}."
        )
    return ConfidenceIndicator(
        score=score,
        level=_level_for_score(score),
        reasoning=reasoning,
        factors=dict(factors) if factors is not None else {},
    )
