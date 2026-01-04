/**
 * SAM3 Constants - Zone types and colors
 */

import type { ZoneType } from '../types';

export const ZONE_TYPES: readonly ZoneType[] = [
  'title_block',
  'revision_block',
  'plan_view',
  'elevation_view',
  'section_view',
  'detail_view',
  'schedule_table',
  'notes_area',
  'legend',
  'grid_system',
  'unknown',
] as const;

// Colors optimized for dark theme (slate-900 background)
export const ZONE_COLORS: Record<ZoneType, string> = {
  title_block: '#60a5fa',      // blue-400
  revision_block: '#c084fc',   // purple-400
  plan_view: '#4ade80',        // green-400
  elevation_view: '#facc15',   // yellow-400
  section_view: '#fb923c',     // orange-400
  detail_view: '#f87171',      // red-400
  schedule_table: '#f472b6',   // pink-400
  notes_area: '#818cf8',       // indigo-400
  legend: '#22d3ee',           // cyan-400
  grid_system: '#2dd4bf',      // teal-400
  unknown: '#9ca3af',          // gray-400
};

export const DEFAULT_CONFIDENCE_THRESHOLD = 0.3;

export function getZoneColor(zoneType: string): string {
  return ZONE_COLORS[zoneType as ZoneType] || ZONE_COLORS.unknown;
}
