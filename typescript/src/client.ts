/**
 * HTTP client for the agent-sense transparency API.
 *
 * Uses the Fetch API (available natively in Node 18+, browsers, and Deno).
 * No external dependencies required.
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

import type {
  AccessibilityCheckResult,
  AccessibilityConfig,
  ApiError,
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
// Internal helpers
// ---------------------------------------------------------------------------

async function fetchJson<T>(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    clearTimeout(timeoutId);

    const body = await response.json() as unknown;

    if (!response.ok) {
      const errorBody = body as Partial<ApiError>;
      return {
        ok: false,
        error: {
          error: errorBody.error ?? "Unknown error",
          detail: errorBody.detail ?? "",
        },
        status: response.status,
      };
    }

    return { ok: true, data: body as T };
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    const message = err instanceof Error ? err.message : String(err);
    return {
      ok: false,
      error: { error: "Network error", detail: message },
      status: 0,
    };
  }
}

function buildHeaders(
  extraHeaders: Readonly<Record<string, string>> | undefined,
): Record<string, string> {
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...extraHeaders,
  };
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
  const { baseUrl, timeoutMs = 30_000, headers: extraHeaders } = config;
  const baseHeaders = buildHeaders(extraHeaders);

  return {
    async parseIntent(options: {
      utterance: string;
      session_id?: string;
      context?: Readonly<Record<string, unknown>>;
    }): Promise<ApiResult<UserIntent>> {
      return fetchJson<UserIntent>(
        `${baseUrl}/sense/intent`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(options),
        },
        timeoutMs,
      );
    },

    async rankResponses(options: {
      candidates: readonly { candidate_id: string; text: string; relevance_score: number }[];
      user_text: string;
      history?: readonly string[];
      recent_shown?: readonly string[];
    }): Promise<ApiResult<readonly ResponseCandidate[]>> {
      return fetchJson<readonly ResponseCandidate[]>(
        `${baseUrl}/sense/rank`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(options),
        },
        timeoutMs,
      );
    },

    async collectFeedback(
      request: FeedbackSubmitRequest,
    ): Promise<ApiResult<FeedbackEntry>> {
      return fetchJson<FeedbackEntry>(
        `${baseUrl}/sense/feedback`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(request),
        },
        timeoutMs,
      );
    },

    async getDialogueState(sessionId: string): Promise<ApiResult<DialogueState>> {
      return fetchJson<DialogueState>(
        `${baseUrl}/sense/sessions/${encodeURIComponent(sessionId)}/state`,
        { method: "GET", headers: baseHeaders },
        timeoutMs,
      );
    },

    async checkAccessibility(
      config: AccessibilityConfig,
    ): Promise<ApiResult<AccessibilityCheckResult>> {
      return fetchJson<AccessibilityCheckResult>(
        `${baseUrl}/sense/accessibility/check`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(config),
        },
        timeoutMs,
      );
    },

    async getTransparencyIndicator(options: {
      agent_id: string;
      session_id?: string;
    }): Promise<ApiResult<TransparencyIndicator>> {
      const params = new URLSearchParams();
      params.set("agent_id", options.agent_id);
      if (options.session_id !== undefined) {
        params.set("session_id", options.session_id);
      }
      return fetchJson<TransparencyIndicator>(
        `${baseUrl}/sense/transparency?${params.toString()}`,
        { method: "GET", headers: baseHeaders },
        timeoutMs,
      );
    },

    async detectContext(options: {
      user_agent: string;
      headers?: Readonly<Record<string, string>>;
    }): Promise<ApiResult<DetectedContext>> {
      return fetchJson<DetectedContext>(
        `${baseUrl}/sense/context/detect`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(options),
        },
        timeoutMs,
      );
    },

    async getFeedbackSummary(agentId: string): Promise<ApiResult<FeedbackSummary>> {
      return fetchJson<FeedbackSummary>(
        `${baseUrl}/sense/feedback/${encodeURIComponent(agentId)}/summary`,
        { method: "GET", headers: baseHeaders },
        timeoutMs,
      );
    },
  };
}

/** Re-export config type for convenience. */
export type {
  AccessibilityCheckResult,
  AccessibilityConfig,
  DetectedContext,
  DialogueState,
  FeedbackEntry,
  FeedbackSubmitRequest,
  FeedbackSummary,
  ResponseCandidate,
  TransparencyIndicator,
  UserIntent,
};
