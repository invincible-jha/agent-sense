"""Test that the 3-line quickstart API works for agent-sense."""
from __future__ import annotations


def test_quickstart_chat_ui_import() -> None:
    from agent_sense import ChatUI

    ui = ChatUI()
    assert ui is not None


def test_quickstart_confidence_import() -> None:
    from agent_sense import Confidence

    conf = Confidence(0.87)
    assert conf is not None


def test_quickstart_confidence_score() -> None:
    from agent_sense import Confidence

    conf = Confidence(0.95)
    assert conf.score == 0.95


def test_quickstart_confidence_level() -> None:
    from agent_sense import Confidence

    conf = Confidence(0.9)
    assert isinstance(conf.level, str)
    assert len(conf.level) > 0


def test_quickstart_annotate() -> None:
    from agent_sense import ChatUI
    from agent_sense.confidence.annotator import AnnotatedResponse

    ui = ChatUI()
    annotated = ui.annotate("Paris is the capital of France.", score=0.92)
    assert isinstance(annotated, AnnotatedResponse)
    assert annotated.score == 0.92


def test_quickstart_repr() -> None:
    from agent_sense import ChatUI, Confidence

    ui = ChatUI()
    assert "ChatUI" in repr(ui)

    conf = Confidence(0.75)
    assert "Confidence" in repr(conf)
    assert "0.75" in repr(conf)
