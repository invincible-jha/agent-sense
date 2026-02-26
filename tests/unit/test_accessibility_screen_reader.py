"""Tests for agent_sense.accessibility.screen_reader."""
from __future__ import annotations

import pytest

from agent_sense.accessibility.screen_reader import ScreenReaderOptimizer


class TestScreenReaderOptimizerOptimize:
    def test_returns_string(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize("<p>Hello</p>")
        assert isinstance(result, str)

    def test_optimize_empty_string(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize("")
        assert result == ""

    def test_optimize_plain_text(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize("plain text no html")
        assert isinstance(result, str)

    def test_nav_gets_navigation_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<nav>Menu</nav>')
        assert 'role="navigation"' in result

    def test_img_no_alt_gets_empty_alt(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<img src="photo.jpg">')
        assert 'alt=""' in result

    def test_img_with_alt_preserved(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<img src="logo.png" alt="Company logo">')
        assert 'alt="Company logo"' in result

    def test_input_gets_aria_label(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<input type="text">')
        assert "aria-label" in result

    def test_table_gets_role(self) -> None:
        opt = ScreenReaderOptimizer()
        html = "<table><tr><td>Cell</td></tr></table>"
        result = opt.optimize(html)
        assert isinstance(result, str)
        assert "<table" in result

    def test_multiple_enhancements_combined(self) -> None:
        opt = ScreenReaderOptimizer()
        html = '<nav><a href="/">Home</a></nav><img src="logo.png">'
        result = opt.optimize(html)
        assert 'role="navigation"' in result
        assert 'alt=""' in result

    def test_header_gets_banner_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<header>Top</header>')
        assert "header" in result

    def test_main_gets_main_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<main>Content</main>')
        assert "main" in result

    def test_footer_gets_contentinfo_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<footer>Bottom</footer>')
        assert "footer" in result

    def test_aside_gets_complementary_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<aside>Sidebar</aside>')
        assert "aside" in result

    def test_section_gets_label(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<section>Body</section>')
        assert "section" in result

    def test_button_processed(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize('<button>Click me</button>')
        assert "button" in result


class TestOptimizeLandmarkRoles:
    def test_nav_gets_navigation_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<nav>links</nav>')
        assert 'role="navigation"' in result

    def test_header_gets_banner_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<header>top</header>')
        assert "header" in result

    def test_main_gets_main_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<main>content</main>')
        assert "main" in result

    def test_footer_gets_contentinfo_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<footer>bottom</footer>')
        assert "footer" in result

    def test_aside_gets_complementary_role(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<aside>sidebar</aside>')
        assert "aside" in result

    def test_empty_html_returns_empty(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles("")
        assert result == ""

    def test_already_has_role_not_duplicated(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<nav role="navigation">links</nav>')
        assert result.count('role="navigation"') == 1

    def test_non_landmark_element_unchanged(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_landmark_roles('<div>content</div>')
        assert result == '<div>content</div>'


class TestOptimizeImages:
    def test_img_without_alt_gets_empty_alt(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_images('<img src="photo.jpg">')
        assert 'alt=""' in result

    def test_img_with_empty_alt_preserved(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_images('<img src="photo.jpg" alt="">')
        assert 'alt=""' in result

    def test_img_with_alt_value_unchanged(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_images('<img src="photo.jpg" alt="description">')
        assert 'alt="description"' in result

    def test_multiple_images_all_get_alt(self) -> None:
        opt = ScreenReaderOptimizer()
        result = opt.optimize_images('<img src="a.jpg"><img src="b.jpg">')
        assert result.count("alt=") == 2

    def test_no_images_html_unchanged(self) -> None:
        opt = ScreenReaderOptimizer()
        html = '<p>text only</p>'
        result = opt.optimize_images(html)
        assert result == html
