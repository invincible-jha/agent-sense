"""WCAG 2.1 AA accessibility checker — heuristic static analysis.

WCAGChecker inspects HTML fragments and text content for common WCAG 2.1 AA
violations. It does not load external resources or execute JavaScript; all
checks are performed with pattern matching on the supplied markup.

Checks implemented
------------------
- color_contrast    : Inline ``color``/``background-color`` pairs with known
                      low-contrast combinations (heuristic — full contrast ratio
                      computation requires rendered CSS).
- text_alternatives : ``<img>`` elements missing a non-empty ``alt`` attribute.
- heading_hierarchy : Heading levels that skip ranks (e.g. h1 -> h3).
- link_text         : ``<a>`` elements with no visible text or generic labels
                      such as "click here" or "read more".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class WCAGCriterion(str, Enum):
    """WCAG 2.1 success criterion identifiers."""

    COLOR_CONTRAST = "1.4.3"
    TEXT_ALTERNATIVES = "1.1.1"
    HEADING_HIERARCHY = "1.3.1"
    LINK_TEXT = "2.4.6"


class WCAGLevel(str, Enum):
    """Conformance level of the violated criterion."""

    A = "A"
    AA = "AA"
    AAA = "AAA"


@dataclass(frozen=True)
class WCAGViolation:
    """A single WCAG 2.1 violation found in the inspected content.

    Attributes
    ----------
    criterion:
        The WCAG success criterion number (e.g. ``"1.1.1"``).
    level:
        The conformance level of the criterion (A, AA, or AAA).
    description:
        Human-readable description of the violation.
    element_snippet:
        A short snippet of the problematic markup or text.
    suggestion:
        Recommended remediation for the violation.
    """

    criterion: str
    level: WCAGLevel
    description: str
    element_snippet: str
    suggestion: str

    def to_dict(self) -> dict[str, str]:
        """Serialise to a plain dict."""
        return {
            "criterion": self.criterion,
            "level": self.level.value,
            "description": self.description,
            "element_snippet": self.element_snippet,
            "suggestion": self.suggestion,
        }


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Matches <img> tags (non-greedy up to the closing >).
_IMG_TAG: re.Pattern[str] = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
# Checks for alt="" or alt=''.
_EMPTY_ALT: re.Pattern[str] = re.compile(r'\balt\s*=\s*["\']["\']', re.IGNORECASE)
# Checks for presence of any alt attribute.
_HAS_ALT: re.Pattern[str] = re.compile(r"\balt\s*=", re.IGNORECASE)

# Matches <a ...>...</a> with captured inner text.
_ANCHOR_TAG: re.Pattern[str] = re.compile(
    r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL
)
# Strips nested tags from anchor text.
_STRIP_TAGS: re.Pattern[str] = re.compile(r"<[^>]+>")

_GENERIC_LINK_TEXT: frozenset[str] = frozenset(
    {
        "click here",
        "here",
        "read more",
        "more",
        "learn more",
        "link",
        "this",
        "click",
        "go",
    }
)

# Matches heading tags h1 through h6.
_HEADING_TAG: re.Pattern[str] = re.compile(r"<h([1-6])\b", re.IGNORECASE)

# Simple heuristic: look for inline style with low-contrast colour pairings.
# These are known WCAG-failing combinations at body text sizes.
_LOW_CONTRAST_PAIRS: list[tuple[str, str]] = [
    ("#ffff00", "#ffffff"),
    ("#ffff00", "#fffffe"),
    ("#cccccc", "#ffffff"),
    ("#aaaaaa", "#ffffff"),
    ("#999999", "#ffffff"),
    ("#bbbbbb", "#ffffff"),
    ("#dddddd", "#ffffff"),
    ("#eeeeee", "#ffffff"),
    ("#777777", "#ffffff"),
    ("#888888", "#ffffff"),
    ("yellow", "white"),
    ("silver", "white"),
    ("lightgray", "white"),
    ("lightgrey", "white"),
]

_INLINE_STYLE: re.Pattern[str] = re.compile(
    r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE
)
_COLOR_PROPERTY: re.Pattern[str] = re.compile(
    r"(?:^|;)\s*color\s*:\s*([^;]+)", re.IGNORECASE
)
_BG_COLOR_PROPERTY: re.Pattern[str] = re.compile(
    r"(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)", re.IGNORECASE
)


def _strip_html(text: str) -> str:
    return _STRIP_TAGS.sub("", text).strip()


def _snippet(text: str, max_length: int = 80) -> str:
    text = text.strip()
    return text[:max_length] + "…" if len(text) > max_length else text


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class WCAGChecker:
    """Run WCAG 2.1 AA heuristic checks on HTML markup.

    All checks accept an HTML string and return a (possibly empty) list of
    WCAGViolation objects.

    Example
    -------
    >>> checker = WCAGChecker()
    >>> html = '<img src="logo.png"><a href="#">click here</a>'
    >>> violations = checker.check_all(html)
    >>> len(violations) >= 2
    True
    """

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def color_contrast(self, html: str) -> list[WCAGViolation]:
        """Heuristically detect low-contrast inline colour pairs.

        Scans ``style`` attributes for ``color`` / ``background-color`` pairs
        that match known WCAG-failing combinations.

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        list[WCAGViolation]
            Violations found (one per flagged element).
        """
        violations: list[WCAGViolation] = []
        for style_match in _INLINE_STYLE.finditer(html):
            style_value = style_match.group(1)
            color_match = _COLOR_PROPERTY.search(style_value)
            bg_match = _BG_COLOR_PROPERTY.search(style_value)
            if not (color_match and bg_match):
                continue
            fg = color_match.group(1).strip().lower().rstrip(";")
            bg = bg_match.group(1).strip().lower().rstrip(";")
            for low_fg, low_bg in _LOW_CONTRAST_PAIRS:
                if fg == low_fg and bg == low_bg:
                    violations.append(
                        WCAGViolation(
                            criterion=WCAGCriterion.COLOR_CONTRAST.value,
                            level=WCAGLevel.AA,
                            description=(
                                f"Low contrast ratio detected: foreground {fg!r} "
                                f"on background {bg!r} likely fails 4.5:1 minimum."
                            ),
                            element_snippet=_snippet(style_match.group(0)),
                            suggestion=(
                                "Choose a foreground colour with sufficient contrast "
                                "against the background. Use a contrast checker tool "
                                "to verify a ratio >= 4.5:1 for normal text."
                            ),
                        )
                    )
                    break
        return violations

    def text_alternatives(self, html: str) -> list[WCAGViolation]:
        """Detect ``<img>`` elements missing a non-empty ``alt`` attribute.

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        list[WCAGViolation]
            One violation per non-compliant image.
        """
        violations: list[WCAGViolation] = []
        for match in _IMG_TAG.finditer(html):
            tag = match.group(0)
            if not _HAS_ALT.search(tag):
                violations.append(
                    WCAGViolation(
                        criterion=WCAGCriterion.TEXT_ALTERNATIVES.value,
                        level=WCAGLevel.A,
                        description="<img> element has no alt attribute.",
                        element_snippet=_snippet(tag),
                        suggestion=(
                            "Add a descriptive alt attribute. "
                            "Use alt=\"\" for purely decorative images."
                        ),
                    )
                )
            elif _EMPTY_ALT.search(tag):
                # Empty alt is acceptable only for decorative images.
                # We emit a notice-level violation to prompt review.
                violations.append(
                    WCAGViolation(
                        criterion=WCAGCriterion.TEXT_ALTERNATIVES.value,
                        level=WCAGLevel.A,
                        description=(
                            "<img> has an empty alt attribute. "
                            "Ensure this image is truly decorative."
                        ),
                        element_snippet=_snippet(tag),
                        suggestion=(
                            "Provide a meaningful alt description if the image "
                            "conveys information. Empty alt is only appropriate for "
                            "decorative images."
                        ),
                    )
                )
        return violations

    def heading_hierarchy(self, html: str) -> list[WCAGViolation]:
        """Detect heading level skips (e.g. h1 -> h3, skipping h2).

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        list[WCAGViolation]
            One violation per skipped heading level.
        """
        violations: list[WCAGViolation] = []
        heading_levels = [
            int(m.group(1)) for m in _HEADING_TAG.finditer(html)
        ]
        for index in range(1, len(heading_levels)):
            previous = heading_levels[index - 1]
            current = heading_levels[index]
            if current > previous + 1:
                violations.append(
                    WCAGViolation(
                        criterion=WCAGCriterion.HEADING_HIERARCHY.value,
                        level=WCAGLevel.AA,
                        description=(
                            f"Heading level jumps from h{previous} to h{current}, "
                            "skipping one or more levels."
                        ),
                        element_snippet=f"h{previous} -> h{current}",
                        suggestion=(
                            f"Insert an h{previous + 1} between h{previous} and "
                            f"h{current}, or restructure the document hierarchy so "
                            "heading levels are contiguous."
                        ),
                    )
                )
        return violations

    def link_text(self, html: str) -> list[WCAGViolation]:
        """Detect ``<a>`` elements with empty or non-descriptive visible text.

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        list[WCAGViolation]
            One violation per non-descriptive or empty anchor.
        """
        violations: list[WCAGViolation] = []
        for match in _ANCHOR_TAG.finditer(html):
            inner_html = match.group(1)
            visible_text = _strip_html(inner_html).lower()
            tag_snippet = _snippet(match.group(0))

            if not visible_text:
                violations.append(
                    WCAGViolation(
                        criterion=WCAGCriterion.LINK_TEXT.value,
                        level=WCAGLevel.AA,
                        description="Anchor element has no visible text.",
                        element_snippet=tag_snippet,
                        suggestion=(
                            "Provide descriptive visible text inside the <a> tag, "
                            "or add an aria-label attribute that describes the link "
                            "destination."
                        ),
                    )
                )
            elif visible_text in _GENERIC_LINK_TEXT:
                violations.append(
                    WCAGViolation(
                        criterion=WCAGCriterion.LINK_TEXT.value,
                        level=WCAGLevel.AA,
                        description=(
                            f"Anchor text {visible_text!r} is non-descriptive and "
                            "does not convey the link destination."
                        ),
                        element_snippet=tag_snippet,
                        suggestion=(
                            "Replace generic link text with a specific description of "
                            "the destination (e.g. 'View account settings' instead of "
                            "'click here')."
                        ),
                    )
                )
        return violations

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------

    def check_all(self, html: str) -> list[WCAGViolation]:
        """Run all WCAG checks and return a combined list of violations.

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        list[WCAGViolation]
            All violations found, grouped in check order.
        """
        violations: list[WCAGViolation] = []
        violations.extend(self.color_contrast(html))
        violations.extend(self.text_alternatives(html))
        violations.extend(self.heading_hierarchy(html))
        violations.extend(self.link_text(html))
        return violations

    def summary(self, html: str) -> dict[str, int]:
        """Return a count of violations per WCAG criterion.

        Parameters
        ----------
        html:
            HTML markup to inspect.

        Returns
        -------
        dict[str, int]
            Maps criterion number to violation count.
        """
        all_violations = self.check_all(html)
        counts: dict[str, int] = {}
        for violation in all_violations:
            counts[violation.criterion] = counts.get(violation.criterion, 0) + 1
        return counts
