"""Disclosure subsystem — AI transparency statements and session reports.

Exports
-------
AIDisclosure
    Generate configurable AI disclosure statements from named templates.
DisclosureStatement
    Frozen rendered disclosure statement.
DisclosureTone
    Tone enum (FORMAL, FRIENDLY, CONCISE).
TransparencyReport
    Generate structured transparency reports from session statistics.
SessionStats
    Dataclass holding session-level statistics for reporting.
"""
from __future__ import annotations

from agent_sense.disclosure.ai_disclosure import (
    AIDisclosure,
    DisclosureStatement,
    DisclosureTone,
)
from agent_sense.disclosure.transparency import SessionStats, TransparencyReport

__all__ = [
    "AIDisclosure",
    "DisclosureStatement",
    "DisclosureTone",
    "TransparencyReport",
    "SessionStats",
]
