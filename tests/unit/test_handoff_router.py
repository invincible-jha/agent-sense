"""Tests for agent_sense.handoff.router."""
from __future__ import annotations

import pytest

from agent_sense.handoff.packager import HandoffPackager
from agent_sense.handoff.router import HandoffRouter, HumanAgent, NoAvailableAgentError


def _make_package(summary: str = "User needs help") -> object:
    packager = HandoffPackager(session_id="session-001")
    return packager.package(summary=summary)


def _make_agent(
    agent_id: str = "a1",
    name: str = "Alice",
    skills: frozenset[str] | None = None,
    is_available: bool = True,
    current_load: int = 0,
    max_load: int = 5,
) -> HumanAgent:
    if skills is None:
        skills = frozenset(["general"])
    return HumanAgent(
        agent_id=agent_id,
        name=name,
        skills=skills,
        is_available=is_available,
        current_load=current_load,
        max_load=max_load,
    )


class TestHandoffRouterRoute:
    def test_routes_to_available_agent(self) -> None:
        agent = _make_agent()
        router = HandoffRouter(agents=[agent])
        result = router.route(_make_package())
        assert result.agent_id == "a1"

    def test_no_agents_raises_no_available_agent_error(self) -> None:
        router = HandoffRouter(agents=[])
        with pytest.raises(NoAvailableAgentError):
            router.route(_make_package())

    def test_unavailable_agent_raises_error(self) -> None:
        agent = _make_agent(is_available=False)
        router = HandoffRouter(agents=[agent])
        with pytest.raises(NoAvailableAgentError):
            router.route(_make_package())

    def test_overloaded_agent_raises_error(self) -> None:
        agent = _make_agent(current_load=5, max_load=5)
        router = HandoffRouter(agents=[agent])
        with pytest.raises(NoAvailableAgentError):
            router.route(_make_package())

    def test_routes_to_least_loaded_agent(self) -> None:
        agent_busy = _make_agent(agent_id="busy", current_load=4)
        agent_free = _make_agent(agent_id="free", current_load=0)
        router = HandoffRouter(agents=[agent_busy, agent_free])
        result = router.route(_make_package())
        assert result.agent_id == "free"

    def test_available_subset_filtering(self) -> None:
        agent1 = _make_agent(agent_id="a1")
        agent2 = _make_agent(agent_id="a2")
        router = HandoffRouter(agents=[agent1, agent2])
        result = router.route(_make_package(), available=[agent2])
        assert result.agent_id == "a2"

    def test_default_no_agents(self) -> None:
        router = HandoffRouter()
        with pytest.raises(NoAvailableAgentError):
            router.route(_make_package())


class TestHandoffRouterAddAgent:
    def test_add_agent_allows_routing(self) -> None:
        router = HandoffRouter()
        agent = _make_agent()
        router.add_agent(agent)
        result = router.route(_make_package())
        assert result.agent_id == "a1"

    def test_add_multiple_agents(self) -> None:
        router = HandoffRouter()
        router.add_agent(_make_agent(agent_id="a1"))
        router.add_agent(_make_agent(agent_id="a2"))
        result = router.route(_make_package())
        assert result.agent_id in ("a1", "a2")
