/**
 * Accessibility utility functions for @aumos/agent-sense-react.
 *
 * Provides helpers for WCAG 2.1 AA compliant ARIA label generation,
 * focus management, and keyboard navigation support.
 */

import type {
  AccessibilityPreferences,
  ConfidenceLevel,
  TextSizeLevel,
  UrgencyLevel,
} from "../types.js";

// ---------------------------------------------------------------------------
// ARIA label generators
// ---------------------------------------------------------------------------

/**
 * Generates a descriptive ARIA label for a confidence indicator.
 * Mirrors Python RenderMetadata.aria_label values.
 */
export function getConfidenceAriaLabel(
  level: ConfidenceLevel,
  score: number
): string {
  const percentage = Math.round(score * 100);
  const levelDescriptions: Record<ConfidenceLevel, string> = {
    high: "Agent is highly confident in this response",
    medium: "Agent has moderate confidence in this response",
    low: "Agent has low confidence; consider human review",
  };
  return `${levelDescriptions[level]}. Score: ${percentage}%.`;
}

/**
 * Generates a descriptive ARIA label for a handoff urgency badge.
 */
export function getUrgencyAriaLabel(urgency: UrgencyLevel): string {
  const descriptions: Record<UrgencyLevel, string> = {
    low: "Low urgency — no immediate action required",
    medium: "Medium urgency — review when possible",
    high: "High urgency — requires prompt attention",
    critical: "Critical urgency — immediate action required",
  };
  return descriptions[urgency];
}

// ---------------------------------------------------------------------------
// CSS font size scale
// ---------------------------------------------------------------------------

const TEXT_SIZE_MAP: Record<TextSizeLevel, string> = {
  normal: "1rem",
  large: "1.25rem",
  xlarge: "1.5rem",
};

/**
 * Returns the CSS font-size value for a given text size level.
 */
export function getTextSizeCss(size: TextSizeLevel): string {
  return TEXT_SIZE_MAP[size];
}

// ---------------------------------------------------------------------------
// Document-level CSS class application
// ---------------------------------------------------------------------------

/**
 * Applies or removes accessibility-related CSS classes on the document root.
 * Designed to be called from AccessibilityToolbar whenever preferences change.
 *
 * Class names used:
 *   - `a11y-high-contrast`
 *   - `a11y-reduced-motion`
 *   - `a11y-focus-indicators`
 */
export function applyDocumentA11yClasses(
  preferences: AccessibilityPreferences
): void {
  if (typeof document === "undefined") return;

  const root = document.documentElement;

  toggleClass(root, "a11y-high-contrast", preferences.highContrast);
  toggleClass(root, "a11y-reduced-motion", preferences.reducedMotion);
  toggleClass(root, "a11y-focus-indicators", preferences.focusIndicators);
  root.style.fontSize = getTextSizeCss(preferences.textSize);
}

function toggleClass(
  element: HTMLElement,
  className: string,
  active: boolean
): void {
  if (active) {
    element.classList.add(className);
  } else {
    element.classList.remove(className);
  }
}

// ---------------------------------------------------------------------------
// Keyboard navigation helpers
// ---------------------------------------------------------------------------

/** Key codes relevant to ARIA listbox/dialog keyboard navigation. */
export const KEYBOARD_KEYS = {
  ARROW_UP: "ArrowUp",
  ARROW_DOWN: "ArrowDown",
  ENTER: "Enter",
  ESCAPE: "Escape",
  HOME: "Home",
  END: "End",
  TAB: "Tab",
} as const;

export type KeyboardKey = (typeof KEYBOARD_KEYS)[keyof typeof KEYBOARD_KEYS];

/**
 * Computes the next focusable index in a listbox given the current index
 * and the pressed key. Wraps around at boundaries.
 *
 * @param currentIndex - Currently active option index (-1 if none).
 * @param totalCount - Total number of options.
 * @param key - The pressed keyboard key.
 */
export function getNextListboxIndex(
  currentIndex: number,
  totalCount: number,
  key: string
): number {
  if (totalCount === 0) return -1;

  switch (key) {
    case KEYBOARD_KEYS.ARROW_DOWN:
      return (currentIndex + 1) % totalCount;
    case KEYBOARD_KEYS.ARROW_UP:
      return (currentIndex - 1 + totalCount) % totalCount;
    case KEYBOARD_KEYS.HOME:
      return 0;
    case KEYBOARD_KEYS.END:
      return totalCount - 1;
    default:
      return currentIndex;
  }
}

// ---------------------------------------------------------------------------
// localStorage helpers (graceful degradation for SSR)
// ---------------------------------------------------------------------------

/**
 * Safely reads a JSON value from localStorage.
 * Returns null on parse errors or when localStorage is unavailable (SSR).
 */
export function readLocalStorage<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

/**
 * Safely writes a JSON-serialisable value to localStorage.
 * Silently no-ops when localStorage is unavailable (SSR, private browsing).
 */
export function writeLocalStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // QuotaExceededError or SecurityError — ignore.
  }
}
