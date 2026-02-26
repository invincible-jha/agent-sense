"""Tests for agent_sense.handoff.tracker."""
from __future__ import annotations

import pytest

from agent_sense.handoff.packager import HandoffPackager
from agent_sense.handoff.tracker import (
    HandoffNotFoundError,
    HandoffStatus,
    HandoffTracker,
    TransitionError,
)


def _make_package(summary: str = "User needs human support") -> object:
    packager = HandoffPackager(session_id="test-session-001")
    return packager.package(summary=summary)


class TestHandoffTrackerCreate:
    def test_create_returns_record(self) -> None:
        tracker = HandoffTracker()
        pkg = _make_package()
        record = tracker.create(pkg)
        assert record is not None

    def test_record_has_handoff_id(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        assert record.handoff_id != ""

    def test_record_initial_status_is_created(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        assert record.status == HandoffStatus.CREATED

    def test_custom_handoff_id(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package(), handoff_id="custom-id-001")
        assert record.handoff_id == "custom-id-001"

    def test_total_count_increases(self) -> None:
        tracker = HandoffTracker()
        assert tracker.total_count() == 0
        tracker.create(_make_package())
        assert tracker.total_count() == 1
        tracker.create(_make_package())
        assert tracker.total_count() == 2


class TestHandoffTrackerGet:
    def test_get_existing_record(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        retrieved = tracker.get(record.handoff_id)
        assert retrieved.handoff_id == record.handoff_id

    def test_get_nonexistent_raises(self) -> None:
        tracker = HandoffTracker()
        with pytest.raises(HandoffNotFoundError):
            tracker.get("nonexistent-id")


class TestHandoffTrackerUpdateStatus:
    def test_update_to_assigned(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        tracker.update_status(record.handoff_id, HandoffStatus.ASSIGNED, agent_id="agent-1")
        updated = tracker.get(record.handoff_id)
        assert updated.status == HandoffStatus.ASSIGNED
        assert updated.assigned_agent_id == "agent-1"

    def test_invalid_transition_raises(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        # Can't go directly from CREATED to RESOLVED
        with pytest.raises(TransitionError):
            tracker.update_status(record.handoff_id, HandoffStatus.RESOLVED)

    def test_update_nonexistent_raises(self) -> None:
        tracker = HandoffTracker()
        with pytest.raises(HandoffNotFoundError):
            tracker.update_status("nonexistent", HandoffStatus.ASSIGNED)

    def test_full_lifecycle(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        tracker.update_status(record.handoff_id, HandoffStatus.ASSIGNED, agent_id="a1")
        tracker.update_status(record.handoff_id, HandoffStatus.IN_PROGRESS)
        tracker.update_status(record.handoff_id, HandoffStatus.RESOLVED)
        final = tracker.get(record.handoff_id)
        assert final.status == HandoffStatus.RESOLVED


class TestHandoffTrackerAddNote:
    def test_add_note_to_record(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        tracker.add_note(record.handoff_id, "Customer is frustrated")
        updated = tracker.get(record.handoff_id)
        assert any("frustrated" in note for note in updated.notes)

    def test_add_note_nonexistent_raises(self) -> None:
        tracker = HandoffTracker()
        with pytest.raises(HandoffNotFoundError):
            tracker.add_note("nonexistent", "test note")


class TestHandoffTrackerListing:
    def test_list_pending_returns_created_records(self) -> None:
        tracker = HandoffTracker()
        tracker.create(_make_package())
        pending = tracker.list_pending()
        assert len(pending) >= 1

    def test_list_by_status_created(self) -> None:
        tracker = HandoffTracker()
        tracker.create(_make_package())
        records = tracker.list_by_status(HandoffStatus.CREATED)
        assert len(records) >= 1

    def test_list_by_status_empty_for_resolved(self) -> None:
        tracker = HandoffTracker()
        tracker.create(_make_package())
        records = tracker.list_by_status(HandoffStatus.RESOLVED)
        assert records == []

    def test_list_by_agent_filters_correctly(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        tracker.update_status(record.handoff_id, HandoffStatus.ASSIGNED, agent_id="agent-xyz")
        by_agent = tracker.list_by_agent("agent-xyz")
        assert len(by_agent) == 1

    def test_list_by_agent_empty_for_wrong_agent(self) -> None:
        tracker = HandoffTracker()
        record = tracker.create(_make_package())
        tracker.update_status(record.handoff_id, HandoffStatus.ASSIGNED, agent_id="agent-xyz")
        by_agent = tracker.list_by_agent("other-agent")
        assert by_agent == []
