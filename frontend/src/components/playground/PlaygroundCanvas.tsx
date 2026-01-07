/**
 * PlaygroundCanvas - Wrapper for DrawingCanvas with interactive point/box support
 *
 * This component wraps DrawingCanvas and adds interactive overlays for:
 * - Point prompts (click to place positive/negative points)
 * - Bounding box prompts (drag to draw boxes)
 *
 * The DrawingCanvas component remains unchanged, avoiding regressions in Viewer.
 */

import { useState, useCallback, useRef } from 'react';
import { DrawingCanvas } from '../viewer';
import { PointOverlay } from './PointOverlay';
import { BoxOverlay } from './BoxOverlay';
import { MaskOverlay } from './MaskOverlay';
import { screenToImageCoords, generatePromptId } from '../../utils/canvasCoordinates';
import type {
  ZoneResult,
  PointPrompt,
  BoxPrompt,
  BoxDragState,
  PointPromptMode,
  PointPromptLabel,
  MaskCandidate,
  PolygonData,
  SmartSelectOutputMode,
  SmartSelectState,
} from '../../types';
import { isPointInMask } from '../../utils/polygonExtraction';

type InputMode = 'text' | 'points' | 'box';

interface PlaygroundCanvasProps {
  imageUrl: string;
  zones: ZoneResult[];
  zoom: number;
  pan: { x: number; y: number };
  isPanning: boolean;
  isZooming: boolean;
  showMasks?: boolean;
  containerRef: React.RefObject<HTMLDivElement>;

  // Zone interaction (pass-through to DrawingCanvas)
  hoveredZoneId: string | null;
  selectedZoneId: string | null;
  onZoneClick: (id: string) => void;
  onZoneHover: (id: string | null) => void;

  // Interactive mode - which mode is active
  inputMode: InputMode;
  pointPromptMode: PointPromptMode;
  imageDimensions: { width: number; height: number } | null;

  // Point prompts
  pointPrompts: PointPrompt[];
  onAddPoint: (point: PointPrompt) => void;
  onRemovePoint: (id: string) => void;

  // Box prompts
  boxPrompts: BoxPrompt[];
  onAddBox: (box: BoxPrompt) => void;
  onRemoveBox: (id: string) => void;

  // Mask result (optional - shown after segmentation)
  selectedMask?: MaskCandidate | null;

  // Exemplar mask (shown alongside selected mask in Find Similar mode)
  exemplarMask?: MaskCandidate | null;
  showExemplarMask?: boolean;

  // Smart Select features
  displayMode?: SmartSelectOutputMode;
  polygon?: PolygonData | null;

  // Refinement mode (click inside/outside mask to add/remove)
  selectState?: SmartSelectState;
  onRefinementClick?: (point: PointPrompt, isInsideMask: boolean) => void;

  // Pass-through handlers
  onPanStart: (e: React.MouseEvent) => void;
  onPanMove: (e: React.MouseEvent) => void;
  onPanEnd: () => void;
  onDoubleClick: (e: React.MouseEvent) => void;
  onImageLoad: (dimensions: { width: number; height: number }) => void;
}

export function PlaygroundCanvas({
  imageUrl,
  zones,
  zoom,
  pan,
  isPanning,
  isZooming,
  showMasks = true,
  containerRef,
  hoveredZoneId,
  selectedZoneId,
  onZoneClick,
  onZoneHover,
  inputMode,
  pointPromptMode,
  imageDimensions: externalImageDimensions,
  pointPrompts,
  onAddPoint,
  onRemovePoint,
  boxPrompts,
  onAddBox,
  onRemoveBox,
  selectedMask,
  exemplarMask = null,
  showExemplarMask = false,
  displayMode = 'pixels',
  polygon = null,
  selectState = 'idle',
  onRefinementClick,
  onPanStart,
  onPanMove,
  onPanEnd,
  onDoubleClick,
  onImageLoad,
}: PlaygroundCanvasProps) {
  // Use passed dimensions or local state as fallback
  const [localImageDimensions, setLocalImageDimensions] = useState<{
    width: number;
    height: number;
  } | null>(null);

  const imageDimensions = externalImageDimensions || localImageDimensions;

  // Box drawing state
  const [activeBox, setActiveBox] = useState<BoxDragState | null>(null);
  const isDrawingBox = useRef(false);

  // Handle image load
  const handleImageLoad = useCallback(
    (dimensions: { width: number; height: number }) => {
      setLocalImageDimensions(dimensions);
      onImageLoad(dimensions);
    },
    [onImageLoad]
  );

  // Convert mouse event to image coordinates
  const getImageCoords = useCallback(
    (e: React.MouseEvent): { x: number; y: number } | null => {
      if (!containerRef.current || !imageDimensions) return null;

      const rect = containerRef.current.getBoundingClientRect();
      return screenToImageCoords(
        e.clientX,
        e.clientY,
        rect,
        pan,
        zoom,
        imageDimensions
      );
    },
    [containerRef, imageDimensions, pan, zoom]
  );

  // Handle canvas click - intercept for point placement and refinement
  const handleCanvasClick = useCallback(
    async (e: React.MouseEvent) => {
      if (isPanning || isDrawingBox.current) return;

      const coords = getImageCoords(e);
      if (!coords || !imageDimensions) return;

      // Check if click is within image bounds
      if (
        coords.x < 0 ||
        coords.x > imageDimensions.width ||
        coords.y < 0 ||
        coords.y > imageDimensions.height
      ) {
        return;
      }

      // Check if we're in refinement mode (have a mask and state is initial/refining)
      const inRefinementMode = selectedMask?.mask_base64 &&
        (selectState === 'initial' || selectState === 'refining') &&
        onRefinementClick;

      if (inRefinementMode) {
        // Determine if click is inside or outside the mask
        try {
          const isInside = await isPointInMask(coords, selectedMask.mask_base64);

          // Create point with appropriate label
          // Inside mask = negative (remove), Outside mask = positive (add)
          const label: PointPromptLabel = isInside ? 0 : 1;
          const newPoint: PointPrompt = {
            id: generatePromptId('point'),
            x: coords.x,
            y: coords.y,
            label,
          };

          onRefinementClick(newPoint, isInside);
        } catch (err) {
          console.error('Failed to check point in mask:', err);
          // Fall back to regular point mode behavior
        }
        return;
      }

      // Regular point mode
      if (inputMode === 'points') {
        const label: PointPromptLabel = pointPromptMode === 'positive' ? 1 : 0;
        const newPoint: PointPrompt = {
          id: generatePromptId('point'),
          x: coords.x,
          y: coords.y,
          label,
        };

        onAddPoint(newPoint);
      }
      // In 'text' or 'box' mode, let DrawingCanvas handle zone clicks
    },
    [
      isPanning,
      inputMode,
      pointPromptMode,
      getImageCoords,
      imageDimensions,
      onAddPoint,
      selectedMask,
      selectState,
      onRefinementClick,
    ]
  );

  // Handle mouse down for box drawing
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Middle button = pan (handled by parent)
      if (e.button === 1) {
        onPanStart(e);
        return;
      }

      // Left button in box mode = start drawing
      if (e.button === 0 && inputMode === 'box') {
        const coords = getImageCoords(e);
        if (!coords) return;

        // Check bounds
        if (
          coords.x < 0 ||
          coords.x > imageDimensions!.width ||
          coords.y < 0 ||
          coords.y > imageDimensions!.height
        ) {
          return;
        }

        isDrawingBox.current = true;
        setActiveBox({
          startX: coords.x,
          startY: coords.y,
          currentX: coords.x,
          currentY: coords.y,
        });
      }
    },
    [inputMode, getImageCoords, imageDimensions, onPanStart]
  );

  // Handle mouse move for box drawing
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      // Handle pan
      if (isPanning) {
        onPanMove(e);
        return;
      }

      // Update active box preview
      if (isDrawingBox.current && activeBox) {
        const coords = getImageCoords(e);
        if (!coords) return;

        // Clamp to image bounds
        const clampedX = Math.max(0, Math.min(coords.x, imageDimensions!.width));
        const clampedY = Math.max(0, Math.min(coords.y, imageDimensions!.height));

        setActiveBox((prev) =>
          prev
            ? {
                ...prev,
                currentX: clampedX,
                currentY: clampedY,
              }
            : null
        );
      }
    },
    [isPanning, activeBox, getImageCoords, imageDimensions, onPanMove]
  );

  // Handle mouse up for box drawing
  const handleMouseUp = useCallback(
    (_e: React.MouseEvent) => {
      if (isPanning) {
        onPanEnd();
        return;
      }

      if (isDrawingBox.current && activeBox && imageDimensions) {
        isDrawingBox.current = false;

        // Only create box if it has meaningful size
        const width = Math.abs(activeBox.currentX - activeBox.startX);
        const height = Math.abs(activeBox.currentY - activeBox.startY);

        if (width > 10 && height > 10) {
          // Clamp box coordinates to image bounds (fixes potential offset issues)
          const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(val, max));
          const newBox: BoxPrompt = {
            id: generatePromptId('box'),
            x1: clamp(Math.min(activeBox.startX, activeBox.currentX), 0, imageDimensions.width),
            y1: clamp(Math.min(activeBox.startY, activeBox.currentY), 0, imageDimensions.height),
            x2: clamp(Math.max(activeBox.startX, activeBox.currentX), 0, imageDimensions.width),
            y2: clamp(Math.max(activeBox.startY, activeBox.currentY), 0, imageDimensions.height),
          };

          onAddBox(newBox);
        }

        setActiveBox(null);
      }
    },
    [isPanning, activeBox, onPanEnd, onAddBox, imageDimensions]
  );

  // Cursor style based on mode
  const getCursor = (): string => {
    if (isPanning) return 'grabbing';
    if (inputMode === 'points') {
      return 'crosshair';
    }
    if (inputMode === 'box') {
      return 'crosshair';
    }
    return 'default';
  };

  return (
    <div
      className="relative w-full h-full overflow-hidden"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        if (isPanning) onPanEnd();
        if (isDrawingBox.current) {
          isDrawingBox.current = false;
          setActiveBox(null);
        }
      }}
      style={{ cursor: getCursor() }}
    >
      {/* Base DrawingCanvas for image and zone overlays */}
      <DrawingCanvas
        imageUrl={imageUrl}
        zones={zones}
        zoom={zoom}
        pan={pan}
        isPanning={isPanning}
        isZooming={isZooming}
        hoveredZoneId={hoveredZoneId}
        selectedZoneId={selectedZoneId}
        showMasks={showMasks}
        onZoneClick={onZoneClick}
        onZoneHover={onZoneHover}
        onPanStart={() => {}}
        onPanMove={() => {}}
        onPanEnd={() => {}}
        onDoubleClick={onDoubleClick}
        onImageLoad={handleImageLoad}
        containerRef={containerRef}
      />

      {/* Interactive overlays - only when image is loaded */}
      {imageDimensions && (
        <>
          {/* Point prompts overlay */}
          {inputMode === 'points' && (
            <PointOverlay
              points={pointPrompts}
              imageDimensions={imageDimensions}
              zoom={zoom}
              pan={pan}
              containerRef={containerRef}
              pointMode={pointPromptMode}
              onPointRemove={onRemovePoint}
            />
          )}

          {/* Box prompts overlay */}
          {inputMode === 'box' && (
            <BoxOverlay
              boxes={boxPrompts}
              activeBox={activeBox}
              imageDimensions={imageDimensions}
              zoom={zoom}
              pan={pan}
              containerRef={containerRef}
              onBoxRemove={onRemoveBox}
            />
          )}

          {/* Exemplar mask overlay (shown when viewing Find Similar results) */}
          {(inputMode === 'points' || inputMode === 'box') && showExemplarMask && exemplarMask && (
            <MaskOverlay
              mask={exemplarMask}
              imageDimensions={imageDimensions}
              zoom={zoom}
              pan={pan}
              containerRef={containerRef}
              displayMode="pixels"
              maskColor="#10b981" // emerald-500 for exemplar
              maskOpacity={0.35}
            />
          )}

          {/* Mask result overlay (shown for both points and box modes) */}
          {(inputMode === 'points' || inputMode === 'box') && selectedMask && (
            <MaskOverlay
              mask={selectedMask}
              imageDimensions={imageDimensions}
              zoom={zoom}
              pan={pan}
              containerRef={containerRef}
              displayMode={displayMode}
              polygon={polygon}
            />
          )}
        </>
      )}

      {/* Click area overlay for interactive modes to capture clicks for points and refinement */}
      {imageDimensions && (inputMode === 'points' || (inputMode === 'box' && selectedMask?.mask_base64)) && (
        <div
          className="absolute inset-0"
          onClick={handleCanvasClick}
          style={{
            cursor: 'crosshair',
          }}
        />
      )}
    </div>
  );
}
