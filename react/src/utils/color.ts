/**
 * Color utility functions for @aumos/agent-sense-react.
 *
 * Maps confidence levels to WCAG-compliant colours matching the Python
 * RenderMetadata hex_colour values from agent_sense.components.confidence.
 */

import type { ConfidenceLevel, UrgencyLevel } from "../types.js";

// Colour tokens sourced directly from Python _RENDER_MAP hex_colour values.
export const CONFIDENCE_COLOURS = {
  high: "#27ae60",
  medium: "#f39c12",
  low: "#e74c3c",
} as const satisfies Record<ConfidenceLevel, string>;

// High-contrast overrides for accessibility mode.
export const CONFIDENCE_COLOURS_HIGH_CONTRAST = {
  high: "#006b2c",
  medium: "#7a4f00",
  low: "#8b0000",
} as const satisfies Record<ConfidenceLevel, string>;

// Urgency badge colours.
export const URGENCY_COLOURS = {
  low: "#27ae60",
  medium: "#f39c12",
  high: "#e74c3c",
  critical: "#8e44ad",
} as const satisfies Record<UrgencyLevel, string>;

// High-contrast urgency colours.
export const URGENCY_COLOURS_HIGH_CONTRAST = {
  low: "#006b2c",
  medium: "#7a4f00",
  high: "#8b0000",
  critical: "#4a0060",
} as const satisfies Record<UrgencyLevel, string>;

/**
 * Returns the background colour for a confidence level.
 *
 * @param level - The confidence level.
 * @param highContrast - Whether to use high-contrast palette.
 */
export function getConfidenceColour(
  level: ConfidenceLevel,
  highContrast = false
): string {
  return highContrast
    ? CONFIDENCE_COLOURS_HIGH_CONTRAST[level]
    : CONFIDENCE_COLOURS[level];
}

/**
 * Returns the background colour for an urgency level.
 *
 * @param urgency - The urgency level.
 * @param highContrast - Whether to use high-contrast palette.
 */
export function getUrgencyColour(
  urgency: UrgencyLevel,
  highContrast = false
): string {
  return highContrast
    ? URGENCY_COLOURS_HIGH_CONTRAST[urgency]
    : URGENCY_COLOURS[urgency];
}

/**
 * Derives the confidence level from a numeric score.
 * Mirrors Python _score_to_level() with thresholds 0.70 / 0.40.
 *
 * @param score - Numeric confidence value in [0.0, 1.0].
 */
export function scoreTolevel(score: number): ConfidenceLevel {
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}
