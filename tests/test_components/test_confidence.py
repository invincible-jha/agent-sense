"""Tests for agent_sense.components.confidence — ConfidenceUIIndicator."""
from __future__ import annotations

import pytest

from agent_sense.components.confidence import (
    ConfidenceLevel,
    ConfidenceUIIndicator,
    EscalationThreshold,
    RenderMetadata,
    build_ui_indicator,
    _score_to_level,
)


# ---------------------------------------------------------------------------
# _score_to_level
# ---------------------------------------------------------------------------


class TestScoreToLevel:
    def test_high_at_boundary(self) -> None:
        assert _score_to_level(0.70) == ConfidenceLevel.HIGH

    def test_high_above_boundary(self) -> None:
        assert _score_to_level(0.99) == ConfidenceLevel.HIGH
        assert _score_to_level(1.0) == ConfidenceLevel.HIGH

    def test_medium_at_lower_boundary(self) -> None:
        assert _score_to_level(0.40) == ConfidenceLevel.MEDIUM

    def test_medium_just_below_high(self) -> None:
        assert _score_to_level(0.699) == ConfidenceLevel.MEDIUM

    def test_low_at_zero(self) -> None:
        assert _score_to_level(0.0) == ConfidenceLevel.LOW

    def test_low_just_below_medium(self) -> None:
        assert _score_to_level(0.39) == ConfidenceLevel.LOW

    def test_low_mid_range(self) -> None:
        assert _score_to_level(0.2) == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# EscalationThreshold
# ---------------------------------------------------------------------------


class TestEscalationThreshold:
    def test_defaults(self) -> None:
        et = EscalationThreshold()
        assert et.score_threshold == 0.40
        assert et.enabled is True
        assert et.escalation_target == "supervisor"

    def test_custom(self) -> None:
        et = EscalationThreshold(
            score_threshold=0.60,
            enabled=False,
            escalation_target="human-queue",
        )
        assert et.score_threshold == 0.60
        assert et.enabled is False

    def test_frozen(self) -> None:
        et = EscalationThreshold()
        with pytest.raises((TypeError, AttributeError)):
            et.enabled = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RenderMetadata
# ---------------------------------------------------------------------------


class TestRenderMetadata:
    def test_frozen(self) -> None:
        rm = RenderMetadata(
            css_class="x",
            hex_colour="#fff",
            icon="x",
            label="X",
            aria_label="X",
        )
        with pytest.raises((TypeError, AttributeError)):
            rm.css_class = "y"  # type: ignore[misc]

    def test_show_score_default(self) -> None:
        rm = RenderMetadata(
            css_class="x", hex_colour="#fff", icon="x", label="X", aria_label="X"
        )
        assert rm.show_score is False


# ---------------------------------------------------------------------------
# ConfidenceUIIndicator
# ---------------------------------------------------------------------------


class TestConfidenceUIIndicator:
    def test_needs_escalation_when_score_below_threshold(self) -> None:
        indicator = build_ui_indicator(0.30)
        assert indicator.needs_escalation is True

    def test_no_escalation_at_threshold(self) -> None:
        indicator = build_ui_indicator(
            0.40, threshold=EscalationThreshold(score_threshold=0.40)
        )
        # score == threshold → NOT below → no escalation
        assert indicator.needs_escalation is False

    def test_no_escalation_when_disabled(self) -> None:
        indicator = build_ui_indicator(
            0.10, threshold=EscalationThreshold(enabled=False)
        )
        assert indicator.needs_escalation is False

    def test_level_high(self) -> None:
        indicator = build_ui_indicator(0.85)
        assert indicator.level == ConfidenceLevel.HIGH

    def test_level_medium(self) -> None:
        indicator = build_ui_indicator(0.55)
        assert indicator.level == ConfidenceLevel.MEDIUM

    def test_level_low(self) -> None:
        indicator = build_ui_indicator(0.20)
        assert indicator.level == ConfidenceLevel.LOW

    def test_render_metadata_high(self) -> None:
        indicator = build_ui_indicator(0.90)
        assert indicator.render.css_class == "confidence-high"
        assert "#" in indicator.render.hex_colour
        assert "confident" in indicator.render.aria_label.lower()

    def test_render_metadata_medium(self) -> None:
        indicator = build_ui_indicator(0.55)
        assert indicator.render.css_class == "confidence-medium"
        assert indicator.render.show_score is True

    def test_render_metadata_low(self) -> None:
        indicator = build_ui_indicator(0.15)
        assert indicator.render.css_class == "confidence-low"
        assert indicator.render.show_score is True

    def test_context_label(self) -> None:
        indicator = build_ui_indicator(0.75, context_label="medical query")
        assert indicator.context_label == "medical query"

    def test_extra_annotations(self) -> None:
        indicator = build_ui_indicator(0.60, extra={"source": "retrieval-v2"})
        assert indicator.extra["source"] == "retrieval-v2"

    def test_to_dict_structure(self) -> None:
        indicator = build_ui_indicator(0.80)
        d = indicator.to_dict()
        assert "score" in d
        assert "level" in d
        assert "render" in d
        assert "needs_escalation" in d
        assert "escalation_target" in d

    def test_to_dict_values(self) -> None:
        indicator = build_ui_indicator(0.30)
        d = indicator.to_dict()
        assert d["level"] == "low"
        assert d["needs_escalation"] is True
        assert d["score"] == pytest.approx(0.30)

    def test_frozen(self) -> None:
        indicator = build_ui_indicator(0.70)
        with pytest.raises((TypeError, AttributeError)):
            indicator.score = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# build_ui_indicator
# ---------------------------------------------------------------------------


class TestBuildUIIndicator:
    def test_score_zero(self) -> None:
        indicator = build_ui_indicator(0.0)
        assert indicator.score == 0.0
        assert indicator.level == ConfidenceLevel.LOW

    def test_score_one(self) -> None:
        indicator = build_ui_indicator(1.0)
        assert indicator.level == ConfidenceLevel.HIGH

    def test_score_out_of_range_high(self) -> None:
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            build_ui_indicator(1.01)

    def test_score_out_of_range_low(self) -> None:
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            build_ui_indicator(-0.01)

    def test_default_threshold(self) -> None:
        indicator = build_ui_indicator(0.35)
        assert indicator.threshold.score_threshold == 0.40
        assert indicator.needs_escalation is True

    def test_custom_threshold(self) -> None:
        et = EscalationThreshold(score_threshold=0.80, escalation_target="team-lead")
        indicator = build_ui_indicator(0.75, threshold=et)
        assert indicator.needs_escalation is True
        assert indicator.threshold.escalation_target == "team-lead"

    def test_escalation_target_in_dict(self) -> None:
        et = EscalationThreshold(escalation_target="ciso")
        indicator = build_ui_indicator(0.50, threshold=et)
        d = indicator.to_dict()
        assert d["escalation_target"] == "ciso"

    @pytest.mark.parametrize("score", [0.0, 0.1, 0.39, 0.40, 0.69, 0.70, 0.99, 1.0])
    def test_boundary_scores(self, score: float) -> None:
        indicator = build_ui_indicator(score)
        assert 0.0 <= indicator.score <= 1.0
        assert indicator.level in list(ConfidenceLevel)
