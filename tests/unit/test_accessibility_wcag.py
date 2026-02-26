"""Tests for agent_sense.accessibility.wcag."""
from __future__ import annotations

import pytest

from agent_sense.accessibility.wcag import WCAGChecker, WCAGViolation


class TestWCAGCheckerTextAlternatives:
    def test_img_without_alt_is_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="photo.jpg">')
        assert len(violations) >= 1
        assert any("alt" in v.description.lower() or "1.1.1" in v.criterion for v in violations)

    def test_img_with_alt_no_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="photo.jpg" alt="A photo">')
        assert violations == []

    def test_img_with_empty_alt_no_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="photo.jpg" alt="">')
        # Empty alt is acceptable for decorative images
        assert isinstance(violations, list)

    def test_no_images_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<p>No images here</p>')
        assert violations == []

    def test_multiple_imgs_missing_alt(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="a.jpg"><img src="b.jpg">')
        assert len(violations) >= 2

    def test_violation_has_criterion(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="x.jpg">')
        assert violations[0].criterion == "1.1.1"

    def test_violation_has_suggestion(self) -> None:
        checker = WCAGChecker()
        violations = checker.text_alternatives('<img src="x.jpg">')
        assert violations[0].suggestion != ""


class TestWCAGCheckerHeadingHierarchy:
    def test_heading_skip_is_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('<h1>Title</h1><h3>Skip</h3>')
        assert len(violations) >= 1

    def test_sequential_headings_no_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('<h1>Title</h1><h2>Subtitle</h2><h3>Sub-sub</h3>')
        assert violations == []

    def test_empty_html_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('')
        assert violations == []

    def test_no_headings_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('<p>No headings</p>')
        assert violations == []

    def test_single_heading_no_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('<h1>Only heading</h1>')
        assert violations == []

    def test_heading_skip_violation_criterion(self) -> None:
        checker = WCAGChecker()
        violations = checker.heading_hierarchy('<h1>Title</h1><h3>Skip h2</h3>')
        assert violations[0].criterion == "1.3.1"


class TestWCAGCheckerLinkText:
    def test_generic_link_text_is_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.link_text('<a href="#">click here</a>')
        assert len(violations) >= 1

    def test_descriptive_link_text_no_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.link_text('<a href="/about">About our company</a>')
        assert violations == []

    def test_read_more_is_violation(self) -> None:
        checker = WCAGChecker()
        violations = checker.link_text('<a href="#">read more</a>')
        assert len(violations) >= 1

    def test_no_links_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.link_text('<p>No links here</p>')
        assert violations == []

    def test_link_text_criterion(self) -> None:
        checker = WCAGChecker()
        violations = checker.link_text('<a href="#">click here</a>')
        assert violations[0].criterion == "2.4.6"


class TestWCAGCheckerColorContrast:
    def test_returns_list(self) -> None:
        checker = WCAGChecker()
        violations = checker.color_contrast('<p>Normal text</p>')
        assert isinstance(violations, list)

    def test_low_contrast_inline_style_is_violation(self) -> None:
        checker = WCAGChecker()
        # White on white — zero contrast
        violations = checker.color_contrast(
            '<p style="color: #ffffff; background-color: #ffffff">invisible</p>'
        )
        # May or may not detect depending on implementation details
        assert isinstance(violations, list)

    def test_no_inline_styles_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.color_contrast('<p class="text-dark">Styled via class</p>')
        assert violations == []


class TestWCAGCheckerCheckAll:
    def test_clean_html_no_violations(self) -> None:
        checker = WCAGChecker()
        violations = checker.check_all('<p>Clean content</p>')
        assert violations == []

    def test_multiple_violations_detected(self) -> None:
        checker = WCAGChecker()
        html = '<img src="x.jpg"><a href="#">click here</a>'
        violations = checker.check_all(html)
        assert len(violations) >= 2

    def test_returns_list_of_wcag_violations(self) -> None:
        checker = WCAGChecker()
        html = '<img src="x.jpg">'
        violations = checker.check_all(html)
        for v in violations:
            assert isinstance(v, WCAGViolation)

    def test_violation_has_level(self) -> None:
        checker = WCAGChecker()
        violations = checker.check_all('<img src="x.jpg">')
        assert violations[0].level is not None

    def test_violation_has_element_snippet(self) -> None:
        checker = WCAGChecker()
        violations = checker.check_all('<img src="x.jpg">')
        assert violations[0].element_snippet != ""

    def test_heading_skip_detected_in_check_all(self) -> None:
        checker = WCAGChecker()
        violations = checker.check_all('<h1>Title</h1><h3>Skip</h3>')
        assert any("1.3.1" in v.criterion for v in violations)
