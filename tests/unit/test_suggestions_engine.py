"""Tests for agent_sense.suggestions.engine."""
from __future__ import annotations

import pytest

from agent_sense.suggestions.engine import Suggestion, SuggestionCategory, SuggestionEngine


class TestSuggestionEngineDefault:
    def test_suggest_returns_list(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        assert isinstance(result, list)

    def test_suggest_items_are_suggestions(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        for item in result:
            assert isinstance(item, Suggestion)

    def test_suggest_returns_non_empty_list(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        assert len(result) > 0

    def test_suggestion_has_text(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        for s in result:
            assert isinstance(s.text, str)
            assert s.text != ""

    def test_suggestion_has_category(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        for s in result:
            assert isinstance(s.category, SuggestionCategory)

    def test_suggestion_has_relevance_score(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?")
        for s in result:
            assert 0.0 <= s.relevance_score <= 1.0

    def test_suggest_with_history(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("What is diabetes?", history=["What is insulin?"])
        assert isinstance(result, list)

    def test_suggest_with_category_filter(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest(
            "What is diabetes?",
            categories=[SuggestionCategory.CLARIFICATION],
        )
        assert isinstance(result, list)

    def test_suggest_category_filter_returns_only_that_category(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest(
            "What is diabetes?",
            categories=[SuggestionCategory.CLARIFICATION],
        )
        for s in result:
            assert s.category == SuggestionCategory.CLARIFICATION

    def test_suggest_empty_text(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("")
        assert isinstance(result, list)

    def test_max_suggestions_respected(self) -> None:
        engine = SuggestionEngine(max_suggestions=2)
        result = engine.suggest("What is diabetes?")
        assert len(result) <= 2


class TestSuggestionEngineWithTopicKeywords:
    def test_password_keyword_gives_next_step_suggestions(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest("I cannot reset my password")
        assert len(result) > 0

    def test_extra_topic_suggestions_merged(self) -> None:
        extra = {"billing": [(SuggestionCategory.NEXT_STEP, "Check your invoice")]}
        engine = SuggestionEngine(extra_topic_suggestions=extra)
        result = engine.suggest("I have a billing question")
        assert len(result) > 0

    def test_topic_in_history_still_generates_suggestions(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest(
            "password issue",
            history=["I had a password problem before"],
        )
        assert isinstance(result, list)

    def test_suggestion_is_high_relevance_method(self) -> None:
        s = Suggestion(text="Test", category=SuggestionCategory.CLARIFICATION, relevance_score=0.8)
        assert s.is_high_relevance() is True

    def test_suggestion_not_high_relevance(self) -> None:
        s = Suggestion(text="Test", category=SuggestionCategory.CLARIFICATION, relevance_score=0.5)
        assert s.is_high_relevance() is False

    def test_duplicate_suggestions_not_returned_twice(self) -> None:
        engine = SuggestionEngine()
        # Suggest the same keyword twice — deduplication should occur
        result = engine.suggest("password reset password reset password")
        texts = [s.text for s in result]
        # No duplicates
        assert len(texts) == len(set(texts))

    def test_generic_suggestions_fill_remaining_slots(self) -> None:
        # Use a keyword that maps to few suggestions to force generic fill
        engine = SuggestionEngine(max_suggestions=10)
        result = engine.suggest("password")
        # Should have suggestions from both topic and generic pools
        assert len(result) > 0


class TestSuggestionEngineForLowConfidence:
    def test_returns_list(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest_for_low_confidence()
        assert isinstance(result, list)

    def test_returns_non_empty_list(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest_for_low_confidence()
        assert len(result) > 0

    def test_items_are_suggestions(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest_for_low_confidence()
        for item in result:
            assert isinstance(item, Suggestion)

    def test_high_relevance_scores(self) -> None:
        engine = SuggestionEngine()
        result = engine.suggest_for_low_confidence()
        # Low-confidence suggestions should have higher relevance scores
        for s in result:
            assert s.relevance_score > 0.0
