"use client";

import { useRef, useEffect, useCallback, useState, memo } from "react";
import type { ZoneResult } from "@/lib/types";
import { getZoneAtPoint } from "@/lib/utils/canvasHitTest";
import { ZONE_COLORS } from "@/lib/constants";

export interface ImageWithZonesProps {
  imageSrc: string;
  zones: ZoneResult[];
  hoveredZoneId?: string | null;  // Externally controlled hover state
  onZoneHover?: (zoneId: string | null) => void;  // Callback when hovering
}

function ImageWithZonesComponent({
  imageSrc,
  zones,
  hoveredZoneId,
  onZoneHover
}: ImageWithZonesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [cursorStyle, setCursorStyle] = useState<string>("default");
  const previousZoneIdRef = useRef<string | null>(null);

  const getZoneColor = (zoneType: string): string => {
    return ZONE_COLORS[zoneType as keyof typeof ZONE_COLORS] || "#6b7280";
  };

  // Mouse move handler with hover detection
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!onZoneHover || !canvasRef.current) return;

      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Scale to canvas coordinates
      const scaleX = canvasRef.current.width / rect.width;
      const scaleY = canvasRef.current.height / rect.height;
      const canvasX = x * scaleX;
      const canvasY = y * scaleY;

      const zone = getZoneAtPoint(
        canvasX,
        canvasY,
        zones,
        canvasRef.current.width,
        canvasRef.current.height
      );

      const currentZoneId = zone?.zone_id || null;

      // Only call onZoneHover if zone actually changed
      if (currentZoneId !== previousZoneIdRef.current) {
        previousZoneIdRef.current = currentZoneId;
        onZoneHover(currentZoneId);
      }

      // Update cursor style
      setCursorStyle(zone ? "pointer" : "default");
    },
    [zones, onZoneHover]
  );

  // Mouse leave handler to clear hover
  const handleMouseLeave = useCallback(() => {
    if (!onZoneHover) return;

    if (previousZoneIdRef.current !== null) {
      previousZoneIdRef.current = null;
      onZoneHover(null);
    }
    setCursorStyle("default");
  }, [onZoneHover]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image || zones.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const drawZones = () => {
      // Set canvas size to match image
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;

      // Draw image
      ctx.drawImage(image, 0, 0);

      // Draw each zone
      zones.forEach((zone) => {
        const [x1, y1, x2, y2] = zone.bbox;
        const width = x2 - x1;
        const height = y2 - y1;
        const color = getZoneColor(zone.zone_type);
        const isHovered = hoveredZoneId === zone.zone_id;

        // Apply hover highlighting
        const lineWidth = isHovered ? 5 : 3;
        const fillOpacity = isHovered ? "40" : "20"; // 40 = 25%, 20 = 12.5%

        // Draw rectangle
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.strokeRect(x1, y1, width, height);

        // Draw semi-transparent fill
        ctx.fillStyle = color + fillOpacity;
        ctx.fillRect(x1, y1, width, height);

        // Draw label background
        const label = `${zone.zone_type.replace(/_/g, " ")} (${(
          zone.confidence * 100
        ).toFixed(0)}%)`;
        ctx.font = "14px system-ui, -apple-system, sans-serif";
        const textMetrics = ctx.measureText(label);
        const labelPadding = 4;
        const labelWidth = textMetrics.width + labelPadding * 2;
        const labelHeight = 20;

        // Position label at top-left of bbox
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - labelHeight, labelWidth, labelHeight);

        // Draw label text
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, x1 + labelPadding, y1 - labelPadding);
      });
    };

    if (image.complete) {
      drawZones();
    } else {
      image.onload = drawZones;
    }
  }, [imageSrc, zones, hoveredZoneId]);

  return (
    <div className="relative w-full">
      <img
        ref={imageRef}
        src={imageSrc}
        alt="Original"
        className="hidden"
      />
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ cursor: cursorStyle }}
        className="max-w-full h-auto border border-slate-300 rounded-lg"
      />
    </div>
  );
}

// Export with React.memo for performance optimization
export const ImageWithZones = memo(ImageWithZonesComponent);
