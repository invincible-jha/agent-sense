"""Accessibility subsystem — WCAG checks, text simplification, screen reader support.

Exports
-------
WCAGChecker
    Run WCAG 2.1 AA heuristic checks on HTML markup.
WCAGViolation
    Dataclass describing a single WCAG violation.
WCAGCriterion
    Enum of WCAG 2.1 success criterion identifiers.
WCAGLevel
    Conformance level enum (A, AA, AAA).
TextSimplifier
    Reduce text complexity toward a target Flesch-Kincaid grade level.
flesch_kincaid_grade
    Compute the Flesch-Kincaid Grade Level for plain text.
ScreenReaderOptimizer
    Add ARIA labels, roles, and landmarks to HTML for screen reader users.
"""
from __future__ import annotations

from agent_sense.accessibility.screen_reader import ScreenReaderOptimizer
from agent_sense.accessibility.simplifier import TextSimplifier, flesch_kincaid_grade
from agent_sense.accessibility.wcag import (
    WCAGChecker,
    WCAGCriterion,
    WCAGLevel,
    WCAGViolation,
)

__all__ = [
    "WCAGChecker",
    "WCAGViolation",
    "WCAGCriterion",
    "WCAGLevel",
    "TextSimplifier",
    "flesch_kincaid_grade",
    "ScreenReaderOptimizer",
]
