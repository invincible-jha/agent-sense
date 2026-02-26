"""Suggestion ranker — score and sort suggestions by multiple criteria.

SuggestionRanker re-orders a list of Suggestion objects produced by
SuggestionEngine using three weighted signals:

1. context_match  — how well the suggestion text overlaps with the current
                    context keywords (user text + recent history).
2. recency        — penalise suggestions whose text appeared in recent history,
                    rewarding freshness.
3. diversity      — de-duplicate suggestions from the same category to prevent
                    all top results being of one type.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from agent_sense.suggestions.engine import Suggestion, SuggestionCategory


@dataclass
class RankedSuggestion:
    """A suggestion paired with its computed composite rank score.

    Attributes
    ----------
    suggestion:
        The original Suggestion object.
    context_match_score:
        Overlap between suggestion text and context keywords (0.0–1.0).
    recency_penalty:
        Score deduction for recently-surfaced suggestions (0.0–0.5).
    diversity_penalty:
        Score deduction for category over-representation (0.0–0.3).
    composite_score:
        Final ranking score (higher = show first).
    """

    suggestion: Suggestion
    context_match_score: float
    recency_penalty: float
    diversity_penalty: float
    composite_score: float


# Weights for each ranking dimension.
_WEIGHT_CONTEXT: float = 0.50
_WEIGHT_RELEVANCE: float = 0.30
_WEIGHT_BASE: float = 0.20


def _extract_keywords(text: str) -> frozenset[str]:
    """Return a set of lower-cased words from text."""
    return frozenset(re.findall(r"[a-z]+", text.lower()))


def _context_match(suggestion_text: str, context_keywords: frozenset[str]) -> float:
    """Return the fraction of suggestion words that appear in context keywords."""
    suggestion_words = _extract_keywords(suggestion_text)
    if not suggestion_words:
        return 0.0
    overlap = len(suggestion_words & context_keywords)
    return round(min(overlap / len(suggestion_words), 1.0), 4)


def _recency_penalty(suggestion_text: str, recent_shown: list[str]) -> float:
    """Return a penalty in [0.0, 0.5] if the suggestion appeared recently."""
    suggestion_lower = suggestion_text.lower()
    for prior in recent_shown:
        if suggestion_lower in prior.lower() or prior.lower() in suggestion_lower:
            return 0.5
    return 0.0


class SuggestionRanker:
    """Re-rank suggestions using context, recency, and diversity signals.

    Parameters
    ----------
    context_weight:
        Weight applied to the context_match signal (default 0.50).
    relevance_weight:
        Weight applied to the suggestion's original relevance_score (default 0.30).
    base_weight:
        Weight applied to a fixed base score of 1.0 (ensures non-zero ranking;
        default 0.20).
    max_per_category:
        Maximum number of suggestions from the same category in the ranked
        output. Surplus suggestions are pushed to the bottom. Defaults to 2.

    Example
    -------
    >>> from agent_sense.suggestions.engine import SuggestionEngine
    >>> engine = SuggestionEngine()
    >>> suggestions = engine.suggest("I cannot access my account")
    >>> ranker = SuggestionRanker()
    >>> ranked = ranker.rank(suggestions, user_text="I cannot access my account")
    >>> ranked[0].composite_score >= 0.0
    True
    """

    def __init__(
        self,
        context_weight: float = _WEIGHT_CONTEXT,
        relevance_weight: float = _WEIGHT_RELEVANCE,
        base_weight: float = _WEIGHT_BASE,
        max_per_category: int = 2,
    ) -> None:
        self._context_weight = context_weight
        self._relevance_weight = relevance_weight
        self._base_weight = base_weight
        self._max_per_category = max(1, max_per_category)

    def rank(
        self,
        suggestions: list[Suggestion],
        user_text: str = "",
        history: list[str] | None = None,
        recent_shown: list[str] | None = None,
    ) -> list[RankedSuggestion]:
        """Rank suggestions by context match, recency, and diversity.

        Parameters
        ----------
        suggestions:
            The candidate suggestions to rank.
        user_text:
            Current user message. Keywords are extracted for context matching.
        history:
            Prior user messages. Combined with user_text for context keywords.
        recent_shown:
            Suggestion texts that have already been shown to the user in recent
            turns. Used to compute recency penalty.

        Returns
        -------
        list[RankedSuggestion]
            All suggestions wrapped in RankedSuggestion, sorted by
            ``composite_score`` descending.
        """
        context_text = user_text + " ".join(history or [])
        context_keywords = _extract_keywords(context_text)
        shown = recent_shown or []

        # Compute raw scores.
        ranked: list[RankedSuggestion] = []
        for suggestion in suggestions:
            ctx_score = _context_match(suggestion.text, context_keywords)
            rec_penalty = _recency_penalty(suggestion.text, shown)
            raw = (
                self._context_weight * ctx_score
                + self._relevance_weight * suggestion.relevance_score
                + self._base_weight * 1.0
                - rec_penalty
            )
            composite = round(max(0.0, min(raw, 1.0)), 4)
            ranked.append(
                RankedSuggestion(
                    suggestion=suggestion,
                    context_match_score=ctx_score,
                    recency_penalty=rec_penalty,
                    diversity_penalty=0.0,  # updated below
                    composite_score=composite,
                )
            )

        # Sort by composite score descending.
        ranked.sort(key=lambda r: r.composite_score, reverse=True)

        # Apply diversity penalty: track category counts as we iterate.
        category_counts: Counter[SuggestionCategory] = Counter()
        diversified: list[RankedSuggestion] = []
        overflow: list[RankedSuggestion] = []

        for ranked_item in ranked:
            cat = ranked_item.suggestion.category
            if category_counts[cat] < self._max_per_category:
                category_counts[cat] += 1
                diversified.append(ranked_item)
            else:
                # Apply diversity penalty and push to overflow.
                diversity_pen = 0.3
                new_score = round(
                    max(0.0, ranked_item.composite_score - diversity_pen), 4
                )
                overflow.append(
                    RankedSuggestion(
                        suggestion=ranked_item.suggestion,
                        context_match_score=ranked_item.context_match_score,
                        recency_penalty=ranked_item.recency_penalty,
                        diversity_penalty=diversity_pen,
                        composite_score=new_score,
                    )
                )

        overflow.sort(key=lambda r: r.composite_score, reverse=True)
        return diversified + overflow

    def top_n(
        self,
        suggestions: list[Suggestion],
        n: int,
        user_text: str = "",
        history: list[str] | None = None,
        recent_shown: list[str] | None = None,
    ) -> list[Suggestion]:
        """Return the top-n ranked Suggestion objects.

        Parameters
        ----------
        suggestions:
            Candidate suggestions.
        n:
            Number of suggestions to return.
        user_text:
            Current user message for context matching.
        history:
            Prior user messages.
        recent_shown:
            Previously-shown suggestion texts.

        Returns
        -------
        list[Suggestion]
            Top-n Suggestion objects in rank order.
        """
        ranked = self.rank(
            suggestions,
            user_text=user_text,
            history=history,
            recent_shown=recent_shown,
        )
        return [r.suggestion for r in ranked[:n]]
