/**
 * SuggestionOverlay — accessible listbox dialog for contextual suggestions.
 *
 * Mirrors the Python Suggestion / SuggestionEngine data contracts from
 * agent_sense.suggestions.engine.
 *
 * Keyboard navigation:
 *   ArrowDown / ArrowUp  — move active option
 *   Home / End           — jump to first / last option
 *   Enter                — select active option
 *   Escape               — close without selecting
 *
 * ARIA: role="listbox", role="option", aria-activedescendant,
 *       aria-selected, aria-expanded on trigger (when used with one).
 *
 * Usage:
 *   <SuggestionOverlay
 *     suggestions={[{ id: "s1", label: "Reset your password", description: "Go to account settings" }]}
 *     isOpen={isOpen}
 *     onSelect={(item) => handleSelect(item)}
 *     onClose={() => setIsOpen(false)}
 *   />
 */

import React, {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import type { SuggestionItem } from "../types.js";
import { getNextListboxIndex, KEYBOARD_KEYS } from "../utils/a11y.js";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface SuggestionOverlayProps {
  /** Suggestions to display in the listbox. */
  suggestions: readonly SuggestionItem[];
  /** Called when the user selects a suggestion. */
  onSelect: (item: SuggestionItem) => void;
  /** Whether the overlay is visible. */
  isOpen: boolean;
  /** Called when the overlay should close (Escape or outside click). */
  onClose: () => void;
  /** Optional placeholder text when suggestions is empty. */
  emptyText?: string;
  /** Optional className for the overlay container. */
  className?: string;
  /** Optional additional styles for the overlay container. */
  style?: React.CSSProperties;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Renders an ARIA-compliant listbox overlay for suggestion selection.
 *
 * Manages keyboard focus internally. The caller controls open/close state
 * via isOpen / onClose.
 */
export function SuggestionOverlay({
  suggestions,
  onSelect,
  isOpen,
  onClose,
  emptyText = "No suggestions available.",
  className,
  style,
}: SuggestionOverlayProps): React.ReactElement | null {
  const [activeIndex, setActiveIndex] = useState(-1);
  const listboxRef = useRef<HTMLUListElement>(null);
  const overlayId = useId();

  // Reset active index whenever suggestions change or overlay opens.
  useEffect(() => {
    if (isOpen) {
      setActiveIndex(-1);
    }
  }, [isOpen, suggestions]);

  // Move DOM focus into the listbox when opened.
  useEffect(() => {
    if (isOpen && listboxRef.current !== null) {
      listboxRef.current.focus();
    }
  }, [isOpen]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLUListElement>) => {
      switch (event.key) {
        case KEYBOARD_KEYS.ARROW_DOWN:
        case KEYBOARD_KEYS.ARROW_UP:
        case KEYBOARD_KEYS.HOME:
        case KEYBOARD_KEYS.END: {
          event.preventDefault();
          const nextIndex = getNextListboxIndex(
            activeIndex,
            suggestions.length,
            event.key
          );
          setActiveIndex(nextIndex);
          break;
        }

        case KEYBOARD_KEYS.ENTER: {
          event.preventDefault();
          if (activeIndex >= 0) {
            const selected = suggestions[activeIndex];
            if (selected !== undefined) {
              onSelect(selected);
              onClose();
            }
          }
          break;
        }

        case KEYBOARD_KEYS.ESCAPE: {
          event.preventDefault();
          onClose();
          break;
        }

        default:
          break;
      }
    },
    [activeIndex, suggestions, onSelect, onClose]
  );

  const handleOptionClick = useCallback(
    (item: SuggestionItem, index: number) => {
      setActiveIndex(index);
      onSelect(item);
      onClose();
    },
    [onSelect, onClose]
  );

  const handleOptionMouseEnter = useCallback((index: number) => {
    setActiveIndex(index);
  }, []);

  if (!isOpen) return null;

  const activeDescendantId =
    activeIndex >= 0 ? `${overlayId}-option-${activeIndex}` : undefined;

  const overlayStyles: React.CSSProperties = {
    position: "absolute",
    zIndex: 1000,
    backgroundColor: "#ffffff",
    border: "1px solid #d0d0d0",
    borderRadius: "8px",
    boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
    padding: "4px 0",
    minWidth: "280px",
    maxHeight: "320px",
    overflowY: "auto",
    ...style,
  };

  const listStyles: React.CSSProperties = {
    listStyle: "none",
    margin: 0,
    padding: 0,
    outline: "none",
  };

  const emptyStyles: React.CSSProperties = {
    padding: "12px 16px",
    fontSize: "0.875rem",
    color: "#888",
  };

  return (
    <div style={overlayStyles} className={className}>
      {suggestions.length === 0 ? (
        <div
          role="status"
          aria-live="polite"
          style={emptyStyles}
        >
          {emptyText}
        </div>
      ) : (
        <ul
          ref={listboxRef}
          role="listbox"
          tabIndex={0}
          aria-label="Suggestions"
          aria-activedescendant={activeDescendantId}
          onKeyDown={handleKeyDown}
          style={listStyles}
        >
          {suggestions.map((item, index) => {
            const isActive = index === activeIndex;
            const optionId = `${overlayId}-option-${index}`;

            const optionStyles: React.CSSProperties = {
              display: "flex",
              flexDirection: "column",
              padding: "10px 16px",
              cursor: "pointer",
              backgroundColor: isActive ? "#f0f4ff" : "transparent",
              borderLeft: isActive ? "3px solid #4a6cf7" : "3px solid transparent",
              outline: "none",
            };

            const labelStyles: React.CSSProperties = {
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "#1a1a1a",
            };

            const descriptionStyles: React.CSSProperties = {
              fontSize: "0.75rem",
              color: "#666",
              marginTop: "2px",
            };

            return (
              <li
                key={item.id}
                id={optionId}
                role="option"
                aria-selected={isActive}
                onClick={() => handleOptionClick(item, index)}
                onMouseEnter={() => handleOptionMouseEnter(index)}
                style={optionStyles}
              >
                <span style={labelStyles}>{item.label}</span>
                {item.description !== undefined && item.description !== "" && (
                  <span style={descriptionStyles}>{item.description}</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
