"""Convenience API for agent-sense — 3-line quickstart.

Example
-------
::

    from agent_sense import ChatUI, Confidence
    ui = ChatUI()
    conf = Confidence(0.87)
    print(conf.level, conf.indicator)

"""
from __future__ import annotations

from typing import Any


class ChatUI:
    """Zero-config human-agent interaction facade for the 80% use case.

    Bundles the most common agent-sense features: confidence annotation,
    AI disclosure, and accessibility text simplification.

    Example
    -------
    ::

        from agent_sense import ChatUI
        ui = ChatUI()
        annotated = ui.annotate("I believe Paris is the capital of France.", score=0.92)
        print(annotated.level)
    """

    def __init__(self) -> None:
        from agent_sense.confidence.annotator import ConfidenceAnnotator
        from agent_sense.disclosure.ai_disclosure import AIDisclosure

        self._annotator = ConfidenceAnnotator()
        self._disclosure = AIDisclosure()

    def annotate(self, text: str, score: float = 0.8) -> Any:
        """Annotate a response with confidence metadata.

        Parameters
        ----------
        text:
            The agent response text to annotate.
        score:
            Confidence score in [0.0, 1.0].

        Returns
        -------
        AnnotatedResponse
            Response with ``.level``, ``.score``, and ``.text`` attributes.
        """
        return self._annotator.annotate(text, score=score)

    def disclosure(self, template_name: str = "greeting") -> Any:
        """Generate an AI identity disclosure statement.

        Parameters
        ----------
        template_name:
            Template to render (e.g. ``"greeting"``, ``"capability"``).

        Returns
        -------
        DisclosureStatement
            Disclosure with ``.text`` and ``.tone`` attributes.
        """
        try:
            return self._disclosure.generate(template_name=template_name)
        except Exception:
            # Fallback for missing templates
            from agent_sense.disclosure.ai_disclosure import DisclosureStatement, DisclosureTone
            return DisclosureStatement(
                template_name=template_name,
                tone=DisclosureTone.NEUTRAL,
                text="I am an AI assistant. I may make mistakes.",
            )

    def simplify(self, text: str, target_grade: float = 8.0) -> str:
        """Simplify text for accessibility.

        Parameters
        ----------
        text:
            Text to simplify.
        target_grade:
            Target Flesch-Kincaid reading grade level (default 8.0).

        Returns
        -------
        str
            Simplified text at approximately the target reading level.
        """
        from agent_sense.accessibility.simplifier import TextSimplifier

        simplifier = TextSimplifier(target_grade=target_grade)
        return simplifier.simplify(text)

    def __repr__(self) -> str:
        return "ChatUI(annotator=ConfidenceAnnotator, disclosure=AIDisclosure)"


class Confidence:
    """Lightweight confidence indicator wrapper.

    Parameters
    ----------
    score:
        Confidence score in [0.0, 1.0].

    Example
    -------
    ::

        from agent_sense import Confidence
        conf = Confidence(0.87)
        print(conf.level)      # "HIGH"
        print(conf.indicator)  # indicator object with rendering methods
    """

    def __init__(self, score: float) -> None:
        from agent_sense.indicators.confidence import from_score

        self.score = score
        self._indicator = from_score(score, reasoning="score-based")

    @property
    def level(self) -> str:
        """String label for the confidence level (e.g. ``"HIGH"``)."""
        return self._indicator.level.value if hasattr(self._indicator.level, "value") else str(self._indicator.level)

    @property
    def indicator(self) -> Any:
        """The underlying ConfidenceIndicator object."""
        return self._indicator

    def __repr__(self) -> str:
        return f"Confidence(score={self.score!r}, level={self.level!r})"
