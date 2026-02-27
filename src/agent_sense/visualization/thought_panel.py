"""ThoughtPanel — collapsible reasoning visualization for agent transparency.

Renders an agent's reasoning process as structured text or JSON for
frontend consumption. Each step captures description, confidence, and duration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PanelFormat(str, Enum):
    """Output format for ThoughtPanel rendering."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ReasoningStep:
    """A single step in an agent's reasoning chain.

    Parameters
    ----------
    description:
        Human-readable description of what was reasoned or decided.
    confidence:
        Confidence score for this step in [0, 1].
    duration_ms:
        Duration of this reasoning step in milliseconds. None if not measured.
    step_type:
        Category label for the step (e.g. ``"observation"``, ``"inference"``,
        ``"decision"``, ``"verification"``).
    metadata:
        Optional key-value pairs for additional step context.
    timestamp:
        UTC datetime when this step was recorded.
    """

    description: str
    confidence: float = 1.0
    duration_ms: Optional[float] = None
    step_type: str = "inference"
    metadata: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("ReasoningStep.description must not be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"ReasoningStep.confidence must be in [0, 1], got {self.confidence}"
            )
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("ReasoningStep.duration_ms must be >= 0.")

    @property
    def confidence_label(self) -> str:
        """Qualitative confidence label."""
        if self.confidence >= 0.9:
            return "very high"
        if self.confidence >= 0.7:
            return "high"
        if self.confidence >= 0.5:
            return "moderate"
        if self.confidence >= 0.3:
            return "low"
        return "very low"

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "description": self.description,
            "confidence": round(self.confidence, 4),
            "confidence_label": self.confidence_label,
            "duration_ms": self.duration_ms,
            "step_type": self.step_type,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class PanelConfig:
    """Configuration for ThoughtPanel rendering.

    Parameters
    ----------
    collapsed_by_default:
        Whether the panel should render in a collapsed state hint.
    show_confidence:
        Whether to include confidence scores in output.
    show_duration:
        Whether to include timing information.
    show_timestamps:
        Whether to include step timestamps.
    max_steps_visible:
        Maximum steps to show in non-collapsed mode. None means all.
    title:
        Panel title displayed in the header.
    """

    collapsed_by_default: bool = False
    show_confidence: bool = True
    show_duration: bool = True
    show_timestamps: bool = False
    max_steps_visible: Optional[int] = None
    title: str = "Reasoning Process"


class ThoughtPanel:
    """Collapsible reasoning visualization panel.

    Collects ReasoningStep objects and renders them in multiple formats
    for consumption by frontend components, logs, or APIs.

    Parameters
    ----------
    config:
        Panel display configuration.
    """

    def __init__(self, config: Optional[PanelConfig] = None) -> None:
        self._config = config or PanelConfig()
        self._steps: list[ReasoningStep] = []
        self._started_at: datetime = _utcnow()
        self._completed_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Step management
    # ------------------------------------------------------------------

    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the panel.

        Parameters
        ----------
        step:
            The reasoning step to append.
        """
        self._steps.append(step)

    def add(
        self,
        description: str,
        confidence: float = 1.0,
        duration_ms: Optional[float] = None,
        step_type: str = "inference",
        metadata: Optional[dict[str, str]] = None,
    ) -> ReasoningStep:
        """Create and add a reasoning step from individual parameters.

        Parameters
        ----------
        description:
            What was reasoned or decided.
        confidence:
            Confidence score in [0, 1].
        duration_ms:
            Optional timing in milliseconds.
        step_type:
            Category label.
        metadata:
            Optional additional context.

        Returns
        -------
        ReasoningStep
            The created step.
        """
        step = ReasoningStep(
            description=description,
            confidence=confidence,
            duration_ms=duration_ms,
            step_type=step_type,
            metadata=metadata or {},
        )
        self._steps.append(step)
        return step

    def complete(self) -> None:
        """Mark the reasoning process as complete."""
        self._completed_at = _utcnow()

    def clear(self) -> None:
        """Remove all steps from the panel."""
        self._steps.clear()
        self._started_at = _utcnow()
        self._completed_at = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def step_count(self) -> int:
        """Number of reasoning steps recorded."""
        return len(self._steps)

    @property
    def average_confidence(self) -> float:
        """Mean confidence across all steps. Returns 0.0 if no steps."""
        if not self._steps:
            return 0.0
        return sum(s.confidence for s in self._steps) / len(self._steps)

    @property
    def total_duration_ms(self) -> Optional[float]:
        """Sum of all step durations. None if no steps have durations."""
        durations = [s.duration_ms for s in self._steps if s.duration_ms is not None]
        return sum(durations) if durations else None

    @property
    def is_complete(self) -> bool:
        """Return True if the panel has been marked as complete."""
        return self._completed_at is not None

    def steps(self) -> list[ReasoningStep]:
        """Return all recorded reasoning steps."""
        return list(self._steps)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(
        self,
        output_format: PanelFormat = PanelFormat.TEXT,
        collapsed: Optional[bool] = None,
    ) -> str:
        """Render the thought panel in the specified format.

        Parameters
        ----------
        output_format:
            Desired output format (text, json, markdown).
        collapsed:
            Override the collapsed state. Uses ``config.collapsed_by_default``
            if not specified.

        Returns
        -------
        str
            Rendered output.
        """
        is_collapsed = collapsed if collapsed is not None else self._config.collapsed_by_default

        if output_format == PanelFormat.JSON:
            return self._render_json(is_collapsed)
        if output_format == PanelFormat.MARKDOWN:
            return self._render_markdown(is_collapsed)
        return self._render_text(is_collapsed)

    def to_dict(self, collapsed: bool = False) -> dict[str, object]:
        """Serialise the panel to a plain dictionary.

        Parameters
        ----------
        collapsed:
            If True, steps are omitted from the output.

        Returns
        -------
        dict[str, object]
            Full panel data.
        """
        visible_steps = self._get_visible_steps()
        return {
            "title": self._config.title,
            "collapsed": collapsed,
            "step_count": self.step_count,
            "average_confidence": round(self.average_confidence, 4),
            "total_duration_ms": self.total_duration_ms,
            "is_complete": self.is_complete,
            "started_at": self._started_at.isoformat(),
            "completed_at": (
                self._completed_at.isoformat() if self._completed_at else None
            ),
            "steps": [] if collapsed else [s.to_dict() for s in visible_steps],
        }

    # ------------------------------------------------------------------
    # Private rendering helpers
    # ------------------------------------------------------------------

    def _get_visible_steps(self) -> list[ReasoningStep]:
        """Return steps respecting the max_steps_visible config."""
        if self._config.max_steps_visible is None:
            return list(self._steps)
        return list(self._steps[: self._config.max_steps_visible])

    def _render_text(self, collapsed: bool) -> str:
        """Render as structured plain text."""
        config = self._config
        status_parts = [f"Steps: {self.step_count}"]
        if config.show_confidence:
            status_parts.append(f"Avg Confidence: {self.average_confidence:.0%}")
        status_parts.append(f"Status: {'Complete' if self.is_complete else 'In Progress'}")
        lines: list[str] = [
            f"=== {config.title} ===",
            " | ".join(status_parts),
        ]

        if collapsed:
            lines.append("[Collapsed — click to expand]")
            return "\n".join(lines)

        visible = self._get_visible_steps()
        for index, step in enumerate(visible, start=1):
            parts = [f"{index}. [{step.step_type.upper()}] {step.description}"]
            if config.show_confidence:
                parts.append(f"   Confidence: {step.confidence:.0%} ({step.confidence_label})")
            if config.show_duration and step.duration_ms is not None:
                parts.append(f"   Duration: {step.duration_ms:.1f}ms")
            if config.show_timestamps:
                parts.append(f"   At: {step.timestamp.isoformat()}")
            lines.extend(parts)

        if self._config.max_steps_visible and len(self._steps) > self._config.max_steps_visible:
            hidden = len(self._steps) - self._config.max_steps_visible
            lines.append(f"... {hidden} more step(s) hidden.")

        return "\n".join(lines)

    def _render_markdown(self, collapsed: bool) -> str:
        """Render as Markdown with details/summary for collapsibility."""
        config = self._config
        summary_line = (
            f"**{config.title}** | {self.step_count} steps | "
            f"avg confidence {self.average_confidence:.0%}"
        )

        if collapsed:
            return f"<details>\n<summary>{summary_line}</summary>\n</details>"

        md_lines: list[str] = [
            f"<details open>",
            f"<summary>{summary_line}</summary>",
            "",
        ]
        visible = self._get_visible_steps()
        for index, step in enumerate(visible, start=1):
            md_lines.append(f"**Step {index}: [{step.step_type}]** {step.description}")
            if config.show_confidence:
                md_lines.append(
                    f"- Confidence: {step.confidence:.0%} ({step.confidence_label})"
                )
            if config.show_duration and step.duration_ms is not None:
                md_lines.append(f"- Duration: {step.duration_ms:.1f}ms")
            md_lines.append("")

        md_lines.append("</details>")
        return "\n".join(md_lines)

    def _render_json(self, collapsed: bool) -> str:
        """Render as JSON."""
        return json.dumps(self.to_dict(collapsed=collapsed), indent=2)


__all__ = ["ThoughtPanel", "ReasoningStep", "PanelConfig", "PanelFormat"]
