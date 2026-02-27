"""Tests for agent_sense.components.confidence_scorer — ConfidenceScorer."""
from __future__ import annotations

import pytest

from agent_sense.components.confidence_scorer import (
    ConfidenceScorer,
    ScorerMetadata,
    ScoringWeights,
)


# ---------------------------------------------------------------------------
# ScorerMetadata
# ---------------------------------------------------------------------------


class TestScorerMetadata:
    def test_defaults(self) -> None:
        meta = ScorerMetadata()
        assert meta.model_temperature is None
        assert meta.retrieval_score is None
        assert meta.tool_success_count == 0
        assert meta.tool_total_count == 0
        assert meta.knowledge_freshness is None
        assert meta.extra == {}

    def test_from_dict_all_fields(self) -> None:
        data = {
            "model_temperature": 0.2,
            "retrieval_score": 0.85,
            "tool_success_count": 3,
            "tool_total_count": 4,
            "knowledge_freshness": 0.9,
            "extra_field": "value",
        }
        meta = ScorerMetadata.from_dict(data)
        assert meta.model_temperature == pytest.approx(0.2)
        assert meta.retrieval_score == pytest.approx(0.85)
        assert meta.tool_success_count == 3
        assert meta.tool_total_count == 4
        assert meta.knowledge_freshness == pytest.approx(0.9)
        assert meta.extra["extra_field"] == "value"

    def test_from_dict_missing_fields(self) -> None:
        meta = ScorerMetadata.from_dict({"retrieval_score": 0.5})
        assert meta.retrieval_score == pytest.approx(0.5)
        assert meta.model_temperature is None
        assert meta.tool_total_count == 0

    def test_from_dict_empty(self) -> None:
        meta = ScorerMetadata.from_dict({})
        assert meta.model_temperature is None
        assert meta.tool_total_count == 0

    def test_from_dict_int_counts(self) -> None:
        meta = ScorerMetadata.from_dict({"tool_success_count": 5, "tool_total_count": 5})
        assert meta.tool_success_count == 5
        assert meta.tool_total_count == 5

    def test_frozen(self) -> None:
        meta = ScorerMetadata()
        with pytest.raises((TypeError, AttributeError)):
            meta.model_temperature = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ScoringWeights
# ---------------------------------------------------------------------------


class TestScoringWeights:
    def test_defaults(self) -> None:
        w = ScoringWeights()
        assert w.temperature == pytest.approx(0.25)
        assert w.retrieval == pytest.approx(0.35)
        assert w.tool_success == pytest.approx(0.25)
        assert w.freshness == pytest.approx(0.15)

    def test_frozen(self) -> None:
        w = ScoringWeights()
        with pytest.raises((TypeError, AttributeError)):
            w.temperature = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ConfidenceScorer
# ---------------------------------------------------------------------------


class TestConfidenceScorerEmptyMetadata:
    def test_empty_returns_midpoint(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({})
        assert result == pytest.approx(0.5)

    def test_none_factors_excluded(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"model_temperature": None})
        assert result == pytest.approx(0.5)


class TestConfidenceScorerTemperature:
    def test_low_temperature_high_confidence(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"model_temperature": 0.0})
        assert result == pytest.approx(1.0, abs=0.01)

    def test_high_temperature_low_confidence(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"model_temperature": 2.0})
        assert result == pytest.approx(0.0, abs=0.01)

    def test_medium_temperature(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"model_temperature": 1.0})
        # temperature=1.0 → contribution=0.5 → weighted score=0.5
        assert 0.45 <= result <= 0.55


class TestConfidenceScorerRetrieval:
    def test_perfect_retrieval(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"retrieval_score": 1.0})
        assert result == pytest.approx(1.0, abs=0.01)

    def test_zero_retrieval(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"retrieval_score": 0.0})
        assert result == pytest.approx(0.0, abs=0.01)

    def test_mid_retrieval(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"retrieval_score": 0.5})
        assert result == pytest.approx(0.5, abs=0.01)


class TestConfidenceScorerToolSuccess:
    def test_all_tools_succeeded(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"tool_success_count": 5, "tool_total_count": 5})
        assert result == pytest.approx(1.0, abs=0.01)

    def test_no_tools_succeeded(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"tool_success_count": 0, "tool_total_count": 3})
        assert result == pytest.approx(0.0, abs=0.01)

    def test_partial_tool_success(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"tool_success_count": 2, "tool_total_count": 4})
        assert result == pytest.approx(0.5, abs=0.01)

    def test_zero_total_excludes_factor(self) -> None:
        scorer = ConfidenceScorer()
        # tool_total_count=0 should be same as empty metadata (neutral)
        result_with = scorer.score({"tool_success_count": 0, "tool_total_count": 0})
        result_empty = scorer.score({})
        assert result_with == result_empty


class TestConfidenceScorerFreshness:
    def test_fresh_knowledge(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"knowledge_freshness": 1.0})
        assert result == pytest.approx(1.0, abs=0.01)

    def test_stale_knowledge(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score({"knowledge_freshness": 0.0})
        assert result == pytest.approx(0.0, abs=0.01)


class TestConfidenceScorerComposite:
    def test_high_all_factors(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score(
            {
                "model_temperature": 0.1,
                "retrieval_score": 0.95,
                "tool_success_count": 4,
                "tool_total_count": 4,
                "knowledge_freshness": 0.98,
            }
        )
        assert result >= 0.85

    def test_low_all_factors(self) -> None:
        scorer = ConfidenceScorer()
        result = scorer.score(
            {
                "model_temperature": 1.8,
                "retrieval_score": 0.05,
                "tool_success_count": 0,
                "tool_total_count": 5,
                "knowledge_freshness": 0.02,
            }
        )
        assert result <= 0.20

    def test_result_clamped_to_unit_range(self) -> None:
        scorer = ConfidenceScorer()
        # Extreme but valid inputs — result must stay in [0.0, 1.0]
        for score_val in [
            scorer.score({"model_temperature": 0.0, "retrieval_score": 1.0}),
            scorer.score({"model_temperature": 2.0, "retrieval_score": 0.0}),
            scorer.score({}),
        ]:
            assert 0.0 <= score_val <= 1.0


class TestConfidenceScorerFactorContributions:
    def test_all_factors_present(self) -> None:
        scorer = ConfidenceScorer()
        contribs = scorer.factor_contributions(
            {
                "model_temperature": 0.5,
                "retrieval_score": 0.7,
                "tool_success_count": 3,
                "tool_total_count": 4,
                "knowledge_freshness": 0.8,
            }
        )
        assert "temperature" in contribs
        assert "retrieval" in contribs
        assert "tool_success" in contribs
        assert "freshness" in contribs
        for contrib in contribs.values():
            assert 0.0 <= contrib <= 1.0

    def test_missing_factors_omitted(self) -> None:
        scorer = ConfidenceScorer()
        contribs = scorer.factor_contributions({"retrieval_score": 0.8})
        assert "retrieval" in contribs
        assert "temperature" not in contribs
        assert "tool_success" not in contribs
        assert "freshness" not in contribs

    def test_temperature_contribution_formula(self) -> None:
        scorer = ConfidenceScorer()
        contribs = scorer.factor_contributions({"model_temperature": 0.4})
        expected = 1.0 - 0.4 / 2.0
        assert contribs["temperature"] == pytest.approx(expected, abs=0.001)


class TestConfidenceScorerFromMetadataObject:
    def test_score_from_metadata(self) -> None:
        scorer = ConfidenceScorer()
        meta = ScorerMetadata(model_temperature=0.3, retrieval_score=0.8)
        result = scorer.score_from_metadata(meta)
        assert 0.0 <= result <= 1.0

    def test_score_matches_dict_input(self) -> None:
        scorer = ConfidenceScorer()
        meta = ScorerMetadata(
            model_temperature=0.5,
            retrieval_score=0.6,
            tool_success_count=2,
            tool_total_count=3,
        )
        dict_result = scorer.score(
            {
                "model_temperature": 0.5,
                "retrieval_score": 0.6,
                "tool_success_count": 2,
                "tool_total_count": 3,
            }
        )
        meta_result = scorer.score_from_metadata(meta)
        assert meta_result == pytest.approx(dict_result, abs=0.001)


class TestConfidenceScorerCustomWeights:
    def test_retrieval_only_weight(self) -> None:
        # Give 100% weight to retrieval
        weights = ScoringWeights(temperature=0.0, retrieval=1.0, tool_success=0.0, freshness=0.0)
        scorer = ConfidenceScorer(weights=weights)
        result = scorer.score(
            {"model_temperature": 0.0, "retrieval_score": 0.6, "knowledge_freshness": 1.0}
        )
        # Only retrieval contributes → result should be close to 0.6
        assert result == pytest.approx(0.6, abs=0.05)
