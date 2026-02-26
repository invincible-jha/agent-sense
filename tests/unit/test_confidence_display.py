"""Tests for agent_sense.confidence.display."""
from __future__ import annotations

import pytest

from agent_sense.confidence.annotator import ConfidenceLevel
from agent_sense.confidence.display import ConfidenceDisplay


class TestConfidenceDisplayAsLabel:
    def test_high_label(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_label(ConfidenceLevel.HIGH) == "High confidence"

    def test_medium_label(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_label(ConfidenceLevel.MEDIUM) == "Medium confidence"

    def test_low_label(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_label(ConfidenceLevel.LOW) == "Low confidence"

    def test_unknown_label(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_label(ConfidenceLevel.UNKNOWN) == "Confidence unknown"


class TestConfidenceDisplayAsColour:
    def test_high_colour_is_green(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_colour(ConfidenceLevel.HIGH) == "green"

    def test_medium_colour_is_yellow(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_colour(ConfidenceLevel.MEDIUM) == "yellow"

    def test_low_colour_is_red(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_colour(ConfidenceLevel.LOW) == "red"

    def test_unknown_colour_is_grey(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_colour(ConfidenceLevel.UNKNOWN) == "grey"


class TestConfidenceDisplayAsPrefix:
    def test_high_prefix(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_prefix(ConfidenceLevel.HIGH) == "[HIGH]"

    def test_medium_prefix(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_prefix(ConfidenceLevel.MEDIUM) == "[MED]"

    def test_low_prefix(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_prefix(ConfidenceLevel.LOW) == "[LOW]"

    def test_unknown_prefix(self) -> None:
        display = ConfidenceDisplay()
        assert display.as_prefix(ConfidenceLevel.UNKNOWN) == "[?]"


class TestConfidenceDisplayFormatScore:
    def test_format_zero(self) -> None:
        display = ConfidenceDisplay()
        assert display.format_score(0.0) == "0.0%"

    def test_format_one(self) -> None:
        display = ConfidenceDisplay()
        assert display.format_score(1.0) == "100.0%"

    def test_format_half(self) -> None:
        display = ConfidenceDisplay()
        assert display.format_score(0.5) == "50.0%"

    def test_format_point_92(self) -> None:
        display = ConfidenceDisplay()
        assert display.format_score(0.92) == "92.0%"

    def test_format_returns_percent_sign(self) -> None:
        display = ConfidenceDisplay()
        result = display.format_score(0.75)
        assert "%" in result

    def test_format_has_one_decimal(self) -> None:
        display = ConfidenceDisplay()
        result = display.format_score(0.333)
        assert "." in result
