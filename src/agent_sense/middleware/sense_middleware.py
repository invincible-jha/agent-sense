"""SenseMiddleware — wrap agent interactions with confidence, context, and disclosure.

SenseMiddleware acts as the integration layer for agent-sense: given a user
message and an agent response, it orchestrates the confidence annotation,
context detection, disclosure generation, and suggestion production into a
single enriched InteractionResult.

Usage pattern
-------------
Instantiate once and call ``process()`` for each conversational turn:

    middleware = SenseMiddleware(
        session_id="sess-42",
        agent_name="Aria",
        org_name="Acme Corp",
    )
    result = middleware.process(
        user_text="I cannot log in",
        agent_response="I can help you reset your password.",
        confidence_score=0.88,
    )

The returned InteractionResult bundles together the annotated response,
disclosure statement, suggestions, and updated session stats.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from agent_sense.confidence.annotator import AnnotatedResponse, ConfidenceAnnotator
from agent_sense.context.situation import SituationAssessor, SituationVector
from agent_sense.disclosure.ai_disclosure import AIDisclosure, DisclosureTone
from agent_sense.disclosure.transparency import SessionStats, TransparencyReport
from agent_sense.suggestions.engine import Suggestion, SuggestionCategory, SuggestionEngine
from agent_sense.suggestions.ranker import SuggestionRanker


@dataclass
class InteractionResult:
    """The enriched output of a single processed interaction turn.

    Attributes
    ----------
    annotated_response:
        The agent response annotated with its confidence level.
    situation:
        The detected situational context for this turn.
    disclosure_text:
        Disclosure statement to show alongside the response (may be empty if
        the turn does not require one).
    suggestions:
        Ranked contextual suggestions for the user's next action.
    session_stats:
        Running session statistics updated after this turn.
    turn_number:
        1-based index of this interaction turn in the session.
    """

    annotated_response: AnnotatedResponse
    situation: SituationVector
    disclosure_text: str
    suggestions: list[Suggestion]
    session_stats: SessionStats
    turn_number: int


class SenseMiddleware:
    """Orchestrate confidence annotation, context detection, disclosure, and suggestions.

    Parameters
    ----------
    session_id:
        Optional unique session identifier carried into session stats.
    agent_name:
        AI agent display name used in disclosure statements.
    org_name:
        Deploying organisation name used in disclosure statements.
    tone:
        Disclosure tone (FORMAL, FRIENDLY, or CONCISE). Defaults to FRIENDLY.
    user_agent:
        HTTP User-Agent string for device/context detection.
    headers:
        Additional HTTP headers for context detection (ECT, Save-Data, etc.).
    domain:
        Domain label passed to ConfidenceAnnotator (e.g. ``"medical"``).
    max_suggestions:
        Maximum number of suggestions to include per turn. Defaults to 3.

    Example
    -------
    >>> mw = SenseMiddleware(session_id="s1", agent_name="Aria", org_name="Acme")
    >>> result = mw.process(
    ...     user_text="How do I cancel my subscription?",
    ...     agent_response="You can cancel from Account > Billing.",
    ...     confidence_score=0.90,
    ... )
    >>> result.annotated_response.confidence_level.value
    'high'
    """

    def __init__(
        self,
        session_id: str = "",
        agent_name: str = "AI Assistant",
        org_name: str = "",
        tone: DisclosureTone = DisclosureTone.FRIENDLY,
        user_agent: str = "",
        headers: dict[str, str] | None = None,
        domain: str = "",
        max_suggestions: int = 3,
    ) -> None:
        self._session_id = session_id
        self._domain = domain
        self._annotator = ConfidenceAnnotator()
        self._assessor = SituationAssessor()
        self._disclosure = AIDisclosure(
            agent_name=agent_name, org_name=org_name, tone=tone
        )
        self._suggestion_engine = SuggestionEngine(max_suggestions=max_suggestions)
        self._ranker = SuggestionRanker()

        # Mutable session state.
        self._turn_number: int = 0
        self._user_history: list[str] = []
        self._recently_shown_suggestions: list[str] = []
        self._session_start: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        )
        self._high_turns: int = 0
        self._medium_turns: int = 0
        self._low_turns: int = 0
        self._disclosures_shown: list[str] = []
        self._handoff_occurred: bool = False
        self._handoff_reason: str = ""

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process(
        self,
        user_text: str,
        agent_response: str,
        confidence_score: float,
        show_disclosure: bool | None = None,
    ) -> InteractionResult:
        """Process a single conversational turn through the middleware stack.

        Parameters
        ----------
        user_text:
            The user's input message for this turn.
        agent_response:
            The agent's response text.
        confidence_score:
            Raw confidence score in [0.0, 1.0] for the agent response.
        show_disclosure:
            Override whether a disclosure statement is generated.
            Defaults to True for the first turn and for low-confidence turns.

        Returns
        -------
        InteractionResult
            All enriched outputs bundled together.

        Raises
        ------
        ValueError
            If ``confidence_score`` is outside [0.0, 1.0].
        """
        self._turn_number += 1
        self._user_history.append(user_text)

        # 1. Confidence annotation.
        annotated = self._annotator.annotate(
            content=agent_response,
            score=confidence_score,
            domain=self._domain,
        )

        # 2. Track confidence tier counts.
        from agent_sense.confidence.annotator import ConfidenceLevel

        if annotated.confidence_level == ConfidenceLevel.HIGH:
            self._high_turns += 1
        elif annotated.confidence_level == ConfidenceLevel.MEDIUM:
            self._medium_turns += 1
        else:
            self._low_turns += 1

        # 3. Context / situation detection (stateless per-turn).
        situation = self._assessor.assess(user_text=user_text)

        # 4. Disclosure — show on first turn or when confidence is low.
        should_disclose = show_disclosure
        if should_disclose is None:
            should_disclose = self._turn_number == 1 or annotated.needs_disclaimer()

        disclosure_text = ""
        if should_disclose:
            template = (
                "initial_greeting"
                if self._turn_number == 1
                else "response_caveat"
            )
            stmt = self._disclosure.generate(template)
            disclosure_text = stmt.text
            if template not in self._disclosures_shown:
                self._disclosures_shown.append(template)

        # 5. Suggestions — enrich with ranker.
        raw_suggestions = (
            self._suggestion_engine.suggest_for_low_confidence()
            if annotated.needs_disclaimer()
            else self._suggestion_engine.suggest(
                user_text=user_text,
                history=self._user_history[:-1],  # exclude current turn
            )
        )
        ranked = self._ranker.top_n(
            raw_suggestions,
            n=len(raw_suggestions),
            user_text=user_text,
            history=self._user_history[:-1],
            recent_shown=self._recently_shown_suggestions,
        )
        # Track recently shown.
        for s in ranked:
            if s.text not in self._recently_shown_suggestions:
                self._recently_shown_suggestions.append(s.text)
        # Keep recent shown list bounded to last 20 entries.
        self._recently_shown_suggestions = self._recently_shown_suggestions[-20:]

        # 6. Build session stats snapshot.
        stats = SessionStats(
            session_id=self._session_id,
            total_turns=self._turn_number * 2,  # user + agent
            agent_turns=self._turn_number,
            high_confidence_turns=self._high_turns,
            medium_confidence_turns=self._medium_turns,
            low_confidence_turns=self._low_turns,
            handoff_occurred=self._handoff_occurred,
            handoff_reason=self._handoff_reason,
            disclosures_shown=list(self._disclosures_shown),
            session_start=self._session_start,
            session_end=None,
        )

        return InteractionResult(
            annotated_response=annotated,
            situation=situation,
            disclosure_text=disclosure_text,
            suggestions=ranked,
            session_stats=stats,
            turn_number=self._turn_number,
        )

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def record_handoff(self, reason: str = "") -> None:
        """Mark the session as having ended in a human handoff.

        Parameters
        ----------
        reason:
            Optional text describing why the handoff occurred.
        """
        self._handoff_occurred = True
        self._handoff_reason = reason

    def finalize_report(self) -> dict[str, object]:
        """Generate a final transparency report for the completed session.

        Returns
        -------
        dict[str, object]
            JSON-serialisable transparency report dict.
        """
        stats = SessionStats(
            session_id=self._session_id,
            total_turns=self._turn_number * 2,
            agent_turns=self._turn_number,
            high_confidence_turns=self._high_turns,
            medium_confidence_turns=self._medium_turns,
            low_confidence_turns=self._low_turns,
            handoff_occurred=self._handoff_occurred,
            handoff_reason=self._handoff_reason,
            disclosures_shown=list(self._disclosures_shown),
            session_start=self._session_start,
            session_end=datetime.datetime.now(datetime.timezone.utc),
        )
        return TransparencyReport().generate(stats)

    @property
    def turn_number(self) -> int:
        """Current 1-based turn counter for this session."""
        return self._turn_number
