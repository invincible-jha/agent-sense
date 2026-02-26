"""Confidence annotation, thresholds, disclaimers, display, calibration, and signals.

Exports
-------
ConfidenceLevel
    Enum of confidence tiers (HIGH, MEDIUM, LOW, UNKNOWN).
AnnotatedResponse
    Dataclass pairing a response with its confidence annotation.
ConfidenceAnnotator
    Annotate responses with a ConfidenceLevel.
ConfidenceThresholds
    Configurable threshold boundaries per domain.
DisclaimerGenerator
    Auto-generate disclaimers for low-confidence responses.
ConfidenceDisplay
    Format confidence info as text, colour codes, or prefix labels.
ConfidenceCalibrator
    Calibrate predicted scores against empirical outcomes.
ConfidenceSignal
    Dataclass for a single extracted linguistic confidence signal.
ExtractedSignals
    Full set of signals extracted from a response.
SignalExtractor
    Extract linguistic confidence signals from agent response text.
"""
from __future__ import annotations

from agent_sense.confidence.annotator import (
    AnnotatedResponse,
    ConfidenceAnnotator,
    ConfidenceLevel,
)
from agent_sense.confidence.calibrator import ConfidenceCalibrator
from agent_sense.confidence.disclaimer import DisclaimerGenerator
from agent_sense.confidence.display import ConfidenceDisplay
from agent_sense.confidence.signals import (
    ConfidenceSignal,
    ExtractedSignals,
    SignalExtractor,
)
from agent_sense.confidence.thresholds import ConfidenceThresholds

__all__ = [
    "AnnotatedResponse",
    "ConfidenceAnnotator",
    "ConfidenceLevel",
    "ConfidenceThresholds",
    "DisclaimerGenerator",
    "ConfidenceDisplay",
    "ConfidenceCalibrator",
    "ConfidenceSignal",
    "ExtractedSignals",
    "SignalExtractor",
]
