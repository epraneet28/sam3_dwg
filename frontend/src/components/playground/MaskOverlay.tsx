/**
 * MaskOverlay - SVG/Canvas overlay for displaying segmentation masks
 *
 * Renders the selected mask from interactive segmentation results.
 * Supports two display modes:
 * - 'pixels': Semi-transparent colored mask overlay (canvas-based)
 * - 'polygon': SVG polygon outline with fill
 *
 * Uses CSS-constrained dimensions to match the canvas's maxWidth/maxHeight behavior.
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import type { MaskCandidate, PolygonData, SmartSelectOutputMode } from '../../types';
import { polygonToSvgPath } from '../../utils/polygonExtraction';
import { calculateCssScale } from '../../utils/canvasCoordinates';

interface MaskOverlayProps {
  mask: MaskCandidate | null;
  imageDimensions: { width: number; height: number };
  zoom: number;
  pan: { x: number; y: number };
  containerRef: React.RefObject<HTMLDivElement>;
  maskColor?: string;
  maskOpacity?: number;
  /** Display mode: 'pixels' for mask, 'polygon' for SVG outline */
  displayMode?: SmartSelectOutputMode;
  /** Polygon data (required when displayMode is 'polygon') */
  polygon?: PolygonData | null;
  /** Show polygon vertices as draggable points */
  showPolygonVertices?: boolean;
}

export function MaskOverlay({
  mask,
  imageDimensions,
  zoom,
  pan,
  containerRef,
  maskColor = '#8b5cf6', // purple-500
  maskOpacity = 0.4,
  displayMode = 'pixels',
  polygon = null,
  showPolygonVertices = true,
}: MaskOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [maskImage, setMaskImage] = useState<HTMLImageElement | null>(null);

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

  // Generate SVG paths for all polygon contours (including disjoint regions like grid bubbles)
  const allPolygonPaths = useMemo(() => {
    if (!polygon) return [];
    // If we have allContours, use them; otherwise fall back to primary points
    const contours = polygon.allContours || [{ points: polygon.points, area: polygon.area, perimeter: polygon.perimeter }];
    return contours
      .filter(c => c.points.length >= 3)
      .map(c => polygonToSvgPath(c.points));
  }, [polygon]);

  // Decode base64 mask to image
  useEffect(() => {
    if (!mask?.mask_base64) {
      setMaskImage(null);
      return;
    }

    const img = new Image();
    img.onload = () => {
      setMaskImage(img);
    };
    img.onerror = () => {
      console.error('Failed to decode mask image');
      setMaskImage(null);
    };

    // Handle both with and without data URL prefix
    const base64 = mask.mask_base64.startsWith('data:')
      ? mask.mask_base64
      : `data:image/png;base64,${mask.mask_base64}`;
    img.src = base64;
  }, [mask?.mask_base64]);

  // Render mask with color overlay
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !maskImage) return;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;

    // Log dimension check for debugging
    if (maskImage.width !== imageDimensions.width || maskImage.height !== imageDimensions.height) {
      console.warn(
        `MaskOverlay: Dimension mismatch! mask=(${maskImage.width}x${maskImage.height}), ` +
        `image=(${imageDimensions.width}x${imageDimensions.height}). Mask will be resampled.`
      );
    }

    // Set canvas size to match image dimensions
    canvas.width = imageDimensions.width;
    canvas.height = imageDimensions.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw mask image (grayscale, white = mask area)
    ctx.drawImage(maskImage, 0, 0, imageDimensions.width, imageDimensions.height);

    // Get image data to colorize the mask
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    // Parse mask color (hex to RGB)
    const r = parseInt(maskColor.slice(1, 3), 16);
    const g = parseInt(maskColor.slice(3, 5), 16);
    const b = parseInt(maskColor.slice(5, 7), 16);

    // Colorize: white pixels become colored, black stays transparent
    for (let i = 0; i < data.length; i += 4) {
      const brightness = data[i]; // R channel (mask is grayscale)
      if (brightness > 128) {
        // Mask area (white in original) - apply color
        data[i] = r;
        data[i + 1] = g;
        data[i + 2] = b;
        data[i + 3] = Math.round(maskOpacity * 255);
      } else {
        // Background (black in original) - make transparent
        data[i + 3] = 0;
      }
    }

    ctx.putImageData(imageData, 0, 0);
  }, [maskImage, imageDimensions, maskColor, maskOpacity, displayMode]);

  if (!mask) return null;

  // Determine if we should show polygon or pixels
  const showPolygon = displayMode === 'polygon' && polygon && polygon.points.length >= 3;

  return (
    <div
      className="absolute pointer-events-none"
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
      {/* Pixels mode: Canvas mask */}
      {displayMode === 'pixels' && (
        <canvas
          ref={canvasRef}
          className="absolute inset-0"
          style={{
            // CSS display size matches container (renderedWidth/renderedHeight)
            // Canvas internal resolution (canvas.width/height) stays at imageDimensions
            width: '100%',
            height: '100%',
          }}
        />
      )}

      {/* Polygon mode: SVG polygon */}
      {showPolygon && (
        <svg
          className="absolute inset-0"
          viewBox={`0 0 ${imageDimensions.width} ${imageDimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            // CSS display size matches container - viewBox handles coordinate scaling
            width: '100%',
            height: '100%',
          }}
        >
          {/* Polygon fill - render ALL contours (including disjoint regions like grid bubbles) */}
          {allPolygonPaths.map((path, idx) => (
            <path
              key={idx}
              d={path}
              fill={maskColor}
              fillOpacity={maskOpacity}
              stroke={maskColor}
              strokeWidth={2 / zoom}
              strokeLinejoin="round"
            />
          ))}

          {/* Polygon vertices */}
          {showPolygonVertices && polygon.points.map((point, idx) => (
            <g key={idx}>
              {/* Vertex circle */}
              <circle
                cx={point.x}
                cy={point.y}
                r={4 / zoom}
                fill="white"
                stroke={maskColor}
                strokeWidth={1.5 / zoom}
              />
              {/* Vertex index (optional, for debugging) */}
              {polygon.points.length <= 20 && (
                <text
                  x={point.x + 6 / zoom}
                  y={point.y - 6 / zoom}
                  fontSize={10 / zoom}
                  fill={maskColor}
                  fontWeight="500"
                >
                  {idx + 1}
                </text>
              )}
            </g>
          ))}

          {/* Polygon stats */}
          {mask.bbox && (
            <text
              x={mask.bbox[0]}
              y={mask.bbox[1] - 6 / zoom}
              fontSize={12 / zoom}
              fill={maskColor}
              fontWeight="bold"
            >
              {polygon.points.length} pts • IoU: {(mask.iou_score * 100).toFixed(1)}%
            </text>
          )}
        </svg>
      )}

      {/* Bounding box outline (pixels mode only) */}
      {displayMode === 'pixels' && mask.bbox && (
        <svg
          className="absolute inset-0"
          viewBox={`0 0 ${imageDimensions.width} ${imageDimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            // CSS display size matches container - viewBox handles coordinate scaling
            width: '100%',
            height: '100%',
          }}
        >
          <rect
            x={mask.bbox[0]}
            y={mask.bbox[1]}
            width={mask.bbox[2] - mask.bbox[0]}
            height={mask.bbox[3] - mask.bbox[1]}
            fill="none"
            stroke={maskColor}
            strokeWidth={2 / zoom}
            strokeDasharray={`${6 / zoom} ${3 / zoom}`}
          />
          {/* IoU score label */}
          <text
            x={mask.bbox[0]}
            y={mask.bbox[1] - 6 / zoom}
            fontSize={12 / zoom}
            fill={maskColor}
            fontWeight="bold"
          >
            IoU: {(mask.iou_score * 100).toFixed(1)}%
          </text>
        </svg>
      )}
    </div>
  );
}
