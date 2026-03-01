/**
 * useAccessibility — manages persistent accessibility preferences.
 *
 * Reads initial state from localStorage (keyed by storageKey prop),
 * applies document-level CSS classes on every change, and exposes
 * typed setters for each preference.
 *
 * Usage:
 *   const { preferences, setTextSize, setHighContrast, ... } = useAccessibility();
 */

import { useCallback, useEffect, useState } from "react";
import type { AccessibilityPreferences, TextSizeLevel } from "../types.js";
import {
  DEFAULT_ACCESSIBILITY_PREFERENCES,
} from "../types.js";
import {
  applyDocumentA11yClasses,
  readLocalStorage,
  writeLocalStorage,
} from "../utils/a11y.js";

export const DEFAULT_STORAGE_KEY = "aumos-agent-sense-a11y";

export interface UseAccessibilityReturn {
  preferences: AccessibilityPreferences;
  setTextSize: (size: TextSizeLevel) => void;
  setHighContrast: (enabled: boolean) => void;
  setReducedMotion: (enabled: boolean) => void;
  setFocusIndicators: (enabled: boolean) => void;
  resetPreferences: () => void;
}

/**
 * Hook that manages WCAG-oriented accessibility preferences with
 * localStorage persistence and document class synchronisation.
 *
 * @param storageKey - Key used for localStorage persistence.
 */
export function useAccessibility(
  storageKey: string = DEFAULT_STORAGE_KEY
): UseAccessibilityReturn {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(
    () => {
      const stored = readLocalStorage<AccessibilityPreferences>(storageKey);
      return stored !== null
        ? { ...DEFAULT_ACCESSIBILITY_PREFERENCES, ...stored }
        : { ...DEFAULT_ACCESSIBILITY_PREFERENCES };
    }
  );

  // Synchronise document-level classes and localStorage whenever prefs change.
  useEffect(() => {
    applyDocumentA11yClasses(preferences);
    writeLocalStorage(storageKey, preferences);
  }, [preferences, storageKey]);

  const updatePreference = useCallback(
    <K extends keyof AccessibilityPreferences>(
      key: K,
      value: AccessibilityPreferences[K]
    ) => {
      setPreferences((previous) => ({ ...previous, [key]: value }));
    },
    []
  );

  const setTextSize = useCallback(
    (size: TextSizeLevel) => updatePreference("textSize", size),
    [updatePreference]
  );

  const setHighContrast = useCallback(
    (enabled: boolean) => updatePreference("highContrast", enabled),
    [updatePreference]
  );

  const setReducedMotion = useCallback(
    (enabled: boolean) => updatePreference("reducedMotion", enabled),
    [updatePreference]
  );

  const setFocusIndicators = useCallback(
    (enabled: boolean) => updatePreference("focusIndicators", enabled),
    [updatePreference]
  );

  const resetPreferences = useCallback(() => {
    setPreferences({ ...DEFAULT_ACCESSIBILITY_PREFERENCES });
  }, []);

  return {
    preferences,
    setTextSize,
    setHighContrast,
    setReducedMotion,
    setFocusIndicators,
    resetPreferences,
  };
}
