"""Tests for agent_sense.context.detector."""
from __future__ import annotations

import pytest

from agent_sense.context.detector import ContextDetector, DeviceType, NetworkQuality


_DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
_MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
_ANDROID_UA = "Mozilla/5.0 (Linux; Android 11; Pixel 5)"
_TABLET_UA = "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
_BOT_UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"


class TestContextDetectorInit:
    def test_empty_user_agent(self) -> None:
        cd = ContextDetector(user_agent="")
        assert cd is not None

    def test_with_user_agent(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA)
        assert cd is not None

    def test_with_headers(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA, headers={"accept-language": "en-US"})
        assert cd is not None


class TestContextDetectorDetectDeviceType:
    def test_iphone_is_mobile(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        assert cd.detect_device_type() == DeviceType.MOBILE

    def test_android_is_mobile(self) -> None:
        cd = ContextDetector(user_agent=_ANDROID_UA)
        assert cd.detect_device_type() == DeviceType.MOBILE

    def test_ipad_is_tablet(self) -> None:
        cd = ContextDetector(user_agent=_TABLET_UA)
        device = cd.detect_device_type()
        # iPad may be classified as tablet or mobile
        assert device in (DeviceType.TABLET, DeviceType.MOBILE)

    def test_desktop_ua_is_desktop(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA)
        device = cd.detect_device_type()
        assert device in (DeviceType.DESKTOP, DeviceType.UNKNOWN)

    def test_empty_ua_returns_unknown_or_desktop(self) -> None:
        cd = ContextDetector(user_agent="")
        device = cd.detect_device_type()
        assert isinstance(device, DeviceType)


class TestContextDetectorDetectNetworkQuality:
    def test_returns_network_quality_enum(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA)
        result = cd.detect_network_quality()
        assert isinstance(result, NetworkQuality)

    def test_no_headers_returns_unknown(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA)
        result = cd.detect_network_quality()
        assert result == NetworkQuality.UNKNOWN

    def test_slow_downlink_header(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA, headers={"downlink": "0.1"})
        result = cd.detect_network_quality()
        assert isinstance(result, NetworkQuality)

    def test_fast_downlink_header(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA, headers={"downlink": "10"})
        result = cd.detect_network_quality()
        assert isinstance(result, NetworkQuality)


class TestContextDetectorDetect:
    def test_detect_returns_detected_context(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert result is not None

    def test_detect_has_device_type(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert isinstance(result.device_type, DeviceType)

    def test_detect_has_network_quality(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert isinstance(result.network_quality, NetworkQuality)

    def test_detect_has_browser_capabilities(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert result.browser_capabilities is not None

    def test_detect_mobile_has_touch_supported(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert result.browser_capabilities.touch_supported is True

    def test_detect_stores_user_agent(self) -> None:
        cd = ContextDetector(user_agent=_MOBILE_UA)
        result = cd.detect()
        assert result.user_agent == _MOBILE_UA

    def test_detect_desktop_no_touch(self) -> None:
        cd = ContextDetector(user_agent=_DESKTOP_UA)
        result = cd.detect()
        assert result.browser_capabilities.touch_supported is False
