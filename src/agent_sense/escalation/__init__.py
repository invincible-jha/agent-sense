"""Escalation package — seamless human escalation protocol.

Provides:
- EscalationProtocol: configurable fallback chain from agent → supervisor → human
- ContextPackager: packages conversation context for human handoff
- SLATracker: tracks time-to-human metrics and SLA compliance
"""
from __future__ import annotations

from agent_sense.escalation.protocol import (
    EscalationLevel,
    EscalationProtocol,
    EscalationRecord,
    EscalationTrigger,
    EscalationTriggerConfig,
)
from agent_sense.escalation.context_packager import (
    ConversationTurn,
    ContextPackage,
    ContextPackager,
    DecisionRecord,
)
from agent_sense.escalation.sla_tracker import (
    SLAConfig,
    SLAStatus,
    SLATracker,
    TimeToHumanRecord,
)

__all__ = [
    # Protocol
    "EscalationLevel",
    "EscalationProtocol",
    "EscalationRecord",
    "EscalationTrigger",
    "EscalationTriggerConfig",
    # Context packager
    "ConversationTurn",
    "ContextPackage",
    "ContextPackager",
    "DecisionRecord",
    # SLA tracker
    "SLAConfig",
    "SLAStatus",
    "SLATracker",
    "TimeToHumanRecord",
]
