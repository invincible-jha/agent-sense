#!/usr/bin/env python3
"""Example: Human Handoff Management

Demonstrates packaging context for handoff, routing to available
human agents, and tracking handoff status transitions.

Usage:
    python examples/03_handoff_management.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    HandoffPackage,
    HandoffPackager,
    HandoffRecord,
    HandoffRouter,
    HandoffStatus,
    HandoffTracker,
    HumanAgent,
    NoAvailableAgentError,
    UrgencyLevel,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: Package conversation context for handoff
    packager = HandoffPackager()
    package: HandoffPackage = packager.package(
        session_id="session-007",
        summary="User cannot reset their MFA device and is locked out.",
        conversation_history=[
            {"role": "user", "content": "I can't log in — MFA is broken."},
            {"role": "assistant", "content": "I've tried the standard recovery steps."},
        ],
        urgency=UrgencyLevel.HIGH,
        reason="Security account issue requiring human verification.",
    )
    print(f"Handoff package: urgency={package.urgency.value}")
    print(f"  Summary: {package.summary[:60]}")

    # Step 2: Route to an available human agent
    router = HandoffRouter()
    agents = [
        HumanAgent(agent_id="human-alice", skills=["security", "mfa"], available=True),
        HumanAgent(agent_id="human-bob", skills=["billing"], available=True),
        HumanAgent(agent_id="human-carol", skills=["security"], available=False),
    ]
    for agent in agents:
        router.register(agent)

    try:
        assigned = router.route(package, required_skills=["security"])
        print(f"\nAssigned to: {assigned.agent_id} (skills={assigned.skills})")
    except NoAvailableAgentError as error:
        print(f"No agent available: {error}")

    # Step 3: Track handoff status transitions
    tracker = HandoffTracker()
    record: HandoffRecord = tracker.create(package=package, assigned_to=assigned.agent_id)
    print(f"\nHandoff record: {record.handoff_id}")
    print(f"  Status: {record.status.value}")

    tracker.transition(record.handoff_id, HandoffStatus.ACCEPTED)
    tracker.transition(record.handoff_id, HandoffStatus.RESOLVED)
    final = tracker.get(record.handoff_id)
    print(f"  Final status: {final.status.value}")
    print(f"  Open handoffs: {tracker.count_open()}")


if __name__ == "__main__":
    main()
