"""Web context adapter — browser-based context from HTTP headers and user-agent.

WebContextAdapter is the primary adapter for traditional web (browser) clients.
It extracts context from the standard HTTP headers typically present in REST or
GraphQL requests coming from a browser.
"""
from __future__ import annotations

from agent_sense.context.detector import ContextDetector, DetectedContext


# Headers forwarded by CDNs / edge workers that carry network quality hints.
_NETWORK_HINT_HEADERS: frozenset[str] = frozenset(
    {
        "ect",
        "downlink",
        "rtt",
        "save-data",
        "sec-ch-prefers-reduced-motion",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "x-forwarded-for",
        "cf-connecting-ip",
        "x-real-ip",
    }
)


class WebContextAdapter:
    """Browser-based context adapter built from HTTP request headers.

    Parses a standard browser request header dict to produce a
    :class:`~agent_sense.context.detector.DetectedContext`.

    Parameters
    ----------
    headers:
        Mapping of HTTP header names to values, as received by the server.
        Header names are matched case-insensitively.

    Example
    -------
    >>> adapter = WebContextAdapter({
    ...     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    ...     "ect": "4g",
    ... })
    >>> ctx = adapter.extract()
    >>> ctx.device_type.value
    'desktop'
    """

    def __init__(self, headers: dict[str, str]) -> None:
        # Normalise header names to lower-case for consistent lookup.
        self._headers: dict[str, str] = {k.lower(): v for k, v in headers.items()}

    @property
    def user_agent(self) -> str:
        """Return the User-Agent string, or empty string if absent."""
        return self._headers.get("user-agent", "")

    def extract(self) -> DetectedContext:
        """Extract context from the supplied headers.

        Returns
        -------
        DetectedContext
            Detected device type, network quality, and browser capabilities.
        """
        detector = ContextDetector(
            user_agent=self.user_agent,
            headers=self._headers,
        )
        return detector.detect()

    def get_client_ip(self) -> str:
        """Return the best-effort client IP address from forwarding headers."""
        for header in ("x-forwarded-for", "cf-connecting-ip", "x-real-ip"):
            value = self._headers.get(header, "")
            if value:
                # X-Forwarded-For may be a comma-separated list; take the first.
                return value.split(",")[0].strip()
        return ""

    def get_accepted_languages(self) -> list[str]:
        """Parse Accept-Language header into an ordered list of language tags.

        Returns
        -------
        list[str]
            Ordered list of BCP-47 language tags (e.g. ``["en-US", "en"]``),
            or an empty list if the header is absent.
        """
        raw = self._headers.get("accept-language", "")
        if not raw:
            return []
        # Each entry looks like "en-US,en;q=0.9,fr;q=0.8"
        parts: list[tuple[float, str]] = []
        for segment in raw.split(","):
            segment = segment.strip()
            if ";q=" in segment:
                lang, q_str = segment.rsplit(";q=", 1)
                try:
                    quality = float(q_str)
                except ValueError:
                    quality = 1.0
            else:
                lang = segment
                quality = 1.0
            parts.append((quality, lang.strip()))
        parts.sort(key=lambda pair: pair[0], reverse=True)
        return [lang for _, lang in parts]
