"""Voice context adapter — voice-only interaction context.

VoiceContextAdapter handles clients where the primary (or sole) input/output
channel is speech. It sets sensible defaults for a voice-only environment:
network quality optimised for audio, no JavaScript/WebGL assumptions, and
voice-only accessibility needs flagged.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from agent_sense.context.detector import (
    BrowserCapabilities,
    DetectedContext,
    DeviceType,
    NetworkQuality,
)


class VoicePlatform(str, Enum):
    """Known voice assistant / smart-speaker platforms."""

    ALEXA = "alexa"
    GOOGLE_ASSISTANT = "google_assistant"
    SIRI = "siri"
    CORTANA = "cortana"
    GENERIC = "generic"


class VoiceContextInfo(BaseModel):
    """Voice-specific supplementary context."""

    platform: VoicePlatform = VoicePlatform.GENERIC
    wake_word_detected: bool = False
    speech_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    locale: str = "en-US"
    supports_display: bool = False
    """Some smart-speakers have a screen (Echo Show, Nest Hub)."""


_PLATFORM_UA_MAP: dict[str, VoicePlatform] = {
    "alexa": VoicePlatform.ALEXA,
    "google-home": VoicePlatform.GOOGLE_ASSISTANT,
    "googleassistant": VoicePlatform.GOOGLE_ASSISTANT,
    "siri": VoicePlatform.SIRI,
    "cortana": VoicePlatform.CORTANA,
}


def _detect_platform(user_agent: str) -> VoicePlatform:
    ua_lower = user_agent.lower()
    for key, platform in _PLATFORM_UA_MAP.items():
        if key in ua_lower:
            return platform
    return VoicePlatform.GENERIC


class VoiceContextAdapter:
    """Voice-only context adapter.

    Produces a :class:`~agent_sense.context.detector.DetectedContext` and
    a :class:`VoiceContextInfo` appropriate for a voice-only client.

    Parameters
    ----------
    user_agent:
        The User-Agent string provided by the voice platform SDK. May be
        empty for generic voice integrations.
    locale:
        BCP-47 locale tag for the user's speech locale (e.g. ``"en-US"``).
    speech_confidence:
        ASR confidence score for the latest utterance (0.0–1.0). Used
        downstream to modulate response confidence thresholds.
    supports_display:
        Set to True for devices with a companion screen (Echo Show, etc.).
    network_quality:
        Pre-determined network quality for the audio channel. Defaults to
        MEDIUM as voice codecs typically operate on constrained bandwidth.
    wake_word_detected:
        Whether the turn was triggered by a wake word.

    Example
    -------
    >>> adapter = VoiceContextAdapter(
    ...     user_agent="AlexaSkill/1.0",
    ...     locale="en-GB",
    ...     speech_confidence=0.95,
    ... )
    >>> ctx, info = adapter.extract()
    >>> info.platform
    <VoicePlatform.ALEXA: 'alexa'>
    """

    def __init__(
        self,
        user_agent: str = "",
        locale: str = "en-US",
        speech_confidence: float = 1.0,
        supports_display: bool = False,
        network_quality: NetworkQuality = NetworkQuality.MEDIUM,
        wake_word_detected: bool = False,
    ) -> None:
        self._user_agent = user_agent
        self._locale = locale
        self._speech_confidence = speech_confidence
        self._supports_display = supports_display
        self._network_quality = network_quality
        self._wake_word_detected = wake_word_detected

    def extract(self) -> tuple[DetectedContext, VoiceContextInfo]:
        """Extract voice context and supplementary info.

        Returns
        -------
        tuple[DetectedContext, VoiceContextInfo]
            Generic context (always VOICE device type) and voice-specific info.
        """
        # Voice clients have no browser features.
        capabilities = BrowserCapabilities(
            javascript_enabled=False,
            webgl_supported=False,
            touch_supported=False,
            screen_reader_likely=False,
            reduced_motion_preferred=False,
        )
        detected = DetectedContext(
            device_type=DeviceType.VOICE,
            network_quality=self._network_quality,
            browser_capabilities=capabilities,
            user_agent=self._user_agent,
            raw_headers={},
        )
        platform = _detect_platform(self._user_agent)
        voice_info = VoiceContextInfo(
            platform=platform,
            wake_word_detected=self._wake_word_detected,
            speech_confidence=self._speech_confidence,
            locale=self._locale,
            supports_display=self._supports_display,
        )
        return detected, voice_info
