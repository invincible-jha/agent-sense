/**
 * TypeScript type contracts for @aumos/agent-sense-react.
 *
 * These types mirror the Python data models in:
 *   - agent_sense.components.confidence (ConfidenceUIIndicator)
 *   - agent_sense.indicators.handoff_signal (HandoffSignal / HandoffPackage)
 *   - agent_sense.indicators.disclosure (AIDisclosureCard)
 *   - agent_sense.suggestions.engine (Suggestion)
 *   - agent_sense.accessibility.wcag (WCAGViolation)
 *
 * No runtime dependencies — plain TypeScript interfaces and const enums.
 */

// ---------------------------------------------------------------------------
// Confidence
// ---------------------------------------------------------------------------

/** Three-tier UI confidence classification matching Python ConfidenceLevel. */
export type ConfidenceLevel = "high" | "medium" | "low";

/**
 * Visual and accessibility metadata for rendering a confidence indicator.
 * Mirrors Python RenderMetadata dataclass.
 */
export interface ConfidenceRenderMetadata {
  readonly cssClass: string;
  readonly hexColour: string;
  readonly icon: string;
  readonly label: string;
  readonly ariaLabel: string;
  readonly showScore: boolean;
}

/**
 * Auto-escalation threshold configuration.
 * Mirrors Python EscalationThreshold dataclass.
 */
export interface EscalationThreshold {
  readonly scoreThreshold: number;
  readonly enabled: boolean;
  readonly escalationTarget: string;
}

/**
 * Full confidence indicator data object.
 * Mirrors Python ConfidenceUIIndicator.to_dict() output.
 */
export interface ConfidenceIndicatorData {
  readonly score: number;
  readonly level: ConfidenceLevel;
  readonly render: ConfidenceRenderMetadata;
  readonly needsEscalation: boolean;
  readonly escalationTarget: string;
  readonly contextLabel: string;
  readonly extra: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Handoff
// ---------------------------------------------------------------------------

/** Urgency classification for a handoff request. Mirrors Python UrgencyLevel. */
export type UrgencyLevel = "low" | "medium" | "high" | "critical";

/**
 * Structured context bundle for agent-to-human handoff.
 * Mirrors Python HandoffPackage.to_dict() output.
 */
export interface HandoffPackageData {
  readonly summary: string;
  readonly keyFacts: readonly string[];
  readonly unresolvedQuestions: readonly string[];
  readonly attemptedActions: readonly string[];
  readonly urgency: UrgencyLevel;
  readonly timestamp: string;
  readonly sessionId: string;
  readonly metadata: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Disclosure
// ---------------------------------------------------------------------------

/** Verbosity level for AI disclosure card rendering. */
export type DisclosureLevel = "minimal" | "standard" | "detailed" | "full";

/**
 * Immutable disclosure card for an AI agent deployment.
 * Mirrors Python AIDisclosureCard.to_dict() output.
 */
export interface AIDisclosureCardData {
  readonly agentName: string;
  readonly agentVersion: string;
  readonly modelProvider: string;
  readonly modelName: string;
  readonly capabilities: readonly string[];
  readonly limitations: readonly string[];
  readonly dataHandling: string;
  readonly lastUpdated: string;
  readonly disclosureLevel: DisclosureLevel;
}

// ---------------------------------------------------------------------------
// Suggestions
// ---------------------------------------------------------------------------

/** Classification for a suggestion. Mirrors Python SuggestionCategory. */
export type SuggestionCategory =
  | "clarification"
  | "next_step"
  | "related_topic"
  | "help";

/**
 * A single contextual suggestion presented to the user.
 * Mirrors Python Suggestion dataclass.
 */
export interface SuggestionItem {
  readonly id: string;
  readonly label: string;
  readonly description?: string;
  readonly category?: SuggestionCategory;
  readonly relevanceScore?: number;
}

// ---------------------------------------------------------------------------
// Accessibility settings (local state, no Python equivalent)
// ---------------------------------------------------------------------------

/** Text size scale for AccessibilityToolbar. */
export type TextSizeLevel = "normal" | "large" | "xlarge";

/** Persisted accessibility preferences for a user session. */
export interface AccessibilityPreferences {
  textSize: TextSizeLevel;
  highContrast: boolean;
  reducedMotion: boolean;
  focusIndicators: boolean;
}

export const DEFAULT_ACCESSIBILITY_PREFERENCES: AccessibilityPreferences = {
  textSize: "normal",
  highContrast: false,
  reducedMotion: false,
  focusIndicators: false,
};

// ---------------------------------------------------------------------------
// AgentSense context shape (for useAgentSense hook)
// ---------------------------------------------------------------------------

export interface AgentSenseContextValue {
  confidence: ConfidenceIndicatorData | null;
  handoff: HandoffPackageData | null;
  disclosure: AIDisclosureCardData | null;
  suggestions: readonly SuggestionItem[];
  accessibility: AccessibilityPreferences;
  setConfidence: (data: ConfidenceIndicatorData | null) => void;
  setHandoff: (data: HandoffPackageData | null) => void;
  setDisclosure: (data: AIDisclosureCardData | null) => void;
  setSuggestions: (items: readonly SuggestionItem[]) => void;
  setAccessibility: (prefs: Partial<AccessibilityPreferences>) => void;
}
