"""Suggestion engine — generate contextual follow-up suggestions.

SuggestionEngine produces Suggestion objects for a given conversation state.
Suggestions help users navigate naturally to their next step without having to
formulate their own queries from scratch.

Suggestion categories
---------------------
CLARIFICATION   : Ask the agent to clarify or expand on a response.
NEXT_STEP       : Logical follow-up actions based on the current topic.
RELATED_TOPIC   : Adjacent topics the user might find relevant.
HELP            : Guidance on how to get the most from the agent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class SuggestionCategory(str, Enum):
    """Classification for a suggestion."""

    CLARIFICATION = "clarification"
    NEXT_STEP = "next_step"
    RELATED_TOPIC = "related_topic"
    HELP = "help"


@dataclass(frozen=True)
class Suggestion:
    """A single contextual suggestion presented to the user.

    Attributes
    ----------
    text:
        The suggestion text as it should appear to the user.
    category:
        The SuggestionCategory this suggestion belongs to.
    relevance_score:
        Estimated relevance to the current context, in [0.0, 1.0].
    metadata:
        Optional key/value metadata for downstream tracking or rendering.
    """

    text: str
    category: SuggestionCategory
    relevance_score: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)

    def is_high_relevance(self) -> bool:
        """Return True if relevance_score >= 0.75."""
        return self.relevance_score >= 0.75


# ---------------------------------------------------------------------------
# Built-in suggestion templates
# ---------------------------------------------------------------------------

# Keyword -> list of suggestion text templates.
# Keywords are lower-cased single words or short phrases.
_TOPIC_SUGGESTIONS: dict[str, list[tuple[SuggestionCategory, str]]] = {
    "password": [
        (SuggestionCategory.NEXT_STEP, "Reset your password via account settings"),
        (SuggestionCategory.CLARIFICATION, "Which account are you unable to access?"),
        (SuggestionCategory.RELATED_TOPIC, "Learn about two-factor authentication"),
    ],
    "billing": [
        (SuggestionCategory.NEXT_STEP, "View your current invoice"),
        (SuggestionCategory.NEXT_STEP, "Update your payment method"),
        (SuggestionCategory.RELATED_TOPIC, "Understand your billing cycle"),
    ],
    "error": [
        (SuggestionCategory.CLARIFICATION, "What error message did you see?"),
        (SuggestionCategory.NEXT_STEP, "Check the status page for known incidents"),
        (SuggestionCategory.RELATED_TOPIC, "Browse the troubleshooting guide"),
    ],
    "slow": [
        (SuggestionCategory.CLARIFICATION, "When did you first notice the slowness?"),
        (SuggestionCategory.NEXT_STEP, "Run a connection speed test"),
        (SuggestionCategory.RELATED_TOPIC, "Tips for optimising performance"),
    ],
    "cancel": [
        (SuggestionCategory.CLARIFICATION, "Are you looking to cancel a subscription or order?"),
        (SuggestionCategory.NEXT_STEP, "Review what is included in your current plan"),
        (SuggestionCategory.RELATED_TOPIC, "Explore alternative plans"),
    ],
    "refund": [
        (SuggestionCategory.NEXT_STEP, "Submit a refund request"),
        (SuggestionCategory.CLARIFICATION, "What was the order number?"),
        (SuggestionCategory.RELATED_TOPIC, "Read the refund policy"),
    ],
    "account": [
        (SuggestionCategory.NEXT_STEP, "View your account settings"),
        (SuggestionCategory.RELATED_TOPIC, "Manage notification preferences"),
        (SuggestionCategory.HELP, "How to update your profile information"),
    ],
    "install": [
        (SuggestionCategory.NEXT_STEP, "Download the latest version"),
        (SuggestionCategory.RELATED_TOPIC, "Check system requirements"),
        (SuggestionCategory.HELP, "View the installation guide"),
    ],
    "api": [
        (SuggestionCategory.NEXT_STEP, "Generate an API key"),
        (SuggestionCategory.RELATED_TOPIC, "Browse the API reference documentation"),
        (SuggestionCategory.HELP, "View example API calls"),
    ],
    "data": [
        (SuggestionCategory.NEXT_STEP, "Export your data"),
        (SuggestionCategory.RELATED_TOPIC, "Understand data retention policies"),
        (SuggestionCategory.HELP, "How to import data from another service"),
    ],
}

# Generic fallback suggestions shown when no topic-specific match is found.
_GENERIC_SUGGESTIONS: list[tuple[SuggestionCategory, str]] = [
    (SuggestionCategory.CLARIFICATION, "Could you share more detail?"),
    (SuggestionCategory.HELP, "How can I phrase my question better?"),
    (SuggestionCategory.RELATED_TOPIC, "Browse the help centre"),
    (SuggestionCategory.NEXT_STEP, "Speak to a human agent"),
]


def _extract_keywords(text: str) -> list[str]:
    """Extract lower-cased words from text for keyword matching."""
    return re.findall(r"[a-z]+", text.lower())


class SuggestionEngine:
    """Generate contextual suggestions based on conversation state.

    Parameters
    ----------
    extra_topic_suggestions:
        Optional additional topic -> suggestion mappings to merge with the
        built-in library. Values follow the same format:
        ``list[tuple[SuggestionCategory, str]]``.
    max_suggestions:
        Maximum number of suggestions to return per call. Defaults to 4.

    Example
    -------
    >>> engine = SuggestionEngine()
    >>> suggestions = engine.suggest("I cannot reset my password", history=[])
    >>> any(s.category == SuggestionCategory.NEXT_STEP for s in suggestions)
    True
    """

    def __init__(
        self,
        extra_topic_suggestions: dict[
            str, list[tuple[SuggestionCategory, str]]
        ] | None = None,
        max_suggestions: int = 4,
    ) -> None:
        self._topic_map: dict[str, list[tuple[SuggestionCategory, str]]] = dict(
            _TOPIC_SUGGESTIONS
        )
        if extra_topic_suggestions:
            for topic, items in extra_topic_suggestions.items():
                existing = self._topic_map.get(topic, [])
                self._topic_map[topic] = existing + items
        self._max_suggestions = max(1, max_suggestions)

    def suggest(
        self,
        user_text: str,
        history: list[str] | None = None,
        categories: list[SuggestionCategory] | None = None,
    ) -> list[Suggestion]:
        """Generate suggestions for the current user message.

        Parameters
        ----------
        user_text:
            The most recent user input or agent response to generate suggestions
            for.
        history:
            Optional prior user messages. Used to detect recently-shown topics
            and reduce repetition.
        categories:
            If provided, only suggestions belonging to these categories are
            returned. Defaults to all categories.

        Returns
        -------
        list[Suggestion]
            Up to ``max_suggestions`` Suggestion objects, ordered by relevance.
        """
        keywords = _extract_keywords(user_text)
        history_keywords: set[str] = set()
        for prior in (history or []):
            history_keywords.update(_extract_keywords(prior))

        collected: list[Suggestion] = []
        seen_texts: set[str] = set()

        for keyword in keywords:
            if keyword not in self._topic_map:
                continue
            for category, text in self._topic_map[keyword]:
                if text in seen_texts:
                    continue
                # Slightly reduce score for topics already in history.
                score = 0.95 if keyword in history_keywords else 1.0
                seen_texts.add(text)
                collected.append(
                    Suggestion(
                        text=text,
                        category=category,
                        relevance_score=round(score, 3),
                    )
                )

        # Fill up to max_suggestions with generic suggestions.
        for category, text in _GENERIC_SUGGESTIONS:
            if len(collected) >= self._max_suggestions:
                break
            if text in seen_texts:
                continue
            seen_texts.add(text)
            collected.append(
                Suggestion(
                    text=text,
                    category=category,
                    relevance_score=0.5,
                )
            )

        # Apply category filter.
        if categories is not None:
            allowed = set(categories)
            collected = [s for s in collected if s.category in allowed]

        # Sort by relevance descending, then stable by original order.
        collected.sort(key=lambda s: s.relevance_score, reverse=True)
        return collected[: self._max_suggestions]

    def suggest_for_low_confidence(self) -> list[Suggestion]:
        """Return suggestions appropriate when the agent has low confidence.

        Returns
        -------
        list[Suggestion]
            Suggestions encouraging user clarification or human escalation.
        """
        return [
            Suggestion(
                text="Could you give me more context or details?",
                category=SuggestionCategory.CLARIFICATION,
                relevance_score=1.0,
            ),
            Suggestion(
                text="Speak to a human agent for further help",
                category=SuggestionCategory.NEXT_STEP,
                relevance_score=0.95,
            ),
            Suggestion(
                text="Rephrase your question in different words",
                category=SuggestionCategory.HELP,
                relevance_score=0.85,
            ),
        ]
