"""Confidence signals — extract linguistic cues that indicate response certainty.

SignalExtractor analyses agent response text and identifies five signal
categories:

1. hedging_language     — words/phrases that soften or qualify a claim.
2. certainty_markers    — words/phrases expressing strong confidence.
3. source_citations     — references to external sources or data.
4. numerical_precision  — exact figures, percentages, or measurements.
5. self_correction      — phrases indicating the agent is revising its answer.

Each signal contributes a normalised score in [0.0, 1.0] and a list of the
matching spans found in the text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

_HEDGING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(might|may|could|possibly|perhaps|probably|presumably|seemingly)\b",
        r"\b(i think|i believe|i suspect|i guess|i imagine|it seems|it appears)\b",
        r"\b(roughly|approximately|around|about|sort of|kind of|more or less)\b",
        r"\b(not sure|uncertain|unclear|debatable|questionable|doubtful)\b",
        r"\b(tend to|often|sometimes|generally|usually|typically|in most cases)\b",
    ]
]

_CERTAINTY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(definitely|certainly|absolutely|undoubtedly|without doubt|clearly)\b",
        r"\b(is|are|was|were) (definitely|certainly|always|never|exactly)\b",
        r"\b(confirmed|proven|established|documented|verified|guaranteed)\b",
        r"\b(always|never|every time|invariably|without exception)\b",
        r"\b(the fact is|it is a fact|it is true that|it is known that)\b",
    ]
]

_SOURCE_CITATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(according to|as per|per|cited in|referenced in)\b",
        r"\b(source[s]?:|reference[s]?:|see also|cf\.|ibid\.)\b",
        r"https?://\S+",
        r"\b(study|research|paper|report|survey|data|statistics) (show[s]?|indicate[s]?|suggest[s]?|reveal[s]?)\b",
        r"\b(published in|reported by|based on data from|from the)\b",
    ]
]

_NUMERICAL_PRECISION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b\d+\.\d+\b",
        r"\b\d+%\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\$\d+(?:[,\d]*)?(?:\.\d+)?",
        r"\b\d+\s*(milliseconds?|ms|seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b",
        r"\b\d+\s*(kb|mb|gb|tb|kib|mib|gib)\b",
    ]
]

_SELF_CORRECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(actually|in fact|to be precise|more precisely|to clarify|let me correct)\b",
        r"\b(i was wrong|i made an error|i misspoke|i stand corrected)\b",
        r"\b(correction:|erratum:|update:|revised:)\b",
        r"\b(wait|hold on|scratch that|disregard that|ignore that)\b",
        r"\b(not \w+, but rather|instead of|rather than what i said)\b",
    ]
]


def _collect_matches(
    patterns: list[re.Pattern[str]], text: str
) -> tuple[float, list[str]]:
    """Run a list of patterns against text and return a (score, spans) pair.

    The score is the total match count normalised against the number of
    patterns, capped at 1.0.

    Parameters
    ----------
    patterns:
        Compiled regex patterns to search.
    text:
        Input text to search.

    Returns
    -------
    tuple[float, list[str]]
        (score in [0.0, 1.0], list of matched span strings)
    """
    spans: list[str] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            spans.append(match.group(0))
    score = min(len(spans) / max(len(patterns), 1), 1.0)
    return round(score, 4), spans


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfidenceSignal:
    """A single extracted confidence signal from agent response text.

    Attributes
    ----------
    signal_type:
        One of: ``hedging_language``, ``certainty_markers``,
        ``source_citations``, ``numerical_precision``, ``self_correction``.
    score:
        Normalised signal strength in [0.0, 1.0]. Higher = stronger signal.
    matches:
        The raw text spans that triggered this signal.
    """

    signal_type: str
    score: float
    matches: list[str] = field(default_factory=list)

    def is_present(self) -> bool:
        """Return True if at least one match was found."""
        return len(self.matches) > 0


@dataclass(frozen=True)
class ExtractedSignals:
    """Full set of signals extracted from a single piece of text.

    Attributes
    ----------
    hedging_language:
        Qualifiers and softeners that reduce apparent certainty.
    certainty_markers:
        Strong affirmations that express high confidence.
    source_citations:
        References to external sources or data.
    numerical_precision:
        Exact numbers, percentages, or measurements.
    self_correction:
        Phrases indicating the agent is revising a prior statement.
    composite_score:
        A single aggregate score in [0.0, 1.0] summarising overall certainty.
        Increases with certainty_markers and numerical_precision; decreases with
        hedging_language and self_correction. source_citations contribute
        positively.
    """

    hedging_language: ConfidenceSignal
    certainty_markers: ConfidenceSignal
    source_citations: ConfidenceSignal
    numerical_precision: ConfidenceSignal
    self_correction: ConfidenceSignal
    composite_score: float = 0.0

    def as_dict(self) -> dict[str, float]:
        """Return a mapping of signal_type -> score."""
        return {
            self.hedging_language.signal_type: self.hedging_language.score,
            self.certainty_markers.signal_type: self.certainty_markers.score,
            self.source_citations.signal_type: self.source_citations.score,
            self.numerical_precision.signal_type: self.numerical_precision.score,
            self.self_correction.signal_type: self.self_correction.score,
        }


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


class SignalExtractor:
    """Extract linguistic confidence signals from agent response text.

    Example
    -------
    >>> extractor = SignalExtractor()
    >>> signals = extractor.extract("The capital of France is definitely Paris.")
    >>> signals.certainty_markers.is_present()
    True
    """

    def extract(self, text: str) -> ExtractedSignals:
        """Extract all confidence signals from the given text.

        Parameters
        ----------
        text:
            The agent response text to analyse. May be any length.

        Returns
        -------
        ExtractedSignals
            All five signal categories plus a composite certainty score.
        """
        hedging_score, hedging_matches = _collect_matches(_HEDGING_PATTERNS, text)
        certainty_score, certainty_matches = _collect_matches(_CERTAINTY_PATTERNS, text)
        citation_score, citation_matches = _collect_matches(_SOURCE_CITATION_PATTERNS, text)
        precision_score, precision_matches = _collect_matches(
            _NUMERICAL_PRECISION_PATTERNS, text
        )
        correction_score, correction_matches = _collect_matches(
            _SELF_CORRECTION_PATTERNS, text
        )

        # Composite: certainty and citations push score up; hedging and
        # self-correction drag it down; numerical precision provides moderate lift.
        raw_composite = (
            0.40 * certainty_score
            + 0.20 * citation_score
            + 0.15 * precision_score
            - 0.35 * hedging_score
            - 0.25 * correction_score
            + 0.50  # baseline shift so neutral text lands near 0.5
        )
        composite = round(max(0.0, min(raw_composite, 1.0)), 4)

        return ExtractedSignals(
            hedging_language=ConfidenceSignal(
                signal_type="hedging_language",
                score=hedging_score,
                matches=hedging_matches,
            ),
            certainty_markers=ConfidenceSignal(
                signal_type="certainty_markers",
                score=certainty_score,
                matches=certainty_matches,
            ),
            source_citations=ConfidenceSignal(
                signal_type="source_citations",
                score=citation_score,
                matches=citation_matches,
            ),
            numerical_precision=ConfidenceSignal(
                signal_type="numerical_precision",
                score=precision_score,
                matches=precision_matches,
            ),
            self_correction=ConfidenceSignal(
                signal_type="self_correction",
                score=correction_score,
                matches=correction_matches,
            ),
            composite_score=composite,
        )

    def extract_score_only(self, text: str) -> float:
        """Return only the composite certainty score for a piece of text.

        Parameters
        ----------
        text:
            The agent response text.

        Returns
        -------
        float
            Composite score in [0.0, 1.0].
        """
        return self.extract(text).composite_score
