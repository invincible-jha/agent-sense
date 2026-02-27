"""WCAGEnhancer — WCAG 2.1 AA enhancement for agent component outputs.

Adds ARIA labels, keyboard navigation hints, high-contrast mode support,
and screen reader text to component outputs. Performs compliance checks
against the existing WCAGChecker and augments HTML/text components.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from agent_sense.accessibility.wcag import WCAGChecker, WCAGViolation


@dataclass(frozen=True)
class EnhancementConfig:
    """Configuration for WCAG enhancements.

    Parameters
    ----------
    add_aria_labels:
        Automatically inject ARIA labels on interactive elements.
    add_keyboard_hints:
        Inject keyboard navigation hint attributes.
    high_contrast_mode:
        Replace known low-contrast inline styles with high-contrast equivalents.
    add_screen_reader_text:
        Inject sr-only spans for icon-only buttons and links.
    language_code:
        HTML lang attribute value to enforce. Defaults to ``"en"``.
    """

    add_aria_labels: bool = True
    add_keyboard_hints: bool = True
    high_contrast_mode: bool = False
    add_screen_reader_text: bool = True
    language_code: str = "en"


@dataclass
class ComplianceReport:
    """WCAG compliance report for a component.

    Parameters
    ----------
    violations:
        List of WCAG violations found.
    enhancements_applied:
        Descriptive list of enhancements that were applied.
    compliant:
        Whether the component has zero violations after enhancement.
    """

    violations: list[WCAGViolation] = field(default_factory=list)
    enhancements_applied: list[str] = field(default_factory=list)
    compliant: bool = False

    @property
    def violation_count(self) -> int:
        """Total number of violations."""
        return len(self.violations)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "compliant": self.compliant,
            "violation_count": self.violation_count,
            "violations": [v.to_dict() for v in self.violations],
            "enhancements_applied": list(self.enhancements_applied),
        }


# ---------------------------------------------------------------------------
# Patterns for enhancement
# ---------------------------------------------------------------------------

# Anchor tags without aria-label
_ANCHOR_NO_ARIA: re.Pattern[str] = re.compile(
    r'<a\b(?![^>]*\baria-label\b)[^>]*>', re.IGNORECASE
)
# Button tags without aria-label or aria-labelledby
_BUTTON_NO_ARIA: re.Pattern[str] = re.compile(
    r'<button\b(?![^>]*\baria-(?:label|labelledby)\b)[^>]*>', re.IGNORECASE
)
# Input tags without aria-label or id-based label
_INPUT_NO_ARIA: re.Pattern[str] = re.compile(
    r'<input\b(?![^>]*\baria-label\b)[^>]*>', re.IGNORECASE
)
# tabindex not present on interactive elements
_INTERACTIVE_NO_TABINDEX: re.Pattern[str] = re.compile(
    r'<(?:a|button|input|select|textarea)\b(?![^>]*\btabindex\b)[^>]*>',
    re.IGNORECASE,
)
# Inline styles with known low-contrast pairs
_STYLE_ATTR: re.Pattern[str] = re.compile(
    r'(style\s*=\s*["\'])([^"\']*?)(["\'])', re.IGNORECASE
)

# Known low-contrast → high-contrast replacements
_CONTRAST_FIXES: dict[str, str] = {
    "color:#aaaaaa": "color:#595959",
    "color:#bbbbbb": "color:#444444",
    "color:#cccccc": "color:#333333",
    "color:#999999": "color:#595959",
    "color:#888888": "color:#444444",
    "color:#777777": "color:#333333",
    "color:yellow": "color:#6b6b00",
    "color:silver": "color:#595959",
    "color:lightgray": "color:#595959",
    "color:lightgrey": "color:#595959",
}

# Icon-only links (href with no visible text)
_ICON_LINK: re.Pattern[str] = re.compile(
    r'(<a\b[^>]*>)\s*(<(?:img|svg|i|span\s+class="icon[^"]*")[^>]*/?>)\s*(</a>)',
    re.IGNORECASE | re.DOTALL,
)


class WCAGEnhancer:
    """Apply WCAG 2.1 AA enhancements to HTML component outputs.

    Works by pattern-matching on HTML strings and injecting accessibility
    attributes. Designed for server-side rendering scenarios where HTML
    is generated before delivery to the client.

    Parameters
    ----------
    config:
        Enhancement configuration.
    checker:
        WCAGChecker instance for compliance assessment.
    """

    def __init__(
        self,
        config: Optional[EnhancementConfig] = None,
        checker: Optional[WCAGChecker] = None,
    ) -> None:
        self._config = config or EnhancementConfig()
        self._checker = checker or WCAGChecker()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enhance(self, html: str) -> tuple[str, ComplianceReport]:
        """Apply all configured enhancements to HTML markup.

        Parameters
        ----------
        html:
            HTML markup to enhance.

        Returns
        -------
        tuple[str, ComplianceReport]
            Enhanced HTML and a compliance report.
        """
        enhanced = html
        applied: list[str] = []

        if self._config.add_aria_labels:
            enhanced, added = self._add_aria_labels(enhanced)
            applied.extend(added)

        if self._config.add_keyboard_hints:
            enhanced, added = self._add_keyboard_hints(enhanced)
            applied.extend(added)

        if self._config.high_contrast_mode:
            enhanced, added = self._apply_high_contrast(enhanced)
            applied.extend(added)

        if self._config.add_screen_reader_text:
            enhanced, added = self._add_screen_reader_text(enhanced)
            applied.extend(added)

        # Run compliance check on enhanced output
        violations = self._checker.check_all(enhanced)
        compliant = len(violations) == 0

        return enhanced, ComplianceReport(
            violations=violations,
            enhancements_applied=applied,
            compliant=compliant,
        )

    def check_compliance(self, html: str) -> ComplianceReport:
        """Run compliance checks without applying enhancements.

        Parameters
        ----------
        html:
            HTML markup to check.

        Returns
        -------
        ComplianceReport
            Violations found and empty enhancements list.
        """
        violations = self._checker.check_all(html)
        return ComplianceReport(
            violations=violations,
            enhancements_applied=[],
            compliant=len(violations) == 0,
        )

    def enforce_lang_attribute(self, html: str) -> str:
        """Ensure the root html element has a lang attribute.

        Parameters
        ----------
        html:
            Full HTML document or fragment.

        Returns
        -------
        str
            HTML with lang attribute added if absent.
        """
        lang = self._config.language_code
        # If <html> tag present without lang, add it
        html_tag = re.compile(r'<html\b(?![^>]*\blang\b)[^>]*>', re.IGNORECASE)
        if html_tag.search(html):
            return html_tag.sub(lambda m: m.group(0).replace(">", f' lang="{lang}">'), html)
        return html

    def generate_skip_link(self, target_id: str = "main-content") -> str:
        """Generate a keyboard-accessible skip navigation link.

        Parameters
        ----------
        target_id:
            ID of the main content element to skip to.

        Returns
        -------
        str
            HTML skip-link element.
        """
        return (
            f'<a href="#{target_id}" class="skip-link" '
            f'style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden"'
            f'>Skip to main content</a>'
        )

    # ------------------------------------------------------------------
    # Private enhancement methods
    # ------------------------------------------------------------------

    def _add_aria_labels(self, html: str) -> tuple[str, list[str]]:
        """Add aria-label to anchors and buttons missing them."""
        applied: list[str] = []

        def _inject_aria_anchor(match: re.Match[str]) -> str:
            tag = match.group(0)
            if "aria-label" not in tag.lower():
                tag = tag[:-1] + ' aria-label="link">'
                return tag
            return tag

        def _inject_aria_button(match: re.Match[str]) -> str:
            tag = match.group(0)
            if "aria-label" not in tag.lower():
                tag = tag[:-1] + ' aria-label="button">'
                return tag
            return tag

        new_html = _ANCHOR_NO_ARIA.sub(_inject_aria_anchor, html)
        if new_html != html:
            applied.append("Added aria-label to anchor elements")

        prev = new_html
        new_html = _BUTTON_NO_ARIA.sub(_inject_aria_button, new_html)
        if new_html != prev:
            applied.append("Added aria-label to button elements")

        return new_html, applied

    def _add_keyboard_hints(self, html: str) -> tuple[str, list[str]]:
        """Add tabindex=0 to interactive elements missing it."""
        applied: list[str] = []

        def _inject_tabindex(match: re.Match[str]) -> str:
            tag = match.group(0)
            if "tabindex" not in tag.lower() and "href" in tag.lower():
                # Only add tabindex to anchors with href
                tag = tag[:-1] + ' tabindex="0">'
            return tag

        new_html = re.sub(
            r'<a\b(?![^>]*\btabindex\b)[^>]*href[^>]*>',
            _inject_tabindex,
            html,
            flags=re.IGNORECASE,
        )
        if new_html != html:
            applied.append("Added tabindex to focusable anchor elements")

        return new_html, applied

    def _apply_high_contrast(self, html: str) -> tuple[str, list[str]]:
        """Replace low-contrast inline styles with high-contrast alternatives."""
        applied: list[str] = []
        new_html = html

        for low, high in _CONTRAST_FIXES.items():
            if low in new_html.lower():
                # Case-insensitive replace using regex
                pattern = re.compile(re.escape(low), re.IGNORECASE)
                replacement = new_html
                replacement = pattern.sub(high, replacement)
                if replacement != new_html:
                    new_html = replacement
                    applied.append(f"Applied high-contrast fix: {low} -> {high}")

        return new_html, applied

    def _add_screen_reader_text(self, html: str) -> tuple[str, list[str]]:
        """Add sr-only text for icon-only links."""
        applied: list[str] = []

        def _inject_sr_text(match: re.Match[str]) -> str:
            open_tag = match.group(1)
            icon = match.group(2)
            close_tag = match.group(3)
            sr_span = '<span class="sr-only">Link</span>'
            return f"{open_tag}{icon}{sr_span}{close_tag}"

        new_html = _ICON_LINK.sub(_inject_sr_text, html)
        if new_html != html:
            applied.append("Added screen reader text to icon-only links")

        return new_html, applied


__all__ = ["WCAGEnhancer", "EnhancementConfig", "ComplianceReport"]
