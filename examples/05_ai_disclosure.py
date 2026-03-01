#!/usr/bin/env python3
"""Example: AI Disclosure and Transparency Reporting

Demonstrates generating AI identity disclosures, transparency
reports, and contextual disclosure statements.

Usage:
    python examples/05_ai_disclosure.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    AIDisclosure,
    AIDisclosureCard,
    DisclosureLevel,
    DisclosureTone,
    DisclosureStatement,
    SessionStats,
    TransparencyReport,
    build_disclosure,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: Create AI disclosure with different tones
    disclosure = AIDisclosure(
        agent_name="AumOS Assistant",
        provider="MuVeraAI",
        capabilities=["text analysis", "document summarisation", "Q&A"],
        limitations=["no real-time data", "may hallucinate facts"],
    )

    for tone in [DisclosureTone.FRIENDLY, DisclosureTone.FORMAL, DisclosureTone.BRIEF]:
        statement: DisclosureStatement = disclosure.generate(tone=tone)
        print(f"\n[{tone.value}] {statement.text[:100]}")

    # Step 2: Build a disclosure card (structured)
    card: AIDisclosureCard = build_disclosure(
        agent_name="AumOS Assistant",
        level=DisclosureLevel.STANDARD,
        is_ai=True,
        provider="MuVeraAI",
    )
    print(f"\nDisclosure card:")
    print(f"  Agent: {card.agent_name}")
    print(f"  Is AI: {card.is_ai}")
    print(f"  Level: {card.level.value}")

    # Step 3: Transparency report for a session
    stats = SessionStats(
        session_id="session-099",
        total_turns=12,
        ai_turns=10,
        human_turns=2,
        tool_calls=5,
        handoffs=1,
        tokens_used=3_200,
        cost_usd=0.0064,
    )
    reporter = TransparencyReport(stats=stats, disclosure=disclosure)
    report = reporter.generate()
    print(f"\nTransparency report for session '{stats.session_id}':")
    print(f"  Turns: {report.total_turns} (AI={report.ai_turns}, human={report.human_turns})")
    print(f"  Tool calls: {report.tool_calls}")
    print(f"  Tokens used: {report.tokens_used:,}")
    print(f"  Estimated cost: ${report.cost_usd:.4f}")
    print(f"  AI ratio: {report.ai_ratio:.0%}")


if __name__ == "__main__":
    main()
