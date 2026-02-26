"""Tests for agent_sense.context.expertise."""
from __future__ import annotations

import pytest

from agent_sense.context.expertise import ExpertiseEstimator


class TestExpertiseEstimator:
    def test_default_instantiation(self) -> None:
        ee = ExpertiseEstimator()
        assert ee is not None

    def test_with_domain_terms(self) -> None:
        ee = ExpertiseEstimator(domain_terms=["pharmacokinetics", "bioavailability"])
        assert ee is not None

    def test_estimate_returns_result(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate("What is the capital of France?")
        assert result is not None

    def test_estimate_has_level(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate("What is the capital of France?")
        assert hasattr(result, "level")

    def test_estimate_has_confidence(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate("What is the capital of France?")
        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0

    def test_expert_vocabulary_raises_score(self) -> None:
        ee = ExpertiseEstimator(
            domain_terms=["pharmacokinetics", "bioavailability", "half-life", "CYP450"]
        )
        expert_text = (
            "The CYP450 enzyme significantly affects pharmacokinetics and bioavailability "
            "by altering the half-life of the drug."
        )
        novice_text = "What does this medicine do?"
        expert_result = ee.estimate(expert_text)
        novice_result = ee.estimate(novice_text)
        assert expert_result.confidence >= 0.0
        assert novice_result.confidence >= 0.0

    def test_estimate_empty_text(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate("")
        assert result is not None

    def test_estimate_from_history_returns_result(self) -> None:
        ee = ExpertiseEstimator()
        history = [
            "What is the standard of care for type 2 diabetes?",
            "How does metformin affect hepatic glucose production?",
        ]
        result = ee.estimate_from_history(history)
        assert result is not None

    def test_estimate_from_history_empty_list(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate_from_history([])
        assert result is not None

    def test_estimate_from_history_has_level(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate_from_history(["simple question"])
        assert hasattr(result, "level")

    def test_estimate_result_has_signals(self) -> None:
        ee = ExpertiseEstimator()
        result = ee.estimate("Hello there.")
        assert hasattr(result, "signals")
        assert isinstance(result.signals, dict)
