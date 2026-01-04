/**
 * ZoneSidebar - Floating zone list with filters (docling-interactive pattern)
 */

import { useEffect, useState, useRef } from 'react';
import {
  Bars3BottomLeftIcon,
  ChevronDownIcon,
  EyeIcon,
  EyeSlashIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { PanelHeader, PanelFooter, ConfidenceSlider } from '../shared';
import { getZoneColor, ZONE_TYPES } from '../../utils/constants';
import type { ZoneResult, ZoneType } from '../../types';

interface ZoneSidebarProps {
  zones: ZoneResult[];
  allZonesForCounting: ZoneResult[]; // Zones filtered by confidence only, for type counts
  confidenceThreshold: number;
  selectedZoneTypes: Set<ZoneType>;
  hoveredZoneId: string | null;
  selectedZoneId: string | null;
  hiddenZoneIds: Set<string>;
  showMasks: boolean;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onThresholdChange: (threshold: number) => void;
  onZoneTypeToggle: (type: ZoneType) => void;
  onSelectAllTypes: () => void;
  onDeselectAllTypes: () => void;
  onZoneClick: (id: string) => void;
  onZoneHover: (id: string | null) => void;
  onZoneDetails: (id: string) => void;
  onToggleZoneVisibility: (id: string) => void;
  onShowMasksChange: (show: boolean) => void;
}

export function ZoneSidebar({
  zones,
  allZonesForCounting,
  confidenceThreshold,
  selectedZoneTypes,
  hoveredZoneId,
  selectedZoneId,
  hiddenZoneIds,
  showMasks,
  isOpen,
  onOpenChange,
  onThresholdChange,
  onZoneTypeToggle,
  onSelectAllTypes,
  onDeselectAllTypes,
  onZoneClick,
  onZoneHover,
  onZoneDetails,
  onToggleZoneVisibility,
  onShowMasksChange,
}: ZoneSidebarProps) {
  // Dropdown state for zone type filter
  const [typeDropdownOpen, setTypeDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected zone
  useEffect(() => {
    if (selectedZoneId && isOpen) {
      const element = document.getElementById(`zone-${selectedZoneId}`);
      element?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [selectedZoneId, isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setTypeDropdownOpen(false);
      }
    };
    if (typeDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [typeDropdownOpen]);

  // Count zones by type (using confidence-filtered zones, not type-filtered)
  const zoneCounts = allZonesForCounting.reduce((acc, zone) => {
    acc[zone.zone_type] = (acc[zone.zone_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Get active types with zones
  const activeTypesWithZones = ZONE_TYPES.filter(
    (type) => selectedZoneTypes.has(type) && zoneCounts[type] > 0
  );

  // Collapsed state - show toggle button
  if (!isOpen) {
    return (
      <button
        onClick={() => onOpenChange(true)}
        className="absolute top-4 right-4 z-40 p-3 bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-lg shadow-lg hover:bg-slate-700 transition-colors"
        title="Show zones panel"
      >
        <Bars3BottomLeftIcon className="w-5 h-5 text-white" />
      </button>
    );
  }

  // Expanded state - show full panel
  return (
    <div className="absolute top-4 right-4 bottom-4 w-96 flex flex-col bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden">
      {/* Header */}
      <PanelHeader
        title="Zones"
        count={zones.length}
        countLabel="zones"
        instruction="Click to highlight • Use icons for details/hide"
        onClose={() => onOpenChange(false)}
        closeIcon="chevron"
      >
        {/* Filters inside header */}
        <div className="mt-3 space-y-3">
          {/* Confidence Slider with Fill */}
          <ConfidenceSlider
            value={confidenceThreshold}
            onChange={onThresholdChange}
          />

          {/* Zone Type Filter - Compact Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs text-slate-400">Zone Types</label>
            </div>

            {/* Dropdown Button */}
            <button
              onClick={() => setTypeDropdownOpen(!typeDropdownOpen)}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg transition-colors"
            >
              {/* Active type color dots (show up to 5) */}
              <div className="flex items-center gap-0.5">
                {activeTypesWithZones.slice(0, 5).map((type) => (
                  <div
                    key={type}
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: getZoneColor(type) }}
                  />
                ))}
                {activeTypesWithZones.length > 5 && (
                  <span className="text-[10px] text-slate-400 ml-0.5">+{activeTypesWithZones.length - 5}</span>
                )}
              </div>
              <span className="flex-1 text-left text-xs text-slate-300">
                {selectedZoneTypes.size === ZONE_TYPES.length
                  ? 'All types'
                  : selectedZoneTypes.size === 0
                  ? 'None selected'
                  : `${selectedZoneTypes.size} of ${ZONE_TYPES.length}`}
              </span>
              <ChevronDownIcon
                className={`w-3.5 h-3.5 text-slate-400 transition-transform ${typeDropdownOpen ? 'rotate-180' : ''}`}
              />
            </button>

            {/* Dropdown Menu */}
            {typeDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
                {/* Quick Actions */}
                <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-slate-700 bg-slate-800/80">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wide">Quick Select</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => { onSelectAllTypes(); }}
                      className="text-[10px] text-blue-400 hover:text-blue-300 font-medium"
                    >
                      All
                    </button>
                    <button
                      onClick={() => { onDeselectAllTypes(); }}
                      className="text-[10px] text-blue-400 hover:text-blue-300 font-medium"
                    >
                      None
                    </button>
                  </div>
                </div>

                {/* Type List */}
                <div className="max-h-48 overflow-y-auto py-1 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
                  {ZONE_TYPES.map((type) => (
                    <label
                      key={type}
                      className="flex items-center gap-2 px-2.5 py-1.5 text-xs text-slate-300 cursor-pointer hover:bg-slate-700/50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedZoneTypes.has(type)}
                        onChange={() => onZoneTypeToggle(type)}
                        className="w-3 h-3 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-1"
                      />
                      <div
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getZoneColor(type) }}
                      />
                      <span className="flex-1 truncate">{type.replace(/_/g, ' ')}</span>
                      <span className="text-slate-500 text-[10px] tabular-nums">
                        {zoneCounts[type] || 0}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Mask Display Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-xs text-slate-400">Display Mode</label>
            <button
              onClick={() => onShowMasksChange(!showMasks)}
              className={`flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs transition-colors ${
                showMasks
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                  : 'bg-slate-700/50 text-slate-400 border border-slate-600'
              }`}
            >
              {showMasks ? (
                <>
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                  </svg>
                  Masks
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1V5z" />
                  </svg>
                  Boxes
                </>
              )}
            </button>
          </div>
        </div>
      </PanelHeader>

      {/* Zone List - Scrollable content */}
      <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
        {zones.length > 0 ? (
          <div className="space-y-2">
            {zones.map((zone) => {
              const isHidden = hiddenZoneIds.has(zone.zone_id);
              const isSelected = selectedZoneId === zone.zone_id;
              const isHovered = hoveredZoneId === zone.zone_id;

              return (
                <div
                  key={zone.zone_id}
                  id={`zone-${zone.zone_id}`}
                  onClick={() => onZoneClick(zone.zone_id)}
                  onMouseEnter={() => onZoneHover(zone.zone_id)}
                  onMouseLeave={() => onZoneHover(null)}
                  className={`
                    p-2.5 rounded-lg border cursor-pointer transition-all
                    ${isSelected
                      ? 'bg-blue-500/20 border-blue-500 ring-1 ring-blue-500/50'
                      : isHovered
                      ? 'bg-slate-700 border-slate-500'
                      : 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-700/50 hover:border-slate-600'
                    }
                    ${isHidden ? 'opacity-50' : ''}
                  `}
                >
                  {/* Top row: Zone type + Confidence */}
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getZoneColor(zone.zone_type) }}
                      />
                      <span className="text-xs font-medium text-white truncate">
                        {zone.zone_type.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-blue-400 tabular-nums flex-shrink-0">
                      {(zone.confidence * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Bottom row: Dimensions + Action buttons */}
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">
                      {Math.round(zone.bbox[2] - zone.bbox[0])} × {Math.round(zone.bbox[3] - zone.bbox[1])} px
                    </span>
                    <div className="flex items-center gap-1">
                      {/* Details button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onZoneDetails(zone.zone_id);
                        }}
                        className="p-1 rounded hover:bg-slate-600/50 text-slate-400 hover:text-white transition-colors"
                        title="View details"
                      >
                        <InformationCircleIcon className="w-4 h-4" />
                      </button>
                      {/* Hide/Show button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleZoneVisibility(zone.zone_id);
                        }}
                        className={`p-1 rounded hover:bg-slate-600/50 transition-colors ${
                          isHidden ? 'text-orange-400 hover:text-orange-300' : 'text-slate-400 hover:text-white'
                        }`}
                        title={isHidden ? 'Show on viewer' : 'Hide on viewer'}
                      >
                        {isHidden ? (
                          <EyeSlashIcon className="w-4 h-4" />
                        ) : (
                          <EyeIcon className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-slate-500 text-xs">
              No zones match filters
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <PanelFooter
        pageCount={zones.length}
        pageCountUnit="zones"
        pageCountSuffix="detected"
        status={selectedZoneId ? '1 selected' : undefined}
      />
    </div>
  );
}
