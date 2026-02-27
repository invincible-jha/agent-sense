"""Confidence scorer — compute a confidence score from agent metadata.

ConfidenceScorer ingests a metadata dictionary produced by the agent runtime
and returns a numeric confidence score in [0.0, 1.0].

Scoring factors
---------------
model_temperature    : Lower temperature → higher certainty.
                       Mapped to confidence contribution via
                       ``1.0 - clamp(temperature / 2.0)``.
retrieval_score      : Pre-computed retrieval quality score in [0.0, 1.0].
                       Represents how relevant/fresh retrieved context is.
tool_success_count   : Number of tool calls that completed successfully.
tool_total_count     : Total number of tool calls attempted.
                       Success rate = tool_success_count / tool_total_count.
knowledge_freshness  : Value in [0.0, 1.0] indicating how up-to-date the
                       agent's knowledge is for this query (0 = stale,
                       1 = current).

All factors are optional.  Missing factors are excluded from the weighted
average so the scorer degrades gracefully when metadata is sparse.

Weights (configurable)
----------------------
temperature_weight    : 0.25 (default)
retrieval_weight      : 0.35 (default)
tool_success_weight   : 0.25 (default)
freshness_weight      : 0.15 (default)
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Scorer metadata type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScorerMetadata:
    """Structured input to ConfidenceScorer.

    Attributes
    ----------
    model_temperature:
        Sampling temperature used for the LLM call.  Typically in [0.0, 2.0].
        A value of ``None`` means the factor is excluded from scoring.
    retrieval_score:
        Pre-computed retrieval quality score in [0.0, 1.0].
        ``None`` means the factor is excluded.
    tool_success_count:
        Number of tool invocations that completed without error.
    tool_total_count:
        Total number of tool invocations attempted.  When non-zero, the tool
        success rate is included as a scoring factor.
    knowledge_freshness:
        Freshness score in [0.0, 1.0].  ``None`` means the factor is excluded.
    extra:
        Additional key/value metadata for downstream consumers.
    """

    model_temperature: float | None = None
    retrieval_score: float | None = None
    tool_success_count: int = 0
    tool_total_count: int = 0
    knowledge_freshness: float | None = None
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ScorerMetadata":
        """Construct ScorerMetadata from a raw metadata dictionary.

        Unrecognised keys are silently ignored.

        Parameters
        ----------
        data:
            Arbitrary metadata dict from the agent runtime.

        Returns
        -------
        ScorerMetadata
            Populated metadata object.
        """
        temperature = data.get("model_temperature")
        retrieval = data.get("retrieval_score")
        freshness = data.get("knowledge_freshness")
        success_count_raw = data.get("tool_success_count", 0)
        total_count_raw = data.get("tool_total_count", 0)
        extra: dict[str, str] = {}
        for key, value in data.items():
            if key not in {
                "model_temperature",
                "retrieval_score",
                "tool_success_count",
                "tool_total_count",
                "knowledge_freshness",
            }:
                extra[str(key)] = str(value)
        return cls(
            model_temperature=float(temperature) if temperature is not None else None,
            retrieval_score=float(retrieval) if retrieval is not None else None,
            tool_success_count=int(success_count_raw),
            tool_total_count=int(total_count_raw),
            knowledge_freshness=float(freshness) if freshness is not None else None,
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable weights for each confidence factor.

    All weights should be positive.  They are normalised internally so their
    absolute values only matter relative to each other.

    Attributes
    ----------
    temperature:
        Weight for the model temperature factor.
    retrieval:
        Weight for the retrieval quality factor.
    tool_success:
        Weight for the tool success rate factor.
    freshness:
        Weight for the knowledge freshness factor.
    """

    temperature: float = 0.25
    retrieval: float = 0.35
    tool_success: float = 0.25
    freshness: float = 0.15


# ---------------------------------------------------------------------------
# ConfidenceScorer
# ---------------------------------------------------------------------------


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp ``value`` to [low, high]."""
    return max(low, min(high, value))


class ConfidenceScorer:
    """Compute a composite confidence score from agent runtime metadata.

    Parameters
    ----------
    weights:
        Factor weights.  Defaults to :class:`ScoringWeights` with the
        standard factor weights.

    Example
    -------
    >>> scorer = ConfidenceScorer()
    >>> score = scorer.score({"model_temperature": 0.2, "retrieval_score": 0.9})
    >>> 0.0 <= score <= 1.0
    True
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self._weights = weights if weights is not None else ScoringWeights()

    def score(self, metadata: dict[str, object]) -> float:
        """Compute a composite confidence score from raw metadata.

        Parameters
        ----------
        metadata:
            Agent runtime metadata dict.  Recognised keys are those defined
            in :class:`ScorerMetadata`; unrecognised keys are ignored.

        Returns
        -------
        float
            Composite confidence score in [0.0, 1.0].
        """
        parsed = ScorerMetadata.from_dict(metadata)
        return self._compute(parsed)

    def score_from_metadata(self, meta: ScorerMetadata) -> float:
        """Compute a confidence score from a structured :class:`ScorerMetadata`.

        Parameters
        ----------
        meta:
            Pre-parsed metadata object.

        Returns
        -------
        float
            Composite confidence score in [0.0, 1.0].
        """
        return self._compute(meta)

    def _compute(self, meta: ScorerMetadata) -> float:
        """Weighted-average computation across available factors.

        Missing factors are excluded from both numerator and denominator so
        that the result is always a valid score regardless of how sparse the
        metadata is.

        Returns
        -------
        float
            Composite confidence score in [0.0, 1.0].
        """
        weighted_sum = 0.0
        weight_total = 0.0

        # --- temperature factor ------------------------------------------
        if meta.model_temperature is not None:
            # temperature=0.0 → confidence=1.0; temperature=2.0 → confidence=0.0
            temp_contribution = _clamp(1.0 - meta.model_temperature / 2.0)
            weighted_sum += temp_contribution * self._weights.temperature
            weight_total += self._weights.temperature

        # --- retrieval factor --------------------------------------------
        if meta.retrieval_score is not None:
            retrieval_contribution = _clamp(meta.retrieval_score)
            weighted_sum += retrieval_contribution * self._weights.retrieval
            weight_total += self._weights.retrieval

        # --- tool success rate factor ------------------------------------
        if meta.tool_total_count > 0:
            tool_rate = _clamp(meta.tool_success_count / meta.tool_total_count)
            weighted_sum += tool_rate * self._weights.tool_success
            weight_total += self._weights.tool_success

        # --- knowledge freshness factor ----------------------------------
        if meta.knowledge_freshness is not None:
            freshness_contribution = _clamp(meta.knowledge_freshness)
            weighted_sum += freshness_contribution * self._weights.freshness
            weight_total += self._weights.freshness

        # If no factors are available, return a neutral mid-point score.
        if weight_total == 0.0:
            return 0.5

        raw = weighted_sum / weight_total
        return round(_clamp(raw), 4)

    def factor_contributions(
        self, metadata: dict[str, object]
    ) -> dict[str, float]:
        """Return a breakdown of each factor's contribution to the score.

        Parameters
        ----------
        metadata:
            Agent runtime metadata dict.

        Returns
        -------
        dict[str, float]
            Mapping of factor name to its normalised contribution score
            (before weighting).  Missing factors are omitted.
        """
        meta = ScorerMetadata.from_dict(metadata)
        contributions: dict[str, float] = {}

        if meta.model_temperature is not None:
            contributions["temperature"] = _clamp(
                1.0 - meta.model_temperature / 2.0
            )
        if meta.retrieval_score is not None:
            contributions["retrieval"] = _clamp(meta.retrieval_score)
        if meta.tool_total_count > 0:
            contributions["tool_success"] = _clamp(
                meta.tool_success_count / meta.tool_total_count
            )
        if meta.knowledge_freshness is not None:
            contributions["freshness"] = _clamp(meta.knowledge_freshness)

        return contributions
