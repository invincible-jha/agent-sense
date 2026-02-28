/**
 * @aumos/agent-sense
 *
 * TypeScript client for the AumOS agent-sense transparency layer.
 * Provides HTTP client, intent parsing, response ranking, feedback collection,
 * accessibility checking, and confidence/disclosure type definitions.
 */

// Client and configuration
export type { AgentSenseClient, AgentSenseClientConfig } from "./client.js";
export { createAgentSenseClient } from "./client.js";

// Core types
export type {
  AccessibilityCheckResult,
  AccessibilityConfig,
  AIDisclosureCard,
  ApiError,
  ApiResult,
  BrowserCapabilities,
  ConfidenceIndicator,
  ConfidenceLevel,
  DetectedContext,
  DeviceType,
  DialogueState,
  DisclosureLevel,
  FeedbackCategory,
  FeedbackEntry,
  FeedbackSubmitRequest,
  FeedbackSummary,
  NetworkQuality,
  ResponseCandidate,
  TransparencyIndicator,
  UserIntent,
  WCAGLevel,
  WCAGViolation,
} from "./types.js";
