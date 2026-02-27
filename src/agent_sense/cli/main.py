"""CLI entry point for agent-sense.

Invoked as::

    agent-sense [OPTIONS] COMMAND [ARGS]...

or, during development::

    python -m agent_sense.cli.main
"""
from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """Human-agent interaction SDK with accessibility and dialogue management"""


@cli.command(name="version")
def version_command() -> None:
    """Show detailed version information."""
    from agent_sense import __version__

    console.print(f"[bold]agent-sense[/bold] v{__version__}")


@cli.command(name="plugins")
def plugins_command() -> None:
    """List all registered plugins loaded from entry-points."""
    console.print("[bold]Registered plugins:[/bold]")
    console.print("  (No plugins registered. Install a plugin package to see entries here.)")


# ---------------------------------------------------------------------------
# sense annotate
# ---------------------------------------------------------------------------


@cli.command(name="annotate")
@click.argument("response_text")
@click.option(
    "--score",
    "-s",
    type=float,
    required=True,
    help="Confidence score in [0.0, 1.0].",
)
@click.option(
    "--domain",
    "-d",
    default="",
    show_default=True,
    help="Optional domain label (e.g. medical, legal).",
)
@click.option("--json-output", "json_output", is_flag=True, default=False)
def annotate_command(
    response_text: str,
    score: float,
    domain: str,
    json_output: bool,
) -> None:
    """Annotate a response text with a confidence level.

    RESPONSE_TEXT is the agent response string to annotate.

    Example::

        agent-sense annotate "The capital is Paris." --score 0.92
    """
    from agent_sense.confidence.annotator import ConfidenceAnnotator

    try:
        annotator = ConfidenceAnnotator()
        result = annotator.annotate(response_text, score=score, domain=domain)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if json_output:
        payload = {
            "content": result.content,
            "confidence_level": result.confidence_level.value,
            "confidence_score": result.confidence_score,
            "domain": result.domain,
            "needs_disclaimer": result.needs_disclaimer(),
        }
        console.print_json(json.dumps(payload))
    else:
        console.print(f"[bold]Content:[/bold]       {result.content}")
        console.print(f"[bold]Level:[/bold]         {result.confidence_level.value.upper()}")
        console.print(f"[bold]Score:[/bold]         {result.confidence_score}")
        if domain:
            console.print(f"[bold]Domain:[/bold]        {result.domain}")
        console.print(f"[bold]Needs disclaimer:[/bold] {result.needs_disclaimer()}")


# ---------------------------------------------------------------------------
# sense handoff
# ---------------------------------------------------------------------------


@cli.command(name="handoff")
@click.option("--summary", "-s", required=True, help="Summary of the unresolved issue.")
@click.option(
    "--urgency",
    "-u",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    default="medium",
    show_default=True,
    help="Urgency level for the handoff.",
)
@click.option(
    "--fact",
    "-f",
    "facts",
    multiple=True,
    help="Key fact to include (repeat for multiple).",
)
@click.option(
    "--question",
    "-q",
    "questions",
    multiple=True,
    help="Unresolved question (repeat for multiple).",
)
@click.option(
    "--action",
    "-a",
    "actions",
    multiple=True,
    help="Attempted action (repeat for multiple).",
)
@click.option("--session-id", default="", help="Optional session identifier.")
@click.option("--json-output", "json_output", is_flag=True, default=False)
def handoff_command(
    summary: str,
    urgency: str,
    facts: tuple[str, ...],
    questions: tuple[str, ...],
    actions: tuple[str, ...],
    session_id: str,
    json_output: bool,
) -> None:
    """Package a conversation for human agent handoff.

    Example::

        agent-sense handoff --summary "User cannot reset password" \\
            --urgency high \\
            --fact "Email: user@example.com" \\
            --question "Is account locked?"
    """
    from agent_sense.handoff.packager import HandoffPackager, UrgencyLevel

    urgency_map = {
        "low": UrgencyLevel.LOW,
        "medium": UrgencyLevel.MEDIUM,
        "high": UrgencyLevel.HIGH,
        "critical": UrgencyLevel.CRITICAL,
    }
    packager = HandoffPackager(session_id=session_id)
    try:
        package = packager.package(
            summary=summary,
            key_facts=list(facts),
            unresolved_questions=list(questions),
            attempted_actions=list(actions),
            urgency=urgency_map[urgency.lower()],
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if json_output:
        console.print_json(json.dumps(package.to_dict()))
    else:
        console.print(f"[bold]Summary:[/bold]   {package.summary}")
        console.print(f"[bold]Urgency:[/bold]   {package.urgency.value.upper()}")
        console.print(f"[bold]Timestamp:[/bold] {package.timestamp.isoformat()}")
        if package.key_facts:
            console.print("[bold]Key facts:[/bold]")
            for fact in package.key_facts:
                console.print(f"  - {fact}")
        if package.unresolved_questions:
            console.print("[bold]Unresolved questions:[/bold]")
            for question in package.unresolved_questions:
                console.print(f"  - {question}")
        if package.attempted_actions:
            console.print("[bold]Attempted actions:[/bold]")
            for action in package.attempted_actions:
                console.print(f"  - {action}")


# ---------------------------------------------------------------------------
# sense accessibility-check
# ---------------------------------------------------------------------------


@cli.command(name="accessibility-check")
@click.argument("html_input", required=False)
@click.option(
    "--file",
    "-f",
    "input_file",
    type=click.Path(exists=True),
    default=None,
    help="Path to an HTML file to check.",
)
@click.option("--json-output", "json_output", is_flag=True, default=False)
def accessibility_check_command(
    html_input: str | None,
    input_file: str | None,
    json_output: bool,
) -> None:
    """Run WCAG 2.1 AA accessibility checks on HTML markup.

    Provide HTML directly as an argument or via --file.

    Example::

        agent-sense accessibility-check '<img src="logo.png"><a href="#">click here</a>'
    """
    from agent_sense.accessibility.wcag import WCAGChecker

    if input_file:
        with open(input_file, encoding="utf-8") as fh:
            html = fh.read()
    elif html_input:
        html = html_input
    else:
        console.print("[red]Error:[/red] Provide HTML as an argument or via --file.")
        sys.exit(1)

    checker = WCAGChecker()
    violations = checker.check_all(html)

    if json_output:
        payload = [v.to_dict() for v in violations]
        console.print_json(json.dumps(payload))
        return

    if not violations:
        console.print("[green]No WCAG violations detected.[/green]")
        return

    table = Table(title=f"WCAG Violations ({len(violations)} found)")
    table.add_column("Criterion", style="cyan", no_wrap=True)
    table.add_column("Level", style="magenta")
    table.add_column("Description")
    table.add_column("Suggestion", style="green")

    for v in violations:
        table.add_row(v.criterion, v.level.value, v.description, v.suggestion)

    console.print(table)


# ---------------------------------------------------------------------------
# sense suggest
# ---------------------------------------------------------------------------


@cli.command(name="suggest")
@click.argument("user_text")
@click.option(
    "--max",
    "-n",
    "max_suggestions",
    type=int,
    default=4,
    show_default=True,
    help="Maximum number of suggestions to return.",
)
@click.option("--json-output", "json_output", is_flag=True, default=False)
def suggest_command(
    user_text: str,
    max_suggestions: int,
    json_output: bool,
) -> None:
    """Generate contextual suggestions for a user message.

    USER_TEXT is the user's latest message.

    Example::

        agent-sense suggest "I cannot access my billing history"
    """
    from agent_sense.suggestions.engine import SuggestionEngine
    from agent_sense.suggestions.ranker import SuggestionRanker

    engine = SuggestionEngine(max_suggestions=max_suggestions)
    ranker = SuggestionRanker()
    raw = engine.suggest(user_text=user_text)
    ranked = ranker.top_n(raw, n=max_suggestions, user_text=user_text)

    if json_output:
        payload = [
            {
                "text": s.text,
                "category": s.category.value,
                "relevance_score": s.relevance_score,
            }
            for s in ranked
        ]
        console.print_json(json.dumps(payload))
        return

    if not ranked:
        console.print("[yellow]No suggestions generated.[/yellow]")
        return

    table = Table(title="Suggestions")
    table.add_column("#", style="dim")
    table.add_column("Category", style="cyan")
    table.add_column("Suggestion")
    table.add_column("Score", style="magenta")

    for index, suggestion in enumerate(ranked, start=1):
        table.add_row(
            str(index),
            suggestion.category.value,
            suggestion.text,
            f"{suggestion.relevance_score:.2f}",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# sense transparency-report
# ---------------------------------------------------------------------------


@cli.command(name="transparency-report")
@click.option("--session-id", default="demo", show_default=True)
@click.option("--total-turns", "total_turns", type=int, default=10)
@click.option("--agent-turns", "agent_turns", type=int, default=5)
@click.option("--high", "high_turns", type=int, default=3)
@click.option("--medium", "medium_turns", type=int, default=1)
@click.option("--low", "low_turns", type=int, default=1)
@click.option(
    "--handoff",
    "handoff_occurred",
    is_flag=True,
    default=False,
    help="Mark that a human handoff occurred.",
)
@click.option("--handoff-reason", default="", help="Reason for the handoff.")
@click.option("--json-output", "json_output", is_flag=True, default=False)
def transparency_report_command(
    session_id: str,
    total_turns: int,
    agent_turns: int,
    high_turns: int,
    medium_turns: int,
    low_turns: int,
    handoff_occurred: bool,
    handoff_reason: str,
    json_output: bool,
) -> None:
    """Generate a session transparency report.

    Provide session statistics via options. Use --json-output for machine-
    readable output.

    Example::

        agent-sense transparency-report --session-id sess-001 \\
            --total-turns 12 --agent-turns 6 --high 4 --medium 1 --low 1
    """
    from agent_sense.disclosure.transparency import SessionStats, TransparencyReport

    stats = SessionStats(
        session_id=session_id,
        total_turns=total_turns,
        agent_turns=agent_turns,
        high_confidence_turns=high_turns,
        medium_confidence_turns=medium_turns,
        low_confidence_turns=low_turns,
        handoff_occurred=handoff_occurred,
        handoff_reason=handoff_reason,
        disclosures_shown=["initial_greeting", "response_caveat"] if agent_turns > 0 else [],
    )
    reporter = TransparencyReport()

    if json_output:
        report = reporter.generate(stats)
        console.print_json(json.dumps(report))
    else:
        summary = reporter.generate_text_summary(stats)
        console.print(summary)


# ---------------------------------------------------------------------------
# sense indicators
# ---------------------------------------------------------------------------


@cli.group(name="indicators")
def indicators_group() -> None:
    """Render universal AI transparency indicators.

    Sub-commands produce confidence indicators, AI disclosure cards, and
    handoff signals in HTML, TEXT, JSON, or MARKDOWN format.
    """


@indicators_group.command(name="confidence")
@click.option("--score", "-s", type=float, required=True, help="Score in [0.0, 1.0].")
@click.option("--reasoning", "-r", default="", show_default=True, help="Reasoning text.")
@click.option(
    "--format",
    "-f",
    "render_format",
    type=click.Choice(["html", "text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
def indicators_confidence_command(
    score: float,
    reasoning: str,
    render_format: str,
) -> None:
    """Render a confidence indicator.

    Example::

        agent-sense indicators confidence --score 0.85 --reasoning "high match" --format text
    """
    from agent_sense.indicators.confidence import from_score
    from agent_sense.indicators.renderers import IndicatorRenderer, RenderFormat

    format_map = {
        "html": RenderFormat.HTML,
        "text": RenderFormat.TEXT,
        "json": RenderFormat.JSON,
        "markdown": RenderFormat.MARKDOWN,
    }
    try:
        indicator = from_score(score, reasoning=reasoning)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    renderer = IndicatorRenderer()
    output = renderer.render_confidence(indicator, format_map[render_format.lower()])
    console.print(output)


@indicators_group.command(name="disclosure")
@click.option("--agent-name", "agent_name", required=True, help="Agent display name.")
@click.option("--model", "model_provider", required=True, help="Model provider name.")
@click.option("--model-name", "model_name", default="", help="Model identifier.")
@click.option("--version", "agent_version", default="1.0.0", show_default=True)
@click.option(
    "--capability",
    "capabilities",
    multiple=True,
    help="Agent capability (repeat for multiple).",
)
@click.option(
    "--limitation",
    "limitations",
    multiple=True,
    help="Agent limitation (repeat for multiple).",
)
@click.option("--data-handling", "data_handling", default="", help="Data handling description.")
@click.option(
    "--level",
    "disclosure_level",
    type=click.Choice(["minimal", "standard", "detailed", "full"], case_sensitive=False),
    default="standard",
    show_default=True,
    help="Disclosure verbosity level.",
)
@click.option(
    "--format",
    "-f",
    "render_format",
    type=click.Choice(["html", "text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
def indicators_disclosure_command(
    agent_name: str,
    model_provider: str,
    model_name: str,
    agent_version: str,
    capabilities: tuple[str, ...],
    limitations: tuple[str, ...],
    data_handling: str,
    disclosure_level: str,
    render_format: str,
) -> None:
    """Render an AI disclosure card.

    Example::

        agent-sense indicators disclosure --agent-name Aria --model Anthropic --format markdown
    """
    from agent_sense.indicators.disclosure import DisclosureLevel, build_disclosure
    from agent_sense.indicators.renderers import IndicatorRenderer, RenderFormat

    level_map = {
        "minimal": DisclosureLevel.MINIMAL,
        "standard": DisclosureLevel.STANDARD,
        "detailed": DisclosureLevel.DETAILED,
        "full": DisclosureLevel.FULL,
    }
    format_map = {
        "html": RenderFormat.HTML,
        "text": RenderFormat.TEXT,
        "json": RenderFormat.JSON,
        "markdown": RenderFormat.MARKDOWN,
    }

    try:
        card = build_disclosure(
            agent_name=agent_name,
            model_provider=model_provider,
            model_name=model_name,
            agent_version=agent_version,
            capabilities=list(capabilities),
            limitations=list(limitations),
            data_handling=data_handling,
            disclosure_level=level_map[disclosure_level.lower()],
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    renderer = IndicatorRenderer()
    output = renderer.render_disclosure(card, format_map[render_format.lower()])
    console.print(output)


@indicators_group.command(name="handoff")
@click.option(
    "--reason",
    "-r",
    type=click.Choice(
        [
            "confidence_too_low",
            "out_of_scope",
            "user_request",
            "safety_concern",
            "complexity_exceeded",
            "requires_human_judgment",
        ],
        case_sensitive=False,
    ),
    required=True,
    help="Reason for the handoff.",
)
@click.option("--confidence", "-c", "confidence_score", type=float, default=0.5, show_default=True)
@click.option("--specialist", default="human agent", show_default=True)
@click.option("--context", "context_summary", default="", help="Context summary.")
@click.option(
    "--format",
    "-f",
    "render_format",
    type=click.Choice(["html", "text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
def indicators_handoff_command(
    reason: str,
    confidence_score: float,
    specialist: str,
    context_summary: str,
    render_format: str,
) -> None:
    """Render a handoff signal.

    Example::

        agent-sense indicators handoff --reason safety_concern --confidence 0.1 --format json
    """
    import datetime

    from agent_sense.indicators.confidence import from_score
    from agent_sense.indicators.handoff_signal import HandoffReason, HandoffSignal
    from agent_sense.indicators.renderers import IndicatorRenderer, RenderFormat

    reason_map = {r.value: r for r in HandoffReason}
    format_map = {
        "html": RenderFormat.HTML,
        "text": RenderFormat.TEXT,
        "json": RenderFormat.JSON,
        "markdown": RenderFormat.MARKDOWN,
    }

    try:
        confidence = from_score(confidence_score, reasoning="score provided via CLI")
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    signal = HandoffSignal(
        reason=reason_map[reason.lower()],
        confidence=confidence,
        suggested_specialist=specialist,
        context_summary=context_summary,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    renderer = IndicatorRenderer()
    output = renderer.render_handoff(signal, format_map[render_format.lower()])
    console.print(output)


if __name__ == "__main__":
    cli()
