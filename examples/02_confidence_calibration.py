#!/usr/bin/env python3
"""Example: Confidence Annotation and Calibration

Demonstrates extracting confidence signals from responses,
annotating with levels, and calibrating scores against ground truth.

Usage:
    python examples/02_confidence_calibration.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    AnnotatedResponse,
    ConfidenceAnnotator,
    ConfidenceCalibrator,
    ConfidenceLevel,
    ExtractedSignals,
    SignalExtractor,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: Extract confidence signals from text
    extractor = SignalExtractor()
    responses = [
        ("I'm certain that Python 3.12 released in October 2023.", 0.95),
        ("I believe the answer might be around 42.", 0.55),
        ("I'm not sure, but it could possibly be option B.", 0.30),
    ]

    annotator = ConfidenceAnnotator()
    print("Signal extraction and annotation:")
    for text, raw_score in responses:
        signals: ExtractedSignals = extractor.extract(text)
        annotated: AnnotatedResponse = annotator.annotate(
            text=text, raw_score=raw_score
        )
        print(f"\n  Text: '{text[:55]}'")
        print(f"  Signals: hedges={signals.hedge_count}, "
              f"assertions={signals.assertion_count}")
        print(f"  Level: {annotated.confidence_level.value} "
              f"| Score: {annotated.score:.2f}")

    # Step 2: Calibrate scores against ground truth
    calibrator = ConfidenceCalibrator()
    observations = [
        (0.90, True),   # predicted confident, was correct
        (0.85, True),
        (0.70, False),  # predicted confident, was wrong
        (0.40, False),  # predicted uncertain, was wrong
        (0.30, True),   # predicted uncertain, but was correct
    ]
    for predicted, correct in observations:
        calibrator.record(predicted_score=predicted, was_correct=correct)

    calibration = calibrator.calibrate()
    print(f"\nCalibration results:")
    print(f"  Brier score: {calibration.brier_score:.4f}")
    print(f"  ECE: {calibration.expected_calibration_error:.4f}")
    print(f"  Recommendation: {calibration.recommendation}")


if __name__ == "__main__":
    main()
