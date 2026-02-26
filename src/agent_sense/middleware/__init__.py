"""Middleware subsystem — wrap agent interactions with the full sense stack.

Exports
-------
SenseMiddleware
    Orchestrates confidence annotation, context detection, disclosure, and
    suggestions for each conversational turn.
InteractionResult
    Dataclass holding the enriched output of a single processed turn.
"""
from __future__ import annotations

from agent_sense.middleware.sense_middleware import InteractionResult, SenseMiddleware

__all__ = [
    "SenseMiddleware",
    "InteractionResult",
]
