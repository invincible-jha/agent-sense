"""Tests for agent_sense.confidence.disclaimer."""
from __future__ import annotations

import pytest

from agent_sense.confidence.annotator import AnnotatedResponse, ConfidenceLevel
from agent_sense.confidence.disclaimer import DisclaimerGenerator


def _make_response(content: str, level: ConfidenceLevel, score: float = 0.5) -> AnnotatedResponse:
    return AnnotatedResponse(
        content=content,
        confidence_level=level,
        confidence_score=score,
    )


class TestDisclaimerGeneratorGenerate:
    def test_low_confidence_appends_disclaimer(self) -> None:
        gen = DisclaimerGenerator()
        resp = _make_response("Maybe Paris?", ConfidenceLevel.LOW, 0.2)
        result = gen.generate(resp)
        assert result.startswith("Maybe Paris?")
        assert "Note:" in result or "certain" in result.lower()

    def test_high_confidence_returns_content_unchanged(self) -> None:
        gen = DisclaimerGenerator()
        resp = _make_response("Paris is the capital.", ConfidenceLevel.HIGH, 0.95)
        result = gen.generate(resp)
        assert result == "Paris is the capital."

    def test_medium_confidence_returns_content_unchanged(self) -> None:
        gen = DisclaimerGenerator()
        resp = _make_response("Probably Paris.", ConfidenceLevel.MEDIUM, 0.65)
        result = gen.generate(resp)
        assert result == "Probably Paris."

    def test_unknown_confidence_appends_disclaimer(self) -> None:
        gen = DisclaimerGenerator()
        resp = _make_response("I don't know.", ConfidenceLevel.UNKNOWN, 0.1)
        result = gen.generate(resp)
        assert "I don't know." in result
        assert "consult" in result.lower() or "information" in result.lower()

    def test_prepend_true_puts_disclaimer_first(self) -> None:
        gen = DisclaimerGenerator(prepend=True)
        resp = _make_response("Maybe Paris?", ConfidenceLevel.LOW, 0.2)
        result = gen.generate(resp)
        assert not result.startswith("Maybe Paris?")
        assert result.endswith("Maybe Paris?")

    def test_prepend_false_appends_disclaimer(self) -> None:
        gen = DisclaimerGenerator(prepend=False)
        resp = _make_response("Maybe Paris?", ConfidenceLevel.LOW, 0.2)
        result = gen.generate(resp)
        assert result.startswith("Maybe Paris?")

    def test_default_prepend_is_false(self) -> None:
        gen = DisclaimerGenerator()
        resp = _make_response("Maybe Paris?", ConfidenceLevel.LOW, 0.2)
        result = gen.generate(resp)
        assert result.startswith("Maybe Paris?")


class TestDisclaimerGeneratorDisclaimerText:
    def test_low_returns_disclaimer_text(self) -> None:
        gen = DisclaimerGenerator()
        text = gen.disclaimer_text(ConfidenceLevel.LOW)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_unknown_returns_disclaimer_text(self) -> None:
        gen = DisclaimerGenerator()
        text = gen.disclaimer_text(ConfidenceLevel.UNKNOWN)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_high_returns_empty_string(self) -> None:
        gen = DisclaimerGenerator()
        text = gen.disclaimer_text(ConfidenceLevel.HIGH)
        assert text == ""

    def test_medium_returns_empty_string(self) -> None:
        gen = DisclaimerGenerator()
        text = gen.disclaimer_text(ConfidenceLevel.MEDIUM)
        assert text == ""

    def test_low_disclaimer_mentions_verification(self) -> None:
        gen = DisclaimerGenerator()
        text = gen.disclaimer_text(ConfidenceLevel.LOW)
        assert "verify" in text.lower() or "certain" in text.lower()
