"""Tests for agent_sense.escalation.context_packager — ContextPackager."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_sense.escalation.context_packager import (
    ContextPackage,
    ContextPackager,
    ConversationTurn,
    DecisionRecord,
)


# ---------------------------------------------------------------------------
# ConversationTurn
# ---------------------------------------------------------------------------


class TestConversationTurn:
    def test_construction(self) -> None:
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.turn_index == 0

    def test_frozen(self) -> None:
        turn = ConversationTurn(role="user", content="Hello")
        with pytest.raises((TypeError, AttributeError)):
            turn.role = "assistant"  # type: ignore[misc]

    def test_explicit_timestamp(self) -> None:
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        turn = ConversationTurn(role="assistant", content="Hi", timestamp=ts)
        assert turn.timestamp == ts


# ---------------------------------------------------------------------------
# DecisionRecord
# ---------------------------------------------------------------------------


class TestDecisionRecord:
    def test_defaults(self) -> None:
        record = DecisionRecord(
            decision="use_tool", reasoning="Needs live data"
        )
        assert record.confidence == 1.0

    def test_explicit(self) -> None:
        record = DecisionRecord(
            decision="refuse",
            reasoning="Out of scope",
            confidence=0.95,
        )
        assert record.decision == "refuse"
        assert record.confidence == pytest.approx(0.95)

    def test_frozen(self) -> None:
        record = DecisionRecord(decision="d", reasoning="r")
        with pytest.raises((TypeError, AttributeError)):
            record.decision = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ContextPackager
# ---------------------------------------------------------------------------


def _make_turns(count: int) -> list[ConversationTurn]:
    turns = []
    for i in range(count):
        role = "user" if i % 2 == 0 else "assistant"
        turns.append(ConversationTurn(role=role, content=f"Message {i}", turn_index=i))
    return turns


def _make_decisions(count: int) -> list[DecisionRecord]:
    return [
        DecisionRecord(
            decision=f"decision_{i}",
            reasoning=f"Because of reason {i}",
            confidence=0.8,
        )
        for i in range(count)
    ]


class TestContextPackagerBasic:
    def test_package_creates_valid_object(self) -> None:
        packager = ContextPackager(session_id="sess-001")
        turns = _make_turns(3)
        pkg = packager.package(
            turns=turns,
            decisions=[],
            confidence_score=0.25,
            escalation_reason="Low confidence",
        )
        assert isinstance(pkg, ContextPackage)
        assert pkg.session_id == "sess-001"

    def test_package_id_is_uuid(self) -> None:
        packager = ContextPackager(session_id="s1")
        pkg = packager.package(
            turns=[],
            decisions=[],
            confidence_score=0.5,
            escalation_reason="test",
        )
        assert len(pkg.package_id) == 36

    def test_package_ids_unique(self) -> None:
        packager = ContextPackager(session_id="s1")
        p1 = packager.package(
            turns=[], decisions=[], confidence_score=0.5, escalation_reason="r"
        )
        p2 = packager.package(
            turns=[], decisions=[], confidence_score=0.5, escalation_reason="r"
        )
        assert p1.package_id != p2.package_id

    def test_confidence_label_low(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[], decisions=[], confidence_score=0.20, escalation_reason="r"
        )
        assert pkg.confidence_label == "Low Confidence"

    def test_confidence_label_medium(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[], decisions=[], confidence_score=0.55, escalation_reason="r"
        )
        assert pkg.confidence_label == "Medium Confidence"

    def test_confidence_label_high(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[], decisions=[], confidence_score=0.80, escalation_reason="r"
        )
        assert pkg.confidence_label == "High Confidence"


class TestContextPackagerTurnTruncation:
    def test_turns_truncated_to_max(self) -> None:
        packager = ContextPackager(session_id="s", max_turns=5)
        turns = _make_turns(20)
        pkg = packager.package(
            turns=turns,
            decisions=[],
            confidence_score=0.3,
            escalation_reason="r",
        )
        assert len(pkg.conversation_turns) == 5

    def test_most_recent_turns_kept(self) -> None:
        packager = ContextPackager(session_id="s", max_turns=3)
        turns = _make_turns(10)
        pkg = packager.package(
            turns=turns,
            decisions=[],
            confidence_score=0.3,
            escalation_reason="r",
        )
        # The last 3 turns (indices 7, 8, 9) should be present
        contents = [t.content for t in pkg.conversation_turns]
        assert "Message 9" in contents
        assert "Message 7" in contents
        assert "Message 0" not in contents

    def test_fewer_turns_than_max_all_kept(self) -> None:
        packager = ContextPackager(session_id="s", max_turns=10)
        turns = _make_turns(4)
        pkg = packager.package(
            turns=turns,
            decisions=[],
            confidence_score=0.5,
            escalation_reason="r",
        )
        assert len(pkg.conversation_turns) == 4


class TestContextPackagerDecisions:
    def test_decisions_preserved(self) -> None:
        packager = ContextPackager(session_id="s")
        decisions = _make_decisions(3)
        pkg = packager.package(
            turns=[],
            decisions=decisions,
            confidence_score=0.5,
            escalation_reason="r",
        )
        assert len(pkg.key_decisions) == 3
        assert pkg.key_decisions[0].decision == "decision_0"


class TestContextPackagerSummary:
    def test_explicit_summary_used(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=_make_turns(2),
            decisions=[],
            confidence_score=0.3,
            escalation_reason="r",
            summary="This is the explicit summary.",
        )
        assert pkg.summary == "This is the explicit summary."

    def test_auto_summary_generated_when_empty(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=_make_turns(3),
            decisions=[],
            confidence_score=0.25,
            escalation_reason="Low confidence",
        )
        assert len(pkg.summary) > 10
        assert "Low confidence" in pkg.summary or "low confidence" in pkg.summary.lower()


class TestContextPackagerRecommendations:
    def test_explicit_recommendations_used(self) -> None:
        packager = ContextPackager(session_id="s")
        recs = ["Check the policy", "Call the user back"]
        pkg = packager.package(
            turns=[],
            decisions=[],
            confidence_score=0.5,
            escalation_reason="r",
            recommendations=recs,
        )
        assert pkg.recommendations == recs

    def test_default_recommendations_generated_low_confidence(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[],
            decisions=[],
            confidence_score=0.20,
            escalation_reason="r",
        )
        assert len(pkg.recommendations) >= 1

    def test_default_recommendations_generated_medium_confidence(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[],
            decisions=[],
            confidence_score=0.60,
            escalation_reason="r",
        )
        assert len(pkg.recommendations) >= 1


class TestContextPackageToDict:
    def test_to_dict_contains_all_keys(self) -> None:
        packager = ContextPackager(session_id="sess-test")
        pkg = packager.package(
            turns=_make_turns(2),
            decisions=_make_decisions(1),
            confidence_score=0.30,
            escalation_reason="Low confidence triggered",
        )
        d = pkg.to_dict()
        expected_keys = {
            "package_id", "created_at", "session_id", "summary",
            "conversation_turns", "key_decisions", "confidence_score",
            "confidence_label", "escalation_reason", "recommendations",
            "metadata",
        }
        assert expected_keys.issubset(set(d.keys()))

    def test_to_dict_turns_serialised(self) -> None:
        packager = ContextPackager(session_id="s")
        turns = [ConversationTurn(role="user", content="test", turn_index=0)]
        pkg = packager.package(
            turns=turns,
            decisions=[],
            confidence_score=0.5,
            escalation_reason="r",
        )
        d = pkg.to_dict()
        assert len(d["conversation_turns"]) == 1  # type: ignore[arg-type]
        assert d["conversation_turns"][0]["role"] == "user"  # type: ignore[index]

    def test_metadata_passed_through(self) -> None:
        packager = ContextPackager(session_id="s")
        pkg = packager.package(
            turns=[],
            decisions=[],
            confidence_score=0.5,
            escalation_reason="r",
            metadata={"queue": "priority-1"},
        )
        assert pkg.metadata["queue"] == "priority-1"
        d = pkg.to_dict()
        assert d["metadata"]["queue"] == "priority-1"  # type: ignore[index]
