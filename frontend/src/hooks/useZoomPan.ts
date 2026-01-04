/**
 * useZoomPan Hook
 *
 * Production-grade zoom and pan controls matching docling-interactive implementation.
 * Provides smooth, responsive zoom/pan with keyboard shortcuts, mouse wheel support,
 * and intelligent fit-to-page functionality.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

// Zoom constants - matching docling-interactive exactly
const MIN_ZOOM = 0.1; // 10%
const MAX_ZOOM = 4; // 400%
const SCROLLS_TO_DOUBLE = 10; // 10 scroll events to double zoom
const ZOOM_MULTIPLIER = Math.pow(2, 1 / SCROLLS_TO_DOUBLE); // ≈1.071
const THROTTLE_MS = 16; // ~60fps for pan throttling

interface ImageDimensions {
  width: number;
  height: number;
}

interface ZoomPanState {
  zoom: number;
  pan: { x: number; y: number };
  isPanning: boolean;
  isZooming: boolean;
}

interface ZoomPanControls {
  handleZoomIn: () => void;
  handleZoomOut: () => void;
  handleFitToPage: () => void;
  handleFitToWidth: () => void;
  handleActualSize: () => void;
  handlePanStart: (e: React.MouseEvent) => void;
  handlePanMove: (e: React.MouseEvent) => void;
  handlePanEnd: () => void;
  handleDoubleClick: (e: React.MouseEvent) => void;
  setZoom: React.Dispatch<React.SetStateAction<number>>;
  setPan: React.Dispatch<React.SetStateAction<{ x: number; y: number }>>;
}

export interface UseZoomPanReturn extends ZoomPanState, ZoomPanControls {
  containerRef: React.RefObject<HTMLDivElement>;
  MIN_ZOOM: number;
  MAX_ZOOM: number;
}

interface UseZoomPanOptions {
  imageDimensions: ImageDimensions | null;
}

export function useZoomPan({ imageDimensions }: UseZoomPanOptions): UseZoomPanReturn {
  // State
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isZooming, setIsZooming] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [fittedPage, setFittedPage] = useState<number | null>(null);

  // Refs for performance optimization
  const containerRef = useRef<HTMLDivElement>(null);
  const currentZoomRef = useRef(1);
  const currentPanRef = useRef({ x: 0, y: 0 });
  const lastPanMoveTimeRef = useRef(0);
  const rafPanIdRef = useRef<number | null>(null);
  const pendingPanRef = useRef<{ x: number; y: number } | null>(null);
  const lastFitDimensionsRef = useRef<{ width: number; height: number } | null>(null);
  const zoomTimeoutRef = useRef<number | null>(null);

  // Keep refs in sync
  useEffect(() => {
    currentZoomRef.current = zoom;
  }, [zoom]);

  useEffect(() => {
    currentPanRef.current = pan;
  }, [pan]);

  // Zoom in (button click or keyboard)
  const handleZoomIn = useCallback(() => {
    const multiplier = Math.pow(ZOOM_MULTIPLIER, 3); // More aggressive for button clicks
    setZoom((prev) => Math.min(MAX_ZOOM, prev * multiplier));
    setFittedPage(null);
  }, []);

  // Zoom out (button click or keyboard)
  const handleZoomOut = useCallback(() => {
    const multiplier = Math.pow(ZOOM_MULTIPLIER, 3);
    setZoom((prev) => Math.max(MIN_ZOOM, prev / multiplier));
    setFittedPage(null);
  }, []);

  // Actual size (100% zoom)
  const handleActualSize = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setFittedPage(null);
  }, []);

  // Fit to page - scale to fit within container with padding
  const handleFitToPage = useCallback(() => {
    if (!containerRef.current || !imageDimensions) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();

    const padding = 40; // 40px padding on each side
    const availableWidth = rect.width - padding * 2;
    const availableHeight = rect.height - padding * 2;

    const widthRatio = availableWidth / imageDimensions.width;
    const heightRatio = availableHeight / imageDimensions.height;

    // Use the smaller ratio to ensure the entire image fits
    const newZoom = Math.min(widthRatio, heightRatio, 1);

    setZoom(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom)));
    setPan({ x: 0, y: 0 });
    setFittedPage(0); // Track that we fitted to this page

    lastFitDimensionsRef.current = {
      width: rect.width,
      height: rect.height,
    };
  }, [imageDimensions]);

  // Fit to width - scale to fit container width
  const handleFitToWidth = useCallback(() => {
    if (!containerRef.current || !imageDimensions) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();

    const padding = 40;
    const availableWidth = rect.width - padding * 2;
    const widthRatio = availableWidth / imageDimensions.width;

    setZoom(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, widthRatio)));
    setPan({ x: 0, y: 0 });
    setFittedPage(null);
  }, [imageDimensions]);

  // Pan start - middle mouse button (button 1)
  const handlePanStart = useCallback(
    (e: React.MouseEvent) => {
      if (e.button === 1) {
        // Middle mouse button
        e.preventDefault();
        setIsPanning(true);
        setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      }
    },
    [pan]
  );

  // Pan move - RAF-based throttling for smooth 60fps updates
  const handlePanMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isPanning) return;

      const now = performance.now();
      const newPan = {
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      };

      // Throttle to ~16ms (60fps) using requestAnimationFrame
      if (now - lastPanMoveTimeRef.current >= THROTTLE_MS) {
        setPan(newPan);
        lastPanMoveTimeRef.current = now;
        pendingPanRef.current = null;
      } else {
        pendingPanRef.current = newPan;
        if (rafPanIdRef.current === null) {
          rafPanIdRef.current = requestAnimationFrame(() => {
            if (pendingPanRef.current) {
              setPan(pendingPanRef.current);
              lastPanMoveTimeRef.current = performance.now();
              pendingPanRef.current = null;
            }
            rafPanIdRef.current = null;
          });
        }
      }

      setFittedPage(null);
    },
    [isPanning, panStart]
  );

  // Pan end
  const handlePanEnd = useCallback(() => {
    setIsPanning(false);
    // Clean up any pending RAF
    if (rafPanIdRef.current !== null) {
      cancelAnimationFrame(rafPanIdRef.current);
      rafPanIdRef.current = null;
    }
  }, []);

  // Double-click to fit to page
  const handleDoubleClick = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      handleFitToPage();
    },
    [handleFitToPage]
  );

  // Mouse wheel zoom - zoom around cursor, with Ctrl/Cmd + wheel = pan
  // Re-runs when imageDimensions changes (ensures container ref is available)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      // Ctrl/Cmd + scroll = pan (trackpad pinch gesture support)
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        setPan((prev) => ({
          x: prev.x - e.deltaX,
          y: prev.y - e.deltaY,
        }));
        setFittedPage(null);
        return;
      }

      // Regular scroll = zoom
      e.preventDefault();

      const zoomIn = e.deltaY < 0;
      const oldZoom = currentZoomRef.current;
      const oldPan = currentPanRef.current;

      // Calculate new zoom level
      const newZoom = Math.min(
        MAX_ZOOM,
        Math.max(MIN_ZOOM, zoomIn ? oldZoom * ZOOM_MULTIPLIER : oldZoom / ZOOM_MULTIPLIER)
      );

      // Get mouse position relative to container
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left - rect.width / 2;
      const mouseY = e.clientY - rect.top - rect.height / 2;

      // Calculate new pan to keep point under cursor fixed
      const zoomRatio = newZoom / oldZoom;
      const newPan = {
        x: mouseX + (oldPan.x - mouseX) * zoomRatio,
        y: mouseY + (oldPan.y - mouseY) * zoomRatio,
      };

      setZoom(newZoom);
      setPan(newPan);
      setFittedPage(null);

      // Set isZooming flag for animation control
      setIsZooming(true);
      if (zoomTimeoutRef.current) clearTimeout(zoomTimeoutRef.current);
      zoomTimeoutRef.current = setTimeout(() => setIsZooming(false), 150);
    };

    // Always re-attach listener when effect runs (cleanup will remove old one)
    container.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      container.removeEventListener('wheel', handleWheel);
      if (zoomTimeoutRef.current) clearTimeout(zoomTimeoutRef.current);
    };
  }, [imageDimensions]);

  // Auto fit-to-page on image load or container resize (with debounce)
  useEffect(() => {
    if (!containerRef.current || !imageDimensions) return;

    const container = containerRef.current;
    const resizeObserver = new ResizeObserver(() => {
      // Only auto-fit if we previously fitted this page
      if (fittedPage !== null) {
        // Debounce: wait 100ms for layout to stabilize
        setTimeout(() => {
          const rect = container.getBoundingClientRect();
          const lastDims = lastFitDimensionsRef.current;

          // Check if dimensions changed significantly
          if (
            !lastDims ||
            Math.abs(rect.width - lastDims.width) > 5 ||
            Math.abs(rect.height - lastDims.height) > 5
          ) {
            handleFitToPage();
          }
        }, 100);
      }
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, [imageDimensions, fittedPage, handleFitToPage]);

  return {
    // State
    zoom,
    pan,
    isPanning,
    isZooming,

    // Controls
    handleZoomIn,
    handleZoomOut,
    handleFitToPage,
    handleFitToWidth,
    handleActualSize,
    handlePanStart,
    handlePanMove,
    handlePanEnd,
    handleDoubleClick,
    setZoom,
    setPan,

    // Ref
    containerRef,

    // Constants
    MIN_ZOOM,
    MAX_ZOOM,
  };
}
