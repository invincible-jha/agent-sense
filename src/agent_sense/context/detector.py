"""Context detector — device type, network quality, and browser capabilities.

The ContextDetector parses a User-Agent string and optional HTTP headers to
produce a structured description of the client environment. No external HTTP
calls are made; all detection is heuristic / string-matching.
"""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    """Canonical device categories."""

    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    VOICE = "voice"
    UNKNOWN = "unknown"


class NetworkQuality(str, Enum):
    """Inferred network quality tiers."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class BrowserCapabilities(BaseModel):
    """Feature flags inferred from the User-Agent and hints headers."""

    javascript_enabled: bool = True
    webgl_supported: bool = False
    touch_supported: bool = False
    screen_reader_likely: bool = False
    reduced_motion_preferred: bool = False


class DetectedContext(BaseModel):
    """Full result of ContextDetector.detect()."""

    device_type: DeviceType = DeviceType.UNKNOWN
    network_quality: NetworkQuality = NetworkQuality.UNKNOWN
    browser_capabilities: BrowserCapabilities = Field(
        default_factory=BrowserCapabilities
    )
    user_agent: str = ""
    raw_headers: dict[str, str] = Field(default_factory=dict)


# Compiled patterns — defined at module level to avoid repeated compilation.
_MOBILE_UA_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(android(?!.*tablet)|iphone|ipod|blackberry|windows phone"
    r"|mobile safari|opera mini|mobi)",
)
_TABLET_UA_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(ipad|android(?=.*tablet)|kindle|silk|playbook)",
)
_VOICE_UA_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(alexa|google-home|siri|cortana|voice|smart.?speaker)",
)
_DESKTOP_UA_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(windows nt|macintosh|x11|linux x86_64)",
)


def _infer_device_type(user_agent: str) -> DeviceType:
    if _VOICE_UA_PATTERN.search(user_agent):
        return DeviceType.VOICE
    if _TABLET_UA_PATTERN.search(user_agent):
        return DeviceType.TABLET
    if _MOBILE_UA_PATTERN.search(user_agent):
        return DeviceType.MOBILE
    if _DESKTOP_UA_PATTERN.search(user_agent):
        return DeviceType.DESKTOP
    return DeviceType.UNKNOWN


def _infer_network_quality(headers: dict[str, str]) -> NetworkQuality:
    """Infer network quality from ECT / Save-Data / Downlink headers."""
    # Network Information API hint (Chrome)
    ect = headers.get("ect", headers.get("ECT", "")).lower()
    if ect in {"4g"}:
        return NetworkQuality.HIGH
    if ect in {"3g"}:
        return NetworkQuality.MEDIUM
    if ect in {"2g", "slow-2g"}:
        return NetworkQuality.LOW

    # Downlink hint (Mbps)
    downlink_raw = headers.get("downlink", headers.get("Downlink", ""))
    try:
        downlink = float(downlink_raw)
        if downlink >= 5.0:
            return NetworkQuality.HIGH
        if downlink >= 1.0:
            return NetworkQuality.MEDIUM
        return NetworkQuality.LOW
    except ValueError:
        pass

    # Save-Data hint implies poor connection
    if headers.get("save-data", headers.get("Save-Data", "")).lower() == "on":
        return NetworkQuality.LOW

    return NetworkQuality.UNKNOWN


def _infer_capabilities(
    user_agent: str,
    device_type: DeviceType,
    headers: dict[str, str],
) -> BrowserCapabilities:
    touch = device_type in {DeviceType.MOBILE, DeviceType.TABLET}
    # WebGL is generally available on modern desktop/tablet browsers
    webgl = device_type in {DeviceType.DESKTOP, DeviceType.TABLET}
    # Screen reader hint: Lynx, NVDA mention in UA (rare but possible in proxies)
    screen_reader = bool(
        re.search(r"(?i)(nvda|jaws|voiceover|talkback|orca)", user_agent)
    )
    # Sec-CH-Prefers-Reduced-Motion client hint
    reduced_motion = (
        headers.get("sec-ch-prefers-reduced-motion", "").lower() == "reduce"
    )
    return BrowserCapabilities(
        javascript_enabled=device_type != DeviceType.VOICE,
        webgl_supported=webgl,
        touch_supported=touch,
        screen_reader_likely=screen_reader,
        reduced_motion_preferred=reduced_motion,
    )


class ContextDetector:
    """Detect device type, network quality, and browser capabilities.

    Parameters
    ----------
    user_agent:
        The ``User-Agent`` request header value.
    headers:
        Optional mapping of additional HTTP headers (e.g., ``ECT``,
        ``Downlink``, ``Save-Data``, ``Sec-CH-Prefers-Reduced-Motion``).

    Example
    -------
    >>> detector = ContextDetector("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)")
    >>> result = detector.detect()
    >>> result.device_type
    <DeviceType.MOBILE: 'mobile'>
    """

    def __init__(
        self,
        user_agent: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._headers: dict[str, str] = headers or {}

    def detect(self) -> DetectedContext:
        """Run full context detection and return a DetectedContext.

        Returns
        -------
        DetectedContext
            Populated with device type, network quality, and capabilities.
        """
        device_type = _infer_device_type(self._user_agent)
        network_quality = _infer_network_quality(self._headers)
        capabilities = _infer_capabilities(
            self._user_agent, device_type, self._headers
        )
        return DetectedContext(
            device_type=device_type,
            network_quality=network_quality,
            browser_capabilities=capabilities,
            user_agent=self._user_agent,
            raw_headers=dict(self._headers),
        )

    def detect_device_type(self) -> DeviceType:
        """Return only the detected DeviceType."""
        return _infer_device_type(self._user_agent)

    def detect_network_quality(self) -> NetworkQuality:
        """Return only the inferred NetworkQuality."""
        return _infer_network_quality(self._headers)
