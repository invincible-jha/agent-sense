/**
 * @aumos/agent-sense-react
 *
 * React 18+ component library for rendering agent-sense signals:
 *   - ConfidenceIndicator — confidence bar with ARIA live region
 *   - HandoffCard         — progressive-disclosure handoff context
 *   - DisclosureWrapper   — AI transparency badge wrapper
 *   - AccessibilityToolbar — persistent WCAG accessibility controls
 *   - SuggestionOverlay  — keyboard-navigable suggestion listbox
 *
 * Hooks:
 *   - useAgentSense      — global agent-sense state context
 *   - useAccessibility   — localStorage-backed accessibility preferences
 *
 * All exports are named (no default exports per project convention).
 */

// Components
export { ConfidenceIndicator } from "./components/ConfidenceIndicator.js";
export type { ConfidenceIndicatorProps } from "./components/ConfidenceIndicator.js";

export { HandoffCard } from "./components/HandoffCard.js";
export type { HandoffCardProps } from "./components/HandoffCard.js";

export { DisclosureWrapper } from "./components/DisclosureWrapper.js";
export type { DisclosureWrapperProps } from "./components/DisclosureWrapper.js";

export { AccessibilityToolbar } from "./components/AccessibilityToolbar.js";
export type { AccessibilityToolbarProps } from "./components/AccessibilityToolbar.js";

export { SuggestionOverlay } from "./components/SuggestionOverlay.js";
export type { SuggestionOverlayProps } from "./components/SuggestionOverlay.js";

// Hooks
export {
  AgentSenseProvider,
  useAgentSense,
} from "./hooks/useAgentSense.js";
export type { AgentSenseProviderProps } from "./hooks/useAgentSense.js";

export {
  useAccessibility,
  DEFAULT_STORAGE_KEY,
} from "./hooks/useAccessibility.js";
export type { UseAccessibilityReturn } from "./hooks/useAccessibility.js";

// Utils
export {
  getConfidenceColour,
  getUrgencyColour,
  scoreTolevel,
  CONFIDENCE_COLOURS,
  CONFIDENCE_COLOURS_HIGH_CONTRAST,
  URGENCY_COLOURS,
  URGENCY_COLOURS_HIGH_CONTRAST,
} from "./utils/color.js";

export {
  getConfidenceAriaLabel,
  getUrgencyAriaLabel,
  getTextSizeCss,
  applyDocumentA11yClasses,
  getNextListboxIndex,
  readLocalStorage,
  writeLocalStorage,
  KEYBOARD_KEYS,
} from "./utils/a11y.js";

// Types
export type {
  ConfidenceLevel,
  ConfidenceRenderMetadata,
  EscalationThreshold,
  ConfidenceIndicatorData,
  UrgencyLevel,
  HandoffPackageData,
  DisclosureLevel,
  AIDisclosureCardData,
  SuggestionCategory,
  SuggestionItem,
  TextSizeLevel,
  AccessibilityPreferences,
  AgentSenseContextValue,
} from "./types.js";

export { DEFAULT_ACCESSIBILITY_PREFERENCES } from "./types.js";
