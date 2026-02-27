"""Tests for agent_sense.escalation.sla_tracker — SLATracker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent_sense.escalation.sla_tracker import (
    SLAConfig,
    SLAStatus,
    SLATracker,
    TimeToHumanRecord,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ago(seconds: float) -> datetime:
    """Return a UTC datetime that is ``seconds`` in the past."""
    return _utcnow() - timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# SLAConfig
# ---------------------------------------------------------------------------


class TestSLAConfig:
    def test_defaults(self) -> None:
        cfg = SLAConfig()
        assert cfg.target_seconds == pytest.approx(300.0)
        assert cfg.warning_threshold_pct == pytest.approx(0.80)
        assert cfg.name == "standard"

    def test_warning_seconds(self) -> None:
        cfg = SLAConfig(target_seconds=100.0, warning_threshold_pct=0.50)
        assert cfg.warning_seconds == pytest.approx(50.0)

    def test_frozen(self) -> None:
        cfg = SLAConfig()
        with pytest.raises((TypeError, AttributeError)):
            cfg.target_seconds = 600.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SLAStatus constants
# ---------------------------------------------------------------------------


class TestSLAStatus:
    def test_constants(self) -> None:
        assert SLAStatus.WITHIN == "within_sla"
        assert SLAStatus.WARNING == "warning"
        assert SLAStatus.BREACHED == "breached"


# ---------------------------------------------------------------------------
# SLATracker — basic
# ---------------------------------------------------------------------------


class TestSLATrackerBasic:
    def test_initial_state(self) -> None:
        tracker = SLATracker()
        assert tracker.records == []
        assert tracker.breach_count == 0
        assert tracker.compliance_rate == pytest.approx(1.0)
        assert tracker.average_tth_seconds == pytest.approx(0.0)

    def test_start_and_pickup(self) -> None:
        tracker = SLATracker()
        tracker.start("sess-001")
        record = tracker.record_pickup("sess-001")
        assert isinstance(record, TimeToHumanRecord)
        assert record.session_id == "sess-001"

    def test_pickup_without_start_raises(self) -> None:
        tracker = SLATracker()
        with pytest.raises(KeyError):
            tracker.record_pickup("unknown-session")

    def test_record_stored_after_pickup(self) -> None:
        tracker = SLATracker()
        tracker.start("s1")
        tracker.record_pickup("s1")
        assert len(tracker.records) == 1


# ---------------------------------------------------------------------------
# SLA classification
# ---------------------------------------------------------------------------


class TestSLAClassification:
    def test_within_sla(self) -> None:
        cfg = SLAConfig(target_seconds=300.0, warning_threshold_pct=0.80)
        tracker = SLATracker(config=cfg)
        start = _ago(60.0)  # 60 seconds ago — well within SLA
        tracker.start("s1", started_at=start)
        record = tracker.record_pickup("s1", pickup_at=_utcnow())
        assert record.sla_status == SLAStatus.WITHIN

    def test_warning_zone(self) -> None:
        cfg = SLAConfig(target_seconds=300.0, warning_threshold_pct=0.80)
        # warning_seconds = 240s; use 250s elapsed → warning
        tracker = SLATracker(config=cfg)
        start = _ago(250.0)
        tracker.start("s1", started_at=start)
        record = tracker.record_pickup("s1", pickup_at=_utcnow())
        assert record.sla_status == SLAStatus.WARNING

    def test_sla_breached(self) -> None:
        cfg = SLAConfig(target_seconds=300.0)
        tracker = SLATracker(config=cfg)
        start = _ago(400.0)  # 400s > 300s → breach
        tracker.start("s1", started_at=start)
        record = tracker.record_pickup("s1", pickup_at=_utcnow())
        assert record.sla_status == SLAStatus.BREACHED
        assert record.is_breach() is True

    def test_within_sla_is_not_breach(self) -> None:
        tracker = SLATracker()
        start = _ago(10.0)
        tracker.start("s1", started_at=start)
        record = tracker.record_pickup("s1", pickup_at=_utcnow())
        assert record.is_breach() is False


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestSLAMetrics:
    def test_breach_count(self) -> None:
        cfg = SLAConfig(target_seconds=100.0)
        tracker = SLATracker(config=cfg)
        # Session 1: within SLA
        tracker.start("s1", started_at=_ago(50.0))
        tracker.record_pickup("s1")
        # Session 2: breached
        tracker.start("s2", started_at=_ago(200.0))
        tracker.record_pickup("s2")
        assert tracker.breach_count == 1

    def test_compliance_rate(self) -> None:
        cfg = SLAConfig(target_seconds=100.0)
        tracker = SLATracker(config=cfg)
        # 3 within, 1 breach → 75% compliance
        for i in range(3):
            tracker.start(f"s{i}", started_at=_ago(50.0))
            tracker.record_pickup(f"s{i}")
        tracker.start("s_breach", started_at=_ago(200.0))
        tracker.record_pickup("s_breach")
        assert tracker.compliance_rate == pytest.approx(0.75, abs=0.001)

    def test_average_tth(self) -> None:
        cfg = SLAConfig(target_seconds=1000.0)
        tracker = SLATracker(config=cfg)
        start_a = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        pickup_a = datetime(2026, 1, 1, 0, 1, 0, tzinfo=timezone.utc)  # 60s
        start_b = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        pickup_b = datetime(2026, 1, 1, 0, 2, 0, tzinfo=timezone.utc)  # 120s
        tracker.start("a", started_at=start_a)
        tracker.record_pickup("a", pickup_at=pickup_a)
        tracker.start("b", started_at=start_b)
        tracker.record_pickup("b", pickup_at=pickup_b)
        assert tracker.average_tth_seconds == pytest.approx(90.0, abs=0.1)


# ---------------------------------------------------------------------------
# TimeToHumanRecord
# ---------------------------------------------------------------------------


class TestTimeToHumanRecord:
    def test_to_dict(self) -> None:
        tracker = SLATracker()
        tracker.start("s1")
        record = tracker.record_pickup("s1", escalation_trigger="low_confidence")
        d = record.to_dict()
        assert d["session_id"] == "s1"
        assert "elapsed_seconds" in d
        assert "sla_status" in d
        assert d["escalation_trigger"] == "low_confidence"

    def test_elapsed_seconds_is_positive(self) -> None:
        tracker = SLATracker()
        start = _ago(30.0)
        tracker.start("s1", started_at=start)
        record = tracker.record_pickup("s1", pickup_at=_utcnow())
        assert record.elapsed_seconds >= 0.0


# ---------------------------------------------------------------------------
# current_elapsed_seconds / current_status
# ---------------------------------------------------------------------------


class TestCurrentElapsed:
    def test_active_session_has_elapsed(self) -> None:
        tracker = SLATracker()
        start = _ago(10.0)
        tracker.start("s1", started_at=start)
        elapsed = tracker.current_elapsed_seconds("s1")
        assert elapsed is not None
        assert elapsed >= 9.0

    def test_unknown_session_returns_none(self) -> None:
        tracker = SLATracker()
        assert tracker.current_elapsed_seconds("unknown") is None

    def test_current_status_within(self) -> None:
        cfg = SLAConfig(target_seconds=300.0)
        tracker = SLATracker(config=cfg)
        start = _ago(10.0)
        tracker.start("s1", started_at=start)
        status = tracker.current_status("s1")
        assert status == SLAStatus.WITHIN

    def test_current_status_breached(self) -> None:
        cfg = SLAConfig(target_seconds=60.0)
        tracker = SLATracker(config=cfg)
        start = _ago(100.0)
        tracker.start("s1", started_at=start)
        status = tracker.current_status("s1")
        assert status == SLAStatus.BREACHED

    def test_current_status_unknown_returns_none(self) -> None:
        tracker = SLATracker()
        assert tracker.current_status("ghost") is None


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_keys(self) -> None:
        tracker = SLATracker()
        s = tracker.summary()
        assert "total_records" in s
        assert "breach_count" in s
        assert "compliance_rate" in s
        assert "average_tth_seconds" in s
        assert "sla_target_seconds" in s
        assert "sla_name" in s

    def test_summary_empty(self) -> None:
        tracker = SLATracker()
        s = tracker.summary()
        assert s["total_records"] == 0
        assert s["breach_count"] == 0
        assert s["compliance_rate"] == pytest.approx(1.0)
