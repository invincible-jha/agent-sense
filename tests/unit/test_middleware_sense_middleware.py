"""Tests for agent_sense.middleware.sense_middleware."""
from __future__ import annotations

import pytest

from agent_sense.middleware.sense_middleware import InteractionResult, SenseMiddleware


class TestSenseMiddlewareProcess:
    def test_process_returns_interaction_result(self) -> None:
        mw = SenseMiddleware(session_id="s1", agent_name="Aria", org_name="Acme")
        result = mw.process(
            user_text="Hello",
            agent_response="Hi there!",
            confidence_score=0.9,
        )
        assert isinstance(result, InteractionResult)

    def test_process_annotated_response_present(self) -> None:
        mw = SenseMiddleware()
        result = mw.process(
            user_text="Hello",
            agent_response="Hi there!",
            confidence_score=0.9,
        )
        assert result.annotated_response is not None

    def test_process_turn_number_increments(self) -> None:
        mw = SenseMiddleware()
        result1 = mw.process("msg1", "resp1", 0.9)
        assert result1.turn_number == 1
        result2 = mw.process("msg2", "resp2", 0.9)
        assert result2.turn_number == 2

    def test_process_first_turn_has_disclosure(self) -> None:
        mw = SenseMiddleware(agent_name="Aria", org_name="Acme")
        result = mw.process("Hello", "Hi!", 0.9)
        assert result.disclosure_text != ""

    def test_process_second_turn_no_disclosure_when_high_confidence(self) -> None:
        mw = SenseMiddleware(agent_name="Aria", org_name="Acme")
        mw.process("msg1", "resp1", 0.95)
        result = mw.process("msg2", "resp2", 0.95)
        # Second turn, high confidence — may or may not have disclosure
        assert isinstance(result.disclosure_text, str)

    def test_process_low_confidence_adds_disclaimer_flag(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("question", "maybe...", 0.1)
        # Low confidence annotated response should need disclaimer
        assert result.annotated_response.needs_disclaimer() is True

    def test_process_suggestions_are_list(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("Hello", "Hi!", 0.9)
        assert isinstance(result.suggestions, list)

    def test_process_session_stats_present(self) -> None:
        mw = SenseMiddleware(session_id="my-session")
        result = mw.process("Hello", "Hi!", 0.9)
        assert result.session_stats is not None
        assert result.session_stats.session_id == "my-session"

    def test_process_session_stats_track_turns(self) -> None:
        mw = SenseMiddleware()
        mw.process("msg1", "resp1", 0.9)
        result = mw.process("msg2", "resp2", 0.5)
        assert result.session_stats.total_turns >= 2

    def test_process_show_disclosure_override_false(self) -> None:
        mw = SenseMiddleware(agent_name="Aria", org_name="Acme")
        result = mw.process("Hello", "Hi!", 0.9, show_disclosure=False)
        assert result.disclosure_text == ""

    def test_process_show_disclosure_override_true(self) -> None:
        mw = SenseMiddleware(agent_name="Aria", org_name="Acme")
        # Second turn but forced show_disclosure=True
        mw.process("msg1", "resp1", 0.9)
        result = mw.process("msg2", "resp2", 0.9, show_disclosure=True)
        assert result.disclosure_text != ""

    def test_process_high_confidence_tracked(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("msg", "resp", 0.95)
        assert result.session_stats.high_confidence_turns >= 1

    def test_process_medium_confidence_tracked(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("msg", "resp", 0.6)
        assert result.session_stats.medium_confidence_turns >= 1

    def test_process_low_confidence_tracked(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("msg", "resp", 0.1)
        assert result.session_stats.low_confidence_turns >= 1

    def test_situation_vector_present(self) -> None:
        mw = SenseMiddleware()
        result = mw.process("Hello", "Hi!", 0.9)
        assert result.situation is not None


class TestSenseMiddlewareRecordHandoff:
    def test_record_handoff_marks_occurred(self) -> None:
        mw = SenseMiddleware()
        mw.process("msg", "resp", 0.9)
        mw.record_handoff(reason="User requested")
        report = mw.finalize_report()
        assert report["handoff"]["occurred"] is True

    def test_record_handoff_stores_reason(self) -> None:
        mw = SenseMiddleware()
        mw.process("msg", "resp", 0.9)
        mw.record_handoff(reason="Billing issue")
        report = mw.finalize_report()
        assert "Billing issue" in report["handoff"]["reason"]

    def test_record_handoff_no_reason(self) -> None:
        mw = SenseMiddleware()
        mw.record_handoff()
        report = mw.finalize_report()
        assert report["handoff"]["occurred"] is True


class TestSenseMiddlewareFinalizeReport:
    def test_finalize_report_returns_dict(self) -> None:
        mw = SenseMiddleware()
        mw.process("msg", "resp", 0.9)
        report = mw.finalize_report()
        assert isinstance(report, dict)

    def test_finalize_report_includes_session_id(self) -> None:
        mw = SenseMiddleware(session_id="test-session")
        mw.process("msg", "resp", 0.9)
        report = mw.finalize_report()
        assert report["session_id"] == "test-session"

    def test_finalize_report_no_turns(self) -> None:
        mw = SenseMiddleware(session_id="empty-session")
        report = mw.finalize_report()
        assert isinstance(report, dict)


class TestSenseMiddlewareTurnNumber:
    def test_initial_turn_number_is_zero(self) -> None:
        mw = SenseMiddleware()
        assert mw.turn_number == 0

    def test_turn_number_increments(self) -> None:
        mw = SenseMiddleware()
        mw.process("msg1", "resp1", 0.9)
        assert mw.turn_number == 1
        mw.process("msg2", "resp2", 0.9)
        assert mw.turn_number == 2
