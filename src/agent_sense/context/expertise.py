"""Expertise estimator — infer user expertise from vocabulary and question structure.

The ExpertiseEstimator uses heuristic analysis of user-supplied text to produce
an ExpertiseLevel. It examines:

- Vocabulary complexity (average word length, rare / domain words).
- Question structure (direct vs. explanatory questions).
- Domain terminology usage from a configurable term list.
"""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class ExpertiseLevel(str, Enum):
    """Ordered expertise tiers, from novice to expert."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# Default domain-agnostic technical terms that signal expertise.
_DEFAULT_TECHNICAL_TERMS: frozenset[str] = frozenset(
    {
        "api",
        "sdk",
        "llm",
        "inference",
        "latency",
        "throughput",
        "token",
        "embedding",
        "vector",
        "pipeline",
        "orchestration",
        "middleware",
        "webhook",
        "oauth",
        "jwt",
        "grpc",
        "protobuf",
        "schema",
        "idempotent",
        "pagination",
        "rate limit",
        "backpressure",
        "concurrency",
        "async",
        "coroutine",
        "serialization",
        "deserialization",
        "namespace",
        "polymorphism",
        "dependency injection",
        "memoization",
        "heuristic",
        "gradient",
        "hyperparameter",
        "fine-tuning",
        "rag",
        "retrieval augmented",
        "context window",
        "temperature",
        "top-p",
        "beam search",
        "transformer",
        "attention",
        "multimodal",
    }
)

# Simple / explanatory question markers suggest a lower expertise level.
_NOVICE_QUESTION_MARKERS: re.Pattern[str] = re.compile(
    r"(?i)\b(what is|what are|how do i|how to|can you explain|i don'?t understand"
    r"|what does .+ mean|please help me understand|is it possible to)\b"
)

# Expert-level question structure: precise, conditional, uses technical framing.
_EXPERT_QUESTION_MARKERS: re.Pattern[str] = re.compile(
    r"(?i)\b(given that|assuming|when .+ fails|edge case|corner case"
    r"|complexity|tradeoff|trade-off|compared to|versus|under what conditions"
    r"|empirically|theoretically|formally|precisely)\b"
)


class ExpertiseEstimate(BaseModel):
    """Result of ExpertiseEstimator.estimate()."""

    level: ExpertiseLevel
    confidence: float = Field(ge=0.0, le=1.0)
    signals: dict[str, float] = Field(default_factory=dict)
    """Named scoring signals that contributed to the final level."""


def _average_word_length(words: list[str]) -> float:
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def _technical_term_density(text_lower: str, terms: frozenset[str]) -> float:
    """Return fraction of terms found in text (capped at 1.0)."""
    if not terms:
        return 0.0
    hits = sum(1 for term in terms if term in text_lower)
    return min(hits / len(terms), 1.0)


def _sentence_length_score(text: str) -> float:
    """Longer average sentences often correlate with more nuanced expression."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0
    avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
    # Normalise: <5 words → 0.0; >=20 words → 1.0
    return min(max((avg_length - 5) / 15, 0.0), 1.0)


class ExpertiseEstimator:
    """Infer user expertise level from vocabulary, question structure, and domain terms.

    Parameters
    ----------
    domain_terms:
        Extra domain-specific technical terms to look for. These are merged with
        the built-in default term set.

    Example
    -------
    >>> estimator = ExpertiseEstimator()
    >>> result = estimator.estimate("What is an API?")
    >>> result.level
    <ExpertiseLevel.NOVICE: 'novice'>
    """

    def __init__(self, domain_terms: frozenset[str] | None = None) -> None:
        extra = domain_terms or frozenset()
        self._terms = _DEFAULT_TECHNICAL_TERMS | {t.lower() for t in extra}

    def estimate(self, text: str) -> ExpertiseEstimate:
        """Estimate expertise from the supplied text.

        Parameters
        ----------
        text:
            Raw user input (question, message, or conversation excerpt).

        Returns
        -------
        ExpertiseEstimate
            Level, confidence, and named scoring signals.
        """
        if not text.strip():
            return ExpertiseEstimate(
                level=ExpertiseLevel.NOVICE,
                confidence=0.0,
                signals={"empty_input": 1.0},
            )

        text_lower = text.lower()
        words = re.findall(r"[a-z']+", text_lower)

        avg_word_len = _average_word_length(words)
        # Normalise word length: <4 → 0.0, >=8 → 1.0
        word_len_score = min(max((avg_word_len - 4) / 4, 0.0), 1.0)

        term_density = _technical_term_density(text_lower, self._terms)
        sentence_score = _sentence_length_score(text)

        novice_markers = len(_NOVICE_QUESTION_MARKERS.findall(text))
        expert_markers = len(_EXPERT_QUESTION_MARKERS.findall(text))
        # Normalise marker counts to [0, 1]
        novice_signal = min(novice_markers * 0.3, 1.0)
        expert_signal = min(expert_markers * 0.3, 1.0)

        # Weighted composite score in [0, 1] — higher = more expert
        composite = (
            0.20 * word_len_score
            + 0.35 * term_density
            + 0.15 * sentence_score
            + 0.30 * expert_signal
            - 0.30 * novice_signal
        )
        # Clamp to [0, 1]
        composite = max(0.0, min(composite, 1.0))

        if composite >= 0.70:
            level = ExpertiseLevel.EXPERT
        elif composite >= 0.45:
            level = ExpertiseLevel.ADVANCED
        elif composite >= 0.20:
            level = ExpertiseLevel.INTERMEDIATE
        else:
            level = ExpertiseLevel.NOVICE

        # Confidence is proportional to signal count: more text = more confident.
        word_count_confidence = min(len(words) / 30, 1.0)

        return ExpertiseEstimate(
            level=level,
            confidence=round(word_count_confidence, 3),
            signals={
                "word_length": round(word_len_score, 3),
                "term_density": round(term_density, 3),
                "sentence_score": round(sentence_score, 3),
                "expert_markers": round(expert_signal, 3),
                "novice_markers": round(novice_signal, 3),
                "composite": round(composite, 3),
            },
        )

    def estimate_from_history(self, messages: list[str]) -> ExpertiseEstimate:
        """Estimate expertise from a list of prior user messages.

        Parameters
        ----------
        messages:
            Ordered list of user-turn text strings.

        Returns
        -------
        ExpertiseEstimate
            Aggregated estimate across all messages.
        """
        if not messages:
            return ExpertiseEstimate(level=ExpertiseLevel.NOVICE, confidence=0.0)
        combined = " ".join(messages)
        return self.estimate(combined)
