"""Transparency report — generate session-level transparency summaries.

TransparencyReport produces structured, human-readable reports about what
happened during an AI agent session: how many interactions occurred, what
confidence levels were assigned, whether a handoff took place, and what
disclosures were shown.

These reports support regulatory compliance, internal auditing, and the
principle of human oversight in AI deployments.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionStats:
    """Statistics about a completed or ongoing agent session.

    Pass this to TransparencyReport.generate() to produce a full report.

    Attributes
    ----------
    session_id:
        Unique identifier for the session.
    total_turns:
        Total number of conversation turns (user + agent combined).
    agent_turns:
        Number of agent-generated response turns.
    high_confidence_turns:
        Turns where the agent confidence level was HIGH.
    medium_confidence_turns:
        Turns where the agent confidence level was MEDIUM.
    low_confidence_turns:
        Turns where confidence was LOW or UNKNOWN.
    handoff_occurred:
        Whether the session ended in a human handoff.
    handoff_reason:
        Optional explanation of why a handoff occurred.
    disclosures_shown:
        Names of disclosure statements presented during the session.
    session_start:
        UTC datetime when the session began.
    session_end:
        UTC datetime when the session ended (or None if still active).
    model_id:
        Identifier of the AI model used (should not include the literal model name
        — use a logical alias such as ``"default"`` or an opaque ID).
    extra_metadata:
        Arbitrary additional metadata to include verbatim in the report.
    """

    session_id: str
    total_turns: int = 0
    agent_turns: int = 0
    high_confidence_turns: int = 0
    medium_confidence_turns: int = 0
    low_confidence_turns: int = 0
    handoff_occurred: bool = False
    handoff_reason: str = ""
    disclosures_shown: list[str] = field(default_factory=list)
    session_start: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    session_end: datetime.datetime | None = None
    model_id: str = ""
    extra_metadata: dict[str, str] = field(default_factory=dict)


class TransparencyReport:
    """Generate structured transparency reports from session statistics.

    Example
    -------
    >>> stats = SessionStats(
    ...     session_id="sess-001",
    ...     total_turns=6,
    ...     agent_turns=3,
    ...     high_confidence_turns=2,
    ...     medium_confidence_turns=1,
    ...     low_confidence_turns=0,
    ...     handoff_occurred=False,
    ...     disclosures_shown=["initial_greeting"],
    ... )
    >>> report = TransparencyReport()
    >>> result = report.generate(stats)
    >>> result["session_id"]
    'sess-001'
    """

    def generate(self, session_stats: SessionStats) -> dict[str, object]:
        """Generate a transparency report from session statistics.

        Parameters
        ----------
        session_stats:
            A SessionStats instance describing the session to report on.

        Returns
        -------
        dict[str, object]
            A JSON-serialisable dictionary with the following top-level keys:

            - ``session_id``          : str
            - ``report_generated_at`` : ISO 8601 UTC timestamp string
            - ``session_duration``    : dict with ``start``, ``end``, ``seconds``
            - ``interaction_summary`` : dict with turn counts and rates
            - ``confidence_breakdown``: dict with per-level counts and percentages
            - ``handoff``             : dict with handoff status and reason
            - ``disclosures``         : dict with shown templates and count
            - ``model``               : dict with model_id (opaque)
            - ``metadata``            : dict with extra fields from stats
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        session_end = session_stats.session_end or now

        duration_seconds = (
            session_end - session_stats.session_start
        ).total_seconds()

        # Confidence percentages are computed relative to agent_turns.
        agent_turns = max(session_stats.agent_turns, 1)
        high_pct = round(
            (session_stats.high_confidence_turns / agent_turns) * 100, 1
        )
        medium_pct = round(
            (session_stats.medium_confidence_turns / agent_turns) * 100, 1
        )
        low_pct = round(
            (session_stats.low_confidence_turns / agent_turns) * 100, 1
        )
        # Automation rate = agent turns / total turns.
        automation_rate = (
            round(session_stats.agent_turns / session_stats.total_turns * 100, 1)
            if session_stats.total_turns > 0
            else 0.0
        )

        return {
            "session_id": session_stats.session_id,
            "report_generated_at": now.isoformat(),
            "session_duration": {
                "start": session_stats.session_start.isoformat(),
                "end": session_end.isoformat(),
                "seconds": round(duration_seconds, 3),
            },
            "interaction_summary": {
                "total_turns": session_stats.total_turns,
                "agent_turns": session_stats.agent_turns,
                "automation_rate_pct": automation_rate,
            },
            "confidence_breakdown": {
                "high": session_stats.high_confidence_turns,
                "medium": session_stats.medium_confidence_turns,
                "low": session_stats.low_confidence_turns,
                "high_pct": high_pct,
                "medium_pct": medium_pct,
                "low_pct": low_pct,
            },
            "handoff": {
                "occurred": session_stats.handoff_occurred,
                "reason": session_stats.handoff_reason,
            },
            "disclosures": {
                "templates_shown": list(session_stats.disclosures_shown),
                "total_shown": len(session_stats.disclosures_shown),
            },
            "model": {
                "model_id": session_stats.model_id or "unspecified",
            },
            "metadata": dict(session_stats.extra_metadata),
        }

    def generate_text_summary(self, session_stats: SessionStats) -> str:
        """Produce a plain-text summary of the transparency report.

        Suitable for inclusion in email notifications or plain-text audit logs.

        Parameters
        ----------
        session_stats:
            The session statistics to summarise.

        Returns
        -------
        str
            A multi-line human-readable summary.
        """
        data = self.generate(session_stats)
        duration_s = data["session_duration"]["seconds"]  # type: ignore[index]
        minutes, seconds = divmod(int(duration_s), 60)  # type: ignore[arg-type]

        handoff_line = (
            "Yes"
            if session_stats.handoff_occurred
            else "No"
        )

        lines = [
            f"Transparency Report — Session {session_stats.session_id}",
            f"  Generated : {data['report_generated_at']}",
            f"  Duration  : {minutes}m {seconds}s",
            f"  Turns     : {session_stats.total_turns} total, "
            f"{session_stats.agent_turns} AI",
            f"  Confidence: HIGH {session_stats.high_confidence_turns}, "
            f"MEDIUM {session_stats.medium_confidence_turns}, "
            f"LOW {session_stats.low_confidence_turns}",
            f"  Handoff   : {handoff_line}",
        ]
        if session_stats.handoff_reason:
            lines.append(f"              Reason: {session_stats.handoff_reason}")
        if session_stats.disclosures_shown:
            lines.append(
                f"  Disclosures: {', '.join(session_stats.disclosures_shown)}"
            )
        return "\n".join(lines)
