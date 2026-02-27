"""UI components package for agent-sense.

Provides confidence-aware UI components and scoring utilities for
rendering agent confidence in user-facing interfaces.
"""
from __future__ import annotations

from agent_sense.components.confidence import (
    ConfidenceLevel,
    ConfidenceUIIndicator,
    EscalationThreshold,
    RenderMetadata,
    build_ui_indicator,
)
from agent_sense.components.confidence_scorer import (
    ConfidenceScorer,
    ScorerMetadata,
)

__all__ = [
    "ConfidenceLevel",
    "ConfidenceUIIndicator",
    "EscalationThreshold",
    "RenderMetadata",
    "build_ui_indicator",
    "ConfidenceScorer",
    "ScorerMetadata",
]
