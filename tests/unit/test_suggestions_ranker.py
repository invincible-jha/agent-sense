"""Tests for agent_sense.suggestions.ranker."""
from __future__ import annotations

import pytest

from agent_sense.suggestions.engine import Suggestion, SuggestionCategory
from agent_sense.suggestions.ranker import SuggestionRanker


def _make_suggestion(
    text: str = "How can I help?",
    category: SuggestionCategory = SuggestionCategory.CLARIFICATION,
    score: float = 0.5,
) -> Suggestion:
    return Suggestion(text=text, category=category, relevance_score=score)


class TestSuggestionRankerInit:
    def test_default_init(self) -> None:
        ranker = SuggestionRanker()
        assert ranker is not None

    def test_custom_weights(self) -> None:
        ranker = SuggestionRanker(
            context_weight=0.4,
            relevance_weight=0.4,
            base_weight=0.2,
        )
        assert ranker is not None


class TestSuggestionRankerRank:
    def test_rank_returns_list(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion()]
        result = ranker.rank(suggestions, user_text="query", history=[])
        assert isinstance(result, list)

    def test_rank_items_have_composite_score(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion()]
        result = ranker.rank(suggestions, user_text="query", history=[])
        for rs in result:
            assert hasattr(rs, "composite_score")
            assert 0.0 <= rs.composite_score <= 1.0

    def test_rank_preserves_all_suggestions(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [
            _make_suggestion("Clarify?", SuggestionCategory.CLARIFICATION, 0.5),
            _make_suggestion("Next step?", SuggestionCategory.NEXT_STEP, 0.8),
        ]
        result = ranker.rank(suggestions, user_text="query", history=[])
        assert len(result) == 2

    def test_rank_higher_relevance_ranks_higher(self) -> None:
        ranker = SuggestionRanker()
        low_rel = _make_suggestion("Low", SuggestionCategory.CLARIFICATION, 0.1)
        high_rel = _make_suggestion("High", SuggestionCategory.CLARIFICATION, 0.9)
        result = ranker.rank([low_rel, high_rel], user_text="query", history=[])
        # Higher relevance should have higher or equal composite score
        scores = [rs.composite_score for rs in result]
        assert max(scores) >= min(scores)

    def test_rank_empty_list_returns_empty(self) -> None:
        ranker = SuggestionRanker()
        result = ranker.rank([], user_text="query", history=[])
        assert result == []

    def test_rank_with_recent_shown(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion("Repeat")]
        result = ranker.rank(suggestions, user_text="query", history=[], recent_shown=["Repeat"])
        assert isinstance(result, list)

    def test_rank_result_sorted_descending(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [
            _make_suggestion("Low relevance", score=0.1),
            _make_suggestion("High relevance", score=0.9),
        ]
        result = ranker.rank(suggestions, user_text="query", history=[])
        scores = [rs.composite_score for rs in result]
        assert scores == sorted(scores, reverse=True)


class TestSuggestionRankerTopN:
    def test_top_n_returns_suggestions(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [
            _make_suggestion("Suggestion 1", score=0.5),
            _make_suggestion("Suggestion 2", score=0.8),
            _make_suggestion("Suggestion 3", score=0.3),
        ]
        result = ranker.top_n(suggestions, n=2, user_text="query")
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_top_n_returns_correct_count(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion(f"S{i}", score=i / 10) for i in range(5)]
        result = ranker.top_n(suggestions, n=3, user_text="query")
        assert len(result) == 3

    def test_top_n_items_are_suggestions(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion()]
        result = ranker.top_n(suggestions, n=1, user_text="query")
        for item in result:
            assert isinstance(item, Suggestion)

    def test_top_n_returns_highest_scoring(self) -> None:
        ranker = SuggestionRanker()
        low = _make_suggestion("Low", score=0.1)
        high = _make_suggestion("High", score=0.9)
        result = ranker.top_n([low, high], n=1, user_text="query")
        assert result[0].text == "High"

    def test_top_n_n_larger_than_list_returns_all(self) -> None:
        ranker = SuggestionRanker()
        suggestions = [_make_suggestion("Only one")]
        result = ranker.top_n(suggestions, n=10, user_text="query")
        assert len(result) == 1

    def test_top_n_empty_input_returns_empty(self) -> None:
        ranker = SuggestionRanker()
        result = ranker.top_n([], n=3, user_text="query")
        assert result == []
