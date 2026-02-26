"""Tests for agent_sense.disclosure.transparency."""
from __future__ import annotations

import pytest

from agent_sense.disclosure.transparency import SessionStats, TransparencyReport


def _make_session_stats(**kwargs: object) -> SessionStats:
    defaults: dict[str, object] = {
        "session_id": "session-001",
        "total_turns": 10,
        "agent_turns": 8,
        "high_confidence_turns": 5,
        "medium_confidence_turns": 2,
        "low_confidence_turns": 1,
        "handoff_occurred": False,
    }
    defaults.update(kwargs)
    return SessionStats(**defaults)  # type: ignore[arg-type]


class TestTransparencyReportGenerate:
    def test_generate_returns_dict(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats())
        assert isinstance(result, dict)

    def test_generate_includes_session_id(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats(session_id="my-session"))
        assert result["session_id"] == "my-session"

    def test_generate_includes_interaction_summary(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats())
        assert "interaction_summary" in result

    def test_generate_includes_confidence_breakdown(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats())
        assert "confidence_breakdown" in result

    def test_generate_includes_handoff_info(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats(handoff_occurred=True, handoff_reason="Test"))
        assert "handoff" in result

    def test_generate_includes_report_generated_at(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats())
        assert "report_generated_at" in result

    def test_generate_no_handoff(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats(handoff_occurred=False))
        assert result is not None

    def test_generate_with_handoff(self) -> None:
        tr = TransparencyReport()
        result = tr.generate(_make_session_stats(handoff_occurred=True, handoff_reason="User requested"))
        assert result is not None


class TestTransparencyReportGenerateTextSummary:
    def test_returns_string(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(_make_session_stats())
        assert isinstance(result, str)

    def test_includes_session_id(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(_make_session_stats(session_id="test-session-abc"))
        assert "test-session-abc" in result

    def test_includes_turn_count(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(_make_session_stats(total_turns=10))
        assert "10" in result

    def test_handoff_mention_when_occurred(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(_make_session_stats(handoff_occurred=True))
        assert "Yes" in result or "handoff" in result.lower()

    def test_no_handoff_mention(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(_make_session_stats(handoff_occurred=False))
        assert isinstance(result, str)

    def test_confidence_breakdown_included(self) -> None:
        tr = TransparencyReport()
        result = tr.generate_text_summary(
            _make_session_stats(high_confidence_turns=5, low_confidence_turns=2)
        )
        assert "HIGH" in result or "5" in result


class TestSessionStats:
    def test_default_values(self) -> None:
        ss = SessionStats(session_id="s1")
        assert ss.total_turns == 0
        assert ss.handoff_occurred is False

    def test_custom_values(self) -> None:
        ss = SessionStats(session_id="s2", total_turns=5, handoff_occurred=True)
        assert ss.total_turns == 5
        assert ss.handoff_occurred is True

    def test_disclosures_shown_default_empty(self) -> None:
        ss = SessionStats(session_id="s3")
        assert ss.disclosures_shown == []
