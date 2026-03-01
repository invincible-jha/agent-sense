/**
 * DisclosureWrapper — wraps AI-generated content with a transparency badge.
 *
 * Implements WCAG 2.1 AA transparency requirements for AI content as specified
 * in the Python AIDisclosureCard model (agent_sense.indicators.disclosure).
 *
 * The badge is always visible so users know they are reading AI output.
 * Badge position is configurable (top | bottom).
 *
 * ARIA: The wrapper region is labelled; the badge has role="note".
 *
 * Usage:
 *   <DisclosureWrapper badgeText="AI Generated" position="top">
 *     <p>AI response content here.</p>
 *   </DisclosureWrapper>
 */

import React from "react";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface DisclosureWrapperProps {
  /** The AI-generated content to wrap. */
  children: React.ReactNode;
  /** Text displayed in the disclosure badge. Defaults to "AI Generated". */
  badgeText?: string;
  /** Badge placement relative to children. Defaults to "top". */
  position?: "top" | "bottom";
  /** Whether to render in high-contrast mode. */
  highContrast?: boolean;
  /** Optional className for the outer wrapper div. */
  className?: string;
  /** Optional additional styles for the outer wrapper. */
  style?: React.CSSProperties;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Wraps children in a disclosure region with an "AI Generated" badge.
 *
 * The badge uses role="note" and an informative aria-label so screen readers
 * announce the AI-generated nature of the content before (or after) reading it.
 */
export function DisclosureWrapper({
  children,
  badgeText = "AI Generated",
  position = "top",
  highContrast = false,
  className,
  style,
}: DisclosureWrapperProps): React.ReactElement {
  const wrapperStyles: React.CSSProperties = {
    position: "relative",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    ...style,
  };

  const badgeContainerStyles: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
  };

  // Badge colours: use a neutral purple-tinted brand colour with enough
  // contrast against white (#6c4bb0 gives approx 5.2:1 — AA compliant).
  const badgeBackgroundColour = highContrast ? "#3a1a70" : "#6c4bb0";

  const badgeStyles: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    padding: "2px 10px",
    borderRadius: "9999px",
    backgroundColor: badgeBackgroundColour,
    color: "#ffffff",
    fontSize: "0.75rem",
    fontWeight: 600,
    letterSpacing: "0.02em",
    userSelect: "none",
  };

  const iconStyles: React.CSSProperties = {
    fontSize: "0.7rem",
    lineHeight: 1,
  };

  const badge = (
    <div style={badgeContainerStyles}>
      <span
        role="note"
        aria-label={`This content was ${badgeText.toLowerCase()}`}
        style={badgeStyles}
      >
        <span aria-hidden="true" style={iconStyles}>
          ✦
        </span>
        {badgeText}
      </span>
    </div>
  );

  return (
    <div
      style={wrapperStyles}
      className={className}
      aria-label="AI-generated content"
    >
      {position === "top" && badge}
      <div>{children}</div>
      {position === "bottom" && badge}
    </div>
  );
}
