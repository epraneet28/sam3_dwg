/**
 * Zone Details Modal - Shows comprehensive zone information
 */
import type { ZoneResult } from '../../types';
import { getZoneColor } from '../../utils/constants';

interface ZoneDetailsModalProps {
  zone: ZoneResult | null;
  onClose: () => void;
}

export default function ZoneDetailsModal({ zone, onClose }: ZoneDetailsModalProps) {
  if (!zone) return null;

  const [x1, y1, x2, y2] = zone.bbox;
  const width = x2 - x1;
  const height = y2 - y1;
  const area = width * height;
  const color = getZoneColor(zone.zone_type);

  // Normalized coordinates (0-1 range, assuming typical drawing dimensions)
  const normalizedCoords = {
    x1: (x1 / 1000).toFixed(3),
    y1: (y1 / 1000).toFixed(3),
    x2: (x2 / 1000).toFixed(3),
    y2: (y2 / 1000).toFixed(3),
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              Zone Details
            </h2>
            <p className="text-sm text-slate-400 mt-1">ID: {zone.zone_id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
            title="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4">
          {/* Zone Type */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Zone Type
            </label>
            <p className="mt-1 text-white font-medium">
              {zone.zone_type.replace(/_/g, ' ').toUpperCase()}
            </p>
          </div>

          {/* Confidence */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Confidence Score
            </label>
            <div className="mt-1 flex items-center gap-3">
              <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all"
                  style={{ width: `${zone.confidence * 100}%` }}
                />
              </div>
              <span className="text-white font-medium tabular-nums">
                {(zone.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Bounding Box */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Bounding Box (Pixels)
            </label>
            <div className="mt-2 grid grid-cols-2 gap-3">
              <div className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">Top-Left</div>
                <div className="text-white font-mono text-sm">
                  ({Math.round(x1)}, {Math.round(y1)})
                </div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">Bottom-Right</div>
                <div className="text-white font-mono text-sm">
                  ({Math.round(x2)}, {Math.round(y2)})
                </div>
              </div>
            </div>
          </div>

          {/* Dimensions */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Dimensions
            </label>
            <div className="mt-2 grid grid-cols-3 gap-3">
              <div className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">Width</div>
                <div className="text-white font-mono text-sm">{Math.round(width)}px</div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">Height</div>
                <div className="text-white font-mono text-sm">{Math.round(height)}px</div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-500 mb-1">Area</div>
                <div className="text-white font-mono text-sm">
                  {area.toLocaleString(undefined, { maximumFractionDigits: 0 })}px²
                </div>
              </div>
            </div>
          </div>

          {/* Normalized Coordinates */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Normalized Coordinates (0-1 scale)
            </label>
            <div className="mt-2 bg-slate-900/50 p-3 rounded-lg">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
                <div className="text-slate-400">x1:</div>
                <div className="text-white">{normalizedCoords.x1}</div>
                <div className="text-slate-400">y1:</div>
                <div className="text-white">{normalizedCoords.y1}</div>
                <div className="text-slate-400">x2:</div>
                <div className="text-white">{normalizedCoords.x2}</div>
                <div className="text-slate-400">y2:</div>
                <div className="text-white">{normalizedCoords.y2}</div>
              </div>
            </div>
          </div>

          {/* Center Point */}
          <div>
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Center Point
            </label>
            <div className="mt-2 bg-slate-900/50 p-3 rounded-lg">
              <div className="text-white font-mono text-sm">
                ({Math.round((x1 + x2) / 2)}, {Math.round((y1 + y2) / 2)})
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
