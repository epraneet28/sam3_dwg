/**
 * BoxOverlay - SVG overlay for displaying bounding box prompts
 *
 * Renders completed boxes and the active box being drawn.
 * Boxes are positioned in image coordinate space and transformed to match zoom/pan.
 *
 * Uses CSS-constrained dimensions to match the canvas's maxWidth/maxHeight behavior.
 */

import { useMemo } from 'react';
import type { BoxPrompt, BoxDragState } from '../../types';
import { calculateCssScale } from '../../utils/canvasCoordinates';

interface BoxOverlayProps {
  boxes: BoxPrompt[];
  activeBox: BoxDragState | null;
  imageDimensions: { width: number; height: number };
  zoom: number;
  pan: { x: number; y: number };
  containerRef: React.RefObject<HTMLDivElement>;
  onBoxRemove?: (id: string) => void;
}

export function BoxOverlay({
  boxes,
  activeBox,
  imageDimensions,
  zoom,
  pan,
  containerRef,
  onBoxRemove,
}: BoxOverlayProps) {
  // SVG viewBox matches image dimensions for proper coordinate mapping
  const viewBox = `0 0 ${imageDimensions.width} ${imageDimensions.height}`;

  // Calculate CSS-constrained dimensions to match canvas sizing
  const { renderedWidth, renderedHeight } = useMemo(() => {
    if (!containerRef.current) {
      return { renderedWidth: imageDimensions.width, renderedHeight: imageDimensions.height };
    }
    const rect = containerRef.current.getBoundingClientRect();
    const cssScale = calculateCssScale(rect, imageDimensions);
    return {
      renderedWidth: imageDimensions.width * cssScale,
      renderedHeight: imageDimensions.height * cssScale,
    };
  }, [containerRef, imageDimensions]);

  // Normalize box coordinates (handle negative-direction draws)
  const normalizeBox = (
    x1: number,
    y1: number,
    x2: number,
    y2: number
  ): { x: number; y: number; width: number; height: number } => {
    const minX = Math.min(x1, x2);
    const minY = Math.min(y1, y2);
    const maxX = Math.max(x1, x2);
    const maxY = Math.max(y1, y2);
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
    };
  };

  return (
    <svg
      className="absolute pointer-events-none"
      viewBox={viewBox}
      preserveAspectRatio="xMidYMid meet"
      style={{
        width: renderedWidth,
        height: renderedHeight,
        // Use translate(-50%, -50%) for centering instead of margins
        // This works correctly when CSS constraints change the rendered size
        transform: `translate(-50%, -50%) translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
        transformOrigin: 'center center',
        left: '50%',
        top: '50%',
      }}
    >
      {/* Render completed boxes */}
      {boxes.map((box) => {
        const rect = normalizeBox(box.x1, box.y1, box.x2, box.y2);

        return (
          <g
            key={box.id}
            className="pointer-events-auto cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onBoxRemove?.(box.id);
            }}
          >
            {/* Box fill */}
            <rect
              x={rect.x}
              y={rect.y}
              width={rect.width}
              height={rect.height}
              fill="#3b82f633" // blue-500 with opacity
              stroke="#3b82f6"
              strokeWidth={2 / zoom}
              strokeDasharray="none"
            />
            {/* Corner handles */}
            {[
              { cx: box.x1, cy: box.y1 },
              { cx: box.x2, cy: box.y1 },
              { cx: box.x1, cy: box.y2 },
              { cx: box.x2, cy: box.y2 },
            ].map((corner, idx) => (
              <rect
                key={idx}
                x={corner.cx - 4 / zoom}
                y={corner.cy - 4 / zoom}
                width={8 / zoom}
                height={8 / zoom}
                fill="#3b82f6"
                stroke="white"
                strokeWidth={1 / zoom}
              />
            ))}
            {/* Delete indicator on hover */}
            <text
              x={rect.x + rect.width / 2}
              y={rect.y - 8 / zoom}
              textAnchor="middle"
              fontSize={12 / zoom}
              fill="#3b82f6"
              className="opacity-0 group-hover:opacity-100"
            >
              Click to remove
            </text>
          </g>
        );
      })}

      {/* Render active box being drawn (dashed preview) */}
      {activeBox && (
        <rect
          {...normalizeBox(
            activeBox.startX,
            activeBox.startY,
            activeBox.currentX,
            activeBox.currentY
          )}
          fill="#3b82f622"
          stroke="#3b82f6"
          strokeWidth={2 / zoom}
          strokeDasharray={`${6 / zoom} ${4 / zoom}`}
        />
      )}
    </svg>
  );
}
