"""Confidence-aware UI component for rendering agent confidence to users.

ConfidenceUIIndicator is a frozen dataclass that bundles:
- A categorical confidence level (high / medium / low)
- A raw numeric score
- Auto-escalation threshold: when the score drops below the threshold the
  indicator signals that the interaction should be escalated to a supervisor
  or human reviewer.
- Rendering metadata (colour, icon, label, ARIA role) consumed by UI layers.

This module deliberately avoids any rendering framework dependencies —
the rendering metadata is plain strings/dicts that the caller's UI layer
interprets according to its own conventions (HTML, Rich, JSON API, etc.).

Design notes
------------
ConfidenceLevel uses "high / medium / low" (three-tier) rather than the
five-tier scale in indicators.confidence so that the UI presenter has a
simpler mapping to CSS classes and icons.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


class ConfidenceLevel(str, Enum):
    """Three-tier UI confidence classification.

    HIGH   — agent is sufficiently certain; no additional UI warnings.
    MEDIUM — moderate uncertainty; show a soft advisory label.
    LOW    — significant uncertainty; trigger auto-escalation if enabled.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Score -> level mapping
# ---------------------------------------------------------------------------

# Lower bound of each tier (inclusive).
_LEVEL_THRESHOLDS: list[tuple[float, ConfidenceLevel]] = [
    (0.70, ConfidenceLevel.HIGH),
    (0.40, ConfidenceLevel.MEDIUM),
    (0.00, ConfidenceLevel.LOW),
]


def _score_to_level(score: float) -> ConfidenceLevel:
    """Map a numeric score in [0.0, 1.0] to a ConfidenceLevel.

    Parameters
    ----------
    score:
        Numeric confidence value.

    Returns
    -------
    ConfidenceLevel
        The corresponding three-tier level.
    """
    for threshold, level in _LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return ConfidenceLevel.LOW  # pragma: no cover


# ---------------------------------------------------------------------------
# Rendering metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderMetadata:
    """Visual and accessibility metadata for rendering a confidence indicator.

    Attributes
    ----------
    css_class:
        CSS class name (e.g. ``"confidence-high"``) for stylesheet targeting.
    hex_colour:
        Hex colour code for the indicator badge (e.g. ``"#27ae60"``).
    icon:
        Short icon name or unicode character (e.g. ``"check"``, ``"⚠"``)
        for icon-based UIs.
    label:
        Short human-readable label (e.g. ``"High Confidence"``).
    aria_label:
        Accessibility label for screen readers.
    show_score:
        Whether to display the numeric score alongside the level label.
    """

    css_class: str
    hex_colour: str
    icon: str
    label: str
    aria_label: str
    show_score: bool = False


# Pre-built render metadata for each level.
_RENDER_MAP: dict[ConfidenceLevel, RenderMetadata] = {
    ConfidenceLevel.HIGH: RenderMetadata(
        css_class="confidence-high",
        hex_colour="#27ae60",
        icon="check-circle",
        label="High Confidence",
        aria_label="Agent is highly confident in this response",
        show_score=False,
    ),
    ConfidenceLevel.MEDIUM: RenderMetadata(
        css_class="confidence-medium",
        hex_colour="#f39c12",
        icon="info-circle",
        label="Medium Confidence",
        aria_label="Agent has moderate confidence in this response",
        show_score=True,
    ),
    ConfidenceLevel.LOW: RenderMetadata(
        css_class="confidence-low",
        hex_colour="#e74c3c",
        icon="exclamation-triangle",
        label="Low Confidence",
        aria_label="Agent has low confidence; consider human review",
        show_score=True,
    ),
}


# ---------------------------------------------------------------------------
# Auto-escalation threshold
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EscalationThreshold:
    """Defines when the confidence indicator should trigger auto-escalation.

    Attributes
    ----------
    score_threshold:
        Numeric threshold in [0.0, 1.0].  When the confidence score is
        strictly below this value the indicator's ``needs_escalation``
        property returns True.
    enabled:
        Master switch — when False, escalation is never triggered regardless
        of the score.
    escalation_target:
        Identifier of the escalation target (e.g. ``"supervisor"``,
        ``"human-queue"``).  Informational only; the UI layer or escalation
        protocol interprets this string.
    """

    score_threshold: float = 0.40
    enabled: bool = True
    escalation_target: str = "supervisor"


# ---------------------------------------------------------------------------
# ConfidenceUIIndicator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfidenceUIIndicator:
    """Confidence-aware UI component metadata for an agent response.

    Consumers read this object to determine what to display in the UI.
    The object is intentionally framework-agnostic: it carries data, not
    render logic.

    Attributes
    ----------
    score:
        Raw numeric confidence score in [0.0, 1.0].
    level:
        Categorical three-tier level derived from ``score``.
    render:
        Visual and accessibility rendering metadata for this level.
    threshold:
        Auto-escalation threshold configuration.
    context_label:
        Optional free-text label describing the context in which this
        confidence was measured (e.g. the topic or query type).
    extra:
        Arbitrary key/value annotations for extended UI frameworks.
    """

    score: float
    level: ConfidenceLevel
    render: RenderMetadata
    threshold: EscalationThreshold = field(default_factory=EscalationThreshold)
    context_label: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def needs_escalation(self) -> bool:
        """Return True when the score falls below the escalation threshold.

        Returns
        -------
        bool
            True when auto-escalation should be triggered.
        """
        if not self.threshold.enabled:
            return False
        return self.score < self.threshold.score_threshold

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dict suitable for JSON encoding.

        Returns
        -------
        dict[str, object]
            All public fields as JSON-compatible Python primitives.
        """
        return {
            "score": self.score,
            "level": self.level.value,
            "render": {
                "css_class": self.render.css_class,
                "hex_colour": self.render.hex_colour,
                "icon": self.render.icon,
                "label": self.render.label,
                "aria_label": self.render.aria_label,
                "show_score": self.render.show_score,
            },
            "needs_escalation": self.needs_escalation,
            "escalation_target": self.threshold.escalation_target,
            "context_label": self.context_label,
            "extra": dict(self.extra),
        }


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


def build_ui_indicator(
    score: float,
    *,
    threshold: EscalationThreshold | None = None,
    context_label: str = "",
    extra: dict[str, str] | None = None,
) -> ConfidenceUIIndicator:
    """Construct a ConfidenceUIIndicator from a raw numeric score.

    Parameters
    ----------
    score:
        Numeric confidence value in [0.0, 1.0].
    threshold:
        Optional escalation threshold configuration.  Defaults to
        ``EscalationThreshold()`` with score_threshold=0.40.
    context_label:
        Optional text describing the context for this confidence measurement.
    extra:
        Optional extra annotations to attach to the indicator.

    Returns
    -------
    ConfidenceUIIndicator
        Fully populated indicator.

    Raises
    ------
    ValueError
        If ``score`` is outside [0.0, 1.0].
    """
    if not 0.0 <= score <= 1.0:
        raise ValueError(
            f"Confidence score must be in [0.0, 1.0]; got {score!r}."
        )
    level = _score_to_level(score)
    render = _RENDER_MAP[level]
    return ConfidenceUIIndicator(
        score=score,
        level=level,
        render=render,
        threshold=threshold if threshold is not None else EscalationThreshold(),
        context_label=context_label,
        extra=extra or {},
    )
