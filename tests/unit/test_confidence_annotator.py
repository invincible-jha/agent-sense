"""Unit tests for agent_sense.confidence.annotator."""
from __future__ import annotations

import pytest

from agent_sense.confidence.annotator import (
    AnnotatedResponse,
    ConfidenceAnnotator,
    ConfidenceLevel,
    _score_to_level,
)
from agent_sense.confidence.thresholds import ConfidenceThresholds


# ---------------------------------------------------------------------------
# ConfidenceLevel enum
# ---------------------------------------------------------------------------


class TestConfidenceLevelEnum:
    def test_high_value(self) -> None:
        assert ConfidenceLevel.HIGH.value == "high"

    def test_medium_value(self) -> None:
        assert ConfidenceLevel.MEDIUM.value == "medium"

    def test_low_value(self) -> None:
        assert ConfidenceLevel.LOW.value == "low"

    def test_unknown_value(self) -> None:
        assert ConfidenceLevel.UNKNOWN.value == "unknown"

    def test_all_four_members_exist(self) -> None:
        members = {level.value for level in ConfidenceLevel}
        assert members == {"high", "medium", "low", "unknown"}

    def test_enum_is_string_subclass(self) -> None:
        assert isinstance(ConfidenceLevel.HIGH, str)

    def test_enum_string_equality(self) -> None:
        assert ConfidenceLevel.HIGH == "high"


# ---------------------------------------------------------------------------
# _score_to_level internal helper
# ---------------------------------------------------------------------------


class TestScoreToLevel:
    def test_at_high_threshold_returns_high(self) -> None:
        assert _score_to_level(0.85, 0.85, 0.60, 0.30) == ConfidenceLevel.HIGH

    def test_above_high_threshold_returns_high(self) -> None:
        assert _score_to_level(1.0, 0.85, 0.60, 0.30) == ConfidenceLevel.HIGH

    def test_at_medium_threshold_returns_medium(self) -> None:
        assert _score_to_level(0.60, 0.85, 0.60, 0.30) == ConfidenceLevel.MEDIUM

    def test_between_medium_and_high_returns_medium(self) -> None:
        assert _score_to_level(0.70, 0.85, 0.60, 0.30) == ConfidenceLevel.MEDIUM

    def test_at_low_threshold_returns_low(self) -> None:
        assert _score_to_level(0.30, 0.85, 0.60, 0.30) == ConfidenceLevel.LOW

    def test_between_low_and_medium_returns_low(self) -> None:
        assert _score_to_level(0.45, 0.85, 0.60, 0.30) == ConfidenceLevel.LOW

    def test_below_low_threshold_returns_unknown(self) -> None:
        assert _score_to_level(0.10, 0.85, 0.60, 0.30) == ConfidenceLevel.UNKNOWN

    def test_zero_returns_unknown(self) -> None:
        assert _score_to_level(0.0, 0.85, 0.60, 0.30) == ConfidenceLevel.UNKNOWN


# ---------------------------------------------------------------------------
# AnnotatedResponse dataclass
# ---------------------------------------------------------------------------


class TestAnnotatedResponse:
    def _make(self, level: ConfidenceLevel, score: float) -> AnnotatedResponse:
        return AnnotatedResponse(
            content="Test response",
            confidence_level=level,
            confidence_score=score,
        )

    def test_is_high_confidence_true_for_high(self) -> None:
        resp = self._make(ConfidenceLevel.HIGH, 0.90)
        assert resp.is_high_confidence() is True

    def test_is_high_confidence_false_for_medium(self) -> None:
        resp = self._make(ConfidenceLevel.MEDIUM, 0.70)
        assert resp.is_high_confidence() is False

    def test_is_high_confidence_false_for_low(self) -> None:
        resp = self._make(ConfidenceLevel.LOW, 0.40)
        assert resp.is_high_confidence() is False

    def test_needs_disclaimer_false_for_high(self) -> None:
        resp = self._make(ConfidenceLevel.HIGH, 0.90)
        assert resp.needs_disclaimer() is False

    def test_needs_disclaimer_false_for_medium(self) -> None:
        resp = self._make(ConfidenceLevel.MEDIUM, 0.70)
        assert resp.needs_disclaimer() is False

    def test_needs_disclaimer_true_for_low(self) -> None:
        resp = self._make(ConfidenceLevel.LOW, 0.40)
        assert resp.needs_disclaimer() is True

    def test_needs_disclaimer_true_for_unknown(self) -> None:
        resp = self._make(ConfidenceLevel.UNKNOWN, 0.10)
        assert resp.needs_disclaimer() is True

    def test_default_domain_is_empty_string(self) -> None:
        resp = self._make(ConfidenceLevel.HIGH, 0.90)
        assert resp.domain == ""

    def test_default_metadata_is_empty_dict(self) -> None:
        resp = self._make(ConfidenceLevel.HIGH, 0.90)
        assert resp.metadata == {}

    def test_is_frozen(self) -> None:
        resp = self._make(ConfidenceLevel.HIGH, 0.90)
        with pytest.raises(AttributeError):
            resp.content = "new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ConfidenceAnnotator.annotate
# ---------------------------------------------------------------------------


class TestConfidenceAnnotatorAnnotate:
    @pytest.fixture()
    def annotator(self) -> ConfidenceAnnotator:
        return ConfidenceAnnotator()

    def test_annotate_returns_annotated_response(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("The capital is Paris.", score=0.92)
        assert isinstance(result, AnnotatedResponse)

    def test_score_above_high_threshold_produces_high(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.92)
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_score_at_high_threshold_produces_high(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.85)
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_score_in_medium_range_produces_medium(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.72)
        assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_score_in_low_range_produces_low(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.45)
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_score_below_low_threshold_produces_unknown(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.15)
        assert result.confidence_level == ConfidenceLevel.UNKNOWN

    def test_score_zero_produces_unknown(self, annotator: ConfidenceAnnotator) -> None:
        result = annotator.annotate("Answer", score=0.0)
        assert result.confidence_level == ConfidenceLevel.UNKNOWN

    def test_score_one_produces_high(self, annotator: ConfidenceAnnotator) -> None:
        result = annotator.annotate("Answer", score=1.0)
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_raw_score_preserved_on_result(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.77)
        assert result.confidence_score == pytest.approx(0.77)

    def test_content_preserved_on_result(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Paris is the capital.", score=0.90)
        assert result.content == "Paris is the capital."

    def test_domain_passed_through(self, annotator: ConfidenceAnnotator) -> None:
        result = annotator.annotate("Answer", score=0.90, domain="medical")
        assert result.domain == "medical"

    def test_metadata_passed_through(self, annotator: ConfidenceAnnotator) -> None:
        metadata = {"source": "gpt", "latency_ms": "120"}
        result = annotator.annotate("Answer", score=0.90, metadata=metadata)
        assert result.metadata == metadata

    def test_invalid_score_above_one_raises_value_error(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        with pytest.raises(ValueError, match="0.0, 1.0"):
            annotator.annotate("Answer", score=1.1)

    def test_invalid_score_below_zero_raises_value_error(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        with pytest.raises(ValueError, match="0.0, 1.0"):
            annotator.annotate("Answer", score=-0.1)

    def test_none_metadata_results_in_empty_dict(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        result = annotator.annotate("Answer", score=0.90, metadata=None)
        assert result.metadata == {}


# ---------------------------------------------------------------------------
# ConfidenceAnnotator with custom thresholds
# ---------------------------------------------------------------------------


class TestConfidenceAnnotatorWithThresholds:
    def test_custom_high_threshold_applied(self) -> None:
        thresholds = ConfidenceThresholds(default_high=0.95)
        annotator = ConfidenceAnnotator(thresholds=thresholds)
        # 0.90 is below 0.95 so should be MEDIUM, not HIGH
        result = annotator.annotate("Answer", score=0.90)
        assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_domain_override_applied(self) -> None:
        thresholds = ConfidenceThresholds()
        thresholds.set_domain("medical", high=0.95, medium=0.80, low=0.50)
        annotator = ConfidenceAnnotator(thresholds=thresholds)
        # 0.85 is below domain-specific HIGH of 0.95
        result = annotator.annotate("Answer", score=0.85, domain="medical")
        assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_non_domain_falls_back_to_defaults(self) -> None:
        thresholds = ConfidenceThresholds()
        thresholds.set_domain("medical", high=0.95, medium=0.80, low=0.50)
        annotator = ConfidenceAnnotator(thresholds=thresholds)
        # general domain uses the defaults
        result = annotator.annotate("Answer", score=0.85, domain="general")
        assert result.confidence_level == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# ConfidenceAnnotator.level_for_score
# ---------------------------------------------------------------------------


class TestLevelForScore:
    @pytest.fixture()
    def annotator(self) -> ConfidenceAnnotator:
        return ConfidenceAnnotator()

    def test_level_for_score_high(self, annotator: ConfidenceAnnotator) -> None:
        assert annotator.level_for_score(0.90) == ConfidenceLevel.HIGH

    def test_level_for_score_medium(self, annotator: ConfidenceAnnotator) -> None:
        assert annotator.level_for_score(0.65) == ConfidenceLevel.MEDIUM

    def test_level_for_score_low(self, annotator: ConfidenceAnnotator) -> None:
        assert annotator.level_for_score(0.40) == ConfidenceLevel.LOW

    def test_level_for_score_unknown(self, annotator: ConfidenceAnnotator) -> None:
        assert annotator.level_for_score(0.20) == ConfidenceLevel.UNKNOWN

    def test_level_for_score_with_domain(
        self, annotator: ConfidenceAnnotator
    ) -> None:
        # No domain override so same result as default
        assert annotator.level_for_score(0.90, domain="tech") == ConfidenceLevel.HIGH
