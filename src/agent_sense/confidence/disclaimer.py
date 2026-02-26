"""Disclaimer generator — auto-generate disclaimers for low-confidence responses.

DisclaimerGenerator appends or prepends a short disclaimer to agent responses
when their confidence level is LOW or UNKNOWN, prompting users to verify
information independently.
"""
from __future__ import annotations

from agent_sense.confidence.annotator import AnnotatedResponse, ConfidenceLevel


_DISCLAIMER_TEMPLATES: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.LOW: (
        "Note: I am not fully certain about this response. "
        "Please verify with an authoritative source."
    ),
    ConfidenceLevel.UNKNOWN: (
        "I do not have enough information to answer this confidently. "
        "Please consult a qualified professional."
    ),
}


class DisclaimerGenerator:
    """Generate disclaimers for low-confidence annotated responses.

    Parameters
    ----------
    prepend:
        If True, place the disclaimer before the response text. If False
        (default), append it after.

    Example
    -------
    >>> from agent_sense.confidence.annotator import ConfidenceAnnotator
    >>> annotator = ConfidenceAnnotator()
    >>> response = annotator.annotate("Maybe Paris?", score=0.25)
    >>> gen = DisclaimerGenerator()
    >>> gen.generate(response)
    'Maybe Paris? Note: I am not fully certain...'
    """

    def __init__(self, prepend: bool = False) -> None:
        self._prepend = prepend

    def generate(self, response: AnnotatedResponse) -> str:
        """Return the response text with a disclaimer appended/prepended if needed.

        Parameters
        ----------
        response:
            An AnnotatedResponse from ConfidenceAnnotator.

        Returns
        -------
        str
            The original content unchanged if confidence is HIGH or MEDIUM.
            Otherwise, the content with a disclaimer added.
        """
        disclaimer = _DISCLAIMER_TEMPLATES.get(response.confidence_level)
        if disclaimer is None:
            return response.content
        if self._prepend:
            return f"{disclaimer} {response.content}"
        return f"{response.content} {disclaimer}"

    def disclaimer_text(self, level: ConfidenceLevel) -> str:
        """Return the raw disclaimer text for a given ConfidenceLevel.

        Parameters
        ----------
        level:
            The ConfidenceLevel to look up.

        Returns
        -------
        str
            Disclaimer text, or empty string if none is needed for this level.
        """
        return _DISCLAIMER_TEMPLATES.get(level, "")
