/**
 * useAgentSense — React context + hook for global agent-sense state.
 *
 * Provides a single context that holds the current confidence, handoff,
 * disclosure, suggestions, and accessibility preferences.
 *
 * Usage:
 *   // Wrap your app:
 *   <AgentSenseProvider>
 *     <App />
 *   </AgentSenseProvider>
 *
 *   // Consume anywhere in the tree:
 *   const { confidence, setConfidence } = useAgentSense();
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import type {
  AccessibilityPreferences,
  AgentSenseContextValue,
  AIDisclosureCardData,
  ConfidenceIndicatorData,
  HandoffPackageData,
  SuggestionItem,
} from "../types.js";
import { DEFAULT_ACCESSIBILITY_PREFERENCES } from "../types.js";

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AgentSenseContext = createContext<AgentSenseContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export interface AgentSenseProviderProps {
  children: ReactNode;
  initialConfidence?: ConfidenceIndicatorData | null;
  initialHandoff?: HandoffPackageData | null;
  initialDisclosure?: AIDisclosureCardData | null;
  initialSuggestions?: readonly SuggestionItem[];
  initialAccessibility?: Partial<AccessibilityPreferences>;
}

/**
 * Provides the AgentSense context to the component tree.
 *
 * All initial* props are optional; omitting them starts with null / defaults.
 */
export function AgentSenseProvider({
  children,
  initialConfidence = null,
  initialHandoff = null,
  initialDisclosure = null,
  initialSuggestions = [],
  initialAccessibility = {},
}: AgentSenseProviderProps): ReactNode {
  const [confidence, setConfidenceState] = useState<ConfidenceIndicatorData | null>(
    initialConfidence
  );
  const [handoff, setHandoffState] = useState<HandoffPackageData | null>(
    initialHandoff
  );
  const [disclosure, setDisclosureState] =
    useState<AIDisclosureCardData | null>(initialDisclosure);
  const [suggestions, setSuggestionsState] = useState<readonly SuggestionItem[]>(
    initialSuggestions
  );
  const [accessibility, setAccessibilityState] =
    useState<AccessibilityPreferences>({
      ...DEFAULT_ACCESSIBILITY_PREFERENCES,
      ...initialAccessibility,
    });

  const setConfidence = useCallback(
    (data: ConfidenceIndicatorData | null) => setConfidenceState(data),
    []
  );
  const setHandoff = useCallback(
    (data: HandoffPackageData | null) => setHandoffState(data),
    []
  );
  const setDisclosure = useCallback(
    (data: AIDisclosureCardData | null) => setDisclosureState(data),
    []
  );
  const setSuggestions = useCallback(
    (items: readonly SuggestionItem[]) => setSuggestionsState(items),
    []
  );
  const setAccessibility = useCallback(
    (prefs: Partial<AccessibilityPreferences>) =>
      setAccessibilityState((previous) => ({ ...previous, ...prefs })),
    []
  );

  const value = useMemo<AgentSenseContextValue>(
    () => ({
      confidence,
      handoff,
      disclosure,
      suggestions,
      accessibility,
      setConfidence,
      setHandoff,
      setDisclosure,
      setSuggestions,
      setAccessibility,
    }),
    [
      confidence,
      handoff,
      disclosure,
      suggestions,
      accessibility,
      setConfidence,
      setHandoff,
      setDisclosure,
      setSuggestions,
      setAccessibility,
    ]
  );

  // Re-export JSX-compatible element via createElement so this .ts file
  // does not need the .tsx extension (JSX pragma handles it at build time).
  return React.createElement(AgentSenseContext.Provider, { value }, children);
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Returns the current AgentSense context value.
 *
 * Must be called within an <AgentSenseProvider> tree.
 *
 * @throws {Error} When called outside of AgentSenseProvider.
 */
export function useAgentSense(): AgentSenseContextValue {
  const context = useContext(AgentSenseContext);
  if (context === null) {
    throw new Error(
      "useAgentSense must be used within an <AgentSenseProvider>."
    );
  }
  return context;
}
