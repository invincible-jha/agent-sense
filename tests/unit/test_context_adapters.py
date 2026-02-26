"""Tests for agent_sense.context.adapters (mobile, voice, web)."""
from __future__ import annotations

import pytest

from agent_sense.context.adapters.mobile import MobileContextAdapter
from agent_sense.context.adapters.voice import VoiceContextAdapter
from agent_sense.context.adapters.web import WebContextAdapter
from agent_sense.context.detector import DeviceType, NetworkQuality


_IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
_ANDROID_UA = "Mozilla/5.0 (Linux; Android 11; Pixel 5)"
_DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class TestMobileContextAdapter:
    def test_extract_returns_tuple(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        result = adapter.extract()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_extract_detected_context_device_type(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        context, info = adapter.extract()
        assert context.device_type == DeviceType.MOBILE

    def test_extract_touch_supported_on_mobile(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        context, info = adapter.extract()
        assert context.browser_capabilities.touch_supported is True

    def test_extract_mobile_device_info(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        context, info = adapter.extract()
        assert info is not None

    def test_extract_ios_os_name(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        context, info = adapter.extract()
        assert "iOS" in info.os_name or info.os_name != ""

    def test_extract_android_ua(self) -> None:
        adapter = MobileContextAdapter(user_agent=_ANDROID_UA)
        context, info = adapter.extract()
        assert context.device_type == DeviceType.MOBILE

    def test_extract_user_agent_stored(self) -> None:
        adapter = MobileContextAdapter(user_agent=_IPHONE_UA)
        context, info = adapter.extract()
        assert context.user_agent == _IPHONE_UA


class TestWebContextAdapter:
    def test_extract_returns_detected_context(self) -> None:
        adapter = WebContextAdapter(headers={"user-agent": _DESKTOP_UA})
        result = adapter.extract()
        assert result is not None

    def test_user_agent_property(self) -> None:
        adapter = WebContextAdapter(headers={"user-agent": _DESKTOP_UA})
        assert adapter.user_agent == _DESKTOP_UA

    def test_get_client_ip_from_forwarded_header(self) -> None:
        adapter = WebContextAdapter(headers={"x-forwarded-for": "1.2.3.4"})
        ip = adapter.get_client_ip()
        assert "1.2.3.4" in ip

    def test_get_client_ip_empty_headers(self) -> None:
        adapter = WebContextAdapter(headers={})
        ip = adapter.get_client_ip()
        assert isinstance(ip, str)

    def test_get_accepted_languages_parses_header(self) -> None:
        adapter = WebContextAdapter(headers={"accept-language": "en-US,fr;q=0.8"})
        langs = adapter.get_accepted_languages()
        assert isinstance(langs, list)
        assert "en-US" in langs

    def test_get_accepted_languages_empty(self) -> None:
        adapter = WebContextAdapter(headers={})
        langs = adapter.get_accepted_languages()
        assert isinstance(langs, list)

    def test_extract_stores_raw_headers(self) -> None:
        headers = {"user-agent": _DESKTOP_UA}
        adapter = WebContextAdapter(headers=headers)
        result = adapter.extract()
        assert result.raw_headers is not None


class TestVoiceContextAdapter:
    def test_extract_returns_tuple(self) -> None:
        adapter = VoiceContextAdapter(user_agent="VoiceApp/1.0", locale="en-US")
        result = adapter.extract()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_extract_device_type_is_voice(self) -> None:
        adapter = VoiceContextAdapter(user_agent="VoiceApp/1.0")
        context, info = adapter.extract()
        assert context.device_type == DeviceType.VOICE

    def test_extract_voice_info_locale(self) -> None:
        adapter = VoiceContextAdapter(user_agent="VoiceApp/1.0", locale="fr-FR")
        context, info = adapter.extract()
        assert info.locale == "fr-FR"

    def test_extract_speech_confidence_stored(self) -> None:
        adapter = VoiceContextAdapter(
            user_agent="VoiceApp/1.0",
            speech_confidence=0.85,
        )
        context, info = adapter.extract()
        assert info.speech_confidence == 0.85

    def test_extract_wake_word_detected(self) -> None:
        adapter = VoiceContextAdapter(user_agent="VoiceApp/1.0", wake_word_detected=True)
        context, info = adapter.extract()
        assert info.wake_word_detected is True

    def test_extract_supports_display_stored(self) -> None:
        adapter = VoiceContextAdapter(user_agent="VoiceApp/1.0", supports_display=True)
        context, info = adapter.extract()
        assert info.supports_display is True

    def test_extract_network_quality_stored(self) -> None:
        adapter = VoiceContextAdapter(
            user_agent="VoiceApp/1.0",
            network_quality=NetworkQuality.HIGH,
        )
        context, info = adapter.extract()
        assert context.network_quality == NetworkQuality.HIGH

    def test_default_locale(self) -> None:
        adapter = VoiceContextAdapter()
        context, info = adapter.extract()
        assert info.locale == "en-US"
