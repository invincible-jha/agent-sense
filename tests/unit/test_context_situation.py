"""Tests for agent_sense.context.situation."""
from __future__ import annotations

import pytest

from agent_sense.context.detector import ContextDetector, DeviceType, NetworkQuality
from agent_sense.context.expertise import ExpertiseEstimator
from agent_sense.context.situation import SituationAssessor


_MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
_DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def _make_assessor(ua: str = _MOBILE_UA) -> SituationAssessor:
    return SituationAssessor(
        context_detector=ContextDetector(user_agent=ua),
        expertise_estimator=ExpertiseEstimator(),
    )


class TestSituationAssessorAssess:
    def test_returns_situation_vector(self) -> None:
        sa = _make_assessor()
        result = sa.assess("What is diabetes?")
        assert result is not None

    def test_has_device_type(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello")
        assert isinstance(result.device_type, DeviceType)

    def test_has_network_quality(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello")
        assert isinstance(result.network_quality, NetworkQuality)

    def test_has_expertise_level(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello")
        assert result.expertise_level is not None

    def test_mobile_ua_mobile_device_type(self) -> None:
        sa = _make_assessor(ua=_MOBILE_UA)
        result = sa.assess("Hello")
        assert result.device_type == DeviceType.MOBILE

    def test_session_duration_default_zero(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello")
        assert result.session_duration_seconds == 0.0

    def test_session_duration_passed_through(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello", session_duration_seconds=120.0)
        assert result.session_duration_seconds == 120.0

    def test_accessibility_needs_returns_frozenset(self) -> None:
        sa = _make_assessor()
        result = sa.assess("Hello")
        assert isinstance(result.accessibility_needs, frozenset)

    def test_empty_text_returns_result(self) -> None:
        sa = _make_assessor()
        result = sa.assess("")
        assert result is not None


class TestSituationAssessorAssessFromHistory:
    def test_returns_situation_vector(self) -> None:
        sa = _make_assessor()
        result = sa.assess_from_history(["question 1", "question 2"])
        assert result is not None

    def test_empty_history_returns_result(self) -> None:
        sa = _make_assessor()
        result = sa.assess_from_history([])
        assert result is not None

    def test_has_device_type(self) -> None:
        sa = _make_assessor()
        result = sa.assess_from_history(["question 1"])
        assert isinstance(result.device_type, DeviceType)

    def test_has_network_quality(self) -> None:
        sa = _make_assessor()
        result = sa.assess_from_history(["question 1"])
        assert isinstance(result.network_quality, NetworkQuality)

    def test_session_duration_passed_through(self) -> None:
        sa = _make_assessor()
        result = sa.assess_from_history(["question 1"], session_duration_seconds=60.0)
        assert result.session_duration_seconds == 60.0
