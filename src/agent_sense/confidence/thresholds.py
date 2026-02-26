"""Confidence thresholds — configurable per-domain score boundaries.

ConfidenceThresholds lets callers override the default HIGH/MEDIUM/LOW
boundaries for specific domains (e.g. medical contexts may require stricter
HIGH thresholds).
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Default boundaries matching the annotator module's defaults.
_DEFAULT_HIGH: float = 0.85
_DEFAULT_MEDIUM: float = 0.60
_DEFAULT_LOW: float = 0.30


@dataclass
class ConfidenceThresholds:
    """Configurable confidence score boundaries per domain.

    Parameters
    ----------
    default_high:
        Default HIGH threshold (score >= this -> HIGH). Default 0.85.
    default_medium:
        Default MEDIUM threshold. Default 0.60.
    default_low:
        Default LOW threshold. Default 0.30.
    domain_overrides:
        Optional mapping of domain label -> (high, medium, low) tuple.

    Example
    -------
    >>> thresholds = ConfidenceThresholds(default_high=0.90)
    >>> thresholds.bounds_for("general")
    (0.9, 0.6, 0.3)
    """

    default_high: float = _DEFAULT_HIGH
    default_medium: float = _DEFAULT_MEDIUM
    default_low: float = _DEFAULT_LOW
    domain_overrides: dict[str, tuple[float, float, float]] = field(
        default_factory=dict
    )

    def bounds_for(self, domain: str) -> tuple[float, float, float]:
        """Return (high, medium, low) thresholds for the given domain.

        Parameters
        ----------
        domain:
            Domain label (e.g. ``"medical"``). Falls back to defaults if no
            override is registered.

        Returns
        -------
        tuple[float, float, float]
            (high, medium, low) boundary floats.
        """
        if domain in self.domain_overrides:
            return self.domain_overrides[domain]
        return (self.default_high, self.default_medium, self.default_low)

    def set_domain(
        self,
        domain: str,
        high: float,
        medium: float,
        low: float,
    ) -> None:
        """Register or update thresholds for a specific domain.

        Parameters
        ----------
        domain:
            Domain label to configure.
        high:
            HIGH threshold boundary.
        medium:
            MEDIUM threshold boundary.
        low:
            LOW threshold boundary.

        Raises
        ------
        ValueError
            If boundaries are not in strictly descending order.
        """
        if not (high > medium > low >= 0.0):
            raise ValueError(
                f"Thresholds must satisfy high > medium > low >= 0; "
                f"got high={high}, medium={medium}, low={low}."
            )
        self.domain_overrides[domain] = (high, medium, low)
