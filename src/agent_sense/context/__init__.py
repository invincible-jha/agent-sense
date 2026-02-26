"""Context detection and situation assessment for human-agent interactions.

Exports
-------
ContextDetector
    Detect device type, network quality, and browser capabilities.
ExpertiseEstimator
    Infer user expertise level from vocabulary and question structure.
SituationVector
    Dataclass capturing the full situational context vector.
SituationAssessor
    Compute a SituationVector from raw context inputs.
WebContextAdapter
    Browser-based context adapter (headers and user-agent).
MobileContextAdapter
    Mobile-specific context adapter.
VoiceContextAdapter
    Voice-only context adapter.
"""
from __future__ import annotations

from agent_sense.context.detector import ContextDetector, DeviceType, NetworkQuality
from agent_sense.context.expertise import ExpertiseEstimator, ExpertiseLevel
from agent_sense.context.situation import SituationAssessor, SituationVector
from agent_sense.context.adapters.web import WebContextAdapter
from agent_sense.context.adapters.mobile import MobileContextAdapter
from agent_sense.context.adapters.voice import VoiceContextAdapter

__all__ = [
    "ContextDetector",
    "DeviceType",
    "NetworkQuality",
    "ExpertiseEstimator",
    "ExpertiseLevel",
    "SituationAssessor",
    "SituationVector",
    "WebContextAdapter",
    "MobileContextAdapter",
    "VoiceContextAdapter",
]
