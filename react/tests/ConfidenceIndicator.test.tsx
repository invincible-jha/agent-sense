/**
 * Tests for ConfidenceIndicator component.
 *
 * Covers:
 *   - Correct colour per confidence level (high/medium/low)
 *   - Score percentage rendered for medium and low
 *   - ARIA role="status", aria-live="polite"
 *   - Progressbar aria attributes
 *   - Size variants affect DOM structure
 *   - Score clamping at 0 and 1
 *   - High-contrast colour variant
 *   - Optional label prop
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceIndicator } from "../src/components/ConfidenceIndicator.js";
import {
  CONFIDENCE_COLOURS,
  CONFIDENCE_COLOURS_HIGH_CONTRAST,
} from "../src/utils/color.js";

describe("ConfidenceIndicator", () => {
  // -------------------------------------------------------------------------
  // ARIA attributes
  // -------------------------------------------------------------------------

  it("renders a status region with aria-live=polite", () => {
    render(<ConfidenceIndicator score={0.8} />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("renders a progressbar with correct aria-valuenow", () => {
    render(<ConfidenceIndicator score={0.75} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "75");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("sets aria-label on the status region describing the level", () => {
    render(<ConfidenceIndicator score={0.85} />);
    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-label")).toMatch(/highly confident/i);
  });

  it("includes score percentage in progressbar aria-label", () => {
    render(<ConfidenceIndicator score={0.6} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-label")).toMatch(/60%/);
  });

  // -------------------------------------------------------------------------
  // Colour mapping
  // -------------------------------------------------------------------------

  it("uses green colour for high confidence score (>=0.7)", () => {
    const { container } = render(<ConfidenceIndicator score={0.9} />);
    // The fill div has the background colour.
    const fill = container.querySelector("[style*='background-color']");
    expect(fill).not.toBeNull();
    // At least one element should carry the high colour.
    const allElements = container.querySelectorAll("[style]");
    const hasHighColour = Array.from(allElements).some((el) =>
      (el as HTMLElement).style.backgroundColor === CONFIDENCE_COLOURS.high ||
      (el as HTMLElement).getAttribute("style")?.includes(CONFIDENCE_COLOURS.high)
    );
    expect(hasHighColour).toBe(true);
  });

  it("uses amber colour for medium confidence score (>=0.4 and <0.7)", () => {
    const { container } = render(<ConfidenceIndicator score={0.55} />);
    const allElements = container.querySelectorAll("[style]");
    const hasMediumColour = Array.from(allElements).some((el) =>
      (el as HTMLElement).getAttribute("style")?.includes(CONFIDENCE_COLOURS.medium)
    );
    expect(hasMediumColour).toBe(true);
  });

  it("uses red colour for low confidence score (<0.4)", () => {
    const { container } = render(<ConfidenceIndicator score={0.2} />);
    const allElements = container.querySelectorAll("[style]");
    const hasLowColour = Array.from(allElements).some((el) =>
      (el as HTMLElement).getAttribute("style")?.includes(CONFIDENCE_COLOURS.low)
    );
    expect(hasLowColour).toBe(true);
  });

  it("uses high-contrast colours when highContrast=true", () => {
    const { container } = render(
      <ConfidenceIndicator score={0.9} highContrast={true} />
    );
    const allElements = container.querySelectorAll("[style]");
    const hasHCColour = Array.from(allElements).some((el) =>
      (el as HTMLElement).getAttribute("style")?.includes(
        CONFIDENCE_COLOURS_HIGH_CONTRAST.high
      )
    );
    expect(hasHCColour).toBe(true);
  });

  // -------------------------------------------------------------------------
  // Score display logic (show_score for medium/low)
  // -------------------------------------------------------------------------

  it("shows numeric score percentage for medium confidence", () => {
    render(<ConfidenceIndicator score={0.55} />);
    expect(screen.getByText("55%")).toBeInTheDocument();
  });

  it("shows numeric score percentage for low confidence", () => {
    render(<ConfidenceIndicator score={0.2} />);
    expect(screen.getByText("20%")).toBeInTheDocument();
  });

  it("does not render a numeric score span for high confidence", () => {
    render(<ConfidenceIndicator score={0.9} />);
    expect(screen.queryByText(/\d+%/)).toBeNull();
  });

  // -------------------------------------------------------------------------
  // Score edge cases
  // -------------------------------------------------------------------------

  it("clamps score above 1.0 to 100%", () => {
    render(<ConfidenceIndicator score={1.5} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "100");
  });

  it("clamps score below 0 to 0%", () => {
    render(<ConfidenceIndicator score={-0.3} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "0");
  });

  it("renders score=0.7 as high (boundary)", () => {
    render(<ConfidenceIndicator score={0.7} />);
    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-label")).toMatch(/highly confident/i);
  });

  it("renders score=0.4 as medium (boundary)", () => {
    render(<ConfidenceIndicator score={0.4} />);
    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-label")).toMatch(/moderate confidence/i);
  });

  it("renders score=0.399 as low (boundary)", () => {
    render(<ConfidenceIndicator score={0.399} />);
    const status = screen.getByRole("status");
    expect(status.getAttribute("aria-label")).toMatch(/low confidence/i);
  });

  // -------------------------------------------------------------------------
  // Props: label, size, className
  // -------------------------------------------------------------------------

  it("renders the label text when provided", () => {
    render(<ConfidenceIndicator score={0.8} label="Response quality" />);
    expect(screen.getByText("Response quality")).toBeInTheDocument();
  });

  it("does not render a label span when label prop is omitted", () => {
    render(<ConfidenceIndicator score={0.8} />);
    // The only text in dom should be the badge, not an empty label.
    expect(screen.queryByText("Response quality")).toBeNull();
  });

  it("accepts size prop without throwing", () => {
    const { rerender } = render(<ConfidenceIndicator score={0.5} size="sm" />);
    rerender(<ConfidenceIndicator score={0.5} size="lg" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("passes className to the outermost container", () => {
    const { container } = render(
      <ConfidenceIndicator score={0.7} className="my-indicator" />
    );
    expect(container.querySelector(".my-indicator")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Level badge labels
  // -------------------------------------------------------------------------

  it("shows 'High Confidence' badge for high score", () => {
    render(<ConfidenceIndicator score={0.85} />);
    expect(screen.getByText("High Confidence")).toBeInTheDocument();
  });

  it("shows 'Medium Confidence' badge for medium score", () => {
    render(<ConfidenceIndicator score={0.5} />);
    expect(screen.getByText("Medium Confidence")).toBeInTheDocument();
  });

  it("shows 'Low Confidence' badge for low score", () => {
    render(<ConfidenceIndicator score={0.1} />);
    expect(screen.getByText("Low Confidence")).toBeInTheDocument();
  });
});
