"""Tests for agent_sense.disclosure.ai_disclosure."""
from __future__ import annotations

import pytest

from agent_sense.disclosure.ai_disclosure import AIDisclosure, DisclosureTone


class TestAIDisclosureGenerate:
    def test_generate_initial_greeting(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("initial_greeting")
        assert stmt is not None
        assert stmt.text != ""

    def test_generate_response_caveat(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("response_caveat")
        assert stmt.text != ""

    def test_generate_handoff_notice(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("handoff_notice")
        assert stmt.text != ""

    def test_generate_data_usage_notice(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("data_usage_notice")
        assert stmt.text != ""

    def test_generate_includes_agent_name(self) -> None:
        ai = AIDisclosure(agent_name="MyAgent", org_name="MyOrg")
        stmt = ai.generate("initial_greeting")
        assert "MyAgent" in stmt.text

    def test_generate_with_explicit_tone(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("initial_greeting", tone=DisclosureTone.FORMAL)
        assert stmt.tone == DisclosureTone.FORMAL

    def test_generate_has_template_name(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        stmt = ai.generate("initial_greeting")
        assert stmt.template_name == "initial_greeting"

    def test_generate_unknown_template_raises(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        with pytest.raises((KeyError, ValueError)):
            ai.generate("unknown_template_xyz")


class TestAIDisclosureGenerateAll:
    def test_generate_all_returns_dict(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.generate_all()
        assert isinstance(result, dict)

    def test_generate_all_has_expected_keys(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.generate_all()
        assert "initial_greeting" in result
        assert "response_caveat" in result

    def test_generate_all_with_tone(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.generate_all(tone=DisclosureTone.CONCISE)
        for stmt in result.values():
            assert stmt.tone == DisclosureTone.CONCISE


class TestAIDisclosureAvailableTemplates:
    def test_returns_list(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.available_templates()
        assert isinstance(result, list)

    def test_contains_initial_greeting(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.available_templates()
        assert "initial_greeting" in result

    def test_returns_sorted_list(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        result = ai.available_templates()
        assert result == sorted(result)


class TestAIDisclosureSetTone:
    def test_set_tone_changes_default(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        ai.set_tone(DisclosureTone.FORMAL)
        stmt = ai.generate("initial_greeting")
        assert stmt.tone == DisclosureTone.FORMAL

    def test_set_tone_concise(self) -> None:
        ai = AIDisclosure(agent_name="TestBot", org_name="TestOrg")
        ai.set_tone(DisclosureTone.CONCISE)
        stmt = ai.generate("initial_greeting")
        assert stmt.tone == DisclosureTone.CONCISE
