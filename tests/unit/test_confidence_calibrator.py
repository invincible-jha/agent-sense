"""Unit tests for agent_sense.confidence.calibrator."""
from __future__ import annotations

import pytest

from agent_sense.confidence.calibrator import ConfidenceCalibrator, _CalibrationBin


# ---------------------------------------------------------------------------
# _CalibrationBin (internal)
# ---------------------------------------------------------------------------


class TestCalibrationBin:
    def test_average_confidence_empty_bin_returns_zero(self) -> None:
        bucket = _CalibrationBin()
        assert bucket.average_confidence() == 0.0

    def test_accuracy_empty_bin_returns_zero(self) -> None:
        bucket = _CalibrationBin()
        assert bucket.accuracy() == 0.0

    def test_average_confidence_computed_correctly(self) -> None:
        bucket = _CalibrationBin(total_confidence=0.9, correct_count=1, total_count=1)
        assert bucket.average_confidence() == pytest.approx(0.9)

    def test_accuracy_computed_correctly(self) -> None:
        bucket = _CalibrationBin(total_confidence=1.8, correct_count=2, total_count=3)
        assert bucket.accuracy() == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# ConfidenceCalibrator construction
# ---------------------------------------------------------------------------


class TestConfidenceCalibratorInit:
    def test_default_bin_count(self) -> None:
        cal = ConfidenceCalibrator()
        assert cal._bin_count == 10

    def test_custom_bin_count(self) -> None:
        cal = ConfidenceCalibrator(bin_count=5)
        assert cal._bin_count == 5

    def test_invalid_bin_count_raises(self) -> None:
        with pytest.raises(ValueError, match="bin_count"):
            ConfidenceCalibrator(bin_count=0)

    def test_negative_bin_count_raises(self) -> None:
        with pytest.raises(ValueError, match="bin_count"):
            ConfidenceCalibrator(bin_count=-1)

    def test_fresh_calibrator_has_no_records(self) -> None:
        cal = ConfidenceCalibrator()
        assert cal.total_records() == 0


# ---------------------------------------------------------------------------
# ConfidenceCalibrator.record
# ---------------------------------------------------------------------------


class TestRecord:
    def test_record_increments_total_count(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.8, True)
        assert cal.total_records() == 1

    def test_record_multiple_increments_count(self) -> None:
        cal = ConfidenceCalibrator()
        for _ in range(5):
            cal.record(0.5, True)
        assert cal.total_records() == 5

    def test_record_score_above_one_raises(self) -> None:
        cal = ConfidenceCalibrator()
        with pytest.raises(ValueError, match="0.0, 1.0"):
            cal.record(1.1, True)

    def test_record_score_below_zero_raises(self) -> None:
        cal = ConfidenceCalibrator()
        with pytest.raises(ValueError, match="0.0, 1.0"):
            cal.record(-0.1, True)

    def test_record_score_at_boundaries_accepted(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.0, False)
        cal.record(1.0, True)
        assert cal.total_records() == 2


# ---------------------------------------------------------------------------
# ConfidenceCalibrator.calibration_error (ECE)
# ---------------------------------------------------------------------------


class TestCalibrationError:
    def test_ece_is_zero_when_no_records(self) -> None:
        cal = ConfidenceCalibrator()
        assert cal.calibration_error() == 0.0

    def test_perfect_calibration_gives_zero_ece(self) -> None:
        """A model predicting 0.9 that is always correct has avg_conf = accuracy = 0.9."""
        cal = ConfidenceCalibrator()
        for _ in range(9):
            cal.record(0.9, True)
        for _ in range(1):
            cal.record(0.9, False)
        # avg_confidence = 0.9, accuracy = 9/10 = 0.9 → ECE = 0
        assert cal.calibration_error() == pytest.approx(0.0, abs=1e-6)

    def test_overconfident_model_has_positive_ece(self) -> None:
        """Predicting 0.9 but always wrong: avg_conf=0.9, accuracy=0. ECE > 0."""
        cal = ConfidenceCalibrator()
        for _ in range(10):
            cal.record(0.9, False)
        assert cal.calibration_error() > 0.0

    def test_ece_bounded_between_zero_and_one(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.9, False)
        cal.record(0.1, True)
        ece = cal.calibration_error()
        assert 0.0 <= ece <= 1.0

    def test_ece_known_value(self) -> None:
        """
        Two samples in one bin (0.8–0.9 = bin index 8 for 10 bins):
        predicted = 0.85 each, one correct, one not.
        avg_conf = 0.85, accuracy = 0.5, gap = 0.35, weight = 1.0 → ECE = 0.35.
        """
        cal = ConfidenceCalibrator(bin_count=10)
        cal.record(0.85, True)
        cal.record(0.85, False)
        ece = cal.calibration_error()
        assert ece == pytest.approx(0.35, abs=1e-6)

    def test_ece_returns_rounded_to_six_decimal_places(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.7, True)
        ece = cal.calibration_error()
        # Result should have at most 6 decimal places
        assert round(ece, 6) == ece


# ---------------------------------------------------------------------------
# ConfidenceCalibrator.reliability_diagram
# ---------------------------------------------------------------------------


class TestReliabilityDiagram:
    def test_diagram_has_correct_keys(self) -> None:
        cal = ConfidenceCalibrator()
        diagram = cal.reliability_diagram()
        expected_keys = {
            "bin_lower",
            "bin_upper",
            "avg_confidence",
            "accuracy",
            "sample_fraction",
        }
        assert set(diagram.keys()) == expected_keys

    def test_diagram_lists_have_correct_length(self) -> None:
        cal = ConfidenceCalibrator(bin_count=5)
        diagram = cal.reliability_diagram()
        for key in diagram:
            assert len(diagram[key]) == 5

    def test_diagram_bin_lower_starts_at_zero(self) -> None:
        cal = ConfidenceCalibrator(bin_count=10)
        diagram = cal.reliability_diagram()
        assert diagram["bin_lower"][0] == pytest.approx(0.0)

    def test_diagram_sample_fraction_sums_to_one_when_records_present(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.2, True)
        cal.record(0.8, False)
        fractions = cal.reliability_diagram()["sample_fraction"]
        assert sum(fractions) == pytest.approx(1.0, abs=1e-6)

    def test_diagram_empty_bins_have_zero_fractions(self) -> None:
        cal = ConfidenceCalibrator()
        diagram = cal.reliability_diagram()
        assert all(f == 0.0 for f in diagram["sample_fraction"])


# ---------------------------------------------------------------------------
# ConfidenceCalibrator.reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_clears_records(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.8, True)
        cal.reset()
        assert cal.total_records() == 0

    def test_reset_restores_zero_ece(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.9, False)
        cal.reset()
        assert cal.calibration_error() == 0.0

    def test_can_record_after_reset(self) -> None:
        cal = ConfidenceCalibrator()
        cal.record(0.5, True)
        cal.reset()
        cal.record(0.7, False)
        assert cal.total_records() == 1
