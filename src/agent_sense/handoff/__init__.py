"""Handoff subsystem — package, route, and track escalations to human agents.

Exports
-------
HandoffPackage
    Frozen snapshot of conversation state for a human agent.
HandoffPackager
    Assemble HandoffPackage instances from conversation state.
UrgencyLevel
    Urgency classification enum (LOW, MEDIUM, HIGH, CRITICAL).
HumanAgent
    Dataclass representing a human agent available for assignment.
HandoffRouter
    Route HandoffPackage to the best available human agent.
NoAvailableAgentError
    Raised when no agent has capacity.
HandoffStatus
    Lifecycle states (CREATED, ASSIGNED, IN_PROGRESS, RESOLVED, ESCALATED).
HandoffRecord
    Mutable tracking record for a single handoff lifecycle.
HandoffTracker
    In-memory registry for handoff records.
HandoffNotFoundError
    Raised when a handoff ID is not in the tracker.
TransitionError
    Raised when a status transition is not permitted.
"""
from __future__ import annotations

from agent_sense.handoff.packager import HandoffPackage, HandoffPackager, UrgencyLevel
from agent_sense.handoff.router import (
    HandoffRouter,
    HumanAgent,
    NoAvailableAgentError,
)
from agent_sense.handoff.tracker import (
    HandoffNotFoundError,
    HandoffRecord,
    HandoffStatus,
    HandoffTracker,
    TransitionError,
)

__all__ = [
    "HandoffPackage",
    "HandoffPackager",
    "UrgencyLevel",
    "HumanAgent",
    "HandoffRouter",
    "NoAvailableAgentError",
    "HandoffStatus",
    "HandoffRecord",
    "HandoffTracker",
    "HandoffNotFoundError",
    "TransitionError",
]
