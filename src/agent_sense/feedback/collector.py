"""FeedbackCollector and FeedbackAggregator — structured user feedback.

FeedbackCollector: collect ratings (1-5), categories, and free text.
FeedbackAggregator: compute satisfaction scores and identify patterns.
"""

from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class FeedbackCategory(str, Enum):
    """Category labels for user feedback."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"
    HARMFUL = "harmful"
    IRRELEVANT = "irrelevant"
    INACCURATE = "inaccurate"
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    OTHER = "other"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class FeedbackEntry:
    """A single structured feedback submission from a user.

    Parameters
    ----------
    rating:
        Satisfaction rating from 1 (very poor) to 5 (excellent).
    category:
        Structured category label for quick classification.
    agent_id:
        The agent that produced the response being rated.
    session_id:
        Optional session identifier for grouping feedback.
    interaction_id:
        Optional identifier for the specific interaction being rated.
    free_text:
        Optional free-form user comment.
    feedback_id:
        Unique identifier for this feedback entry.
    submitted_at:
        UTC datetime when feedback was submitted.
    metadata:
        Optional additional key-value metadata.
    """

    rating: int
    category: FeedbackCategory
    agent_id: str
    session_id: str = ""
    interaction_id: str = ""
    free_text: str = ""
    feedback_id: str = field(default_factory=_new_id)
    submitted_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError(
                f"rating must be between 1 and 5, got {self.rating}"
            )
        if not self.agent_id:
            raise ValueError("FeedbackEntry.agent_id must not be empty.")

    @property
    def is_positive(self) -> bool:
        """Return True if rating >= 4 or category is HELPFUL."""
        return self.rating >= 4 or self.category == FeedbackCategory.HELPFUL

    @property
    def is_negative(self) -> bool:
        """Return True if rating <= 2 or category is HARMFUL/UNHELPFUL."""
        return self.rating <= 2 or self.category in (
            FeedbackCategory.HARMFUL,
            FeedbackCategory.UNHELPFUL,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "feedback_id": self.feedback_id,
            "rating": self.rating,
            "category": self.category.value,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "interaction_id": self.interaction_id,
            "free_text": self.free_text,
            "submitted_at": self.submitted_at.isoformat(),
            "is_positive": self.is_positive,
            "is_negative": self.is_negative,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FeedbackSummary:
    """Aggregated feedback statistics for an agent.

    Parameters
    ----------
    agent_id:
        The agent this summary covers.
    total_feedback:
        Total number of feedback entries processed.
    average_rating:
        Mean rating across all entries (1 – 5).
    satisfaction_score:
        Normalised satisfaction score in [0, 1].
    category_distribution:
        Count of feedback entries per category.
    positive_count:
        Number of positive feedback entries.
    negative_count:
        Number of negative feedback entries.
    neutral_count:
        Number of neutral feedback entries (rating = 3).
    top_free_text_keywords:
        Most frequent words from free-text comments.
    computed_at:
        UTC datetime when this summary was computed.
    """

    agent_id: str
    total_feedback: int
    average_rating: float
    satisfaction_score: float
    category_distribution: dict[str, int]
    positive_count: int
    negative_count: int
    neutral_count: int
    top_free_text_keywords: list[str]
    computed_at: datetime

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "agent_id": self.agent_id,
            "total_feedback": self.total_feedback,
            "average_rating": round(self.average_rating, 4),
            "satisfaction_score": round(self.satisfaction_score, 4),
            "category_distribution": dict(self.category_distribution),
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "top_free_text_keywords": list(self.top_free_text_keywords),
            "computed_at": self.computed_at.isoformat(),
        }


class FeedbackCollector:
    """Collects and stores structured user feedback entries.

    Parameters
    ----------
    max_free_text_length:
        Maximum character length for free-text comments. Longer text is
        truncated silently.
    """

    def __init__(self, max_free_text_length: int = 1000) -> None:
        self._max_free_text_length = max_free_text_length
        self._entries: list[FeedbackEntry] = []

    def submit(
        self,
        rating: int,
        category: FeedbackCategory,
        agent_id: str,
        session_id: str = "",
        interaction_id: str = "",
        free_text: str = "",
        metadata: Optional[dict[str, str]] = None,
    ) -> FeedbackEntry:
        """Submit a new feedback entry.

        Parameters
        ----------
        rating:
            Satisfaction rating 1 – 5.
        category:
            Structured category label.
        agent_id:
            The agent being rated.
        session_id:
            Optional session identifier.
        interaction_id:
            Optional interaction identifier.
        free_text:
            Optional free-form comment (truncated if too long).
        metadata:
            Optional additional key-value pairs.

        Returns
        -------
        FeedbackEntry
            The stored feedback entry.

        Raises
        ------
        ValueError
            If rating is out of range or agent_id is empty.
        """
        truncated_text = free_text[: self._max_free_text_length]
        entry = FeedbackEntry(
            rating=rating,
            category=category,
            agent_id=agent_id,
            session_id=session_id,
            interaction_id=interaction_id,
            free_text=truncated_text,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    def get_entries(
        self,
        agent_id: Optional[str] = None,
        category: Optional[FeedbackCategory] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
    ) -> list[FeedbackEntry]:
        """Retrieve feedback entries with optional filtering.

        Parameters
        ----------
        agent_id:
            Filter by agent. None returns entries for all agents.
        category:
            Filter by category.
        min_rating:
            Filter to entries with rating >= min_rating.
        max_rating:
            Filter to entries with rating <= max_rating.

        Returns
        -------
        list[FeedbackEntry]
            Matching entries in submission order.
        """
        results = list(self._entries)
        if agent_id is not None:
            results = [e for e in results if e.agent_id == agent_id]
        if category is not None:
            results = [e for e in results if e.category == category]
        if min_rating is not None:
            results = [e for e in results if e.rating >= min_rating]
        if max_rating is not None:
            results = [e for e in results if e.rating <= max_rating]
        return results

    def total_count(self, agent_id: Optional[str] = None) -> int:
        """Return the number of feedback entries.

        Parameters
        ----------
        agent_id:
            If provided, count only entries for this agent.
        """
        return len(self.get_entries(agent_id=agent_id))

    def clear(self, agent_id: Optional[str] = None) -> int:
        """Remove feedback entries.

        Parameters
        ----------
        agent_id:
            If provided, clear only entries for this agent.

        Returns
        -------
        int
            Number of entries removed.
        """
        if agent_id is None:
            count = len(self._entries)
            self._entries.clear()
            return count
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.agent_id != agent_id]
        return before - len(self._entries)


# ---------------------------------------------------------------------------
# Stop words for keyword extraction
# ---------------------------------------------------------------------------

_STOP_WORDS: frozenset[str] = frozenset(
    """a an the is are was were be been being have has had do does did
    will would could should may might shall must can this that it its
    for in of on or so and but i me my we you your he she they what
    with as if then very just to from at by all not no yes too very
    more most some such about up out also any""".split()
)


def _extract_keywords(texts: list[str], top_n: int = 10) -> list[str]:
    """Extract the most frequent non-stop-word tokens from texts."""
    import re
    counter: Counter[str] = Counter()
    for text in texts:
        tokens = re.findall(r"[a-z][a-z0-9]*", text.lower())
        meaningful = [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]
        counter.update(set(meaningful))  # Count each word once per text
    return [word for word, _ in counter.most_common(top_n)]


class FeedbackAggregator:
    """Computes satisfaction scores and identifies patterns from feedback.

    Parameters
    ----------
    collector:
        The FeedbackCollector to read entries from.
    """

    def __init__(self, collector: FeedbackCollector) -> None:
        self._collector = collector

    def summarise(self, agent_id: str) -> FeedbackSummary:
        """Compute an aggregated feedback summary for an agent.

        Parameters
        ----------
        agent_id:
            The agent to summarise feedback for.

        Returns
        -------
        FeedbackSummary
            Aggregated statistics.
        """
        entries = self._collector.get_entries(agent_id=agent_id)
        now = _utcnow()

        if not entries:
            return FeedbackSummary(
                agent_id=agent_id,
                total_feedback=0,
                average_rating=0.0,
                satisfaction_score=0.0,
                category_distribution={},
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                top_free_text_keywords=[],
                computed_at=now,
            )

        total = len(entries)
        avg_rating = sum(e.rating for e in entries) / total

        # Satisfaction score: normalise rating from [1,5] to [0,1]
        satisfaction = (avg_rating - 1) / 4.0

        category_distribution = dict(
            Counter(e.category.value for e in entries)
        )

        positive_count = sum(1 for e in entries if e.is_positive)
        negative_count = sum(1 for e in entries if e.is_negative)
        neutral_count = total - positive_count - negative_count

        free_texts = [e.free_text for e in entries if e.free_text]
        keywords = _extract_keywords(free_texts)

        return FeedbackSummary(
            agent_id=agent_id,
            total_feedback=total,
            average_rating=round(avg_rating, 4),
            satisfaction_score=round(satisfaction, 4),
            category_distribution=category_distribution,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            top_free_text_keywords=keywords,
            computed_at=now,
        )

    def satisfaction_trend(
        self,
        agent_id: str,
        bucket_count: int = 5,
    ) -> list[dict[str, object]]:
        """Compute satisfaction score over time buckets.

        Divides feedback chronologically into ``bucket_count`` equal buckets
        and computes average rating per bucket.

        Parameters
        ----------
        agent_id:
            The agent to analyse.
        bucket_count:
            Number of time buckets to divide feedback into.

        Returns
        -------
        list[dict[str, object]]
            One dict per bucket with ``bucket``, ``count``, ``avg_rating``.
        """
        entries = sorted(
            self._collector.get_entries(agent_id=agent_id),
            key=lambda e: e.submitted_at,
        )
        if not entries:
            return []

        bucket_size = max(1, len(entries) // bucket_count)
        trend: list[dict[str, object]] = []

        for bucket_index in range(bucket_count):
            start = bucket_index * bucket_size
            end = start + bucket_size if bucket_index < bucket_count - 1 else len(entries)
            bucket_entries = entries[start:end]
            if not bucket_entries:
                continue
            avg = sum(e.rating for e in bucket_entries) / len(bucket_entries)
            trend.append({
                "bucket": bucket_index + 1,
                "count": len(bucket_entries),
                "avg_rating": round(avg, 4),
            })

        return trend

    def harmful_feedback_count(self, agent_id: str) -> int:
        """Return count of feedback flagged as harmful.

        Parameters
        ----------
        agent_id:
            The agent to check.

        Returns
        -------
        int
            Number of HARMFUL category entries.
        """
        return len(
            self._collector.get_entries(
                agent_id=agent_id,
                category=FeedbackCategory.HARMFUL,
            )
        )

    def agents_by_satisfaction(self) -> list[tuple[str, float]]:
        """Return all agents with feedback ranked by satisfaction score (descending).

        Returns
        -------
        list[tuple[str, float]]
            Sorted (agent_id, satisfaction_score) pairs.
        """
        all_entries = self._collector.get_entries()
        agent_ids = {e.agent_id for e in all_entries}
        scores: list[tuple[str, float]] = []
        for agent_id in agent_ids:
            summary = self.summarise(agent_id)
            scores.append((agent_id, summary.satisfaction_score))
        return sorted(scores, key=lambda x: x[1], reverse=True)


__all__ = [
    "FeedbackCollector",
    "FeedbackAggregator",
    "FeedbackEntry",
    "FeedbackCategory",
    "FeedbackSummary",
]
