"""Universal AI transparency indicators — Phase 6E of the AumOS implementation.

This package provides three core transparency primitives and a multi-format
renderer for surfacing AI behaviour to end users:

ConfidenceIndicator
    Structured confidence measurement with five-tier level, raw score,
    human-readable reasoning, and a factor breakdown.

AIDisclosureCard
    Immutable disclosure card describing an AI agent's identity, model,
    capabilities, limitations, and data-handling practices.

HandoffSignal
    Structured escalation signal produced when an agent cannot or should
    not continue handling a request.

IndicatorRenderer
    Renders all three primitives in HTML, TEXT, JSON, and MARKDOWN formats.
    HTML output is WCAG 2.1 AA compliant (ARIA attributes, 4.5:1 contrast).

Example
-------
>>> from agent_sense.indicators import from_score, IndicatorRenderer, RenderFormat
>>> indicator = from_score(0.72, reasoning="strong keyword overlap")
>>> renderer = IndicatorRenderer()
>>> print(renderer.render_confidence(indicator, RenderFormat.TEXT))
Confidence: High (72%)
[##############------] 72%
Reasoning: strong keyword overlap
"""
from __future__ import annotations

from agent_sense.indicators.confidence import (
    ConfidenceIndicator,
    ConfidenceLevel,
    from_score,
)
from agent_sense.indicators.disclosure import (
    AIDisclosureCard,
    DisclosureLevel,
    build_disclosure,
)
from agent_sense.indicators.handoff_signal import (
    HandoffReason,
    HandoffSignal,
)
from agent_sense.indicators.renderers import (
    IndicatorRenderer,
    RenderFormat,
)

__all__ = [
    # Confidence
    "ConfidenceIndicator",
    "ConfidenceLevel",
    "from_score",
    # Disclosure
    "AIDisclosureCard",
    "DisclosureLevel",
    "build_disclosure",
    # Handoff signal
    "HandoffReason",
    "HandoffSignal",
    # Renderers
    "IndicatorRenderer",
    "RenderFormat",
]
