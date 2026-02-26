"""agent-sense — Human-agent interaction SDK with accessibility and dialogue management.

Public API
----------
The stable public surface is everything exported from this module.
Anything inside submodules not re-exported here is considered private
and may change without notice.

Example
-------
>>> import agent_sense
>>> agent_sense.__version__
'0.1.0'
"""
from __future__ import annotations

__version__: str = "0.1.0"

# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------
from agent_sense.confidence.annotator import (
    AnnotatedResponse,
    ConfidenceAnnotator,
    ConfidenceLevel,
)
from agent_sense.confidence.calibrator import ConfidenceCalibrator
from agent_sense.confidence.signals import (
    ConfidenceSignal,
    ExtractedSignals,
    SignalExtractor,
)

# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------
from agent_sense.context.detector import ContextDetector, DeviceType, NetworkQuality
from agent_sense.context.expertise import ExpertiseEstimator, ExpertiseLevel
from agent_sense.context.situation import (
    AccessibilityNeed,
    SituationAssessor,
    SituationVector,
)
from agent_sense.context.adapters.web import WebContextAdapter
from agent_sense.context.adapters.mobile import MobileContextAdapter
from agent_sense.context.adapters.voice import VoiceContextAdapter

# ---------------------------------------------------------------------------
# Handoff
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
from agent_sense.accessibility.wcag import WCAGChecker, WCAGCriterion, WCAGLevel, WCAGViolation
from agent_sense.accessibility.simplifier import TextSimplifier, flesch_kincaid_grade
from agent_sense.accessibility.screen_reader import ScreenReaderOptimizer

# ---------------------------------------------------------------------------
# Disclosure
# ---------------------------------------------------------------------------
from agent_sense.disclosure.ai_disclosure import (
    AIDisclosure,
    DisclosureStatement,
    DisclosureTone,
)
from agent_sense.disclosure.transparency import SessionStats, TransparencyReport

# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------
from agent_sense.suggestions.engine import (
    Suggestion,
    SuggestionCategory,
    SuggestionEngine,
)
from agent_sense.suggestions.ranker import RankedSuggestion, SuggestionRanker

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
from agent_sense.middleware.sense_middleware import InteractionResult, SenseMiddleware

# ---------------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------------
from agent_sense.plugins.registry import PluginRegistry

__all__ = [
    "__version__",
    # Confidence
    "AnnotatedResponse",
    "ConfidenceAnnotator",
    "ConfidenceLevel",
    "ConfidenceCalibrator",
    "ConfidenceSignal",
    "ExtractedSignals",
    "SignalExtractor",
    # Context
    "ContextDetector",
    "DeviceType",
    "NetworkQuality",
    "ExpertiseEstimator",
    "ExpertiseLevel",
    "AccessibilityNeed",
    "SituationAssessor",
    "SituationVector",
    "WebContextAdapter",
    "MobileContextAdapter",
    "VoiceContextAdapter",
    # Handoff
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
    # Accessibility
    "WCAGChecker",
    "WCAGCriterion",
    "WCAGLevel",
    "WCAGViolation",
    "TextSimplifier",
    "flesch_kincaid_grade",
    "ScreenReaderOptimizer",
    # Disclosure
    "AIDisclosure",
    "DisclosureStatement",
    "DisclosureTone",
    "TransparencyReport",
    "SessionStats",
    # Suggestions
    "Suggestion",
    "SuggestionCategory",
    "SuggestionEngine",
    "RankedSuggestion",
    "SuggestionRanker",
    # Middleware
    "SenseMiddleware",
    "InteractionResult",
    # Plugins
    "PluginRegistry",
]
