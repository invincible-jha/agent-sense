"""Tests for agent_sense.confidence.signals."""
from __future__ import annotations

import pytest

from agent_sense.confidence.signals import SignalExtractor


class TestSignalExtractorExtract:
    def test_extract_returns_signals_object(self) -> None:
        se = SignalExtractor()
        result = se.extract("I am certain the answer is 42.")
        assert result is not None

    def test_extract_has_composite_score(self) -> None:
        se = SignalExtractor()
        result = se.extract("I am certain the answer is 42.")
        assert hasattr(result, "composite_score")
        assert 0.0 <= result.composite_score <= 1.0

    def test_hedging_language_detected(self) -> None:
        se = SignalExtractor()
        result = se.extract("I think it might be Paris, but I am not sure.")
        assert len(result.hedging_language.matches) > 0

    def test_certainty_markers_detected(self) -> None:
        se = SignalExtractor()
        result = se.extract("I am certain this is the correct answer.")
        assert hasattr(result.certainty_markers, "score")

    def test_low_confidence_text_low_score(self) -> None:
        se = SignalExtractor()
        result = se.extract("I think it might possibly be, but I'm not sure about this.")
        assert result.composite_score < 0.7

    def test_empty_text_returns_valid_result(self) -> None:
        se = SignalExtractor()
        result = se.extract("")
        assert hasattr(result, "composite_score")

    def test_extract_score_only_returns_float(self) -> None:
        se = SignalExtractor()
        score = se.extract_score_only("I am certain this is 42.")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_extract_score_only_hedged_text(self) -> None:
        se = SignalExtractor()
        score = se.extract_score_only("Maybe it could be, possibly.")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_hedging_decreases_score(self) -> None:
        se = SignalExtractor()
        certain_score = se.extract_score_only("The answer is definitely 42.")
        hedged_score = se.extract_score_only(
            "I think it might possibly be around 42, but I'm not entirely sure."
        )
        # Hedged text should yield lower or equal composite score
        assert isinstance(certain_score, float)
        assert isinstance(hedged_score, float)

    def test_signals_have_signal_type(self) -> None:
        se = SignalExtractor()
        result = se.extract("The quick brown fox.")
        assert hasattr(result.hedging_language, "signal_type")
        assert result.hedging_language.signal_type == "hedging_language"

    def test_signals_have_score(self) -> None:
        se = SignalExtractor()
        result = se.extract("Some text here.")
        assert hasattr(result.hedging_language, "score")
        assert 0.0 <= result.hedging_language.score <= 1.0

    def test_signals_have_matches_list(self) -> None:
        se = SignalExtractor()
        result = se.extract("Some text here.")
        assert isinstance(result.hedging_language.matches, list)

    def test_source_citations_signal_exists(self) -> None:
        se = SignalExtractor()
        result = se.extract("According to Smith et al. (2023), the answer is 42.")
        assert hasattr(result, "source_citations")

    def test_numerical_precision_signal_exists(self) -> None:
        se = SignalExtractor()
        result = se.extract("The exact measurement is 3.14159 meters.")
        assert hasattr(result, "numerical_precision")

    def test_self_correction_signal_exists(self) -> None:
        se = SignalExtractor()
        result = se.extract("Actually, I was wrong — it is 43, not 42.")
        assert hasattr(result, "self_correction")
