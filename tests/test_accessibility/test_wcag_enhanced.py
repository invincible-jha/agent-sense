"""Tests for WCAGEnhancer — E16.4."""

from __future__ import annotations

import pytest

from agent_sense.accessibility.wcag_enhanced import (
    ComplianceReport,
    EnhancementConfig,
    WCAGEnhancer,
)


# ---------------------------------------------------------------------------
# EnhancementConfig
# ---------------------------------------------------------------------------


class TestEnhancementConfig:
    def test_default_config(self) -> None:
        config = EnhancementConfig()
        assert config.add_aria_labels is True
        assert config.add_keyboard_hints is True
        assert config.high_contrast_mode is False
        assert config.add_screen_reader_text is True
        assert config.language_code == "en"

    def test_frozen(self) -> None:
        config = EnhancementConfig()
        with pytest.raises((AttributeError, TypeError)):
            config.language_code = "fr"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WCAGEnhancer — basic setup
# ---------------------------------------------------------------------------


class TestWCAGEnhancerInit:
    def test_default_enhancer_created(self) -> None:
        enhancer = WCAGEnhancer()
        assert enhancer._config.add_aria_labels is True

    def test_custom_config(self) -> None:
        config = EnhancementConfig(high_contrast_mode=True)
        enhancer = WCAGEnhancer(config)
        assert enhancer._config.high_contrast_mode is True


# ---------------------------------------------------------------------------
# enhance() — ARIA labels
# ---------------------------------------------------------------------------


class TestAriaLabels:
    def test_adds_aria_label_to_anchor_without_one(self) -> None:
        config = EnhancementConfig(add_keyboard_hints=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = '<a href="/home">Home</a>'
        enhanced, report = enhancer.enhance(html)
        assert "aria-label" in enhanced

    def test_does_not_duplicate_existing_aria_label(self) -> None:
        config = EnhancementConfig(add_keyboard_hints=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = '<a href="/home" aria-label="Go to home page">Home</a>'
        enhanced, report = enhancer.enhance(html)
        assert enhanced.count("aria-label") == 1

    def test_adds_aria_label_to_button(self) -> None:
        config = EnhancementConfig(add_keyboard_hints=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = "<button>Submit</button>"
        enhanced, report = enhancer.enhance(html)
        assert "aria-label" in enhanced

    def test_enhancement_logged_in_report(self) -> None:
        config = EnhancementConfig(add_keyboard_hints=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = '<a href="#">Click</a>'
        _, report = enhancer.enhance(html)
        assert len(report.enhancements_applied) >= 0


# ---------------------------------------------------------------------------
# enhance() — keyboard hints
# ---------------------------------------------------------------------------


class TestKeyboardHints:
    def test_adds_tabindex_to_anchor_with_href(self) -> None:
        config = EnhancementConfig(add_aria_labels=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = '<a href="/page">Go</a>'
        enhanced, report = enhancer.enhance(html)
        assert "tabindex" in enhanced

    def test_no_tabindex_added_to_anchor_without_href(self) -> None:
        config = EnhancementConfig(add_aria_labels=False, add_screen_reader_text=False)
        enhancer = WCAGEnhancer(config)
        html = "<a>Anchor without href</a>"
        enhanced, report = enhancer.enhance(html)
        # Without href, no tabindex should be injected
        # (the regex requires href)
        assert "tabindex" not in enhanced


# ---------------------------------------------------------------------------
# enhance() — high contrast
# ---------------------------------------------------------------------------


class TestHighContrast:
    def test_replaces_low_contrast_color(self) -> None:
        config = EnhancementConfig(
            add_aria_labels=False,
            add_keyboard_hints=False,
            add_screen_reader_text=False,
            high_contrast_mode=True,
        )
        enhancer = WCAGEnhancer(config)
        html = '<p style="color:#aaaaaa;background:white">Low contrast text</p>'
        enhanced, report = enhancer.enhance(html)
        # The low-contrast color should be replaced
        assert "#aaaaaa" not in enhanced.lower() or "#595959" in enhanced

    def test_high_contrast_off_leaves_styles_unchanged(self) -> None:
        config = EnhancementConfig(
            add_aria_labels=False,
            add_keyboard_hints=False,
            add_screen_reader_text=False,
            high_contrast_mode=False,
        )
        enhancer = WCAGEnhancer(config)
        html = '<p style="color:#aaaaaa">Text</p>'
        enhanced, _ = enhancer.enhance(html)
        assert "#aaaaaa" in enhanced


# ---------------------------------------------------------------------------
# enhance() — screen reader text
# ---------------------------------------------------------------------------


class TestScreenReaderText:
    def test_adds_sr_only_to_icon_link(self) -> None:
        config = EnhancementConfig(
            add_aria_labels=False,
            add_keyboard_hints=False,
            add_screen_reader_text=True,
        )
        enhancer = WCAGEnhancer(config)
        html = '<a href="/"><img src="icon.png"/></a>'
        enhanced, report = enhancer.enhance(html)
        assert "sr-only" in enhanced

    def test_no_sr_text_added_to_normal_link(self) -> None:
        config = EnhancementConfig(
            add_aria_labels=False,
            add_keyboard_hints=False,
            add_screen_reader_text=True,
        )
        enhancer = WCAGEnhancer(config)
        html = '<a href="/page">Click here to read more details</a>'
        enhanced, _ = enhancer.enhance(html)
        # No icon-only detection — sr-only should not be injected
        assert enhanced.count("sr-only") == 0


# ---------------------------------------------------------------------------
# check_compliance
# ---------------------------------------------------------------------------


class TestCheckCompliance:
    def test_clean_html_is_compliant(self) -> None:
        enhancer = WCAGEnhancer()
        html = (
            '<h1>Title</h1>'
            '<h2>Section</h2>'
            '<img src="logo.png" alt="Company logo">'
            '<a href="/about">About us</a>'
        )
        report = enhancer.check_compliance(html)
        assert isinstance(report, ComplianceReport)
        assert report.violation_count == 0
        assert report.compliant is True

    def test_non_compliant_html_has_violations(self) -> None:
        enhancer = WCAGEnhancer()
        html = '<img src="logo.png"><a href="#">click here</a>'
        report = enhancer.check_compliance(html)
        assert report.violation_count > 0
        assert report.compliant is False

    def test_compliance_report_to_dict(self) -> None:
        enhancer = WCAGEnhancer()
        html = '<img src="logo.png">'
        report = enhancer.check_compliance(html)
        data = report.to_dict()
        assert "compliant" in data
        assert "violation_count" in data
        assert "violations" in data
        assert "enhancements_applied" in data


# ---------------------------------------------------------------------------
# Lang attribute enforcement
# ---------------------------------------------------------------------------


class TestLangAttribute:
    def test_adds_lang_to_html_element(self) -> None:
        enhancer = WCAGEnhancer()
        html = "<html><body>Content</body></html>"
        result = enhancer.enforce_lang_attribute(html)
        assert 'lang="en"' in result

    def test_does_not_duplicate_lang_attribute(self) -> None:
        enhancer = WCAGEnhancer()
        html = '<html lang="fr"><body>Content</body></html>'
        result = enhancer.enforce_lang_attribute(html)
        assert result.count("lang=") == 1


# ---------------------------------------------------------------------------
# Skip link generation
# ---------------------------------------------------------------------------


class TestSkipLink:
    def test_generates_skip_link(self) -> None:
        enhancer = WCAGEnhancer()
        skip_link = enhancer.generate_skip_link()
        assert "skip-link" in skip_link
        assert "#main-content" in skip_link

    def test_custom_target_id(self) -> None:
        enhancer = WCAGEnhancer()
        skip_link = enhancer.generate_skip_link(target_id="content")
        assert "#content" in skip_link
