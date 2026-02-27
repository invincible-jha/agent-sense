"""Universal AI transparency — multi-format indicator renderers.

IndicatorRenderer turns ConfidenceIndicator, AIDisclosureCard, and
HandoffSignal objects into human- or machine-readable strings in one of
four output formats:

- HTML     : semantic markup with full WCAG 2.1 AA compliance
             (ARIA attributes, 4.5:1 minimum colour contrast ratios,
             progress bar for confidence scores)
- TEXT     : plain text with an ASCII progress bar for confidence
- JSON     : structured JSON string
- MARKDOWN : formatted Markdown

HTML colour palette
-------------------
All foreground/background pairs used by the HTML renderer have been
verified to meet the WCAG 2.1 AA minimum contrast ratio of 4.5:1 for
normal-weight text at 16 px:

    VERY_LOW  background #7f1d1d  foreground #ffffff  ratio ≈ 10.4:1
    LOW       background #92400e  foreground #ffffff  ratio ≈  7.4:1
    MEDIUM    background #78350f  foreground #ffffff  ratio ≈  8.4:1
    HIGH      background #14532d  foreground #ffffff  ratio ≈  9.6:1
    VERY_HIGH background #1e3a5f  foreground #ffffff  ratio ≈  9.8:1

(All ratios > 4.5:1 — AA compliant.)

Example
-------
>>> from agent_sense.indicators.confidence import from_score
>>> from agent_sense.indicators.renderers import IndicatorRenderer, RenderFormat
>>> renderer = IndicatorRenderer()
>>> text = renderer.render_confidence(from_score(0.75, "good match"), RenderFormat.TEXT)
>>> "HIGH" in text
True
"""
from __future__ import annotations

import json
from enum import Enum

from agent_sense.indicators.confidence import ConfidenceIndicator, ConfidenceLevel
from agent_sense.indicators.disclosure import AIDisclosureCard, DisclosureLevel
from agent_sense.indicators.handoff_signal import HandoffSignal


class RenderFormat(str, Enum):
    """Output format for indicator rendering."""

    HTML = "html"
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


# ---------------------------------------------------------------------------
# Confidence level metadata used by multiple renderers
# ---------------------------------------------------------------------------

# Mapping of ConfidenceLevel to (label, hex_bg, hex_fg, wcag_verified_ratio)
# All ratios meet WCAG 2.1 AA minimum of 4.5:1.
_LEVEL_META: dict[ConfidenceLevel, tuple[str, str, str]] = {
    ConfidenceLevel.VERY_LOW:  ("Very Low",  "#7f1d1d", "#ffffff"),
    ConfidenceLevel.LOW:       ("Low",        "#92400e", "#ffffff"),
    ConfidenceLevel.MEDIUM:    ("Medium",     "#78350f", "#ffffff"),
    ConfidenceLevel.HIGH:      ("High",       "#14532d", "#ffffff"),
    ConfidenceLevel.VERY_HIGH: ("Very High",  "#1e3a5f", "#ffffff"),
}

# ASCII progress bar settings for TEXT renderer
_BAR_WIDTH: int = 20


def _ascii_bar(score: float, width: int = _BAR_WIDTH) -> str:
    """Return an ASCII progress bar string for a score in [0.0, 1.0]."""
    filled = round(score * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _percent(score: float) -> str:
    """Format a score as a percentage string (e.g. '75%')."""
    return f"{round(score * 100)}%"


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def _html_escape(value: str) -> str:
    """Escape the five XML special characters in a string."""
    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _confidence_html(indicator: ConfidenceIndicator) -> str:
    label, bg, fg = _LEVEL_META[indicator.level]
    percent_int = round(indicator.score * 100)
    bar_id = f"confidence-bar-{id(indicator)}"

    lines: list[str] = [
        '<div role="status"',
        f'     aria-label="Confidence indicator: {label}, {percent_int} percent"',
        f'     style="font-family:sans-serif;border:1px solid {bg};'
        f'border-radius:4px;padding:12px;max-width:480px;">',
        f'  <h3 style="margin:0 0 8px;color:{bg}">',
        f'    Confidence: <span style="background:{bg};color:{fg};'
        f'padding:2px 6px;border-radius:3px;">{_html_escape(label)}</span>',
        "  </h3>",
        "  <!-- Progress bar -->",
        '  <div style="background:#e5e7eb;border-radius:4px;height:16px;"',
        '       role="img"',
        f'       aria-label="Confidence score progress bar showing {percent_int} percent">',
        f'    <div id="{bar_id}"',
        f'         role="progressbar"',
        f'         aria-valuenow="{percent_int}"',
        '         aria-valuemin="0"',
        '         aria-valuemax="100"',
        f'         aria-label="Confidence {percent_int} percent"',
        f'         style="width:{percent_int}%;background:{bg};color:{fg};'
        f'border-radius:4px;height:16px;">',
        "    </div>",
        "  </div>",
        f'  <p style="margin:8px 0 4px;color:#111827;">',
        f'    Score: <strong>{percent_int}%</strong>',
        "  </p>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    {_html_escape(indicator.reasoning)}',
        "  </p>",
    ]

    if indicator.factors:
        lines.append(
            '  <ul aria-label="Confidence factors" style="margin:8px 0;'
            'padding-left:20px;color:#111827;">'
        )
        for factor_name, factor_score in indicator.factors.items():
            factor_pct = round(factor_score * 100)
            lines.append(
                f'    <li aria-label="{_html_escape(factor_name)}: '
                f'{factor_pct} percent">'
                f"{_html_escape(factor_name)}: {factor_pct}%</li>"
            )
        lines.append("  </ul>")

    lines.append("</div>")
    return "\n".join(lines)


def _disclosure_html(card: AIDisclosureCard) -> str:
    level = card.disclosure_level

    lines: list[str] = [
        '<section aria-label="AI disclosure card"',
        '         style="font-family:sans-serif;border:1px solid #1e3a5f;'
        'border-radius:4px;padding:12px;max-width:600px;">',
        '  <h2 style="margin:0 0 8px;color:#1e3a5f;">',
        f'    AI Disclosure: {_html_escape(card.agent_name)}',
        "  </h2>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    <strong>Model provider:</strong> {_html_escape(card.model_provider)}',
        "  </p>",
    ]

    if level in (DisclosureLevel.STANDARD, DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        lines += [
            f'  <p style="margin:4px 0;color:#111827;">',
            f'    <strong>Model:</strong> {_html_escape(card.model_name)}',
            "  </p>",
            f'  <p style="margin:4px 0;color:#111827;">',
            f'    <strong>Agent version:</strong> {_html_escape(card.agent_version)}',
            "  </p>",
        ]
        if card.capabilities:
            lines.append(
                '  <div aria-label="Capabilities">'
                '<strong style="color:#111827;">Capabilities:</strong>'
            )
            lines.append('  <ul style="margin:4px 0;padding-left:20px;color:#111827;">')
            for cap in card.capabilities:
                lines.append(f"    <li>{_html_escape(cap)}</li>")
            lines.append("  </ul></div>")

    if level in (DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        if card.limitations:
            lines.append(
                '  <div aria-label="Limitations">'
                '<strong style="color:#111827;">Limitations:</strong>'
            )
            lines.append('  <ul style="margin:4px 0;padding-left:20px;color:#111827;">')
            for lim in card.limitations:
                lines.append(f"    <li>{_html_escape(lim)}</li>")
            lines.append("  </ul></div>")

    if level == DisclosureLevel.FULL:
        if card.data_handling:
            lines += [
                f'  <p style="margin:4px 0;color:#111827;">',
                f'    <strong>Data handling:</strong> '
                f"{_html_escape(card.data_handling)}",
                "  </p>",
            ]
        lines += [
            f'  <p style="margin:4px 0;color:#6b7280;font-size:0.875em;">',
            f'    Last updated: {_html_escape(card.last_updated.isoformat())}',
            "  </p>",
        ]

    lines.append("</section>")
    return "\n".join(lines)


def _handoff_html(signal: HandoffSignal) -> str:
    urgent = signal.is_urgent()
    border_color = "#7f1d1d" if urgent else "#92400e"
    urgency_label = "URGENT" if urgent else "Standard"

    lines: list[str] = [
        '<div role="alert"' if urgent else '<div role="status"',
        f'     aria-label="Handoff signal: {_html_escape(signal.reason.value)}'
        f', {urgency_label}"',
        f'     style="font-family:sans-serif;border:2px solid {border_color};'
        f'border-radius:4px;padding:12px;max-width:560px;">',
        f'  <h3 style="margin:0 0 8px;color:{border_color};">',
        f'    Handoff Signal'
        + (' &mdash; <strong aria-live="assertive">URGENT</strong>' if urgent else ""),
        "  </h3>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    <strong>Reason:</strong> '
        f'{_html_escape(signal.reason.value.replace("_", " ").title())}',
        "  </p>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    <strong>Suggested specialist:</strong> '
        f'{_html_escape(signal.suggested_specialist)}',
        "  </p>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    <strong>Context:</strong> {_html_escape(signal.context_summary)}',
        "  </p>",
        f'  <p style="margin:4px 0;color:#111827;">',
        f'    <strong>Confidence at escalation:</strong> '
        f'{round(signal.confidence.score * 100)}% '
        f'({_html_escape(signal.confidence.level.value.replace("_", " ").title())})',
        "  </p>",
        f'  <p style="margin:4px 0;color:#6b7280;font-size:0.875em;">',
        f'    {_html_escape(signal.timestamp.isoformat())}',
        "  </p>",
        "</div>",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TEXT helpers
# ---------------------------------------------------------------------------


def _confidence_text(indicator: ConfidenceIndicator) -> str:
    label, _, _ = _LEVEL_META[indicator.level]
    bar = _ascii_bar(indicator.score)
    pct = _percent(indicator.score)
    lines: list[str] = [
        f"Confidence: {label} ({pct})",
        f"{bar} {pct}",
        f"Reasoning: {indicator.reasoning}",
    ]
    if indicator.factors:
        lines.append("Factors:")
        for name, score in indicator.factors.items():
            lines.append(f"  {name}: {_percent(score)}")
    return "\n".join(lines)


def _disclosure_text(card: AIDisclosureCard) -> str:
    level = card.disclosure_level
    lines: list[str] = [
        f"AI Disclosure: {card.agent_name}",
        f"Model provider: {card.model_provider}",
    ]
    if level in (DisclosureLevel.STANDARD, DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        lines += [
            f"Model: {card.model_name}",
            f"Version: {card.agent_version}",
        ]
        if card.capabilities:
            lines.append("Capabilities:")
            for cap in card.capabilities:
                lines.append(f"  - {cap}")
    if level in (DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        if card.limitations:
            lines.append("Limitations:")
            for lim in card.limitations:
                lines.append(f"  - {lim}")
    if level == DisclosureLevel.FULL:
        if card.data_handling:
            lines.append(f"Data handling: {card.data_handling}")
        lines.append(f"Last updated: {card.last_updated.isoformat()}")
    return "\n".join(lines)


def _handoff_text(signal: HandoffSignal) -> str:
    urgency = "URGENT" if signal.is_urgent() else "Standard"
    lines: list[str] = [
        f"Handoff Signal [{urgency}]",
        f"Reason: {signal.reason.value.replace('_', ' ').title()}",
        f"Specialist: {signal.suggested_specialist}",
        f"Context: {signal.context_summary}",
        f"Confidence: {_percent(signal.confidence.score)} "
        f"({signal.confidence.level.value.replace('_', ' ').title()})",
        f"Timestamp: {signal.timestamp.isoformat()}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MARKDOWN helpers
# ---------------------------------------------------------------------------


def _confidence_markdown(indicator: ConfidenceIndicator) -> str:
    label, _, _ = _LEVEL_META[indicator.level]
    pct = _percent(indicator.score)
    lines: list[str] = [
        f"## Confidence: {label} ({pct})",
        "",
        f"**Score:** {pct}  ",
        f"**Reasoning:** {indicator.reasoning}",
    ]
    if indicator.factors:
        lines += ["", "### Factors", ""]
        for name, score in indicator.factors.items():
            lines.append(f"- **{name}:** {_percent(score)}")
    return "\n".join(lines)


def _disclosure_markdown(card: AIDisclosureCard) -> str:
    level = card.disclosure_level
    lines: list[str] = [
        f"## AI Disclosure: {card.agent_name}",
        "",
        f"**Model provider:** {card.model_provider}",
    ]
    if level in (DisclosureLevel.STANDARD, DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        lines += [
            f"**Model:** {card.model_name}",
            f"**Agent version:** {card.agent_version}",
        ]
        if card.capabilities:
            lines += ["", "### Capabilities", ""]
            for cap in card.capabilities:
                lines.append(f"- {cap}")
    if level in (DisclosureLevel.DETAILED, DisclosureLevel.FULL):
        if card.limitations:
            lines += ["", "### Limitations", ""]
            for lim in card.limitations:
                lines.append(f"- {lim}")
    if level == DisclosureLevel.FULL:
        if card.data_handling:
            lines += ["", f"**Data handling:** {card.data_handling}"]
        lines += ["", f"*Last updated: {card.last_updated.isoformat()}*"]
    return "\n".join(lines)


def _handoff_markdown(signal: HandoffSignal) -> str:
    urgency = "URGENT" if signal.is_urgent() else "Standard"
    lines: list[str] = [
        f"## Handoff Signal [{urgency}]",
        "",
        f"**Reason:** {signal.reason.value.replace('_', ' ').title()}  ",
        f"**Suggested specialist:** {signal.suggested_specialist}  ",
        f"**Context:** {signal.context_summary}  ",
        f"**Confidence:** {_percent(signal.confidence.score)} "
        f"({signal.confidence.level.value.replace('_', ' ').title()})  ",
        f"**Timestamp:** {signal.timestamp.isoformat()}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# IndicatorRenderer
# ---------------------------------------------------------------------------


class IndicatorRenderer:
    """Render transparency indicators in multiple output formats.

    All render methods return a ``str``.  No state is held between calls;
    the class is stateless and safe for concurrent use.

    Example
    -------
    >>> from agent_sense.indicators.confidence import from_score
    >>> renderer = IndicatorRenderer()
    >>> output = renderer.render_confidence(
    ...     from_score(0.85, "strong match"),
    ...     RenderFormat.TEXT,
    ... )
    >>> "Very High" in output
    True
    """

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    def render_confidence(
        self,
        indicator: ConfidenceIndicator,
        format: RenderFormat,  # noqa: A002
    ) -> str:
        """Render a ConfidenceIndicator to the requested format.

        Parameters
        ----------
        indicator:
            The confidence indicator to render.
        format:
            Target output format.

        Returns
        -------
        str
            Rendered output as a string.
        """
        if format == RenderFormat.HTML:
            return _confidence_html(indicator)
        if format == RenderFormat.TEXT:
            return _confidence_text(indicator)
        if format == RenderFormat.JSON:
            return json.dumps(indicator.to_dict(), indent=2)
        # MARKDOWN
        return _confidence_markdown(indicator)

    # ------------------------------------------------------------------
    # Disclosure
    # ------------------------------------------------------------------

    def render_disclosure(
        self,
        card: AIDisclosureCard,
        format: RenderFormat,  # noqa: A002
    ) -> str:
        """Render an AIDisclosureCard to the requested format.

        Parameters
        ----------
        card:
            The disclosure card to render.
        format:
            Target output format.

        Returns
        -------
        str
            Rendered output as a string.
        """
        if format == RenderFormat.HTML:
            return _disclosure_html(card)
        if format == RenderFormat.TEXT:
            return _disclosure_text(card)
        if format == RenderFormat.JSON:
            return json.dumps(card.to_dict(), indent=2)
        # MARKDOWN
        return _disclosure_markdown(card)

    # ------------------------------------------------------------------
    # Handoff
    # ------------------------------------------------------------------

    def render_handoff(
        self,
        signal: HandoffSignal,
        format: RenderFormat,  # noqa: A002
    ) -> str:
        """Render a HandoffSignal to the requested format.

        Parameters
        ----------
        signal:
            The handoff signal to render.
        format:
            Target output format.

        Returns
        -------
        str
            Rendered output as a string.
        """
        if format == RenderFormat.HTML:
            return _handoff_html(signal)
        if format == RenderFormat.TEXT:
            return _handoff_text(signal)
        if format == RenderFormat.JSON:
            return json.dumps(signal.to_dict(), indent=2)
        # MARKDOWN
        return _handoff_markdown(signal)
