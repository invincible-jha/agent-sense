"""Screen reader optimizer — enhance HTML markup for assistive technologies.

ScreenReaderOptimizer adds ARIA roles, labels, and landmark attributes to
HTML fragments so that screen reader users receive a well-structured, fully
navigable experience.

Transformations performed
--------------------------
- ``<nav>`` without ``role``     -> adds ``role="navigation"``
- ``<main>`` without ``role``    -> adds ``role="main"``
- ``<header>`` without ``role``  -> adds ``role="banner"``
- ``<footer>`` without ``role``  -> adds ``role="contentinfo"``
- ``<aside>`` without ``role``   -> adds ``role="complementary"``
- ``<section>`` without ``aria-label`` or ``aria-labelledby``
                                 -> adds ``aria-label="section"``
- ``<button>`` without accessible name
                                 -> adds ``aria-label="button"`` placeholder
- ``<input>`` without ``aria-label`` or ``id``-linked ``<label>``
                                 -> adds ``aria-label`` from ``placeholder`` or type
- ``<img>`` without ``alt``      -> adds ``alt=""`` (decorative fallback)
- ``<table>`` without ``summary`` or ``<caption>``
                                 -> adds ``role="table"`` and ``aria-label``
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Helper: inject an attribute into a tag
# ---------------------------------------------------------------------------


def _add_attribute(tag: str, attribute: str, value: str) -> str:
    """Insert ``attribute="value"`` before the closing ``>`` of ``tag``."""
    # If already self-closing (<br/>), insert before '/>'.
    if tag.endswith("/>"):
        return tag[:-2] + f' {attribute}="{value}" />'
    return tag[:-1] + f' {attribute}="{value}">'


def _has_attribute(tag: str, attribute: str) -> bool:
    """Return True if ``attribute`` is present in the tag string."""
    pattern = re.compile(r"\b" + re.escape(attribute) + r"\s*=", re.IGNORECASE)
    return bool(pattern.search(tag))


def _get_attribute(tag: str, attribute: str) -> str:
    """Extract the value of an attribute from a tag string, or return ''."""
    pattern = re.compile(
        r'\b' + re.escape(attribute) + r'\s*=\s*["\']([^"\']*)["\']',
        re.IGNORECASE,
    )
    match = pattern.search(tag)
    return match.group(1) if match else ""


# ---------------------------------------------------------------------------
# Landmark roles
# ---------------------------------------------------------------------------

_LANDMARK_ELEMENTS: list[tuple[str, str]] = [
    ("nav", "navigation"),
    ("main", "main"),
    ("header", "banner"),
    ("footer", "contentinfo"),
    ("aside", "complementary"),
]


def _add_landmark_roles(html: str) -> str:
    """Add ARIA roles to landmark HTML5 elements that lack them."""
    for element, role in _LANDMARK_ELEMENTS:
        pattern = re.compile(
            r"(<" + element + r"\b(?![^>]*\brole\s*=)[^>]*)>",
            re.IGNORECASE,
        )
        html = pattern.sub(lambda m: _add_attribute(m.group(0), "role", role), html)
    return html


# ---------------------------------------------------------------------------
# Section labels
# ---------------------------------------------------------------------------

_SECTION_WITHOUT_LABEL: re.Pattern[str] = re.compile(
    r"(<section\b(?![^>]*\baria-label(?:ledby)?\s*=)[^>]*)>",
    re.IGNORECASE,
)


def _add_section_labels(html: str) -> str:
    """Add an ``aria-label`` to ``<section>`` elements that lack labelling."""
    return _SECTION_WITHOUT_LABEL.sub(
        lambda m: _add_attribute(m.group(0), "aria-label", "section"),
        html,
    )


# ---------------------------------------------------------------------------
# Buttons without accessible names
# ---------------------------------------------------------------------------

_BUTTON_TAG: re.Pattern[str] = re.compile(r"<button\b[^>]*>", re.IGNORECASE)
_BUTTON_INNER: re.Pattern[str] = re.compile(
    r"<button\b([^>]*)>(.*?)</button>", re.IGNORECASE | re.DOTALL
)
_STRIP_TAGS: re.Pattern[str] = re.compile(r"<[^>]+>")


def _add_button_labels(html: str) -> str:
    """Add ``aria-label`` to buttons that have no accessible name."""

    def _process_button(match: re.Match[str]) -> str:  # type: ignore[type-arg]
        attrs = match.group(1)
        inner = _STRIP_TAGS.sub("", match.group(2)).strip()
        tag_str = "<button" + attrs + ">"
        full_match = match.group(0)
        # Already has aria-label or aria-labelledby.
        if re.search(r"\baria-label(?:ledby)?\s*=", attrs, re.IGNORECASE):
            return full_match
        # Has visible text — no label needed.
        if inner:
            return full_match
        # No visible text — add placeholder aria-label.
        new_tag = _add_attribute(tag_str, "aria-label", "button")
        return new_tag + match.group(2) + "</button>"

    return _BUTTON_INNER.sub(_process_button, html)


# ---------------------------------------------------------------------------
# Input elements
# ---------------------------------------------------------------------------

_INPUT_TAG: re.Pattern[str] = re.compile(r"<input\b[^>]*>", re.IGNORECASE)


def _add_input_labels(html: str) -> str:
    """Add ``aria-label`` to ``<input>`` elements that lack accessible names."""

    def _process_input(match: re.Match[str]) -> str:  # type: ignore[type-arg]
        tag = match.group(0)
        # Already has aria-label or aria-labelledby or id (paired with <label for>).
        if _has_attribute(tag, "aria-label") or _has_attribute(tag, "aria-labelledby"):
            return tag
        if _has_attribute(tag, "id"):
            # Assume a <label for="..."> exists elsewhere — do not add redundant label.
            return tag
        # Derive label from placeholder or type.
        placeholder = _get_attribute(tag, "placeholder")
        input_type = _get_attribute(tag, "type") or "text"
        label = placeholder or input_type
        return _add_attribute(tag, "aria-label", label)

    return _INPUT_TAG.sub(_process_input, html)


# ---------------------------------------------------------------------------
# Images without alt
# ---------------------------------------------------------------------------

_IMG_WITHOUT_ALT: re.Pattern[str] = re.compile(
    r"(<img\b(?![^>]*\balt\s*=)[^>]*)(/?>)",
    re.IGNORECASE,
)


def _add_img_alt(html: str) -> str:
    """Add ``alt=""`` to ``<img>`` elements that have no alt attribute."""
    return _IMG_WITHOUT_ALT.sub(
        lambda m: _add_attribute(m.group(1) + m.group(2), "alt", ""),
        html,
    )


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

_TABLE_WITHOUT_ROLE: re.Pattern[str] = re.compile(
    r"(<table\b(?![^>]*\brole\s*=)[^>]*)>",
    re.IGNORECASE,
)
_TABLE_HAS_CAPTION: re.Pattern[str] = re.compile(
    r"<table\b[^>]*>.*?<caption\b", re.IGNORECASE | re.DOTALL
)


def _add_table_roles(html: str) -> str:
    """Add ``role="table"`` and ``aria-label`` to unlabelled tables."""
    if _TABLE_HAS_CAPTION.search(html):
        return html
    return _TABLE_WITHOUT_ROLE.sub(
        lambda m: _add_attribute(
            _add_attribute(m.group(0), "role", "table"),
            "aria-label",
            "data table",
        ),
        html,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class ScreenReaderOptimizer:
    """Add ARIA landmarks, roles, and labels to HTML for screen reader users.

    Example
    -------
    >>> opt = ScreenReaderOptimizer()
    >>> html = '<nav><a href="/">Home</a></nav><img src="logo.png">'
    >>> result = opt.optimize(html)
    >>> 'role="navigation"' in result
    True
    >>> 'alt=""' in result
    True
    """

    def optimize(self, html: str) -> str:
        """Apply all screen reader optimisations to the given HTML.

        Optimisations are applied in a fixed order so that later passes do
        not undo the work of earlier ones.

        Parameters
        ----------
        html:
            Raw HTML markup to enhance.

        Returns
        -------
        str
            Enhanced HTML with ARIA attributes added where missing.
        """
        html = _add_landmark_roles(html)
        html = _add_section_labels(html)
        html = _add_button_labels(html)
        html = _add_input_labels(html)
        html = _add_img_alt(html)
        html = _add_table_roles(html)
        return html

    def optimize_landmark_roles(self, html: str) -> str:
        """Apply only landmark role enhancements.

        Parameters
        ----------
        html:
            Raw HTML markup.

        Returns
        -------
        str
            HTML with ARIA landmark roles added.
        """
        return _add_landmark_roles(html)

    def optimize_images(self, html: str) -> str:
        """Apply only image alt-text enhancements.

        Parameters
        ----------
        html:
            Raw HTML markup.

        Returns
        -------
        str
            HTML with alt attributes added to images that lack them.
        """
        return _add_img_alt(html)
