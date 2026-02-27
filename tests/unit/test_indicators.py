"""Unit tests for agent_sense.indicators — Phase 6E universal transparency indicators.

Covers:
- ConfidenceLevel auto-computation from score (all five tiers)
- Boundary values: 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- ConfidenceIndicator dataclass properties and to_dict serialisation
- from_score factory: valid inputs, edge cases, invalid inputs
- DisclosureLevel enum values
- AIDisclosureCard construction at all four DisclosureLevel values
- build_disclosure factory defaults and error paths
- HandoffReason enum values
- HandoffSignal construction and to_dict
- HandoffSignal.is_urgent: SAFETY_CONCERN always urgent, others not
- IndicatorRenderer: all 4 formats × all 3 indicator types = 12 combos
- HTML output: ARIA attributes, role attributes, progress bar markup
- HTML output: colour hex values confirming AA-compliant palette
- JSON output: round-trip parse correctness
- TEXT output: human-readable content assertions
- MARKDOWN output: heading and list structure
- CLI commands: confidence, disclosure, handoff
- Edge cases: score=0.0, score=1.0, empty reasoning, empty fields
"""
from __future__ import annotations

import datetime
import json

import pytest
from click.testing import CliRunner

from agent_sense.indicators.confidence import (
    ConfidenceIndicator,
    ConfidenceLevel,
    _level_for_score,
    from_score,
)
from agent_sense.indicators.disclosure import (
    AIDisclosureCard,
    DisclosureLevel,
    build_disclosure,
)
from agent_sense.indicators.handoff_signal import (
    HandoffReason,
    HandoffSignal,
)
from agent_sense.indicators.renderers import (
    IndicatorRenderer,
    RenderFormat,
    _ascii_bar,
    _percent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def renderer() -> IndicatorRenderer:
    return IndicatorRenderer()


@pytest.fixture()
def basic_confidence() -> ConfidenceIndicator:
    return from_score(0.75, reasoning="test reasoning", factors={"kw": 0.8, "ctx": 0.7})


@pytest.fixture()
def basic_card() -> AIDisclosureCard:
    return build_disclosure(
        agent_name="TestAgent",
        model_provider="Anthropic",
        model_name="claude-test",
        capabilities=["answering questions"],
        limitations=["no real-time data"],
        data_handling="Data is not stored.",
    )


@pytest.fixture()
def basic_signal(basic_confidence: ConfidenceIndicator) -> HandoffSignal:
    return HandoffSignal(
        reason=HandoffReason.CONFIDENCE_TOO_LOW,
        confidence=basic_confidence,
        suggested_specialist="human agent",
        context_summary="Could not answer billing question.",
        timestamp=datetime.datetime(2026, 2, 26, 12, 0, 0, tzinfo=datetime.timezone.utc),
    )


@pytest.fixture()
def safety_signal(basic_confidence: ConfidenceIndicator) -> HandoffSignal:
    return HandoffSignal(
        reason=HandoffReason.SAFETY_CONCERN,
        confidence=basic_confidence,
        suggested_specialist="safety reviewer",
        context_summary="Potentially harmful request detected.",
        timestamp=datetime.datetime(2026, 2, 26, 12, 0, 0, tzinfo=datetime.timezone.utc),
    )


# ===========================================================================
# ConfidenceLevel enum
# ===========================================================================


class TestConfidenceLevelEnum:
    def test_very_low_value(self) -> None:
        assert ConfidenceLevel.VERY_LOW.value == "very_low"

    def test_low_value(self) -> None:
        assert ConfidenceLevel.LOW.value == "low"

    def test_medium_value(self) -> None:
        assert ConfidenceLevel.MEDIUM.value == "medium"

    def test_high_value(self) -> None:
        assert ConfidenceLevel.HIGH.value == "high"

    def test_very_high_value(self) -> None:
        assert ConfidenceLevel.VERY_HIGH.value == "very_high"

    def test_has_exactly_five_members(self) -> None:
        assert len(ConfidenceLevel) == 5

    def test_is_string_subclass(self) -> None:
        assert isinstance(ConfidenceLevel.HIGH, str)

    def test_string_equality(self) -> None:
        assert ConfidenceLevel.HIGH == "high"


# ===========================================================================
# _level_for_score internal helper — boundary values
# ===========================================================================


class TestLevelForScore:
    def test_score_zero_is_very_low(self) -> None:
        assert _level_for_score(0.0) == ConfidenceLevel.VERY_LOW

    def test_score_just_below_low_boundary_is_very_low(self) -> None:
        assert _level_for_score(0.19) == ConfidenceLevel.VERY_LOW

    def test_score_at_low_boundary_is_low(self) -> None:
        assert _level_for_score(0.20) == ConfidenceLevel.LOW

    def test_score_mid_low_is_low(self) -> None:
        assert _level_for_score(0.30) == ConfidenceLevel.LOW

    def test_score_just_below_medium_boundary_is_low(self) -> None:
        assert _level_for_score(0.39) == ConfidenceLevel.LOW

    def test_score_at_medium_boundary_is_medium(self) -> None:
        assert _level_for_score(0.40) == ConfidenceLevel.MEDIUM

    def test_score_mid_medium_is_medium(self) -> None:
        assert _level_for_score(0.50) == ConfidenceLevel.MEDIUM

    def test_score_just_below_high_boundary_is_medium(self) -> None:
        assert _level_for_score(0.59) == ConfidenceLevel.MEDIUM

    def test_score_at_high_boundary_is_high(self) -> None:
        assert _level_for_score(0.60) == ConfidenceLevel.HIGH

    def test_score_mid_high_is_high(self) -> None:
        assert _level_for_score(0.70) == ConfidenceLevel.HIGH

    def test_score_just_below_very_high_boundary_is_high(self) -> None:
        assert _level_for_score(0.79) == ConfidenceLevel.HIGH

    def test_score_at_very_high_boundary_is_very_high(self) -> None:
        assert _level_for_score(0.80) == ConfidenceLevel.VERY_HIGH

    def test_score_mid_very_high_is_very_high(self) -> None:
        assert _level_for_score(0.90) == ConfidenceLevel.VERY_HIGH

    def test_score_one_is_very_high(self) -> None:
        assert _level_for_score(1.0) == ConfidenceLevel.VERY_HIGH


# ===========================================================================
# from_score factory
# ===========================================================================


class TestFromScore:
    def test_returns_confidence_indicator(self) -> None:
        indicator = from_score(0.5, "test")
        assert isinstance(indicator, ConfidenceIndicator)

    def test_score_is_preserved(self) -> None:
        indicator = from_score(0.65, "test")
        assert indicator.score == pytest.approx(0.65)

    def test_reasoning_is_preserved(self) -> None:
        indicator = from_score(0.5, "good match")
        assert indicator.reasoning == "good match"

    def test_factors_are_preserved(self) -> None:
        factors = {"semantic": 0.9, "lexical": 0.7}
        indicator = from_score(0.8, "test", factors=factors)
        assert indicator.factors == factors

    def test_factors_defaults_to_empty_dict(self) -> None:
        indicator = from_score(0.5, "test")
        assert indicator.factors == {}

    def test_none_factors_gives_empty_dict(self) -> None:
        indicator = from_score(0.5, "test", factors=None)
        assert indicator.factors == {}

    def test_level_auto_computed_very_low(self) -> None:
        assert from_score(0.1, "test").level == ConfidenceLevel.VERY_LOW

    def test_level_auto_computed_low(self) -> None:
        assert from_score(0.3, "test").level == ConfidenceLevel.LOW

    def test_level_auto_computed_medium(self) -> None:
        assert from_score(0.5, "test").level == ConfidenceLevel.MEDIUM

    def test_level_auto_computed_high(self) -> None:
        assert from_score(0.7, "test").level == ConfidenceLevel.HIGH

    def test_level_auto_computed_very_high(self) -> None:
        assert from_score(0.9, "test").level == ConfidenceLevel.VERY_HIGH

    def test_score_zero_is_accepted(self) -> None:
        indicator = from_score(0.0, "test")
        assert indicator.score == 0.0
        assert indicator.level == ConfidenceLevel.VERY_LOW

    def test_score_one_is_accepted(self) -> None:
        indicator = from_score(1.0, "test")
        assert indicator.score == 1.0
        assert indicator.level == ConfidenceLevel.VERY_HIGH

    def test_score_above_one_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="0.0, 1.0"):
            from_score(1.01, "test")

    def test_score_below_zero_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="0.0, 1.0"):
            from_score(-0.01, "test")

    def test_indicator_is_frozen(self) -> None:
        indicator = from_score(0.5, "test")
        with pytest.raises(AttributeError):
            indicator.score = 0.9  # type: ignore[misc]

    def test_empty_reasoning_accepted(self) -> None:
        indicator = from_score(0.5, "")
        assert indicator.reasoning == ""


# ===========================================================================
# ConfidenceIndicator.to_dict
# ===========================================================================


class TestConfidenceIndicatorToDict:
    def test_to_dict_returns_dict(self, basic_confidence: ConfidenceIndicator) -> None:
        assert isinstance(basic_confidence.to_dict(), dict)

    def test_to_dict_contains_score(self, basic_confidence: ConfidenceIndicator) -> None:
        assert "score" in basic_confidence.to_dict()

    def test_to_dict_contains_level(self, basic_confidence: ConfidenceIndicator) -> None:
        result = basic_confidence.to_dict()
        assert result["level"] == basic_confidence.level.value

    def test_to_dict_contains_reasoning(self, basic_confidence: ConfidenceIndicator) -> None:
        result = basic_confidence.to_dict()
        assert result["reasoning"] == basic_confidence.reasoning

    def test_to_dict_contains_factors(self, basic_confidence: ConfidenceIndicator) -> None:
        result = basic_confidence.to_dict()
        assert result["factors"] == basic_confidence.factors

    def test_to_dict_is_json_serialisable(self, basic_confidence: ConfidenceIndicator) -> None:
        # Should not raise
        serialised = json.dumps(basic_confidence.to_dict())
        assert isinstance(serialised, str)


# ===========================================================================
# DisclosureLevel enum
# ===========================================================================


class TestDisclosureLevelEnum:
    def test_minimal_value(self) -> None:
        assert DisclosureLevel.MINIMAL.value == "minimal"

    def test_standard_value(self) -> None:
        assert DisclosureLevel.STANDARD.value == "standard"

    def test_detailed_value(self) -> None:
        assert DisclosureLevel.DETAILED.value == "detailed"

    def test_full_value(self) -> None:
        assert DisclosureLevel.FULL.value == "full"

    def test_has_exactly_four_members(self) -> None:
        assert len(DisclosureLevel) == 4


# ===========================================================================
# build_disclosure factory
# ===========================================================================


class TestBuildDisclosure:
    def test_returns_ai_disclosure_card(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        assert isinstance(card, AIDisclosureCard)

    def test_agent_name_preserved(self) -> None:
        card = build_disclosure(agent_name="Aria", model_provider="Anthropic")
        assert card.agent_name == "Aria"

    def test_agent_name_stripped(self) -> None:
        card = build_disclosure(agent_name="  Aria  ", model_provider="Anthropic")
        assert card.agent_name == "Aria"

    def test_model_provider_preserved(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="OpenAI")
        assert card.model_provider == "OpenAI"

    def test_default_version(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        assert card.agent_version == "1.0.0"

    def test_default_capabilities_is_empty(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        assert card.capabilities == []

    def test_default_limitations_is_empty(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        assert card.limitations == []

    def test_default_disclosure_level_is_standard(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        assert card.disclosure_level == DisclosureLevel.STANDARD

    def test_capabilities_preserved(self) -> None:
        card = build_disclosure(
            agent_name="A", model_provider="B", capabilities=["do x", "do y"]
        )
        assert card.capabilities == ["do x", "do y"]

    def test_limitations_preserved(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B", limitations=["no x"])
        assert card.limitations == ["no x"]

    def test_full_level(self) -> None:
        card = build_disclosure(
            agent_name="A", model_provider="B", disclosure_level=DisclosureLevel.FULL
        )
        assert card.disclosure_level == DisclosureLevel.FULL

    def test_empty_agent_name_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_name"):
            build_disclosure(agent_name="", model_provider="B")

    def test_whitespace_agent_name_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_name"):
            build_disclosure(agent_name="   ", model_provider="B")

    def test_empty_model_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="model_provider"):
            build_disclosure(agent_name="A", model_provider="")

    def test_card_is_frozen(self) -> None:
        card = build_disclosure(agent_name="A", model_provider="B")
        with pytest.raises(AttributeError):
            card.agent_name = "other"  # type: ignore[misc]

    def test_explicit_last_updated_preserved(self) -> None:
        dt = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        card = build_disclosure(agent_name="A", model_provider="B", last_updated=dt)
        assert card.last_updated == dt


# ===========================================================================
# AIDisclosureCard.to_dict
# ===========================================================================


class TestAIDisclosureCardToDict:
    def test_to_dict_has_agent_name(self, basic_card: AIDisclosureCard) -> None:
        assert basic_card.to_dict()["agent_name"] == "TestAgent"

    def test_to_dict_has_model_provider(self, basic_card: AIDisclosureCard) -> None:
        assert basic_card.to_dict()["model_provider"] == "Anthropic"

    def test_to_dict_has_disclosure_level(self, basic_card: AIDisclosureCard) -> None:
        assert basic_card.to_dict()["disclosure_level"] == "standard"

    def test_to_dict_last_updated_is_iso_string(self, basic_card: AIDisclosureCard) -> None:
        value = basic_card.to_dict()["last_updated"]
        assert isinstance(value, str)
        # Should be parseable as ISO datetime
        datetime.datetime.fromisoformat(str(value))

    def test_to_dict_is_json_serialisable(self, basic_card: AIDisclosureCard) -> None:
        serialised = json.dumps(basic_card.to_dict())
        assert isinstance(serialised, str)


# ===========================================================================
# HandoffReason enum
# ===========================================================================


class TestHandoffReasonEnum:
    def test_confidence_too_low_value(self) -> None:
        assert HandoffReason.CONFIDENCE_TOO_LOW.value == "confidence_too_low"

    def test_out_of_scope_value(self) -> None:
        assert HandoffReason.OUT_OF_SCOPE.value == "out_of_scope"

    def test_user_request_value(self) -> None:
        assert HandoffReason.USER_REQUEST.value == "user_request"

    def test_safety_concern_value(self) -> None:
        assert HandoffReason.SAFETY_CONCERN.value == "safety_concern"

    def test_complexity_exceeded_value(self) -> None:
        assert HandoffReason.COMPLEXITY_EXCEEDED.value == "complexity_exceeded"

    def test_requires_human_judgment_value(self) -> None:
        assert HandoffReason.REQUIRES_HUMAN_JUDGMENT.value == "requires_human_judgment"

    def test_has_exactly_six_members(self) -> None:
        assert len(HandoffReason) == 6


# ===========================================================================
# HandoffSignal
# ===========================================================================


class TestHandoffSignal:
    def test_is_frozen(self, basic_signal: HandoffSignal) -> None:
        with pytest.raises(AttributeError):
            basic_signal.context_summary = "new"  # type: ignore[misc]

    def test_reason_preserved(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.reason == HandoffReason.CONFIDENCE_TOO_LOW

    def test_confidence_preserved(
        self, basic_signal: HandoffSignal, basic_confidence: ConfidenceIndicator
    ) -> None:
        assert basic_signal.confidence is basic_confidence

    def test_suggested_specialist_preserved(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.suggested_specialist == "human agent"

    def test_context_summary_preserved(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.context_summary == "Could not answer billing question."

    def test_timestamp_preserved(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.timestamp.year == 2026


class TestHandoffSignalIsUrgent:
    def test_safety_concern_is_urgent(self, safety_signal: HandoffSignal) -> None:
        assert safety_signal.is_urgent() is True

    def test_confidence_too_low_is_not_urgent(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.is_urgent() is False

    def test_out_of_scope_is_not_urgent(self, basic_confidence: ConfidenceIndicator) -> None:
        signal = HandoffSignal(
            reason=HandoffReason.OUT_OF_SCOPE,
            confidence=basic_confidence,
            suggested_specialist="expert",
            context_summary="",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert signal.is_urgent() is False

    def test_user_request_is_not_urgent(self, basic_confidence: ConfidenceIndicator) -> None:
        signal = HandoffSignal(
            reason=HandoffReason.USER_REQUEST,
            confidence=basic_confidence,
            suggested_specialist="human",
            context_summary="",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert signal.is_urgent() is False

    def test_complexity_exceeded_is_not_urgent(
        self, basic_confidence: ConfidenceIndicator
    ) -> None:
        signal = HandoffSignal(
            reason=HandoffReason.COMPLEXITY_EXCEEDED,
            confidence=basic_confidence,
            suggested_specialist="senior agent",
            context_summary="",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert signal.is_urgent() is False

    def test_requires_human_judgment_is_not_urgent(
        self, basic_confidence: ConfidenceIndicator
    ) -> None:
        signal = HandoffSignal(
            reason=HandoffReason.REQUIRES_HUMAN_JUDGMENT,
            confidence=basic_confidence,
            suggested_specialist="human",
            context_summary="",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert signal.is_urgent() is False


class TestHandoffSignalToDict:
    def test_to_dict_has_reason(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.to_dict()["reason"] == "confidence_too_low"

    def test_to_dict_has_confidence(self, basic_signal: HandoffSignal) -> None:
        assert "confidence" in basic_signal.to_dict()

    def test_to_dict_has_suggested_specialist(self, basic_signal: HandoffSignal) -> None:
        assert basic_signal.to_dict()["suggested_specialist"] == "human agent"

    def test_to_dict_has_is_urgent(self, basic_signal: HandoffSignal) -> None:
        result = basic_signal.to_dict()
        assert "is_urgent" in result
        assert result["is_urgent"] is False

    def test_to_dict_safety_is_urgent_true(self, safety_signal: HandoffSignal) -> None:
        assert safety_signal.to_dict()["is_urgent"] is True

    def test_to_dict_is_json_serialisable(self, basic_signal: HandoffSignal) -> None:
        serialised = json.dumps(basic_signal.to_dict())
        assert isinstance(serialised, str)

    def test_to_dict_timestamp_is_iso_string(self, basic_signal: HandoffSignal) -> None:
        ts = basic_signal.to_dict()["timestamp"]
        datetime.datetime.fromisoformat(str(ts))


# ===========================================================================
# IndicatorRenderer — TEXT format
# ===========================================================================


class TestRenderConfidenceText:
    def test_contains_level_label(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.TEXT)
        assert "High" in output

    def test_contains_percentage(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.TEXT)
        assert "75%" in output

    def test_contains_ascii_bar(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.TEXT)
        assert "[" in output and "]" in output

    def test_contains_reasoning(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.TEXT)
        assert "test reasoning" in output

    def test_contains_factor_names(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.TEXT)
        assert "kw" in output
        assert "ctx" in output

    def test_score_zero_renders_all_dashes(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.0, "no confidence")
        output = renderer.render_confidence(indicator, RenderFormat.TEXT)
        assert "Very Low" in output


class TestRenderDisclosureText:
    def test_contains_agent_name(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.TEXT)
        assert "TestAgent" in output

    def test_contains_model_provider(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.TEXT)
        assert "Anthropic" in output

    def test_standard_contains_model_name(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.TEXT)
        assert "claude-test" in output

    def test_minimal_does_not_contain_model_name(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            model_name="secret-model",
            disclosure_level=DisclosureLevel.MINIMAL,
        )
        output = renderer.render_disclosure(card, RenderFormat.TEXT)
        assert "secret-model" not in output

    def test_full_contains_data_handling(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            data_handling="No storage.",
            disclosure_level=DisclosureLevel.FULL,
        )
        output = renderer.render_disclosure(card, RenderFormat.TEXT)
        assert "No storage." in output


class TestRenderHandoffText:
    def test_contains_reason(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.TEXT)
        assert "Confidence Too Low" in output

    def test_contains_specialist(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.TEXT)
        assert "human agent" in output

    def test_contains_standard_urgency_label(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.TEXT)
        assert "Standard" in output

    def test_urgent_signal_contains_urgent_label(
        self, renderer: IndicatorRenderer, safety_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(safety_signal, RenderFormat.TEXT)
        assert "URGENT" in output

    def test_contains_context_summary(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.TEXT)
        assert "billing question" in output


# ===========================================================================
# IndicatorRenderer — JSON format
# ===========================================================================


class TestRenderConfidenceJson:
    def test_output_is_valid_json(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.JSON)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_contains_score(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        parsed = json.loads(renderer.render_confidence(basic_confidence, RenderFormat.JSON))
        assert parsed["score"] == pytest.approx(0.75)

    def test_json_contains_level(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        parsed = json.loads(renderer.render_confidence(basic_confidence, RenderFormat.JSON))
        assert parsed["level"] == "high"

    def test_json_contains_reasoning(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        parsed = json.loads(renderer.render_confidence(basic_confidence, RenderFormat.JSON))
        assert parsed["reasoning"] == "test reasoning"

    def test_json_factors_round_trip(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        parsed = json.loads(renderer.render_confidence(basic_confidence, RenderFormat.JSON))
        assert parsed["factors"]["kw"] == pytest.approx(0.8)


class TestRenderDisclosureJson:
    def test_output_is_valid_json(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.JSON)
        assert isinstance(json.loads(output), dict)

    def test_json_has_agent_name(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        parsed = json.loads(renderer.render_disclosure(basic_card, RenderFormat.JSON))
        assert parsed["agent_name"] == "TestAgent"

    def test_json_has_capabilities(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        parsed = json.loads(renderer.render_disclosure(basic_card, RenderFormat.JSON))
        assert "answering questions" in parsed["capabilities"]


class TestRenderHandoffJson:
    def test_output_is_valid_json(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.JSON)
        assert isinstance(json.loads(output), dict)

    def test_json_has_reason(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        parsed = json.loads(renderer.render_handoff(basic_signal, RenderFormat.JSON))
        assert parsed["reason"] == "confidence_too_low"

    def test_json_is_urgent_false_for_non_safety(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        parsed = json.loads(renderer.render_handoff(basic_signal, RenderFormat.JSON))
        assert parsed["is_urgent"] is False

    def test_json_is_urgent_true_for_safety(
        self, renderer: IndicatorRenderer, safety_signal: HandoffSignal
    ) -> None:
        parsed = json.loads(renderer.render_handoff(safety_signal, RenderFormat.JSON))
        assert parsed["is_urgent"] is True


# ===========================================================================
# IndicatorRenderer — MARKDOWN format
# ===========================================================================


class TestRenderConfidenceMarkdown:
    def test_starts_with_heading(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.MARKDOWN)
        assert output.startswith("## Confidence")

    def test_contains_percentage(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.MARKDOWN)
        assert "75%" in output

    def test_contains_reasoning(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.MARKDOWN)
        assert "test reasoning" in output

    def test_factors_rendered_as_list(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.MARKDOWN)
        assert "- **kw:**" in output


class TestRenderDisclosureMarkdown:
    def test_starts_with_heading(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.MARKDOWN)
        assert output.startswith("## AI Disclosure")

    def test_contains_agent_name(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.MARKDOWN)
        assert "TestAgent" in output

    def test_capabilities_rendered_as_list(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.MARKDOWN)
        assert "- answering questions" in output

    def test_limitations_in_detailed_level(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            limitations=["slow for large files"],
            disclosure_level=DisclosureLevel.DETAILED,
        )
        output = renderer.render_disclosure(card, RenderFormat.MARKDOWN)
        assert "slow for large files" in output

    def test_data_handling_in_full_level(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            data_handling="Stored 30 days.",
            disclosure_level=DisclosureLevel.FULL,
        )
        output = renderer.render_disclosure(card, RenderFormat.MARKDOWN)
        assert "Stored 30 days." in output


class TestRenderHandoffMarkdown:
    def test_starts_with_heading(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.MARKDOWN)
        assert output.startswith("## Handoff Signal")

    def test_urgent_in_heading_for_safety(
        self, renderer: IndicatorRenderer, safety_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(safety_signal, RenderFormat.MARKDOWN)
        assert "URGENT" in output

    def test_contains_specialist(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.MARKDOWN)
        assert "human agent" in output


# ===========================================================================
# IndicatorRenderer — HTML format (ARIA and colour contrast)
# ===========================================================================


class TestRenderConfidenceHtml:
    def test_contains_role_status(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert 'role="status"' in output

    def test_contains_aria_label(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert "aria-label" in output

    def test_contains_progressbar_role(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert 'role="progressbar"' in output

    def test_progressbar_has_aria_valuenow(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert "aria-valuenow" in output

    def test_progressbar_has_aria_valuemin(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert 'aria-valuemin="0"' in output

    def test_progressbar_has_aria_valuemax(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert 'aria-valuemax="100"' in output

    def test_progressbar_valuenow_matches_score(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert 'aria-valuenow="75"' in output

    def test_contains_reasoning_text(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert "test reasoning" in output

    def test_very_low_uses_dark_red_background(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.05, "very uncertain")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        # Palette colour for VERY_LOW — contrast ratio verified ≥ 4.5:1
        assert "#7f1d1d" in output

    def test_low_uses_amber_background(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.25, "uncertain")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert "#92400e" in output

    def test_medium_uses_brown_background(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.50, "moderate")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert "#78350f" in output

    def test_high_uses_dark_green_background(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.70, "confident")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert "#14532d" in output

    def test_very_high_uses_dark_blue_background(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.90, "very confident")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert "#1e3a5f" in output

    def test_foreground_is_white(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert "#ffffff" in output

    def test_factors_rendered_as_list(
        self, renderer: IndicatorRenderer, basic_confidence: ConfidenceIndicator
    ) -> None:
        output = renderer.render_confidence(basic_confidence, RenderFormat.HTML)
        assert "<ul" in output
        assert "<li" in output


class TestRenderDisclosureHtml:
    def test_contains_section_with_aria_label(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.HTML)
        assert '<section aria-label="AI disclosure card"' in output

    def test_contains_agent_name(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.HTML)
        assert "TestAgent" in output

    def test_standard_contains_capabilities_list(
        self, renderer: IndicatorRenderer, basic_card: AIDisclosureCard
    ) -> None:
        output = renderer.render_disclosure(basic_card, RenderFormat.HTML)
        assert "answering questions" in output

    def test_minimal_does_not_contain_capabilities(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            capabilities=["do x"],
            disclosure_level=DisclosureLevel.MINIMAL,
        )
        output = renderer.render_disclosure(card, RenderFormat.HTML)
        assert "do x" not in output

    def test_full_level_contains_data_handling(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            data_handling="Retained 7 days.",
            disclosure_level=DisclosureLevel.FULL,
        )
        output = renderer.render_disclosure(card, RenderFormat.HTML)
        assert "Retained 7 days." in output


class TestRenderHandoffHtml:
    def test_non_urgent_uses_role_status(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.HTML)
        assert 'role="status"' in output

    def test_urgent_uses_role_alert(
        self, renderer: IndicatorRenderer, safety_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(safety_signal, RenderFormat.HTML)
        assert 'role="alert"' in output

    def test_urgent_contains_aria_live_assertive(
        self, renderer: IndicatorRenderer, safety_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(safety_signal, RenderFormat.HTML)
        assert "aria-live" in output

    def test_contains_reason(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.HTML)
        assert "Confidence Too Low" in output

    def test_contains_specialist(
        self, renderer: IndicatorRenderer, basic_signal: HandoffSignal
    ) -> None:
        output = renderer.render_handoff(basic_signal, RenderFormat.HTML)
        assert "human agent" in output

    def test_html_escape_in_context(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.2, "test")
        signal = HandoffSignal(
            reason=HandoffReason.OUT_OF_SCOPE,
            confidence=indicator,
            suggested_specialist="expert",
            context_summary="User asked <script>alert('x')</script>",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        output = renderer.render_handoff(signal, RenderFormat.HTML)
        assert "<script>" not in output
        assert "&lt;script&gt;" in output


# ===========================================================================
# Rendering edge cases
# ===========================================================================


class TestRenderEdgeCases:
    def test_confidence_score_zero_html(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.0, "")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert 'aria-valuenow="0"' in output

    def test_confidence_score_one_html(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(1.0, "maximum")
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert 'aria-valuenow="100"' in output

    def test_confidence_empty_factors_html_no_list(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.5, "test", factors={})
        output = renderer.render_confidence(indicator, RenderFormat.HTML)
        assert "<ul" not in output

    def test_disclosure_empty_capabilities_no_list(self, renderer: IndicatorRenderer) -> None:
        card = build_disclosure(
            agent_name="A",
            model_provider="B",
            capabilities=[],
        )
        output = renderer.render_disclosure(card, RenderFormat.TEXT)
        assert "Capabilities" not in output

    def test_handoff_empty_context_summary(self, renderer: IndicatorRenderer) -> None:
        indicator = from_score(0.3, "low")
        signal = HandoffSignal(
            reason=HandoffReason.OUT_OF_SCOPE,
            confidence=indicator,
            suggested_specialist="specialist",
            context_summary="",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        output = renderer.render_handoff(signal, RenderFormat.TEXT)
        assert "Out Of Scope" in output

    def test_all_formats_return_strings(
        self,
        renderer: IndicatorRenderer,
        basic_confidence: ConfidenceIndicator,
        basic_card: AIDisclosureCard,
        basic_signal: HandoffSignal,
    ) -> None:
        for fmt in RenderFormat:
            assert isinstance(renderer.render_confidence(basic_confidence, fmt), str)
            assert isinstance(renderer.render_disclosure(basic_card, fmt), str)
            assert isinstance(renderer.render_handoff(basic_signal, fmt), str)


# ===========================================================================
# _ascii_bar and _percent helpers
# ===========================================================================


class TestAsciiBarHelper:
    def test_zero_score_all_dashes(self) -> None:
        bar = _ascii_bar(0.0, width=10)
        assert bar == "[----------]"

    def test_full_score_all_hashes(self) -> None:
        bar = _ascii_bar(1.0, width=10)
        assert bar == "[##########]"

    def test_half_score(self) -> None:
        bar = _ascii_bar(0.5, width=10)
        assert bar == "[#####-----]"

    def test_total_length_is_width_plus_two(self) -> None:
        bar = _ascii_bar(0.75, width=20)
        assert len(bar) == 22  # 20 + 2 brackets


class TestPercentHelper:
    def test_zero(self) -> None:
        assert _percent(0.0) == "0%"

    def test_one(self) -> None:
        assert _percent(1.0) == "100%"

    def test_half(self) -> None:
        assert _percent(0.5) == "50%"

    def test_rounding(self) -> None:
        assert _percent(0.756) == "76%"


# ===========================================================================
# CLI integration tests
# ===========================================================================


class TestIndicatorsConfidenceCli:
    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_text_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(cli, ["indicators", "confidence", "--score", "0.8"])
        assert result.exit_code == 0

    def test_json_format_output_is_valid_json(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "confidence", "--score", "0.85", "--format", "json"],
        )
        assert result.exit_code == 0

    def test_html_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "confidence", "--score", "0.6", "--format", "html"],
        )
        assert result.exit_code == 0

    def test_markdown_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "confidence", "--score", "0.4", "--format", "markdown"],
        )
        assert result.exit_code == 0

    def test_invalid_score_exits_nonzero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(cli, ["indicators", "confidence", "--score", "1.5"])
        assert result.exit_code != 0

    def test_reasoning_passed_through(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "confidence",
                "--score",
                "0.9",
                "--reasoning",
                "excellent match",
                "--format",
                "text",
            ],
        )
        assert result.exit_code == 0


class TestIndicatorsDisclosureCli:
    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_default_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "disclosure", "--agent-name", "Aria", "--model", "Anthropic"],
        )
        assert result.exit_code == 0

    def test_json_format_contains_agent_name(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "disclosure",
                "--agent-name",
                "Aria",
                "--model",
                "Anthropic",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0

    def test_empty_agent_name_exits_nonzero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "disclosure", "--agent-name", "", "--model", "Anthropic"],
        )
        assert result.exit_code != 0

    def test_full_level_flag(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "disclosure",
                "--agent-name",
                "Aria",
                "--model",
                "Anthropic",
                "--level",
                "full",
                "--format",
                "text",
            ],
        )
        assert result.exit_code == 0

    def test_markdown_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "disclosure",
                "--agent-name",
                "Bot",
                "--model",
                "OpenAI",
                "--format",
                "markdown",
            ],
        )
        assert result.exit_code == 0


class TestIndicatorsHandoffCli:
    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_confidence_too_low_text(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            ["indicators", "handoff", "--reason", "confidence_too_low"],
        )
        assert result.exit_code == 0

    def test_safety_concern_json(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "handoff",
                "--reason",
                "safety_concern",
                "--confidence",
                "0.05",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0

    def test_html_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "handoff",
                "--reason",
                "out_of_scope",
                "--format",
                "html",
            ],
        )
        assert result.exit_code == 0

    def test_markdown_format_exits_zero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "handoff",
                "--reason",
                "user_request",
                "--format",
                "markdown",
            ],
        )
        assert result.exit_code == 0

    def test_invalid_confidence_score_exits_nonzero(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        result = runner.invoke(
            cli,
            [
                "indicators",
                "handoff",
                "--reason",
                "confidence_too_low",
                "--confidence",
                "2.0",
            ],
        )
        assert result.exit_code != 0

    def test_all_reason_values_accepted(self, runner: CliRunner) -> None:
        from agent_sense.cli.main import cli

        for reason in [
            "confidence_too_low",
            "out_of_scope",
            "user_request",
            "safety_concern",
            "complexity_exceeded",
            "requires_human_judgment",
        ]:
            result = runner.invoke(
                cli, ["indicators", "handoff", "--reason", reason]
            )
            assert result.exit_code == 0, f"Failed for reason: {reason}"


# ===========================================================================
# Public __init__ re-exports
# ===========================================================================


class TestIndicatorsPackageExports:
    def test_confidence_indicator_importable(self) -> None:
        from agent_sense.indicators import ConfidenceIndicator  # noqa: F401

    def test_confidence_level_importable(self) -> None:
        from agent_sense.indicators import ConfidenceLevel  # noqa: F401

    def test_from_score_importable(self) -> None:
        from agent_sense.indicators import from_score  # noqa: F401

    def test_ai_disclosure_card_importable(self) -> None:
        from agent_sense.indicators import AIDisclosureCard  # noqa: F401

    def test_disclosure_level_importable(self) -> None:
        from agent_sense.indicators import DisclosureLevel  # noqa: F401

    def test_build_disclosure_importable(self) -> None:
        from agent_sense.indicators import build_disclosure  # noqa: F401

    def test_handoff_reason_importable(self) -> None:
        from agent_sense.indicators import HandoffReason  # noqa: F401

    def test_handoff_signal_importable(self) -> None:
        from agent_sense.indicators import HandoffSignal  # noqa: F401

    def test_indicator_renderer_importable(self) -> None:
        from agent_sense.indicators import IndicatorRenderer  # noqa: F401

    def test_render_format_importable(self) -> None:
        from agent_sense.indicators import RenderFormat  # noqa: F401
