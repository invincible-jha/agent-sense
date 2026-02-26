"""Confidence calibrator — align predicted scores against empirical outcomes.

ConfidenceCalibrator tracks (predicted_score, was_correct) pairs and computes
calibration quality metrics. A well-calibrated model produces a predicted
probability of 0.7 that is correct exactly 70 % of the time.

Metrics
-------
- Expected Calibration Error (ECE): mean |avg_confidence - accuracy| per bin.
- reliability_diagram: bin-level breakdown for plotting.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Number of equal-width bins in [0, 1] for calibration computation.
_DEFAULT_BIN_COUNT: int = 10


@dataclass
class _CalibrationBin:
    """Accumulator for a single confidence bin."""

    total_confidence: float = 0.0
    correct_count: int = 0
    total_count: int = 0

    def average_confidence(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.total_confidence / self.total_count

    def accuracy(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.correct_count / self.total_count


class ConfidenceCalibrator:
    """Calibrate predicted confidence scores against empirical correctness.

    Records predictions and their ground-truth outcomes, then computes
    Expected Calibration Error (ECE) and a reliability diagram suitable
    for visualisation.

    Parameters
    ----------
    bin_count:
        Number of equal-width bins to use for calibration. Defaults to 10.

    Example
    -------
    >>> cal = ConfidenceCalibrator()
    >>> cal.record(0.9, True)
    >>> cal.record(0.4, False)
    >>> cal.calibration_error()
    0.0
    """

    def __init__(self, bin_count: int = _DEFAULT_BIN_COUNT) -> None:
        if bin_count < 1:
            raise ValueError(f"bin_count must be >= 1; got {bin_count!r}.")
        self._bin_count: int = bin_count
        self._bins: list[_CalibrationBin] = [
            _CalibrationBin() for _ in range(bin_count)
        ]
        self._total_records: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def record(self, predicted: float, actual_correct: bool) -> None:
        """Record a single prediction and its empirical outcome.

        Parameters
        ----------
        predicted:
            The model's predicted confidence score in [0.0, 1.0].
        actual_correct:
            Whether the prediction was ultimately correct (True) or not (False).

        Raises
        ------
        ValueError
            If ``predicted`` is outside [0.0, 1.0].
        """
        if not 0.0 <= predicted <= 1.0:
            raise ValueError(
                f"Predicted score must be in [0.0, 1.0]; got {predicted!r}."
            )
        bin_index = self._bin_index(predicted)
        bucket = self._bins[bin_index]
        bucket.total_confidence += predicted
        bucket.total_count += 1
        if actual_correct:
            bucket.correct_count += 1
        self._total_records += 1

    def calibration_error(self) -> float:
        """Compute the Expected Calibration Error (ECE).

        ECE is the weighted average of |avg_confidence - accuracy| across all
        non-empty bins, where the weight is the fraction of total samples in
        each bin.

        Returns
        -------
        float
            ECE in [0.0, 1.0]. Returns 0.0 if no records have been added.
        """
        if self._total_records == 0:
            return 0.0

        ece: float = 0.0
        for bucket in self._bins:
            if bucket.total_count == 0:
                continue
            bin_weight = bucket.total_count / self._total_records
            gap = abs(bucket.average_confidence() - bucket.accuracy())
            ece += bin_weight * gap
        return round(ece, 6)

    def reliability_diagram(self) -> dict[str, list[float]]:
        """Return bin-level data suitable for plotting a reliability diagram.

        Returns
        -------
        dict[str, list[float]]
            A dict with keys:
            - ``"bin_lower"``: lower boundary of each bin.
            - ``"bin_upper"``: upper boundary of each bin.
            - ``"avg_confidence"``: mean predicted score per bin (0.0 for empty).
            - ``"accuracy"``: empirical accuracy per bin (0.0 for empty).
            - ``"sample_fraction"``: fraction of total records in each bin.
        """
        bin_width = 1.0 / self._bin_count
        bin_lower: list[float] = []
        bin_upper: list[float] = []
        avg_confidence: list[float] = []
        accuracy: list[float] = []
        sample_fraction: list[float] = []

        for index, bucket in enumerate(self._bins):
            lower = round(index * bin_width, 10)
            upper = round(lower + bin_width, 10)
            fraction = (
                bucket.total_count / self._total_records
                if self._total_records > 0
                else 0.0
            )
            bin_lower.append(lower)
            bin_upper.append(upper)
            avg_confidence.append(round(bucket.average_confidence(), 6))
            accuracy.append(round(bucket.accuracy(), 6))
            sample_fraction.append(round(fraction, 6))

        return {
            "bin_lower": bin_lower,
            "bin_upper": bin_upper,
            "avg_confidence": avg_confidence,
            "accuracy": accuracy,
            "sample_fraction": sample_fraction,
        }

    def total_records(self) -> int:
        """Return the number of (predicted, actual) pairs recorded so far."""
        return self._total_records

    def reset(self) -> None:
        """Clear all recorded data and reset bins to empty."""
        self._bins = [_CalibrationBin() for _ in range(self._bin_count)]
        self._total_records = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bin_index(self, score: float) -> int:
        """Map a score in [0, 1] to a bin index in [0, bin_count - 1]."""
        # A score of exactly 1.0 maps to the last bin.
        index = int(score * self._bin_count)
        return min(index, self._bin_count - 1)
