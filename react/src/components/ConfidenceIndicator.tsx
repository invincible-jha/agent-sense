/**
 * ConfidenceIndicator — visual confidence bar for AI agent responses.
 *
 * Renders a horizontal progress bar coloured by confidence level:
 *   green  >= 0.7  (high)
 *   amber  >= 0.4  (medium)
 *   red    <  0.4  (low)
 *
 * ARIA: role="status", aria-live="polite", aria-label derived from level.
 * Mirrors Python ConfidenceUIIndicator rendering metadata.
 *
 * Usage:
 *   <ConfidenceIndicator score={0.82} label="Response confidence" size="md" />
 */

import React, { useMemo } from "react";
import type { ConfidenceLevel } from "../types.js";
import { getConfidenceAriaLabel } from "../utils/a11y.js";
import { getConfidenceColour, scoreTolevel } from "../utils/color.js";

// ---------------------------------------------------------------------------
// Size constants
// ---------------------------------------------------------------------------

interface SizeTokens {
  height: string;
  fontSize: string;
  gap: string;
}

const SIZE_MAP: Record<"sm" | "md" | "lg", SizeTokens> = {
  sm: { height: "4px", fontSize: "0.75rem", gap: "4px" },
  md: { height: "8px", fontSize: "0.875rem", gap: "6px" },
  lg: { height: "12px", fontSize: "1rem", gap: "8px" },
};

function getSizeTokens(size: "sm" | "md" | "lg"): SizeTokens {
  // All three keys are always present — explicit lookup is safe.
  const tokens = SIZE_MAP[size];
  return tokens;
}

// ---------------------------------------------------------------------------
// Level labels matching Python _RENDER_MAP labels
// ---------------------------------------------------------------------------

const LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  high: "High Confidence",
  medium: "Medium Confidence",
  low: "Low Confidence",
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ConfidenceIndicatorProps {
  /** Numeric confidence score in [0.0, 1.0]. */
  score: number;
  /** Optional context label shown beside the level badge. */
  label?: string;
  /** Visual size of the indicator bar. Defaults to "md". */
  size?: "sm" | "md" | "lg";
  /** Whether to render in high-contrast mode. */
  highContrast?: boolean;
  /** Optional additional styles for the outermost container. */
  style?: React.CSSProperties;
  /** Optional className for the outermost container. */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Renders an accessible confidence bar derived from a numeric score.
 *
 * The bar width is set to the score percentage. Colour maps directly to the
 * Python ConfidenceUIIndicator RenderMetadata hex_colour values.
 */
export function ConfidenceIndicator({
  score,
  label,
  size = "md",
  highContrast = false,
  style,
  className,
}: ConfidenceIndicatorProps): React.ReactElement {
  const clampedScore = Math.max(0, Math.min(1, score));
  const level: ConfidenceLevel = useMemo(() => scoreTolevel(clampedScore), [clampedScore]);
  const colour = getConfidenceColour(level, highContrast);
  const ariaLabel = getConfidenceAriaLabel(level, clampedScore);
  const levelLabel = LEVEL_LABELS[level];
  const sizeTokens = getSizeTokens(size);
  const percentage = Math.round(clampedScore * 100);

  // Show numeric score for medium/low — mirrors Python RenderMetadata.show_score.
  const showScore = level !== "high";

  const containerStyles: React.CSSProperties = {
    display: "flex",
    flexDirection: "column",
    gap: sizeTokens.gap,
    width: "100%",
    ...style,
  };

  const headerStyles: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: sizeTokens.fontSize,
  };

  const trackStyles: React.CSSProperties = {
    width: "100%",
    height: sizeTokens.height,
    backgroundColor: "#e0e0e0",
    borderRadius: "9999px",
    overflow: "hidden",
  };

  const fillStyles: React.CSSProperties = {
    width: `${percentage}%`,
    height: "100%",
    backgroundColor: colour,
    borderRadius: "9999px",
    transition: "width 0.3s ease, background-color 0.3s ease",
  };

  const badgeStyles: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    padding: "2px 8px",
    borderRadius: "9999px",
    backgroundColor: colour,
    color: "#ffffff",
    fontSize: sizeTokens.fontSize,
    fontWeight: 600,
  };

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={ariaLabel}
      style={containerStyles}
      className={className}
    >
      <div style={headerStyles}>
        {label !== undefined && label !== "" && (
          <span style={{ fontWeight: 500 }}>{label}</span>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginLeft: "auto" }}>
          {showScore && (
            <span aria-hidden="true" style={{ fontSize: sizeTokens.fontSize, color: "#555" }}>
              {percentage}%
            </span>
          )}
          <span style={badgeStyles} aria-hidden="true">
            {levelLabel}
          </span>
        </div>
      </div>

      <div
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Confidence: ${percentage}%`}
        style={trackStyles}
      >
        <div style={fillStyles} />
      </div>
    </div>
  );
}
