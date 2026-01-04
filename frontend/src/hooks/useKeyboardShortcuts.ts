/**
 * Custom hook for keyboard shortcut handling
 * Supports platform-specific modifiers (Cmd on Mac, Ctrl elsewhere)
 */
import { useEffect, useRef } from 'react';

export interface ShortcutConfig {
  key: string;
  handler: () => void;
  description: string;
  requireCtrl?: boolean;
  requireShift?: boolean;
  preventDefault?: boolean;
}

/**
 * Registers global keyboard shortcuts with automatic cleanup
 *
 * @param shortcuts - Array of shortcut configurations
 * @param enabled - Whether shortcuts are active (default: true)
 *
 * @example
 * useKeyboardShortcuts([
 *   {
 *     key: 'Escape',
 *     handler: () => setSelected(null),
 *     description: 'Deselect',
 *   },
 *   {
 *     key: 'ArrowLeft',
 *     handler: () => goToPreviousPage(),
 *     description: 'Previous page',
 *     preventDefault: true,
 *   },
 * ]);
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutConfig[],
  enabled: boolean = true
): void {
  // Use ref to avoid recreating listener on every shortcut change
  const shortcutsRef = useRef(shortcuts);

  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      for (const shortcut of shortcutsRef.current) {
        // Handle Mac Cmd key as Ctrl for cross-platform compatibility
        const platformCtrl = /mac|iphone|ipad/i.test(navigator.platform)
          ? e.metaKey
          : e.ctrlKey;

        const ctrlMatch = !shortcut.requireCtrl || platformCtrl;
        const shiftMatch = !shortcut.requireShift || e.shiftKey;
        const keyMatch =
          e.key === shortcut.key ||
          e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (keyMatch && ctrlMatch && shiftMatch) {
          if (shortcut.preventDefault) {
            e.preventDefault();
          }

          try {
            shortcut.handler();
          } catch (error) {
            console.error('Keyboard shortcut handler error:', error);
          }

          // Stop after first match
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled]); // Only re-attach when enabled changes
}
