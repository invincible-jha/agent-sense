"""Situation vector and assessor for human-agent interaction context.

SituationVector is an immutable snapshot of the user's current situational
context. SituationAssessor computes it by combining inputs from a
ContextDetector and an ExpertiseEstimator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from agent_sense.context.detector import ContextDetector, DeviceType, NetworkQuality
from agent_sense.context.expertise import ExpertiseEstimator, ExpertiseLevel


class AccessibilityNeed(str, Enum):
    """Identified accessibility requirements."""

    NONE = "none"
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    REDUCED_MOTION = "reduced_motion"
    KEYBOARD_ONLY = "keyboard_only"
    VOICE_ONLY = "voice_only"


@dataclass(frozen=True)
class SituationVector:
    """Immutable situational context snapshot.

    Attributes
    ----------
    device_type:
        The detected client device category.
    network_quality:
        The inferred network quality tier.
    expertise_level:
        The estimated user expertise level.
    accessibility_needs:
        Set of identified accessibility requirements.
    session_duration_seconds:
        Elapsed session time in seconds (0 if unknown).
    """

    device_type: DeviceType = DeviceType.UNKNOWN
    network_quality: NetworkQuality = NetworkQuality.UNKNOWN
    expertise_level: ExpertiseLevel = ExpertiseLevel.NOVICE
    accessibility_needs: frozenset[AccessibilityNeed] = field(
        default_factory=frozenset
    )
    session_duration_seconds: float = 0.0

    def is_low_bandwidth(self) -> bool:
        """Return True if network quality is LOW."""
        return self.network_quality == NetworkQuality.LOW

    def requires_accessibility(self) -> bool:
        """Return True if any accessibility need beyond NONE is present."""
        return any(need != AccessibilityNeed.NONE for need in self.accessibility_needs)

    def is_voice_context(self) -> bool:
        """Return True if the device is voice-only or voice-only accessibility is needed."""
        return (
            self.device_type == DeviceType.VOICE
            or AccessibilityNeed.VOICE_ONLY in self.accessibility_needs
        )


def _resolve_accessibility_needs(
    device_type: DeviceType,
    screen_reader_likely: bool,
    reduced_motion_preferred: bool,
    extra_needs: frozenset[AccessibilityNeed] | None,
) -> frozenset[AccessibilityNeed]:
    needs: set[AccessibilityNeed] = set()

    if device_type == DeviceType.VOICE:
        needs.add(AccessibilityNeed.VOICE_ONLY)
    if screen_reader_likely:
        needs.add(AccessibilityNeed.SCREEN_READER)
    if reduced_motion_preferred:
        needs.add(AccessibilityNeed.REDUCED_MOTION)
    if extra_needs:
        needs.update(extra_needs)
    if not needs:
        needs.add(AccessibilityNeed.NONE)

    return frozenset(needs)


class SituationAssessor:
    """Compute a SituationVector from raw context inputs.

    Parameters
    ----------
    context_detector:
        Pre-configured ContextDetector instance (or None to construct a
        default detector with an empty user-agent).
    expertise_estimator:
        Pre-configured ExpertiseEstimator (or None for the default).

    Example
    -------
    >>> assessor = SituationAssessor(
    ...     context_detector=ContextDetector("Mozilla/5.0 (iPhone; ...)"),
    ... )
    >>> vector = assessor.assess(user_text="What is a webhook?")
    >>> vector.device_type
    <DeviceType.MOBILE: 'mobile'>
    """

    def __init__(
        self,
        context_detector: ContextDetector | None = None,
        expertise_estimator: ExpertiseEstimator | None = None,
    ) -> None:
        self._detector = context_detector or ContextDetector()
        self._estimator = expertise_estimator or ExpertiseEstimator()

    def assess(
        self,
        user_text: str = "",
        session_duration_seconds: float = 0.0,
        extra_accessibility_needs: frozenset[AccessibilityNeed] | None = None,
    ) -> SituationVector:
        """Compute a SituationVector.

        Parameters
        ----------
        user_text:
            Latest user message text, used to estimate expertise.
        session_duration_seconds:
            Elapsed session time. Pass 0.0 if unknown.
        extra_accessibility_needs:
            Any explicitly declared accessibility needs (e.g. from user profile).

        Returns
        -------
        SituationVector
            Fully populated context snapshot.
        """
        detected = self._detector.detect()
        expertise_estimate = self._estimator.estimate(user_text)
        accessibility_needs = _resolve_accessibility_needs(
            device_type=detected.device_type,
            screen_reader_likely=detected.browser_capabilities.screen_reader_likely,
            reduced_motion_preferred=detected.browser_capabilities.reduced_motion_preferred,
            extra_needs=extra_accessibility_needs,
        )
        return SituationVector(
            device_type=detected.device_type,
            network_quality=detected.network_quality,
            expertise_level=expertise_estimate.level,
            accessibility_needs=accessibility_needs,
            session_duration_seconds=session_duration_seconds,
        )

    def assess_from_history(
        self,
        messages: list[str],
        session_duration_seconds: float = 0.0,
        extra_accessibility_needs: frozenset[AccessibilityNeed] | None = None,
    ) -> SituationVector:
        """Compute a SituationVector using all prior user messages for expertise.

        Parameters
        ----------
        messages:
            Ordered list of user-turn text strings.
        session_duration_seconds:
            Elapsed session time.
        extra_accessibility_needs:
            Explicitly declared accessibility needs.

        Returns
        -------
        SituationVector
            Fully populated context snapshot.
        """
        combined = " ".join(messages)
        return self.assess(
            user_text=combined,
            session_duration_seconds=session_duration_seconds,
            extra_accessibility_needs=extra_accessibility_needs,
        )
