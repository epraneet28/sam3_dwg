/**
 * usePlaygroundState - Persist playground annotations per document
 *
 * Saves playground state (results, prompts, points, boxes, masks) to localStorage
 * so users can return to their work later. State is keyed by document ID.
 */

import { useEffect, useRef } from 'react';
import type { ZoneResult, PointPrompt, BoxPrompt, MaskCandidate } from '../types';

const STORAGE_KEY_PREFIX = 'sam3_playground_state_';

export interface ExperimentResult {
  id: string;
  prompts: string[];
  zones: ZoneResult[];
  processingTimeMs: number;
  timestamp: number;
}

export interface PlaygroundState {
  // Text mode state
  prompts: string[];
  results: ExperimentResult[];
  activeResultId: string | null;

  // Interactive mode state
  pointPrompts: PointPrompt[];
  boxPrompts: BoxPrompt[];
  maskCandidates: MaskCandidate[];
  selectedMaskIndex: number;
  maskInputBase64: string | null;
  /** Low-res logits for refinement (preferred over maskInputBase64) */
  maskLogitsBase64?: string | null;

  // Settings
  inputMode: 'text' | 'box' | 'points';
  confidenceThreshold: number;

  // Metadata
  savedAt: number;
}

const getStorageKey = (docId: string) => `${STORAGE_KEY_PREFIX}${docId}`;

/**
 * Save playground state for a document
 */
export function savePlaygroundState(docId: string, state: Omit<PlaygroundState, 'savedAt'>): void {
  if (!docId) return;

  const stateToSave: PlaygroundState = {
    ...state,
    savedAt: Date.now(),
  };

  try {
    localStorage.setItem(getStorageKey(docId), JSON.stringify(stateToSave));
  } catch (error) {
    console.error('Failed to save playground state:', error);
  }
}

/**
 * Load playground state for a document
 */
export function loadPlaygroundState(docId: string): PlaygroundState | null {
  if (!docId) return null;

  try {
    const stored = localStorage.getItem(getStorageKey(docId));
    if (!stored) return null;

    const parsed = JSON.parse(stored) as PlaygroundState;

    // Validate essential fields exist
    if (!parsed.savedAt || typeof parsed.savedAt !== 'number') {
      return null;
    }

    return parsed;
  } catch (error) {
    console.error('Failed to load playground state:', error);
    return null;
  }
}

/**
 * Clear playground state for a document
 */
export function clearPlaygroundState(docId: string): void {
  if (!docId) return;

  try {
    localStorage.removeItem(getStorageKey(docId));
  } catch (error) {
    console.error('Failed to clear playground state:', error);
  }
}

/**
 * Check if a document has saved playground state
 */
export function hasPlaygroundState(docId: string): boolean {
  if (!docId) return false;
  return localStorage.getItem(getStorageKey(docId)) !== null;
}

/**
 * Get all document IDs with saved playground state
 */
export function getDocumentsWithPlaygroundState(): string[] {
  const docIds: string[] = [];

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(STORAGE_KEY_PREFIX)) {
      docIds.push(key.replace(STORAGE_KEY_PREFIX, ''));
    }
  }

  return docIds;
}

interface UsePlaygroundStatePersistenceOptions {
  docId: string | null;
  prompts: string[];
  results: ExperimentResult[];
  activeResultId: string | null;
  pointPrompts: PointPrompt[];
  boxPrompts: BoxPrompt[];
  maskCandidates: MaskCandidate[];
  selectedMaskIndex: number;
  maskInputBase64: string | null;
  maskLogitsBase64?: string | null;
  inputMode: 'text' | 'box' | 'points';
  confidenceThreshold: number;
  enabled?: boolean;
}

/**
 * Hook to auto-save playground state when it changes
 */
export function usePlaygroundStatePersistence(options: UsePlaygroundStatePersistenceOptions): void {
  const {
    docId,
    prompts,
    results,
    activeResultId,
    pointPrompts,
    boxPrompts,
    maskCandidates,
    selectedMaskIndex,
    maskInputBase64,
    maskLogitsBase64,
    inputMode,
    confidenceThreshold,
    enabled = true,
  } = options;

  // Debounce save to avoid excessive writes
  const saveTimeoutRef = useRef<number | null>(null);

  // Check if there's anything worth saving
  const hasContent =
    results.length > 0 ||
    pointPrompts.length > 0 ||
    boxPrompts.length > 0 ||
    maskCandidates.length > 0 ||
    prompts.some((p) => p.trim());

  useEffect(() => {
    if (!enabled || !docId || !hasContent) return;

    // Clear any pending save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Debounce save by 1 second
    saveTimeoutRef.current = window.setTimeout(() => {
      savePlaygroundState(docId, {
        prompts,
        results,
        activeResultId,
        pointPrompts,
        boxPrompts,
        maskCandidates,
        selectedMaskIndex,
        maskInputBase64,
        maskLogitsBase64,
        inputMode,
        confidenceThreshold,
      });
    }, 1000);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [
    enabled,
    docId,
    hasContent,
    prompts,
    results,
    activeResultId,
    pointPrompts,
    boxPrompts,
    maskCandidates,
    selectedMaskIndex,
    maskInputBase64,
    maskLogitsBase64,
    inputMode,
    confidenceThreshold,
  ]);
}

/**
 * Format saved time for display
 */
export function formatSavedTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;

  // Less than 1 minute
  if (diff < 60 * 1000) {
    return 'just now';
  }

  // Less than 1 hour
  if (diff < 60 * 60 * 1000) {
    const mins = Math.floor(diff / (60 * 1000));
    return `${mins} min${mins === 1 ? '' : 's'} ago`;
  }

  // Less than 24 hours
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  }

  // More than 24 hours - show date
  const date = new Date(timestamp);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
