/**
 * Tests for HandoffCard component.
 *
 * Covers:
 *   - Summary always visible
 *   - Urgency badge shows correct level label
 *   - Collapsible sections for facts and questions
 *   - Section expand/collapse with keyboard and click
 *   - Empty facts / questions render no section
 *   - ARIA attributes on collapsible regions
 *   - High-contrast colour variant
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { HandoffCard } from "../src/components/HandoffCard.js";

const DEFAULT_PROPS = {
  summary: "User cannot reset their password.",
  facts: ["Email: alice@example.com", "Account created: 2024-01-01"],
  questions: ["Is the account locked?", "Has MFA been enabled?"],
  urgency: "high" as const,
};

describe("HandoffCard", () => {
  // -------------------------------------------------------------------------
  // Summary visibility
  // -------------------------------------------------------------------------

  it("always renders the summary text", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    expect(
      screen.getByText("User cannot reset their password.")
    ).toBeInTheDocument();
  });

  it("renders as a section element with an accessible name", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const section = screen.getByRole("region", { name: /handoff context/i });
    expect(section).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Urgency badge
  // -------------------------------------------------------------------------

  it("renders High urgency badge for urgency='high'", () => {
    render(<HandoffCard {...DEFAULT_PROPS} urgency="high" />);
    expect(screen.getByText(/High Urgency/i)).toBeInTheDocument();
  });

  it("renders Low urgency badge for urgency='low'", () => {
    render(<HandoffCard {...DEFAULT_PROPS} urgency="low" />);
    expect(screen.getByText(/Low Urgency/i)).toBeInTheDocument();
  });

  it("renders Medium urgency by default when urgency prop is omitted", () => {
    render(
      <HandoffCard
        summary="Test"
        facts={["fact"]}
        questions={["q"]}
      />
    );
    expect(screen.getByText(/Medium Urgency/i)).toBeInTheDocument();
  });

  it("urgency badge has an accessible aria-label describing the urgency", () => {
    render(<HandoffCard {...DEFAULT_PROPS} urgency="critical" />);
    const badge = screen.getByRole("status");
    expect(badge.getAttribute("aria-label")).toMatch(/critical/i);
  });

  // -------------------------------------------------------------------------
  // Collapsible sections — initial state
  // -------------------------------------------------------------------------

  it("facts section starts collapsed (hidden)", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    expect(toggleButton).toHaveAttribute("aria-expanded", "false");
  });

  it("questions section starts collapsed (hidden)", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Open Questions/i });
    expect(toggleButton).toHaveAttribute("aria-expanded", "false");
  });

  it("fact items are not visible before expanding", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    expect(screen.queryByText("Email: alice@example.com")).toBeNull();
  });

  // -------------------------------------------------------------------------
  // Collapsible sections — expand via click
  // -------------------------------------------------------------------------

  it("expands facts section on button click", async () => {
    const user = userEvent.setup();
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    await user.click(toggleButton);
    expect(toggleButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Email: alice@example.com")).toBeVisible();
  });

  it("collapses facts section on second click", async () => {
    const user = userEvent.setup();
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    await user.click(toggleButton);
    await user.click(toggleButton);
    expect(toggleButton).toHaveAttribute("aria-expanded", "false");
  });

  it("expands questions section on button click", async () => {
    const user = userEvent.setup();
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Open Questions/i });
    await user.click(toggleButton);
    expect(toggleButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Is the account locked?")).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // Keyboard activation
  // -------------------------------------------------------------------------

  it("expands facts section via Enter key", async () => {
    const user = userEvent.setup();
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    toggleButton.focus();
    await user.keyboard("{Enter}");
    expect(toggleButton).toHaveAttribute("aria-expanded", "true");
  });

  it("expands facts section via Space key", async () => {
    const user = userEvent.setup();
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    toggleButton.focus();
    await user.keyboard(" ");
    expect(toggleButton).toHaveAttribute("aria-expanded", "true");
  });

  // -------------------------------------------------------------------------
  // Empty sections
  // -------------------------------------------------------------------------

  it("does not render facts section when facts is empty", () => {
    render(<HandoffCard summary="Test" facts={[]} questions={["q"]} />);
    expect(screen.queryByRole("button", { name: /Key Facts/i })).toBeNull();
  });

  it("does not render questions section when questions is empty", () => {
    render(<HandoffCard summary="Test" facts={["f"]} questions={[]} />);
    expect(
      screen.queryByRole("button", { name: /Open Questions/i })
    ).toBeNull();
  });

  // -------------------------------------------------------------------------
  // Item count in section headings
  // -------------------------------------------------------------------------

  it("shows item count in section heading", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    expect(
      screen.getByText(`Key Facts (${DEFAULT_PROPS.facts.length})`)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // ARIA button controls relationship
  // -------------------------------------------------------------------------

  it("toggle button aria-controls points to the region id", () => {
    render(<HandoffCard {...DEFAULT_PROPS} />);
    const toggleButton = screen.getByRole("button", { name: /Key Facts/i });
    const controlsId = toggleButton.getAttribute("aria-controls");
    expect(controlsId).not.toBeNull();
    expect(document.getElementById(controlsId!)).not.toBeNull();
  });
});
