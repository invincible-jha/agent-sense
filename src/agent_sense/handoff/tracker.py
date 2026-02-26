"""Handoff tracker — manage the lifecycle of human agent handoff requests.

HandoffTracker maintains an in-memory registry of HandoffRecord objects.
Each record progresses through a defined status lifecycle:

    CREATED -> ASSIGNED -> IN_PROGRESS -> RESOLVED
                       \-> ESCALATED

Status transitions outside the allowed set raise TransitionError.
"""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum

from agent_sense.handoff.packager import HandoffPackage


class HandoffStatus(str, Enum):
    """Lifecycle states for a handoff request."""

    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


# Allowed transitions from each status.
_ALLOWED_TRANSITIONS: dict[HandoffStatus, frozenset[HandoffStatus]] = {
    HandoffStatus.CREATED: frozenset(
        {HandoffStatus.ASSIGNED, HandoffStatus.ESCALATED}
    ),
    HandoffStatus.ASSIGNED: frozenset(
        {HandoffStatus.IN_PROGRESS, HandoffStatus.ESCALATED}
    ),
    HandoffStatus.IN_PROGRESS: frozenset(
        {HandoffStatus.RESOLVED, HandoffStatus.ESCALATED}
    ),
    HandoffStatus.RESOLVED: frozenset(),
    HandoffStatus.ESCALATED: frozenset(),
}


class HandoffNotFoundError(KeyError):
    """Raised when a handoff ID does not exist in the tracker."""

    def __init__(self, handoff_id: str) -> None:
        super().__init__(f"Handoff {handoff_id!r} not found in tracker.")


class TransitionError(ValueError):
    """Raised when a status transition is not permitted."""

    def __init__(
        self, handoff_id: str, current: HandoffStatus, target: HandoffStatus
    ) -> None:
        super().__init__(
            f"Handoff {handoff_id!r} cannot transition from "
            f"{current.value!r} to {target.value!r}."
        )


@dataclass
class HandoffRecord:
    """Mutable record tracking a single handoff request over its lifetime.

    Attributes
    ----------
    handoff_id:
        Unique UUID string for this handoff.
    package:
        The HandoffPackage created at escalation time.
    status:
        Current lifecycle status.
    assigned_agent_id:
        ID of the human agent this was routed to (empty until assigned).
    created_at:
        UTC datetime when the record was created.
    updated_at:
        UTC datetime of the most recent status change.
    notes:
        Ordered list of timestamped notes added during processing.
    """

    handoff_id: str
    package: HandoffPackage
    status: HandoffStatus = HandoffStatus.CREATED
    assigned_agent_id: str = ""
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    notes: list[str] = field(default_factory=list)

    def is_terminal(self) -> bool:
        """Return True if the handoff has reached a terminal state."""
        return self.status in {HandoffStatus.RESOLVED, HandoffStatus.ESCALATED}


class HandoffTracker:
    """Track handoff request lifecycle in memory.

    Example
    -------
    >>> from agent_sense.handoff.packager import HandoffPackager
    >>> packager = HandoffPackager()
    >>> pkg = packager.package(summary="User cannot login.")
    >>> tracker = HandoffTracker()
    >>> record = tracker.create(pkg)
    >>> tracker.update_status(record.handoff_id, HandoffStatus.ASSIGNED, agent_id="a1")
    >>> tracker.list_pending()
    [...]
    """

    def __init__(self) -> None:
        self._records: dict[str, HandoffRecord] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        package: HandoffPackage,
        handoff_id: str | None = None,
    ) -> HandoffRecord:
        """Create and register a new HandoffRecord.

        Parameters
        ----------
        package:
            The HandoffPackage to track.
        handoff_id:
            Optional explicit ID. A UUID is generated when omitted.

        Returns
        -------
        HandoffRecord
            The newly created record in CREATED status.

        Raises
        ------
        ValueError
            If a record with ``handoff_id`` already exists.
        """
        record_id = handoff_id or str(uuid.uuid4())
        if record_id in self._records:
            raise ValueError(
                f"Handoff ID {record_id!r} already exists in the tracker."
            )
        record = HandoffRecord(handoff_id=record_id, package=package)
        self._records[record_id] = record
        return record

    def get(self, handoff_id: str) -> HandoffRecord:
        """Return the HandoffRecord for the given ID.

        Parameters
        ----------
        handoff_id:
            The unique handoff identifier.

        Returns
        -------
        HandoffRecord

        Raises
        ------
        HandoffNotFoundError
            If no record exists for ``handoff_id``.
        """
        try:
            return self._records[handoff_id]
        except KeyError:
            raise HandoffNotFoundError(handoff_id) from None

    def update_status(
        self,
        handoff_id: str,
        new_status: HandoffStatus,
        agent_id: str = "",
        note: str = "",
    ) -> HandoffRecord:
        """Transition a handoff to a new status.

        Parameters
        ----------
        handoff_id:
            The handoff to update.
        new_status:
            The target status. Must be an allowed transition from the current one.
        agent_id:
            If provided, updates ``assigned_agent_id`` on the record.
        note:
            Optional note to append to the record's notes list.

        Returns
        -------
        HandoffRecord
            The updated record.

        Raises
        ------
        HandoffNotFoundError
            If no record exists for ``handoff_id``.
        TransitionError
            If the requested transition is not permitted.
        """
        record = self.get(handoff_id)
        allowed = _ALLOWED_TRANSITIONS[record.status]
        if new_status not in allowed:
            raise TransitionError(handoff_id, record.status, new_status)

        record.status = new_status
        record.updated_at = datetime.datetime.now(datetime.timezone.utc)
        if agent_id:
            record.assigned_agent_id = agent_id
        if note:
            timestamp = record.updated_at.isoformat()
            record.notes.append(f"[{timestamp}] {note}")
        return record

    def add_note(self, handoff_id: str, note: str) -> HandoffRecord:
        """Append a timestamped note to a handoff record.

        Parameters
        ----------
        handoff_id:
            The handoff to annotate.
        note:
            The note text to append.

        Returns
        -------
        HandoffRecord

        Raises
        ------
        HandoffNotFoundError
            If no record exists for ``handoff_id``.
        """
        record = self.get(handoff_id)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record.notes.append(f"[{timestamp}] {note}")
        record.updated_at = datetime.datetime.now(datetime.timezone.utc)
        return record

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_pending(self) -> list[HandoffRecord]:
        """Return all non-terminal handoff records.

        Returns
        -------
        list[HandoffRecord]
            Records with status CREATED, ASSIGNED, or IN_PROGRESS, ordered
            by ``created_at`` ascending.
        """
        pending = [r for r in self._records.values() if not r.is_terminal()]
        pending.sort(key=lambda r: r.created_at)
        return pending

    def list_by_status(self, status: HandoffStatus) -> list[HandoffRecord]:
        """Return all records matching the given status.

        Parameters
        ----------
        status:
            The HandoffStatus to filter by.

        Returns
        -------
        list[HandoffRecord]
            Matching records ordered by ``created_at`` ascending.
        """
        matches = [r for r in self._records.values() if r.status == status]
        matches.sort(key=lambda r: r.created_at)
        return matches

    def list_by_agent(self, agent_id: str) -> list[HandoffRecord]:
        """Return all records assigned to a specific agent.

        Parameters
        ----------
        agent_id:
            The agent ID to filter by.

        Returns
        -------
        list[HandoffRecord]
            Matching records ordered by ``created_at`` ascending.
        """
        matches = [
            r for r in self._records.values() if r.assigned_agent_id == agent_id
        ]
        matches.sort(key=lambda r: r.created_at)
        return matches

    def total_count(self) -> int:
        """Return the total number of tracked handoffs."""
        return len(self._records)
