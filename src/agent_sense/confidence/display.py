"""Confidence display — format confidence information for UI rendering.

ConfidenceDisplay converts a ConfidenceLevel into human-readable text,
ANSI colour codes (for terminal output), or simple text prefix labels.
"""
from __future__ import annotations

from agent_sense.confidence.annotator import ConfidenceLevel


_LABEL_MAP: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.HIGH: "High confidence",
    ConfidenceLevel.MEDIUM: "Medium confidence",
    ConfidenceLevel.LOW: "Low confidence",
    ConfidenceLevel.UNKNOWN: "Confidence unknown",
}

_COLOUR_MAP: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.HIGH: "green",
    ConfidenceLevel.MEDIUM: "yellow",
    ConfidenceLevel.LOW: "red",
    ConfidenceLevel.UNKNOWN: "grey",
}

_PREFIX_MAP: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.HIGH: "[HIGH]",
    ConfidenceLevel.MEDIUM: "[MED]",
    ConfidenceLevel.LOW: "[LOW]",
    ConfidenceLevel.UNKNOWN: "[?]",
}


class ConfidenceDisplay:
    """Format confidence levels for display in different output contexts.

    Example
    -------
    >>> display = ConfidenceDisplay()
    >>> display.as_label(ConfidenceLevel.HIGH)
    'High confidence'
    >>> display.as_prefix(ConfidenceLevel.LOW)
    '[LOW]'
    """

    def as_label(self, level: ConfidenceLevel) -> str:
        """Return a human-readable label for the given confidence level.

        Parameters
        ----------
        level:
            The ConfidenceLevel to format.

        Returns
        -------
        str
            Descriptive label string.
        """
        return _LABEL_MAP.get(level, "Unknown")

    def as_colour(self, level: ConfidenceLevel) -> str:
        """Return a colour name associated with the confidence level.

        Colour names are compatible with Rich and similar terminal libraries.

        Parameters
        ----------
        level:
            The ConfidenceLevel to look up.

        Returns
        -------
        str
            A colour name string (e.g. ``"green"``, ``"yellow"``, ``"red"``).
        """
        return _COLOUR_MAP.get(level, "grey")

    def as_prefix(self, level: ConfidenceLevel) -> str:
        """Return a short bracketed prefix tag for the confidence level.

        Parameters
        ----------
        level:
            The ConfidenceLevel to format.

        Returns
        -------
        str
            A short tag such as ``"[HIGH]"`` or ``"[LOW]"``.
        """
        return _PREFIX_MAP.get(level, "[?]")

    def format_score(self, score: float) -> str:
        """Return a percentage string for a raw confidence score.

        Parameters
        ----------
        score:
            Raw confidence score in [0.0, 1.0].

        Returns
        -------
        str
            E.g. ``"92.0%"`` for a score of 0.92.
        """
        return f"{score * 100:.1f}%"
