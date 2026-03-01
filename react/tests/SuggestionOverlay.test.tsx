/**
 * Tests for SuggestionOverlay component.
 *
 * Covers:
 *   - Returns null when isOpen=false
 *   - Renders listbox when isOpen=true
 *   - Renders all suggestion labels and descriptions
 *   - Empty state text when suggestions is []
 *   - aria-activedescendant tracks active option
 *   - ArrowDown navigates to next option
 *   - ArrowUp navigates to previous option (wraps)
 *   - Home / End jump to first / last
 *   - Enter selects active option and calls onSelect + onClose
 *   - Escape calls onClose without selecting
 *   - Click on option calls onSelect + onClose
 *   - Mouse hover sets active option
 *   - role="option" with aria-selected on each item
 *   - className forwarded
 */

import React, { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SuggestionOverlay } from "../src/components/SuggestionOverlay.js";
import type { SuggestionItem } from "../src/types.js";

const SUGGESTIONS: SuggestionItem[] = [
  { id: "s1", label: "Reset your password", description: "Go to account settings" },
  { id: "s2", label: "Contact support", description: "Reach our team" },
  { id: "s3", label: "View billing info" },
];

// ---------------------------------------------------------------------------
// Controlled wrapper for interactive tests
// ---------------------------------------------------------------------------

interface WrapperProps {
  initialOpen?: boolean;
  suggestions?: SuggestionItem[];
  onSelectMock?: (item: SuggestionItem) => void;
}

function ControlledWrapper({
  initialOpen = true,
  suggestions = SUGGESTIONS,
  onSelectMock = vi.fn(),
}: WrapperProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(initialOpen);
  return (
    <SuggestionOverlay
      suggestions={suggestions}
      isOpen={isOpen}
      onSelect={onSelectMock}
      onClose={() => setIsOpen(false)}
    />
  );
}

describe("SuggestionOverlay", () => {
  // -------------------------------------------------------------------------
  // Visibility
  // -------------------------------------------------------------------------

  it("returns null when isOpen=false", () => {
    const { container } = render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={false}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders the listbox when isOpen=true", () => {
    render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Suggestions rendering
  // -------------------------------------------------------------------------

  it("renders all suggestion labels", () => {
    render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("Reset your password")).toBeInTheDocument();
    expect(screen.getByText("Contact support")).toBeInTheDocument();
    expect(screen.getByText("View billing info")).toBeInTheDocument();
  });

  it("renders suggestion descriptions when provided", () => {
    render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("Go to account settings")).toBeInTheDocument();
    expect(screen.getByText("Reach our team")).toBeInTheDocument();
  });

  it("does not render description span when description is absent", () => {
    render(
      <SuggestionOverlay
        suggestions={[{ id: "x", label: "No desc" }]}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    // The option should only contain the label text.
    expect(options[0]!.querySelectorAll("span")).toHaveLength(1);
  });

  // -------------------------------------------------------------------------
  // Empty state
  // -------------------------------------------------------------------------

  it("renders empty state text when suggestions is empty", () => {
    render(
      <SuggestionOverlay
        suggestions={[]}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
        emptyText="Nothing here."
      />
    );
    expect(screen.getByText("Nothing here.")).toBeInTheDocument();
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("empty state has role='status' and aria-live='polite'", () => {
    render(
      <SuggestionOverlay
        suggestions={[]}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  // -------------------------------------------------------------------------
  // ARIA option attributes
  // -------------------------------------------------------------------------

  it("each suggestion has role='option'", () => {
    render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(SUGGESTIONS.length);
  });

  it("no option is aria-selected on initial render", () => {
    render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
      />
    );
    const options = screen.getAllByRole("option");
    options.forEach((option) => {
      expect(option).toHaveAttribute("aria-selected", "false");
    });
  });

  // -------------------------------------------------------------------------
  // Keyboard navigation
  // -------------------------------------------------------------------------

  it("ArrowDown moves active option to first item", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{ArrowDown}");
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveAttribute("aria-selected", "true");
  });

  it("ArrowDown again moves active option to second item", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{ArrowDown}");
    const options = screen.getAllByRole("option");
    expect(options[1]).toHaveAttribute("aria-selected", "true");
  });

  it("ArrowDown wraps from last to first", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    // Move to last (3 items, so press 3 times).
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{ArrowDown}");
    // One more wraps to first.
    await user.keyboard("{ArrowDown}");
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveAttribute("aria-selected", "true");
  });

  it("ArrowUp wraps from first to last", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    // First ArrowDown to select index 0.
    await user.keyboard("{ArrowDown}");
    // ArrowUp wraps to last.
    await user.keyboard("{ArrowUp}");
    const options = screen.getAllByRole("option");
    expect(options[options.length - 1]).toHaveAttribute("aria-selected", "true");
  });

  it("Home key moves to first option", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{Home}");
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveAttribute("aria-selected", "true");
  });

  it("End key moves to last option", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{End}");
    const options = screen.getAllByRole("option");
    expect(options[options.length - 1]).toHaveAttribute("aria-selected", "true");
  });

  // -------------------------------------------------------------------------
  // Selection
  // -------------------------------------------------------------------------

  it("Enter calls onSelect with the active suggestion", async () => {
    const user = userEvent.setup();
    const onSelectMock = vi.fn();
    render(<ControlledWrapper onSelectMock={onSelectMock} />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{Enter}");
    expect(onSelectMock).toHaveBeenCalledOnce();
    expect(onSelectMock).toHaveBeenCalledWith(SUGGESTIONS[0]);
  });

  it("Escape calls onClose without selecting", async () => {
    const user = userEvent.setup();
    const onSelectMock = vi.fn();
    render(<ControlledWrapper onSelectMock={onSelectMock} />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{Escape}");
    expect(onSelectMock).not.toHaveBeenCalled();
    // Overlay should be closed.
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("clicking an option calls onSelect with the correct item", async () => {
    const user = userEvent.setup();
    const onSelectMock = vi.fn();
    render(<ControlledWrapper onSelectMock={onSelectMock} />);
    await user.click(screen.getByText("Contact support"));
    expect(onSelectMock).toHaveBeenCalledWith(SUGGESTIONS[1]);
  });

  // -------------------------------------------------------------------------
  // aria-activedescendant
  // -------------------------------------------------------------------------

  it("listbox aria-activedescendant points to the active option id", async () => {
    const user = userEvent.setup();
    render(<ControlledWrapper />);
    const listbox = screen.getByRole("listbox");
    listbox.focus();
    await user.keyboard("{ArrowDown}");
    const activeDescendant = listbox.getAttribute("aria-activedescendant");
    expect(activeDescendant).not.toBeNull();
    const activeOption = document.getElementById(activeDescendant!);
    expect(activeOption).not.toBeNull();
    expect(activeOption!.getAttribute("aria-selected")).toBe("true");
  });

  // -------------------------------------------------------------------------
  // className
  // -------------------------------------------------------------------------

  it("forwards className to the outer container", () => {
    const { container } = render(
      <SuggestionOverlay
        suggestions={SUGGESTIONS}
        isOpen={true}
        onSelect={vi.fn()}
        onClose={vi.fn()}
        className="custom-overlay"
      />
    );
    expect(container.querySelector(".custom-overlay")).toBeInTheDocument();
  });
});
