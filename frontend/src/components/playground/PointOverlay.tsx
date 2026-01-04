/**
 * PointOverlay - SVG overlay for displaying point prompts
 *
 * Renders positive points (green) and negative points (red) on top of the canvas.
 * Points are positioned in image coordinate space and transformed to match zoom/pan.
 */

import type { PointPrompt, PointPromptMode } from '../../types';

interface PointOverlayProps {
  points: PointPrompt[];
  imageDimensions: { width: number; height: number };
  zoom: number;
  pan: { x: number; y: number };
  pointMode: PointPromptMode;
  onPointRemove?: (id: string) => void;
}

export function PointOverlay({
  points,
  imageDimensions,
  zoom,
  pan,
  pointMode,
  onPointRemove,
}: PointOverlayProps) {
  // SVG viewBox matches image dimensions for proper coordinate mapping
  const viewBox = `0 0 ${imageDimensions.width} ${imageDimensions.height}`;

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      viewBox={viewBox}
      preserveAspectRatio="xMidYMid meet"
      style={{
        width: imageDimensions.width,
        height: imageDimensions.height,
        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
        transformOrigin: 'center center',
        left: '50%',
        top: '50%',
        marginLeft: -imageDimensions.width / 2,
        marginTop: -imageDimensions.height / 2,
      }}
    >
      {/* Render each point */}
      {points.map((point) => {
        const isPositive = point.label === 1;
        const color = isPositive ? '#22c55e' : '#ef4444'; // green-500 / red-500
        const bgColor = isPositive ? '#166534' : '#991b1b'; // green-800 / red-800

        return (
          <g
            key={point.id}
            className="pointer-events-auto cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onPointRemove?.(point.id);
            }}
          >
            {/* Outer ring */}
            <circle
              cx={point.x}
              cy={point.y}
              r={12 / zoom}
              fill="none"
              stroke={color}
              strokeWidth={2 / zoom}
              opacity={0.8}
            />
            {/* Inner filled circle */}
            <circle
              cx={point.x}
              cy={point.y}
              r={6 / zoom}
              fill={bgColor}
              stroke={color}
              strokeWidth={1.5 / zoom}
            />
            {/* Plus/Minus symbol */}
            {isPositive ? (
              <>
                {/* Plus sign */}
                <line
                  x1={point.x - 3 / zoom}
                  y1={point.y}
                  x2={point.x + 3 / zoom}
                  y2={point.y}
                  stroke="white"
                  strokeWidth={1.5 / zoom}
                  strokeLinecap="round"
                />
                <line
                  x1={point.x}
                  y1={point.y - 3 / zoom}
                  x2={point.x}
                  y2={point.y + 3 / zoom}
                  stroke="white"
                  strokeWidth={1.5 / zoom}
                  strokeLinecap="round"
                />
              </>
            ) : (
              /* Minus sign */
              <line
                x1={point.x - 3 / zoom}
                y1={point.y}
                x2={point.x + 3 / zoom}
                y2={point.y}
                stroke="white"
                strokeWidth={1.5 / zoom}
                strokeLinecap="round"
              />
            )}
          </g>
        );
      })}

      {/* Mode indicator (cursor preview) */}
      <defs>
        <marker
          id="cursor-point"
          viewBox="0 0 20 20"
          refX="10"
          refY="10"
          markerWidth="20"
          markerHeight="20"
        >
          <circle
            cx="10"
            cy="10"
            r="8"
            fill={pointMode === 'positive' ? '#22c55e33' : '#ef444433'}
            stroke={pointMode === 'positive' ? '#22c55e' : '#ef4444'}
            strokeWidth="1"
          />
        </marker>
      </defs>
    </svg>
  );
}
