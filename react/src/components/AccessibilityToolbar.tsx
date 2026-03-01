/**
 * AccessibilityToolbar — persistent WCAG accessibility controls.
 *
 * Provides three text size levels (normal / large / x-large),
 * high-contrast mode toggle, reduced-motion toggle, and enhanced
 * focus indicator toggle.
 *
 * All preferences are persisted to localStorage via useAccessibility hook.
 *
 * ARIA: toolbar landmark, each button has aria-pressed for toggle state.
 *
 * Usage:
 *   <AccessibilityToolbar storageKey="my-app-a11y" />
 */

import React, { useCallback } from "react";
import type { TextSizeLevel } from "../types.js";
import { useAccessibility } from "../hooks/useAccessibility.js";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AccessibilityToolbarProps {
  /**
   * localStorage key for persistence. Defaults to "aumos-agent-sense-a11y".
   */
  storageKey?: string;
  /** Optional className for the toolbar element. */
  className?: string;
  /** Optional additional styles for the toolbar element. */
  style?: React.CSSProperties;
}

// ---------------------------------------------------------------------------
// Internal sub-components
// ---------------------------------------------------------------------------

interface ToolbarButtonProps {
  ariaLabel: string;
  isPressed: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function ToolbarButton({
  ariaLabel,
  isPressed,
  onClick,
  children,
}: ToolbarButtonProps): React.ReactElement {
  const buttonStyles: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "6px 12px",
    border: "1px solid #ccc",
    borderRadius: "4px",
    backgroundColor: isPressed ? "#1a1a1a" : "#ffffff",
    color: isPressed ? "#ffffff" : "#1a1a1a",
    cursor: "pointer",
    fontSize: "0.875rem",
    fontWeight: 500,
    lineHeight: 1,
    transition: "background-color 0.15s ease, color 0.15s ease",
    minWidth: "44px",  // WCAG 2.5.5 minimum touch target.
    minHeight: "44px",
  };

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-pressed={isPressed}
      onClick={onClick}
      style={buttonStyles}
    >
      {children}
    </button>
  );
}

// ---------------------------------------------------------------------------
// AccessibilityToolbar component
// ---------------------------------------------------------------------------

const TEXT_SIZE_LEVELS: readonly TextSizeLevel[] = ["normal", "large", "xlarge"];

const TEXT_SIZE_LABELS: Record<TextSizeLevel, string> = {
  normal: "A",
  large: "A+",
  xlarge: "A++",
};

const TEXT_SIZE_ARIA_LABELS: Record<TextSizeLevel, string> = {
  normal: "Normal text size",
  large: "Large text size",
  xlarge: "Extra large text size",
};

/**
 * Renders an accessible toolbar for managing visual accessibility preferences.
 *
 * Preferences persist across page loads via localStorage. Document-level
 * CSS classes are applied immediately for application-wide effect.
 */
export function AccessibilityToolbar({
  storageKey,
  className,
  style,
}: AccessibilityToolbarProps): React.ReactElement {
  const {
    preferences,
    setTextSize,
    setHighContrast,
    setReducedMotion,
    setFocusIndicators,
    resetPreferences,
  } = useAccessibility(storageKey);

  const handleHighContrast = useCallback(() => {
    setHighContrast(!preferences.highContrast);
  }, [preferences.highContrast, setHighContrast]);

  const handleReducedMotion = useCallback(() => {
    setReducedMotion(!preferences.reducedMotion);
  }, [preferences.reducedMotion, setReducedMotion]);

  const handleFocusIndicators = useCallback(() => {
    setFocusIndicators(!preferences.focusIndicators);
  }, [preferences.focusIndicators, setFocusIndicators]);

  const toolbarStyles: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "8px",
    padding: "8px",
    backgroundColor: "#f8f8f8",
    border: "1px solid #ddd",
    borderRadius: "6px",
    ...style,
  };

  const separatorStyles: React.CSSProperties = {
    width: "1px",
    height: "28px",
    backgroundColor: "#ccc",
    margin: "0 4px",
  };

  const labelStyles: React.CSSProperties = {
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "#555",
    marginRight: "4px",
    whiteSpace: "nowrap",
  };

  return (
    <div
      role="toolbar"
      aria-label="Accessibility settings"
      style={toolbarStyles}
      className={className}
    >
      {/* Text size controls */}
      <span style={labelStyles} aria-hidden="true">
        Text:
      </span>
      {TEXT_SIZE_LEVELS.map((sizeLevel) => (
        <ToolbarButton
          key={sizeLevel}
          ariaLabel={TEXT_SIZE_ARIA_LABELS[sizeLevel]}
          isPressed={preferences.textSize === sizeLevel}
          onClick={() => setTextSize(sizeLevel)}
        >
          {TEXT_SIZE_LABELS[sizeLevel]}
        </ToolbarButton>
      ))}

      <div role="separator" aria-orientation="vertical" style={separatorStyles} />

      {/* High contrast */}
      <ToolbarButton
        ariaLabel="Toggle high contrast mode"
        isPressed={preferences.highContrast}
        onClick={handleHighContrast}
      >
        ◑
      </ToolbarButton>

      {/* Reduced motion */}
      <ToolbarButton
        ariaLabel="Toggle reduced motion"
        isPressed={preferences.reducedMotion}
        onClick={handleReducedMotion}
      >
        ⏸
      </ToolbarButton>

      {/* Focus indicators */}
      <ToolbarButton
        ariaLabel="Toggle enhanced focus indicators"
        isPressed={preferences.focusIndicators}
        onClick={handleFocusIndicators}
      >
        ⬚
      </ToolbarButton>

      <div role="separator" aria-orientation="vertical" style={separatorStyles} />

      {/* Reset */}
      <button
        type="button"
        aria-label="Reset all accessibility preferences to defaults"
        onClick={resetPreferences}
        style={{
          padding: "6px 12px",
          border: "1px solid #ccc",
          borderRadius: "4px",
          backgroundColor: "#fff",
          color: "#555",
          cursor: "pointer",
          fontSize: "0.75rem",
          minWidth: "44px",
          minHeight: "44px",
        }}
      >
        Reset
      </button>
    </div>
  );
}
