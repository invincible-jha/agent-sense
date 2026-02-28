/**
 * TypeScript interfaces for the agent-sense transparency layer.
 *
 * Mirrors the Python dataclasses and Pydantic models defined in:
 *   agent_sense.indicators.confidence   (ConfidenceLevel, ConfidenceIndicator)
 *   agent_sense.indicators.disclosure   (DisclosureLevel, AIDisclosureCard)
 *   agent_sense.feedback.collector      (FeedbackCategory, FeedbackEntry, FeedbackSummary)
 *   agent_sense.context.detector        (DeviceType, NetworkQuality, BrowserCapabilities, DetectedContext)
 *   agent_sense.accessibility.wcag      (WCAGLevel, WCAGViolation)
 *   agent_sense.disclosure.transparency (SessionStats)
 *
 * All interfaces use readonly fields to match Python frozen dataclasses.
 */

// ---------------------------------------------------------------------------
// Confidence types
// ---------------------------------------------------------------------------

/**
 * Five-tier categorical confidence classification.
 * Maps to ConfidenceLevel enum in Python.
 * Score bands: very_low [0,0.2), low [0.2,0.4), medium [0.4,0.6),
 *              high [0.6,0.8), very_high [0.8,1.0].
 */
export type ConfidenceLevel =
  | "very_low"
  | "low"
  | "medium"
  | "high"
  | "very_high";

/** Structured confidence measurement for an AI agent response. */
export interface ConfidenceIndicator {
  /** Raw numeric confidence in [0.0, 1.0]. */
  readonly score: number;
  /** Categorical tier derived from score. */
  readonly level: ConfidenceLevel;
  /** Human-readable explanation of the confidence assessment. */
  readonly reasoning: string;
  /** Map of contributing factor names to their individual scores [0, 1]. */
  readonly factors: Readonly<Record<string, number>>;
}

// ---------------------------------------------------------------------------
// Disclosure types
// ---------------------------------------------------------------------------

/**
 * Controls the verbosity of disclosure card rendering.
 * Maps to DisclosureLevel enum in Python.
 */
export type DisclosureLevel = "minimal" | "standard" | "detailed" | "full";

/** Immutable disclosure card for an AI agent deployment. */
export interface AIDisclosureCard {
  /** Human-readable name of the agent. */
  readonly agent_name: string;
  /** Semantic version or build identifier. */
  readonly agent_version: string;
  /** Organisation that produced the underlying model. */
  readonly model_provider: string;
  /** Identifier of the specific model being used. */
  readonly model_name: string;
  /** Ordered list of things this agent can do well. */
  readonly capabilities: readonly string[];
  /** Ordered list of known constraints or failure modes. */
  readonly limitations: readonly string[];
  /** Plain-language description of how conversation data is handled. */
  readonly data_handling: string;
  /** ISO-8601 UTC datetime at which this card was last revised. */
  readonly last_updated: string;
  /** Verbosity level used when rendering this card. */
  readonly disclosure_level: DisclosureLevel;
}

// ---------------------------------------------------------------------------
// Transparency indicator (combined type requested by spec)
// ---------------------------------------------------------------------------

/** Full transparency indicator combining confidence and disclosure. */
export interface TransparencyIndicator {
  /** The confidence measurement for a response. */
  readonly confidence: ConfidenceIndicator;
  /** The AI disclosure card for this deployment. */
  readonly disclosure: AIDisclosureCard;
  /** ISO-8601 UTC timestamp when this indicator was generated. */
  readonly generated_at: string;
}

// ---------------------------------------------------------------------------
// Feedback types
// ---------------------------------------------------------------------------

/**
 * Category labels for user feedback.
 * Maps to FeedbackCategory enum in Python.
 */
export type FeedbackCategory =
  | "helpful"
  | "unhelpful"
  | "harmful"
  | "irrelevant"
  | "inaccurate"
  | "too_long"
  | "too_short"
  | "other";

/** A single structured feedback submission from a user. */
export interface FeedbackEntry {
  /** Unique identifier for this feedback entry. */
  readonly feedback_id: string;
  /** Satisfaction rating from 1 (very poor) to 5 (excellent). */
  readonly rating: number;
  /** Structured category label for quick classification. */
  readonly category: FeedbackCategory;
  /** The agent that produced the response being rated. */
  readonly agent_id: string;
  /** Optional session identifier for grouping feedback. */
  readonly session_id: string;
  /** Optional identifier for the specific interaction being rated. */
  readonly interaction_id: string;
  /** Optional free-form user comment. */
  readonly free_text: string;
  /** ISO-8601 UTC datetime when feedback was submitted. */
  readonly submitted_at: string;
  /** Whether this is positive feedback (rating >= 4 or category = helpful). */
  readonly is_positive: boolean;
  /** Whether this is negative feedback (rating <= 2 or category = harmful/unhelpful). */
  readonly is_negative: boolean;
  /** Arbitrary additional key-value metadata. */
  readonly metadata: Readonly<Record<string, string>>;
}

/** Request payload for submitting feedback. */
export interface FeedbackSubmitRequest {
  /** Satisfaction rating from 1 to 5. */
  readonly rating: number;
  /** Structured category label. */
  readonly category: FeedbackCategory;
  /** The agent being rated. */
  readonly agent_id: string;
  /** Optional session identifier. */
  readonly session_id?: string;
  /** Optional interaction identifier. */
  readonly interaction_id?: string;
  /** Optional free-form comment. */
  readonly free_text?: string;
  /** Optional additional metadata. */
  readonly metadata?: Readonly<Record<string, string>>;
}

/** Aggregated feedback statistics for an agent. */
export interface FeedbackSummary {
  /** The agent this summary covers. */
  readonly agent_id: string;
  /** Total number of feedback entries processed. */
  readonly total_feedback: number;
  /** Mean rating across all entries (1–5). */
  readonly average_rating: number;
  /** Normalised satisfaction score in [0, 1]. */
  readonly satisfaction_score: number;
  /** Count of feedback entries per category. */
  readonly category_distribution: Readonly<Record<string, number>>;
  /** Number of positive feedback entries. */
  readonly positive_count: number;
  /** Number of negative feedback entries. */
  readonly negative_count: number;
  /** Number of neutral feedback entries (rating = 3). */
  readonly neutral_count: number;
  /** Most frequent words from free-text comments. */
  readonly top_free_text_keywords: readonly string[];
  /** ISO-8601 UTC datetime when this summary was computed. */
  readonly computed_at: string;
}

// ---------------------------------------------------------------------------
// Dialogue / context types
// ---------------------------------------------------------------------------

/**
 * Canonical device categories.
 * Maps to DeviceType enum in Python.
 */
export type DeviceType = "desktop" | "mobile" | "tablet" | "voice" | "unknown";

/**
 * Inferred network quality tiers.
 * Maps to NetworkQuality enum in Python.
 */
export type NetworkQuality = "high" | "medium" | "low" | "unknown";

/** Feature flags inferred from User-Agent and hints headers. */
export interface BrowserCapabilities {
  readonly javascript_enabled: boolean;
  readonly webgl_supported: boolean;
  readonly touch_supported: boolean;
  readonly screen_reader_likely: boolean;
  readonly reduced_motion_preferred: boolean;
}

/** Full result of a context detection call. */
export interface DetectedContext {
  readonly device_type: DeviceType;
  readonly network_quality: NetworkQuality;
  readonly browser_capabilities: BrowserCapabilities;
  readonly user_agent: string;
  readonly raw_headers: Readonly<Record<string, string>>;
}

/** Intent parsed from a user utterance. */
export interface UserIntent {
  /** The raw user utterance. */
  readonly utterance: string;
  /** Primary intent label (e.g. "question", "command", "clarification"). */
  readonly intent: string;
  /** Confidence score for this intent classification in [0, 1]. */
  readonly confidence: number;
  /** Extracted named entities. */
  readonly entities: Readonly<Record<string, string>>;
  /** ISO-8601 UTC timestamp when this intent was parsed. */
  readonly parsed_at: string;
}

/** Ranked response candidate with score. */
export interface ResponseCandidate {
  /** Unique identifier for this candidate. */
  readonly candidate_id: string;
  /** The response text. */
  readonly text: string;
  /** Composite ranking score in [0, 1] (higher = preferred). */
  readonly score: number;
  /** Context match contribution to the score. */
  readonly context_match_score: number;
  /** Relevance contribution to the score. */
  readonly relevance_score: number;
}

/** Current state of a dialogue session. */
export interface DialogueState {
  /** Unique session identifier. */
  readonly session_id: string;
  /** Current turn number (1-indexed). */
  readonly turn_number: number;
  /** Detected context for this session. */
  readonly detected_context: DetectedContext;
  /** Current confidence level for the session. */
  readonly confidence_level: ConfidenceLevel;
  /** ISO-8601 UTC timestamp of the last activity. */
  readonly last_activity_at: string;
  /** Whether a human handoff has been triggered. */
  readonly handoff_triggered: boolean;
}

// ---------------------------------------------------------------------------
// Accessibility types
// ---------------------------------------------------------------------------

/**
 * WCAG 2.1 conformance level.
 * Maps to WCAGLevel enum in Python.
 */
export type WCAGLevel = "A" | "AA" | "AAA";

/** A single WCAG 2.1 violation found in inspected content. */
export interface WCAGViolation {
  /** WCAG success criterion number (e.g. "1.1.1"). */
  readonly criterion: string;
  /** Conformance level of the criterion. */
  readonly level: WCAGLevel;
  /** Human-readable description of the violation. */
  readonly description: string;
  /** Short snippet of the problematic markup or text. */
  readonly element_snippet: string;
  /** Recommended remediation for the violation. */
  readonly suggestion: string;
}

/** Result of an accessibility check. */
export interface AccessibilityCheckResult {
  /** Whether the content passed all WCAG checks. */
  readonly passed: boolean;
  /** List of WCAG violations found. */
  readonly violations: readonly WCAGViolation[];
  /** Per-criterion violation counts. */
  readonly violation_counts: Readonly<Record<string, number>>;
}

/** Configuration for an accessibility check request. */
export interface AccessibilityConfig {
  /** HTML markup or text content to check. */
  readonly html: string;
  /** Whether to check color contrast. */
  readonly check_color_contrast?: boolean;
  /** Whether to check text alternatives for images. */
  readonly check_text_alternatives?: boolean;
  /** Whether to check heading hierarchy. */
  readonly check_heading_hierarchy?: boolean;
  /** Whether to check link text descriptiveness. */
  readonly check_link_text?: boolean;
}

// ---------------------------------------------------------------------------
// API result wrapper (shared pattern)
// ---------------------------------------------------------------------------

/** Standard error payload returned by the agent-sense API. */
export interface ApiError {
  readonly error: string;
  readonly detail: string;
}

/** Result type for all client operations. */
export type ApiResult<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly error: ApiError; readonly status: number };
