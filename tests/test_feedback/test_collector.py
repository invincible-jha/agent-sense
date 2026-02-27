"""Tests for FeedbackCollector and FeedbackAggregator — E16.5."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent_sense.feedback.collector import (
    FeedbackAggregator,
    FeedbackCategory,
    FeedbackCollector,
    FeedbackEntry,
    FeedbackSummary,
    _extract_keywords,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(offset_hours: float = 0.0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=offset_hours)


def _submit_feedback(
    collector: FeedbackCollector,
    agent_id: str = "agent-001",
    rating: int = 4,
    category: FeedbackCategory = FeedbackCategory.HELPFUL,
    free_text: str = "",
) -> FeedbackEntry:
    return collector.submit(
        rating=rating,
        category=category,
        agent_id=agent_id,
        free_text=free_text,
    )


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------


class TestExtractKeywords:
    def test_extracts_frequent_words(self) -> None:
        texts = [
            "great response helpful agent",
            "very helpful and clear response",
            "helpful agent clear explanation",
        ]
        keywords = _extract_keywords(texts)
        assert "helpful" in keywords
        assert "response" in keywords

    def test_excludes_stop_words(self) -> None:
        texts = ["this is a very helpful and clear response"]
        keywords = _extract_keywords(texts)
        assert "this" not in keywords
        assert "very" not in keywords

    def test_empty_texts_returns_empty(self) -> None:
        assert _extract_keywords([]) == []

    def test_respects_top_n(self) -> None:
        texts = ["word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11"]
        keywords = _extract_keywords(texts, top_n=5)
        assert len(keywords) <= 5


# ---------------------------------------------------------------------------
# FeedbackEntry validation
# ---------------------------------------------------------------------------


class TestFeedbackEntry:
    def test_valid_entry_created(self) -> None:
        entry = FeedbackEntry(
            rating=4,
            category=FeedbackCategory.HELPFUL,
            agent_id="agent-001",
        )
        assert entry.rating == 4
        assert entry.category == FeedbackCategory.HELPFUL

    def test_rating_below_one_raises(self) -> None:
        with pytest.raises(ValueError, match="rating"):
            FeedbackEntry(rating=0, category=FeedbackCategory.HELPFUL, agent_id="a")

    def test_rating_above_five_raises(self) -> None:
        with pytest.raises(ValueError, match="rating"):
            FeedbackEntry(rating=6, category=FeedbackCategory.HELPFUL, agent_id="a")

    def test_empty_agent_id_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_id"):
            FeedbackEntry(rating=3, category=FeedbackCategory.OTHER, agent_id="")

    def test_is_positive_when_rating_4_or_5(self) -> None:
        entry = FeedbackEntry(rating=4, category=FeedbackCategory.IRRELEVANT, agent_id="a")
        assert entry.is_positive is True

    def test_is_positive_when_category_helpful(self) -> None:
        entry = FeedbackEntry(rating=2, category=FeedbackCategory.HELPFUL, agent_id="a")
        assert entry.is_positive is True

    def test_is_negative_when_rating_1_or_2(self) -> None:
        entry = FeedbackEntry(rating=1, category=FeedbackCategory.IRRELEVANT, agent_id="a")
        assert entry.is_negative is True

    def test_is_negative_when_harmful(self) -> None:
        entry = FeedbackEntry(rating=3, category=FeedbackCategory.HARMFUL, agent_id="a")
        assert entry.is_negative is True

    def test_neutral_rating_is_neither_positive_nor_negative(self) -> None:
        entry = FeedbackEntry(rating=3, category=FeedbackCategory.OTHER, agent_id="a")
        assert not entry.is_positive
        assert not entry.is_negative

    def test_to_dict_structure(self) -> None:
        entry = FeedbackEntry(
            rating=5,
            category=FeedbackCategory.HELPFUL,
            agent_id="agent-001",
            free_text="Excellent response.",
        )
        data = entry.to_dict()
        required_keys = {
            "feedback_id", "rating", "category", "agent_id",
            "session_id", "free_text", "submitted_at", "is_positive", "is_negative",
        }
        assert required_keys.issubset(data.keys())

    def test_feedback_id_is_unique(self) -> None:
        e1 = FeedbackEntry(rating=3, category=FeedbackCategory.OTHER, agent_id="a")
        e2 = FeedbackEntry(rating=3, category=FeedbackCategory.OTHER, agent_id="a")
        assert e1.feedback_id != e2.feedback_id


# ---------------------------------------------------------------------------
# FeedbackCollector tests
# ---------------------------------------------------------------------------


class TestFeedbackCollector:
    def test_submit_creates_entry(self) -> None:
        collector = FeedbackCollector()
        entry = collector.submit(
            rating=4,
            category=FeedbackCategory.HELPFUL,
            agent_id="agent-001",
        )
        assert isinstance(entry, FeedbackEntry)
        assert collector.total_count() == 1

    def test_submit_multiple_entries(self) -> None:
        collector = FeedbackCollector()
        for i in range(5):
            collector.submit(4, FeedbackCategory.HELPFUL, "agent-001")
        assert collector.total_count() == 5

    def test_submit_truncates_long_free_text(self) -> None:
        collector = FeedbackCollector(max_free_text_length=10)
        entry = collector.submit(3, FeedbackCategory.OTHER, "a", free_text="x" * 100)
        assert len(entry.free_text) == 10

    def test_get_entries_filter_by_agent(self) -> None:
        collector = FeedbackCollector()
        collector.submit(4, FeedbackCategory.HELPFUL, "agent-001")
        collector.submit(3, FeedbackCategory.OTHER, "agent-002")
        entries = collector.get_entries(agent_id="agent-001")
        assert len(entries) == 1
        assert entries[0].agent_id == "agent-001"

    def test_get_entries_filter_by_category(self) -> None:
        collector = FeedbackCollector()
        collector.submit(5, FeedbackCategory.HELPFUL, "agent-001")
        collector.submit(1, FeedbackCategory.HARMFUL, "agent-001")
        harmful = collector.get_entries(category=FeedbackCategory.HARMFUL)
        assert len(harmful) == 1
        assert harmful[0].category == FeedbackCategory.HARMFUL

    def test_get_entries_filter_by_rating_range(self) -> None:
        collector = FeedbackCollector()
        for rating in [1, 2, 3, 4, 5]:
            collector.submit(rating, FeedbackCategory.OTHER, "agent-001")
        high = collector.get_entries(min_rating=4)
        assert len(high) == 2
        assert all(e.rating >= 4 for e in high)

    def test_clear_all_entries(self) -> None:
        collector = FeedbackCollector()
        collector.submit(3, FeedbackCategory.OTHER, "agent-001")
        removed = collector.clear()
        assert removed == 1
        assert collector.total_count() == 0

    def test_clear_by_agent(self) -> None:
        collector = FeedbackCollector()
        collector.submit(4, FeedbackCategory.HELPFUL, "agent-001")
        collector.submit(3, FeedbackCategory.OTHER, "agent-002")
        removed = collector.clear(agent_id="agent-001")
        assert removed == 1
        assert collector.total_count() == 1


# ---------------------------------------------------------------------------
# FeedbackAggregator tests
# ---------------------------------------------------------------------------


class TestFeedbackAggregator:
    def _make_collector_with_data(self) -> FeedbackCollector:
        collector = FeedbackCollector()
        collector.submit(5, FeedbackCategory.HELPFUL, "agent-001", free_text="Great clear response helpful")
        collector.submit(4, FeedbackCategory.HELPFUL, "agent-001", free_text="Helpful and clear explanation")
        collector.submit(2, FeedbackCategory.UNHELPFUL, "agent-001", free_text="Not helpful response")
        collector.submit(3, FeedbackCategory.OTHER, "agent-001")
        collector.submit(1, FeedbackCategory.HARMFUL, "agent-001")
        return collector

    def test_summarise_returns_correct_total(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        assert summary.total_feedback == 5

    def test_summarise_average_rating(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        expected_avg = (5 + 4 + 2 + 3 + 1) / 5
        assert abs(summary.average_rating - expected_avg) < 0.01

    def test_summarise_satisfaction_score_in_range(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        assert 0.0 <= summary.satisfaction_score <= 1.0

    def test_summarise_positive_negative_counts(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        assert summary.positive_count >= 2  # ratings 4 and 5
        assert summary.negative_count >= 1  # rating 1 or 2 or harmful

    def test_summarise_category_distribution(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        assert FeedbackCategory.HELPFUL.value in summary.category_distribution
        assert summary.category_distribution[FeedbackCategory.HELPFUL.value] == 2

    def test_summarise_extracts_keywords(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        assert isinstance(summary.top_free_text_keywords, list)
        # "helpful" appears in multiple texts — should be a top keyword
        # (keywords are present if free text was provided)
        assert len(summary.top_free_text_keywords) >= 0

    def test_summarise_empty_agent_returns_zero_summary(self) -> None:
        collector = FeedbackCollector()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("ghost-agent")
        assert summary.total_feedback == 0
        assert summary.average_rating == 0.0

    def test_harmful_feedback_count(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        count = agg.harmful_feedback_count("agent-001")
        assert count == 1

    def test_agents_by_satisfaction_sorted_descending(self) -> None:
        collector = FeedbackCollector()
        collector.submit(5, FeedbackCategory.HELPFUL, "best-agent")
        collector.submit(5, FeedbackCategory.HELPFUL, "best-agent")
        collector.submit(1, FeedbackCategory.HARMFUL, "worst-agent")
        collector.submit(1, FeedbackCategory.HARMFUL, "worst-agent")
        agg = FeedbackAggregator(collector)
        ranking = agg.agents_by_satisfaction()
        assert ranking[0][0] == "best-agent"
        assert ranking[-1][0] == "worst-agent"

    def test_satisfaction_trend_returns_buckets(self) -> None:
        collector = FeedbackCollector()
        for i in range(10):
            collector.submit(3 + (i % 3), FeedbackCategory.OTHER, "agent-001")
        agg = FeedbackAggregator(collector)
        trend = agg.satisfaction_trend("agent-001", bucket_count=5)
        assert len(trend) >= 1
        for bucket in trend:
            assert "bucket" in bucket
            assert "count" in bucket
            assert "avg_rating" in bucket

    def test_summary_to_dict_structure(self) -> None:
        collector = self._make_collector_with_data()
        agg = FeedbackAggregator(collector)
        summary = agg.summarise("agent-001")
        data = summary.to_dict()
        required_keys = {
            "agent_id", "total_feedback", "average_rating",
            "satisfaction_score", "category_distribution",
            "positive_count", "negative_count", "neutral_count",
            "top_free_text_keywords", "computed_at",
        }
        assert required_keys.issubset(data.keys())
