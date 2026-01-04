/**
 * DrawingCanvas - Production-grade canvas rendering with zone overlays
 *
 * Matches docling-interactive viewer architecture with:
 * - Parent-managed zoom/pan state (via useZoomPan hook)
 * - Middle mouse button panning
 * - Mouse wheel zoom around cursor
 * - RAF-based smooth updates
 * - Double-click to fit-to-page
 * - Keyboard shortcut support
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { getZoneColor } from '../../utils/constants';
import type { ZoneResult } from '../../types';

// Convert hex color to RGB
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

interface DrawingCanvasProps {
  imageUrl: string;
  zones: ZoneResult[];
  zoom: number;
  pan: { x: number; y: number };
  isPanning: boolean;
  isZooming: boolean;
  hoveredZoneId: string | null;
  selectedZoneId: string | null;
  showMasks?: boolean; // Toggle between masks and bounding boxes
  onZoneClick: (id: string) => void;
  onZoneHover: (id: string | null) => void;
  onPanStart: (e: React.MouseEvent) => void;
  onPanMove: (e: React.MouseEvent) => void;
  onPanEnd: () => void;
  onDoubleClick: (e: React.MouseEvent) => void;
  onImageLoad: (dimensions: { width: number; height: number }) => void;
  containerRef: React.RefObject<HTMLDivElement>;
}

export function DrawingCanvas({
  imageUrl,
  zones,
  zoom,
  pan,
  isPanning,
  isZooming,
  hoveredZoneId,
  selectedZoneId,
  showMasks = true,
  onZoneClick,
  onZoneHover,
  onPanStart,
  onPanMove,
  onPanEnd,
  onDoubleClick,
  onImageLoad,
  containerRef,
}: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(
    null
  );
  const [imageError, setImageError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Cache for decoded mask images
  const maskCacheRef = useRef<Map<string, HTMLImageElement>>(new Map());

  // Decode base64 mask and colorize it
  const decodeMask = useCallback(
    async (maskBase64: string, zoneId: string, color: string): Promise<HTMLImageElement | null> => {
      // Check cache first
      const cacheKey = `${zoneId}-${color}`;
      if (maskCacheRef.current.has(cacheKey)) {
        return maskCacheRef.current.get(cacheKey)!;
      }

      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          // Create a canvas to colorize the mask
          const tempCanvas = document.createElement('canvas');
          tempCanvas.width = img.width;
          tempCanvas.height = img.height;
          const tempCtx = tempCanvas.getContext('2d');

          if (!tempCtx) {
            resolve(null);
            return;
          }

          // Draw the mask
          tempCtx.drawImage(img, 0, 0);

          // Get image data and colorize
          const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
          const data = imageData.data;
          const rgb = hexToRgb(color);

          if (rgb) {
            for (let i = 0; i < data.length; i += 4) {
              // If pixel is not transparent (mask area)
              if (data[i + 3] > 0) {
                // Apply zone color with transparency
                data[i] = rgb.r;
                data[i + 1] = rgb.g;
                data[i + 2] = rgb.b;
                data[i + 3] = 100; // Semi-transparent
              }
            }
            tempCtx.putImageData(imageData, 0, 0);
          }

          // Create final image from colorized canvas
          const colorizedImg = new Image();
          colorizedImg.onload = () => {
            maskCacheRef.current.set(cacheKey, colorizedImg);
            resolve(colorizedImg);
          };
          colorizedImg.src = tempCanvas.toDataURL();
        };

        img.onerror = () => resolve(null);

        // Handle both raw base64 and data URL formats
        if (maskBase64.startsWith('data:')) {
          img.src = maskBase64;
        } else {
          img.src = `data:image/png;base64,${maskBase64}`;
        }
      });
    },
    []
  );

  // Clear mask cache when zones change
  useEffect(() => {
    maskCacheRef.current.clear();
  }, [zones]);

  // Load and draw image with zones
  useEffect(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image || !imageDimensions) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Async function to handle mask loading and drawing
    const drawCanvas = async () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw image
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

      // Draw zone overlays
      for (const zone of zones) {
        const [x1, y1, x2, y2] = zone.bbox;
        const color = getZoneColor(zone.zone_type);

        const isSelected = zone.zone_id === selectedZoneId;
        const isHovered = zone.zone_id === hoveredZoneId;

        // Try to draw mask if available and showMasks is enabled
        let maskDrawn = false;
        if (showMasks && zone.mask_base64) {
          const maskImg = await decodeMask(zone.mask_base64, zone.zone_id, color);
          if (maskImg) {
            // Draw mask scaled to fit the bounding box area
            ctx.globalAlpha = isSelected ? 0.6 : isHovered ? 0.5 : 0.4;
            ctx.drawImage(maskImg, x1, y1, x2 - x1, y2 - y1);
            ctx.globalAlpha = 1.0;
            maskDrawn = true;
          }
        }

        // Fall back to bounding box fill if no mask
        if (!maskDrawn) {
          ctx.fillStyle = `${color}${isSelected ? '55' : isHovered ? '44' : '33'}`;
          ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
        }

        // Always draw bounding box outline
        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw label for selected/hovered zones
        if (isSelected || isHovered) {
          ctx.font = 'bold 14px sans-serif';
          const label = zone.zone_type.replace(/_/g, ' ').toUpperCase();
          const labelWidth = ctx.measureText(label).width;

          // Draw label background
          ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
          ctx.fillRect(x1, y1 - 20, labelWidth + 10, 20);

          // Draw label text
          ctx.fillStyle = color;
          ctx.fillText(label, x1 + 5, y1 - 5);
        }
      }
    };

    drawCanvas();
  }, [zones, imageDimensions, hoveredZoneId, selectedZoneId, imageUrl, showMasks, decodeMask]);

  // Click detection for zones
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!imageDimensions || isPanning || !canvasRef.current) return;

    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;

    // Calculate mouse position in image coordinates
    // Account for: container center, pan offset, and zoom
    const mouseRelativeToContainer = {
      x: e.clientX - containerRect.left - containerRect.width / 2,
      y: e.clientY - containerRect.top - containerRect.height / 2,
    };

    const imageX = (mouseRelativeToContainer.x - pan.x) / zoom + imageDimensions.width / 2;
    const imageY = (mouseRelativeToContainer.y - pan.y) / zoom + imageDimensions.height / 2;

    // Find clicked zone (reverse order for top-most)
    for (let i = zones.length - 1; i >= 0; i--) {
      const [x1, y1, x2, y2] = zones[i].bbox;
      if (imageX >= x1 && imageX <= x2 && imageY >= y1 && imageY <= y2) {
        onZoneClick(zones[i].zone_id);
        return;
      }
    }

    // Click outside zones - deselect
    onZoneClick('');
  };

  // Hover detection
  const handleMouseHover = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!imageDimensions || isPanning || !canvasRef.current) return;

    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;

    const mouseRelativeToContainer = {
      x: e.clientX - containerRect.left - containerRect.width / 2,
      y: e.clientY - containerRect.top - containerRect.height / 2,
    };

    const imageX = (mouseRelativeToContainer.x - pan.x) / zoom + imageDimensions.width / 2;
    const imageY = (mouseRelativeToContainer.y - pan.y) / zoom + imageDimensions.height / 2;

    // Find hovered zone
    for (let i = zones.length - 1; i >= 0; i--) {
      const [x1, y1, x2, y2] = zones[i].bbox;
      if (imageX >= x1 && imageX <= x2 && imageY >= y1 && imageY <= y2) {
        if (hoveredZoneId !== zones[i].zone_id) {
          onZoneHover(zones[i].zone_id);
        }
        return;
      }
    }

    if (hoveredZoneId !== null) {
      onZoneHover(null);
    }
  };

  // Handle pan mouse leave - auto-end pan
  const handlePanMouseLeave = () => {
    if (isPanning) {
      onPanEnd();
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden flex items-center justify-center bg-slate-950"
      onMouseDown={onPanStart}
      onMouseMove={onPanMove}
      onMouseUp={onPanEnd}
      onMouseLeave={handlePanMouseLeave}
      onDoubleClick={onDoubleClick}
      style={{
        cursor: isPanning ? 'grabbing' : 'default',
      }}
    >
      {/* Hidden image for loading */}
      <img
        ref={imageRef}
        key={`image-${retryCount}`}
        src={imageUrl}
        alt="Drawing"
        onLoad={(e) => {
          const img = e.currentTarget;

          // Handle cached image load race condition
          if (img.complete && img.naturalWidth > 0) {
            const dims = { width: img.naturalWidth, height: img.naturalHeight };
            setImageDimensions(dims);
            setImageError(false);
            onImageLoad(dims); // Notify parent

            // Set canvas dimensions to match image
            if (canvasRef.current) {
              canvasRef.current.width = img.naturalWidth;
              canvasRef.current.height = img.naturalHeight;
            }
          }
        }}
        onError={() => setImageError(true)}
        className="hidden"
        draggable={false}
      />

      {/* Canvas with CSS transform (matching docling architecture) */}
      {imageDimensions && (
        <canvas
          ref={canvasRef}
          width={imageDimensions.width}
          height={imageDimensions.height}
          onClick={handleCanvasClick}
          onMouseMove={handleMouseHover}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isPanning || isZooming ? 'none' : 'transform 0.05s ease-out',
            maxWidth: '100%',
            maxHeight: '100%',
            pointerEvents: 'auto',
          }}
          className="shadow-2xl"
        />
      )}

      {/* Loading state */}
      {!imageDimensions && !imageError && (
        <div className="text-slate-400">Loading image...</div>
      )}

      {/* Error state */}
      {imageError && (
        <div className="flex items-center justify-center h-full bg-slate-900">
          <div className="text-center">
            <p className="text-slate-400 mb-4">Failed to load image</p>
            <button
              onClick={() => {
                setImageError(false);
                setImageDimensions(null);
                // Force reload with cache-busting
                setRetryCount((prev) => prev + 1);
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
