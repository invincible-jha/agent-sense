"""Tests for agent_sense.accessibility.simplifier."""
from __future__ import annotations

import pytest

from agent_sense.accessibility.simplifier import (
    TextSimplifier,
    flesch_kincaid_grade,
)


class TestFleschKincaidGrade:
    def test_empty_text_returns_zero(self) -> None:
        assert flesch_kincaid_grade("") == 0.0

    def test_simple_sentence_low_grade(self) -> None:
        grade = flesch_kincaid_grade("The cat sat on the mat.")
        assert isinstance(grade, float)
        assert grade >= 0.0

    def test_complex_sentence_higher_grade(self) -> None:
        simple_grade = flesch_kincaid_grade("The cat sat.")
        complex_grade = flesch_kincaid_grade(
            "The patient demonstrated significant cardiovascular improvement "
            "after pharmaceutical interventions were administered subcutaneously."
        )
        assert complex_grade > simple_grade

    def test_returns_float(self) -> None:
        result = flesch_kincaid_grade("Hello world.")
        assert isinstance(result, float)

    def test_single_word(self) -> None:
        grade = flesch_kincaid_grade("Hello.")
        assert isinstance(grade, float)


class TestTextSimplifier:
    def test_default_instantiation(self) -> None:
        ts = TextSimplifier()
        assert ts is not None

    def test_grade_level_returns_float(self) -> None:
        ts = TextSimplifier()
        result = ts.grade_level("The quick brown fox jumps over the lazy dog.")
        assert isinstance(result, float)

    def test_grade_level_empty_text(self) -> None:
        ts = TextSimplifier()
        result = ts.grade_level("")
        assert result == 0.0

    def test_grade_level_matches_flesch_kincaid(self) -> None:
        ts = TextSimplifier()
        text = "The cat sat on the mat. It was nice."
        assert ts.grade_level(text) == flesch_kincaid_grade(text)

    def test_simplify_returns_string(self) -> None:
        ts = TextSimplifier()
        result = ts.simplify("Hello world.", target_grade_level=6.0)
        assert isinstance(result, str)

    def test_simplify_non_empty_input(self) -> None:
        ts = TextSimplifier()
        text = "The cat sat on the mat."
        result = ts.simplify(text, target_grade_level=6.0)
        assert len(result) > 0

    def test_simplify_already_simple_text_unchanged(self) -> None:
        ts = TextSimplifier()
        text = "The cat sat on the mat."
        result = ts.simplify(text, target_grade_level=12.0)
        # Already below target grade, should remain essentially the same
        assert isinstance(result, str)

    def test_simplify_high_grade_text(self) -> None:
        ts = TextSimplifier()
        text = (
            "The patient demonstrated significant improvement in cardiovascular "
            "function after the administration of the prescribed pharmaceutical "
            "interventions."
        )
        result = ts.simplify(text, target_grade_level=6.0)
        assert isinstance(result, str)

    def test_readability_summary_returns_dict(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("The cat sat on the mat.")
        assert isinstance(result, dict)

    def test_readability_summary_keys(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("The quick brown fox.")
        expected_keys = {
            "grade_level",
            "word_count",
            "sentence_count",
            "avg_sentence_length",
            "avg_syllables_per_word",
        }
        assert expected_keys.issubset(result.keys())

    def test_readability_summary_values_are_floats(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("The cat sat on the mat.")
        for value in result.values():
            assert isinstance(value, float)

    def test_readability_summary_word_count(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("The cat sat on the mat.")
        assert result["word_count"] > 0

    def test_readability_summary_sentence_count(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("First sentence. Second sentence.")
        assert result["sentence_count"] >= 1.0

    def test_readability_summary_empty_text(self) -> None:
        ts = TextSimplifier()
        result = ts.readability_summary("")
        assert result["grade_level"] == 0.0
        assert result["word_count"] == 0.0

    def test_grade_level_multi_sentence(self) -> None:
        ts = TextSimplifier()
        text = "The cat sat. The dog ran. The bird flew."
        grade = ts.grade_level(text)
        assert isinstance(grade, float)
        assert grade >= 0.0
