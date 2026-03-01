/**
 * HTTP client for the agent-sense transparency API.
 *
 * Delegates all HTTP transport to `@aumos/sdk-core` which provides
 * automatic retry with exponential back-off, timeout management via
 * `AbortSignal.timeout`, interceptor support, and a typed error hierarchy.
 *
 * The public-facing `ApiResult<T>` envelope is preserved for full
 * backward compatibility with existing callers.
 *
 * @example
 * ```ts
 * import { createAgentSenseClient } from "@aumos/agent-sense";
 *
 * const client = createAgentSenseClient({ baseUrl: "http://localhost:8091" });
 *
 * const intent = await client.parseIntent({
 *   utterance: "Show me my account balance",
 *   session_id: "sess-001",
 * });
 *
 * if (intent.ok) {
 *   console.log("Parsed intent:", intent.data.intent);
 * }
 * ```
 */

import {
  createHttpClient,
  HttpError,
  NetworkError,
  TimeoutError,
  AumosError,
  type HttpClient,
} from "@aumos/sdk-core";

import type {
  AccessibilityCheckResult,
  AccessibilityConfig,
  ApiResult,
  DetectedContext,
  DialogueState,
  FeedbackEntry,
  FeedbackSubmitRequest,
  FeedbackSummary,
  ResponseCandidate,
  TransparencyIndicator,
  UserIntent,
} from "./types.js";

// ---------------------------------------------------------------------------
// Client configuration
// ---------------------------------------------------------------------------

/** Configuration options for the AgentSenseClient. */
export interface AgentSenseClientConfig {
  /** Base URL of the agent-sense server (e.g. "http://localhost:8091"). */
  readonly baseUrl: string;
  /** Optional request timeout in milliseconds (default: 30000). */
  readonly timeoutMs?: number;
  /** Optional extra HTTP headers sent with every request. */
  readonly headers?: Readonly<Record<string, string>>;
}

// ---------------------------------------------------------------------------
// Internal adapter
// ---------------------------------------------------------------------------

async function callApi<T>(
  operation: () => Promise<{ readonly data: T; readonly status: number }>,
): Promise<ApiResult<T>> {
  try {
    const response = await operation();
    return { ok: true, data: response.data };
  } catch (error: unknown) {
    if (error instanceof HttpError) {
      return {
        ok: false,
        error: { error: error.message, detail: String(error.body ?? "") },
        status: error.statusCode,
      };
    }
    if (error instanceof TimeoutError) {
      return {
        ok: false,
        error: { error: "Request timed out", detail: error.message },
        status: 0,
      };
    }
    if (error instanceof NetworkError) {
      return {
        ok: false,
        error: { error: "Network error", detail: error.message },
        status: 0,
      };
    }
    if (error instanceof AumosError) {
      return {
        ok: false,
        error: { error: error.code, detail: error.message },
        status: error.statusCode ?? 0,
      };
    }
    const message = error instanceof Error ? error.message : String(error);
    return {
      ok: false,
      error: { error: "Unexpected error", detail: message },
      status: 0,
    };
  }
}

// ---------------------------------------------------------------------------
// Client interface
// ---------------------------------------------------------------------------

/** Typed HTTP client for the agent-sense server. */
export interface AgentSenseClient {
  /**
   * Parse the intent from a user utterance.
   *
   * @param options - Utterance and optional session context.
   * @returns A UserIntent record with intent label, confidence, and entities.
   */
  parseIntent(options: {
    utterance: string;
    session_id?: string;
    context?: Readonly<Record<string, unknown>>;
  }): Promise<ApiResult<UserIntent>>;

  /**
   * Rank a list of response candidates for the given context.
   *
   * @param options - Candidates, user text, and optional history.
   * @returns The candidates re-ordered by composite score.
   */
  rankResponses(options: {
    candidates: readonly { candidate_id: string; text: string; relevance_score: number }[];
    user_text: string;
    history?: readonly string[];
    recent_shown?: readonly string[];
  }): Promise<ApiResult<readonly ResponseCandidate[]>>;

  /**
   * Submit structured feedback for an agent interaction.
   *
   * @param request - Feedback submission payload.
   * @returns The stored FeedbackEntry record.
   */
  collectFeedback(
    request: FeedbackSubmitRequest,
  ): Promise<ApiResult<FeedbackEntry>>;

  /**
   * Retrieve the current dialogue state for a session.
   *
   * @param sessionId - The session identifier.
   * @returns The DialogueState record for this session.
   */
  getDialogueState(sessionId: string): Promise<ApiResult<DialogueState>>;

  /**
   * Check HTML content for WCAG 2.1 accessibility violations.
   *
   * @param config - Accessibility check configuration including HTML markup.
   * @returns The check result with any violations found.
   */
  checkAccessibility(
    config: AccessibilityConfig,
  ): Promise<ApiResult<AccessibilityCheckResult>>;

  /**
   * Get the transparency indicator (confidence + disclosure) for an agent.
   *
   * @param options - Agent ID and optional session context.
   * @returns A TransparencyIndicator combining confidence and disclosure.
   */
  getTransparencyIndicator(options: {
    agent_id: string;
    session_id?: string;
  }): Promise<ApiResult<TransparencyIndicator>>;

  /**
   * Detect the client context from a User-Agent string and HTTP headers.
   *
   * @param options - User-Agent string and optional HTTP hint headers.
   * @returns A DetectedContext with device type, network quality, and capabilities.
   */
  detectContext(options: {
    user_agent: string;
    headers?: Readonly<Record<string, string>>;
  }): Promise<ApiResult<DetectedContext>>;

  /**
   * Get aggregated feedback summary for an agent.
   *
   * @param agentId - The agent identifier.
   * @returns A FeedbackSummary with satisfaction score and category breakdown.
   */
  getFeedbackSummary(agentId: string): Promise<ApiResult<FeedbackSummary>>;
}

// ---------------------------------------------------------------------------
// Client factory
// ---------------------------------------------------------------------------

/**
 * Create a typed HTTP client for the agent-sense server.
 *
 * @param config - Client configuration including base URL.
 * @returns An AgentSenseClient instance.
 */
export function createAgentSenseClient(
  config: AgentSenseClientConfig,
): AgentSenseClient {
  const http: HttpClient = createHttpClient({
    baseUrl: config.baseUrl,
    timeout: config.timeoutMs ?? 30_000,
    defaultHeaders: config.headers,
  });

  return {
    parseIntent(options: {
      utterance: string;
      session_id?: string;
      context?: Readonly<Record<string, unknown>>;
    }): Promise<ApiResult<UserIntent>> {
      return callApi(() => http.post<UserIntent>("/sense/intent", options));
    },

    rankResponses(options: {
      candidates: readonly { candidate_id: string; text: string; relevance_score: number }[];
      user_text: string;
      history?: readonly string[];
      recent_shown?: readonly string[];
    }): Promise<ApiResult<readonly ResponseCandidate[]>> {
      return callApi(() =>
        http.post<readonly ResponseCandidate[]>("/sense/rank", options),
      );
    },

    collectFeedback(request: FeedbackSubmitRequest): Promise<ApiResult<FeedbackEntry>> {
      return callApi(() => http.post<FeedbackEntry>("/sense/feedback", request));
    },

    getDialogueState(sessionId: string): Promise<ApiResult<DialogueState>> {
      return callApi(() =>
        http.get<DialogueState>(
          `/sense/sessions/${encodeURIComponent(sessionId)}/state`,
        ),
      );
    },

    checkAccessibility(
      config: AccessibilityConfig,
    ): Promise<ApiResult<AccessibilityCheckResult>> {
      return callApi(() =>
        http.post<AccessibilityCheckResult>("/sense/accessibility/check", config),
      );
    },

    getTransparencyIndicator(options: {
      agent_id: string;
      session_id?: string;
    }): Promise<ApiResult<TransparencyIndicator>> {
      const queryParams: Record<string, string> = { agent_id: options.agent_id };
      if (options.session_id !== undefined) queryParams["session_id"] = options.session_id;
      return callApi(() =>
        http.get<TransparencyIndicator>("/sense/transparency", { queryParams }),
      );
    },

    detectContext(options: {
      user_agent: string;
      headers?: Readonly<Record<string, string>>;
    }): Promise<ApiResult<DetectedContext>> {
      return callApi(() =>
        http.post<DetectedContext>("/sense/context/detect", options),
      );
    },

    getFeedbackSummary(agentId: string): Promise<ApiResult<FeedbackSummary>> {
      return callApi(() =>
        http.get<FeedbackSummary>(
          `/sense/feedback/${encodeURIComponent(agentId)}/summary`,
        ),
      );
    },
  };
}
