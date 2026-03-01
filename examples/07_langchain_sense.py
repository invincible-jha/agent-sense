#!/usr/bin/env python3
"""Example: LangChain Sense Integration

Demonstrates wrapping LangChain outputs with confidence annotation,
disclosure, and human handoff detection.

Usage:
    python examples/07_langchain_sense.py

Requirements:
    pip install agent-sense
    pip install langchain   # optional — example degrades gracefully
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    AIDisclosure,
    ConfidenceAnnotator,
    DisclosureTone,
    HandoffPackager,
    HandoffRouter,
    HumanAgent,
    SenseMiddleware,
    SituationVector,
    UrgencyLevel,
)

try:
    from langchain.schema.runnable import RunnableLambda
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False


def sense_wrapped_chain(query: str, confidence_threshold: float = 0.5) -> dict[str, object]:
    """Invoke an LLM chain and annotate the response with sense."""
    # Simulate LangChain chain output
    if _LANGCHAIN_AVAILABLE:
        chain = RunnableLambda(lambda q: {
            "text": f"Based on available data, {q[:30]}... result is approximately 42.",
            "raw_confidence": 0.75,
        })
        output = chain.invoke(query)
    else:
        output = {
            "text": f"Based on available data, the result is approximately 42.",
            "raw_confidence": 0.40,
        }

    annotator = ConfidenceAnnotator()
    annotated = annotator.annotate(
        text=str(output["text"]),
        raw_score=float(output["raw_confidence"]),  # type: ignore[arg-type]
    )

    needs_handoff = annotated.score < confidence_threshold
    return {
        "response": annotated.text,
        "confidence": annotated.confidence_level.value,
        "score": annotated.score,
        "needs_handoff": needs_handoff,
    }


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    if not _LANGCHAIN_AVAILABLE:
        print("LangChain not installed — demonstrating sense layer only.")
        print("Install with: pip install langchain")

    # AI Disclosure before any response
    disclosure = AIDisclosure(
        agent_name="AumOS LangChain Agent",
        provider="MuVeraAI",
        capabilities=["question answering", "analysis"],
        limitations=["no real-time data"],
    )
    stmt = disclosure.generate(DisclosureTone.BRIEF)
    print(f"Disclosure: {stmt.text}")

    # Process queries through sense-wrapped chain
    queries = [
        "What is the projected revenue for next quarter?",
        "What is 2 + 2?",
    ]

    router = HandoffRouter()
    router.register(HumanAgent(
        agent_id="human-support-1",
        skills=["finance", "analysis"],
        available=True,
    ))
    packager = HandoffPackager()

    for query in queries:
        result = sense_wrapped_chain(query, confidence_threshold=0.5)
        print(f"\nQuery: '{query[:50]}'")
        print(f"  Response: '{str(result['response'])[:55]}'")
        print(f"  Confidence: {result['confidence']} ({result['score']:.2f})")

        if result["needs_handoff"]:
            package = packager.package(
                session_id="lc-session",
                summary=f"Low-confidence response to: {query}",
                conversation_history=[],
                urgency=UrgencyLevel.NORMAL,
                reason="Confidence below threshold.",
            )
            print(f"  Handoff triggered (urgency={package.urgency.value})")


if __name__ == "__main__":
    main()
