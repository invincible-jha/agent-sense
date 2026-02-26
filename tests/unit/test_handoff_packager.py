"""Tests for agent_sense.handoff.packager."""
from __future__ import annotations

import pytest

from agent_sense.handoff.packager import HandoffPackager, UrgencyLevel


class TestHandoffPackager:
    def test_package_returns_object(self) -> None:
        pk = HandoffPackager(session_id="session-001")
        pkg = pk.package(summary="User needs help")
        assert pkg is not None

    def test_package_summary_stored(self) -> None:
        pk = HandoffPackager(session_id="session-001")
        pkg = pk.package(summary="Test summary")
        assert pkg.summary == "Test summary"

    def test_package_session_id_stored(self) -> None:
        pk = HandoffPackager(session_id="session-abc")
        pkg = pk.package(summary="Test")
        assert pkg.session_id == "session-abc"

    def test_package_default_urgency_medium(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test")
        assert pkg.urgency == UrgencyLevel.MEDIUM

    def test_package_custom_urgency(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Urgent!", urgency=UrgencyLevel.HIGH)
        assert pkg.urgency == UrgencyLevel.HIGH

    def test_package_default_urgency_from_init(self) -> None:
        pk = HandoffPackager(session_id="s1", default_urgency=UrgencyLevel.LOW)
        pkg = pk.package(summary="Test")
        assert pkg.urgency == UrgencyLevel.LOW

    def test_package_key_facts_stored(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test", key_facts=["User frustrated", "Third attempt"])
        assert "User frustrated" in pkg.key_facts

    def test_package_unresolved_questions_stored(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test", unresolved_questions=["What is their account type?"])
        assert "What is their account type?" in pkg.unresolved_questions

    def test_package_attempted_actions_stored(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test", attempted_actions=["Reset password"])
        assert "Reset password" in pkg.attempted_actions

    def test_package_metadata_stored(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test", metadata={"priority": "high"})
        assert pkg.metadata["priority"] == "high"

    def test_package_has_timestamp(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test")
        assert pkg.timestamp is not None

    def test_package_empty_key_facts_default(self) -> None:
        pk = HandoffPackager(session_id="s1")
        pkg = pk.package(summary="Test")
        assert pkg.key_facts == []

    def test_package_empty_session_id(self) -> None:
        pk = HandoffPackager()
        pkg = pk.package(summary="Test")
        assert pkg is not None
