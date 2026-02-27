"""Tests for ThoughtPanel — E16.3."""

from __future__ import annotations

import json

import pytest

from agent_sense.visualization.thought_panel import (
    PanelConfig,
    PanelFormat,
    ReasoningStep,
    ThoughtPanel,
)


# ---------------------------------------------------------------------------
# ReasoningStep tests
# ---------------------------------------------------------------------------


class TestReasoningStep:
    def test_valid_step_created(self) -> None:
        step = ReasoningStep(description="Evaluated user query intent.", confidence=0.85)
        assert step.description == "Evaluated user query intent."
        assert step.confidence == 0.85

    def test_empty_description_raises(self) -> None:
        with pytest.raises(ValueError, match="description"):
            ReasoningStep(description="")

    def test_confidence_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            ReasoningStep(description="Test", confidence=1.5)

    def test_confidence_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            ReasoningStep(description="Test", confidence=-0.1)

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError, match="duration_ms"):
            ReasoningStep(description="Test", duration_ms=-1.0)

    def test_confidence_label_very_high(self) -> None:
        step = ReasoningStep(description="Test", confidence=0.95)
        assert step.confidence_label == "very high"

    def test_confidence_label_high(self) -> None:
        step = ReasoningStep(description="Test", confidence=0.75)
        assert step.confidence_label == "high"

    def test_confidence_label_moderate(self) -> None:
        step = ReasoningStep(description="Test", confidence=0.55)
        assert step.confidence_label == "moderate"

    def test_confidence_label_low(self) -> None:
        step = ReasoningStep(description="Test", confidence=0.35)
        assert step.confidence_label == "low"

    def test_confidence_label_very_low(self) -> None:
        step = ReasoningStep(description="Test", confidence=0.1)
        assert step.confidence_label == "very low"

    def test_to_dict_structure(self) -> None:
        step = ReasoningStep(
            description="Check query relevance.",
            confidence=0.8,
            duration_ms=15.5,
            step_type="observation",
        )
        data = step.to_dict()
        assert data["description"] == "Check query relevance."
        assert data["confidence"] == 0.8
        assert data["duration_ms"] == 15.5
        assert data["step_type"] == "observation"
        assert "confidence_label" in data
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# ThoughtPanel — basic setup
# ---------------------------------------------------------------------------


class TestThoughtPanelInit:
    def test_empty_panel_has_zero_steps(self) -> None:
        panel = ThoughtPanel()
        assert panel.step_count == 0

    def test_custom_config(self) -> None:
        config = PanelConfig(title="My Panel", show_confidence=False)
        panel = ThoughtPanel(config)
        assert panel._config.title == "My Panel"

    def test_not_complete_initially(self) -> None:
        panel = ThoughtPanel()
        assert panel.is_complete is False


# ---------------------------------------------------------------------------
# Step management
# ---------------------------------------------------------------------------


class TestStepManagement:
    def test_add_step_object(self) -> None:
        panel = ThoughtPanel()
        step = ReasoningStep(description="Identified intent.")
        panel.add_step(step)
        assert panel.step_count == 1

    def test_add_shorthand(self) -> None:
        panel = ThoughtPanel()
        step = panel.add("Evaluated context.", confidence=0.9, duration_ms=10.0)
        assert panel.step_count == 1
        assert step.confidence == 0.9

    def test_multiple_steps(self) -> None:
        panel = ThoughtPanel()
        for i in range(5):
            panel.add(f"Step {i} description.")
        assert panel.step_count == 5

    def test_clear_removes_all_steps(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step one.")
        panel.add("Step two.")
        panel.clear()
        assert panel.step_count == 0
        assert panel.is_complete is False

    def test_complete_marks_panel(self) -> None:
        panel = ThoughtPanel()
        panel.add("Reasoning done.")
        panel.complete()
        assert panel.is_complete is True

    def test_steps_returns_list_copy(self) -> None:
        panel = ThoughtPanel()
        panel.add("Test step.")
        steps = panel.steps()
        steps.clear()  # Mutate returned list
        assert panel.step_count == 1  # Original unchanged


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestPanelProperties:
    def test_average_confidence_correct(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step 1.", confidence=0.8)
        panel.add("Step 2.", confidence=0.6)
        panel.add("Step 3.", confidence=1.0)
        expected = (0.8 + 0.6 + 1.0) / 3
        assert abs(panel.average_confidence - expected) < 1e-9

    def test_average_confidence_empty_panel(self) -> None:
        panel = ThoughtPanel()
        assert panel.average_confidence == 0.0

    def test_total_duration_ms_sums_correctly(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step 1.", duration_ms=10.0)
        panel.add("Step 2.", duration_ms=20.0)
        panel.add("Step 3.", duration_ms=5.0)
        assert panel.total_duration_ms == 35.0

    def test_total_duration_ms_none_when_no_durations(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step without duration.")
        assert panel.total_duration_ms is None


# ---------------------------------------------------------------------------
# Rendering — JSON
# ---------------------------------------------------------------------------


class TestRenderJSON:
    def test_json_render_produces_valid_json(self) -> None:
        panel = ThoughtPanel()
        panel.add("Analysed user request.", confidence=0.9, duration_ms=8.0)
        output = panel.render(output_format=PanelFormat.JSON)
        data = json.loads(output)
        assert "title" in data
        assert "steps" in data
        assert len(data["steps"]) == 1

    def test_json_collapsed_has_empty_steps(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step one.")
        output = panel.render(output_format=PanelFormat.JSON, collapsed=True)
        data = json.loads(output)
        assert data["collapsed"] is True
        assert data["steps"] == []

    def test_json_contains_step_count(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step A.")
        panel.add("Step B.")
        output = panel.render(output_format=PanelFormat.JSON)
        data = json.loads(output)
        assert data["step_count"] == 2


# ---------------------------------------------------------------------------
# Rendering — text
# ---------------------------------------------------------------------------


class TestRenderText:
    def test_text_contains_title(self) -> None:
        config = PanelConfig(title="Agent Thought Process")
        panel = ThoughtPanel(config)
        panel.add("Identify the request type.")
        output = panel.render(output_format=PanelFormat.TEXT)
        assert "Agent Thought Process" in output

    def test_text_collapsed_shows_collapsed_hint(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step.")
        output = panel.render(output_format=PanelFormat.TEXT, collapsed=True)
        assert "Collapsed" in output

    def test_text_includes_step_descriptions(self) -> None:
        panel = ThoughtPanel()
        panel.add("Determined the user needs a summary.")
        output = panel.render(output_format=PanelFormat.TEXT)
        assert "Determined the user needs a summary." in output

    def test_text_shows_confidence_by_default(self) -> None:
        panel = ThoughtPanel()
        panel.add("Verified fact.", confidence=0.75)
        output = panel.render(output_format=PanelFormat.TEXT)
        assert "75%" in output or "Confidence" in output

    def test_text_hides_confidence_when_disabled(self) -> None:
        config = PanelConfig(show_confidence=False)
        panel = ThoughtPanel(config)
        panel.add("Step.", confidence=0.75)
        output = panel.render(output_format=PanelFormat.TEXT)
        assert "75%" not in output


# ---------------------------------------------------------------------------
# Rendering — markdown
# ---------------------------------------------------------------------------


class TestRenderMarkdown:
    def test_markdown_contains_details_tag(self) -> None:
        panel = ThoughtPanel()
        panel.add("Observation step.")
        output = panel.render(output_format=PanelFormat.MARKDOWN)
        assert "<details" in output
        assert "</details>" in output

    def test_markdown_collapsed_uses_closed_details(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step.")
        output = panel.render(output_format=PanelFormat.MARKDOWN, collapsed=True)
        assert "<details>" in output or "<details\n>" in output or "<details>" in output
        assert "<details open>" not in output


# ---------------------------------------------------------------------------
# Max steps visible
# ---------------------------------------------------------------------------


class TestMaxStepsVisible:
    def test_max_steps_limits_visible_steps(self) -> None:
        config = PanelConfig(max_steps_visible=2)
        panel = ThoughtPanel(config)
        for i in range(5):
            panel.add(f"Step {i}.")
        output = panel.render(output_format=PanelFormat.TEXT)
        # Only first 2 steps should appear
        assert "Step 2." in output or "Step 1." in output
        # The hidden count should be mentioned
        assert "3 more" in output

    def test_to_dict_max_steps_limits_steps(self) -> None:
        config = PanelConfig(max_steps_visible=2)
        panel = ThoughtPanel(config)
        for i in range(5):
            panel.add(f"Step {i}.")
        data = panel.to_dict()
        assert len(data["steps"]) == 2


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------


class TestToDict:
    def test_to_dict_structure(self) -> None:
        panel = ThoughtPanel()
        panel.add("Reasoned about the query.")
        panel.complete()
        data = panel.to_dict()
        expected_keys = {
            "title", "collapsed", "step_count", "average_confidence",
            "total_duration_ms", "is_complete", "started_at", "completed_at", "steps"
        }
        assert expected_keys.issubset(data.keys())

    def test_to_dict_completed_at_set_after_complete(self) -> None:
        panel = ThoughtPanel()
        panel.add("Final step.")
        panel.complete()
        data = panel.to_dict()
        assert data["completed_at"] is not None

    def test_to_dict_completed_at_none_before_complete(self) -> None:
        panel = ThoughtPanel()
        panel.add("Step.")
        data = panel.to_dict()
        assert data["completed_at"] is None
