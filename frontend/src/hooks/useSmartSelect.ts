/**
 * useSmartSelect - Hook for Smart Select state management
 *
 * Manages:
 * - Output mode (polygon/pixels)
 * - Polygon complexity
 * - Undo/redo history
 * - Refinement state machine
 */

import { useState, useCallback, useEffect } from 'react';
import type {
  SmartSelectOutputMode,
  SmartSelectState,
  SmartSelectHistoryEntry,
  MaskCandidate,
  PointPrompt,
  BoxPrompt,
  PolygonData,
} from '../types';
import { extractPolygonsFromMask } from '../utils/polygonExtraction';

const MAX_HISTORY_SIZE = 20;

interface UseSmartSelectOptions {
  /** Called when mask/polygon is confirmed */
  onFinish?: (mask: MaskCandidate, polygon: PolygonData | null) => void;
  /** Called when selection is deleted */
  onDelete?: () => void;
}

interface UseSmartSelectReturn {
  // State
  selectState: SmartSelectState;
  outputMode: SmartSelectOutputMode;
  polygonComplexity: number;
  currentPolygon: PolygonData | null;
  isExtractingPolygon: boolean;

  // History
  history: SmartSelectHistoryEntry[];
  historyIndex: number;
  canUndo: boolean;
  canRedo: boolean;

  // Actions
  setOutputMode: (mode: SmartSelectOutputMode) => void;
  setPolygonComplexity: (complexity: number) => void;
  setMask: (mask: MaskCandidate, points: PointPrompt[], box: BoxPrompt | null) => void;
  undo: () => SmartSelectHistoryEntry | null;
  redo: () => SmartSelectHistoryEntry | null;
  finish: () => void;
  deleteSelection: () => void;
  reset: () => void;
  transitionTo: (state: SmartSelectState) => void;
}

export function useSmartSelect(options: UseSmartSelectOptions = {}): UseSmartSelectReturn {
  const { onFinish, onDelete } = options;

  // Core state
  const [selectState, setSelectState] = useState<SmartSelectState>('idle');
  const [outputMode, setOutputMode] = useState<SmartSelectOutputMode>('pixels');
  // NOTE: Changed default to 1.0 for maximum fidelity (no simplification).
  // This ensures polygon mode matches pixel mode as closely as possible.
  // Users can still use the slider to simplify if needed.
  const [polygonComplexity, setPolygonComplexityState] = useState(1.0);

  // Current data
  const [currentMask, setCurrentMask] = useState<MaskCandidate | null>(null);
  const [currentPolygon, setCurrentPolygon] = useState<PolygonData | null>(null);
  const [isExtractingPolygon, setIsExtractingPolygon] = useState(false);

  // History for undo/redo
  const [history, setHistory] = useState<SmartSelectHistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Computed values
  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  // Extract polygon when mask changes or complexity changes (only in polygon mode)
  useEffect(() => {
    if (outputMode !== 'polygon' || !currentMask?.mask_base64) {
      setCurrentPolygon(null);
      return;
    }

    let cancelled = false;
    setIsExtractingPolygon(true);

    extractPolygonsFromMask(currentMask.mask_base64, polygonComplexity)
      .then((polygons) => {
        if (!cancelled && polygons.length > 0) {
          // Find the largest polygon for primary contour (backwards compatibility)
          const largest = polygons.reduce((a, b) => (a.area > b.area ? a : b));
          // Keep ALL contours including disjoint regions (grid bubbles, annotations)
          const allContours = polygons.map(p => ({
            points: p.points,
            area: p.area,
            perimeter: p.perimeter,
          }));
          const totalArea = polygons.reduce((sum, p) => sum + p.area, 0);

          setCurrentPolygon({
            points: largest.points,
            area: largest.area,
            perimeter: largest.perimeter,
            allContours,
            totalArea,
          });
        }
      })
      .catch((err) => {
        console.error('Polygon extraction failed:', err);
        if (!cancelled) {
          setCurrentPolygon(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsExtractingPolygon(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [outputMode, currentMask?.mask_base64, polygonComplexity]);

  // Set a new mask (pushes to history)
  const setMask = useCallback(
    (mask: MaskCandidate, points: PointPrompt[], box: BoxPrompt | null) => {
      setCurrentMask(mask);

      // Transition state
      if (selectState === 'idle') {
        setSelectState('initial');
      } else if (selectState === 'initial' || selectState === 'confirmed') {
        setSelectState('refining');
      }

      // Push to history
      const entry: SmartSelectHistoryEntry = {
        mask,
        points: [...points],
        box,
        polygon: null, // Will be computed async
        timestamp: Date.now(),
      };

      setHistory((prev) => {
        // Truncate any redo history
        const newHistory = prev.slice(0, historyIndex + 1);
        newHistory.push(entry);

        // Limit history size
        if (newHistory.length > MAX_HISTORY_SIZE) {
          return newHistory.slice(-MAX_HISTORY_SIZE);
        }
        return newHistory;
      });

      setHistoryIndex((prev) => Math.min(prev + 1, MAX_HISTORY_SIZE - 1));
    },
    [selectState, historyIndex]
  );

  // Undo - go back in history
  const undo = useCallback((): SmartSelectHistoryEntry | null => {
    if (!canUndo) return null;

    const newIndex = historyIndex - 1;
    setHistoryIndex(newIndex);

    const entry = history[newIndex];
    if (entry) {
      setCurrentMask(entry.mask);
      setSelectState('refining');
      return entry;
    }
    return null;
  }, [canUndo, historyIndex, history]);

  // Redo - go forward in history
  const redo = useCallback((): SmartSelectHistoryEntry | null => {
    if (!canRedo) return null;

    const newIndex = historyIndex + 1;
    setHistoryIndex(newIndex);

    const entry = history[newIndex];
    if (entry) {
      setCurrentMask(entry.mask);
      setSelectState('refining');
      return entry;
    }
    return null;
  }, [canRedo, historyIndex, history]);

  // Finish - confirm current selection
  const finish = useCallback(() => {
    if (!currentMask) return;

    setSelectState('confirmed');
    onFinish?.(currentMask, currentPolygon);
  }, [currentMask, currentPolygon, onFinish]);

  // Delete current selection
  const deleteSelection = useCallback(() => {
    setCurrentMask(null);
    setCurrentPolygon(null);
    setSelectState('idle');
    onDelete?.();
  }, [onDelete]);

  // Reset all state
  const reset = useCallback(() => {
    setSelectState('idle');
    setCurrentMask(null);
    setCurrentPolygon(null);
    setHistory([]);
    setHistoryIndex(-1);
  }, []);

  // Manual state transition
  const transitionTo = useCallback((state: SmartSelectState) => {
    setSelectState(state);
  }, []);

  // Update polygon complexity with debounce effect already in useEffect
  const setPolygonComplexity = useCallback((complexity: number) => {
    setPolygonComplexityState(Math.max(0, Math.min(1, complexity)));
  }, []);

  return {
    // State
    selectState,
    outputMode,
    polygonComplexity,
    currentPolygon,
    isExtractingPolygon,

    // History
    history,
    historyIndex,
    canUndo,
    canRedo,

    // Actions
    setOutputMode,
    setPolygonComplexity,
    setMask,
    undo,
    redo,
    finish,
    deleteSelection,
    reset,
    transitionTo,
  };
}

export default useSmartSelect;
