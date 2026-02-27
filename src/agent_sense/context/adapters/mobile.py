"""Mobile context adapter — mobile-specific context extraction.

MobileContextAdapter targets native mobile apps that pass platform-specific
metadata (OS version, screen density, battery state) alongside the standard
User-Agent. It extends the generic context detection with mobile-only signals.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

from agent_sense.context.detector import ContextDetector, DetectedContext, DeviceType


class MobileDeviceInfo(BaseModel):
    """Additional mobile-specific device information."""

    os_name: str = ""
    os_version: str = ""
    app_version: str = ""
    screen_density: float = Field(default=1.0, ge=0.0)
    battery_low: bool = False
    data_saver_active: bool = False


# Platform detection patterns.
_IOS_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(?:iphone|ipad|ipod).*?OS ([\d_]+)"
)
_ANDROID_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)Android ([\d.]+)"
)
_APP_VERSION_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)agent-sense/([\d.]+)"
)


def _parse_ios_version(user_agent: str) -> tuple[str, str]:
    match = _IOS_PATTERN.search(user_agent)
    if match:
        version = match.group(1).replace("_", ".")
        return "iOS", version
    return "", ""


def _parse_android_version(user_agent: str) -> tuple[str, str]:
    match = _ANDROID_PATTERN.search(user_agent)
    if match:
        return "Android", match.group(1)
    return "", ""


def _parse_app_version(user_agent: str) -> str:
    match = _APP_VERSION_PATTERN.search(user_agent)
    return match.group(1) if match else ""


class MobileContextAdapter:
    """Mobile-specific context adapter.

    Accepts a User-Agent string and optional mobile metadata headers/values
    to produce a :class:`~agent_sense.context.detector.DetectedContext`
    augmented with :class:`MobileDeviceInfo`.

    Parameters
    ----------
    user_agent:
        The ``User-Agent`` header value.
    headers:
        Additional HTTP headers. Recognises:
        - ``X-Screen-Density`` (float dpi ratio, e.g. ``"2.0"``)
        - ``X-Battery-Low`` (``"true"``/``"false"``)
        - ``X-Data-Saver`` (``"on"``/``"off"``)
        - Standard network hints (``ECT``, ``Downlink``, ``Save-Data``).

    Example
    -------
    >>> adapter = MobileContextAdapter(
    ...     "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) agent-sense/1.2.0",
    ...     headers={"X-Battery-Low": "true"},
    ... )
    >>> ctx, info = adapter.extract()
    >>> info.os_name
    'iOS'
    """

    def __init__(
        self,
        user_agent: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._headers: dict[str, str] = {
            k.lower(): v for k, v in (headers or {}).items()
        }

    def extract(self) -> tuple[DetectedContext, MobileDeviceInfo]:
        """Extract context and mobile device info.

        Returns
        -------
        tuple[DetectedContext, MobileDeviceInfo]
            A pair of the generic context and the mobile-specific details.
        """
        detector = ContextDetector(
            user_agent=self._user_agent,
            headers=self._headers,
        )
        detected = detector.detect()

        # Override device type: mobile adapters should always produce
        # MOBILE or TABLET, never UNKNOWN for a UA that we are explicitly
        # told is mobile.
        if detected.device_type == DeviceType.UNKNOWN:
            detected = detected.model_copy(
                update={"device_type": DeviceType.MOBILE}
            )

        os_name, os_version = _parse_ios_version(self._user_agent)
        if not os_name:
            os_name, os_version = _parse_android_version(self._user_agent)

        app_version = _parse_app_version(self._user_agent)

        try:
            screen_density = float(self._headers.get("x-screen-density", "1.0"))
        except ValueError:
            screen_density = 1.0

        battery_low = self._headers.get("x-battery-low", "false").lower() == "true"
        data_saver = self._headers.get("x-data-saver", "off").lower() == "on"

        device_info = MobileDeviceInfo(
            os_name=os_name,
            os_version=os_version,
            app_version=app_version,
            screen_density=screen_density,
            battery_low=battery_low,
            data_saver_active=data_saver,
        )
        return detected, device_info
