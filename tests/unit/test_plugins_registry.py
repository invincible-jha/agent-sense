"""Tests for agent_sense.plugins.registry."""
from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

from agent_sense.plugins.registry import (
    PluginAlreadyRegisteredError,
    PluginNotFoundError,
    PluginRegistry,
)


class BaseTestPlugin(ABC):
    @abstractmethod
    def run(self) -> str:
        ...


class ConcretePluginA(BaseTestPlugin):
    def run(self) -> str:
        return "A"


class ConcretePluginB(BaseTestPlugin):
    def run(self) -> str:
        return "B"


def _make_registry() -> PluginRegistry[BaseTestPlugin]:
    return PluginRegistry(BaseTestPlugin, "test-registry")


class TestPluginRegistryBasics:
    def test_empty_registry_has_zero_plugins(self) -> None:
        reg = _make_registry()
        assert len(reg) == 0

    def test_list_plugins_empty(self) -> None:
        reg = _make_registry()
        assert reg.list_plugins() == []

    def test_repr_includes_name(self) -> None:
        reg = _make_registry()
        assert "test-registry" in repr(reg)


class TestPluginRegistryRegisterDecorator:
    def test_register_decorator_adds_plugin(self) -> None:
        reg = _make_registry()

        @reg.register("plugin-a")
        class MyPlugin(BaseTestPlugin):
            def run(self) -> str:
                return "a"

        assert "plugin-a" in reg

    def test_register_decorator_returns_class_unchanged(self) -> None:
        reg = _make_registry()

        @reg.register("plugin-x")
        class MyPlugin(BaseTestPlugin):
            def run(self) -> str:
                return "x"

        assert MyPlugin().run() == "x"

    def test_register_decorator_duplicate_name_raises(self) -> None:
        reg = _make_registry()
        reg.register_class("dup", ConcretePluginA)

        with pytest.raises(PluginAlreadyRegisteredError):
            @reg.register("dup")
            class AnotherPlugin(BaseTestPlugin):
                def run(self) -> str:
                    return "dup"

    def test_register_decorator_non_subclass_raises(self) -> None:
        reg = _make_registry()

        with pytest.raises(TypeError):
            @reg.register("bad")  # type: ignore[arg-type]
            class NotAPlugin:
                def run(self) -> str:
                    return "x"

    def test_register_duplicate_raises(self) -> None:
        reg = _make_registry()
        reg.register_class("dup", ConcretePluginA)
        with pytest.raises(PluginAlreadyRegisteredError):
            reg.register_class("dup", ConcretePluginB)

    def test_register_non_subclass_raises(self) -> None:
        reg = _make_registry()

        class NotAPlugin:
            def run(self) -> str:
                return "x"

        with pytest.raises(TypeError):
            reg.register_class("bad-plugin", NotAPlugin)  # type: ignore[arg-type]


class TestPluginRegistryRegisterClass:
    def test_register_class_directly(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        assert "plugin-a" in reg

    def test_register_class_duplicate_raises(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        with pytest.raises(PluginAlreadyRegisteredError):
            reg.register_class("plugin-a", ConcretePluginB)


class TestPluginRegistryGet:
    def test_get_registered_plugin(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        cls = reg.get("plugin-a")
        assert cls is ConcretePluginA

    def test_get_missing_raises(self) -> None:
        reg = _make_registry()
        with pytest.raises(PluginNotFoundError):
            reg.get("missing")

    def test_get_returns_instantiable_class(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        cls = reg.get("plugin-a")
        instance = cls()
        assert instance.run() == "A"


class TestPluginRegistryDeregister:
    def test_deregister_removes_plugin(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        reg.deregister("plugin-a")
        assert "plugin-a" not in reg

    def test_deregister_missing_raises(self) -> None:
        reg = _make_registry()
        with pytest.raises(PluginNotFoundError):
            reg.deregister("missing")


class TestPluginRegistryListPlugins:
    def test_list_plugins_sorted(self) -> None:
        reg = _make_registry()
        reg.register_class("z-plugin", ConcretePluginA)
        reg.register_class("a-plugin", ConcretePluginB)
        result = reg.list_plugins()
        assert result == ["a-plugin", "z-plugin"]

    def test_len_matches_registered_count(self) -> None:
        reg = _make_registry()
        reg.register_class("p1", ConcretePluginA)
        reg.register_class("p2", ConcretePluginB)
        assert len(reg) == 2


class TestPluginRegistryLoadEntrypoints:
    def test_load_entrypoints_nonexistent_group_noop(self) -> None:
        reg = _make_registry()
        reg.load_entrypoints("nonexistent.group.xyz")
        assert len(reg) == 0

    def test_load_entrypoints_idempotent(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        # Calling load_entrypoints should not raise even if group is empty
        reg.load_entrypoints("nonexistent.group.xyz")
        assert "plugin-a" in reg


class TestPluginRegistryContains:
    def test_in_operator_true(self) -> None:
        reg = _make_registry()
        reg.register_class("plugin-a", ConcretePluginA)
        assert "plugin-a" in reg

    def test_in_operator_false(self) -> None:
        reg = _make_registry()
        assert "missing" not in reg
