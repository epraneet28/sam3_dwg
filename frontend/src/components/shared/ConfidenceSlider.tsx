/**
 * ConfidenceSlider - Reusable confidence threshold slider with visual fill
 *
 * Used in both Viewer (ZoneSidebar) and Playground for consistent UI
 */

interface ConfidenceSliderProps {
  value: number;
  onChange: (value: number) => void;
  label?: string;
  step?: number;
}

export function ConfidenceSlider({
  value,
  onChange,
  label = 'Confidence Threshold',
  step = 0.01,
}: ConfidenceSliderProps) {
  const percentage = value * 100;

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs text-slate-400">{label}</label>
        <span className="text-xs font-medium text-blue-400 tabular-nums">
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="relative h-2">
        {/* Track background */}
        <div className="absolute inset-0 bg-slate-700 rounded-lg" />
        {/* Fill indicator */}
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-500 rounded-lg transition-all duration-100"
          style={{ width: `${percentage}%` }}
        />
        {/* Invisible range input on top */}
        <input
          type="range"
          min="0"
          max="1"
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        {/* Thumb indicator */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 bg-white rounded-full shadow-md border-2 border-blue-500 pointer-events-none transition-all duration-100"
          style={{ left: `calc(${percentage}% - 7px)` }}
        />
      </div>
    </div>
  );
}
