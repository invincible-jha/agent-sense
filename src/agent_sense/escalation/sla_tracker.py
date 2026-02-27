"""SLA tracker — tracks time-to-human metrics and SLA compliance.

SLATracker records the time from the start of an agent interaction to the
moment a human reviewer picks it up.  It evaluates whether the elapsed time
falls within the configured SLA window.

Metrics tracked
---------------
- Time-to-human (TTH): elapsed time from interaction start to human pickup
- SLA compliance: whether TTH <= configured SLA target
- Breach count: number of SLA breaches recorded in this tracker's lifetime
- Average TTH: rolling average across all completed interactions

All times are in seconds for consistency and ease of comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


# ---------------------------------------------------------------------------
# SLA configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SLAConfig:
    """Configuration for SLA targets.

    Attributes
    ----------
    target_seconds:
        Maximum acceptable time-to-human in seconds.  Default: 300 (5 min).
    warning_threshold_pct:
        Fraction of target at which a warning state is triggered.
        E.g. 0.80 means warn when TTH > 80% of target_seconds.
    name:
        Human-readable name for this SLA tier (e.g. ``"standard"``,
        ``"premium"``).
    """

    target_seconds: float = 300.0
    warning_threshold_pct: float = 0.80
    name: str = "standard"

    @property
    def warning_seconds(self) -> float:
        """Elapsed time in seconds at which a warning is triggered."""
        return self.target_seconds * self.warning_threshold_pct


# ---------------------------------------------------------------------------
# SLA status
# ---------------------------------------------------------------------------


class SLAStatus(str):
    """String constant class for SLA status values."""

    WITHIN = "within_sla"
    WARNING = "warning"
    BREACHED = "breached"


# ---------------------------------------------------------------------------
# Time-to-human record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TimeToHumanRecord:
    """Immutable record of a single time-to-human measurement.

    Attributes
    ----------
    record_id:
        Unique identifier for this measurement.
    session_id:
        Identifier of the originating session.
    started_at:
        UTC timestamp when the interaction began.
    human_pickup_at:
        UTC timestamp when a human reviewer picked up the interaction.
    elapsed_seconds:
        Computed elapsed time in seconds.
    sla_target_seconds:
        The SLA target that was in effect for this interaction.
    sla_status:
        One of ``SLAStatus.WITHIN``, ``SLAStatus.WARNING``,
        or ``SLAStatus.BREACHED``.
    escalation_trigger:
        Label describing what triggered the escalation (e.g. ``"low_confidence"``).
    """

    record_id: str
    session_id: str
    started_at: datetime
    human_pickup_at: datetime
    elapsed_seconds: float
    sla_target_seconds: float
    sla_status: str
    escalation_trigger: str = ""

    def is_breach(self) -> bool:
        """Return True if the SLA was breached."""
        return self.sla_status == SLAStatus.BREACHED

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dict.

        Returns
        -------
        dict[str, object]
            All fields as JSON-compatible Python primitives.
        """
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "human_pickup_at": self.human_pickup_at.isoformat(),
            "elapsed_seconds": self.elapsed_seconds,
            "sla_target_seconds": self.sla_target_seconds,
            "sla_status": self.sla_status,
            "escalation_trigger": self.escalation_trigger,
        }


# ---------------------------------------------------------------------------
# SLATracker
# ---------------------------------------------------------------------------


class SLATracker:
    """Track time-to-human metrics and evaluate SLA compliance.

    Parameters
    ----------
    config:
        SLA configuration (target window and warning threshold).

    Example
    -------
    >>> tracker = SLATracker()
    >>> tracker.start("sess-001")
    >>> record = tracker.record_pickup("sess-001")
    >>> record.sla_status in (SLAStatus.WITHIN, SLAStatus.WARNING, SLAStatus.BREACHED)
    True
    """

    def __init__(self, config: SLAConfig | None = None) -> None:
        self._config = config if config is not None else SLAConfig()
        # session_id -> started_at
        self._active: dict[str, datetime] = {}
        self._records: list[TimeToHumanRecord] = []

    @property
    def config(self) -> SLAConfig:
        """The active SLA configuration."""
        return self._config

    @property
    def records(self) -> list[TimeToHumanRecord]:
        """All completed time-to-human records."""
        return list(self._records)

    @property
    def breach_count(self) -> int:
        """Number of SLA breaches recorded."""
        return sum(1 for r in self._records if r.is_breach())

    @property
    def compliance_rate(self) -> float:
        """Fraction of interactions that met the SLA target.

        Returns 1.0 when no records have been collected.
        """
        if not self._records:
            return 1.0
        within = sum(1 for r in self._records if not r.is_breach())
        return round(within / len(self._records), 4)

    @property
    def average_tth_seconds(self) -> float:
        """Rolling average time-to-human across all completed records.

        Returns 0.0 when no records have been collected.
        """
        if not self._records:
            return 0.0
        return round(sum(r.elapsed_seconds for r in self._records) / len(self._records), 2)

    def start(self, session_id: str, *, started_at: datetime | None = None) -> None:
        """Mark the start of an interaction that may require human handoff.

        Parameters
        ----------
        session_id:
            Unique session identifier.
        started_at:
            Optional override for the start time.  Defaults to UTC now.
        """
        self._active[session_id] = started_at if started_at is not None else datetime.now(timezone.utc)

    def record_pickup(
        self,
        session_id: str,
        *,
        pickup_at: datetime | None = None,
        escalation_trigger: str = "",
    ) -> TimeToHumanRecord:
        """Record a human pickup event and produce a TimeToHumanRecord.

        Parameters
        ----------
        session_id:
            The session that was picked up.
        pickup_at:
            Optional override for the pickup time.  Defaults to UTC now.
        escalation_trigger:
            Label for what triggered the escalation.

        Returns
        -------
        TimeToHumanRecord
            Immutable record with elapsed time and SLA status.

        Raises
        ------
        KeyError
            If ``session_id`` was not registered via :meth:`start`.
        """
        if session_id not in self._active:
            raise KeyError(
                f"Session {session_id!r} is not active. Call start() first."
            )
        started_at = self._active.pop(session_id)
        now = pickup_at if pickup_at is not None else datetime.now(timezone.utc)
        elapsed = (now - started_at).total_seconds()
        status = self._classify(elapsed)

        record = TimeToHumanRecord(
            record_id=str(uuid4()),
            session_id=session_id,
            started_at=started_at,
            human_pickup_at=now,
            elapsed_seconds=round(elapsed, 3),
            sla_target_seconds=self._config.target_seconds,
            sla_status=status,
            escalation_trigger=escalation_trigger,
        )
        self._records.append(record)
        return record

    def current_elapsed_seconds(self, session_id: str) -> float | None:
        """Return the elapsed time in seconds for an active session.

        Parameters
        ----------
        session_id:
            The active session to query.

        Returns
        -------
        float | None
            Elapsed seconds, or None if the session is not active.
        """
        if session_id not in self._active:
            return None
        elapsed = (datetime.now(timezone.utc) - self._active[session_id]).total_seconds()
        return round(elapsed, 3)

    def current_status(self, session_id: str) -> str | None:
        """Return the current SLA status for an active session.

        Parameters
        ----------
        session_id:
            The active session to query.

        Returns
        -------
        str | None
            One of the SLAStatus constants, or None if the session is not active.
        """
        elapsed = self.current_elapsed_seconds(session_id)
        if elapsed is None:
            return None
        return self._classify(elapsed)

    def _classify(self, elapsed: float) -> str:
        """Map elapsed seconds to an SLA status string."""
        if elapsed > self._config.target_seconds:
            return SLAStatus.BREACHED
        if elapsed > self._config.warning_seconds:
            return SLAStatus.WARNING
        return SLAStatus.WITHIN

    def summary(self) -> dict[str, object]:
        """Return a summary of SLA performance metrics.

        Returns
        -------
        dict[str, object]
            Keys: total_records, breach_count, compliance_rate,
            average_tth_seconds, sla_target_seconds, sla_name.
        """
        return {
            "total_records": len(self._records),
            "breach_count": self.breach_count,
            "compliance_rate": self.compliance_rate,
            "average_tth_seconds": self.average_tth_seconds,
            "sla_target_seconds": self._config.target_seconds,
            "sla_name": self._config.name,
        }
