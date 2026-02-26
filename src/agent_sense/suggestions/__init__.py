"""Suggestions subsystem — contextual follow-up recommendations.

Exports
-------
Suggestion
    Dataclass representing a single contextual suggestion.
SuggestionCategory
    Enum of suggestion types (CLARIFICATION, NEXT_STEP, RELATED_TOPIC, HELP).
SuggestionEngine
    Generate contextual suggestions from user text and history.
RankedSuggestion
    Suggestion paired with its computed ranking scores.
SuggestionRanker
    Re-rank suggestions by context match, recency, and diversity.
"""
from __future__ import annotations

from agent_sense.suggestions.engine import (
    Suggestion,
    SuggestionCategory,
    SuggestionEngine,
)
from agent_sense.suggestions.ranker import RankedSuggestion, SuggestionRanker

__all__ = [
    "Suggestion",
    "SuggestionCategory",
    "SuggestionEngine",
    "RankedSuggestion",
    "SuggestionRanker",
]
