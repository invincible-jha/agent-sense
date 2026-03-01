#!/usr/bin/env python3
"""Example: Quickstart — agent-sense

Minimal working example: annotate a response with confidence,
suggest next actions, and check accessibility.

Usage:
    python examples/01_quickstart.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    ChatUI,
    Confidence,
    ConfidenceAnnotator,
    SuggestionEngine,
    SuggestionCategory,
    TextSimplifier,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: Annotate a response with confidence
    response = "The Q3 revenue grew by approximately 18% year-over-year."
    annotator = ConfidenceAnnotator()
    annotated = annotator.annotate(text=response, raw_score=0.87)
    print(f"Response: '{response[:50]}'")
    print(f"  Confidence: {annotated.confidence_level.value} ({annotated.score:.2f})")
    print(f"  Annotation: {annotated.annotation}")

    # Step 2: Simplify text for accessibility
    simplifier = TextSimplifier()
    complex_text = ("The aforementioned financial metrics corroborate the hypothesis "
                    "that operational expenditures have been substantially mitigated.")
    simplified = simplifier.simplify(complex_text)
    print(f"\nOriginal: '{complex_text[:60]}'")
    print(f"Simplified: '{simplified[:60]}'")

    # Step 3: Generate suggestions for the user
    engine = SuggestionEngine()
    suggestions = engine.generate(
        context="User asked about revenue and got an 18% figure.",
        category=SuggestionCategory.FOLLOW_UP,
    )
    print(f"\nSuggestions ({len(suggestions)}):")
    for suggestion in suggestions[:3]:
        print(f"  - {suggestion.text}")

    # Step 4: ChatUI convenience class
    ui = ChatUI(session_id="demo-001")
    ui.send("Hello, can you help me with the Q3 report?")
    print(f"\nChatUI session: {ui.session_id}, "
          f"turns={ui.turn_count()}")


if __name__ == "__main__":
    main()
