/**
 * Playground - Experiment with SAM3 input modes on uploaded images
 *
 * Supports all 6 SAM3 input modalities:
 * 1. Text Prompts (PCS) - working
 * 2. Bounding Box (PVS) - working
 * 3. Point Prompts (PVS) - working
 * 4. Mask Prompts - working (use existing mask for refinement)
 * 5. Visual Exemplars - planned
 * 6. Combined Mode - planned
 */

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlayIcon,
  ArrowPathIcon,
  ChatBubbleBottomCenterTextIcon,
  Square2StackIcon,
  CursorArrowRaysIcon,
  XMarkIcon,
  PlusIcon,
  MinusIcon,
  TrashIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';
import { useDocuments } from '../store';
import { api } from '../api/client';
import { PlaygroundCanvas, SmartSelectPanel } from '../components/playground';
import { DrawingCanvas } from '../components/viewer';
import { MinimalTopBar, ControlsHint, ConfidenceSlider } from '../components/shared';
import { useZoomPan } from '../hooks/useZoomPan';
import { useSmartSelect } from '../hooks/useSmartSelect';
import {
  usePlaygroundStatePersistence,
  loadPlaygroundState,
  clearPlaygroundState,
  hasPlaygroundState,
  formatSavedTime,
  type ExperimentResult,
} from '../hooks/usePlaygroundState';
import { getZoneColor } from '../utils/constants';
import type {
  PointPrompt,
  BoxPrompt,
  PointPromptMode,
  BoxPromptMode,
  MaskCandidate,
  SimilarRegion,
} from '../types';

type InputMode = 'text' | 'box' | 'points';

export default function Playground() {
  const navigate = useNavigate();
  const documents = useDocuments();

  // Document selection
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  // Input mode
  const [inputMode, setInputMode] = useState<InputMode>('text');

  // Text prompts state
  const [prompts, setPrompts] = useState<string[]>(['']);

  // Inference settings
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.3);

  // Results
  const [results, setResults] = useState<ExperimentResult[]>([]);
  const [activeResultId, setActiveResultId] = useState<string | null>(null);

  // Execution state
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Zone interaction state
  const [hoveredZoneId, setHoveredZoneId] = useState<string | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);

  // Display settings
  const [showMasks, setShowMasks] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Image dimensions for zoom/pan
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(null);

  // Point prompts state (PVS mode)
  const [pointPrompts, setPointPrompts] = useState<PointPrompt[]>([]);
  const [pointPromptMode, setPointPromptMode] = useState<PointPromptMode>('positive');

  // Box prompts state (PVS mode)
  const [boxPrompts, setBoxPrompts] = useState<BoxPrompt[]>([]);
  const [boxMode, setBoxMode] = useState<BoxPromptMode>('single');

  // Auto-run inference when prompts change (opt-in)
  const [autoRun, setAutoRun] = useState(false);
  const autoRunTimeoutRef = useRef<number | null>(null);

  // Interactive segmentation results (for point/box modes)
  const [maskCandidates, setMaskCandidates] = useState<MaskCandidate[]>([]);
  const [selectedMaskIndex, setSelectedMaskIndex] = useState<number>(0);

  // Mask input for refinement (Input Type 4)
  // Prefer low-res logits (maskLogitsBase64) over binarized mask (maskInputBase64) for better quality
  const [maskInputBase64, setMaskInputBase64] = useState<string | null>(null);
  const [maskLogitsBase64, setMaskLogitsBase64] = useState<string | null>(null);

  // Smart Select state (Roboflow-style features)
  const [smartSelectOpen, setSmartSelectOpen] = useState(false);
  const smartSelect = useSmartSelect({
    onFinish: (mask, polygon) => {
      console.log('Selection confirmed:', { mask, polygon });
      // Could save annotation here
    },
    onDelete: () => {
      setMaskCandidates([]);
      setSelectedMaskIndex(0);
    },
  });

  // Find Similar state
  const [similarRegions, setSimilarRegions] = useState<SimilarRegion[]>([]);
  const [selectedSimilarIndex, setSelectedSimilarIndex] = useState<number | null>(null);
  const [isFindingSimilar, setIsFindingSimilar] = useState(false);

  // Saved state tracking
  const [savedStateTimestamp, setSavedStateTimestamp] = useState<number | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Zoom/pan controls (matching Viewer)
  const {
    zoom,
    pan,
    isPanning,
    isZooming,
    handlePanStart,
    handlePanMove,
    handlePanEnd,
    handleDoubleClick,
    containerRef,
  } = useZoomPan({ imageDimensions });

  // Get active result zones
  const activeResult = useMemo(() => {
    return results.find((r) => r.id === activeResultId) || null;
  }, [results, activeResultId]);

  const activeZones = useMemo(() => {
    if (!activeResult) return [];
    return activeResult.zones.filter((z) => z.confidence >= confidenceThreshold);
  }, [activeResult, confidenceThreshold]);

  // Selected mask for interactive modes
  const selectedMask = useMemo(() => {
    if (maskCandidates.length === 0) return null;
    return maskCandidates[selectedMaskIndex] || null;
  }, [maskCandidates, selectedMaskIndex]);

  // Filter documents to segmented ones
  const segmentedDocs = useMemo(() => {
    return documents.filter((d) => d.status === 'segmented');
  }, [documents]);

  // Track which documents have saved playground state
  const docsWithSavedState = useMemo(() => {
    const set = new Set<string>();
    segmentedDocs.forEach((doc) => {
      if (hasPlaygroundState(doc.id)) {
        set.add(doc.id);
      }
    });
    return set;
  }, [segmentedDocs]);

  // Auto-save playground state
  usePlaygroundStatePersistence({
    docId: selectedDocId,
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
    enabled: true,
  });

  // Handle document selection - load saved state if exists
  const handleSelectDocument = useCallback(async (docId: string) => {
    setSelectedDocId(docId);
    setError(null);
    setShowClearConfirm(false);

    // Load image from backend storage
    try {
      const url = await api.getPageImageUrl(docId, 0);
      setImageUrl(url);
    } catch (err) {
      console.error('Failed to load document image:', err);
      setError('Failed to load document image');
      return;
    }

    // Try to load saved playground state for this document
    const savedState = loadPlaygroundState(docId);
    if (savedState) {
      // Restore saved state
      setPrompts(savedState.prompts.length > 0 ? savedState.prompts : ['']);
      setResults(savedState.results || []);
      setActiveResultId(savedState.activeResultId);
      setPointPrompts(savedState.pointPrompts || []);
      setBoxPrompts(savedState.boxPrompts || []);
      setMaskCandidates(savedState.maskCandidates || []);
      setSelectedMaskIndex(savedState.selectedMaskIndex || 0);
      setMaskInputBase64(savedState.maskInputBase64 || null);
      setMaskLogitsBase64(savedState.maskLogitsBase64 || null);
      setInputMode(savedState.inputMode || 'text');
      setConfidenceThreshold(savedState.confidenceThreshold ?? 0.3);
      setSavedStateTimestamp(savedState.savedAt);
    } else {
      // Reset to defaults
      setPrompts(['']);
      setResults([]);
      setActiveResultId(null);
      setPointPrompts([]);
      setBoxPrompts([]);
      setMaskCandidates([]);
      setSelectedMaskIndex(0);
      setMaskInputBase64(null);
      setMaskLogitsBase64(null);
      setSavedStateTimestamp(null);
    }
  }, []);

  // Prompt management
  const handleAddPrompt = useCallback(() => {
    setPrompts((prev) => [...prev, '']);
  }, []);

  const handleUpdatePrompt = useCallback((index: number, value: string) => {
    setPrompts((prev) => {
      const newPrompts = [...prev];
      newPrompts[index] = value;
      return newPrompts;
    });
  }, []);

  const handleRemovePrompt = useCallback((index: number) => {
    setPrompts((prev) => {
      if (prev.length === 1) return prev;
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  // Run segmentation
  const handleRun = useCallback(async () => {
    if (!selectedDocId || inputMode !== 'text') return;

    const activePrompts = prompts.filter((p) => p.trim());
    if (activePrompts.length === 0) {
      setError('Enter at least one prompt');
      return;
    }

    setRunning(true);
    setError(null);

    try {
      // Use imageUrl which is already loaded from backend storage
      if (!imageUrl) {
        throw new Error('Image not loaded');
      }

      // Call segment endpoint with custom prompts
      const result = await api.segmentWithPrompts(imageUrl, activePrompts, confidenceThreshold);

      const newResult: ExperimentResult = {
        id: `result_${Date.now()}`,
        prompts: activePrompts,
        zones: result.zones,
        processingTimeMs: result.processing_time_ms,
        timestamp: Date.now(),
      };

      setResults((prev) => [newResult, ...prev]);
      setActiveResultId(newResult.id);
      // Clear "restored from" indicator since we have new results
      setSavedStateTimestamp(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Segmentation failed');
      console.error('Playground run failed:', err);
    } finally {
      setRunning(false);
    }
  }, [selectedDocId, imageUrl, inputMode, prompts, confidenceThreshold]);

  // Quick prompt templates
  const quickPrompts = [
    'title block',
    'floor plan',
    'elevation',
    'section',
    'detail',
    'schedule',
    'legend',
    'notes',
  ];

  const handleQuickPrompt = useCallback((prompt: string) => {
    setPrompts((prev) => {
      const emptyIdx = prev.findIndex((p) => !p.trim());
      if (emptyIdx >= 0) {
        const newPrompts = [...prev];
        newPrompts[emptyIdx] = prompt;
        return newPrompts;
      }
      return [...prev, prompt];
    });
  }, []);

  // Point prompt handlers
  const handleAddPoint = useCallback((point: PointPrompt) => {
    setPointPrompts((prev) => [...prev, point]);
    setMaskCandidates([]); // Clear previous results
    setSelectedMaskIndex(0);
  }, []);

  // Refinement click handler - adds point and auto-runs with mask input
  const handleRefinementClick = useCallback(
    async (point: PointPrompt, isInsideMask: boolean) => {
      // Use current mask as input for refinement
      const currentMask = maskCandidates[selectedMaskIndex];
      if (!currentMask?.mask_base64) return;

      // Add the new point to existing points
      const newPoints = [...pointPrompts, point];
      setPointPrompts(newPoints);

      // Prefer low-res logits for refinement (better quality than binarized mask)
      const hasLogits = !!currentMask.low_res_logits_base64;
      if (hasLogits) {
        setMaskLogitsBase64(currentMask.low_res_logits_base64!);
        setMaskInputBase64(null);
      } else {
        setMaskInputBase64(currentMask.mask_base64);
        setMaskLogitsBase64(null);
      }

      // Log the action for debugging
      console.log(`Refinement: ${isInsideMask ? 'Remove (inside)' : 'Add (outside)'} at (${Math.round(point.x)}, ${Math.round(point.y)}), using ${hasLogits ? 'logits' : 'binarized mask'}`);

      // Auto-run inference with the new point and mask input
      if (!imageUrl) return;

      setRunning(true);
      setError(null);

      try {
        const result = await api.segmentInteractive(imageUrl, {
          points: newPoints.map((p) => ({ x: p.x, y: p.y, label: p.label })),
          // Prefer logits over binarized mask for higher quality refinement
          maskLogits: currentMask.low_res_logits_base64 || undefined,
          maskInput: currentMask.low_res_logits_base64 ? undefined : currentMask.mask_base64,
          // Send doc_id for debug logging
          docId: selectedDocId || undefined,
        });

        // Sort masks by iou_score descending so highest confidence is first
        const sortedMasks = [...result.masks].sort((a, b) => b.iou_score - a.iou_score);
        setMaskCandidates(sortedMasks);
        setSelectedMaskIndex(0);

        // Sync with Smart Select
        if (sortedMasks.length > 0) {
          smartSelect.setMask(sortedMasks[0], newPoints, null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Refinement failed');
        console.error('Refinement failed:', err);
      } finally {
        setRunning(false);
      }
    },
    [imageUrl, maskCandidates, selectedMaskIndex, pointPrompts, smartSelect]
  );

  const handleRemovePoint = useCallback((id: string) => {
    setPointPrompts((prev) => prev.filter((p) => p.id !== id));
    setMaskCandidates([]); // Clear results when points change
    setSelectedMaskIndex(0);
  }, []);

  const handleClearPoints = useCallback(() => {
    setPointPrompts([]);
    setMaskCandidates([]);
    setSelectedMaskIndex(0);
  }, []);

  // Box prompt handlers
  const handleAddBox = useCallback((box: BoxPrompt) => {
    setBoxPrompts((prev) => {
      // Single mode: replace all boxes with new one
      if (boxMode === 'single') {
        return [box];
      }
      // Multi mode: append to existing boxes
      return [...prev, box];
    });
    setMaskCandidates([]); // Clear previous results
    setSelectedMaskIndex(0);
  }, [boxMode]);

  const handleRemoveBox = useCallback((id: string) => {
    setBoxPrompts((prev) => prev.filter((b) => b.id !== id));
    setMaskCandidates([]);
    setSelectedMaskIndex(0);
  }, []);

  const handleClearBoxes = useCallback(() => {
    setBoxPrompts([]);
    setMaskCandidates([]);
    setSelectedMaskIndex(0);
  }, []);

  // Mask input handlers (Input Type 4 - Mask Prompts)
  const handleUseMaskAsInput = useCallback(() => {
    if (maskCandidates.length > 0 && selectedMaskIndex < maskCandidates.length) {
      const selectedMask = maskCandidates[selectedMaskIndex];
      // Prefer low-res logits for better quality refinement
      if (selectedMask.low_res_logits_base64) {
        setMaskLogitsBase64(selectedMask.low_res_logits_base64);
        setMaskInputBase64(null);
      } else {
        setMaskInputBase64(selectedMask.mask_base64);
        setMaskLogitsBase64(null);
      }
    }
  }, [maskCandidates, selectedMaskIndex]);

  const handleClearMaskInput = useCallback(() => {
    setMaskInputBase64(null);
    setMaskLogitsBase64(null);
  }, []);

  // Clear all annotations (unified clear for all modes)
  const handleClearAllAnnotations = useCallback(() => {
    // Clear text mode state
    setPrompts(['']);
    setResults([]);
    setActiveResultId(null);
    // Clear point prompts
    setPointPrompts([]);
    // Clear box prompts
    setBoxPrompts([]);
    // Clear mask candidates and selection
    setMaskCandidates([]);
    setSelectedMaskIndex(0);
    // Clear mask input for refinement (both binarized and logits)
    setMaskInputBase64(null);
    setMaskLogitsBase64(null);
    // Clear similar regions
    setSimilarRegions([]);
    setSelectedSimilarIndex(null);
    // Clear any error
    setError(null);
    // Clear saved state timestamp indicator
    setSavedStateTimestamp(null);
    // Clear saved state from localStorage
    if (selectedDocId) {
      clearPlaygroundState(selectedDocId);
    }
    // Close confirmation dialog
    setShowClearConfirm(false);
  }, [selectedDocId]);

  // Find Similar handler
  const handleFindSimilar = useCallback(async () => {
    const selectedMask = maskCandidates[selectedMaskIndex];
    if (!selectedMask || !imageUrl || !selectedDocId) return;

    // Store the exemplar mask so we can restore it when user clicks "Exemplar"
    setExemplarMask(selectedMask);

    setIsFindingSimilar(true);
    setSimilarRegions([]);
    setSelectedSimilarIndex(-1); // Start with exemplar selected

    try {
      const response = await api.segmentFindSimilar(
        imageUrl,
        selectedMask.mask_base64,
        {
          exemplarBbox: selectedMask.bbox as [number, number, number, number],
          maxResults: 10,
          docId: selectedDocId,
        }
      );

      setSimilarRegions(response.regions);

      if (response.regions.length > 0) {
        console.log(
          `Found ${response.regions.length} similar regions in ${response.processing_time_ms.toFixed(0)}ms`
        );
      } else {
        console.log('No similar regions found');
      }
    } catch (err) {
      console.error('Find similar failed:', err);
      setError(err instanceof Error ? err.message : 'Find similar failed');
    } finally {
      setIsFindingSimilar(false);
    }
  }, [maskCandidates, selectedMaskIndex, imageUrl, selectedDocId]);

  // Store the exemplar mask when Find Similar is called
  const [exemplarMask, setExemplarMask] = useState<MaskCandidate | null>(null);

  // Handle selecting a similar region (or exemplar with index -1)
  const handleSelectSimilarRegion = useCallback(
    (index: number) => {
      // Handle exemplar selection (index -1)
      if (index === -1) {
        setSelectedSimilarIndex(-1);
        // Restore the exemplar mask
        if (exemplarMask) {
          setMaskCandidates([exemplarMask]);
          setSelectedMaskIndex(0);
        }
        return;
      }

      if (index < 0 || index >= similarRegions.length) return;

      setSelectedSimilarIndex(index);

      // Convert similar region to mask candidate format for display
      const region = similarRegions[index];
      const asMaskCandidate: MaskCandidate = {
        mask_base64: region.mask_base64,
        iou_score: region.iou_score ?? region.similarity_score,
        bbox: region.bbox,
        low_res_logits_base64: region.low_res_logits_base64,
      };

      // Add to mask candidates for selection/refinement
      setMaskCandidates([asMaskCandidate]);
      setSelectedMaskIndex(0);
    },
    [similarRegions, exemplarMask]
  );

  // Run interactive segmentation for points/box modes
  const handleRunInteractive = useCallback(async () => {
    if (!selectedDocId) return;

    // Use imageUrl which is already loaded from backend storage
    if (!imageUrl) {
      setError('Image not loaded');
      return;
    }

    setRunning(true);
    setError(null);

    try {
      // Build options for interactive segmentation
      const options: {
        points?: Array<{ x: number; y: number; label: 0 | 1 }>;
        box?: [number, number, number, number];
        boxes?: Array<[number, number, number, number]>;
        maskInput?: string;
        maskLogits?: string;
      } = {};

      // Add point prompts if in points mode
      if (inputMode === 'points' && pointPrompts.length > 0) {
        options.points = pointPrompts.map((p) => ({
          x: p.x,
          y: p.y,
          label: p.label,
        }));
      }

      // Add box prompt(s) if in box mode
      if (inputMode === 'box' && boxPrompts.length > 0) {
        if (boxPrompts.length === 1) {
          // Single box mode - use 'box' field
          const box = boxPrompts[0];
          options.box = [box.x1, box.y1, box.x2, box.y2];
        } else {
          // Multi-box mode - use 'boxes' field for merged segmentation
          options.boxes = boxPrompts.map(box => [box.x1, box.y1, box.x2, box.y2] as [number, number, number, number]);
        }
      }

      // Add mask input if available (for refinement)
      // Prefer logits over binarized mask for better quality
      if (maskLogitsBase64) {
        options.maskLogits = maskLogitsBase64;
      } else if (maskInputBase64) {
        options.maskInput = maskInputBase64;
      }

      // Validate that at least one prompt type is provided
      if (!options.points && !options.box && !options.boxes) {
        setError('Add points or draw a box to segment');
        setRunning(false);
        return;
      }

      // Call unified interactive segmentation API
      const result = await api.segmentInteractive(imageUrl, {
        ...options,
        // Send doc_id for debug logging
        docId: selectedDocId || undefined,
      });
      // Sort masks by iou_score descending so highest confidence is first
      const sortedMasks = [...result.masks].sort((a, b) => b.iou_score - a.iou_score);
      setMaskCandidates(sortedMasks);
      setSelectedMaskIndex(0);
      // Clear "restored from" indicator since we have new results
      setSavedStateTimestamp(null);

      // Sync with Smart Select for undo/redo tracking
      if (sortedMasks.length > 0) {
        smartSelect.setMask(
          sortedMasks[0],
          pointPrompts,
          boxPrompts.length > 0 ? boxPrompts[boxPrompts.length - 1] : null
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Interactive segmentation failed');
      console.error('Interactive segmentation failed:', err);
    } finally {
      setRunning(false);
    }
  }, [selectedDocId, imageUrl, inputMode, pointPrompts, boxPrompts, maskInputBase64, maskLogitsBase64]);

  // Keyboard shortcut for clearing annotations (Escape key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape key clears all annotations in interactive modes
      if (e.key === 'Escape' && (inputMode === 'points' || inputMode === 'box')) {
        // Don't clear if user is typing in an input
        if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
          return;
        }
        handleClearAllAnnotations();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [inputMode, handleClearAllAnnotations]);

  // Auto-run effect with debounce (only for interactive modes when enabled)
  useEffect(() => {
    // Only auto-run for interactive modes when enabled
    if (!autoRun || running || !selectedDocId) return;
    if (inputMode === 'text') return; // Text mode should not auto-run

    // Check if there are prompts to run
    const hasPrompts =
      (inputMode === 'points' && pointPrompts.length > 0) ||
      (inputMode === 'box' && boxPrompts.length > 0);

    if (!hasPrompts) return;

    // Clear any existing timeout
    if (autoRunTimeoutRef.current) {
      clearTimeout(autoRunTimeoutRef.current);
    }

    // Debounce: wait 500ms after last change before running
    autoRunTimeoutRef.current = window.setTimeout(() => {
      handleRunInteractive();
    }, 500);

    return () => {
      if (autoRunTimeoutRef.current) {
        clearTimeout(autoRunTimeoutRef.current);
      }
    };
  }, [autoRun, running, selectedDocId, inputMode, pointPrompts, boxPrompts, handleRunInteractive]);

  // Mode descriptions
  const modeInfo = {
    text: {
      icon: ChatBubbleBottomCenterTextIcon,
      label: 'Text Prompts',
      description: 'Describe what to find using natural language',
      available: true,
    },
    box: {
      icon: Square2StackIcon,
      label: 'Bounding Box',
      description: 'Draw a box around an example to find similar',
      available: true,
    },
    points: {
      icon: CursorArrowRaysIcon,
      label: 'Point Prompts',
      description: 'Click positive/negative points to guide detection',
      available: true,
    },
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      {/* Top Bar */}
      <MinimalTopBar
        title="Playground"
        subtitle="Experiment with SAM3 input modes"
        onBack={() => navigate('/')}
        centerContent={
          <select
            value={selectedDocId || ''}
            onChange={(e) => handleSelectDocument(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500 w-full min-w-[200px] max-w-[350px]"
            title="Select document"
          >
            <option value="">Select a document...</option>
            {segmentedDocs.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {docsWithSavedState.has(doc.id) ? '● ' : ''}{doc.name}
              </option>
            ))}
          </select>
        }
        actions={
          <button
            onClick={() => setShowClearConfirm(true)}
            disabled={
              results.length === 0 &&
              pointPrompts.length === 0 &&
              boxPrompts.length === 0 &&
              maskCandidates.length === 0 &&
              !maskInputBase64 &&
              prompts.every((p) => !p.trim())
            }
            className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-slate-700/50 disabled:text-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
            title="Clear all annotations"
          >
            <TrashIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Clear All</span>
          </button>
        }
      />

      {/* Main Content Area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Canvas Area - Use PlaygroundCanvas for interactive modes, DrawingCanvas for text mode */}
        {imageUrl ? (
          inputMode === 'text' ? (
            <DrawingCanvas
              imageUrl={imageUrl}
              zones={activeZones}
              zoom={zoom}
              pan={pan}
              isPanning={isPanning}
              isZooming={isZooming}
              hoveredZoneId={hoveredZoneId}
              selectedZoneId={selectedZoneId}
              showMasks={showMasks}
              onZoneClick={setSelectedZoneId}
              onZoneHover={setHoveredZoneId}
              onPanStart={handlePanStart}
              onPanMove={handlePanMove}
              onPanEnd={handlePanEnd}
              onDoubleClick={handleDoubleClick}
              onImageLoad={setImageDimensions}
              containerRef={containerRef}
            />
          ) : (
            <PlaygroundCanvas
              imageUrl={imageUrl}
              zones={activeZones}
              zoom={zoom}
              pan={pan}
              isPanning={isPanning}
              isZooming={isZooming}
              hoveredZoneId={hoveredZoneId}
              selectedZoneId={selectedZoneId}
              showMasks={showMasks}
              onZoneClick={setSelectedZoneId}
              onZoneHover={setHoveredZoneId}
              onPanStart={handlePanStart}
              onPanMove={handlePanMove}
              onPanEnd={handlePanEnd}
              onDoubleClick={handleDoubleClick}
              onImageLoad={setImageDimensions}
              containerRef={containerRef}
              inputMode={inputMode}
              pointPrompts={pointPrompts}
              boxPrompts={boxPrompts}
              pointPromptMode={pointPromptMode}
              imageDimensions={imageDimensions}
              onAddPoint={handleAddPoint}
              onRemovePoint={handleRemovePoint}
              onAddBox={handleAddBox}
              onRemoveBox={handleRemoveBox}
              selectedMask={selectedMask}
              exemplarMask={exemplarMask}
              showExemplarMask={similarRegions.length > 0 && selectedSimilarIndex !== -1}
              displayMode={smartSelect.outputMode}
              polygon={smartSelect.currentPolygon}
              selectState={smartSelect.selectState}
              onRefinementClick={handleRefinementClick}
            />
          )
        ) : (
          <div className="flex items-center justify-center h-full bg-slate-950">
            <div className="text-center text-slate-500">
              <Square2StackIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Select a document to start</p>
              <p className="text-sm mt-2">
                Choose a processed document from the dropdown above
              </p>
            </div>
          </div>
        )}

        <ControlsHint />

        {/* Left Side Panels Container */}
        {selectedDocId && (
          <div className="absolute top-4 left-4 w-80 z-40 flex flex-col gap-3">
            {/* Input Modes Panel */}
            <div className="bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
            {/* Mode Tabs */}
            <div className="flex border-b border-slate-700">
              {(Object.keys(modeInfo) as InputMode[]).map((mode) => {
                const info = modeInfo[mode];
                const Icon = info.icon;
                const isActive = inputMode === mode;

                return (
                  <button
                    key={mode}
                    onClick={() => info.available && setInputMode(mode)}
                    disabled={!info.available}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border-b-2 border-blue-500'
                        : info.available
                        ? 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                        : 'text-slate-600 cursor-not-allowed'
                    }`}
                    title={info.available ? info.label : `${info.label} (Coming Soon)`}
                  >
                    <Icon className="w-4 h-4" />
                    {mode === 'text' ? 'Text' : mode === 'box' ? 'Box' : 'Points'}
                    {!info.available && (
                      <span className="text-[10px] text-amber-500">Soon</span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Mode Content */}
            <div className="p-4">
              {inputMode === 'text' && (
                <div className="space-y-3">
                  {/* Prompt inputs */}
                  <div className="space-y-2">
                    {prompts.map((prompt, idx) => (
                      <div key={idx} className="flex gap-2">
                        <input
                          type="text"
                          value={prompt}
                          onChange={(e) => handleUpdatePrompt(idx, e.target.value)}
                          placeholder={`Prompt ${idx + 1}...`}
                          className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleRun();
                            }
                          }}
                        />
                        {prompts.length > 1 && (
                          <button
                            onClick={() => handleRemovePrompt(idx)}
                            className="p-2 text-slate-500 hover:text-red-400 transition-colors"
                          >
                            <XMarkIcon className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Add prompt button */}
                  <button
                    onClick={handleAddPrompt}
                    className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    <PlusIcon className="w-3.5 h-3.5" />
                    Add prompt
                  </button>

                  {/* Quick prompts */}
                  <div>
                    <label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1.5">
                      Quick add
                    </label>
                    <div className="flex flex-wrap gap-1">
                      {quickPrompts.map((qp) => (
                        <button
                          key={qp}
                          onClick={() => handleQuickPrompt(qp)}
                          className="px-2 py-0.5 text-xs bg-slate-700/50 hover:bg-slate-700 text-slate-400 hover:text-white rounded transition-colors"
                        >
                          {qp}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {inputMode === 'box' && (
                <div className="space-y-3">
                  {/* Box mode toggle */}
                  <div>
                    <label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1.5">
                      Box mode
                    </label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setBoxMode('single')}
                        className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          boxMode === 'single'
                            ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                            : 'bg-slate-700/50 text-slate-400 border border-slate-600 hover:bg-slate-700'
                        }`}
                      >
                        Single
                      </button>
                      <button
                        onClick={() => setBoxMode('multi')}
                        className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          boxMode === 'multi'
                            ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                            : 'bg-slate-700/50 text-slate-400 border border-slate-600 hover:bg-slate-700'
                        }`}
                      >
                        Multi
                      </button>
                    </div>
                  </div>

                  {/* Instructions */}
                  <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-700">
                    <p className="text-xs text-slate-300 font-medium">Draw a box on the canvas</p>
                    <p className="text-[11px] text-slate-500 mt-1">
                      {boxMode === 'single'
                        ? 'Each new box replaces the previous one.'
                        : 'Draw multiple boxes to segment. Click and drag to draw.'}
                    </p>
                  </div>

                  {/* Auto-run toggle */}
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-slate-400">Auto-run</label>
                    <button
                      onClick={() => setAutoRun(!autoRun)}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        autoRun ? 'bg-blue-600' : 'bg-slate-600'
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          autoRun ? 'translate-x-4' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Current boxes */}
                  {boxPrompts.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-[10px] uppercase tracking-wide text-slate-500">
                          Boxes ({boxPrompts.length})
                        </label>
                        <button
                          onClick={handleClearBoxes}
                          className="text-[10px] text-red-400 hover:text-red-300"
                        >
                          Clear all
                        </button>
                      </div>
                      {boxPrompts.map((box, idx) => (
                        <div
                          key={box.id}
                          className="flex items-center justify-between px-2 py-1.5 bg-slate-700/50 rounded text-xs"
                        >
                          <span className="text-slate-300">
                            Box {idx + 1}: {Math.round(box.x2 - box.x1)} × {Math.round(box.y2 - box.y1)} px
                          </span>
                          <button
                            onClick={() => handleRemoveBox(box.id)}
                            className="p-0.5 text-slate-500 hover:text-red-400"
                          >
                            <XMarkIcon className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {boxPrompts.length === 0 && (
                    <div className="text-center py-4 text-xs text-slate-500">
                      No boxes drawn yet
                    </div>
                  )}
                </div>
              )}

              {inputMode === 'points' && (
                <div className="space-y-3">
                  {/* Point mode toggle */}
                  <div>
                    <label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1.5">
                      Click to add
                    </label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setPointPromptMode('positive')}
                        className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          pointPromptMode === 'positive'
                            ? 'bg-green-600/20 text-green-400 border border-green-500/50'
                            : 'bg-slate-700/50 text-slate-400 border border-slate-600 hover:bg-slate-700'
                        }`}
                      >
                        <PlusIcon className="w-3.5 h-3.5" />
                        Positive
                      </button>
                      <button
                        onClick={() => setPointPromptMode('negative')}
                        className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          pointPromptMode === 'negative'
                            ? 'bg-red-600/20 text-red-400 border border-red-500/50'
                            : 'bg-slate-700/50 text-slate-400 border border-slate-600 hover:bg-slate-700'
                        }`}
                      >
                        <MinusIcon className="w-3.5 h-3.5" />
                        Negative
                      </button>
                    </div>
                  </div>

                  {/* Instructions */}
                  <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-700">
                    <p className="text-xs text-slate-300 font-medium">Click on the canvas</p>
                    <p className="text-[11px] text-slate-500 mt-1">
                      <span className="text-green-400">Positive</span> points include regions,{' '}
                      <span className="text-red-400">negative</span> points exclude them.
                    </p>
                  </div>

                  {/* Auto-run toggle */}
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-slate-400">Auto-run</label>
                    <button
                      onClick={() => setAutoRun(!autoRun)}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        autoRun ? 'bg-blue-600' : 'bg-slate-600'
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          autoRun ? 'translate-x-4' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Current points */}
                  {pointPrompts.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-[10px] uppercase tracking-wide text-slate-500">
                          Points ({pointPrompts.length})
                        </label>
                        <button
                          onClick={handleClearPoints}
                          className="text-[10px] text-red-400 hover:text-red-300"
                        >
                          Clear all
                        </button>
                      </div>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {pointPrompts.map((point) => (
                          <div
                            key={point.id}
                            className="flex items-center justify-between px-2 py-1.5 bg-slate-700/50 rounded text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  point.label === 1 ? 'bg-green-500' : 'bg-red-500'
                                }`}
                              />
                              <span className="text-slate-300">
                                ({Math.round(point.x)}, {Math.round(point.y)})
                              </span>
                            </div>
                            <button
                              onClick={() => handleRemovePoint(point.id)}
                              className="p-0.5 text-slate-500 hover:text-red-400"
                            >
                              <XMarkIcon className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {pointPrompts.length === 0 && (
                    <div className="text-center py-4 text-xs text-slate-500">
                      No points added yet
                    </div>
                  )}
                </div>
              )}

              {/* Action buttons */}
              <div className="mt-4 flex gap-2">
                <button
                  onClick={inputMode === 'text' ? handleRun : handleRunInteractive}
                  disabled={
                    running ||
                    !selectedDocId ||
                    (inputMode === 'text' && prompts.every((p) => !p.trim())) ||
                    (inputMode === 'points' && pointPrompts.length === 0) ||
                    (inputMode === 'box' && boxPrompts.length === 0)
                  }
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg font-medium transition-colors"
                >
                  {running ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4" />
                      Run
                    </>
                  )}
                </button>
              </div>

              {/* Error message */}
              {error && (
                <div className="mt-3 p-2 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-xs">
                  {error}
                </div>
              )}
            </div>
            </div>

            {/* Smart Select Panel (shown in interactive modes when masks are available) */}
            {(inputMode === 'points' || inputMode === 'box') && (
              <SmartSelectPanel
                isOpen={smartSelectOpen || maskCandidates.length > 0}
                onClose={() => setSmartSelectOpen(false)}
                selectState={smartSelect.selectState}
                outputMode={smartSelect.outputMode}
                onOutputModeChange={smartSelect.setOutputMode}
                currentMask={selectedMask}
                currentPolygon={smartSelect.currentPolygon}
                maskCandidates={maskCandidates}
                selectedMaskIndex={selectedMaskIndex}
                onSelectMask={(idx) => {
                  setSelectedMaskIndex(idx);
                  // Sync the selected mask to SmartSelect for polygon extraction
                  // Also update mask input so manual Run uses the selected mask
                  if (maskCandidates[idx]) {
                    const mask = maskCandidates[idx];
                    // Prefer logits for refinement
                    if (mask.low_res_logits_base64) {
                      setMaskLogitsBase64(mask.low_res_logits_base64);
                      setMaskInputBase64(null);
                    } else {
                      setMaskInputBase64(mask.mask_base64);
                      setMaskLogitsBase64(null);
                    }
                    smartSelect.setMask(
                      mask,
                      pointPrompts,
                      boxPrompts.length > 0 ? boxPrompts[boxPrompts.length - 1] : null
                    );
                  }
                }}
                polygonComplexity={smartSelect.polygonComplexity}
                onPolygonComplexityChange={smartSelect.setPolygonComplexity}
                canUndo={smartSelect.canUndo}
                canRedo={smartSelect.canRedo}
                onUndo={() => {
                  const entry = smartSelect.undo();
                  if (entry) {
                    setPointPrompts(entry.points);
                    setBoxPrompts(entry.box ? [entry.box] : []);
                    setMaskCandidates([entry.mask]);
                    setSelectedMaskIndex(0);
                  }
                }}
                onRedo={() => {
                  const entry = smartSelect.redo();
                  if (entry) {
                    setPointPrompts(entry.points);
                    setBoxPrompts(entry.box ? [entry.box] : []);
                    setMaskCandidates([entry.mask]);
                    setSelectedMaskIndex(0);
                  }
                }}
                onDelete={() => {
                  smartSelect.deleteSelection();
                  setMaskCandidates([]);
                  setSelectedMaskIndex(0);
                }}
                onFinish={() => {
                  smartSelect.finish();
                  // Could trigger save/export action here
                }}
                isRunning={running}
                onFindSimilar={handleFindSimilar}
                isFindingSimilar={isFindingSimilar}
                similarRegions={similarRegions}
                onSelectSimilarRegion={handleSelectSimilarRegion}
                selectedSimilarIndex={selectedSimilarIndex}
              />
            )}
          </div>
        )}

        {/* Floating Results Sidebar (Right) */}
        {selectedDocId && sidebarOpen && (
          <div className="absolute top-4 right-4 bottom-4 w-80 flex flex-col bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-white">Results</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {activeZones.length} zones detected
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {/* Clear All button */}
                  <button
                    onClick={() => setShowClearConfirm(true)}
                    disabled={results.length === 0 && pointPrompts.length === 0 && boxPrompts.length === 0 && maskCandidates.length === 0}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 disabled:text-slate-600 disabled:hover:bg-transparent rounded transition-colors"
                    title="Clear all annotations"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="p-1 text-slate-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Clear confirmation dialog */}
              {showClearConfirm && (
                <div className="mt-3 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                  <p className="text-xs text-red-300 font-medium mb-2">
                    Clear all annotations?
                  </p>
                  <p className="text-[10px] text-slate-400 mb-3">
                    This will remove all results, prompts, and saved state for this document.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleClearAllAnnotations}
                      className="flex-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition-colors"
                    >
                      Clear All
                    </button>
                    <button
                      onClick={() => setShowClearConfirm(false)}
                      className="flex-1 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-medium rounded transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Saved state indicator */}
              {savedStateTimestamp && !showClearConfirm && (
                <div className="mt-2 flex items-center gap-1.5 text-[10px] text-emerald-400">
                  <BookmarkIcon className="w-3 h-3" />
                  <span>Restored from {formatSavedTime(savedStateTimestamp)}</span>
                </div>
              )}

              {/* Confidence threshold */}
              <div className="mt-3">
                <ConfidenceSlider
                  value={confidenceThreshold}
                  onChange={setConfidenceThreshold}
                  label="Confidence"
                  step={0.05}
                />
              </div>

              {/* Display mode toggle */}
              <div className="mt-3 flex items-center justify-between">
                <label className="text-xs text-slate-400">Display</label>
                <button
                  onClick={() => setShowMasks(!showMasks)}
                  className={`flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs transition-colors ${
                    showMasks
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                      : 'bg-slate-700/50 text-slate-400 border border-slate-600'
                  }`}
                >
                  {showMasks ? 'Masks' : 'Boxes'}
                </button>
              </div>

              {/* Mask input indicator */}
              {(inputMode === 'points' || inputMode === 'box') && (maskInputBase64 || maskLogitsBase64) && (
                <div className="mt-3 p-2.5 bg-amber-900/20 border border-amber-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                      <span className="text-xs text-amber-300 font-medium">
                        {maskLogitsBase64 ? 'Logits Input Active' : 'Mask Input Active'}
                      </span>
                    </div>
                    <button
                      onClick={handleClearMaskInput}
                      className="text-[10px] text-amber-400 hover:text-amber-300"
                    >
                      Clear
                    </button>
                  </div>
                  <p className="mt-1.5 text-[10px] text-slate-500">
                    {maskLogitsBase64
                      ? 'Using low-res logits for high-quality refinement.'
                      : 'Using previous mask for refinement (legacy mode).'}
                  </p>
                </div>
              )}

              {/* Mask selection for interactive modes */}
              {(inputMode === 'points' || inputMode === 'box') && maskCandidates.length > 0 && (
                <div className="mt-3 p-2.5 bg-purple-900/20 border border-purple-500/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-purple-300 font-medium">
                      Mask Candidates
                    </label>
                    <span className="text-[10px] text-purple-400">
                      {selectedMaskIndex + 1} / {maskCandidates.length}
                    </span>
                  </div>
                  <div className="flex gap-1.5">
                    {maskCandidates.map((mask, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedMaskIndex(idx)}
                        className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                          selectedMaskIndex === idx
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white'
                        }`}
                        title={`IoU: ${(mask.iou_score * 100).toFixed(1)}%`}
                      >
                        {(mask.iou_score * 100).toFixed(0)}%
                      </button>
                    ))}
                  </div>
                  {/* Use as Mask Input button */}
                  <button
                    onClick={handleUseMaskAsInput}
                    className="w-full mt-2 px-2 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/50 text-amber-300 hover:text-amber-200 rounded text-xs font-medium transition-colors"
                  >
                    Use as Mask Input for Refinement
                  </button>
                  <p className="mt-2 text-[10px] text-slate-500">
                    Click to switch between masks. Use "Mask Input" to refine with additional prompts.
                  </p>
                </div>
              )}
            </div>

            {/* Results history tabs */}
            {results.length > 0 && (
              <div className="flex gap-1 px-3 py-2 border-b border-slate-700 overflow-x-auto">
                {results.slice(0, 5).map((result, idx) => (
                  <button
                    key={result.id}
                    onClick={() => setActiveResultId(result.id)}
                    className={`flex-shrink-0 px-2 py-1 rounded text-xs transition-colors ${
                      activeResultId === result.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                    }`}
                    title={result.prompts.join(', ')}
                  >
                    #{results.length - idx}
                  </button>
                ))}
              </div>
            )}

            {/* Zone list */}
            <div className="flex-1 overflow-y-auto px-3 py-2">
              {activeZones.length > 0 ? (
                <div className="space-y-2">
                  {activeZones.map((zone) => {
                    const isSelected = selectedZoneId === zone.zone_id;
                    const isHovered = hoveredZoneId === zone.zone_id;
                    const color = getZoneColor(zone.zone_type);

                    return (
                      <div
                        key={zone.zone_id}
                        onClick={() => setSelectedZoneId(zone.zone_id)}
                        onMouseEnter={() => setHoveredZoneId(zone.zone_id)}
                        onMouseLeave={() => setHoveredZoneId(null)}
                        className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-blue-500/20 border-blue-500 ring-1 ring-blue-500/50'
                            : isHovered
                            ? 'bg-slate-700 border-slate-500'
                            : 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-700/50'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <div
                              className="w-3 h-3 rounded-full flex-shrink-0"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-xs text-white truncate">
                              {zone.prompt_matched || zone.zone_type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-blue-400 tabular-nums flex-shrink-0">
                            {(zone.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="mt-1 text-[10px] text-slate-500">
                          {Math.round(zone.bbox[2] - zone.bbox[0])} × {Math.round(zone.bbox[3] - zone.bbox[1])} px
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : results.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-slate-500 text-xs">
                    <p>No results yet</p>
                    <p className="mt-1 text-slate-600">
                      Enter prompts and run segmentation
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-slate-500 text-xs">
                    No zones above threshold
                  </div>
                </div>
              )}
            </div>

            {/* Processing time footer */}
            {activeResult && (
              <div className="px-3 py-2 border-t border-slate-700 bg-slate-800/50">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Processing time</span>
                  <span className="font-mono">{activeResult.processingTimeMs.toFixed(0)}ms</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sidebar toggle when closed */}
        {selectedDocId && !sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute top-4 right-4 z-40 p-3 bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-lg shadow-lg hover:bg-slate-700 transition-colors"
            title="Show results panel"
          >
            <ChatBubbleBottomCenterTextIcon className="w-5 h-5 text-white" />
          </button>
        )}
      </div>
    </div>
  );
}
