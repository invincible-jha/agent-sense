/**
 * Tests for DisclosureWrapper component.
 *
 * Covers:
 *   - Children render inside wrapper
 *   - Default badge text "AI Generated"
 *   - Custom badgeText prop
 *   - Badge position: top (default) renders before children
 *   - Badge position: bottom renders after children
 *   - ARIA role="note" on badge
 *   - aria-label on badge includes badgeText
 *   - High-contrast background colour change
 *   - className prop forwarded to outer div
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DisclosureWrapper } from "../src/components/DisclosureWrapper.js";

describe("DisclosureWrapper", () => {
  // -------------------------------------------------------------------------
  // Children
  // -------------------------------------------------------------------------

  it("renders children inside the wrapper", () => {
    render(
      <DisclosureWrapper>
        <p>AI response content here.</p>
      </DisclosureWrapper>
    );
    expect(screen.getByText("AI response content here.")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Badge text
  // -------------------------------------------------------------------------

  it("renders default badge text 'AI Generated'", () => {
    render(<DisclosureWrapper><p>content</p></DisclosureWrapper>);
    expect(screen.getByText("AI Generated")).toBeInTheDocument();
  });

  it("renders custom badgeText when provided", () => {
    render(
      <DisclosureWrapper badgeText="AI Summary">
        <p>content</p>
      </DisclosureWrapper>
    );
    expect(screen.getByText("AI Summary")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // ARIA
  // -------------------------------------------------------------------------

  it("badge has role='note'", () => {
    render(<DisclosureWrapper><p>content</p></DisclosureWrapper>);
    const note = screen.getByRole("note");
    expect(note).toBeInTheDocument();
  });

  it("badge aria-label contains the badge text in lowercase", () => {
    render(
      <DisclosureWrapper badgeText="AI Generated">
        <p>content</p>
      </DisclosureWrapper>
    );
    const note = screen.getByRole("note");
    expect(note.getAttribute("aria-label")).toMatch(/ai generated/i);
  });

  it("outer wrapper has an accessible label identifying AI-generated content", () => {
    render(<DisclosureWrapper><p>content</p></DisclosureWrapper>);
    const wrapper = screen.getByLabelText(/ai-generated content/i);
    expect(wrapper).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Position
  // -------------------------------------------------------------------------

  it("badge appears before children when position='top' (default)", () => {
    const { container } = render(
      <DisclosureWrapper position="top">
        <p data-testid="child">content</p>
      </DisclosureWrapper>
    );
    const outerDiv = container.firstChild as HTMLElement;
    const childElements = Array.from(outerDiv.children);
    const badgeContainerIndex = childElements.findIndex((el) =>
      el.querySelector("[role='note']") !== null
    );
    const contentIndex = childElements.findIndex((el) =>
      el.querySelector("[data-testid='child']") !== null
    );
    expect(badgeContainerIndex).toBeLessThan(contentIndex);
  });

  it("badge appears after children when position='bottom'", () => {
    const { container } = render(
      <DisclosureWrapper position="bottom">
        <p data-testid="child">content</p>
      </DisclosureWrapper>
    );
    const outerDiv = container.firstChild as HTMLElement;
    const childElements = Array.from(outerDiv.children);
    const badgeContainerIndex = childElements.findIndex((el) =>
      el.querySelector("[role='note']") !== null
    );
    const contentIndex = childElements.findIndex((el) =>
      el.querySelector("[data-testid='child']") !== null
    );
    expect(badgeContainerIndex).toBeGreaterThan(contentIndex);
  });

  // -------------------------------------------------------------------------
  // High contrast
  // -------------------------------------------------------------------------

  it("applies darker background in high-contrast mode", () => {
    const { container: hcContainer } = render(
      <DisclosureWrapper highContrast={true}><p>content</p></DisclosureWrapper>
    );
    const { container: normalContainer } = render(
      <DisclosureWrapper highContrast={false}><p>content</p></DisclosureWrapper>
    );

    const hcBadge = hcContainer.querySelector("[role='note']") as HTMLElement;
    const normalBadge = normalContainer.querySelector("[role='note']") as HTMLElement;

    // High-contrast background should differ from normal.
    expect(hcBadge.style.backgroundColor).not.toEqual(
      normalBadge.style.backgroundColor
    );
  });

  // -------------------------------------------------------------------------
  // className / style props
  // -------------------------------------------------------------------------

  it("forwards className to the outer container", () => {
    const { container } = render(
      <DisclosureWrapper className="my-wrapper">
        <p>content</p>
      </DisclosureWrapper>
    );
    expect(container.querySelector(".my-wrapper")).toBeInTheDocument();
  });

  it("merges custom style into outer container", () => {
    const { container } = render(
      <DisclosureWrapper style={{ maxWidth: "600px" }}>
        <p>content</p>
      </DisclosureWrapper>
    );
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.style.maxWidth).toBe("600px");
  });
});
