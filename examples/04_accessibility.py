#!/usr/bin/env python3
"""Example: Accessibility Checking and Text Simplification

Demonstrates WCAG compliance checking, text simplification for
reading level, and screen reader optimisation.

Usage:
    python examples/04_accessibility.py

Requirements:
    pip install agent-sense
"""
from __future__ import annotations

import agent_sense
from agent_sense import (
    ScreenReaderOptimizer,
    TextSimplifier,
    WCAGChecker,
    WCAGLevel,
    WCAGViolation,
    flesch_kincaid_grade,
)


def main() -> None:
    print(f"agent-sense version: {agent_sense.__version__}")

    # Step 1: WCAG compliance check
    checker = WCAGChecker(level=WCAGLevel.AA)
    ui_components = [
        {"type": "image", "alt": "", "src": "chart.png"},
        {"type": "button", "label": "Submit", "aria_label": "Submit form"},
        {"type": "link", "text": "Click here", "href": "/details"},
        {"type": "input", "label": "Email address", "required": True},
    ]

    violations: list[WCAGViolation] = []
    for component in ui_components:
        component_violations = checker.check(component)
        violations.extend(component_violations)

    print(f"WCAG {checker.level.value} check: {len(violations)} violation(s)")
    for violation in violations:
        print(f"  [{violation.criterion}] {violation.description[:60]}")

    # Step 2: Text simplification
    simplifier = TextSimplifier(target_grade=8)
    complex_texts = [
        "The utilisation of sophisticated algorithms facilitates the expeditious "
        "retrieval of pertinent information.",
        "Please click the button to proceed.",
    ]

    print("\nText simplification:")
    for text in complex_texts:
        grade = flesch_kincaid_grade(text)
        simplified = simplifier.simplify(text)
        simplified_grade = flesch_kincaid_grade(simplified)
        print(f"\n  Original (grade {grade:.1f}): '{text[:55]}'")
        print(f"  Simplified (grade {simplified_grade:.1f}): '{simplified[:55]}'")

    # Step 3: Screen reader optimisation
    optimizer = ScreenReaderOptimizer()
    html_snippet = (
        "<button>X</button>"
        "<img src='graph.png'/>"
        "<span>Revenue increased by 18%</span>"
    )
    optimized = optimizer.optimize(html_snippet)
    print(f"\nScreen reader optimised: {len(optimized)} characters")
    print(f"  {optimized[:120]}")


if __name__ == "__main__":
    main()
