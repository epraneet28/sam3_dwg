/**
 * Zone export utilities for JSON and CSV formats
 */
import type { SAM3Document } from '../types';

export interface ExportOptions {
  includeConfidence?: boolean;
  includeCoordinates?: boolean;
}

/**
 * Exports document zones as JSON
 */
export function exportAsJSON(
  document: SAM3Document,
  options: ExportOptions = {}
): string {
  const {
    includeConfidence = true,
    includeCoordinates = true,
  } = options;

  const exportData: any = {
    documentName: document.name,
    exportedAt: new Date().toISOString(),
    totalPages: document.totalPages,
    pages: document.pages.map((page) => ({
      pageNumber: page.pageNumber + 1, // 1-indexed for export
      pageType: page.pageType,
      zones: page.zones.map((zone) => {
        const zoneData: any = {
          zoneId: zone.zone_id,
          zoneType: zone.zone_type,
        };

        if (includeConfidence) {
          zoneData.confidence = zone.confidence;
        }

        if (includeCoordinates) {
          zoneData.boundingBox = {
            x1: zone.bbox[0],
            y1: zone.bbox[1],
            x2: zone.bbox[2],
            y2: zone.bbox[3],
          };
        }

        return zoneData;
      }),
    })),
  };

  return JSON.stringify(exportData, null, 2);
}

/**
 * Exports document zones as CSV
 */
export function exportAsCSV(
  document: SAM3Document,
  options: ExportOptions = {}
): string {
  const { includeConfidence = true, includeCoordinates = true } = options;

  const headers = ['Page', 'Zone Type', 'Zone ID'];
  if (includeConfidence) headers.push('Confidence');
  if (includeCoordinates) headers.push('X1', 'Y1', 'X2', 'Y2');

  const rows: string[][] = [headers];

  document.pages.forEach((page) => {
    page.zones.forEach((zone) => {
      const row = [
        String(page.pageNumber + 1), // 1-indexed
        zone.zone_type,
        zone.zone_id,
      ];

      if (includeConfidence) {
        row.push(zone.confidence.toFixed(3));
      }

      if (includeCoordinates) {
        row.push(...zone.bbox.map((coord) => String(Math.round(coord))));
      }

      rows.push(row);
    });
  });

  // Proper CSV escaping: double quotes for escaping
  const escapeCSV = (cell: string): string => {
    const escaped = cell.toString().replace(/"/g, '""');
    return `"${escaped}"`;
  };

  return rows.map((row) => row.map(escapeCSV).join(',')).join('\n');
}

/**
 * Triggers browser file download
 */
export function downloadFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  // Sanitize filename for cross-platform compatibility
  const safeFilename = filename.replace(/[/\\":*?<>|]/g, '_');

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = safeFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
