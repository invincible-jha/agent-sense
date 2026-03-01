#!/usr/bin/env python3
"""Example: SenseMiddleware Pipeline

Demonstrates the SenseMiddleware pipeline that combines confidence
annotation, suggestion generation, and interaction tracking.

Usage:
    python examples/06_sense_middleware.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    ContextDetector,
    DeviceType,
    ExpertiseEstimator,
    ExpertiseLevel,
    InteractionResult,
    NetworkQuality,
    SenseMiddleware,
    SituationAssessor,
    SituationVector,
    SuggestionEngine,
    SuggestionCategory,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: Detect context (device, network, expertise)
    detector = ContextDetector()
    context = detector.detect(hints={
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17)",
        "connection": "4G",
    })
    print(f"Context: device={context.device_type.value}, "
          f"network={context.network_quality.value}")

    # Step 2: Estimate user expertise level
    estimator = ExpertiseEstimator()
    sample_messages = [
        "Can you explain how the gradient descent works?",
        "What is a hyperparameter?",
        "Show me a confusion matrix interpretation.",
    ]
    expertise: ExpertiseLevel = estimator.estimate(messages=sample_messages)
    print(f"Expertise level: {expertise.value}")

    # Step 3: Build situation vector and assess
    assessor = SituationAssessor()
    vector: SituationVector = assessor.assess(
        device_type=context.device_type,
        expertise=expertise,
        network_quality=context.network_quality,
    )
    print(f"Situation: needs_simplification={vector.needs_simplification}, "
          f"accessibility_needs={[n.value for n in vector.accessibility_needs]}")

    # Step 4: Process interactions through SenseMiddleware
    middleware = SenseMiddleware()
    interactions = [
        {
            "query": "What is the quarterly revenue trend?",
            "response": "Revenue grew 18% in Q3, with enterprise tier leading.",
            "raw_confidence": 0.88,
        },
        {
            "query": "Predict next quarter precisely.",
            "response": "I cannot make precise financial predictions.",
            "raw_confidence": 0.35,
        },
    ]

    print("\nMiddleware pipeline results:")
    for interaction in interactions:
        result: InteractionResult = middleware.process(
            query=str(interaction["query"]),
            response=str(interaction["response"]),
            raw_confidence=float(interaction["raw_confidence"]),  # type: ignore[arg-type]
            situation=vector,
        )
        print(f"\n  Query: '{result.query[:45]}'")
        print(f"  Confidence: {result.confidence_level.value} ({result.confidence_score:.2f})")
        print(f"  Suggestions: {len(result.suggestions)}")


if __name__ == "__main__":
    main()
