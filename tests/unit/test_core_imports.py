"""Tests to ensure core module imports work and coverage is achieved."""
from __future__ import annotations


def test_core_package_import() -> None:
    import agent_sense.core
    assert agent_sense.core is not None


def test_agent_sense_top_level_import() -> None:
    import agent_sense
    assert agent_sense is not None
