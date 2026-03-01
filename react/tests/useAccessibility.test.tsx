/**
 * Tests for useAccessibility hook.
 *
 * Covers:
 *   - Returns DEFAULT_ACCESSIBILITY_PREFERENCES on first render
 *   - setTextSize updates textSize preference
 *   - setHighContrast updates highContrast preference
 *   - setReducedMotion updates reducedMotion preference
 *   - setFocusIndicators updates focusIndicators preference
 *   - resetPreferences restores all defaults
 *   - Persists to localStorage on change
 *   - Reads initial state from localStorage when available
 *   - Merges partial localStorage data with defaults (forward-compat)
 *   - Applies document CSS classes when highContrast changes
 *   - Updates document font-size when textSize changes
 */

import React, { type ReactNode } from "react";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { useAccessibility } from "../src/hooks/useAccessibility.js";
import { DEFAULT_ACCESSIBILITY_PREFERENCES } from "../src/types.js";

// ---------------------------------------------------------------------------
// Test harness — renders a component that exercises the hook
// ---------------------------------------------------------------------------

interface HarnessProps {
  storageKey?: string;
}

function Harness({ storageKey }: HarnessProps): ReactNode {
  const {
    preferences,
    setTextSize,
    setHighContrast,
    setReducedMotion,
    setFocusIndicators,
    resetPreferences,
  } = useAccessibility(storageKey);

  return (
    <div>
      <span data-testid="textSize">{preferences.textSize}</span>
      <span data-testid="highContrast">{String(preferences.highContrast)}</span>
      <span data-testid="reducedMotion">{String(preferences.reducedMotion)}</span>
      <span data-testid="focusIndicators">{String(preferences.focusIndicators)}</span>

      <button onClick={() => setTextSize("large")}>Set Large</button>
      <button onClick={() => setTextSize("xlarge")}>Set XLarge</button>
      <button onClick={() => setTextSize("normal")}>Set Normal</button>
      <button onClick={() => setHighContrast(true)}>HC On</button>
      <button onClick={() => setHighContrast(false)}>HC Off</button>
      <button onClick={() => setReducedMotion(true)}>RM On</button>
      <button onClick={() => setFocusIndicators(true)}>FI On</button>
      <button onClick={resetPreferences}>Reset</button>
    </div>
  );
}

describe("useAccessibility", () => {
  const UNIQUE_KEY = "test-hook-a11y";

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.style.fontSize = "";
  });

  // -------------------------------------------------------------------------
  // Default values
  // -------------------------------------------------------------------------

  it("starts with default textSize='normal'", () => {
    render(<Harness storageKey={UNIQUE_KEY} />);
    expect(screen.getByTestId("textSize").textContent).toBe(
      DEFAULT_ACCESSIBILITY_PREFERENCES.textSize
    );
  });

  it("starts with highContrast=false", () => {
    render(<Harness storageKey={UNIQUE_KEY} />);
    expect(screen.getByTestId("highContrast").textContent).toBe("false");
  });

  it("starts with reducedMotion=false", () => {
    render(<Harness storageKey={UNIQUE_KEY} />);
    expect(screen.getByTestId("reducedMotion").textContent).toBe("false");
  });

  it("starts with focusIndicators=false", () => {
    render(<Harness storageKey={UNIQUE_KEY} />);
    expect(screen.getByTestId("focusIndicators").textContent).toBe("false");
  });

  // -------------------------------------------------------------------------
  // Setters
  // -------------------------------------------------------------------------

  it("setTextSize updates textSize to 'large'", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("Set Large"));
    expect(screen.getByTestId("textSize").textContent).toBe("large");
  });

  it("setTextSize updates textSize to 'xlarge'", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("Set XLarge"));
    expect(screen.getByTestId("textSize").textContent).toBe("xlarge");
  });

  it("setHighContrast(true) updates highContrast", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("HC On"));
    expect(screen.getByTestId("highContrast").textContent).toBe("true");
  });

  it("setHighContrast(false) turns off highContrast", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("HC On"));
    await user.click(screen.getByText("HC Off"));
    expect(screen.getByTestId("highContrast").textContent).toBe("false");
  });

  it("setReducedMotion(true) updates reducedMotion", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("RM On"));
    expect(screen.getByTestId("reducedMotion").textContent).toBe("true");
  });

  it("setFocusIndicators(true) updates focusIndicators", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("FI On"));
    expect(screen.getByTestId("focusIndicators").textContent).toBe("true");
  });

  // -------------------------------------------------------------------------
  // Reset
  // -------------------------------------------------------------------------

  it("resetPreferences restores all defaults", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("Set Large"));
    await user.click(screen.getByText("HC On"));
    await user.click(screen.getByText("Reset"));
    expect(screen.getByTestId("textSize").textContent).toBe("normal");
    expect(screen.getByTestId("highContrast").textContent).toBe("false");
  });

  // -------------------------------------------------------------------------
  // localStorage persistence
  // -------------------------------------------------------------------------

  it("saves preferences to localStorage after change", async () => {
    const user = userEvent.setup();
    const storageKey = "test-persist";
    render(<Harness storageKey={storageKey} />);
    await user.click(screen.getByText("Set Large"));
    const stored = JSON.parse(localStorage.getItem(storageKey) ?? "{}");
    expect(stored.textSize).toBe("large");
  });

  it("reads textSize from localStorage on mount", () => {
    const storageKey = "test-read";
    localStorage.setItem(
      storageKey,
      JSON.stringify({ textSize: "xlarge", highContrast: false, reducedMotion: false, focusIndicators: false })
    );
    render(<Harness storageKey={storageKey} />);
    expect(screen.getByTestId("textSize").textContent).toBe("xlarge");
  });

  it("merges partial localStorage data with defaults", () => {
    const storageKey = "test-merge";
    // Only set highContrast; other keys should default.
    localStorage.setItem(storageKey, JSON.stringify({ highContrast: true }));
    render(<Harness storageKey={storageKey} />);
    expect(screen.getByTestId("highContrast").textContent).toBe("true");
    expect(screen.getByTestId("textSize").textContent).toBe("normal");
  });

  // -------------------------------------------------------------------------
  // Document class synchronisation
  // -------------------------------------------------------------------------

  it("adds a11y-high-contrast class to documentElement when highContrast=true", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("HC On"));
    expect(document.documentElement.classList.contains("a11y-high-contrast")).toBe(
      true
    );
  });

  it("removes a11y-high-contrast class when highContrast=false", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("HC On"));
    await user.click(screen.getByText("HC Off"));
    expect(document.documentElement.classList.contains("a11y-high-contrast")).toBe(
      false
    );
  });

  it("updates document font-size when textSize changes", async () => {
    const user = userEvent.setup();
    render(<Harness storageKey={UNIQUE_KEY} />);
    await user.click(screen.getByText("Set Large"));
    // 1.25rem corresponds to 'large' in TEXT_SIZE_MAP.
    expect(document.documentElement.style.fontSize).toBe("1.25rem");
  });
});
