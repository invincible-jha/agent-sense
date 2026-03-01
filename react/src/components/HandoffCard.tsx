/**
 * HandoffCard — renders an agent-to-human handoff context bundle.
 *
 * Implements progressive disclosure: the summary is always visible;
 * facts, unresolved questions, and attempted actions are collapsible.
 * Urgency is shown as a coloured badge.
 *
 * Mirrors Python HandoffPackage data contract from:
 *   agent_sense.handoff.packager (HandoffPackage)
 *
 * ARIA: section landmark, expandable regions use aria-expanded.
 *
 * Usage:
 *   <HandoffCard
 *     summary="User cannot reset their password."
 *     facts={["Email: alice@example.com"]}
 *     questions={["Is the account locked?"]}
 *     urgency="high"
 *   />
 */

import React, { useCallback, useState } from "react";
import type { UrgencyLevel } from "../types.js";
import { getUrgencyAriaLabel } from "../utils/a11y.js";
import { getUrgencyColour } from "../utils/color.js";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface HandoffCardProps {
  /** Brief summary of the user's unresolved need. */
  summary: string;
  /** Important facts established during the AI conversation. */
  facts?: readonly string[];
  /** Open questions the human agent should address. */
  questions?: readonly string[];
  /** Urgency level of this handoff. Defaults to "medium". */
  urgency?: UrgencyLevel;
  /** Whether to render in high-contrast mode. */
  highContrast?: boolean;
  /** Optional className for the card container. */
  className?: string;
  /** Optional additional styles for the card container. */
  style?: React.CSSProperties;
}

// ---------------------------------------------------------------------------
// Internal section component
// ---------------------------------------------------------------------------

interface CollapsibleSectionProps {
  title: string;
  items: readonly string[];
  id: string;
}

function CollapsibleSection({
  title,
  items,
  id,
}: CollapsibleSectionProps): React.ReactElement | null {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = useCallback(() => {
    setIsExpanded((previous) => !previous);
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLButtonElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setIsExpanded((previous) => !previous);
      }
    },
    []
  );

  if (items.length === 0) return null;

  const headingId = `${id}-heading`;
  const regionId = `${id}-region`;

  const buttonStyles: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
    background: "none",
    border: "none",
    borderTop: "1px solid #e0e0e0",
    padding: "10px 0",
    cursor: "pointer",
    fontSize: "0.875rem",
    fontWeight: 600,
    textAlign: "left",
    color: "inherit",
  };

  const chevronStyles: React.CSSProperties = {
    display: "inline-block",
    transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
    transition: "transform 0.2s ease",
    fontSize: "0.75rem",
    lineHeight: 1,
  };

  const listStyles: React.CSSProperties = {
    margin: 0,
    paddingLeft: "1.25rem",
    paddingTop: "4px",
    paddingBottom: "8px",
  };

  const itemStyles: React.CSSProperties = {
    fontSize: "0.875rem",
    lineHeight: 1.5,
    marginBottom: "4px",
    color: "#333",
  };

  return (
    <div>
      <button
        type="button"
        id={headingId}
        aria-expanded={isExpanded}
        aria-controls={regionId}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        style={buttonStyles}
      >
        <span>
          {title} ({items.length})
        </span>
        <span aria-hidden="true" style={chevronStyles}>
          ▼
        </span>
      </button>

      <div
        id={regionId}
        role="region"
        aria-labelledby={headingId}
        hidden={!isExpanded}
      >
        <ul style={listStyles} aria-label={title}>
          {items.map((item, index) => (
            <li key={index} style={itemStyles}>
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// HandoffCard component
// ---------------------------------------------------------------------------

const URGENCY_LABELS: Record<UrgencyLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

/**
 * Renders a structured handoff context card with progressive disclosure.
 *
 * The summary is always visible. Facts and questions are in collapsible
 * sections labelled with item counts so agents can triage quickly.
 */
export function HandoffCard({
  summary,
  facts = [],
  questions = [],
  urgency = "medium",
  highContrast = false,
  className,
  style,
}: HandoffCardProps): React.ReactElement {
  // useId must be called unconditionally at component top level.
  const cardId = React.useId();
  const urgencyColour = getUrgencyColour(urgency, highContrast);
  const urgencyAriaLabel = getUrgencyAriaLabel(urgency);

  const cardStyles: React.CSSProperties = {
    border: "1px solid #e0e0e0",
    borderRadius: "8px",
    padding: "16px",
    backgroundColor: "#fff",
    fontFamily: "system-ui, sans-serif",
    ...style,
  };

  const headerStyles: React.CSSProperties = {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "12px",
    marginBottom: "12px",
  };

  const titleStyles: React.CSSProperties = {
    fontSize: "0.75rem",
    fontWeight: 700,
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    color: "#888",
    marginBottom: "4px",
  };

  const summaryStyles: React.CSSProperties = {
    fontSize: "0.9375rem",
    lineHeight: 1.5,
    color: "#1a1a1a",
    margin: 0,
  };

  const badgeStyles: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "2px 10px",
    borderRadius: "9999px",
    backgroundColor: urgencyColour,
    color: "#ffffff",
    fontSize: "0.75rem",
    fontWeight: 700,
    whiteSpace: "nowrap",
    flexShrink: 0,
  };

  return (
    <section
      aria-label="Agent handoff context"
      style={cardStyles}
      className={className}
    >
      <div style={headerStyles}>
        <div>
          <div style={titleStyles} aria-hidden="true">
            Handoff Summary
          </div>
          <p style={summaryStyles}>{summary}</p>
        </div>

        <span
          style={badgeStyles}
          role="status"
          aria-label={urgencyAriaLabel}
        >
          <span aria-hidden="true">!</span>
          {URGENCY_LABELS[urgency]} Urgency
        </span>
      </div>

      <CollapsibleSection
        title="Key Facts"
        items={facts}
        id={`${cardId}-facts`}
      />

      <CollapsibleSection
        title="Open Questions"
        items={questions}
        id={`${cardId}-questions`}
      />
    </section>
  );
}
