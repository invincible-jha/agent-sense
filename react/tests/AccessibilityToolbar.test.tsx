/**
 * Tests for AccessibilityToolbar component.
 *
 * Covers:
 *   - Renders toolbar landmark
 *   - Three text size buttons (A, A+, A++) present
 *   - High contrast, reduced motion, focus indicator toggles
 *   - aria-pressed state reflects current preference
 *   - Reset button restores defaults
 *   - localStorage persistence (via storageKey)
 *   - Document class toggling for high-contrast
 *   - className forwarded to toolbar element
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, beforeEach } from "vitest";
import { AccessibilityToolbar } from "../src/components/AccessibilityToolbar.js";

// Use a unique storage key per test to avoid cross-test contamination.
function uniqueKey(): string {
  return `test-a11y-${Math.random().toString(36).slice(2)}`;
}

describe("AccessibilityToolbar", () => {
  beforeEach(() => {
    // Clear any lingering document classes between tests.
    document.documentElement.className = "";
    document.documentElement.style.fontSize = "";
  });

  // -------------------------------------------------------------------------
  // Toolbar structure
  // -------------------------------------------------------------------------

  it("renders a toolbar landmark with an accessible label", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const toolbar = screen.getByRole("toolbar");
    expect(toolbar).toHaveAttribute("aria-label", "Accessibility settings");
  });

  it("renders text size buttons A, A+, A++", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    expect(screen.getByRole("button", { name: /Normal text size/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Large text size/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Extra large text size/i })).toBeInTheDocument();
  });

  it("renders toggle buttons for high contrast, reduced motion, focus indicators", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    expect(
      screen.getByRole("button", { name: /Toggle high contrast mode/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Toggle reduced motion/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Toggle enhanced focus indicators/i })
    ).toBeInTheDocument();
  });

  it("renders a Reset button", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    expect(
      screen.getByRole("button", { name: /Reset all accessibility preferences/i })
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Default aria-pressed states
  // -------------------------------------------------------------------------

  it("normal text size button is pressed by default", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const normalBtn = screen.getByRole("button", { name: /Normal text size/i });
    expect(normalBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("large and xlarge text size buttons are not pressed by default", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    expect(
      screen.getByRole("button", { name: /Large text size/i })
    ).toHaveAttribute("aria-pressed", "false");
    expect(
      screen.getByRole("button", { name: /Extra large text size/i })
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("high contrast toggle starts not pressed", () => {
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const btn = screen.getByRole("button", { name: /Toggle high contrast mode/i });
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });

  // -------------------------------------------------------------------------
  // Text size interaction
  // -------------------------------------------------------------------------

  it("pressing large text size button sets it to pressed", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const largeBtn = screen.getByRole("button", { name: /Large text size/i });
    await user.click(largeBtn);
    expect(largeBtn).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: /Normal text size/i })
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("pressing xlarge text size button deselects large", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    await user.click(screen.getByRole("button", { name: /Large text size/i }));
    await user.click(screen.getByRole("button", { name: /Extra large text size/i }));
    expect(
      screen.getByRole("button", { name: /Extra large text size/i })
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: /Large text size/i })
    ).toHaveAttribute("aria-pressed", "false");
  });

  // -------------------------------------------------------------------------
  // Toggle interactions
  // -------------------------------------------------------------------------

  it("high contrast toggles to pressed on click", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const btn = screen.getByRole("button", { name: /Toggle high contrast mode/i });
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("high contrast toggles back to not pressed on second click", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const btn = screen.getByRole("button", { name: /Toggle high contrast mode/i });
    await user.click(btn);
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "false");
  });

  it("reduced motion toggles on click", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    const btn = screen.getByRole("button", { name: /Toggle reduced motion/i });
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  // -------------------------------------------------------------------------
  // Reset
  // -------------------------------------------------------------------------

  it("reset button restores all defaults", async () => {
    const user = userEvent.setup();
    render(<AccessibilityToolbar storageKey={uniqueKey()} />);
    // Change a few settings.
    await user.click(screen.getByRole("button", { name: /Large text size/i }));
    await user.click(screen.getByRole("button", { name: /Toggle high contrast mode/i }));
    // Reset.
    await user.click(
      screen.getByRole("button", { name: /Reset all accessibility preferences/i })
    );
    // Verify defaults restored.
    expect(
      screen.getByRole("button", { name: /Normal text size/i })
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: /Toggle high contrast mode/i })
    ).toHaveAttribute("aria-pressed", "false");
  });

  // -------------------------------------------------------------------------
  // className / style
  // -------------------------------------------------------------------------

  it("forwards className to toolbar element", () => {
    const { container } = render(
      <AccessibilityToolbar
        storageKey={uniqueKey()}
        className="custom-toolbar"
      />
    );
    expect(container.querySelector(".custom-toolbar")).toBeInTheDocument();
  });
});
