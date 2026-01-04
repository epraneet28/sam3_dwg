/**
 * MaskOverlay - SVG/Canvas overlay for displaying segmentation masks
 *
 * Renders the selected mask from interactive segmentation results.
 * The mask is displayed as a semi-transparent colored overlay.
 */

import { useEffect, useRef, useState } from 'react';
import type { MaskCandidate } from '../../types';

interface MaskOverlayProps {
  mask: MaskCandidate | null;
  imageDimensions: { width: number; height: number };
  zoom: number;
  pan: { x: number; y: number };
  maskColor?: string;
  maskOpacity?: number;
}

export function MaskOverlay({
  mask,
  imageDimensions,
  zoom,
  pan,
  maskColor = '#8b5cf6', // purple-500
  maskOpacity = 0.4,
}: MaskOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [maskImage, setMaskImage] = useState<HTMLImageElement | null>(null);

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

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

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
  }, [maskImage, imageDimensions, maskColor, maskOpacity]);

  if (!mask) return null;

  return (
    <div
      className="absolute inset-0 pointer-events-none"
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
      {/* Mask canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0"
        style={{
          width: imageDimensions.width,
          height: imageDimensions.height,
        }}
      />

      {/* Bounding box outline around mask */}
      {mask.bbox && (
        <svg
          className="absolute inset-0"
          viewBox={`0 0 ${imageDimensions.width} ${imageDimensions.height}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            width: imageDimensions.width,
            height: imageDimensions.height,
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
